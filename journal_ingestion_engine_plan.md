# Journal Ingestion Engine — Backend-First Plan

**Date:** 2026-05-01 19:50 PDT
**Author:** Eric D. Martin
**Stack decision:** Postgres + Flask + Flask-AppBuilder (FAB). Backend-first, MVC Joomla-style. No separate frontend codebase. Login-to-admin and the admin panel generates all the UI from the data models.

## Why this stack

**Postgres** (not MariaDB):
- `pgvector` extension handles vector similarity search natively — no separate Qdrant or vector DB required. Single-database stack.
- `pg_trgm` for fuzzy text search across titles/abstracts.
- Native full-text search (`tsvector`, GIN indexes) for keyword search across the Crossref corpus.
- JSONB columns store full Crossref records without schema migration headache as their format evolves.
- Mature partitioning for time-series/year-based corpus splits.

**Flask** (not FastAPI):
- Synchronous request model fits CRUD-heavy admin work better than FastAPI's async (which we'd want for the public review API).
- Mature `Flask-AppBuilder` ecosystem for the Joomla-style admin generation.
- Easier to layer SQLAlchemy + Alembic migrations + Flask-Login + Flask-AppBuilder without async-bridge contortions.

**Flask-AppBuilder** (FAB, the Joomla-style framework):
- Auto-generates views, forms, menus, and CRUD UI from SQLAlchemy model classes.
- Built-in RBAC (roles, permissions, users) — ships with login and admin user management.
- Menus + sub-menus + page categories — exactly the Joomla mental model.
- Used by Apache Superset (heavy production validation).
- Custom views for non-CRUD actions (e.g., "Trigger ingest", "Re-embed batch").

**The result:** all the UI is admin-generated. Eric logs in, sees the menu, clicks Journals → table of all 35,910 ingested files → can filter, sort, edit, trigger actions. No HTML/CSS/JS we write by hand except small bits of customization. The "front end" is whatever FAB renders from the model + view definitions.

## Architecture diagram

```
┌────────────────────────────────────────────────────────┐
│  Flask + Flask-AppBuilder app (admin/backend)          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Login (Flask-Login + FAB user table)            │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Admin menus (auto-generated from models):       │  │
│  │   • Corpus / Journals / Papers / Authors         │  │
│  │   • Ingest jobs / Embedding jobs / Search index  │  │
│  │   • Subjects / Venues / DOI registry             │  │
│  │   • Reports / Dashboards (FAB-rendered)          │  │
│  │   • System / Logs / RBAC                         │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Custom views (non-CRUD):                        │  │
│  │   • POST /admin/ingest/trigger                   │  │
│  │   • POST /admin/embed/batch                      │  │
│  │   • POST /admin/search/query (testbench)         │  │
│  │   • GET  /admin/corpus/health                    │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
                         ↓
                    SQLAlchemy
                         ↓
┌────────────────────────────────────────────────────────┐
│  Postgres 16 + pgvector + pg_trgm + tsvector           │
│   • papers (id, doi, title, abstract, raw JSONB,       │
│     embedding vector(384), tsvector, ...)              │
│   • journals (id, issn, container_title, ...)          │
│   • authors (id, name, orcid, ...)                     │
│   • subjects (id, label, parent_id)                    │
│   • paper_authors (many-to-many)                       │
│   • paper_subjects (many-to-many)                      │
│   • ingest_jobs (id, status, file_count, ...)          │
│   • embed_jobs (id, status, paper_count, model, ...)   │
│   • search_logs (id, query, hits, latency, ...)        │
│   • ab_user, ab_role, ab_permission_view (FAB)         │
└────────────────────────────────────────────────────────┘
                         ↓
                  Background workers
                         ↓
┌────────────────────────────────────────────────────────┐
│  Celery + Redis (or Postgres-as-queue with `pq`)       │
│   • crossref_ingest_worker.py                          │
│   • embedding_worker.py                                │
│   • reindex_worker.py                                  │
└────────────────────────────────────────────────────────┘
                         ↓
                  Disk / corpus storage
                         ↓
┌────────────────────────────────────────────────────────┐
│  /mnt/volume_nyc3_1777600565990/                       │
│   • datasets-peerreview.7z (corpus archive)            │
│   • datasets-peerreview/  (decompressed jsonl.gz dir)  │
└────────────────────────────────────────────────────────┘
```

## Wireframe — admin views, modules, menus, actions, content

### Top-level menu structure (Joomla-style)

```
File ▾                Corpus ▾              Workers ▾           Search ▾           System ▾
─────                 ──────                ────────            ──────             ──────
• Logout              • Papers              • Ingest Jobs       • Testbench        • Logs
                      • Journals            • Embed Jobs        • Search Index     • Users
                      • Authors             • Reindex Jobs      • Saved Queries    • Roles
                      • Subjects            • Worker Health                        • Permissions
                      • DOI Registry                                               • Health
                      • Bulk Actions
                      • Import from File
```

### Module breakdown

| Module | Purpose | FAB View Type | Key Actions |
|---|---|---|---|
| **Papers** | Browse/search/edit ~155M Crossref records (sample-loaded for MVP) | `ModelView` + custom search filter | view, edit metadata, mark canonical, hide, re-embed |
| **Journals** | Container titles, ISSNs, scope statements | `ModelView` | view, edit scope, link to subjects |
| **Authors** | Author records with ORCID disambiguation | `ModelView` | merge duplicates, link to papers |
| **Subjects** | Subject taxonomy (Crossref subjects + custom) | `ModelView` (tree view) | add/edit hierarchy, map to RDoC/HiTOP |
| **DOI Registry** | DOI canonical store + reverse lookup | `ModelView` | resolve DOI, view full Crossref record |
| **Bulk Actions** | Multi-row operations | Custom `BaseView` | re-embed selected, mark scope, export |
| **Import from File** | Upload + parse Crossref jsonl.gz | Custom `BaseView` with FileUpload | trigger ingest_job, monitor progress |
| **Ingest Jobs** | Async corpus ingestion runs | `ModelView` (read-mostly) | view status, view errors, cancel |
| **Embed Jobs** | Async embedding generation | `ModelView` (read-mostly) | view status, retry, view model used |
| **Reindex Jobs** | Search-index rebuilds | `ModelView` (read-mostly) | trigger, view progress |
| **Worker Health** | Live worker status | Custom dashboard view | restart workers, view queue depth |
| **Search Testbench** | Query-vs-corpus interactive testing | Custom `BaseView` | run vector query, run text query, compare |
| **Search Index** | Index maintenance + stats | Custom dashboard view | rebuild GIN, vacuum, analyze |
| **Saved Queries** | Stored queries used by handlers | `ModelView` | name, save, edit, delete |
| **Logs** | Application + access logs | Custom view | tail, filter, download |
| **Users / Roles / Permissions** | RBAC | FAB built-in | standard FAB CRUD |
| **Health** | DB stats, disk, vector index health | Custom dashboard view | view |

### Action buttons (inline on rows + bulk-action dropdown)

- **Per-paper:** view raw Crossref JSON, view embedding (vector preview), recompute embedding, mark scope canonical, hide from search, link to journal, link to subjects.
- **Per-journal:** view all papers, view scope statement (editable), set RDoC mapping, set HiTOP mapping.
- **Per-subject:** view all papers, view child subjects, edit parent.
- **Per-job:** cancel, retry failed batch, download error log.
- **Bulk:** re-embed selected, export selected as CSV/JSON, mark scope, delete (soft-delete).

### Content types

- **Paper** — Crossref record + computed fields (title_tsvector, abstract_tsvector, embedding vector(384), embedding_model, embedded_at, scope_canonical_at, hidden_at). Raw `record_jsonb` keeps the original Crossref payload.
- **Journal** — container_title, issn, scope_statement (editable), rdoc_mapping (jsonb), hitop_mapping (jsonb), policy_url.
- **Author** — name, orcid (nullable), affiliation_history (jsonb), canonical_id (FK self for merge tracking).
- **Subject** — label, parent_id (self-FK for tree), source ("crossref" / "rdoc" / "hitop" / "custom"), description.
- **Job (ingest/embed/reindex)** — uuid id, status enum, started_at, completed_at, error_log text, progress_count int, target_count int, params jsonb, triggered_by user_id.

## Database schema (Postgres 16 + pgvector + pg_trgm)

```sql
-- enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- core tables (pseudo-DDL, full version in app/models/ when scaffolded)
CREATE TABLE journals (
  id BIGSERIAL PRIMARY KEY,
  issn VARCHAR(16) UNIQUE,
  container_title TEXT NOT NULL,
  scope_statement TEXT,
  rdoc_mapping JSONB,
  hitop_mapping JSONB,
  policy_url TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX journals_title_trgm ON journals USING GIN (container_title gin_trgm_ops);

CREATE TABLE authors (
  id BIGSERIAL PRIMARY KEY,
  given_name TEXT,
  family_name TEXT,
  orcid VARCHAR(19) UNIQUE,
  affiliation_history JSONB,
  canonical_id BIGINT REFERENCES authors(id),
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX authors_family_trgm ON authors USING GIN (family_name gin_trgm_ops);

CREATE TABLE subjects (
  id BIGSERIAL PRIMARY KEY,
  label TEXT NOT NULL,
  parent_id BIGINT REFERENCES subjects(id),
  source VARCHAR(32) NOT NULL,  -- crossref | rdoc | hitop | custom
  description TEXT,
  UNIQUE (label, source)
);

CREATE TABLE papers (
  id BIGSERIAL PRIMARY KEY,
  doi VARCHAR(255) UNIQUE NOT NULL,
  title TEXT NOT NULL,
  abstract TEXT,
  journal_id BIGINT REFERENCES journals(id),
  published_year INT,
  published_date DATE,
  raw_record JSONB NOT NULL,   -- full Crossref payload
  title_tsv TSVECTOR,
  abstract_tsv TSVECTOR,
  embedding vector(384),       -- all-MiniLM-L6-v2; bump to 768 for mpnet later
  embedding_model VARCHAR(64),
  embedded_at TIMESTAMPTZ,
  scope_canonical_at TIMESTAMPTZ,  -- nullable; set when human-reviewed
  hidden_at TIMESTAMPTZ,            -- nullable; soft-delete
  ingested_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX papers_doi_idx ON papers (doi);
CREATE INDEX papers_journal_idx ON papers (journal_id);
CREATE INDEX papers_year_idx ON papers (published_year);
CREATE INDEX papers_title_tsv_idx ON papers USING GIN (title_tsv);
CREATE INDEX papers_abstract_tsv_idx ON papers USING GIN (abstract_tsv);
CREATE INDEX papers_embedding_idx ON papers USING ivfflat (embedding vector_cosine_ops) WITH (lists = 1000);

CREATE TABLE paper_authors (
  paper_id BIGINT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  author_id BIGINT NOT NULL REFERENCES authors(id) ON DELETE CASCADE,
  author_order SMALLINT NOT NULL,
  PRIMARY KEY (paper_id, author_id)
);

CREATE TABLE paper_subjects (
  paper_id BIGINT NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  subject_id BIGINT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  PRIMARY KEY (paper_id, subject_id)
);

CREATE TABLE ingest_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  status VARCHAR(32) NOT NULL,
  file_count INT,
  files_processed INT DEFAULT 0,
  papers_inserted INT DEFAULT 0,
  papers_updated INT DEFAULT 0,
  errors_count INT DEFAULT 0,
  error_log TEXT,
  params JSONB,
  triggered_by INT,  -- FAB user id
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ
);

CREATE TABLE embed_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  status VARCHAR(32) NOT NULL,
  model VARCHAR(64) NOT NULL,
  target_count INT,
  processed_count INT DEFAULT 0,
  errors_count INT DEFAULT 0,
  error_log TEXT,
  triggered_by INT,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ
);

CREATE TABLE search_logs (
  id BIGSERIAL PRIMARY KEY,
  query_text TEXT,
  query_vector vector(384),
  search_type VARCHAR(16),   -- 'text' | 'vector' | 'hybrid'
  hits_count INT,
  top_doi VARCHAR(255),
  latency_ms INT,
  user_id INT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- FAB tables created automatically on first migration: ab_user, ab_role, ab_permission, ab_view_menu, ab_permission_view, ab_user_role
```

## Resource requirements

### Compute (droplet edm.aybllc.org, 8 vCPU / 16 GB RAM)

| Workload | CPU | RAM | Disk | Notes |
|---|---|---|---|---|
| **Postgres 16 + pgvector** | 2 vCPU baseline; 4–6 vCPU during ingest | 4 GB shared_buffers; 8 GB during ingest | corpus + indexes + WAL: budget 350 GB on `/mnt/volume_nyc3_...` | 470 GB free; corpus ~25 GB after dedup; indexes + WAL ~150 GB |
| **Flask app + FAB** | 1 vCPU | 1 GB | 200 MB | runs on root `/dev/vda1` |
| **Celery workers (Postgres-backed queue)** | 2–4 vCPU pooled | 1–2 GB | 100 MB | embedding-batch worker is the heavy one |
| **Embedding model in-memory** | 1 vCPU | 800 MB (MiniLM-L6) or 1.6 GB (mpnet-base) | 100 MB cache | runs in worker process |
| **OS / nginx / sshd / cron** | 0.5 vCPU | 1 GB | — | shared |
| **Headroom** | 0.5–1 vCPU | 1–2 GB | — | leaves room for eaiou + checksubmit + Perfex on same box |

**Verdict:** runs on the existing droplet without upgrading. If embedding throughput becomes the bottleneck, scale workers; if Postgres becomes the bottleneck, give it more shared_buffers + work_mem.

### Software / libraries

```
Python 3.12
Flask 3.x
Flask-AppBuilder 4.x
Flask-Login (transitive via FAB)
Flask-WTF (transitive via FAB)
SQLAlchemy 2.x
Alembic
psycopg 3 (psycopg[binary])
pgvector (Python client)
sentence-transformers (all-MiniLM-L6-v2 → all-mpnet-base-v2 upgrade path)
celery + redis OR pq (Postgres-as-queue)
gunicorn (production WSGI)
```

System packages on droplet:
```
postgresql-16
postgresql-16-pgvector
postgresql-contrib-16  (pg_trgm, pg_stat_statements)
redis-server  (if using Celery + Redis; skip if using pq)
```

### Estimated build effort

| Phase | Effort | Description |
|---|---|---|
| **Phase 0** — Stack bootstrap | 1 day | Install Postgres + extensions, Flask + FAB skeleton, login working, dashboard rendering |
| **Phase 1** — Schema + models | 1 day | All tables + SQLAlchemy models + Alembic migration + FAB ModelViews wired |
| **Phase 2** — Ingest worker | 2 days | jsonl.gz parser, batch insert with conflict-resolution, ingest_jobs tracking, custom Trigger Ingest view |
| **Phase 3** — Embedding worker | 1–2 days | sentence-transformers wired, batch embedding, embed_jobs tracking |
| **Phase 4** — Search testbench | 1 day | Custom view: text query, vector query, hybrid query; latency display; result preview |
| **Phase 5** — Polish + RBAC + deploy | 1 day | Roles/permissions, Worker Health view, Logs view, systemd unit, nginx vhost on `journals.aybllc.org` or similar subdomain |

**Total: 7–8 days** for a polished single-developer build.

## Why backend-only / no frontend

Eric's directive: "no front end at all except a login to the backend." The reasoning is sound:

1. **Eric is the operator, not the customer.** This service ingests + indexes + serves; it doesn't sell directly. Customers (eaiou, checksubmit, future external partners) hit the API. Operators (Eric, Mae) hit the admin.
2. **FAB renders all the operational UI from models.** No bespoke React/Vue/Svelte to maintain.
3. **The "frontend" in MVC-Joomla-style means: views generated from controllers + models.** Add a model class → admin menu item appears. Add a custom action → button appears. The HTML/CSS is FAB's, not ours.
4. **Theming is one config file** if we want to brand it later.

If a public-facing search UI ever becomes necessary, it can be added as a separate static-site or as part of eaiou's existing frontend. The journal-ingestion engine itself stays admin-only.

## API surface (for external callers, behind the admin)

Even with no public frontend, the engine exposes JSON API for downstream services like checksubmit and eaiou:

```
POST   /api/v1/search/text?q=...&limit=10
POST   /api/v1/search/vector  (body: {abstract: "..."}, optional venue filter)
POST   /api/v1/search/hybrid  (body: {q: "...", abstract: "..."})
GET    /api/v1/papers/{doi}
GET    /api/v1/journals/{issn}
GET    /api/v1/journals/{issn}/papers
POST   /api/v1/admin/ingest    (auth required; admin-only)
POST   /api/v1/admin/embed      (auth required; admin-only)
```

Auth: Flask-Login session for admin UI, signed JWT or partner key for API. Same pattern as checksubmit's partner-key model — reuse the auth layer.

## File structure

```
/scratch/repos/journals-engine/                    (new repo, separate from eaiou)
├── README.md
├── requirements.txt
├── alembic.ini
├── alembic/
│   └── versions/
│       └── 0001_initial_schema.py
├── app/
│   ├── __init__.py                                  (Flask app factory)
│   ├── config.py
│   ├── models.py                                    (SQLAlchemy models)
│   ├── views/
│   │   ├── __init__.py                              (FAB ModelView definitions)
│   │   ├── ingest.py                                (custom Trigger Ingest view)
│   │   ├── embed.py                                 (custom Trigger Embed view)
│   │   ├── search.py                                (search testbench view)
│   │   └── health.py                                (worker-health dashboard)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── search.py                                (public search endpoints)
│   │   ├── papers.py                                (DOI lookup)
│   │   └── admin.py                                 (admin ingest/embed triggers)
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   ├── ingest.py                                (jsonl.gz → DB)
│   │   ├── embed.py                                 (text → vector)
│   │   └── reindex.py
│   └── utils/
│       ├── crossref_parser.py                       (Crossref jsonl.gz schema handler)
│       └── search.py                                (text + vector query helpers)
├── deploy/
│   ├── postgresql.conf.snippet                      (tuning params)
│   ├── systemd/
│   │   ├── journals-engine.service
│   │   └── journals-engine-worker.service
│   ├── nginx/
│   │   └── journals-engine.conf
│   └── install.sh
├── scripts/
│   ├── decompress_corpus.sh
│   ├── init_db.sh
│   └── seed_subjects.py
└── tests/
    ├── test_models.py
    ├── test_ingest_worker.py
    ├── test_embed_worker.py
    ├── test_search_api.py
    └── conftest.py
```

## Decisions to confirm with Eric

These are the small confirms-required calls before scaffolding starts:

1. **Subdomain or path:** `journals.aybllc.org` (subdomain) vs `aybllc.org/journals/` (path). Recommend subdomain for clean nginx config and per-service certs.
2. **Embedding model:** start with `all-MiniLM-L6-v2` (384-dim, fast, free) or jump straight to `all-mpnet-base-v2` (768-dim, better quality, slower)?
3. **Queue backend:** Celery + Redis (industry standard, more moving parts) vs `pq` (Postgres-as-queue, fewer moving parts, simpler ops)?
4. **Filter strategy for first ingest:** full corpus (155M+ records, 2 days), last 5 years (~50M records, 12 hours), or eaiou-relevant venues only (~5M records, 90 minutes)?
5. **Repo location:** `/scratch/repos/journals-engine/` (new repo, github.com/abba-01/journals-engine) or `/scratch/repos/eaiou/journals-engine/` (subdir of eaiou monorepo)?

I have defaults for all five and will proceed unless you override:
- subdomain `journals.aybllc.org`
- start with MiniLM-L6
- Celery + Redis (smoother long-term, even if slightly more setup)
- last-5-years for first ingest (compromise: useful corpus, 12-hour build time)
- new repo at `/scratch/repos/journals-engine/`

## Next concrete actions

After the cosmoid.org Perfex task lands and this plan is read:

1. Spin up Postgres 16 with pgvector + pg_trgm on droplet
2. `git init` the journals-engine repo locally
3. Scaffold the Flask + FAB skeleton with login working and one test ModelView
4. Apply Alembic 0001 migration
5. Smoke test: log in to admin, see one row of test data, click through.

Phase 0 ships in 1 day from start. Then you can decide: keep going, hand off, or pause.
