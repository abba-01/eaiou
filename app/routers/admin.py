"""
eaiou — Admin router
User and group management. Admin group required for all routes.
"""
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone

from ..database import get_db
from ..deps import require_admin
from ..security import hash_password, get_csrf_token, validate_csrf

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")


def _get_groups(db: Session) -> list:
    return db.execute(
        text("SELECT id, name, description FROM `#__eaiou_groups` ORDER BY name")
    ).mappings().all()


def _get_users(db: Session) -> list:
    rows = db.execute(text("""
        SELECT u.id, u.username, u.display_name, u.email, u.active, u.created_at, u.last_login_at,
               GROUP_CONCAT(g.name ORDER BY g.name SEPARATOR ',') AS groups
        FROM `#__eaiou_users` u
        LEFT JOIN `#__eaiou_user_groups` ug ON ug.user_id = u.id
        LEFT JOIN `#__eaiou_groups` g ON g.id = ug.group_id
        GROUP BY u.id ORDER BY u.username
    """)).mappings().all()
    return [dict(r) | {"group_list": (r["groups"] or "").split(",") if r["groups"] else []} for r in rows]


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    user_count = db.execute(text("SELECT COUNT(*) FROM `#__eaiou_users`")).scalar()
    group_count = db.execute(text("SELECT COUNT(*) FROM `#__eaiou_groups`")).scalar()
    return templates.TemplateResponse(
        request, "admin/dashboard.html",
        {"current_user": current_user, "user_count": user_count, "group_count": group_count},
    )


# ── User list ─────────────────────────────────────────────────────────────────

@router.get("/users", response_class=HTMLResponse)
async def user_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return templates.TemplateResponse(
        request, "admin/users.html",
        {"current_user": current_user, "users": _get_users(db)},
    )


# ── Create user ───────────────────────────────────────────────────────────────

@router.get("/users/new", response_class=HTMLResponse)
async def user_new_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    return templates.TemplateResponse(
        request, "admin/user_form.html",
        {
            "current_user": current_user,
            "user": None,
            "all_groups": _get_groups(db),
            "user_groups": [],
            "error": None,
            "csrf_token": get_csrf_token(request),
        },
    )


@router.post("/users/new")
async def user_create(
    request: Request,
    username: str = Form(...),
    display_name: str = Form(""),
    email: str = Form(""),
    password: str = Form(...),
    groups: list[int] = Form(default=[]),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    validate_csrf(request, csrf_token)
    username = username.strip().lower()
    if not username or not password:
        return templates.TemplateResponse(
            request, "admin/user_form.html",
            {
                "current_user": current_user, "user": None,
                "all_groups": _get_groups(db), "user_groups": groups,
                "error": "Username and password are required.",
                "csrf_token": get_csrf_token(request),
            }, status_code=422,
        )
    existing = db.execute(
        text("SELECT id FROM `#__eaiou_users` WHERE username = :u"), {"u": username}
    ).scalar()
    if existing:
        return templates.TemplateResponse(
            request, "admin/user_form.html",
            {
                "current_user": current_user, "user": None,
                "all_groups": _get_groups(db), "user_groups": groups,
                "error": f"Username '{username}' is already taken.",
                "csrf_token": get_csrf_token(request),
            }, status_code=422,
        )
    db.execute(text("""
        INSERT INTO `#__eaiou_users`
            (username, email, password_hash, display_name, active, created_at)
        VALUES (:u, :e, :h, :d, 1, :now)
    """), {
        "u": username, "e": email.strip() or None,
        "h": hash_password(password),
        "d": display_name.strip() or username.title(),
        "now": datetime.now(timezone.utc).replace(tzinfo=None),
    })
    db.commit()
    user_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
    for gid in groups:
        db.execute(
            text("INSERT IGNORE INTO `#__eaiou_user_groups` (user_id, group_id) VALUES (:u, :g)"),
            {"u": user_id, "g": gid},
        )
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=303)


# ── Edit user ─────────────────────────────────────────────────────────────────

@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
async def user_edit_form(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    user = db.execute(
        text("SELECT id, username, display_name, email, active FROM `#__eaiou_users` WHERE id = :id"),
        {"id": user_id},
    ).mappings().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user_groups = [r["group_id"] for r in db.execute(
        text("SELECT group_id FROM `#__eaiou_user_groups` WHERE user_id = :id"),
        {"id": user_id},
    ).mappings().all()]
    return templates.TemplateResponse(
        request, "admin/user_form.html",
        {
            "current_user": current_user,
            "user": dict(user),
            "all_groups": _get_groups(db),
            "user_groups": user_groups,
            "error": None,
            "csrf_token": get_csrf_token(request),
        },
    )


@router.post("/users/{user_id}/edit")
async def user_update(
    request: Request,
    user_id: int,
    display_name: str = Form(""),
    email: str = Form(""),
    password: str = Form(""),
    active: str = Form("off"),
    groups: list[int] = Form(default=[]),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    validate_csrf(request, csrf_token)
    updates = {
        "d": display_name.strip() or None,
        "e": email.strip() or None,
        "a": 1 if active == "on" else 0,
        "id": user_id,
    }
    if password.strip():
        db.execute(
            text("UPDATE `#__eaiou_users` SET display_name=:d, email=:e, active=:a, password_hash=:h WHERE id=:id"),
            updates | {"h": hash_password(password.strip())},
        )
    else:
        db.execute(
            text("UPDATE `#__eaiou_users` SET display_name=:d, email=:e, active=:a WHERE id=:id"),
            updates,
        )
    db.execute(text("DELETE FROM `#__eaiou_user_groups` WHERE user_id = :id"), {"id": user_id})
    for gid in groups:
        db.execute(
            text("INSERT IGNORE INTO `#__eaiou_user_groups` (user_id, group_id) VALUES (:u, :g)"),
            {"u": user_id, "g": gid},
        )
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=303)


# ── Delete user ───────────────────────────────────────────────────────────────

@router.post("/users/{user_id}/delete")
async def user_delete(
    request: Request,
    user_id: int,
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    validate_csrf(request, csrf_token)
    if current_user["id"] == user_id:
        return RedirectResponse(url="/admin/users?error=self", status_code=303)
    db.execute(text("DELETE FROM `#__eaiou_users` WHERE id = :id"), {"id": user_id})
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=303)
