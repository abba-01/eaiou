"""
iid_dispatcher.py — central dispatcher for IID action invocations on the
                     eaiou authoring surface.

Responsibilities:
  1. Resolve provider + action from the request payload
  2. Enforce ToS Compliance Doctrine §1 rules (no chaining, per-provider isolation)
  3. Pin a manuscript snapshot at invocation time
  4. Insert pending action row in eaiou_iid_actions
  5. Call the provider adapter (anthropic / openai / gemini / custom)
  6. Persist result + IID disclosure block
  7. Return the action record for the API layer to render

This module never:
  * Calls one IID and feeds its output to another (Rule 1: no chaining).
  * Runs in a background loop (Rule 2: no background invocation).
  * Touches another provider's credentials (Rule 3: per-provider isolation).
  * Strips the disclosure block (Rule 4: mandatory disclosure).
  * Auto-applies output to manuscript text (Rule 5: author-owned text).

See `/scratch/repos/eaiou/docs/TOS_COMPLIANCE_DOCTRINE.md` for the full doctrine.
"""

import hashlib
import json
import secrets
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

# Phase 0: handler stubs are reused from review_handlers/ (which already
# implement the @register pattern). Phase 1 will move provider adapters
# into iid_providers/<name>.py per IID_PROVIDER_MODULE_PATTERN.md.
# For Phase A scaffolding, dispatch through review_handlers.dispatch().
from app.services.review_handlers import dispatch as review_dispatch


class IIDDispatcherError(RuntimeError):
    """Base for dispatcher errors."""


class ProviderNotConfiguredError(IIDDispatcherError):
    """User has no provider with the requested name."""


class ChainingViolationError(IIDDispatcherError):
    """Attempted to feed one IID's output as another IID's input. Rule 1."""


# ── Public API ────────────────────────────────────────────────────────────────

def invoke(
    db: Session,
    *,
    user_id: int,
    provider_id: int,
    action_name: str,
    inputs: dict,
    manuscript_id: Optional[int] = None,
) -> dict:
    """
    Dispatch one IID action.

    Args:
      db:           SQLAlchemy session.
      user_id:      eaiou_users.id of the author invoking.
      provider_id:  eaiou_iid_providers.id (must belong to user_id).
      action_name:  e.g. 'scope_check', 'clarity_check', 'methods_check'.
      inputs:       per-action input payload (validated upstream by the API layer).
      manuscript_id: optional; if set, snapshot is pinned and result is logged
                     against the manuscript.

    Returns:
      dict with the action record (matches _iid_output_card.html template
      variables — id, intellid, provider, action, model_family, instance_hash,
      result_text, body_html, structured, created_at, completed_at, etc.).

    Raises:
      ProviderNotConfiguredError, ChainingViolationError, IIDDispatcherError.
    """
    # 1. Resolve provider (and verify ownership — per-provider isolation rule)
    provider = _load_provider(db, user_id=user_id, provider_id=provider_id)
    if not provider:
        raise ProviderNotConfiguredError(
            f"provider {provider_id} not found for user {user_id} (or inactive)"
        )

    # 2. Rule 1 (no chaining): inputs must not contain references to
    #    intellids of OTHER actions. This is a structural check at the
    #    dispatcher layer.
    _check_no_chaining(inputs)

    # 3. Generate identity for this invocation
    intellid = str(uuid.uuid4())
    instance_hash = secrets.token_hex(8)  # 16 hex chars

    # 4. Pin manuscript snapshot if applicable
    snapshot_id = None
    if manuscript_id is not None:
        snapshot_id = _pin_manuscript_snapshot(
            db, manuscript_id=manuscript_id,
            triggered_by="iid_action",
        )

    # 5. Insert pending action row
    action_id = _insert_pending_action(
        db,
        intellid=intellid,
        user_id=user_id,
        provider_id=provider["id"],
        manuscript_id=manuscript_id,
        action_name=action_name,
        model_family=provider["default_model"],
        instance_hash=instance_hash,
    )
    _insert_action_inputs(
        db,
        action_id=action_id,
        inputs=inputs,
        manuscript_snapshot_id=snapshot_id,
    )

    # 6. Dispatch via the handler registry. Phase 0 returns stubs; Phase 1
    #    swaps in real provider adapters but the dispatch contract is identical.
    ctx = {
        "user_id": user_id,
        "provider_id": provider["id"],
        "manuscript_id": manuscript_id,
        "intellid": intellid,
        "model_family": provider["default_model"],
    }
    try:
        result = review_dispatch(action_name, inputs, ctx)
    except Exception as exc:
        _mark_action_failed(db, action_id=action_id, error_text=str(exc))
        db.commit()
        raise IIDDispatcherError(f"handler {action_name} raised: {exc}") from exc

    # 7. Persist result + complete the action
    completed_at = datetime.utcnow()
    _mark_action_completed(
        db,
        action_id=action_id,
        result=result,
        completed_at=completed_at,
        instance_hash=instance_hash,  # may be overwritten if handler returned its own
    )
    db.commit()

    # 8. Re-fetch and return the canonical action record (with all fields
    #    a template needs to render the disclosure block faithfully)
    return get_action(db, action_id=action_id)


def get_action(db: Session, *, action_id: int) -> dict:
    """Fetch one action with all fields the output card needs."""
    row = db.execute(text("""
        SELECT a.id, a.intellid, a.user_id, a.provider_id, a.manuscript_id,
               a.action_name, a.model_family, a.instance_hash, a.status,
               a.input_tokens, a.output_tokens, a.cost_cents,
               a.result_text, a.result_structured, a.error_text,
               a.created_at, a.completed_at,
               p.name AS provider_name, p.display_name AS provider_display,
               p.provider_legal AS provider_legal
        FROM `#__eaiou_iid_actions` a
        JOIN `#__eaiou_iid_providers` p ON p.id = a.provider_id
        WHERE a.id = :aid
    """), {"aid": action_id}).mappings().first()
    if not row:
        return None

    structured = None
    if row["result_structured"]:
        try:
            structured = json.loads(row["result_structured"])
        except json.JSONDecodeError:
            structured = None

    return {
        "id": row["id"],
        "intellid": row["intellid"],
        "provider": {
            "name": row["provider_name"],
            "display_name": row["provider_display"],
            "legal_name": row["provider_legal"],
        },
        "action": {"name": row["action_name"]},
        "model_family": row["model_family"],
        "instance_hash": row["instance_hash"],
        "status": row["status"],
        "input_tokens": row["input_tokens"],
        "output_tokens": row["output_tokens"],
        "cost_cents": row["cost_cents"],
        "cost_display": _format_cost(row["cost_cents"]),
        "result_text": row["result_text"],
        "body_html": _render_body_html(row["result_text"]),
        "structured": structured,
        "stub": (structured or {}).get("stub", False) if structured else False,
        "error_text": row["error_text"],
        "created_at": row["created_at"],
        "created_at_display": _format_relative_time(row["created_at"]),
        "completed_at": row["completed_at"],
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _load_provider(db: Session, *, user_id: int, provider_id: int) -> Optional[dict]:
    """Per-provider isolation: provider must belong to user_id and be active."""
    row = db.execute(text("""
        SELECT id, user_id, name, display_name, provider_legal,
               default_model, enabled_actions, active, disabled_at
        FROM `#__eaiou_iid_providers`
        WHERE id = :pid AND user_id = :uid AND active = 1 AND disabled_at IS NULL
    """), {"pid": provider_id, "uid": user_id}).mappings().first()
    return dict(row) if row else None


def _check_no_chaining(inputs: dict) -> None:
    """Reject inputs that reference another IID's intellid (Rule 1)."""
    if not isinstance(inputs, dict):
        return
    for key, val in inputs.items():
        if not isinstance(val, str):
            continue
        # An intellid is a uuid4. Detect a 36-char dash-separated hex pattern
        # in input field names that suggest IID-output reference.
        if "intellid" in key.lower() or "iid_output" in key.lower():
            raise ChainingViolationError(
                f"input field {key!r} appears to reference another IID action's output. "
                "ToS Compliance Rule 1: no chaining. Each invocation receives original "
                "inputs only."
            )


def _pin_manuscript_snapshot(
    db: Session,
    *,
    manuscript_id: int,
    triggered_by: str,
) -> int:
    """Create a snapshot of the manuscript's current blocks. Returns snapshot id."""
    # Read all blocks in order
    blocks = db.execute(text("""
        SELECT sort_index, type, text, html, anchor, metadata_json
        FROM `#__eaiou_manuscript_blocks`
        WHERE manuscript_id = :mid ORDER BY sort_index
    """), {"mid": manuscript_id}).mappings().all()
    blocks_json = json.dumps([dict(b) for b in blocks], default=str)
    word_count = sum(len((b["text"] or "").split()) for b in blocks)
    content_hash = hashlib.sha256(blocks_json.encode("utf-8")).hexdigest()

    # Auto-label as next rN
    last = db.execute(text("""
        SELECT label FROM `#__eaiou_manuscript_snapshots`
        WHERE manuscript_id = :mid ORDER BY id DESC LIMIT 1
    """), {"mid": manuscript_id}).mappings().first()
    if last and last["label"] and last["label"].startswith("r") and last["label"][1:].isdigit():
        label = f"r{int(last['label'][1:]) + 1}"
    else:
        label = "r1"

    result = db.execute(text("""
        INSERT INTO `#__eaiou_manuscript_snapshots`
          (manuscript_id, label, triggered_by, blocks_json, word_count, content_hash)
        VALUES (:mid, :label, :triggered_by, :blocks_json, :wc, :hash)
    """), {
        "mid": manuscript_id, "label": label, "triggered_by": triggered_by,
        "blocks_json": blocks_json, "wc": word_count, "hash": content_hash,
    })
    return result.lastrowid


def _insert_pending_action(
    db: Session, *,
    intellid: str, user_id: int, provider_id: int,
    manuscript_id: Optional[int], action_name: str,
    model_family: str, instance_hash: str,
) -> int:
    result = db.execute(text("""
        INSERT INTO `#__eaiou_iid_actions`
          (intellid, user_id, provider_id, manuscript_id,
           action_name, model_family, instance_hash, status)
        VALUES
          (:intellid, :uid, :pid, :mid,
           :action, :model, :hash, 'pending')
    """), {
        "intellid": intellid, "uid": user_id, "pid": provider_id,
        "mid": manuscript_id, "action": action_name,
        "model": model_family, "hash": instance_hash,
    })
    return result.lastrowid


def _insert_action_inputs(
    db: Session, *,
    action_id: int, inputs: dict,
    manuscript_snapshot_id: Optional[int],
) -> None:
    selected = inputs.get("selected_text") if isinstance(inputs, dict) else None
    db.execute(text("""
        INSERT INTO `#__eaiou_iid_action_inputs`
          (action_id, selected_text, inputs_json, manuscript_snapshot_id)
        VALUES (:aid, :sel, :inp, :snap)
    """), {
        "aid": action_id, "sel": selected,
        "inp": json.dumps(inputs), "snap": manuscript_snapshot_id,
    })


def _mark_action_completed(
    db: Session, *,
    action_id: int, result: dict, completed_at: datetime,
    instance_hash: str,
) -> None:
    # Provider may return its own iid sub-block; honour it for instance_hash
    iid_meta = result.get("iid", {}) if isinstance(result, dict) else {}
    final_hash = iid_meta.get("instance_hash") or instance_hash

    structured = {k: v for k, v in (result or {}).items() if k != "reasoning"}
    db.execute(text("""
        UPDATE `#__eaiou_iid_actions`
        SET status = :status,
            instance_hash = :hash,
            result_text = :reasoning,
            result_structured = :structured,
            input_tokens = :input_tokens,
            output_tokens = :output_tokens,
            cost_cents = :cost_cents,
            completed_at = :completed_at
        WHERE id = :aid
    """), {
        "aid": action_id,
        "status": "failed" if result.get("error") else "completed",
        "hash": final_hash,
        "reasoning": result.get("reasoning"),
        "structured": json.dumps(structured) if structured else None,
        "input_tokens": result.get("input_tokens"),
        "output_tokens": result.get("output_tokens"),
        "cost_cents": result.get("cost_cents"),
        "completed_at": completed_at,
    })


def _mark_action_failed(db: Session, *, action_id: int, error_text: str) -> None:
    db.execute(text("""
        UPDATE `#__eaiou_iid_actions`
        SET status = 'failed',
            error_text = :err,
            completed_at = NOW()
        WHERE id = :aid
    """), {"aid": action_id, "err": error_text[:65000]})


def _format_cost(cost_cents: Optional[int]) -> Optional[str]:
    if cost_cents is None:
        return None
    if cost_cents == 0:
        return "1 credit"
    return f"${cost_cents / 100:.2f}"


def _format_relative_time(dt: datetime) -> str:
    if not dt:
        return "just now"
    delta = (datetime.utcnow() - dt).total_seconds()
    if delta < 60:
        return "just now"
    if delta < 3600:
        return f"{int(delta // 60)} min ago"
    if delta < 86400:
        return f"{int(delta // 3600)} hr ago"
    return dt.strftime("%Y-%m-%d")


def _render_body_html(result_text: Optional[str]) -> Optional[str]:
    """
    Phase 0: pass-through with paragraph wrapping.
    Phase 1+: markdown rendering, citation linking, math typesetting.
    """
    if not result_text:
        return None
    paragraphs = [p.strip() for p in result_text.split("\n\n") if p.strip()]
    return "".join(f"<p>{p}</p>" for p in paragraphs)
