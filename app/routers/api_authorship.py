"""
eaiou — Tier 3 JSON REST API: Authorship + AI
7 endpoints: attribution CRUD, AI session logging, AI disclosure.

Router prefix: /api/v1
Tags:          api-authorship

Live schema verified 2026-04-12:
  #__eaiou_attribution_log — id, paper_id, contributor_name, orcid,
      role_description, contribution_type, is_human, is_ai, ai_tool_used,
      state, created, created_by, modified, modified_by
  #__eaiou_ai_sessions     — id, paper_id, session_label, ai_model_name,
      start_time, end_time, tokens_in, tokens_out, redaction_status,
      session_notes, session_hash, state, created, created_by
  #__eaiou_didntmakeit     — id, session_id, prompt_text, response_text,
      exclusion_reason, redacted, redaction_hash, state, created
  #__eaiou_papers          — ai_disclosure_level, ai_disclosure_notes,
      ai_involvement_level does NOT exist — omit
"""

import hashlib
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..deps import (
    get_current_user,
    require_auth,
    require_editor,
    require_reviewer,
    require_eic,
    optional_auth,
)
from ..services.api_log import log_api_call

router = APIRouter(prefix="/api/v1", tags=["api-authorship"])

# ── Allowed patch fields (whitelist) ─────────────────────────────────────────

_ATTRIBUTION_PATCH = frozenset({
    "contributor_name", "orcid", "role_description",
    "contribution_type", "is_human", "is_ai", "ai_tool_used",
})


# ── Pydantic models ───────────────────────────────────────────────────────────

class ContributionUpdate(BaseModel):
    contributor_name: Optional[str] = None
    orcid: Optional[str] = None
    role_description: Optional[str] = None
    contribution_type: Optional[str] = None
    is_human: Optional[bool] = None
    is_ai: Optional[bool] = None
    ai_tool_used: Optional[str] = None


class AISessionByPaper(BaseModel):
    session_label: str
    ai_model_name: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    redaction_status: str = "none"
    session_notes: Optional[str] = None


# ── 1. PATCH /attribution/{id} — contribution.update ─────────────────────────

@router.patch("/attribution/{id}")
async def contribution_update(
    id: int,
    body: ContributionUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    # Reject any attempt to change paper_id via body
    body_data = body.model_dump(exclude_none=True)
    if "paper_id" in body_data:
        raise HTTPException(status_code=422, detail="Cannot change paper_id on an attribution row.")

    # Fetch attribution row to check ownership
    row = db.execute(text(
        "SELECT id, paper_id, state FROM `#__eaiou_attribution_log` WHERE id = :id"
    ), {"id": id}).mappings().first()

    if row is None or row["state"] == -2:
        raise HTTPException(status_code=404, detail="Attribution record not found.")

    # ACL: EDITOR/ADMIN can always edit; AUTHOR must own the paper
    groups = set(current_user.get("groups", []))
    is_editor_plus = bool({"editor", "admin"} & groups)

    if not is_editor_plus:
        paper = db.execute(text(
            "SELECT id FROM `#__eaiou_papers` "
            "WHERE id = :pid AND author_name = :name AND tombstone_state IS NULL"
        ), {"pid": row["paper_id"], "name": current_user["name"]}).fetchone()
        if paper is None:
            # Also check created_by
            creator = db.execute(text(
                "SELECT id FROM `#__eaiou_attribution_log` WHERE id = :id AND created_by = :uid"
            ), {"id": id, "uid": current_user["id"]}).fetchone()
            if creator is None:
                raise HTTPException(status_code=403, detail="You do not own this attribution record.")

    # Build dynamic UPDATE using only whitelisted columns
    sets = {}
    for field, val in body_data.items():
        if field in _ATTRIBUTION_PATCH:
            sets[field] = val

    if not sets:
        raise HTTPException(status_code=422, detail="No valid fields to update.")

    now = datetime.now(timezone.utc)
    set_clause = ", ".join(f"`{k}` = :{k}" for k in sets)
    sets["_id"] = id
    sets["_now"] = now
    sets["_uid"] = current_user["id"]

    db.execute(text(
        f"UPDATE `#__eaiou_attribution_log` SET {set_clause}, "
        f"modified = :_now, modified_by = :_uid WHERE id = :_id"
    ), sets)
    db.commit()

    updated = db.execute(text(
        "SELECT id, paper_id, contributor_name, orcid, role_description, "
        "contribution_type, is_human, is_ai, ai_tool_used, state, modified "
        "FROM `#__eaiou_attribution_log` WHERE id = :id"
    ), {"id": id}).mappings().first()

    log_api_call(
        db, f"/api/v1/attribution/{id}", "PATCH",
        hashlib.sha256(str(id).encode()).hexdigest(), 200,
    )

    return dict(updated)


# ── 2. DELETE /attribution/{id} — contribution.delete ────────────────────────

@router.delete("/attribution/{id}")
async def contribution_delete(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    existing = db.execute(text(
        "SELECT id, state FROM `#__eaiou_attribution_log` WHERE id = :id"
    ), {"id": id}).fetchone()
    if existing is None:
        raise HTTPException(status_code=404, detail="Attribution not found.")
    if existing[1] == -2:
        raise HTTPException(status_code=404, detail="Attribution already deleted.")

    result = db.execute(text(
        "UPDATE `#__eaiou_attribution_log` SET state = -2 WHERE id = :id"
    ), {"id": id})
    db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Attribution record not found.")

    log_api_call(
        db, f"/api/v1/attribution/{id}", "DELETE",
        hashlib.sha256(str(id).encode()).hexdigest(), 200,
    )

    return {"id": id, "tombstoned": True}


# ── 3. GET /ai/sessions/{id} — intellid.get ──────────────────────────────────

@router.get("/ai/sessions/{id}")
async def ai_session_get(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_reviewer),
):
    row = db.execute(text(
        "SELECT id, paper_id, session_label, ai_model_name, start_time, end_time, "
        "tokens_in, tokens_out, redaction_status, session_notes, session_hash, "
        "state, created, created_by "
        "FROM `#__eaiou_ai_sessions` "
        "WHERE id = :id AND (state IS NULL OR state != -2)"
    ), {"id": id}).mappings().first()

    if row is None:
        raise HTTPException(status_code=404, detail="AI session not found.")

    return {k: v for k, v in dict(row).items() if k != "session_hash"}


# ── 4. GET /ai/sessions/{session_id}/didntmakeit — intellid.get_contributions ─

@router.get("/ai/sessions/{session_id}/didntmakeit")
async def ai_session_didntmakeit(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_reviewer),
):
    rows = db.execute(text(
        "SELECT id, session_id, prompt_text, response_text, exclusion_reason, "
        "redacted, redaction_hash, state, created "
        "FROM `#__eaiou_didntmakeit` WHERE session_id = :sid ORDER BY id"
    ), {"sid": session_id}).mappings().all()

    groups = set(current_user.get("groups", []))
    is_eic_plus = bool({"eic", "admin"} & groups)

    result = []
    for r in rows:
        d = dict(r)
        if not is_eic_plus:
            # REVIEWER gets metadata only — scrub content fields
            d["prompt_text"] = None
            d["response_text"] = None
        result.append(d)

    return result


# ── 5. POST /papers/{paper_id}/ai/sessions — ai.log_session ──────────────────

@router.post("/papers/{paper_id}/ai/sessions")
async def ai_log_session(
    paper_id: int,
    body: AISessionByPaper,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    paper = db.execute(text(
        "SELECT id FROM `#__eaiou_papers` WHERE id = :pid AND tombstone_state IS NULL"
    ), {"pid": paper_id}).fetchone()
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found.")

    now = datetime.now(timezone.utc)
    session_hash = hashlib.sha256(
        f"{paper_id}|{body.session_label}|{now.isoformat()}".encode()
    ).hexdigest()

    # Parse optional datetime strings
    start_time = None
    end_time = None
    if body.start_time:
        try:
            start_time = datetime.fromisoformat(body.start_time.replace("Z", "+00:00"))
        except ValueError:
            pass
    if body.end_time:
        try:
            end_time = datetime.fromisoformat(body.end_time.replace("Z", "+00:00"))
        except ValueError:
            pass

    db.execute(text(
        "INSERT INTO `#__eaiou_ai_sessions` "
        "(paper_id, session_label, ai_model_name, start_time, end_time, "
        " tokens_in, tokens_out, redaction_status, session_notes, session_hash, "
        " state, created, created_by) "
        "VALUES (:pid, :label, :model, :start, :end, "
        "        :tin, :tout, :redact, :notes, :hash, "
        "        1, :now, :uid)"
    ), {
        "pid":    paper_id,
        "label":  body.session_label,
        "model":  body.ai_model_name,
        "start":  start_time,
        "end":    end_time,
        "tin":    body.tokens_in,
        "tout":   body.tokens_out,
        "redact": body.redaction_status,
        "notes":  body.session_notes,
        "hash":   session_hash,
        "now":    now,
        "uid":    current_user["id"],
    })
    db.commit()

    new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()

    log_api_call(
        db, f"/api/v1/papers/{paper_id}/ai/sessions", "POST",
        hashlib.sha256(str(paper_id).encode()).hexdigest(), 201,
    )

    return JSONResponse(
        status_code=201,
        content={"session_id": new_id, "paper_id": paper_id, "session_label": body.session_label},
    )


# ── 6. GET /papers/{paper_id}/ai/sessions — ai.get_sessions ──────────────────

@router.get("/papers/{paper_id}/ai/sessions")
async def ai_get_sessions(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_reviewer),
):
    rows = db.execute(text(
        "SELECT id, paper_id, session_label, ai_model_name, start_time, end_time, "
        "tokens_in, tokens_out, redaction_status, session_notes, session_hash, "
        "state, created "
        "FROM `#__eaiou_ai_sessions` WHERE paper_id = :pid ORDER BY id"
    ), {"pid": paper_id}).mappings().all()

    return [{k: v for k, v in dict(r).items() if k != "session_hash"} for r in rows]


# ── 7. GET /papers/{paper_id}/ai/disclosure — ai.get_disclosure (PUBLIC) ──────

@router.get("/papers/{paper_id}/ai/disclosure")
async def ai_get_disclosure(
    paper_id: int,
    db: Session = Depends(get_db),
):
    paper = db.execute(text(
        "SELECT ai_disclosure_level, ai_disclosure_notes "
        "FROM `#__eaiou_papers` "
        "WHERE id = :pid AND tombstone_state IS NULL"
    ), {"pid": paper_id}).mappings().first()

    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found.")

    interaction_count = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_ai_sessions` WHERE paper_id = :pid"
    ), {"pid": paper_id}).scalar() or 0

    disclosure_level = paper["ai_disclosure_level"]
    ai_used = bool(disclosure_level and disclosure_level != "none")
    ai_log_complete = interaction_count > 0

    return {
        "ai_used":             ai_used,
        "ai_disclosure_level": disclosure_level,
        "ai_disclosure_notes": paper["ai_disclosure_notes"],
        "interaction_count":   interaction_count,
        "ai_log_complete":     ai_log_complete,
    }
