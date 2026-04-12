"""
eaiou — Tier 11 JSON REST API: System
4 endpoints: health (public/admin), metrics, maintenance toggle, maintenance status.

Router prefix: /api/v1
Tags:          api-system

Live schema verified 2026-04-12:
  #__eaiou_papers      — id, status, tombstone_state, ...
  #__eaiou_review_logs — id, ...
  #__eaiou_api_logs    — id, log_timestamp, ...
"""

import hashlib
import os
import platform
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..deps import optional_auth, require_admin
from ..services.api_log import log_api_call

router = APIRouter(prefix="/api/v1", tags=["api-system"])


# ── Module-level maintenance state ────────────────────────────────────────────

_MAINTENANCE: dict = {"enabled": False, "message": ""}


# ── Pydantic models ───────────────────────────────────────────────────────────

class MaintenanceToggle(BaseModel):
    enabled: bool
    message: str = "Maintenance in progress"


# ── 1. GET /system/health — PUBLIC (basic) / ADMIN (detailed) ─────────────────

@router.get("/system/health")
async def system_health(
    db: Session = Depends(get_db),
    current_user=Depends(optional_auth),
):
    base = {"status": "ok", "version": "0.1.0"}

    # Admin callers get extended details
    groups = current_user.get("groups", []) if current_user else []
    if "admin" in groups:
        db_status = "error"
        try:
            db.execute(text("SELECT 1")).fetchone()
            db_status = "connected"
        except Exception:
            pass

        base.update({
            "db":                db_status,
            "python":            platform.python_version(),
            "environment":       os.getenv("ENVIRONMENT", "development"),
            "upload_dir_exists": Path(os.getenv("UPLOAD_DIR", "/var/eaiou/uploads")).exists(),
        })

    return base


# ── 2. GET /system/metrics — require_admin ────────────────────────────────────

@router.get("/system/metrics")
async def system_metrics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    total_papers = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_papers` WHERE tombstone_state IS NULL"
    )).scalar() or 0

    published_papers = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_papers` "
        "WHERE status = 'published' AND tombstone_state IS NULL"
    )).scalar() or 0

    under_review_papers = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_papers` WHERE status = 'under_review'"
    )).scalar() or 0

    total_reviews = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_review_logs`"
    )).scalar() or 0

    api_calls_24h = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_api_logs` "
        "WHERE log_timestamp > NOW() - INTERVAL 24 HOUR"
    )).scalar() or 0

    return {
        "papers": {
            "total":        total_papers,
            "published":    published_papers,
            "under_review": under_review_papers,
        },
        "reviews": {
            "total": total_reviews,
        },
        "api": {
            "calls_24h": api_calls_24h,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ── 3. POST /system/maintenance — require_admin ───────────────────────────────

@router.post("/system/maintenance")
async def set_maintenance(
    body: MaintenanceToggle,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    global _MAINTENANCE
    _MAINTENANCE["enabled"] = body.enabled
    _MAINTENANCE["message"] = body.message

    log_api_call(
        db, "/api/v1/system/maintenance", "POST",
        hashlib.sha256(f"maintenance|{body.enabled}".encode()).hexdigest(), 200,
    )

    return {"maintenance": body.enabled, "message": body.message}


# ── 4. GET /system/maintenance — PUBLIC ───────────────────────────────────────

@router.get("/system/maintenance")
async def get_maintenance():
    return {
        "maintenance": _MAINTENANCE["enabled"],
        "message":     _MAINTENANCE["message"],
    }
