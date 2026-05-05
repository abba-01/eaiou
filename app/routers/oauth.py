"""
eaiou — OAuth login
Google OAuth 2.0 (OpenID Connect) and ORCID OAuth 2.0.
No new library dependency — uses httpx (already installed).
State parameter stored in session provides CSRF protection.
On success, sets request.session["user"] = username, exactly like password login.
New users are auto-created and assigned to the "author" group.
"""
import os
import secrets
from datetime import datetime, timezone
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db

router = APIRouter(prefix="/auth", tags=["oauth"])

SITE_URL             = os.getenv("SITE_URL", "https://eaiou.org").rstrip("/")
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
ORCID_CLIENT_ID      = os.getenv("ORCID_CLIENT_ID", "")
ORCID_CLIENT_SECRET  = os.getenv("ORCID_CLIENT_SECRET", "")


# ── Shared helpers ────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _find_user(db: Session, auth_provider: str, provider_sub: str):
    """Return existing user row for this provider identity, or None."""
    return db.execute(
        text("SELECT id, username, active FROM `#__eaiou_users` "
             "WHERE auth_provider = :p AND provider_sub = :s"),
        {"p": auth_provider, "s": provider_sub},
    ).mappings().first()


def _create_oauth_user(
    db: Session,
    *,
    username: str,
    display_name: str,
    email: str | None,
    orcid: str | None,
    auth_provider: str,
    provider_sub: str,
) -> int:
    """
    Insert new user + assign author group. Returns new user id.
    Raises HTTPException 409 if username already taken by a different provider.
    """
    existing = db.execute(
        text("SELECT id FROM `#__eaiou_users` WHERE username = :u"),
        {"u": username},
    ).mappings().first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                f"An account with the username '{username}' already exists. "
                "If this is your account, sign in with your password, "
                "or contact editor@eaiou.org."
            ),
        )
    db.execute(text("""
        INSERT INTO `#__eaiou_users`
            (username, email, password_hash, display_name, orcid,
             auth_provider, provider_sub, active, created_at)
        VALUES (:u, :e, NULL, :d, :o, :p, :s, 1, :now)
    """), {
        "u": username, "e": email, "d": display_name,
        "o": orcid, "p": auth_provider, "s": provider_sub, "now": _now(),
    })
    db.commit()
    user_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
    # Auto-assign author group
    db.execute(text("""
        INSERT IGNORE INTO `#__eaiou_user_groups` (user_id, group_id)
        SELECT :uid, g.id FROM `#__eaiou_groups` g WHERE g.name = 'author'
    """), {"uid": user_id})
    db.commit()
    return user_id


def _update_last_login(db: Session, user_id: int) -> None:
    db.execute(
        text("UPDATE `#__eaiou_users` SET last_login_at = :now WHERE id = :id"),
        {"now": _now(), "id": user_id},
    )
    db.commit()


def _complete_login(request: Request, username: str) -> RedirectResponse:
    """Set session cookie and redirect to ?next or home."""
    request.session["user"] = username
    next_url = request.query_params.get("next") or request.session.pop("oauth_next", "/")
    return RedirectResponse(url=next_url, status_code=303)


# ── Google ────────────────────────────────────────────────────────────────────

GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO  = "https://www.googleapis.com/oauth2/v3/userinfo"


@router.get("/login/google")
async def login_google(request: Request):
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(503, "Google login is not configured.")
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"]    = state
    request.session["oauth_provider"] = "google"
    if "next" in request.query_params:
        request.session["oauth_next"] = request.query_params["next"]
    params = urlencode({
        "client_id":     GOOGLE_CLIENT_ID,
        "redirect_uri":  f"{SITE_URL}/auth/callback/google",
        "response_type": "code",
        "scope":         "openid email profile",
        "state":         state,
        "access_type":   "online",
        "prompt":        "select_account",
    })
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{params}", status_code=302)


@router.get("/callback/google")
async def callback_google(request: Request, db: Session = Depends(get_db)):
    # Provider-reported error (e.g. user denied access)
    error = request.query_params.get("error")
    if error:
        return RedirectResponse(f"/auth/login?error={error}", status_code=302)

    code  = request.query_params.get("code", "")
    state = request.query_params.get("state", "")

    if not state or state != request.session.pop("oauth_state", None):
        raise HTTPException(403, "OAuth state mismatch. Please try signing in again.")
    if request.session.pop("oauth_provider", None) != "google":
        raise HTTPException(403, "Provider mismatch.")

    # Exchange authorization code for tokens
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(GOOGLE_TOKEN_URL, data={
            "code":          code,
            "client_id":     GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri":  f"{SITE_URL}/auth/callback/google",
            "grant_type":    "authorization_code",
        })
    if token_resp.status_code != 200:
        raise HTTPException(502, "Failed to exchange Google authorization code.")
    token_data = token_resp.json()

    # Fetch user profile from Google
    async with httpx.AsyncClient() as client:
        info_resp = await client.get(
            GOOGLE_USERINFO,
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
    if info_resp.status_code != 200:
        raise HTTPException(502, "Failed to fetch Google user profile.")
    info = info_resp.json()

    sub          = info.get("sub", "")
    email        = info.get("email", "")
    display_name = info.get("name") or info.get("given_name") or email.split("@")[0]

    if not sub:
        raise HTTPException(502, "Google did not return a user identifier.")

    # Find or create
    row = _find_user(db, "google", sub)
    if row:
        if not row["active"]:
            return RedirectResponse("/auth/login?error=inactive", status_code=302)
        _update_last_login(db, row["id"])
        return _complete_login(request, row["username"])

    # New user — use email as username (already globally unique via Google)
    username = email[:64] if email else f"google_{sub[:16]}"
    _create_oauth_user(
        db, username=username, display_name=display_name,
        email=email, orcid=None,
        auth_provider="google", provider_sub=sub,
    )
    return _complete_login(request, username)


# ── ORCID ─────────────────────────────────────────────────────────────────────

ORCID_AUTH_URL  = "https://orcid.org/oauth/authorize"
ORCID_TOKEN_URL = "https://orcid.org/oauth/token"


@router.get("/login/orcid")
async def login_orcid(request: Request):
    if not ORCID_CLIENT_ID:
        raise HTTPException(503, "ORCID login is not configured.")
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"]    = state
    request.session["oauth_provider"] = "orcid"
    if "next" in request.query_params:
        request.session["oauth_next"] = request.query_params["next"]
    params = urlencode({
        "client_id":     ORCID_CLIENT_ID,
        "redirect_uri":  f"{SITE_URL}/auth/callback/orcid",
        "response_type": "code",
        "scope":         "/authenticate",
        "state":         state,
    })
    return RedirectResponse(f"{ORCID_AUTH_URL}?{params}", status_code=302)


@router.get("/callback/orcid")
async def callback_orcid(request: Request, db: Session = Depends(get_db)):
    error = request.query_params.get("error")
    if error:
        return RedirectResponse(f"/auth/login?error={error}", status_code=302)

    code  = request.query_params.get("code", "")
    state = request.query_params.get("state", "")

    if not state or state != request.session.pop("oauth_state", None):
        raise HTTPException(403, "OAuth state mismatch. Please try signing in again.")
    if request.session.pop("oauth_provider", None) != "orcid":
        raise HTTPException(403, "Provider mismatch.")

    # Exchange code — ORCID returns orcid iD and name directly in the token response
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            ORCID_TOKEN_URL,
            data={
                "code":          code,
                "client_id":     ORCID_CLIENT_ID,
                "client_secret": ORCID_CLIENT_SECRET,
                "redirect_uri":  f"{SITE_URL}/auth/callback/orcid",
                "grant_type":    "authorization_code",
            },
            headers={"Accept": "application/json"},
        )
    if token_resp.status_code != 200:
        raise HTTPException(502, "Failed to exchange ORCID authorization code.")
    token_data = token_resp.json()

    orcid_id     = token_data.get("orcid", "")
    display_name = token_data.get("name", "")

    if not orcid_id:
        raise HTTPException(502, "ORCID did not return an iD.")

    # Find or create — username IS the ORCID iD (e.g. 0009-0006-5944-1742)
    row = _find_user(db, "orcid", orcid_id)
    if row:
        if not row["active"]:
            return RedirectResponse("/auth/login?error=inactive", status_code=302)
        _update_last_login(db, row["id"])
        return _complete_login(request, row["username"])

    _create_oauth_user(
        db, username=orcid_id, display_name=display_name or orcid_id,
        email=None, orcid=orcid_id,
        auth_provider="orcid", provider_sub=orcid_id,
    )
    return _complete_login(request, orcid_id)
