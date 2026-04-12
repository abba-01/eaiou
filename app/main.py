"""
eaiou CMS — Main Application
Observer-preserving full-context peer-review journal platform.
Author: Eric D. Martin | ORCID 0009-0006-5944-1742
"""

import os
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.exceptions import HTTPException
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from contextlib import asynccontextmanager

from .database import Base, get_db
from .deps import get_current_user, get_user_from_session
from .routers import papers, auth, author, editor, intelligence, api, intellid, report, admin, oauth
from .middleware.temporal_blindness import TemporalBlindnessMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Idempotent schema migrations — safe to run on every start
    from .database import engine
    with engine.begin() as conn:
        # BF-1: q_signal column was missing from python_cms_migration_001
        conn.execute(text(
            "ALTER TABLE `#__eaiou_papers` "
            "ADD COLUMN IF NOT EXISTS `q_signal` DECIMAL(7,4) DEFAULT NULL"
        ))
        # P2: rejection fields
        for col_ddl in [
            "ALTER TABLE `#__eaiou_papers` ADD COLUMN IF NOT EXISTS `rejection_reason_code` VARCHAR(64) DEFAULT NULL",
            "ALTER TABLE `#__eaiou_papers` ADD COLUMN IF NOT EXISTS `rejection_notes` TEXT DEFAULT NULL",
            "ALTER TABLE `#__eaiou_papers` ADD COLUMN IF NOT EXISTS `rejection_public_summary` TEXT DEFAULT NULL",
        ]:
            try:
                conn.execute(text(col_ddl))
            except Exception:
                pass  # Column already exists on older MariaDB without IF NOT EXISTS support
        # F2-A: Revision tracking table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS `#__eaiou_revisions` (
                id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                paper_id       INT UNSIGNED NOT NULL,
                round          INT DEFAULT 1,
                instructions   TEXT,
                due_at         DATE DEFAULT NULL,
                requested_at   DATETIME NOT NULL,
                resubmitted_at DATETIME DEFAULT NULL,
                FOREIGN KEY (paper_id) REFERENCES `#__eaiou_papers`(id)
            )
        """))
        # F2-D: Author notifications table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS `#__eaiou_notifications` (
                id         INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                paper_id   INT UNSIGNED NOT NULL,
                type       VARCHAR(64) NOT NULL,
                message    TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                read_at    DATETIME DEFAULT NULL,
                FOREIGN KEY (paper_id) REFERENCES `#__eaiou_papers`(id)
            )
        """))
        # ── Users / groups ────────────────────────────────────────────────────
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS `#__eaiou_users` (
                `id`            INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                `username`      VARCHAR(64) NOT NULL UNIQUE,
                `email`         VARCHAR(255) DEFAULT NULL,
                `password_hash` VARCHAR(255) NOT NULL,
                `display_name`  VARCHAR(255) DEFAULT NULL,
                `active`        TINYINT(1) NOT NULL DEFAULT 1,
                `created_at`    DATETIME NOT NULL,
                `last_login_at` DATETIME DEFAULT NULL,
                INDEX `idx_username` (`username`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS `#__eaiou_groups` (
                `id`          INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                `name`        VARCHAR(64) NOT NULL UNIQUE,
                `description` VARCHAR(255) DEFAULT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS `#__eaiou_user_groups` (
                `user_id`  INT UNSIGNED NOT NULL,
                `group_id` INT UNSIGNED NOT NULL,
                PRIMARY KEY (`user_id`, `group_id`),
                FOREIGN KEY (`user_id`)  REFERENCES `#__eaiou_users`(`id`)  ON DELETE CASCADE,
                FOREIGN KEY (`group_id`) REFERENCES `#__eaiou_groups`(`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        # Seed default groups (idempotent)
        for _gname, _gdesc in [
            ("admin",  "Full platform administration"),
            ("editor", "Paper queue and review management"),
            ("author", "Paper submission and workspace"),
        ]:
            conn.execute(text(
                "INSERT IGNORE INTO `#__eaiou_groups` (name, description) VALUES (:n, :d)"
            ), {"n": _gname, "d": _gdesc})
        # Seed admin user from env (only if username not already in table)
        _admin_user = os.getenv("ADMIN_USER", "mae")
        _admin_pass = os.getenv("ADMIN_PASS", "")
        if _admin_pass:
            import bcrypt as _bcrypt
            from datetime import datetime as _dt
            _hashed = _bcrypt.hashpw(_admin_pass.encode("utf-8"), _bcrypt.gensalt(12)).decode("utf-8")
            conn.execute(text("""
                INSERT IGNORE INTO `#__eaiou_users`
                    (username, password_hash, display_name, active, created_at)
                VALUES (:u, :h, :d, 1, :now)
            """), {"u": _admin_user, "h": _hashed, "d": _admin_user.title(), "now": _dt.utcnow()})
            conn.execute(text("""
                INSERT IGNORE INTO `#__eaiou_user_groups` (user_id, group_id)
                SELECT u.id, g.id FROM `#__eaiou_users` u, `#__eaiou_groups` g
                WHERE u.username = :u AND g.name = 'admin'
            """), {"u": _admin_user})
        # ── User file drawer ──────────────────────────────────────────────────
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS `#__eaiou_user_files` (
                `id`             INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                `user_id`        INT UNSIGNED NOT NULL,
                `original_name`  VARCHAR(255) NOT NULL,
                `stored_path`    VARCHAR(512) NOT NULL,
                `mime_type`      VARCHAR(128) NOT NULL,
                `file_size`      INT UNSIGNED NOT NULL,
                `sha256`         CHAR(64) NOT NULL,
                `extracted_text` LONGTEXT DEFAULT NULL,
                `uploaded_at`    DATETIME NOT NULL,
                `deleted_at`     DATETIME DEFAULT NULL,
                INDEX `idx_user_files_active` (`user_id`, `deleted_at`),
                FOREIGN KEY (`user_id`) REFERENCES `#__eaiou_users`(`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        # Ensure UPLOAD_DIR exists at startup
        import pathlib as _pl, os as _os
        _pl.Path(_os.getenv("UPLOAD_DIR", "/var/eaiou/uploads")).mkdir(parents=True, exist_ok=True)
        # ── OAuth provider columns ────────────────────────────────────────────
        for _col_ddl in [
            "ALTER TABLE `#__eaiou_users` ADD COLUMN IF NOT EXISTS `orcid` VARCHAR(32) DEFAULT NULL",
            "ALTER TABLE `#__eaiou_users` ADD COLUMN IF NOT EXISTS `auth_provider` VARCHAR(32) NOT NULL DEFAULT 'local'",
            "ALTER TABLE `#__eaiou_users` ADD COLUMN IF NOT EXISTS `provider_sub` VARCHAR(255) DEFAULT NULL",
        ]:
            try:
                conn.execute(text(_col_ddl))
            except Exception:
                pass
        try:
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS `uq_user_provider` "
                "ON `#__eaiou_users` (`auth_provider`, `provider_sub`)"
            ))
        except Exception:
            pass
        try:
            conn.execute(text(
                "ALTER TABLE `#__eaiou_users` "
                "MODIFY COLUMN `password_hash` VARCHAR(255) DEFAULT NULL"
            ))
        except Exception:
            pass
        # M-005: Canonical archival tables
        import pathlib as _pl
        _m005 = _pl.Path(__file__).parent.parent / "schema" / "migration_005_canonical_tables.sql"
        if _m005.exists():
            _sql = _m005.read_text()
            for _stmt in [s.strip() for s in _sql.split(";") if s.strip() and not s.strip().startswith("--")]:
                try:
                    conn.execute(text(_stmt))
                except Exception as _e:
                    pass  # Idempotent — column/table already exists
    yield


app = FastAPI(
    title="eaiou",
    description="Observer-preserving full-context peer-review journal",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url=None,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "dev-secret-not-for-production"),
    session_cookie="eaiou_session",
    https_only=os.getenv("ENVIRONMENT", "development") == "production",
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(TemporalBlindnessMiddleware)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# ── Exception handlers ────────────────────────────────────────────────────────

@app.exception_handler(403)
async def forbidden(request: Request, exc: HTTPException):
    from fastapi.responses import RedirectResponse
    if get_user_from_session(request):
        return RedirectResponse(url="/", status_code=302)
    next_path = request.url.path
    return RedirectResponse(url=f"/auth/login?next={next_path}", status_code=302)


@app.exception_handler(404)
async def not_found(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        request, "errors/404.html",
        {"detail": exc.detail, "current_user": get_user_from_session(request)},
        status_code=404,
    )


@app.exception_handler(500)
async def server_error(request: Request, exc: Exception):
    return templates.TemplateResponse(
        request, "errors/500.html",
        {"current_user": get_user_from_session(request)},
        status_code=500,
    )


# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(papers.router)
app.include_router(auth.router)
app.include_router(author.router)
app.include_router(editor.router)
app.include_router(intelligence.router)
app.include_router(api.router)
app.include_router(intellid.router)
app.include_router(report.router)
app.include_router(admin.router)
app.include_router(oauth.router)


# ── Page routes ───────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    rows = db.execute(text(
        "SELECT id, title, abstract, author_name, orcid, status, "
        "ai_disclosure_level, q_overall FROM `#__eaiou_papers` "
        "WHERE status != 'draft' AND tombstone_state IS NULL "
        "ORDER BY q_overall IS NULL, q_overall DESC, paper_uuid ASC LIMIT 5"
    )).mappings().all()
    return templates.TemplateResponse(
        request, "index.html", {"papers": rows, "current_user": current_user}
    )


@app.get("/about", response_class=HTMLResponse)
async def about(request: Request, current_user=Depends(get_current_user)):
    return templates.TemplateResponse(
        request, "about.html", {"current_user": current_user}
    )


@app.get("/policy/temporal-blindness", response_class=HTMLResponse)
async def policy_temporal(request: Request, current_user=Depends(get_current_user)):
    return templates.TemplateResponse(
        request, "policy/temporal-blindness.html", {"current_user": current_user}
    )


@app.get("/policy/ai-disclosure", response_class=HTMLResponse)
async def policy_ai(request: Request, current_user=Depends(get_current_user)):
    return templates.TemplateResponse(
        request, "policy/ai-disclosure.html", {"current_user": current_user}
    )


@app.get("/policy/open-access", response_class=HTMLResponse)
async def policy_open(request: Request, current_user=Depends(get_current_user)):
    return templates.TemplateResponse(
        request, "policy/open-access.html", {"current_user": current_user}
    )


@app.get("/policy/intelligence-blindness", response_class=HTMLResponse)
async def policy_intelligence(request: Request, current_user=Depends(get_current_user)):
    return templates.TemplateResponse(
        request, "policy/intelligence-blindness.html", {"current_user": current_user}
    )


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
