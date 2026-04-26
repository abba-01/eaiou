"""
eaiou — Auth router
DB-backed login: queries #__eaiou_users, verifies bcrypt hash.
CSRF token generated on GET, validated on POST.
Rate limiting: 5 attempts per IP per 60 seconds.
"""
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone

from ..database import get_db
from ..security import verify_password, get_csrf_token, validate_csrf, check_login_rate_limit, record_login_attempt

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    if request.session.get("user"):
        return RedirectResponse(url="/", status_code=302)
    csrf_token = get_csrf_token(request)
    return templates.TemplateResponse(
        request, "auth/login.html", {"error": None, "csrf_token": csrf_token}
    )


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else "unknown"
    check_login_rate_limit(ip)
    validate_csrf(request, csrf_token)

    row = db.execute(
        text("SELECT id, username, password_hash, active FROM `#__eaiou_users` WHERE username = :u"),
        {"u": username},
    ).mappings().first()

    if row and row["active"] and verify_password(password, row["password_hash"]):
        db.execute(
            text("UPDATE `#__eaiou_users` SET last_login_at = :now WHERE id = :id"),
            {"now": datetime.now(timezone.utc).replace(tzinfo=None), "id": row["id"]},
        )
        db.commit()
        request.session["user"] = row["username"]
        next_url = request.query_params.get("next", "/")
        return RedirectResponse(url=next_url, status_code=303)

    record_login_attempt(ip)
    csrf_token = get_csrf_token(request)
    return templates.TemplateResponse(
        request, "auth/login.html",
        {"error": "Invalid username or password.", "csrf_token": csrf_token},
        status_code=401,
    )


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)
