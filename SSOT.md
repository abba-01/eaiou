# eaiou — Single Source of Truth
**Version:** 3.0 (2026-04-13)
**Author:** Eric D. Martin — ORCID 0009-0006-5944-1742
**Status:** CANONICAL — all development decisions resolved against this file

> This document supersedes SSOT v2.0 (Joomla 6.0.3). The system is FastAPI. See git history for the archived Joomla specification.

---

## 0. Governing Doctrine

### 0.1 The Sort Principle
Papers surface in the order that science flows — quality, relevance, methodological rigor, transparency of process. Submission dates are sealed. Recency is not a discovery axis. A paper that matters more arrives first, regardless of when it entered the archive.

### 0.2 Temporal Blindness
The submission timestamp (`submitted_at`) is sealed state. It is captured at receipt and is:
- Never displayed to reviewers or editors
- Never used in a sort key
- Never indexed for discovery
- Accessible only by admins via explicit governance unlock

**Enforcement rule:** No template, query, or route may expose `submitted_at` to any session that is not an authenticated admin. Any `ORDER BY id DESC` or `ORDER BY created DESC` is a Temporal Blindness violation.

SAID witness: Eric D. Martin, ORCID 0009-0006-5944-1742

### 0.3 Intelligence Blindness
AI involvement is disclosed but not penalized. `ai_disclosure_level` is mandatory on submission; it is visible to editors and in the public paper view. It has zero effect on Q scoring or sort order. The system never suppresses AI involvement — it structures and preserves it.

### 0.4 Full-Context Preservation
Archive everything. Annotate, don't delete. Tombstone, don't purge. `status` field drives lifecycle. No hard deletes. CosmoID persists through tombstone and is never removed.

### 0.5 Observer-Preserving
eaiou is an OMMP Layer 5 module. It preserves the entire research path — used and unused sources, included and excluded AI outputs, accepted and rejected versions. Cross-domain serendipity is real.

---

## 1. Authoritative Stack

```
FastAPI 0.111 + Starlette SessionMiddleware
MariaDB via SQLAlchemy (pymysql driver)
Jinja2 templates — NO JavaScript framework
Tailwind CSS via CDN (runtime config override — monochrome scale)
Font Awesome 6.4 via CDN
DM Sans (body) + DM Serif Display italic (brand/titles)
```

**Run:**
```bash
source .venv/bin/activate && uvicorn app.main:app --reload
```

**Environment variables required:**
```
DB_HOST  DB_PORT  DB_NAME  DB_USER  DB_PASS
ADMIN_USER  ADMIN_PASS  SECRET_KEY
```

---

## 2. Design System — eaiou Monochrome

### 2.1 Color Tokens (CSS vars on `:root`)

```css
--ds-bg:      #F7F6F3   /* warm off-white page background */
--ds-surface: #FFFFFF   /* card/panel surfaces */
--ds-border:  #E2E0DB   /* all borders */
--ds-ink-1:   #18171A   /* primary text, headings, dark buttons */
--ds-ink-2:   #5A5856   /* secondary text, descriptions */
--ds-ink-3:   #9A9895   /* placeholders, metadata, labels */
--ds-accent:  #18171A   /* same as ink-1; no color accent exists */
```

**Tailwind primary scale (runtime config override):**
```
50:#F0EFEB  100:#EDECE9  200:#E2E0DB  300:#CAC8C2
400:#9A9895  500:#5A5856  600:#18171A  700:#18171A  900:#0A090B
```

### 2.2 Rules (non-negotiable)

- **Zero blue anywhere.** No yellow, green, or red status colors.
- Primary buttons: `style="background: #18171A;"` + white text
- Secondary buttons: white bg + `style="border-color: var(--ds-border); color: var(--ds-ink-1);"`
- Status badges: neutral pills — bg `#F0EFEB` or `#EDECE9`, border `#CAC8C2`, text ink-1/ink-2
- Accepted/Published badges: inverted — `background: #18171A; color: #fff`
- Active nav item: `bg-primary-50 text-primary-700` (resolves to #F0EFEB bg + #18171A text)
- Blockquote/notices: `border-l-4` with `border-left-color: #18171A`, bg `#F0EFEB`
- Focus rings: monochrome only (primary-200/300 scale) — never blue Tailwind default

### 2.3 Typography

- Body: `DM Sans` (Google Fonts)
- Brand wordmark: `DM Serif Display` italic — class `eaiou-brand`
- Section headers: `DM Serif Display` italic — class `eaiou-title`

---

## 3. File Structure

```
app/
  main.py                       # FastAPI app, middleware, routes, exception handlers
  database.py                   # SQLAlchemy engine + get_db()
  deps.py                       # get_current_user() — reads session cookie
  routers/
    auth.py                     # GET/POST /auth/login, GET /auth/logout
    papers.py                   # GET /papers/, /papers/{id}, /papers/submitted/{id}, /papers/status/{id}
    author.py                   # GET /author/, /author/submit, POST /author/submit
  templates/
    base.html                   # PUBLIC shell: top nav + footer; owns all CSS vars + CDN imports
    index.html                  # /
    about.html                  # /about
    policy.html                 # /policy
    report.html                 # /report
    base/
      base.html                 # Layout variant base
      layout_a.html             # Layout variant A
      layout_b.html             # Layout variant B
      layout_c.html             # Layout variant C
    auth/
      login.html                # /auth/login
    admin/
      base_admin.html           # ADMIN shell (extends base.html)
      dashboard.html            # admin dashboard
      users.html                # user list
      user_form.html            # create/edit user
    author/
      base_author.html          # AUTHOR shell (extends base.html)
      dashboard.html            # /author/
      drawer.html               # slide-out drawer component
      intake.html               # submission intake view
      submission_hub.html       # submission hub
      submit.html               # /author/submit
      workspace.html            # author workspace
    editor/
      base_editor.html          # EDITOR shell (extends base.html)
      dashboard.html            # editor dashboard
      queue.html                # review queue
      paper_detail.html         # paper detail for editor
    papers/
      list.html                 # /papers/
      detail.html               # /papers/{id}
      submitted.html            # /papers/submitted/{id}
      status.html               # /papers/status/{id}
      submit.html               # legacy — redirects to /author/submit
    partials/
      notification_card.html    # reusable notification card
      widget_toolbar.html       # reusable toolbar widget
    errors/
      404.html                  # 404 handler
      500.html                  # 500 handler
    views/                      # WIREFRAMES — 17 files pending promotion to shell inheritance
      01_communication_center.html
      13_status_tracking.html
      14_notifications.html
      15_reviewer_performance.html
      16_reviewer_matching.html
      17_communication_center.html
      18_reviewer_management.html
      19_reviewer_database.html
      20_conflict_detection.html
      21_review_model.html
      22_the_article.html
      23_plagiarism_check.html
      24_transparency.html
      25_online_platforms.html
      28_submission_form.html
      29_version_control.html
      30_submission_dashboard.html
```

---

## 4. Route Table

### Public Routes
```
GET  /                             → templates/index.html
GET  /about                        → templates/about.html
GET  /policy                       → templates/policy.html
GET  /policy/temporal-blindness    → templates/policy/temporal-blindness.html
GET  /policy/ai-disclosure         → templates/policy/ai-disclosure.html
GET  /policy/open-access           → templates/policy/open-access.html
GET  /policy/intelligence-blindness → templates/policy/intelligence-blindness.html
GET  /health                       → JSON health check
GET  /api/docs                     → Swagger UI
GET  /papers/                      → templates/papers/list.html
GET  /papers/{id}                  → templates/views/22_the_article.html
GET  /papers/submitted/{id}        → templates/papers/submitted.html
GET  /papers/status/{id}           → templates/views/13_status_tracking.html
```

### Auth Routes
```
GET  /auth/login               → templates/auth/login.html
POST /auth/login               → DB-backed auth → sets session cookie → redirect /
GET  /auth/logout              → clears session → redirect /
```

### Author Routes (require login)
```
GET  /author/                  → templates/author/dashboard.html
GET  /author/dashboard         → templates/author/dashboard.html
GET  /author/submit            → templates/author/submit.html
GET  /author/drawer            → templates/author/drawer.html
GET  /author/notifications     → author notifications
POST /author/submit            → insert paper → redirect /papers/submitted/{id}
```

### Editor Routes (require login)
```
GET  /editor/                  → templates/editor/dashboard.html
GET  /editor/queue             → templates/editor/queue.html
GET  /editor/papers/{id}       → templates/editor/paper_detail.html
POST /editor/papers/{id}/status → status transition
POST /editor/papers/{id}/score  → save Q score
GET  /editor/papers/{id}/score/breakdown → Q score breakdown
```

### Admin Routes (require login)
```
GET  /admin/                   → templates/admin/dashboard.html
GET  /admin/users              → templates/admin/users.html
GET  /admin/users/new          → templates/admin/user_form.html
```

### API Routes (`/api/v1/` prefix)
87 endpoints across 12 tiers — see router files for full list.

---

## 5. Database Schema

### 5.1 Papers Table (authoritative)

```sql
paper_uuid        CHAR(36) PRIMARY KEY   -- canonical submission identity (UUID4)
cosmoid           VARCHAR(64)            -- context fingerprint for intelligence instance
title             TEXT
abstract          TEXT
authors_json      JSON                   -- [{name, orcid, affiliation}]
keywords_json     JSON
ai_disclosure_level ENUM('none','editing','analysis','drafting','collaborative')
ai_disclosure_notes TEXT
status            VARCHAR(50) DEFAULT 'draft'
  -- lifecycle: draft → submitted → under_review →
  --            revision_requested → accepted/rejected → published/archived
submitted_at      DATETIME               -- sealed at receipt; NO INDEX (Temporal Blindness)
q_overall         DECIMAL(4,2)           -- discovery sort key; NULL = unscored
created           DATETIME
modified          DATETIME
```

### 5.2 Sort Order Rule

```sql
ORDER BY q_overall IS NULL, q_overall DESC, paper_uuid ASC
```

**Never:** `ORDER BY id DESC` or `ORDER BY created DESC` — both leak submission order (Temporal Blindness violation).

### 5.3 Key Decisions

- `paper_uuid` = submission identity. `cosmoid` = context fingerprint for the intelligence session that operated on this paper. They are different things.
- `cosmoid` persists through tombstone and is never removed or overwritten.
- No hard deletes. `status` field drives lifecycle.
- `submitted_at` carries no index — intentional schema enforcement of Temporal Blindness.

---

## 6. Auth Model

### Phase 1 (current)
Single admin via `.env` credentials, authenticated against `#__eaiou_users` table (bcrypt hash).
```
ADMIN_USER=admin
ADMIN_PASS=<set>
SECRET_KEY=<set>
```

Login flow: CSRF token (session-bound) → bcrypt password verification → session cookie → redirect.
Rate limiting: 5 attempts per IP per 60 seconds.

`get_current_user(request)` returns `{"name": username, "initials": username[:2].upper()}` or `None`.

### Phase 2 (future)
Multi-user registration, role-based access (author, editor, reviewer, admin). Users table exists but registration flow is not built.

---

## 7. RS: Research State Tags

Author-applied tags, bottom-up signals indexed for discovery. Visibility: public / reviewers / editorial / private.

```
rs:LookCollab              — seeking collaboration
rs:NotTopic                — not on topic (subtypes: AnotherField, FutureWork, Tangent,
                             AbandonedHypothesis, Contradiction, NullResult)
rs:Stalled                 — work blocked (subtypes: Literature, Data, Analysis, Writing,
                             Funding, Equipment, Methodology, Collaboration, Ethics,
                             Compute, Reproducibility)
rs:ForLater                — archived for a future paper
rs:OpenQuestion            — raised but not answered
rs:NullResult              — null/negative result, positive contribution
rs:Replication             — replication study
rs:CrossDomain             — cross-domain value flagged by author
rs:Exploratory             — speculative, not yet formal claim
rs:Contradiction           — contradicts existing literature
rs:UnderReconsideration    — author reconsidering this section/claim
```

Tags feed `/discover/gaps` (gap map by domain + stall type) and `/discover/ideas` (cross-domain discovery).  
`tag_resolved=true` removes from active feeds while preserving in archive.

---

## 8. Phase Boundaries

### Phase 1 (complete — verified 2026-04-17)
- Single admin, env-based auth (bcrypt, CSRF, rate limiting, session middleware)
- Submit → confirm → public view pipeline (end-to-end verified)
- 34 database tables live against MariaDB
- 183 routes registered, 87 API endpoints across tiers 1-12
- Admin router (`routers/admin.py`) — dashboard, user CRUD, group management
- Editor router (`routers/editor.py`) — dashboard, queue, paper detail, status transitions, Q scoring
- Q scoring service (`services/qscore.py`) — 4-dimension weighted score, editor override, recompute
- Author router (`routers/author.py`) — dashboard, drawer, submit, notifications, workspace
- TemporalBlindnessMiddleware — sealed field stripping, date-sort rejection (400)
- Design system — monochrome palette, DM Sans/DM Serif Display, verified across all templates
- MCP server — 32 tools (paper.*, auth.*, user.*)
- IntelliD router — CosmoID minting, tombstone lifecycle
- 2 test papers in database

### Phase 2 (not started)
- Reviewer assignment and matching
- RS: tag ingestion, indexing, and UI
- Discovery routes (HTML frontend — API endpoints exist)
- Local DB setup script / standalone migration runner
- Multi-user registration flow (Phase 1 is single-admin via .env)

### Phase 3 (future)
- UHA address minting for papers (pending eaiou operational)
- Public API for OMMP integration
- Zenodo mirror export

---

## 9. Current Build Status (verified 2026-04-17)

### Phase 1 — Complete
- Admin router (`routers/admin.py`) — dashboard, user CRUD, group management: all routes return 200
- Editor router (`routers/editor.py`) — dashboard, queue, paper detail, status transitions, Q scoring: all routes return 200
- Q scoring service (`services/qscore.py`) — 4-dimension weighted score, editor override, recompute: verified via `/editor/papers/{id}/score/breakdown`
- Papers submission pipeline — submit → confirm → public view: end-to-end verified
- Auth — bcrypt login, CSRF protection, rate limiting, session middleware: login/logout flow verified
- TemporalBlindnessMiddleware — sealed field stripping (13 fields clean), date-sort rejection (400 on date/created/submitted_at)
- Design system — monochrome palette verified; no color words; all shells extend base; design tokens consistent
- API tiers 1-12 — 87 endpoints at `/api/v1/` prefix (papers CRUD, workflow, review, authorship, transparency, discovery, gaps, versioning, admin, logging, notifications, system)
- MCP server — 32 tools (paper.*, auth.*, user.*)
- The app runs live against MariaDB with 2 test papers

### Phase 1 — Known Gaps
- `papers/submit.html` is a legacy placeholder — `/author/submit` is the active route
- `base/base.html` defines an alternate color palette (river, amber, sage, coral, violet) for layout variants; not used by primary templates

### Phase 2 — Not Started
- Reviewer assignment and matching
- RS: tag ingestion, indexing, and UI
- Discovery routes (HTML frontend — API endpoints exist)
- Local DB setup script / standalone migration runner
- Multi-user registration flow (Phase 1 is single-admin via .env)

---

## 10. Verification Checklist (run after any template change)

```bash
# No hardcoded hex outside design token set:
grep -rn "#[0-9a-fA-F]\{6\}" app/templates/ | grep -v "18171A\|F7F6F3\|FFFFFF\|E2E0DB\|5A5856\|9A9895\|F0EFEB\|EDECE9\|CAC8C2\|0A090B\|ECECEC"

# No Temporal Blindness violations in templates:
grep -rn "id DESC\|created DESC\|submitted_at" app/templates/

# All shells extend base.html:
grep -rL "extends.*base" app/templates/admin/ app/templates/author/ app/templates/editor/

# No color words in templates:
grep -rni "text-blue\|text-red\|text-green\|text-yellow\|bg-blue\|bg-red\|bg-green\|bg-yellow" app/templates/
```
