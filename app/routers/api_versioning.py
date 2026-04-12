"""
eaiou — Tier 7 JSON REST API: Versioning & Audit
4 endpoints: paper versions CRUD, integrity check, hash chain audit.

Router prefix: /api/v1
Tags:          api-versioning

Live schema verified 2026-04-12:
  #__eaiou_versions — id, paper_id, label, file_path, content_hash,
                       ai_flag, ai_model_name, generated_at, notes,
                       state, access, ordering, created, ...
  #__eaiou_papers   — id, submission_hash, submission_capstone, cosmoid,
                       tombstone_state, submission_version, ...
  #__eaiou_api_logs — id, log_hash, prior_hash, ...
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
from ..deps import get_current_user, require_auth, require_editor, require_admin, optional_auth
from ..services.api_log import log_api_call

router = APIRouter(prefix="/api/v1", tags=["api-versioning"])


# ── Pydantic models ───────────────────────────────────────────────────────────

class VersionCreate(BaseModel):
    label: str
    ai_flag: bool = False
    ai_model_name: Optional[str] = None
    notes: Optional[str] = None


# ── 1. GET /papers/{paper_id}/versions — PUBLIC ───────────────────────────────

@router.get("/papers/{paper_id}/versions")
async def list_paper_versions(
    paper_id: int,
    db: Session = Depends(get_db),
):
    # Verify paper exists and is not tombstoned
    paper = db.execute(text(
        "SELECT id FROM `#__eaiou_papers` WHERE id = :pid AND tombstone_state IS NULL"
    ), {"pid": paper_id}).fetchone()
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found.")

    rows = db.execute(text(
        "SELECT id, paper_id, label, ai_flag, notes, content_hash "
        "FROM `#__eaiou_versions` "
        "WHERE paper_id = :pid "
        "ORDER BY id ASC"
    ), {"pid": paper_id}).mappings().all()

    # TB: strip generated_at from public response (governance-only)
    return [dict(r) for r in rows]


# ── 2. POST /papers/{paper_id}/versions — require_auth ───────────────────────

@router.post("/papers/{paper_id}/versions")
async def create_paper_version(
    paper_id: int,
    body: VersionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    # Verify paper exists, not tombstoned, and user has access
    paper = db.execute(text(
        "SELECT id, author_name, submission_version FROM `#__eaiou_papers` "
        "WHERE id = :pid AND tombstone_state IS NULL"
    ), {"pid": paper_id}).mappings().first()
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found or tombstoned.")

    # ACL: AUTHOR of own paper or EDITOR/ADMIN
    groups = current_user.get("groups", [])
    is_privileged = bool({"admin", "editor"} & set(groups))
    is_own = paper["author_name"] == current_user["name"]
    if not is_privileged and not is_own:
        raise HTTPException(status_code=403, detail="Access denied.")

    now = datetime.now(timezone.utc)

    db.execute(text(
        "INSERT INTO `#__eaiou_versions` "
        "(paper_id, label, ai_flag, ai_model_name, notes, created) "
        "VALUES (:pid, :label, :ai_flag, :ai_model, :notes, :now)"
    ), {
        "pid":      paper_id,
        "label":    body.label,
        "ai_flag":  int(body.ai_flag),
        "ai_model": body.ai_model_name,
        "notes":    body.notes,
        "now":      now,
    })
    db.commit()
    version_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()

    # Bump submission_version counter (column exists per schema check)
    db.execute(text(
        "UPDATE `#__eaiou_papers` "
        "SET submission_version = COALESCE(submission_version, 0) + 1 "
        "WHERE id = :pid"
    ), {"pid": paper_id})
    db.commit()

    log_api_call(
        db, f"/api/v1/papers/{paper_id}/versions", "POST",
        hashlib.sha256(str(version_id).encode()).hexdigest(), 201,
    )

    return JSONResponse(
        status_code=201,
        content={"version_id": version_id, "paper_id": paper_id, "label": body.label},
    )


# ── 3. GET /papers/{paper_id}/integrity — PUBLIC ──────────────────────────────

@router.get("/papers/{paper_id}/integrity")
async def paper_integrity(
    paper_id: int,
    db: Session = Depends(get_db),
):
    paper = db.execute(text(
        "SELECT submission_hash, submission_capstone, cosmoid "
        "FROM `#__eaiou_papers` "
        "WHERE id = :pid AND tombstone_state IS NULL"
    ), {"pid": paper_id}).mappings().first()
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found.")

    # Use submission_capstone if available, else cosmoid as capstone fallback
    capstone = paper["submission_capstone"] or paper["cosmoid"]

    versions = db.execute(text(
        "SELECT label, content_hash "
        "FROM `#__eaiou_versions` "
        "WHERE paper_id = :pid "
        "ORDER BY id ASC"
    ), {"pid": paper_id}).mappings().all()

    # IMPORTANT: No sealed date fields in public response
    return {
        "sealed": {
            "hash":     paper["submission_hash"],
            "capstone": capstone,
        },
        "versions": [{"label": r["label"], "content_hash": r["content_hash"]} for r in versions],
    }


# ── 4. GET /audit/chain_status — require_admin ────────────────────────────────

@router.get("/audit/chain_status")
async def audit_chain_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    rows = db.execute(text(
        "SELECT id, log_hash, prior_hash "
        "FROM `#__eaiou_api_logs` "
        "ORDER BY id ASC"
    )).mappings().all()

    entries = len(rows)
    last_verified = datetime.now(timezone.utc).isoformat()

    if entries == 0:
        return {
            "status":        "intact",
            "entries":       0,
            "last_verified": last_verified,
            "break_at":      None,
        }

    if rows[0]["prior_hash"] is not None:
        return JSONResponse({
            "status":        "broken",
            "break_at":      rows[0]["id"],
            "reason":        "First row has non-null prior_hash — chain head may have been deleted",
            "entries":       entries,
            "last_verified": last_verified,
        })

    prev_hash = rows[0]["log_hash"]
    for row in rows[1:]:
        if row["prior_hash"] != prev_hash:
            return {
                "status":        "broken",
                "break_at":      row["id"],
                "expected_hash": prev_hash,
                "found_hash":    row["prior_hash"],
                "entries":       entries,
                "last_verified": last_verified,
            }
        prev_hash = row["log_hash"]

    return {
        "status":        "intact",
        "entries":       entries,
        "last_verified": last_verified,
        "break_at":      None,
    }
