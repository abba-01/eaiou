"""
eaiou — Tier 12 JSON REST API: API Key Management & Webhooks
6 endpoints: create key, list keys, revoke key, logs alias,
             gitgap webhook, rate limit info.

Router prefix: /api/v1
Tags:          api-keys

Live schema verified 2026-04-12:
  #__eaiou_api_keys — id, user_id, api_key, description, access_level,
                       status, last_used, state, access, ordering,
                       created, created_by, modified, modified_by,
                       checked_out, checked_out_time
  Column notes:
    - api_key: stores the raw/hashed key (VARCHAR 255)
    - No key_hash or key_preview column exists; we store key hash in api_key
    - No created_at column: use 'created'
"""

import hashlib
import json
import os
import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..deps import require_auth, require_admin
from ..services.api_log import log_api_call

router = APIRouter(prefix="/api/v1", tags=["api-keys"])


# ── Pydantic models ───────────────────────────────────────────────────────────

class ApiKeyCreate(BaseModel):
    user_id: int
    description: str
    access_level: str = "read"


# ── 1. POST /api/keys — require_admin ────────────────────────────────────────

@router.post("/api/keys")
async def create_api_key(
    body: ApiKeyCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    # Generate raw key — shown ONCE ONLY, never stored
    raw_key = "eaiou_" + secrets.token_hex(24)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    now = datetime.now(timezone.utc)

    db.execute(text(
        "INSERT INTO `#__eaiou_api_keys` "
        "(user_id, api_key, description, access_level, status, created, created_by) "
        "VALUES (:uid, :key_hash, :desc, :access_level, 'active', :now, :creator)"
    ), {
        "uid":          body.user_id,
        "key_hash":     key_hash,
        "desc":         body.description,
        "access_level": body.access_level,
        "now":          now,
        "creator":      current_user["id"],
    })
    db.commit()
    key_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()

    log_api_call(
        db, "/api/v1/api/keys", "POST",
        hashlib.sha256(str(key_id).encode()).hexdigest(), 201,
    )

    # Raw key returned ONCE ONLY — hash is stored, raw is not
    return JSONResponse(
        status_code=201,
        content={
            "id":           key_id,
            "api_key":      raw_key,
            "access_level": body.access_level,
            "status":       "active",
        },
    )


# ── 2. GET /api/keys — require_admin ─────────────────────────────────────────

@router.get("/api/keys")
async def list_api_keys(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    rows = db.execute(text(
        "SELECT id, user_id, description, access_level, status, "
        "last_used, created, api_key "
        "FROM `#__eaiou_api_keys` "
        "ORDER BY id DESC"
    )).mappings().all()

    result = []
    for r in rows:
        item = {
            "id":           r["id"],
            "user_id":      r["user_id"],
            "description":  r["description"],
            "access_level": r["access_level"],
            "status":       r["status"],
            "last_used_at": r["last_used"],
            "created_at":   r["created"],
            # Mask: show only last 8 chars of stored hash (raw was never stored)
            "key_masked":   "..." + (r["api_key"] or "")[-8:] if r["api_key"] else None,
        }
        result.append(item)

    return result


# ── 3. PATCH /api/keys/{id}/revoke — require_admin ───────────────────────────

@router.patch("/api/keys/{id}/revoke")
async def revoke_api_key(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    result = db.execute(text(
        "UPDATE `#__eaiou_api_keys` SET status = 'revoked' WHERE id = :id"
    ), {"id": id})
    db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="API key not found.")

    log_api_call(
        db, f"/api/v1/api/keys/{id}/revoke", "PATCH",
        hashlib.sha256(str(id).encode()).hexdigest(), 200,
    )

    return {"id": id, "status": "revoked"}


# ── 4. GET /api/logs — alias for GET /admin/api/logs ─────────────────────────

@router.get("/api/logs")
async def api_logs_alias(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    rows = db.execute(text(
        "SELECT id, api_key_id, endpoint, method, response_code, "
        "log_hash, prior_hash, log_timestamp "
        "FROM `#__eaiou_api_logs` ORDER BY id DESC LIMIT :limit OFFSET :offset"
    ), {"limit": limit, "offset": offset}).mappings().all()

    return {"logs": [dict(r) for r in rows]}


# ── 5. POST /webhooks/gitgap — webhook secret auth ───────────────────────────

@router.post("/webhooks/gitgap")
async def webhook_gitgap(
    payload: dict,
    db: Session = Depends(get_db),
    x_gitgap_secret: Optional[str] = Header(default=None),
):
    expected_secret = os.getenv("GITGAP_WEBHOOK_SECRET", "")
    if not expected_secret or not secrets.compare_digest(
        x_gitgap_secret or "", expected_secret
    ):
        raise HTTPException(status_code=401, detail="Invalid or missing webhook secret.")

    log_api_call(
        db, "/api/v1/webhooks/gitgap", "POST",
        hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest(), 200,
    )

    return {"received": True}


# ── 6. GET /api/rate_limit — require_auth ────────────────────────────────────

@router.get("/api/rate_limit")
async def api_rate_limit(
    current_user: dict = Depends(require_auth),
):
    return {
        "limit":     1000,
        "remaining": 999,
        "reset_at":  "next hour",
        "window":    "1h",
        "note":      "Rate limit enforcement is per-process.",
    }
