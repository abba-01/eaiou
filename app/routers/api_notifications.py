"""
eaiou — Tier 10 JSON REST API: Notifications
3 endpoints: list notifications, mark read, admin preview.

Router prefix: /api/v1
Tags:          api-notifications

Note: notification.send is internal/triggered by workflow, not an HTTP endpoint.

Live schema verified 2026-04-12:
  #__eaiou_notifications — id, paper_id, type, message, created_at, read_at
  (No user_id column — ownership resolved via paper's author_name)
  #__eaiou_papers — id, author_name, title, ...
  #__eaiou_users  — id, username, display_name, ...
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
from ..deps import require_auth, require_admin
from ..services.api_log import log_api_call

router = APIRouter(prefix="/api/v1", tags=["api-notifications"])


# ── 1. GET /notifications — require_auth ──────────────────────────────────────

@router.get("/notifications")
async def list_notifications(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    # Ownership via paper's author_name (no user_id column on notifications)
    rows = db.execute(text(
        "SELECT n.id, n.type, n.message, n.paper_id, n.created_at, n.read_at "
        "FROM `#__eaiou_notifications` n "
        "JOIN `#__eaiou_papers` p ON p.id = n.paper_id "
        "WHERE p.author_name = :username "
        "ORDER BY n.id DESC "
        "LIMIT :limit OFFSET :offset"
    ), {"username": current_user["name"], "limit": limit, "offset": offset}).mappings().all()

    result = []
    for r in rows:
        item = dict(r)
        item["read"] = item.pop("read_at") is not None
        result.append(item)

    return {"notifications": result}


# ── 2. PATCH /notifications/{id}/read — require_auth ─────────────────────────

@router.patch("/notifications/{id}/read")
async def mark_notification_read(
    id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    # Verify ownership: notification's paper must belong to current user
    notif = db.execute(text(
        "SELECT n.id, n.read_at, p.author_name "
        "FROM `#__eaiou_notifications` n "
        "JOIN `#__eaiou_papers` p ON p.id = n.paper_id "
        "WHERE n.id = :nid"
    ), {"nid": id}).mappings().first()

    if notif is None:
        raise HTTPException(status_code=404, detail="Notification not found.")

    if notif["author_name"] != current_user["name"]:
        groups = current_user.get("groups", [])
        if not ({"admin", "editor"} & set(groups)):
            raise HTTPException(status_code=403, detail="Access denied.")

    now = datetime.now(timezone.utc)
    result = db.execute(text(
        "UPDATE `#__eaiou_notifications` SET read_at = :now WHERE id = :nid"
    ), {"now": now, "nid": id})
    db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Notification not found.")

    log_api_call(
        db, f"/api/v1/notifications/{id}/read", "PATCH",
        hashlib.sha256(str(id).encode()).hexdigest(), 200,
    )

    return {"id": id, "read": True}


# ── 3. GET /admin/notifications/preview — require_admin ──────────────────────

@router.get("/admin/notifications/preview")
async def admin_notification_preview(
    template: str,
    paper_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    paper = db.execute(text(
        "SELECT id, title FROM `#__eaiou_papers` WHERE id = :pid AND tombstone_state IS NULL"
    ), {"pid": paper_id}).mappings().first()
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found.")

    user = db.execute(text(
        "SELECT id, username, display_name FROM `#__eaiou_users` WHERE id = :uid"
    ), {"uid": user_id}).mappings().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    user_name = user["display_name"] or user["username"]
    paper_title = paper["title"]
    due_date = "TBD"

    templates_map = {
        "mail_reviewer_invite_reminder": (
            f"Dear {user_name}, you have been invited to review paper: "
            f"{paper_title}. Due: {due_date}."
        ),
        "mail_paper_accepted": (
            f"Dear {user_name}, your paper '{paper_title}' has been accepted."
        ),
        "mail_paper_rejected": (
            f"Dear {user_name}, your paper '{paper_title}' was not accepted at this time."
        ),
        "mail_author_revision_reminder": (
            f"Dear {user_name}, revisions are requested for '{paper_title}'."
        ),
    }

    if template not in templates_map:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown template '{template}'. "
                   f"Valid: {list(templates_map.keys())}",
        )

    return {
        "template": template,
        "rendered": templates_map[template],
    }
