# eaiou — Claude Context Document
**For: Claude on the Web (claude.ai) handoff sessions**
**Updated: 2026-04-10**

---

## What this project is

eaiou is a FastAPI + MariaDB peer-review journal CMS. Core doctrine:
- **Temporal Blindness** — submission timestamps sealed at receipt, never shown to reviewers or indexed
- **Intelligence Blindness** — AI involvement disclosed but not penalized in scoring
- **Full-context review** — reviewers see everything except when the paper arrived
- **Observer-preserving** — nothing is hard-deleted; tombstone model; annotate, don't purge

Author: Eric D. Martin | ORCID 0009-0006-5944-1742

---

## Stack

```
FastAPI 0.111 + Starlette SessionMiddleware
MariaDB via SQLAlchemy (pymysql driver)
Jinja2 templates (no JS framework)
Tailwind CSS via CDN (runtime config override)
Font Awesome 6.4 via CDN
```

Run: `source .venv/bin/activate && uvicorn app.main:app --reload`
Env: `.env` needs `DB_HOST DB_PORT DB_NAME DB_USER DB_PASS ADMIN_USER ADMIN_PASS SECRET_KEY`

---

## Design System — eaiou Monochrome

**Fonts:**
- Body: `DM Sans` (Google Fonts)
- Brand/titles: `DM Serif Display` italic — class `eaiou-brand` (brand wordmark) or `eaiou-title` (section headers)

**Color tokens (CSS variables on `:root`):**
```css
--ds-bg:      #F7F6F3   /* warm off-white page background */
--ds-surface: #FFFFFF   /* card/panel surfaces */
--ds-border:  #E2E0DB   /* all borders */
--ds-ink-1:   #18171A   /* primary text, headings, dark buttons */
--ds-ink-2:   #5A5856   /* secondary text, descriptions */
--ds-ink-3:   #9A9895   /* placeholders, metadata, labels */
--ds-accent:  #18171A   /* same as ink-1; no color accent exists */
```

**Tailwind primary scale (runtime override):**
```
50:#F0EFEB  100:#EDECE9  200:#E2E0DB  300:#CAC8C2
400:#9A9895  500:#5A5856  600:#18171A  700:#18171A  900:#0A090B
```

**Rules:**
- Zero blue anywhere. No yellow/green/red status colors.
- Primary buttons: `style="background: #18171A;"` with white text
- Secondary buttons: white bg + `style="border-color: var(--ds-border); color: var(--ds-ink-1);"`
- Status badges: neutral pills using `#F0EFEB / #EDECE9` bg + ink-1/2 text + `#CAC8C2` border
- Accepted/Published: inverted — `background: #18171A; color: #fff`
- Active nav: `bg-primary-50 text-primary-700` (resolves to #F0EFEB bg + #18171A text via Tailwind config)
- Blockquotes / notices: `border-l-4` with `border-left-color: #18171A`, bg `#F0EFEB`

---

## File Structure

```
app/
  main.py                    # FastAPI app, middleware, routes, exception handlers
  database.py                # SQLAlchemy engine + get_db()
  deps.py                    # get_current_user() — reads session cookie
  routers/
    auth.py                  # GET/POST /auth/login, GET /auth/logout (env-based, no users table)
    papers.py                # GET /papers/, /papers/{id}, /papers/submitted/{id}, /papers/status/{id}
    author.py                # GET /author/, /author/submit, POST /author/submit (requires login)
  templates/
    base.html                # Public layout: top nav + footer. All design system CSS lives here.
    index.html               # Homepage: hero + doctrine strip + recent papers
    about.html               # About page
    auth/login.html          # Login form
    papers/
      list.html              # Public paper list
      detail.html            # Single paper view (public)
      status.html            # Submission timeline tracker (public)
      submitted.html         # Post-submit confirmation (extends author/base_author.html)
    author/
      base_author.html       # Author workspace layout: 3-panel (sidebar + main + right panel)
      dashboard.html         # Author dashboard: stats + papers table
      submit.html            # New submission form (2-step: paper details + AI disclosure)
    policy/
      temporal-blindness.html
      intelligence-blindness.html
      ai-disclosure.html
      open-access.html
    errors/
      404.html
      500.html
```

---

## Database Table: `#__eaiou_papers`

The primary table (prefix `#__` = `eaiou_` in practice):

```sql
id                INT PK AUTO_INCREMENT
paper_uuid        CHAR(36) UNIQUE          -- random UUID4, minted at submission
cosmoid           CHAR(36)                 -- context fingerprint, minted at creation, NEVER removed
title             VARCHAR(500)
abstract          TEXT
author_name       VARCHAR(255)
orcid             VARCHAR(50)
keywords          VARCHAR(500)
ai_disclosure_level ENUM('none','editing','analysis','drafting','collaborative')
ai_disclosure_notes TEXT
status            VARCHAR(50) DEFAULT 'draft'
                  -- states: draft → submitted → under_review →
                  --         revision_requested → accepted/rejected → published/archived
submitted_at      DATETIME                 -- sealed at receipt, NO INDEX (timing side-channel)
q_overall         DECIMAL(4,2)             -- quality score, discovery sort key
created           DATETIME
modified          DATETIME
```

**Sort order rule:** `ORDER BY q_overall IS NULL, q_overall DESC, paper_uuid ASC`
Never use `id DESC` or `created DESC` as tiebreaker — that leaks submission order (Temporal Blindness violation).

---

## Auth Model (Phase 1)

Single admin. Credentials in `.env`:
```
ADMIN_USER=admin
ADMIN_PASS=<set this>
SECRET_KEY=<set this>
```

`get_current_user(request)` returns `{"name": username, "initials": username[:2].upper()}` or `None`.
No users table. Phase 2 will add proper user model.

---

## Submission Flow

```
GET  /author/submit          → author/submit.html (requires login)
POST /author/submit          → inserts paper, mints paper_uuid + cosmoid, status='submitted'
                             → redirects to /papers/submitted/{id}
GET  /papers/submitted/{id}  → papers/submitted.html (confirmation + pipeline status sidebar)
GET  /papers/{id}            → papers/detail.html (public paper view)
GET  /papers/status/{id}     → papers/status.html (timeline: Submitted→Review→Decision→Published)
```

---

## Key Architecture Decisions

- **CosmoID ≠ paper_uuid**: `paper_uuid` is the submission identity. `cosmoid` is the context fingerprint for the intelligence instance that operated on this paper. CosmoID persists through tombstone; it is never removed.
- **No hard deletes**: tombstone model. `status` field handles lifecycle. Future: `tombstone_state ENUM`.
- **Temporal fields carry no index**: intentional schema enforcement of Temporal Blindness doctrine.
- **rs: Research State Tags**: author-applied tags (rs:LookCollab, rs:NotTopic:*, rs:Stalled:*, rs:Exploratory, etc.) — bottom-up signals indexed for discovery. Tag visibility: public / reviewers / editorial / private.
- **Phase 1 scope**: single admin, no users table, no Q scoring UI, no reviewer assignment. Just: submit → confirm → view.

---

## What Is Not Yet Built

- `papers/submit.html` — legacy public submit route (may redirect to `/author/submit`)
- Local DB setup script / migration runner
- The app hasn't been run live yet (DB connection not tested)
- Phase 2: Q scoring, reviewer assignment, editor dashboard, rs: tag UI

---

## RS: Research State Tag Vocabulary (for future UI)

```
rs:LookCollab              — seeking collaboration
rs:NotTopic                — not on topic for this paper (subtypes: AnotherField, FutureWork, Tangent, AbandonedHypothesis, Contradiction, NullResult)
rs:Stalled                 — work blocked (subtypes: Literature, Data, Analysis, Writing, Funding, Equipment, Methodology, Collaboration, Ethics, Compute, Reproducibility)
rs:ForLater                — explicitly archived for a future paper
rs:OpenQuestion            — raised but not answered in this paper
rs:NullResult              — null/negative result, marked as positive contribution
rs:Replication             — replication study
rs:CrossDomain             — cross-domain value flagged by author
rs:Exploratory             — speculative, not yet ready for formal claim
rs:Contradiction           — contradicts existing literature
rs:UnderReconsideration    — author reconsidering this section/claim
```

Tags feed `/discover/gaps` (gap map by domain + stall type) and `/discover/ideas` (cross-domain discovery).
Tags can be `tag_resolved=true` to remove from active feeds while preserving in archive.
