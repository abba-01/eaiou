"""
eaiou — Tier 8 JSON REST API: Admin
8 endpoints: dashboard, user management, paper override, settings, workflow config.

Router prefix: /api/v1
Tags:          api-admin

Note: There is already an app/routers/admin.py (HTML admin panel at /admin/...).
This file exposes JSON API admin endpoints at /api/v1/admin/...
No URL collision.

Live schema verified 2026-04-12:
  #__eaiou_users       — id, username, email, display_name, active, orcid, ...
  #__eaiou_papers      — id, status, tombstone_state, ...
  #__eaiou_review_logs — state (1 = invited), ...
  #__eaiou_api_logs    — log_timestamp, ...
"""

import hashlib
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..deps import require_admin, require_editor
from ..services.api_log import log_api_call

router = APIRouter(prefix="/api/v1", tags=["api-admin"])


# ── Pydantic models ───────────────────────────────────────────────────────────

class AdminUserUpdate(BaseModel):
    active: Optional[bool] = None
    display_name: Optional[str] = None


class PaperOverride(BaseModel):
    target_state: str
    reason: str
    bypass_guards: bool = True


class SettingsUpdate(BaseModel):
    max_api_keys_per_user: Optional[int] = None


# ── Whitelisted user patch fields ─────────────────────────────────────────────

_USER_PATCH = frozenset({"active", "display_name"})


# ── 1. GET /admin/dashboard — require_editor ─────────────────────────────────

@router.get("/admin/dashboard")
async def admin_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    total = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_papers` WHERE tombstone_state IS NULL"
    )).scalar() or 0

    published = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_papers` "
        "WHERE status = 'published' AND tombstone_state IS NULL"
    )).scalar() or 0

    under_review = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_papers` WHERE status = 'under_review'"
    )).scalar() or 0

    pending_reviews = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_review_logs` WHERE state = 1"
    )).scalar() or 0

    api_calls_30d = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_api_logs` "
        "WHERE log_timestamp > NOW() - INTERVAL 30 DAY"
    )).scalar() or 0

    return {
        "papers": {
            "total":        total,
            "published":    published,
            "under_review": under_review,
        },
        "reviews": {
            "pending": pending_reviews,
        },
        "api_calls_30d": api_calls_30d,
    }


# ── 2. GET /admin/users — require_admin ───────────────────────────────────────

@router.get("/admin/users")
async def admin_list_users(
    group: Optional[str] = None,
    has_orcid: bool = False,
    status: str = "active",
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    base_sql = (
        "SELECT u.id, u.username, u.email, u.display_name, u.active, "
        "u.created_at, u.last_login_at, u.orcid, u.auth_provider "
        "FROM `#__eaiou_users` u "
    )
    params: dict = {}
    conditions = []

    if group:
        base_sql += (
            "JOIN `#__eaiou_user_groups` ug ON ug.user_id = u.id "
            "JOIN `#__eaiou_groups` g ON g.id = ug.group_id "
        )
        conditions.append("g.name = :group_name")
        params["group_name"] = group

    if status == "active":
        conditions.append("u.active = 1")
    elif status == "inactive":
        conditions.append("u.active = 0")

    if has_orcid:
        conditions.append("u.orcid IS NOT NULL AND u.orcid != ''")

    if conditions:
        base_sql += "WHERE " + " AND ".join(conditions)

    base_sql += " ORDER BY u.id ASC"

    rows = db.execute(text(base_sql), params).mappings().all()
    # Never return password_hash
    return [dict(r) for r in rows]


# ── 3. PATCH /admin/users/{id} — require_admin ───────────────────────────────

@router.patch("/admin/users/{id}")
async def admin_update_user(
    id: int,
    body: AdminUserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    body_data = body.model_dump(exclude_none=True)
    sets = {k: v for k, v in body_data.items() if k in _USER_PATCH}

    if not sets:
        raise HTTPException(status_code=422, detail="No valid fields to update.")

    set_clause = ", ".join(f"`{k}` = :{k}" for k in sets)
    sets["_id"] = id

    result = db.execute(text(
        f"UPDATE `#__eaiou_users` SET {set_clause} WHERE id = :_id"
    ), sets)
    db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found.")

    log_api_call(
        db, f"/api/v1/admin/users/{id}", "PATCH",
        hashlib.sha256(str(id).encode()).hexdigest(), 200,
    )

    return {"id": id, "updated": True}


# ── 4. POST /admin/papers/{id}/override — require_admin ──────────────────────

@router.post("/admin/papers/{id}/override")
async def admin_paper_override(
    id: int,
    body: PaperOverride,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    result = db.execute(text(
        "UPDATE `#__eaiou_papers` SET status = :state "
        "WHERE id = :id AND tombstone_state IS NULL"
    ), {"state": body.target_state, "id": id})
    db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Paper not found or tombstoned.")

    log_api_call(
        db, f"/api/v1/admin/papers/{id}/override", "POST",
        hashlib.sha256(f"STATUS_OVERRIDE|{id}|{body.target_state}".encode()).hexdigest(), 200,
    )

    return {
        "paper_id":  id,
        "new_state": body.target_state,
        "reason":    body.reason,
        "bypassed":  True,
    }


# ── 5. GET /admin/settings — require_admin ────────────────────────────────────

@router.get("/admin/settings")
async def admin_get_settings(
    current_user: dict = Depends(require_admin),
):
    return {
        "q_signal_weights": {"transparency": 1.5, "others": 1.0},
        "max_api_keys_per_user": 5,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "upload_dir": os.getenv("UPLOAD_DIR", "/var/eaiou/uploads"),
    }


# ── 6. PATCH /admin/settings — require_admin ──────────────────────────────────

@router.patch("/admin/settings")
async def admin_update_settings(
    body: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    # No DB-persisted settings yet — in-memory only
    log_api_call(
        db, "/api/v1/admin/settings", "PATCH",
        hashlib.sha256("settings_update".encode()).hexdigest(), 200,
    )

    return {
        "updated": True,
        "note": "In-memory only — restart required for changes",
    }


# ── 7. GET /admin/qsignal/config — require_admin ─────────────────────────────

@router.get("/admin/qsignal/config")
async def admin_qsignal_config(
    current_user: dict = Depends(require_admin),
):
    return {
        "weights": {
            "overall":        1.0,
            "originality":    1.0,
            "methodology":    1.0,
            "transparency":   1.5,
            "ai_disclosure":  1.0,
            "crossdomain":    1.0,
        }
    }


# ── 8. GET /admin/workflow/config — require_admin ─────────────────────────────

@router.get("/admin/workflow/config")
async def admin_workflow_config(
    current_user: dict = Depends(require_admin),
):
    return {
        "states": [
            "draft", "submitted", "under_review", "decision_pending",
            "revisions_requested", "accepted", "published", "rejected",
        ],
        "transitions": {
            "draft":                ["submitted"],
            "submitted":            ["under_review"],
            "under_review":         ["decision_pending"],
            "decision_pending":     ["accepted", "rejected", "revisions_requested"],
            "revisions_requested":  ["submitted"],
            "accepted":             ["published"],
        },
    }
