"""
eaiou — Shared FastAPI dependencies
"""
from fastapi import Request, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from .database import get_db


def get_current_user(request: Request, db: Session = Depends(get_db)):
    """
    Load the logged-in user from DB using session username.
    Returns dict with id, name, display, initials, groups — or None if not logged in.
    """
    username = request.session.get("user")
    if not username:
        return None
    row = db.execute(
        text("SELECT id, username, display_name, active FROM `#__eaiou_users` WHERE username = :u"),
        {"u": username},
    ).mappings().first()
    if not row or not row["active"]:
        request.session.clear()
        return None
    groups = [
        r["name"] for r in db.execute(
            text("""
                SELECT g.name FROM `#__eaiou_groups` g
                JOIN `#__eaiou_user_groups` ug ON ug.group_id = g.id
                JOIN `#__eaiou_users` u ON u.id = ug.user_id
                WHERE u.username = :u
            """),
            {"u": username},
        ).mappings().all()
    ]
    display = row["display_name"] or row["username"]
    return {
        "id":       row["id"],
        "name":     row["username"],
        "display":  display,
        "initials": display[:2].upper(),
        "groups":   groups,
    }


def get_user_from_session(request: Request) -> dict | None:
    """Lightweight session-only read — used in error handlers where DB is unavailable."""
    username = request.session.get("user")
    if not username:
        return None
    return {"name": username, "initials": username[:2].upper(), "groups": []}


def require_admin(current_user=Depends(get_current_user)) -> dict:
    if not current_user or "admin" not in current_user.get("groups", []):
        raise HTTPException(status_code=403, detail="Admin access required.")
    return current_user


def require_editor(current_user=Depends(get_current_user)) -> dict:
    groups = current_user.get("groups", []) if current_user else []
    if not current_user or not ({"admin", "editor"} & set(groups)):
        raise HTTPException(status_code=403, detail="Editor access required.")
    return current_user


def require_author(current_user=Depends(get_current_user)) -> dict:
    if not current_user or not ({"author", "admin", "editor"} & set(current_user.get("groups", []))):
        raise HTTPException(status_code=403, detail="Author access required.")
    return current_user

def require_reviewer(current_user=Depends(get_current_user)) -> dict:
    if not current_user or not ({"reviewer", "editor", "eic", "admin"} & set(current_user.get("groups", []))):
        raise HTTPException(status_code=403, detail="Reviewer access required.")
    return current_user

def require_eic(current_user=Depends(get_current_user)) -> dict:
    if not current_user or not ({"eic", "admin"} & set(current_user.get("groups", []))):
        raise HTTPException(status_code=403, detail="EIC access required.")
    return current_user

def require_auth(current_user=Depends(get_current_user)) -> dict:
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return current_user

def optional_auth(current_user=Depends(get_current_user)):
    """Returns user or None — for endpoints that vary response by auth level."""
    return current_user
