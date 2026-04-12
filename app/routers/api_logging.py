"""
eaiou — Tier 9 JSON REST API: Logging (Read endpoints)
3 active endpoints: API log list, webhook logs, notification logs.

Router prefix: /api/v1
Tags:          api-logging

Note: Internal log functions (log_api_call) are already implemented as
services in app/services/api_log.py. This tier exposes READ endpoints only.

# log.hash_chain is an alias for system.hash.verify
# See GET /audit/chain_status in api_versioning.py — not duplicated here.

Live schema verified 2026-04-12:
  #__eaiou_api_logs — id, api_key_id, endpoint, method, request_data,
                       response_code, log_hash, prior_hash, log_timestamp, ...
"""

import hashlib
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..deps import require_admin
from ..services.api_log import log_api_call

router = APIRouter(prefix="/api/v1", tags=["api-logging"])


# ── 1. GET /admin/api/logs — require_admin ────────────────────────────────────

@router.get("/admin/api/logs")
async def list_api_logs(
    endpoint: Optional[str] = None,
    response_code: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    base_sql = (
        "SELECT id, api_key_id, endpoint, method, response_code, "
        "log_hash, prior_hash, log_timestamp "
        "FROM `#__eaiou_api_logs` "
    )
    params: dict = {"limit": limit, "offset": offset}
    conditions = []

    if endpoint:
        conditions.append("endpoint LIKE :endpoint_filter")
        params["endpoint_filter"] = f"%{endpoint}%"

    if response_code is not None:
        conditions.append("response_code = :response_code")
        params["response_code"] = response_code

    if conditions:
        base_sql += "WHERE " + " AND ".join(conditions) + " "

    base_sql += "ORDER BY id DESC LIMIT :limit OFFSET :offset"

    rows = db.execute(text(base_sql), params).mappings().all()

    # Total count (without limit/offset)
    count_sql = "SELECT COUNT(*) FROM `#__eaiou_api_logs`"
    count_params: dict = {}
    if conditions:
        count_sql += " WHERE " + " AND ".join(conditions)
        count_params = {k: v for k, v in params.items() if k not in ("limit", "offset")}
    total = db.execute(text(count_sql), count_params).scalar() or 0

    return {
        "logs":  [dict(r) for r in rows],
        "total": total,
    }


# ── 2. GET /admin/webhooks/logs — require_admin ───────────────────────────────

@router.get("/admin/webhooks/logs")
async def list_webhook_logs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    rows = db.execute(text(
        "SELECT id, api_key_id, endpoint, method, response_code, "
        "log_hash, prior_hash, log_timestamp "
        "FROM `#__eaiou_api_logs` "
        "WHERE endpoint LIKE '%webhook%' OR endpoint LIKE '%sync%' "
        "ORDER BY id DESC LIMIT 200"
    )).mappings().all()

    return {"logs": [dict(r) for r in rows]}


# ── 3. GET /admin/notifications/logs — require_admin ─────────────────────────

@router.get("/admin/notifications/logs")
async def list_notification_logs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    rows = db.execute(text(
        "SELECT id, api_key_id, endpoint, method, response_code, "
        "log_hash, prior_hash, log_timestamp "
        "FROM `#__eaiou_api_logs` "
        "WHERE endpoint LIKE '%notif%' OR method = 'NOTIFY' "
        "ORDER BY id DESC LIMIT 200"
    )).mappings().all()

    return {"logs": [dict(r) for r in rows]}
