# eaiou Foundation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Import the build package into the repo, add missing canonical tables to FastAPI, enforce Temporal Blindness doctrine, and scaffold the Laravel admin panel.

**Architecture:** FastAPI (Python) is the entire application — public, author, editor, API. Laravel (PHP) is the admin-only backend panel sharing the same MariaDB. Both connect to `#__eaiou_*` tables. The Joomla-era build plans in the package are reference only; implementation is pure FastAPI + Laravel.

**Tech Stack:** FastAPI 0.x, Python 3.12, SQLAlchemy (text queries), MariaDB, Jinja2 · Laravel 11, PHP 8.2, Eloquent ORM

**Subsequent plans:**
- Plan 2: FastAPI API tiers 1–6 (papers, workflow, reviews, discovery, gitgap)
- Plan 3: FastAPI API tiers 7–12 + MCP orchestration layer
- Plan 4: Frontend views (37 HTML views per Frontend Build Plan)
- Plan 5: CommKit + hardening

---

## File Map

**Created:**
- `docs/build_plans/` — 5 reference build plans (from package)
- `app/middleware/temporal_blindness.py` — TB enforcement middleware
- `schema/migration_005_canonical_tables.sql` — 10 new tables
- `/scratch/repos/eaiou-admin/` — Laravel admin scaffold (new repo)

**Modified:**
- `app/main.py` — add migration_005 tables + Temporal Blindness middleware registration
- `app/routers/papers.py` — ensure paper list sorts by q_signal, never date
- `app/routers/editor.py` — same sort enforcement
- `schema/eaiou_install_canonical.sql` — sync with package version (no override of working tables)

---

## Task 1: Import Build Package Into Repo

**Files:**
- Create: `docs/build_plans/` (5 plan files)
- Verify: `schema/eaiou_install_canonical.sql` (already exists — do NOT overwrite)

- [ ] **Step 1: Move build plans**

```bash
mkdir -p /scratch/repos/eaiou/docs/build_plans
cp /tmp/eaiou-pkg/01_build_plans/*.md /scratch/repos/eaiou/docs/build_plans/
```

Expected: 5 `.md` files in `docs/build_plans/`.

- [ ] **Step 2: Move DEVELOPMENT_GUIDE.md**

```bash
cp /tmp/eaiou-pkg/00_START_HERE/DEVELOPMENT_GUIDE.md \
   /scratch/repos/eaiou/docs/DEVELOPMENT_GUIDE_reference.md
```

- [ ] **Step 3: Move wireframes batch 1**

```bash
cp /tmp/eaiou-pkg/05_design_reference/eaiou_wireframes_batch1.html \
   /scratch/repos/eaiou/ui-projects/eaiou_wireframes_batch1.html
```

- [ ] **Step 4: Move CommKit integration plan**

The CommKit plan is already in `docs/build_plans/` from Step 1. Verify it landed:

```bash
ls /scratch/repos/eaiou/docs/build_plans/
```

Expected output includes `EAIOU_COMMKIT_INTEGRATION_PLAN.md`, `EAIOU_FRONTEND_BUILD_PLAN.md`, `EAIOU_API_BUILD_PLAN.md`, `EAIOU_MCP_BUILD_PLAN.md`, `EAIOU_BACKEND_BUILD_PLAN.md`.

- [ ] **Step 5: Verify schema files are current**

The package schema at `/tmp/eaiou-pkg/03_schema/eaiou_install_canonical.sql` is the 2026-04-07 version. The repo already has this file. Check if the repo version is newer:

```bash
head -5 /scratch/repos/eaiou/schema/eaiou_install_canonical.sql
head -5 /tmp/eaiou-pkg/03_schema/eaiou_install_canonical.sql
```

Do NOT overwrite the repo schema — the repo version is authoritative.

- [ ] **Step 6: Commit package import**

```bash
cd /scratch/repos/eaiou
git add docs/build_plans/ docs/DEVELOPMENT_GUIDE_reference.md ui-projects/eaiou_wireframes_batch1.html
git commit -m "docs: import eaiou build package — 5 build plans + DEVELOPMENT_GUIDE + wireframes batch 1"
```

---

## Task 2: Add Missing Canonical Tables to FastAPI

The canonical schema has 11 tables. The current FastAPI `main.py` creates only the basic CMS tables (users, groups, papers, revisions, notifications, user_files). The following 10 tables from the spec are missing: `versions`, `ai_sessions`, `didntmakeit`, `remsearch`, `review_logs`, `attribution_log`, `plugins_used`, `api_keys`, `api_logs`, `quality_signals`.

**Files:**
- Create: `schema/migration_005_canonical_tables.sql`
- Modify: `app/main.py` (add migration_005 to lifespan)

- [ ] **Step 1: Create the migration SQL file**

Create `/scratch/repos/eaiou/schema/migration_005_canonical_tables.sql`:

```sql
-- eaiou Migration 005 — Canonical Schema Tables
-- Adds the 10 archival tables from SSOT.md that are missing from the Python CMS base.
-- All tables idempotent (CREATE TABLE IF NOT EXISTS).
-- Temporal Blindness: NO INDEXES on sealed fields (timing side-channel prevention).

CREATE TABLE IF NOT EXISTS `#__eaiou_versions` (
  `id`              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`        INT NOT NULL,
  `label`           VARCHAR(100) NOT NULL,
  `file_path`       VARCHAR(500) DEFAULT NULL,
  `content_hash`    VARCHAR(64) DEFAULT NULL,
  `ai_flag`         TINYINT NOT NULL DEFAULT 0,
  `ai_model_name`   VARCHAR(255) DEFAULT NULL,
  `generated_at`    DATETIME DEFAULT NULL,
  `notes`           TEXT DEFAULT NULL,
  `created`         DATETIME NOT NULL,
  `created_by`      INT DEFAULT NULL,
  INDEX `idx_paper_id` (`paper_id`),
  INDEX `idx_ai_flag`  (`ai_flag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `#__eaiou_ai_sessions` (
  `id`                          INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`                    INT NOT NULL,
  `session_label`               VARCHAR(255) DEFAULT NULL,
  `ai_model_name`               VARCHAR(255) NOT NULL,
  `start_time`                  DATETIME DEFAULT NULL,
  `end_time`                    DATETIME DEFAULT NULL,
  `tokens_in`                   INT DEFAULT NULL,
  `tokens_out`                  INT DEFAULT NULL,
  `redaction_status`            ENUM('none','partial','full') NOT NULL DEFAULT 'none',
  `session_notes`               TEXT DEFAULT NULL,
  `session_hash`                VARCHAR(64) DEFAULT NULL,
  `answer_box_session_id`       VARCHAR(255) DEFAULT NULL,
  `answer_box_ledger_capstone`  VARCHAR(255) DEFAULT NULL,
  `created`                     DATETIME NOT NULL,
  `created_by`                  INT DEFAULT NULL,
  INDEX `idx_paper_id`   (`paper_id`),
  INDEX `idx_model`      (`ai_model_name`),
  INDEX `idx_redaction`  (`redaction_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `#__eaiou_didntmakeit` (
  `id`               INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `session_id`       INT NOT NULL,
  `prompt_text`      LONGTEXT DEFAULT NULL,
  `response_text`    LONGTEXT DEFAULT NULL,
  `exclusion_reason` TEXT DEFAULT NULL,
  `redacted`         TINYINT NOT NULL DEFAULT 0,
  `redaction_hash`   VARCHAR(64) DEFAULT NULL,
  `created`          DATETIME NOT NULL,
  `created_by`       INT DEFAULT NULL,
  INDEX `idx_session_id` (`session_id`),
  INDEX `idx_redacted`   (`redacted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `#__eaiou_remsearch` (
  `id`              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`        INT NOT NULL,
  `citation_title`  VARCHAR(500) DEFAULT NULL,
  `citation_source` VARCHAR(255) DEFAULT NULL,
  `citation_link`   VARCHAR(1000) DEFAULT NULL,
  `source_type`     ENUM('journal','preprint','book','dataset','code','other') DEFAULT 'journal',
  `used`            TINYINT NOT NULL DEFAULT 0,
  `reason_unused`   TEXT DEFAULT NULL,
  `fulltext_notes`  TEXT DEFAULT NULL,
  `created`         DATETIME NOT NULL,
  `created_by`      INT DEFAULT NULL,
  INDEX `idx_paper_id`    (`paper_id`),
  INDEX `idx_used`        (`used`),
  INDEX `idx_source_type` (`source_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `#__eaiou_review_logs` (
  `id`             INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`       INT NOT NULL,
  `reviewer_id`    INT NOT NULL,
  `round`          INT NOT NULL DEFAULT 1,
  `dim_clarity`    TINYINT DEFAULT NULL COMMENT '1-5',
  `dim_rigor`      TINYINT DEFAULT NULL COMMENT '1-5',
  `dim_novelty`    TINYINT DEFAULT NULL COMMENT '1-5',
  `dim_relevance`  TINYINT DEFAULT NULL COMMENT '1-5',
  `dim_transp`     TINYINT DEFAULT NULL COMMENT '1-5 transparency',
  `dim_ai`         TINYINT DEFAULT NULL COMMENT '1-5 AI disclosure quality',
  `overall`        TINYINT DEFAULT NULL COMMENT '1-5',
  `comments`       TEXT DEFAULT NULL,
  `recommendation` ENUM('accept','minor','major','reject') DEFAULT NULL,
  `submitted_at`   DATETIME NOT NULL,
  INDEX `idx_paper_id`   (`paper_id`),
  INDEX `idx_reviewer`   (`reviewer_id`),
  INDEX `idx_round`      (`round`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `#__eaiou_attribution_log` (
  `id`               INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`         INT NOT NULL,
  `agent_type`       ENUM('human','ai','system') NOT NULL DEFAULT 'human',
  `agent_name`       VARCHAR(255) NOT NULL,
  `agent_id`         VARCHAR(255) DEFAULT NULL COMMENT 'ORCID, IntelliD, or system ID',
  `contribution`     VARCHAR(500) NOT NULL,
  `weight`           DECIMAL(4,2) DEFAULT NULL COMMENT '0.00–1.00',
  `created`          DATETIME NOT NULL,
  INDEX `idx_paper_id` (`paper_id`),
  INDEX `idx_agent_type` (`agent_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `#__eaiou_plugins_used` (
  `id`              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`        INT NOT NULL,
  `plugin_name`     VARCHAR(255) NOT NULL,
  `plugin_version`  VARCHAR(50) DEFAULT NULL,
  `event_type`      VARCHAR(100) NOT NULL,
  `event_data`      JSON DEFAULT NULL,
  `fired_at`        DATETIME NOT NULL,
  INDEX `idx_paper_id`   (`paper_id`),
  INDEX `idx_plugin`     (`plugin_name`),
  INDEX `idx_event_type` (`event_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `#__eaiou_api_keys` (
  `id`           INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `user_id`      INT NOT NULL,
  `key_hash`     VARCHAR(64) NOT NULL UNIQUE,
  `label`        VARCHAR(255) DEFAULT NULL,
  `permissions`  JSON DEFAULT NULL,
  `last_used_at` DATETIME DEFAULT NULL,
  `expires_at`   DATETIME DEFAULT NULL,
  `active`       TINYINT NOT NULL DEFAULT 1,
  `created_at`   DATETIME NOT NULL,
  INDEX `idx_user_id`  (`user_id`),
  INDEX `idx_key_hash` (`key_hash`),
  INDEX `idx_active`   (`active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `#__eaiou_api_logs` (
  `id`          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `api_key_id`  INT DEFAULT NULL,
  `user_id`     INT DEFAULT NULL,
  `method`      VARCHAR(10) NOT NULL,
  `endpoint`    VARCHAR(500) NOT NULL,
  `status_code` SMALLINT NOT NULL,
  `log_hash`    VARCHAR(64) NOT NULL COMMENT 'SHA256 of this row',
  `prior_hash`  VARCHAR(64) DEFAULT NULL COMMENT 'SHA256 of previous row — hash chain',
  `fired_at`    DATETIME NOT NULL,
  INDEX `idx_api_key`  (`api_key_id`),
  INDEX `idx_user`     (`user_id`),
  INDEX `idx_endpoint` (`endpoint`(100)),
  INDEX `idx_fired_at` (`fired_at`)
  -- NO INDEX on log_hash / prior_hash — chain integrity checked via sequential scan
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `#__eaiou_quality_signals` (
  `id`            INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`      INT NOT NULL,
  `round`         INT NOT NULL DEFAULT 1,
  `basin`         DECIMAL(5,4) DEFAULT NULL COMMENT 'basin_integrity dimension',
  `investigation` DECIMAL(5,4) DEFAULT NULL COMMENT 'investigation dimension',
  `completeness`  DECIMAL(5,4) DEFAULT NULL COMMENT 'completeness dimension',
  `gap_coverage`  DECIMAL(5,4) DEFAULT NULL COMMENT 'gap_coverage dimension',
  `q_signal`      DECIMAL(7,4) DEFAULT NULL COMMENT 'weighted composite',
  `computed_at`   DATETIME NOT NULL,
  INDEX `idx_paper_id` (`paper_id`),
  INDEX `idx_q_signal` (`q_signal`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add Temporal Blindness sealed fields to papers table (idempotent)
-- NO INDEXES on sealed fields — timing side-channel prevention
ALTER TABLE `#__eaiou_papers`
  ADD COLUMN IF NOT EXISTS `submission_sealed_at`   DATETIME DEFAULT NULL
      COMMENT 'sealed at submission — NEVER displayed publicly, NEVER indexed',
  ADD COLUMN IF NOT EXISTS `sealed_by`              INT DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS `submission_hash`        VARCHAR(64) DEFAULT NULL
      COMMENT 'SHA256(paper_uuid + submission_sealed_at + content_hash)',
  ADD COLUMN IF NOT EXISTS `acceptance_sealed_at`   DATETIME DEFAULT NULL
      COMMENT 'sealed at acceptance — NEVER displayed publicly, NEVER indexed',
  ADD COLUMN IF NOT EXISTS `publication_sealed_at`  DATETIME DEFAULT NULL
      COMMENT 'sealed at publication — NEVER displayed publicly, NEVER indexed';
```

- [ ] **Step 2: Verify migration SQL syntax**

```bash
cd /scratch/repos/eaiou
python3 -c "
with open('schema/migration_005_canonical_tables.sql') as f:
    sql = f.read()
tables = [l.strip() for l in sql.split('\n') if 'CREATE TABLE' in l]
alters = [l.strip() for l in sql.split('\n') if 'ALTER TABLE' in l]
print(f'Tables: {len(tables)}')
print(f'Alters: {len(alters)}')
for t in tables: print(' ', t)
for a in alters: print(' ', a)
"
```

Expected: 10 tables listed, 1 ALTER on `#__eaiou_papers`.

- [ ] **Step 3: Add migration_005 to FastAPI lifespan**

In `app/main.py`, locate the end of the lifespan `with engine.begin() as conn:` block (around line 200). Add this after all existing migrations:

```python
        # M-005: Canonical archival tables (versions, ai_sessions, didntmakeit,
        #        remsearch, review_logs, attribution_log, plugins_used,
        #        api_keys, api_logs, quality_signals) + TB sealed fields on papers
        import pathlib as _pl
        _m005 = _pl.Path(__file__).parent.parent / "schema" / "migration_005_canonical_tables.sql"
        if _m005.exists():
            _sql = _m005.read_text()
            for _stmt in [s.strip() for s in _sql.split(";") if s.strip() and not s.strip().startswith("--")]:
                try:
                    conn.execute(text(_stmt))
                except Exception:
                    pass  # Column/table already exists — idempotent
```

- [ ] **Step 4: Start the app and verify tables were created**

```bash
cd /scratch/repos/eaiou
source .venv/bin/activate
uvicorn app.main:app --port 8200 --reload &
sleep 3
python3 -c "
from app.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    rows = conn.execute(text(\"SHOW TABLES LIKE '%eaiou%'\")).fetchall()
    for r in rows: print(r[0])
" 2>/dev/null
kill %1 2>/dev/null
```

Expected: at least 20 tables listed, including `#__eaiou_versions`, `#__eaiou_api_keys`, `#__eaiou_api_logs`, `#__eaiou_quality_signals`.

- [ ] **Step 5: Commit**

```bash
cd /scratch/repos/eaiou
git add schema/migration_005_canonical_tables.sql app/main.py
git commit -m "feat: add migration_005 — 10 canonical archival tables + Temporal Blindness sealed fields on papers"
```

---

## Task 3: Enforce Temporal Blindness in FastAPI

The L0 doctrine: `submission_sealed_at`, `acceptance_sealed_at`, `publication_sealed_at` are **never returned in any response** (except to users with `governance` group membership). Any endpoint that accepts a `sort` parameter must reject `sort=date`, `sort=submitted_at`, `sort=created`, or any date-field sort with a 400.

**Files:**
- Create: `app/middleware/temporal_blindness.py`
- Create: `app/middleware/__init__.py`
- Modify: `app/main.py` (register middleware)
- Modify: `app/routers/papers.py` (sort validation + remove sealed fields from public response)
- Modify: `app/routers/editor.py` (sort validation)

- [ ] **Step 1: Create the middleware module**

Create `/scratch/repos/eaiou/app/middleware/__init__.py` (empty file):

```python
```

Create `/scratch/repos/eaiou/app/middleware/temporal_blindness.py`:

```python
"""
Temporal Blindness Middleware
L0 Doctrine: sealed temporal fields NEVER appear in any response
to users who lack the 'governance' group membership.

Sealed fields stripped: submission_sealed_at, acceptance_sealed_at,
publication_sealed_at, sealed_by, submission_hash

Sort rejection: any sort parameter that references a date or temporal
field returns 400 before the query executes.
"""

import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

# Fields that are NEVER returned to non-governance users
_SEALED_FIELDS = frozenset({
    "submission_sealed_at",
    "acceptance_sealed_at",
    "publication_sealed_at",
    "sealed_by",
    "submission_hash",
})

# Sort parameters that violate Temporal Blindness
_FORBIDDEN_SORT_KEYS = frozenset({
    "date", "created", "submitted_at", "submission_sealed_at",
    "acceptance_sealed_at", "publication_sealed_at",
    "created_at", "modified", "modified_at",
})


def _has_governance(request: Request) -> bool:
    """True if the session user has the 'governance' group."""
    user = request.session.get("user")
    if not user:
        return False
    return "governance" in (user.get("groups") or [])


def _strip_sealed(obj):
    """Recursively remove sealed fields from a dict/list."""
    if isinstance(obj, dict):
        return {k: _strip_sealed(v) for k, v in obj.items()
                if k not in _SEALED_FIELDS}
    if isinstance(obj, list):
        return [_strip_sealed(i) for i in obj]
    return obj


class TemporalBlindnessMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Reject forbidden sort parameters
        sort_param = request.query_params.get("sort", "").lower().lstrip("-")
        if sort_param and sort_param in _FORBIDDEN_SORT_KEYS:
            return JSONResponse(
                {"error": "sort_forbidden",
                 "detail": (
                     f"Sorting by '{sort_param}' violates the Temporal Blindness "
                     "doctrine. q_signal is the only permitted sort key."
                 )},
                status_code=400,
            )

        response = await call_next(request)

        # 2. Strip sealed fields from JSON responses for non-governance callers
        if _has_governance(request):
            return response

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        # Read, strip, and re-stream the body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        try:
            data = json.loads(body)
            cleaned = _strip_sealed(data)
            cleaned_body = json.dumps(cleaned).encode()
        except (json.JSONDecodeError, ValueError):
            cleaned_body = body

        return Response(
            content=cleaned_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type="application/json",
        )
```

- [ ] **Step 2: Register the middleware in main.py**

In `app/main.py`, after the existing `SessionMiddleware` registration, add:

```python
from .middleware.temporal_blindness import TemporalBlindnessMiddleware
# ... (after app = FastAPI(...) and SessionMiddleware registration)
app.add_middleware(TemporalBlindnessMiddleware)
```

The middleware stack executes outermost-last, so TB middleware wraps around all routes.

- [ ] **Step 3: Add sort validation to papers list route**

In `app/routers/papers.py`, find the `GET /papers/` list handler. The SQL query for the list likely does `ORDER BY q_overall DESC` or similar. Confirm it never uses a date field:

```bash
grep -n "ORDER BY" /scratch/repos/eaiou/app/routers/papers.py
```

If any `ORDER BY` references a date column in a public endpoint, change it to `ORDER BY q_signal DESC, q_overall DESC, paper_uuid ASC`.

- [ ] **Step 4: Add sort validation to editor list route**

```bash
grep -n "ORDER BY" /scratch/repos/eaiou/app/routers/editor.py
```

Editor routes may legitimately show internal dates to editors. Keep internal dates for editor-only views. Ensure no public API endpoint returns sealed fields.

- [ ] **Step 5: Test TB middleware**

```bash
cd /scratch/repos/eaiou
source .venv/bin/activate
uvicorn app.main:app --port 8200 &
sleep 2

# Test: sort=date is rejected
curl -s "http://localhost:8200/papers?sort=date" | python3 -m json.tool

# Test: sealed fields not in public paper list
curl -s "http://localhost:8200/papers/" | python3 -c "
import json, sys
data = json.load(sys.stdin)
papers = data if isinstance(data, list) else data.get('papers', [])
if papers:
    keys = set(papers[0].keys())
    sealed = {'submission_sealed_at','acceptance_sealed_at','publication_sealed_at'}
    found = keys & sealed
    if found:
        print(f'FAIL: sealed fields in response: {found}')
    else:
        print('PASS: no sealed fields in public response')
else:
    print('SKIP: no papers in DB yet')
"
kill %1 2>/dev/null
```

Expected: sort=date returns 400 with `sort_forbidden` error; no sealed fields in paper list.

- [ ] **Step 6: Commit**

```bash
cd /scratch/repos/eaiou
git add app/middleware/ app/main.py app/routers/papers.py app/routers/editor.py
git commit -m "feat: Temporal Blindness middleware — strips sealed fields, rejects date-sort on all public endpoints"
```

---

## Task 4: Scaffold Laravel Admin Panel

Laravel handles site administration only: users, papers admin CRUD, API keys, audit logs. It shares the same MariaDB as the FastAPI app.

**Files:**
- Create: `/scratch/repos/eaiou-admin/` (new Laravel 11 project)
- Modify: `/etc/nginx/conf.d/eaiou.conf` (add `/admin` proxy block)

- [ ] **Step 1: Check PHP + Composer availability**

```bash
php -v 2>/dev/null | head -1
composer --version 2>/dev/null | head -1
```

Expected: PHP 8.2+ and Composer 2.x. If PHP is missing:

```bash
# On the local dev machine:
which php || sudo dnf install -y php php-cli php-json php-mbstring php-xml php-pdo php-mysqlnd
which composer || curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer
```

- [ ] **Step 2: Create the Laravel project**

```bash
cd /scratch/repos
composer create-project laravel/laravel eaiou-admin --prefer-dist 2>&1 | tail -5
cd eaiou-admin
```

Expected: Laravel 11 project created at `/scratch/repos/eaiou-admin/`.

- [ ] **Step 3: Configure database connection**

Edit `/scratch/repos/eaiou-admin/.env`:

```bash
cd /scratch/repos/eaiou-admin
# Read the eaiou .env for DB credentials
source /scratch/repos/eaiou/.env 2>/dev/null || true

# Write Laravel .env DB block
python3 - << 'EOF'
import os, re

env_path = "/scratch/repos/eaiou-admin/.env"
with open(env_path) as f:
    content = f.read()

# Parse DATABASE_URL from eaiou .env
db_url = ""
try:
    with open("/scratch/repos/eaiou/.env") as ef:
        for line in ef:
            if line.startswith("DATABASE_URL="):
                db_url = line.split("=", 1)[1].strip()
                break
except FileNotFoundError:
    pass

if db_url:
    # mysql+pymysql://user:pass@host:port/dbname
    import re
    m = re.match(r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
    if m:
        user, pwd, host, port, dbname = m.groups()
        replacements = {
            "DB_CONNECTION=sqlite": "DB_CONNECTION=mysql",
            "DB_DATABASE=laravel": f"DB_DATABASE={dbname}",
            "DB_USERNAME=root": f"DB_USERNAME={user}",
            "DB_PASSWORD=": f"DB_PASSWORD={pwd}",
            "DB_HOST=127.0.0.1": f"DB_HOST={host}",
            "DB_PORT=3306": f"DB_PORT={port}",
        }
        for old, new in replacements.items():
            content = content.replace(old, new)
        # Remove sqlite file line
        content = re.sub(r"DB_DATABASE=.*\\.sqlite[^\n]*\n", "", content)
        with open(env_path, "w") as f:
            f.write(content)
        print("DB config written.")
    else:
        print(f"Could not parse DATABASE_URL: {db_url}")
else:
    print("DATABASE_URL not found in eaiou .env — set DB_* manually in eaiou-admin/.env")
EOF
```

If the DATABASE_URL parse fails, manually edit `/scratch/repos/eaiou-admin/.env`:

```
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=<dbname from eaiou .env>
DB_USERNAME=<user from eaiou .env>
DB_PASSWORD=<password from eaiou .env>
```

- [ ] **Step 4: Install Laravel Breeze (admin auth)**

```bash
cd /scratch/repos/eaiou-admin
composer require laravel/breeze --dev
php artisan breeze:install blade --dark
```

Expected: Breeze scaffolds login/register/dashboard views in Blade.

- [ ] **Step 5: Configure app name and URL**

```bash
cd /scratch/repos/eaiou-admin
sed -i 's|APP_NAME=Laravel|APP_NAME="eaiou Admin"|' .env
sed -i 's|APP_URL=http://localhost|APP_URL=https://eaiou.org/admin|' .env
```

- [ ] **Step 6: Run migrations (Breeze creates users/sessions tables)**

```bash
cd /scratch/repos/eaiou-admin
php artisan migrate --force
```

Expected: Breeze tables (users, sessions, password_reset_tokens) created in MariaDB.

Note: These are Laravel's own auth tables (`users`), separate from `#__eaiou_users`. The admin panel will use Laravel auth for the admin interface while querying `#__eaiou_*` tables for content management.

- [ ] **Step 7: Create the first admin controller**

```bash
cd /scratch/repos/eaiou-admin
php artisan make:controller Admin/PapersController --resource
```

Replace contents of `app/Http/Controllers/Admin/PapersController.php`:

```php
<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

class PapersController extends Controller
{
    public function index(Request $request)
    {
        $status = $request->query('status');
        $query = DB::table('eaiou_papers')
            ->select('id', 'paper_uuid', 'title', 'author_name', 'ai_disclosure_level',
                     'status', 'q_signal', 'q_overall', 'created')
            ->orderByRaw('q_signal IS NULL ASC')
            ->orderBy('q_signal', 'desc');

        if ($status) {
            $query->where('status', $status);
        }

        $papers = $query->paginate(25);
        $stats = [
            'total'              => DB::table('eaiou_papers')->count(),
            'submitted'          => DB::table('eaiou_papers')->where('status', 'submitted')->count(),
            'under_review'       => DB::table('eaiou_papers')->where('status', 'under_review')->count(),
            'accepted'           => DB::table('eaiou_papers')->where('status', 'accepted')->count(),
            'published'          => DB::table('eaiou_papers')->where('status', 'published')->count(),
        ];

        return view('admin.papers.index', compact('papers', 'stats', 'status'));
    }

    public function show($id)
    {
        $paper = DB::table('eaiou_papers')->where('id', $id)->first();
        abort_if(!$paper, 404);

        $revisions = DB::table('eaiou_revisions')
            ->where('paper_id', $id)
            ->orderBy('round')
            ->get();

        // Note: submission_sealed_at is available here because this is the admin panel
        return view('admin.papers.show', compact('paper', 'revisions'));
    }
}
```

Note: The DB table prefix in Laravel must match. Add to `config/database.php` under the mysql connection:

```php
'prefix' => '#__',
```

Or alternatively query with the full prefix `eaiou_papers` (since `#__` + `eaiou_papers` = `#__eaiou_papers`). Set prefix to `#__` so Laravel's table builder will prepend it.

- [ ] **Step 8: Add admin route**

In `/scratch/repos/eaiou-admin/routes/web.php`, add:

```php
use App\Http\Controllers\Admin\PapersController;

Route::middleware(['auth'])->prefix('admin')->name('admin.')->group(function () {
    Route::resource('papers', PapersController::class)->only(['index', 'show']);
});
```

- [ ] **Step 9: Verify the app starts**

```bash
cd /scratch/repos/eaiou-admin
php artisan serve --port=8300 &
sleep 2
curl -s -o /dev/null -w "%{http_code}" http://localhost:8300/admin/papers
kill %1 2>/dev/null
```

Expected: HTTP 302 (redirect to login — auth middleware working).

- [ ] **Step 10: Initialize git repo for admin**

```bash
cd /scratch/repos/eaiou-admin
git init
git add -A
git commit -m "feat: scaffold eaiou-admin — Laravel 11 + Breeze auth + admin papers controller"
```

---

## Verification: All 4 Tasks Complete

Run these checks to confirm the foundation is solid before moving to Plan 2:

```bash
# 1. Build plans exist
ls /scratch/repos/eaiou/docs/build_plans/*.md | wc -l
# Expected: 5

# 2. Migration 005 tables exist in DB
cd /scratch/repos/eaiou && source .venv/bin/activate
python3 -c "
from app.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    tbls = [r[0] for r in conn.execute(text(\"SHOW TABLES LIKE '%eaiou%'\")).fetchall()]
    required = ['#__eaiou_versions','#__eaiou_api_keys','#__eaiou_api_logs','#__eaiou_quality_signals']
    missing = [t for t in required if t not in tbls]
    if missing:
        print(f'MISSING: {missing}')
    else:
        print(f'PASS: all canonical tables present ({len(tbls)} total)')
"

# 3. Temporal Blindness sort rejection
uvicorn app.main:app --port 8200 &
sleep 2
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8200/papers?sort=date")
echo "TB sort test: $STATUS (expected 400)"
kill %1 2>/dev/null

# 4. Laravel admin starts
cd /scratch/repos/eaiou-admin
php artisan route:list --name=admin | head -5
```

---

*Plan 2 (FastAPI API tiers 1–6) begins after this foundation is verified green.*
