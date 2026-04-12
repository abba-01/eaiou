---
title: "eaiou Platform Documentation"
subtitle: "Version 3.0 — FastAPI Reference"
author: "Eric D. Martin | ORCID 0009-0006-5944-1742"
date: "2026-04-12"
documentclass: article
geometry: margin=1in
fontsize: 11pt
colorlinks: true
toc: true
---

\newpage

# 1. Mission and Purpose

eaiou (pronounced "ay-oo") is an observer-preserving full-context peer-review journal
platform. It implements the NAUGHT/CAUGHT/FOUND/REJECTED (NCF) lifecycle for research
claims, linking submitted papers to declared knowledge gaps tracked in gitgap.org.

**Core principles:**

- AI disclosure is mandatory at submission (none / assisted / generated)
- Q scoring provides automated quality signals based on process provenance, not claim truth
- IntelliD tracks every intelligence instance (human or AI) that contributed to an artifact
- Papers are never deleted — only tombstoned or archived; `cosmoid` is permanent
- GitGap lifecycle webhooks fire on accept/publish and reject to update gap status
- The Appreciated scale amplifies scores for older unresolved gaps — age is opportunity, not deterrence

---

# 2. Technology Stack

| Layer            | Technology                                            |
|------------------|-------------------------------------------------------|
| Runtime          | Python 3.12                                           |
| Web framework    | FastAPI 0.x                                           |
| ASGI server      | Uvicorn (dev) / Gunicorn + UvicornWorker (production) |
| Templating       | Jinja2 3.1                                            |
| ORM              | SQLAlchemy (raw `text()` queries — no ORM models)     |
| Database         | MariaDB (table prefix `#__eaiou_`)                    |
| Auth             | Starlette SessionMiddleware (`eaiou_session` cookie)  |
| Password hashing | bcrypt (passlib), cost 12                             |
| OAuth            | Google OAuth2, ORCID OAuth2 via httpx                 |
| File extraction  | pypdf (PDF), python-docx (DOCX), UTF-8 (TXT)          |
| HTTP client      | httpx (sync, timeout=4s for external calls)           |
| Frontend CSS     | Tailwind CSS CDN (custom `primary` color scale)       |
| Frontend JS      | SortableJS (drag-and-drop section ordering)           |
| Reverse proxy    | Nginx                                                 |
| TLS              | Let's Encrypt (certbot)                               |
| Process manager  | systemd (`eaiou.service`)                             |
| Server           | 136.118.94.112, domain eaiou.org                      |

---

# 3. Application Bootstrap (`app/main.py`)

The `lifespan` async context manager runs idempotent schema migrations on every startup
using `CREATE TABLE IF NOT EXISTS` and `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`. There
is no separate migration tool or migration history table.

**Startup sequence:**

1. Run schema migrations (see Section 6 for full table list)
2. Seed default groups: `admin`, `editor`, `author`
3. Seed admin user from `ADMIN_USER` / `ADMIN_PASS` environment variables (bcrypt-hashed)
4. Ensure `UPLOAD_DIR` directory exists on disk

**Middleware stack (applied in order):**

1. `SessionMiddleware` — signed `eaiou_session` cookie; `https_only=True` in production
2. `SecurityHeadersMiddleware` (custom) — adds X-Frame-Options, X-Content-Type-Options,
   X-XSS-Protection, Referrer-Policy to every response

**Static files:** `app/static/` mounted at `/static`

**Exception handlers:**

| Code | Behavior                                                  |
|------|-----------------------------------------------------------|
| 403  | Logged-in users → redirect `/`; guests → `/auth/login`   |
| 404  | Renders `errors/404.html`                                 |
| 500  | Renders `errors/500.html`                                 |

---

# 4. Route Reference

## 4.1 Public / Page Routes (`app/main.py`)

| Method | Path                              | Template                            | Auth     |
|--------|-----------------------------------|-------------------------------------|----------|
| GET    | `/`                               | `index.html`                        | optional |
| GET    | `/about`                          | `about.html`                        | optional |
| GET    | `/policy/temporal-blindness`      | `policy/temporal-blindness.html`    | optional |
| GET    | `/policy/ai-disclosure`           | `policy/ai-disclosure.html`         | optional |
| GET    | `/policy/open-access`             | `policy/open-access.html`           | optional |
| GET    | `/policy/intelligence-blindness`  | `policy/intelligence-blindness.html`| optional |
| GET    | `/health`                         | JSON `{"status":"ok"}`              | none     |

## 4.2 Papers Router (`app/routers/papers.py`, prefix `/papers`)

| Method | Path                   | Template                         | Notes                                         |
|--------|------------------------|----------------------------------|-----------------------------------------------|
| GET    | `/papers/`             | `papers/list.html`               | Excludes drafts and tombstoned; top 50 by Q   |
| GET    | `/papers/submit`       | `papers/submit.html`             | Public submission form                        |
| GET    | `/papers/submitted/{id}` | `papers/submitted.html`        | Post-submission confirmation                  |
| GET    | `/papers/status/{id}`  | `views/13_status_tracking.html`  | Public status tracker                         |
| GET    | `/papers/{id}`         | `views/22_the_article.html`      | Full paper + CoA seal + IntelliD contributions|
| POST   | `/papers/submit`       | —                                | Creates paper, redirects to `/papers/submitted/{id}` |

## 4.3 Auth Router (`app/routers/auth.py`, prefix `/auth`)

| Method | Path              | Notes                                        |
|--------|-------------------|----------------------------------------------|
| GET    | `/auth/login`     | Login form                                   |
| POST   | `/auth/login`     | Validates credentials, sets session cookie   |
| GET    | `/auth/logout`    | Clears `eaiou_session`, redirects to `/`     |
| GET    | `/auth/register`  | Registration form (may require invite code)  |
| POST   | `/auth/register`  | Creates user (bcrypt), sets session          |

## 4.4 OAuth Router (`app/routers/oauth.py`, prefix `/auth/oauth`)

| Method | Path                         | Notes                                     |
|--------|------------------------------|-------------------------------------------|
| GET    | `/auth/oauth/google`         | Redirect to Google authorization endpoint |
| GET    | `/auth/oauth/google/callback`| Google callback; auto-creates user        |
| GET    | `/auth/oauth/orcid`          | Redirect to ORCID authorization endpoint  |
| GET    | `/auth/oauth/orcid/callback` | ORCID callback; auto-creates user         |

OAuth users have `password_hash = NULL` and `auth_provider` = `google` or `orcid`.

## 4.5 Author Router (`app/routers/author.py`, prefix `/author`)

Requires login. Unauthenticated requests redirect to `/auth/login?next=<path>`.

| Method  | Path                                | Template                            | Notes             |
|---------|-------------------------------------|-------------------------------------|-------------------|
| GET     | `/author/`                          | `views/30_submission_dashboard.html`| Dashboard + notifications |
| GET     | `/author/intake`                    | `views/28_submission_form.html`     | Intake wizard     |
| GET     | `/author/submit`                    | `author/submit.html`                | Full submission form |
| POST    | `/author/submit`                    | —                                   | Saves draft, redirects |
| GET     | `/author/workspace/{id}`            | `author/workspace.html`             | Paper workspace   |
| GET     | `/author/drawer`                    | `author/drawer.html`                | File drawer       |
| GET     | `/author/notifications`             | `views/14_notifications.html`       | Stub              |
| GET     | `/author/messages`                  | `views/01_communication_center.html`| Stub              |
| GET     | `/author/messages-v2`               | `views/17_communication_center.html`| Stub              |
| GET     | `/author/papers/{id}/versions`      | `views/29_version_control.html`     | Stub              |
| GET     | `/author/papers/{id}/transparency`  | `views/24_transparency.html`        | Stub              |
| Various | `/author/api/sections/*`            | JSON                                | Section CRUD API  |

## 4.6 Editor Router (`app/routers/editor.py`, prefix `/editor`)

Requires login. Uses `_require_login()` helper (redirect, not 403).

| Method | Path                              | Template                  | Notes                         |
|--------|-----------------------------------|---------------------------|-------------------------------|
| GET    | `/editor/`                        | `editor/dashboard.html`   | All papers, stats sidebar     |
| GET    | `/editor/papers`                  | `editor/dashboard.html`   | Alias                         |
| GET    | `/editor/queue`                   | `editor/queue.html`       | Submitted-only queue          |
| GET    | `/editor/papers/{id}`             | `editor/paper_detail.html`| Full editorial view + Q + trajectory |
| POST   | `/editor/papers/{id}/status`      | —                         | Status transition; fires notifications + GitGap webhook |
| POST   | `/editor/papers/{id}/score`       | —                         | Manual Q override             |
| POST   | `/editor/papers/{id}/score/recompute` | JSON                  | Recomputes Q signal, clears override |
| GET    | `/editor/papers/{id}/score/breakdown` | JSON                  | Current Q breakdown (live, not persisted) |

## 4.7 Report Router (`app/routers/report.py`, no prefix)

No authentication required for paste analysis. Upload endpoint requires login.

| Method | Path            | Notes                                             |
|--------|-----------------|---------------------------------------------------|
| GET    | `/report`       | Coverage analysis form (`report.html`)            |
| POST   | `/report`       | Run full analysis pipeline; renders `report.html` |
| POST   | `/report/upload`| Upload PDF/DOCX/TXT to user drawer; returns extracted text |

## 4.8 Admin Router (`app/routers/admin.py`, prefix `/admin`)

Requires `admin` group membership (`require_admin` dependency).

| Method | Path                  | Notes            |
|--------|-----------------------|------------------|
| GET    | `/admin/`             | Dashboard        |
| GET    | `/admin/users`        | User list        |
| GET    | `/admin/users/new`    | Create user form |
| POST   | `/admin/users/new`    | Create user      |
| GET    | `/admin/users/{id}/edit` | Edit user form|
| POST   | `/admin/users/{id}/edit` | Save edits    |

## 4.9 Intelligence / IntelliD Routers

`app/routers/intelligence.py` and `app/routers/intellid.py` handle IntelliD registry
management and artifact contribution queries. See Section 8 for the IntelliD system.

## 4.10 API Router (`app/routers/api.py`, prefix `/api`)

Internal JSON endpoints used by frontend JavaScript widgets (section drag-and-drop
ordering, paper section CRUD). Not documented publicly.

---

# 5. Authentication and Authorization

## 5.1 Session Structure

`current_user` is a Python dict injected into every route via `Depends(get_current_user)`:

| Key        | Type       | Value                                      |
|------------|------------|--------------------------------------------|
| `id`       | `int`      | User PK                                    |
| `name`     | `str`      | Username (login name)                      |
| `display`  | `str`      | `display_name` or username if not set      |
| `initials` | `str`      | First 2 chars of display, uppercased       |
| `groups`   | `list[str]`| e.g. `["admin", "editor"]`                |

Returns `None` for unauthenticated requests.

## 5.2 Authorization Helpers (`app/deps.py`)

| Dependency       | Requirement               | Failure    |
|------------------|---------------------------|------------|
| `get_current_user` | session only             | Returns None |
| `require_admin`  | `"admin"` in groups       | HTTP 403   |
| `require_editor` | `"admin"` or `"editor"`   | HTTP 403   |

## 5.3 CSRF Protection (`app/security.py`)

CSRF tokens are per-session. All state-changing POST forms must include `csrf_token`.

- `get_csrf_token(request)` — generates/retrieves token from session
- `validate_csrf(request, token)` — raises HTTP 403 on mismatch

---

# 6. Database Schema

All tables use the `#__eaiou_` prefix. The prefix is part of the `DATABASE_URL` connection
configuration. SQLAlchemy uses raw `text()` queries throughout — no ORM model classes.

## 6.1 `#__eaiou_papers`

The central table. Every submitted paper has a `cosmoid` (permanent UUID) and a
`paper_uuid` (submission UUID). `tombstone_state IS NULL` means the paper is active.

| Column                    | Type           | Notes                                          |
|---------------------------|----------------|------------------------------------------------|
| `id`                      | INT PK         | Auto-increment                                 |
| `paper_uuid`              | VARCHAR(36)    | UUID generated at submission                   |
| `cosmoid`                 | VARCHAR(36)    | Permanent UUID, never removed                  |
| `title`                   | TEXT           |                                                |
| `abstract`                | LONGTEXT       |                                                |
| `author_name`             | VARCHAR(255)   |                                                |
| `orcid`                   | VARCHAR(32)    | Author's ORCID iD                              |
| `keywords`                | TEXT           |                                                |
| `ai_disclosure_level`     | VARCHAR(32)    | `none` / `assisted` / `generated`             |
| `ai_disclosure_notes`     | TEXT           |                                                |
| `status`                  | VARCHAR(32)    | See Section 9 (lifecycle)                      |
| `submitted_at`            | DATETIME       |                                                |
| `created`                 | DATETIME       |                                                |
| `q_signal`                | DECIMAL(7,4)   | Computed Q score (0–10)                        |
| `q_overall`               | DECIMAL(7,4)   | Editor override; falls back to `q_signal`      |
| `rejection_reason_code`   | VARCHAR(64)    | Set on rejection                               |
| `rejection_notes`         | TEXT           | Internal editor notes                          |
| `rejection_public_summary`| TEXT           | Shown to author                                |
| `doi`                     | VARCHAR(255)   | Set on publication                             |
| `submission_capstone`     | TEXT           | Zenodo receipt URL or ID                       |
| `gitgap_gap_id`           | INT            | FK to gitgap gap (nullable)                    |
| `tombstone_state`         | VARCHAR(32)    | NULL = active                                  |

## 6.2 `#__eaiou_users`

| Column          | Type         | Notes                                         |
|-----------------|--------------|-----------------------------------------------|
| `id`            | INT PK       |                                               |
| `username`      | VARCHAR(64)  | UNIQUE                                        |
| `email`         | VARCHAR(255) |                                               |
| `password_hash` | VARCHAR(255) | NULL for OAuth users                          |
| `display_name`  | VARCHAR(255) |                                               |
| `active`        | TINYINT(1)   | 1 = active                                    |
| `created_at`    | DATETIME     |                                               |
| `last_login_at` | DATETIME     |                                               |
| `orcid`         | VARCHAR(32)  | ORCID iD (from ORCID OAuth or user profile)   |
| `auth_provider` | VARCHAR(32)  | `local` / `google` / `orcid`                 |
| `provider_sub`  | VARCHAR(255) | OAuth subject identifier                      |

## 6.3 `#__eaiou_groups` / `#__eaiou_user_groups`

Three groups seeded at startup: `admin`, `editor`, `author`.
`#__eaiou_user_groups` is a M2M join table with `(user_id, group_id)` PK.

## 6.4 `#__eaiou_user_files`

| Column          | Type         | Notes                                             |
|-----------------|--------------|---------------------------------------------------|
| `id`            | INT PK       |                                                   |
| `user_id`       | INT FK       | → `#__eaiou_users`                               |
| `original_name` | VARCHAR(255) | Original upload filename                          |
| `stored_path`   | VARCHAR(512) | Relative to `UPLOAD_DIR`; sharded by SHA prefix   |
| `mime_type`     | VARCHAR(128) | pdf / docx / txt                                  |
| `file_size`     | INT          | Bytes                                             |
| `sha256`        | CHAR(64)     | SHA-256 of raw bytes; dedup key per user          |
| `extracted_text`| LONGTEXT     | pypdf/python-docx extracted text (no metadata)    |
| `uploaded_at`   | DATETIME     |                                                   |
| `deleted_at`    | DATETIME     | NULL = active (soft delete)                       |

Storage path: `UPLOAD_DIR/{user_id}/{sha256[:2]}/{sha256}{.ext}` (two-char shard prefix).

## 6.5 `#__eaiou_notifications`

| Column      | Type        | Notes                                         |
|-------------|-------------|-----------------------------------------------|
| `id`        | INT PK      |                                               |
| `paper_id`  | INT FK      | → `#__eaiou_papers`                          |
| `type`      | VARCHAR(64) | e.g. `status_accepted`, `status_rejected`     |
| `message`   | TEXT        | Human-readable; includes paper title and msg  |
| `created_at`| DATETIME    |                                               |
| `read_at`   | DATETIME    | NULL = unread                                 |

## 6.6 `#__eaiou_revisions`

| Column           | Type     | Notes                                    |
|------------------|----------|------------------------------------------|
| `id`             | INT PK   |                                          |
| `paper_id`       | INT FK   |                                          |
| `round`          | INT      | 1-indexed revision round                 |
| `instructions`   | TEXT     | Editor's revision request text           |
| `due_at`         | DATE     | Optional deadline                        |
| `requested_at`   | DATETIME |                                          |
| `resubmitted_at` | DATETIME | NULL until author resubmits              |

## 6.7 `#__eaiou_integrity_seals`

CoA seals generated per paper at seal time.

| Column       | Type        | Notes                                     |
|--------------|-------------|-------------------------------------------|
| `cosmoid`    | VARCHAR(36) | Paper cosmoid at seal time                |
| `gate_valid` | TINYINT     | Boolean: seal passed gate                 |
| `audit_status`| VARCHAR(32)| `pending` / `passed` / `failed`           |
| `mbs`        | DECIMAL     | Methodology-Balance-Specificity score 0–1 |
| `seal_hash`  | CHAR(64)    | SHA-256 of sealed content                 |
| `sealed_at`  | DATETIME    |                                           |

## 6.8 `#__eaiou_intellid_registry`

| Column        | Type        | Notes                                         |
|---------------|-------------|-----------------------------------------------|
| `intellid`    | VARCHAR(36) | UUID, PK                                      |
| `type`        | VARCHAR(32) | `human` / `ai`                               |
| `model_family`| VARCHAR(64) | e.g. `Claude`, `GPT-4`, `Gemini`             |
| `connector`   | VARCHAR(64) | Interface (e.g. `Claude Code`, `API`, `Web`) |

## 6.9 `#__eaiou_intellid_contributions`

| Column         | Type        | Notes                                          |
|----------------|-------------|------------------------------------------------|
| `intellid`     | VARCHAR(36) | FK → `#__eaiou_intellid_registry`             |
| `artifact_type`| VARCHAR(32) | `paper` / `section` / `analysis`             |
| `artifact_id`  | VARCHAR(64) | cosmoid or section ID                          |
| `relation`     | VARCHAR(32) | `authored` / `reviewed` / `edited` / `assisted` |
| `weight`       | DECIMAL     | 0.0–1.0 contribution weight                   |
| `confidence`   | DECIMAL     | 0.0–1.0 confidence in attribution             |

## 6.10 Additional Tables

The following tables support the Q score investigation pipeline (not yet fully
deployed in the current production version):

- `#__eaiou_interrogation_log` — interrogation exchanges per paper
- `#__eaiou_volley_log` — volley rounds per paper
- `#__eaiou_paper_sections` — structured paper sections with content and notes

---

# 7. Paper Status Lifecycle

Papers follow a controlled state machine. Invalid transitions return HTTP 422.

```
submitted
    |
    v
under_review -------------------------------------------+
    |                                                   |
    v                                                   v
revision_requested --> submitted (loop)         accepted --> published --> archived
    |                                                   |
    v                                                   v
rejected --> archived                               archived
```

Terminal state: `archived` (no further transitions permitted).

**On each status change, three things happen:**

1. `status` column updated in `#__eaiou_papers`
2. Notification inserted into `#__eaiou_notifications` (non-fatal if it fails)
3. GitGap lifecycle webhook fired if `gitgap_gap_id` is set (best-effort, exceptions swallowed)

**Status messages shown to authors:**

| Status               | Message                                          |
|----------------------|--------------------------------------------------|
| `under_review`       | "Your paper is now under editorial review."      |
| `revision_requested` | "The editor has requested revisions..."          |
| `accepted`           | "Congratulations — your paper has been accepted."|
| `rejected`           | "Your paper was not accepted at this time."      |
| `published`          | "Your paper has been published."                 |
| `archived`           | "Your paper has been archived."                  |

---

# 8. IntelliD System

IntelliD (Intelligence Identifier) tracks every intelligence instance — human or AI —
that contributed to an artifact. Each distinct agent (a person, a specific AI model
invocation, a connector) receives a permanent `intellid` UUID.

**Purpose:** Observer preservation. Every paper's contribution graph is permanently
recorded, showing what intelligence, at what weight, contributed to what artifact.
This is the SAID (Scientific AI Intelligence Disclosure) primitive in practice.

**Flow:**
1. An IntelliD is registered in `#__eaiou_intellid_registry` with type, model family, connector
2. Each contribution is recorded in `#__eaiou_intellid_contributions` with relation, weight, confidence
3. The paper view (`/papers/{id}`) fetches and displays the full contribution graph

**Key distinction:** IntelliD != CosmoID. CosmoID (`cosmoid`) identifies the paper artifact.
IntelliD identifies the intelligence instance that contributed to it.

---

# 9. GitGap Integration

Papers submitted in response to a declared knowledge gap carry a `gitgap_gap_id` FK.
eaiou is the **CAUGHT** layer in the NCF lifecycle; gitgap.org is the **NAUGHT** layer.

| eaiou Event          | GitGap Webhook           | Endpoint                       |
|----------------------|--------------------------|--------------------------------|
| `accepted` / `published` | Gap FOUND            | `POST /gaps/{id}/found`        |
| `rejected`           | Gap REJECTED             | `POST /gaps/{id}/reject`       |

**FOUND payload:** `{"found_paper_cosmoid": cosmoid, "found_paper_doi": doi}`

**REJECTED payload:** `{"rejection_mode": code, "rejection_notes": notes, "pickup_instructions": summary}`

GitGap URL configured via `GITGAP_API_URL` env var (default: `http://127.0.0.1:8001`).
All webhook calls are best-effort — exceptions are caught and swallowed to avoid
blocking status transitions.

---

# 10. Coverage Analysis (`/report`)

The coverage tool analyzes paper text for claim coverage against the gitgap gap index.
No authentication required for paste analysis; file uploads require login.

## 10.1 Pipeline

1. **Claim extraction** — 20 assertion-pattern regexes identify high-confidence claim
   sentences (40–400 chars, at least one pattern match). Up to 20 claims extracted.
2. **Gap scoring** — each claim sent to gitgap API for keyword-overlap matching; TF-IDF
   cosine similarity used as internal fallback (discounted by 0.75× so gitgap always wins)
3. **Appreciated scale** — gap age amplifies score: `age_amp = 1.0 + min(age_years/15, 0.8)`
   (caps at 1.8× for gaps 15+ years old)
4. **Classification** (from `appreciated` score):
   - `covered` >= 0.55 — strong literature match
   - `needs_work` 0.25-0.54 — weak support, needs citation framing
   - `novel` < 0.25 — no prior match; paper may fill this gap
5. **AI signal** — 9 characteristic AI phrases scored across 3 tiers (low/moderate/high)
6. **Discipline inference** — 10 disciplines, minimum 2 keyword hits to register
7. **Recommendations** — 6 priority conditions generate actionable items
8. Render `report.html` with full breakdown

## 10.2 File Upload Limits

| Limit          | Value                         |
|----------------|-------------------------------|
| Max file size  | 10 MB                         |
| Max files/user | 100 (soft cap; soft-deleted files count as free) |
| Supported types| PDF, DOCX, plain text (.txt)  |
| Deduplication  | SHA-256 per user (same content returns existing record) |

---

# 11. Q Score Service (`app/services/qscore.py`)

Q score is a 0–10 quality signal measuring the provenance quality of the paper's
creation process, not the correctness of its claims.

**Four dimensions and weights:**

| Dimension         | Weight | Source                                         |
|-------------------|--------|------------------------------------------------|
| `basin_integrity` | 0.40   | MBS from latest integrity seal (0.0–1.0 → 0–10)|
| `investigation`   | 0.25   | Interrogation exchanges + volley rounds         |
| `completeness`    | 0.20   | Ratio of sections with written content          |
| `gap_coverage`    | 0.15   | Gap anchor present in gitgap (10.0) or not (5.0)|

**Classification:**

| Score  | Label    |
|--------|----------|
| >= 8.0 | STRONG   |
| >= 6.0 | GOOD     |
| >= 4.0 | FAIR     |
| < 4.0  | WEAK     |

**Two columns on `#__eaiou_papers`:**

- `q_signal` — computed by `persist_q_signal()`; updated at seal time
- `q_overall` — editor decision; defaults to `q_signal`; manual override via `/editor/papers/{id}/score`

`COALESCE(q_overall, q_signal)` — editor override preserved until explicitly cleared.

---

# 12. Template System

## 12.1 Base Templates

| File                         | Used by                                   |
|------------------------------|-------------------------------------------|
| `app/templates/base.html`    | Public pages (index, about, policy, papers)|
| `author/base_author.html`    | All `/author/*` pages                     |
| `editor/base_editor.html`    | All `/editor/*` pages                     |
| `base/base.html`             | Wireframe views (extends same head block) |
| `base/layout_b.html`         | Wireframe sidebar layout                  |

## 12.2 Design System (`app/static/css/eaiou.css`)

Two CSS variable systems:

**`--ep-*` (eaiou primary):**

```css
--ep-primary: #18171A;
--ep-primary-hover: #0F0E10;
--ep-primary-light: #F0EFEB;
--ep-bg: #F7F6F3;
```

**`--ds-*` (used in wireframe templates):**

```css
--ds-ink-1: #18171A;     /* primary text */
--ds-ink-2: #4A4846;     /* secondary text */
--ds-ink-3: #9A9895;     /* muted text */
--ds-border: #E2E0DB;    /* default border */
--ds-border-strong: #CAC8C2;
--ds-bg: #FFFFFF;
--ds-surface: #F7F6F3;   /* off-white surface */
```

Tailwind `primary` scale overridden in every base template's CDN config block,
pivoted from sky-blue to a warm dark charcoal scale (`primary-600: #18171A`).

## 12.3 Wireframe Views (`app/templates/views/`)

17 locked UXPilot HTML designs. Four are wired to live routes; nine are stub pages
(login redirect only); four are reserved for future routing.

| Template                       | Route                          | Status  |
|--------------------------------|--------------------------------|---------|
| `30_submission_dashboard.html` | `/author/`                     | Live    |
| `28_submission_form.html`      | `/author/intake`               | Live    |
| `13_status_tracking.html`      | `/papers/status/{id}`          | Live    |
| `22_the_article.html`          | `/papers/{id}`                 | Live    |
| `14_notifications.html`        | `/author/notifications`        | Stub    |
| `01_communication_center.html` | `/author/messages`             | Stub    |
| `17_communication_center.html` | `/author/messages-v2`          | Stub    |
| `29_version_control.html`      | `/author/papers/{id}/versions` | Stub    |
| `24_transparency.html`         | `/author/papers/{id}/transparency` | Stub |
| `15_reviewer_performance.html` | (unrouted)                     | Reserved|
| `16_reviewer_matching.html`    | (unrouted)                     | Reserved|
| `18_reviewer_management.html`  | (unrouted)                     | Reserved|
| `19_reviewer_database.html`    | (unrouted)                     | Reserved|
| `20_conflict_detection.html`   | (unrouted)                     | Reserved|
| `21_review_model.html`         | (unrouted)                     | Reserved|
| `23_plagiarism_check.html`     | (unrouted)                     | Reserved|
| `25_online_platforms.html`     | (unrouted)                     | Reserved|

---

# 13. Deployment

## 13.1 Server

| Item             | Value                        |
|------------------|------------------------------|
| Host             | 136.118.94.112               |
| Domain           | eaiou.org                    |
| SSH user         | mae                          |
| App directory    | `/home/mae/eaiou/`           |
| Venv             | `/home/mae/eaiou/venv/`      |
| Upload directory | `/var/eaiou/uploads/`        |
| Service port     | 127.0.0.1:8102 (internal)    |

## 13.2 systemd Service Unit

```ini
[Unit]
Description=eaiou FastAPI Application
After=network.target mariadb.service

[Service]
User=mae
WorkingDirectory=/home/mae/eaiou
EnvironmentFile=/home/mae/eaiou/.env
ExecStart=/home/mae/eaiou/venv/bin/gunicorn app.main:app \
    -k uvicorn.workers.UvicornWorker -w 2 -b 127.0.0.1:8102
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Restart command: `printf "Evolitub76\041@#\n" | sudo -S systemctl restart eaiou`
(The `\041` is an octal escape for `!` to avoid shell interpretation.)

## 13.3 Nginx

Nginx reverse-proxies HTTPS port 443 → `127.0.0.1:8102`. TLS certificates managed by
certbot (Let's Encrypt). Config lives at `/etc/nginx/conf.d/`.

## 13.4 Deploy Pattern

```bash
rsync -av \
  --exclude='__pycache__' --exclude='.git' --exclude='*.pyc' \
  --exclude='venv' --exclude='.env' --exclude='docs' \
  /scratch/repos/eaiou/ mae@136.118.94.112:/home/mae/eaiou/

ssh mae@136.118.94.112 \
  'printf "Evolitub76\041@#\n" | sudo -S systemctl restart eaiou'
```

**Never sync `.env`** — production credentials live on the server only.

## 13.5 Environment Variables (`.env`)

| Variable               | Purpose                                           |
|------------------------|---------------------------------------------------|
| `DATABASE_URL`         | MariaDB connection string with `#__eaiou_` prefix |
| `SECRET_KEY`           | Session signing key (rotate periodically)         |
| `ADMIN_USER`           | Bootstrap admin username                          |
| `ADMIN_PASS`           | Bootstrap admin password (bcrypt-hashed at start) |
| `UPLOAD_DIR`           | Absolute path for file storage root               |
| `GOOGLE_CLIENT_ID`     | Google OAuth2 client ID                           |
| `GOOGLE_CLIENT_SECRET` | Google OAuth2 client secret                       |
| `ORCID_CLIENT_ID`      | ORCID OAuth2 client ID                            |
| `ORCID_CLIENT_SECRET`  | ORCID OAuth2 client secret                        |
| `GITGAP_API_URL`       | GitGap service base URL (default: `http://127.0.0.1:8001`) |
| `ENVIRONMENT`          | `production` enables HTTPS-only session cookies   |

All secrets stored in `/root/.env` (development) or `/home/mae/eaiou/.env` (production).

---

# 14. Agent Automation (Local Only — Not Deployed)

Three agents in the `agents/` directory. They run locally and are not deployed to the
production server. They assist with research and paper management workflows.

| Agent   | Role                                                          |
|---------|---------------------------------------------------------------|
| Author  | Assists paper drafting, section editing, and submission prep  |
| Mira    | Peer review simulation and gap analysis                       |
| Scorch  | QC watchdog, procedural compliance, stderr flagging           |

**Scorch the turtle** is the designated QC agent. Scorch flags carry research-record weight —
they must be addressed, not dismissed. Scorch operates on stderr and surfaces issues that
the other agents and humans may overlook.

---

# 15. Governing Principles

## 15.1 NCF Lifecycle

The NAUGHT/CAUGHT/FOUND/REJECTED lifecycle connects papers to declared knowledge gaps:

| State     | Meaning                                              | System     |
|-----------|------------------------------------------------------|------------|
| NAUGHT    | Gap declared; no paper yet addresses it              | gitgap.org |
| CAUGHT    | Paper submitted claiming to address the gap          | eaiou.org  |
| FOUND     | Paper accepted/published; gap considered resolved    | gitgap.org |
| REJECTED  | Submission did not satisfy the gap                   | eaiou.org  |

eaiou is the **CAUGHT layer**. GitGap is the NAUGHT/FOUND/REJECTED tracker.
Lifecycle webhooks keep both systems synchronized.

## 15.2 Chain of Appreciation (CoA)

Every paper receives a cryptographic integrity seal at submission time:

- `cosmoid` — permanent UUID minted at creation, never removed even on archival
- `seal_hash` — SHA-256 of paper content at seal time
- `gate_valid` — whether content passed the gate at sealing
- `mbs` — Methodology, Balance, Specificity score (0.0–1.0)

The CoA seal is displayed publicly on every paper's view page.

## 15.3 Observer Preservation

eaiou's core commitment is to preserve the full context of a submission:

- **AI contributions** — IntelliD records every AI instance that touched an artifact
- **Revision history** — every revision round is stored with instructions and dates
- **Trajectory tree** — rewrite/branch/amendment relationships are tracked
- **Temporal Blindness** — AI models have knowledge cutoffs; eaiou's policy page
  (`/policy/temporal-blindness`) documents this as a known epistemic risk

## 15.4 Q Score as Signal, Not Imprimatur

Q score measures the quality of the *process* that produced the paper, not the correctness
of its claims. A STRONG score means the paper has excellent provenance documentation. It
does not certify scientific validity. Editorial judgment remains paramount.

## 15.5 Appreciated Opportunity

Gap age is an amplifier in coverage scoring, not a deterrence signal. An unresolved 15-year-old
gap matched at 0.60 similarity scores as 1.08 (appreciated). The UI surfaces this as
"N years unresolved — appreciated opportunity," not as evidence the work is outdated.

---

*Documentation version: 3.0 | Generated: 2026-04-12 | Author: Eric D. Martin*
*ORCID: 0009-0006-5944-1742 | Platform: eaiou.org*
