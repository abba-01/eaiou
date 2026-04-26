"""
eaiou — Security utilities
Password hashing (bcrypt direct) and CSRF token management.
Uses bcrypt directly rather than passlib to avoid passlib/bcrypt-5.x incompatibility.
"""
import secrets
import time
import bcrypt
from fastapi import Request, HTTPException

_ROUNDS = 12

# ── Password ──────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(_ROUNDS)).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

# ── CSRF ──────────────────────────────────────────────────────────────────────

def get_csrf_token(request: Request) -> str:
    """Return existing CSRF token from session, or generate and store a new one."""
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_hex(32)
        request.session["csrf_token"] = token
    return token

def validate_csrf(request: Request, submitted: str) -> None:
    """Raise 403 if submitted CSRF token doesn't match session token."""
    session_token = request.session.get("csrf_token")
    if not session_token or not submitted:
        raise HTTPException(status_code=403, detail="CSRF token missing.")
    if not secrets.compare_digest(session_token, submitted):
        raise HTTPException(status_code=403, detail="CSRF validation failed.")

# ── Login rate limiting (in-memory, per IP) ───────────────────────────────────

_login_attempts: dict[str, list[float]] = {}
_MAX_ATTEMPTS = 5
_WINDOW_SECONDS = 60

def check_login_rate_limit(ip: str) -> None:
    """Raise 429 if IP has exceeded 5 login attempts in the last 60 seconds."""
    now = time.monotonic()
    attempts = [t for t in _login_attempts.get(ip, []) if now - t < _WINDOW_SECONDS]
    _login_attempts[ip] = attempts
    if len(attempts) >= _MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many login attempts. Wait 60 seconds.")

def record_login_attempt(ip: str) -> None:
    now = time.monotonic()
    _login_attempts.setdefault(ip, []).append(now)
