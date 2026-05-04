"""
api_iid.py — IID dispatch endpoint for the eaiou authoring surface.

POST /api/iid/invoke
GET  /api/iid/actions/{action_id}
GET  /api/iid/manuscripts/{manuscript_id}/recent
POST /api/iid/actions/{action_id}/dismiss

Auth: requires logged-in eaiou user (Depends(require_auth)). Partner-key access
is on the marketplace router, not here — IID actions are author-initiated only.

Response format: every endpoint that returns an action emits both:
  * the JSON record (for client-side wiring), and
  * an html_fragment field with the rendered _iid_output_card.html for direct
    DOM insertion when the client wants the server to do the rendering.

ToS Compliance Doctrine §1 enforced via:
  * Rule 1 (no chaining): iid_dispatcher.invoke() raises ChainingViolationError
  * Rule 2 (no background): every endpoint requires authenticated user request
  * Rule 3 (per-provider isolation): dispatcher loads provider scoped to user
  * Rule 4 (mandatory disclosure): _iid_output_card.html ALWAYS emits the
    disclosure block; html_fragment field includes it verbatim
  * Rule 5 (author-owned text): no auto-apply; client receives the result
    and the author chooses to insert/dismiss

Tags: iid
Prefix: /api/iid
"""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_auth
from ..services import iid_dispatcher

router = APIRouter(prefix="/api/iid", tags=["iid"])

# Templates loaded the same way the rest of eaiou does (path matches existing
# Jinja2 setup; if the live server uses a different templates dir, this picks
# up the same conventions automatically).
_templates = Jinja2Templates(directory="app/templates")


# ── Constants ─────────────────────────────────────────────────────────────────

_VALID_ACTIONS = frozenset({
    "scope_check", "journal_select", "outline_check", "clarity_check",
    "methods_check", "reference_audit", "full_review", "premium_review",
})

_MAX_INPUTS_BYTES = 8 * 1024  # match marketplace cap


# ── Pydantic models ───────────────────────────────────────────────────────────

class IIDInvokeRequest(BaseModel):
    provider_id: int
    action_name: str
    inputs: dict = Field(default_factory=dict)
    manuscript_id: Optional[int] = None

    @field_validator("action_name")
    @classmethod
    def _validate_action(cls, v: str) -> str:
        if v not in _VALID_ACTIONS:
            raise ValueError(f"action_name must be one of {sorted(_VALID_ACTIONS)}")
        return v

    @field_validator("inputs")
    @classmethod
    def _validate_inputs(cls, v: dict) -> dict:
        if not isinstance(v, dict):
            raise ValueError("inputs must be a JSON object")
        if any(not isinstance(k, str) for k in v.keys()):
            raise ValueError("inputs keys must all be strings")
        size = len(json.dumps(v).encode("utf-8"))
        if size > _MAX_INPUTS_BYTES:
            raise ValueError(f"inputs exceeds 8KB cap (got {size} bytes)")
        return v


class IIDActionOut(BaseModel):
    id: int
    intellid: str
    provider: dict
    action: dict
    model_family: str
    instance_hash: str
    status: str
    result_text: Optional[str] = None
    body_html: Optional[str] = None
    structured: Optional[dict] = None
    stub: bool = False
    cost_display: Optional[str] = None
    created_at_display: Optional[str] = None
    html_fragment: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/invoke")
def invoke_action(
    body: IIDInvokeRequest,
    request: Request,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    Dispatch one IID action. Returns the action record + rendered html_fragment.

    The author has explicitly initiated this call (Rule 2: no background invocation).
    The dispatcher enforces no-chaining (Rule 1) and per-provider isolation (Rule 3).
    The output card template emits the mandatory disclosure block (Rule 4).
    The result is advisory; client decides insert / dismiss (Rule 5).
    """
    try:
        action = iid_dispatcher.invoke(
            db,
            user_id=current_user["id"],
            provider_id=body.provider_id,
            action_name=body.action_name,
            inputs=body.inputs,
            manuscript_id=body.manuscript_id,
        )
    except iid_dispatcher.ProviderNotConfiguredError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except iid_dispatcher.ChainingViolationError as exc:
        # ToS Compliance Rule 1 violation; refuse explicitly with a clear error.
        raise HTTPException(status_code=400, detail=f"chaining-violation: {exc}")
    except iid_dispatcher.IIDDispatcherError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    # Render the output card server-side so client can drop it into the DOM.
    html_fragment = _render_output_card(request, action)
    response = {**action, "html_fragment": html_fragment}
    return response


@router.get("/actions/{action_id}")
def get_action(
    action_id: int,
    request: Request,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Fetch one action by id. Owner-only."""
    action = iid_dispatcher.get_action(db, action_id=action_id)
    if not action:
        raise HTTPException(status_code=404, detail="action not found")

    # Ownership check — actions are author-private
    row = db.execute(text("""
        SELECT user_id FROM `#__eaiou_iid_actions` WHERE id = :aid
    """), {"aid": action_id}).mappings().first()
    if not row or row["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="not your action")

    html_fragment = _render_output_card(request, action)
    return {**action, "html_fragment": html_fragment}


@router.get("/manuscripts/{manuscript_id}/recent")
def list_recent_actions(
    manuscript_id: int,
    limit: int = 20,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Recent IID actions on a manuscript, newest first. Author-private."""
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be in [1, 100]")

    # Ownership check via manuscript
    row = db.execute(text("""
        SELECT user_id FROM `#__eaiou_manuscripts` WHERE id = :mid
    """), {"mid": manuscript_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="manuscript not found")
    if row["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="not your manuscript")

    rows = db.execute(text("""
        SELECT id FROM `#__eaiou_iid_actions`
        WHERE manuscript_id = :mid AND user_id = :uid
        ORDER BY created_at DESC LIMIT :lim
    """), {"mid": manuscript_id, "uid": current_user["id"], "lim": limit}).mappings().all()

    return [iid_dispatcher.get_action(db, action_id=r["id"]) for r in rows]


@router.post("/actions/{action_id}/dismiss")
def dismiss_action(
    action_id: int,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    Mark an action as dismissed (UI hide). Soft-deletes it from the manuscript's
    output stream but preserves the audit-log record (Rule 4 — disclosure
    survives even when author dismisses).
    """
    row = db.execute(text("""
        SELECT user_id, status FROM `#__eaiou_iid_actions` WHERE id = :aid
    """), {"aid": action_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="action not found")
    if row["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="not your action")

    # Soft-dismiss via status transition. The action row itself is preserved.
    db.execute(text("""
        UPDATE `#__eaiou_iid_actions`
        SET status = CASE
            WHEN status IN ('completed', 'failed') THEN CONCAT(status, '_dismissed')
            ELSE status
          END
        WHERE id = :aid
    """), {"aid": action_id})
    db.commit()

    return {"action_id": action_id, "dismissed": True}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _render_output_card(request: Request, action: dict) -> str:
    """
    Render _iid_output_card.html with the action context.

    Returns the HTML fragment as a string (not a TemplateResponse) — the API
    layer wraps it in JSON. Client-side iid_dispatch.js drops the fragment
    directly into the output stream.
    """
    template = _templates.get_template("author/_iid_output_card.html")
    return template.render(output=action, request=request)
