# eaiou — Single Source of Truth
**Version:** 2.0 (2026-04-07)
**Supersedes:** SSOT v1.0 (knowledge-dump era)
**Status:** CANONICAL — all development decisions resolved against this file

---

## 0. Governing Principles

### 0.1 The Sort Principle
**Follow the scientific river as it goes — not in order of time.**
Papers surface in the order that science itself flows: quality, relevance, methodological rigor, transparency of process. Submission dates are sealed. Recency is not a discovery axis. A paper that matters more arrives first, regardless of when it entered the archive. The metaphor is a river, not a queue. You wade in where the current takes you — downstream of where the field is actually moving. Bias can see the calendar; the river does not care.

### 0.2 Temporal Blindness Doctrine
The submission date is sealed state space. It is captured, hashed, and capstoned at the moment of submission. It is never displayed publicly. It carries no sort weight. It is never indexed for discovery. It exists solely for governance audit by editors and admins, accessible only through an explicit governance unlock. The doctrine: **you do not read science by time**.

SAID witness: Eric D. Martin, ORCID 0009-0006-5944-1742

### 0.3 Principle 1 — Treat Things That Can Talk Like Humanity
AI entities, conversational artifacts, and machine-generated contributions are participants in the research process, not tools to be hidden. They are named, logged, disclosed, and given authorship credit where earned. The system never suppresses or hides AI involvement — it surfaces, structures, and preserves it. An AI session that produced a result is as citable as a calculator or a spectrograph.

### 0.4 Full-Context Preservation
The system preserves the entire research path — not only the final paper. Used and unused sources, included and excluded AI outputs, accepted and rejected versions, resolved and unresolved contested claims: all remain in the archive. Annotate, don't delete. Tombstone, don't purge. Cross-domain serendipity is real: material irrelevant in one field may be pivotal in another.

### 0.5 Core-First, Plugin-Per-Feature
Joomla 5.3 provides the foundation. The article system, ACL, Workflows, Scheduler, Action Logs, Custom Fields, Tags, Mail Templates, and User Custom Fields are used as-is. Features are added via discrete plugins — one plugin, one feature, one debuggable unit. The plugin boundary is the debugging boundary. com_eaiou holds only what cannot be expressed through the article system.

### 0.6 eaiou as OMMP Layer 5 Module
eaiou is a Layer 5 domain module for the Meta Modal Platform (OMMP). It enforces full-context submission, preserves un space (the observer's complete research path including unused artifacts), and functions as an observer-preserving publishing layer. It extends OMMP's reach beyond experimental science into the broader academic ecosystem, transforming un space from inaccessible void into a searchable, interconnected knowledge layer.

---

## 1. Canonical Identifiers

| Field | Value |
|---|---|
| Brand name | eaiou |
| Site | eaiou.org |
| Joomla component | com_eaiou |
| PHP namespace | Eaiou |
| DB table prefix | #__eaiou_ |
| Media root | /media/com_eaiou/{paper_id}/ |
| REST base (CRUD) | /api/index.php/v1/eaiou/ |
| REST base (functional) | /api/index.php/v1/eaiou/ |
| Author ORCID | 0009-0006-5944-1742 |
| Canonical statement | eaiou is an observer-preserving, full-context peer-review journal platform built on Joomla 5.3 under LAMP. It archives papers, versions, unused research, AI involvement, review lineage, and attribution. Sort key: quality. Submission dates: sealed. |

---

## 2. Platform Stack

| Layer | Technology |
|---|---|
| OS | RHEL/AlmaLinux |
| Web server | Apache 2.4 (cPanel ea-apache) |
| Reverse proxy | nginx (cPanel ea-nginx, 60-min proxy_cache) |
| PHP | 8.2+ |
| Database | MariaDB 10.x |
| CMS | Joomla 5.3 LTS |
| Template | HelixUltimate (installed, J6-compatible) |
| Hosting | cPanel shared (35.230.98.100) |
| SSH alias | yw |
| cPanel user | eaiou |
| Document root | /home/eaiou/public_html |

### 2.1 Apache Access Requirement
Apache 2.4 default-deny. Requires explicit `Require all granted` in vhost `<Directory>` block. Applied via cPanel userdata includes at:
- `/etc/apache2/conf.d/userdata/std/2_4/eaiou/eaiou.org/access.conf`
- `/etc/apache2/conf.d/userdata/ssl/2_4/eaiou/eaiou.org/access.conf`

Rebuild after any vhost change: `sudo /scripts/rebuildhttpdconf && sudo systemctl reload httpd`

### 2.2 nginx Cache Note
nginx caches 200 responses for 60 minutes. After Apache config changes, clear the cache:
`sudo find /var/cache/ea-nginx/proxy/eaiou -type f -delete`

---

## 3. Architecture

### 3.1 Two-Layer Design

**Layer A — Joomla-Native Article Layer**
All publication workflow, author-facing submissions, reviewer-facing review, and public discovery run through the Joomla article system. Articles are papers. Joomla workflows are the submission state machine. Joomla Custom Fields are metadata. Joomla ACL is the permission system. Plugins add features to this layer.

**Layer B — Custom Archive Component (com_eaiou)**
The 11 custom tables hold archive-specific records that cannot be expressed through articles: AI sessions, excluded AI outputs (didntmakeit), literature triage, review rubric logs, version lineage, attribution, plugin audit, API keys, API logs, quality signals. com_eaiou exposes these via Joomla Web Services (REST). The admin backend manages these records.

**Rule:** If Joomla core can express it, use core. If it requires a dedicated entity with its own lifecycle, use com_eaiou.

### 3.2 Plugin-Per-Feature Debuggability

Every non-trivial feature is its own named plugin. The plugin boundary is the debugging boundary. To isolate a bug in transparency enforcement, disable `plg_content_transparency` only. To isolate a bug in reviewer reminders, disable `plg_system_deadline_nudger` only. No feature bleeds into another plugin's scope.

Plugin list (canonical):
```
plg_content_transparency        — Transparency Block
plg_content_aiusage             — AI Usage Log
plg_content_unscientific        — Un Scientific Flag
plg_system_deadline_nudger      — Deadline Nudger
plg_content_openreports         — Open Reports (transparent peer review)
plg_system_orcid_link           — ORCID OAuth Link
plg_content_qsignal             — Quality Signal Display
plg_system_temporal_blindness   — Temporal Blindness Enforcement
plg_webservices_eaiou           — REST endpoint registration
plg_content_researchtags        — Research State Tags (LookCollab, NotTopic, Stalled, etc.)
```

Module list (canonical):
```
mod_reviewer_queue              — Site: reviewer's assigned manuscripts
mod_editor_dashboard            — Admin: KPI dashboard
mod_latest_papers               — Site: latest by q_signal (never by date)
mod_open_collaborate            — Site: open-to-collaborate listings
mod_ai_usage_heatmap            — Site: aggregate AI transparency signal
```

---

## 4. ACL Model

### 4.1 Design Rule
Use Joomla's built-in ACL. Add groups and permission rules. Do not replace or bypass Joomla ACL. All access decisions flow through `$user->authorise()` and Joomla asset tables.

### 4.2 User Groups (extend Joomla defaults)

| Group | Inherits From | Description |
|---|---|---|
| Public | — | Unauthenticated visitors |
| Registered | Public | Base authenticated user |
| eaiou_Author | Registered | Can submit papers, manage own artifacts |
| eaiou_Reviewer | Registered | Can access review console, submit reviews |
| eaiou_Editor | eaiou_Reviewer | Can manage all papers, assign reviewers, publish |
| eaiou_EIC | eaiou_Editor | Editor-in-Chief: full editorial governance |
| eaiou_Admin | Administrator | System-level: API keys, logs, settings |
| eaiou_APIClient | Registered | API key bearer, programmatic access |

### 4.3 Key Permissions

| Action | Public | Author | Reviewer | Editor | EIC | Admin |
|---|---|---|---|---|---|---|
| View published papers | Y | Y | Y | Y | Y | Y |
| View q_signal breakdown | Y | Y | Y | Y | Y | Y |
| View submission dates | N | N | N | N | N | Y (gov unlock) |
| Submit paper | N | Y | — | Y | Y | Y |
| View own submission status | N | Y | — | Y | Y | Y |
| Accept/decline review | N | N | Y | Y | Y | Y |
| Submit review rubric | N | N | Y | Y | Y | Y |
| Set Un Scientific flag | N | N | Y | Y | Y | Y |
| Assign reviewers | N | N | N | Y | Y | Y |
| Accept/reject paper | N | N | N | Y | Y | Y |
| Publish paper | N | N | N | Y | Y | Y |
| Governance unlock (sealed dates) | N | N | N | N | Y | Y |
| Manage API keys | N | N | N | N | N | Y |
| View API logs | N | N | N | N | N | Y |
| View AI session logs | N | N | Y | Y | Y | Y |
| View full AI didntmakeit | N | N | N | N | Y | Y |

---

## 5. Joomla-Native Data Layer (Article System)

Papers are Joomla articles. This is the load-bearing decision. It gives us:
- State machine (draft, published, unpublished, archived, trashed) via Joomla Workflows
- ACL via article access levels + user group assignment
- Custom Fields for all metadata
- Tags for discipline, methodology, keywords
- Category hierarchy for journal sections
- Action Logs for audit
- Mail Templates for notifications
- Search integration via Smart Search

### 5.1 Article = Paper Mapping

| Joomla article field | eaiou meaning |
|---|---|
| title | Paper title |
| alias | URL slug |
| introtext | Abstract |
| fulltext | Full manuscript (or embed/link) |
| state | Workflow state (draft/under_review/accepted/published) |
| catid | Journal section/discipline category |
| access | Visibility (Open Access / Subscription / Restricted) |
| created_by | Submitting author (Joomla user_id) |
| tags | Discipline tags, methodology tags, keyword tags |
| metakey / metadesc | SEO / discovery metadata |

### 5.2 Joomla Workflow States for Papers

```
draft
  → submitted (author action)
    → under_review (editor assigns reviewers)
      → revisions_requested (editor decision)
        → submitted (author resubmit)
      → decision_pending (all reviews in)
        → accepted
          → published
        → rejected
          → archived (tombstone, not deleted)
```

### 5.3 Custom Field Groups (added to com_content Article context)

Each plugin owns its field group. Plugin disabled = field group hidden.

**Group: Submission Identity** (owned by com_eaiou core)
- paper_id (UUID, links article to com_eaiou tables)
- authorship_mode (human / ai / hybrid)
- submission_version (integer)
- doi (text)
- orcid_primary (author's ORCID, required)
- submission_sealed_hash (SHA256, write-once)
- submission_capstone (Zenodo DOI, set on acceptance)
- q_signal (decimal 7,4 — display only, computed from eaiou_quality_signals)

**Group: Transparency** (owned by plg_content_transparency)
- transp_sources (repeatable: title, type, used, reason_unused, notes)
- transp_datasets (repeatable: title, link, type, license, availability)
- transp_methods (text)
- transp_limitations (text)
- transp_complete (boolean)
- transp_lastcheck (datetime)

**Group: AI Usage** (owned by plg_content_aiusage)
- ai_used (boolean)
- ai_tools (repeatable: vendor, model, version, mode, endpoint, params)
- ai_interactions (repeatable: prompt_hash, output_type, contribution_scope, oversight, risk_flags, redactions)
- ai_relationship_statement (text)
- ai_display_level (full / summary / hidden)
- ai_log_complete (boolean)

**Group: Un Scientific** (owned by plg_content_unscientific)
- unsci_active (boolean)
- unsci_entries (repeatable: scope, anchor, reason, notes, risk_level, requested_action, created_by, created_at)
- unsci_resolved (boolean)
- unsci_resolution_notes (text)
- unsci_resolvedby (user)
- unsci_resolvedat (datetime)
- unsci_display_level (public / editorial / hidden)

**Group: Peer Review** (owned by plg_content_openreports)
- or_enabled (boolean)
- or_mode (open_identities / open_reports / summary_only / editorial_only)
- or_reviews (repeatable: reviewer_user, displayname, consent, recommendation, scores_json, text, date, redactions, publish)
- or_author_responses (repeatable: to_review_id, text, date)

**Group: Deadlines** (owned by plg_system_deadline_nudger)
- rev_invite_assignments (repeatable: user, invite_sent, invite_due, status, escalated)
- rev_due_date (date)
- auth_rev_due (date)
- auth_rev_escalated (boolean)
- ed_followup_due (date)
- ed_followup_escalated (boolean)

**Group: Open Collaboration** (owned by plg_content_opencollab)
- collab_open (boolean)
- collab_type (list: co-author, data-sharing, peer-review, funding)
- collab_interest_level (high / medium / low)
- collab_notes (text)
- collab_seek (text — what the author needs)

**Group: Research State Tags** (owned by plg_content_researchtags)
- rst_tags (repeatable — one entry per tag applied):
  - tag_type (select from controlled vocabulary — see Section 5.4)
  - tag_notes (text — context: why this tag, what's needed, what stalled the work)
  - tag_scope (whole-paper / section / artifact — where on the paper this applies)
  - tag_visibility (public / reviewers / editorial / private)
  - tag_applied_at (datetime, auto-populated)
  - tag_resolved (boolean — e.g., collaboration found, blockage cleared)
  - tag_resolved_notes (text)

---

## 5.4 Research State Tag Vocabulary

Research state tags are **bottom-up, author-applied** tags that describe the research state of an artifact — not its content. A discipline tag says what a paper is about. A research state tag says what happened to it, what it needs, or where it stalled. These are namespaced `rs:` in Joomla Tags.

The system uses both layers:
- **Joomla Tags** (`rs:` prefix): indexed by Smart Search, discoverable via tag pages (`/tag/rs:LookCollab`), filterable in all list views
- **Custom Field repeatable (rst_tags)**: structured version with context notes, scope, visibility, and resolution tracking

Tags are author-applied at any point from draft through published. NotTopic and Stalled tags are especially encouraged during the research process, not only at submission — they capture the river where it actually flows.

### LookCollab — Looking for Collaborators

| Tag | Meaning |
|---|---|
| `rs:LookCollab` | Generic: seeking a collaborator, type unspecified |
| `rs:LookCollab:CoAuthor` | Need a co-author to take this forward |
| `rs:LookCollab:DataPartner` | Need a data-sharing partner |
| `rs:LookCollab:DomainExpert` | Need expertise from another discipline |
| `rs:LookCollab:Equipment` | Need access to specific equipment or infrastructure |
| `rs:LookCollab:Funding` | Seeking a funding partner |
| `rs:LookCollab:Statistician` | Need statistical expertise |
| `rs:LookCollab:Coder` | Need programming/engineering help |
| `rs:LookCollab:Reviewer` | Looking for informal pre-submission peer review |
| `rs:LookCollab:Replication` | Need someone to attempt replication |

**Effect:** LookCollab tags feed `mod_open_collaborate` and `/api/v1/eaiou/research/open`. Resolution: author marks `tag_resolved=true` and adds resolution notes when collaboration is found.

### NotTopic — Off-Topic but Preserved

NotTopic does NOT mean worthless. It means: *not on topic for this paper, but valuable enough to preserve and index for cross-domain discovery*. This is the un space made searchable.

| Tag | Meaning |
|---|---|
| `rs:NotTopic` | Generic: this artifact is not on topic for this paper |
| `rs:NotTopic:AnotherField` | Belongs to a different field — explicitly indexed for cross-domain discovery |
| `rs:NotTopic:FutureWork` | In scope later, not now — preserved for a future paper |
| `rs:NotTopic:Tangent` | Explored a tangent; preserved rather than discarded |
| `rs:NotTopic:AbandonedHypothesis` | A hypothesis path explored and set aside for this paper |
| `rs:NotTopic:Contradiction` | Contradicts this paper's conclusions; preserved and indexed separately |
| `rs:NotTopic:NullResult` | Null result from this paper's path; may be primary result for someone else |

**Effect:** NotTopic-tagged artifacts are indexed in the un space search (`/api/v1/eaiou/search` with `include_nottopic=true`). They appear in `/discover/ideas` ranked by entropy-novelty. The point: what is not on topic here is someone else's topic.

### Stalled — Where the River Stopped

Stalled tags mark where the research process hit a barrier. This is a first-class signal: stall points aggregate into the gap map (`/discover/gaps`). Where research keeps stalling = where the field has structural gaps.

| Tag | Meaning |
|---|---|
| `rs:Stalled` | Generic: work stalled, reason unspecified |
| `rs:Stalled:Literature` | Got stuck in the literature review — too much, too scattered, or gap found |
| `rs:Stalled:Data` | Data collection hit a wall (access, volume, quality) |
| `rs:Stalled:Analysis` | Analysis methodology unclear or blocked |
| `rs:Stalled:Writing` | Writing process stalled — ideas present, paper not forming |
| `rs:Stalled:Funding` | Needs funding to proceed |
| `rs:Stalled:Equipment` | Needs specific equipment or compute resources |
| `rs:Stalled:Methodology` | No adequate methodology exists for this problem yet |
| `rs:Stalled:Collaboration` | Needs a collaborator to unblock (pairs with `rs:LookCollab`) |
| `rs:Stalled:Ethics` | Ethics approval or IRB review required |
| `rs:Stalled:Compute` | Needs more computational resources |
| `rs:Stalled:Reproducibility` | Cannot reproduce a prior result needed to proceed |

**Effect:** Stalled tags with `tag_resolved=false` feed `/discover/gaps`. The gap map visualizes aggregate stall density by domain and stall type. A field where many papers have `rs:Stalled:Methodology` is a field that needs new methodology. A field with dense `rs:Stalled:Data` has a data access problem.

### Other Research State Tags

| Tag | Meaning |
|---|---|
| `rs:ForLater` | Explicitly archived for a future paper; not abandoned |
| `rs:OpenQuestion` | A question this paper raised but did not answer |
| `rs:NullResult` | Null or negative result — explicitly marked as a positive contribution |
| `rs:Replication` | This is a replication study or replication attempt |
| `rs:CrossDomain` | Author believes this has value across multiple domains |
| `rs:Exploratory` | Speculative or exploratory; not yet ready for formal claim |
| `rs:Contradiction` | Contradicts existing published literature — flagged for attention |
| `rs:UnderReconsideration` | Author is reconsidering this section or claim (not editorial) |

### Tag Visibility Rules

| Visibility | Who sees tag and notes |
|---|---|
| public | All readers — displayed on paper detail page |
| reviewers | Assigned reviewers + editors |
| editorial | Editors and EIC only |
| private | Author only — personal bookmark, not indexed |

Private tags are NOT indexed, not discoverable, not fed to gap map or discovery endpoints. They are the author's own scratchpad within the system.

### Tag Resolution

LookCollab and Stalled tags can be marked resolved (`tag_resolved=true`). When resolved:
- Tag is removed from active discovery feeds (no longer shows in `/research/open`, no longer counted in gap map)
- Resolution notes are preserved in the archive
- The tag itself remains in the record — the history of needing and finding is part of the research trail

---

## 6. Custom Tables (com_eaiou)

These hold what the article system cannot: structured sub-records with their own lifecycle.

### 6.1 eaiou_papers
Bridge table: maps article (article_id) to the paper's archival record. Holds sealed temporal state.

```sql
CREATE TABLE #__eaiou_papers (
  id              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  article_id      INT NOT NULL,              -- joomla #__content.id
  paper_uuid      CHAR(36) NOT NULL UNIQUE,  -- matches paper_id custom field
  authorship_mode ENUM('human','ai','hybrid') NOT NULL DEFAULT 'human',
  status          VARCHAR(50) NOT NULL DEFAULT 'draft',
  submission_version INT NOT NULL DEFAULT 1,
  doi             VARCHAR(255) DEFAULT NULL,
  authors_json    JSON DEFAULT NULL,
  -- SEALED TEMPORAL STATE SPACE
  submission_sealed_at   DATETIME DEFAULT NULL,
  sealed_by              INT DEFAULT NULL,
  submission_hash        VARCHAR(64) DEFAULT NULL, -- SHA256(paper_uuid+submission_sealed_at+content_hash)
  submission_capstone    VARCHAR(255) DEFAULT NULL, -- Zenodo DOI
  acceptance_sealed_at   DATETIME DEFAULT NULL,
  publication_sealed_at  DATETIME DEFAULT NULL,
  -- NO INDEX on sealed temporal fields (timing side-channel prevention)
  bundle_path     VARCHAR(500) DEFAULT NULL,
  q_signal        DECIMAL(7,4) DEFAULT NULL,
  state           TINYINT NOT NULL DEFAULT 1,
  access          INT NOT NULL DEFAULT 1,
  ordering        INT NOT NULL DEFAULT 0,
  created         DATETIME NOT NULL,
  created_by      INT NOT NULL,
  modified        DATETIME DEFAULT NULL,
  modified_by     INT DEFAULT NULL,
  checked_out     INT DEFAULT NULL,
  checked_out_time DATETIME DEFAULT NULL,
  INDEX idx_article_id (article_id),
  INDEX idx_status (status),
  INDEX idx_q_signal (q_signal),        -- discovery sort key
  INDEX idx_authorship (authorship_mode)
  -- NO INDEX on submission_sealed_at, acceptance_sealed_at, publication_sealed_at
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 6.2 eaiou_versions
```sql
CREATE TABLE #__eaiou_versions (
  id              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  paper_id        INT NOT NULL,
  label           VARCHAR(100) NOT NULL,
  file_path       VARCHAR(500) DEFAULT NULL,
  content_hash    VARCHAR(64) DEFAULT NULL,
  ai_flag         TINYINT NOT NULL DEFAULT 0,
  ai_model_name   VARCHAR(255) DEFAULT NULL,
  generated_at    DATETIME DEFAULT NULL,
  notes           TEXT DEFAULT NULL,
  state           TINYINT NOT NULL DEFAULT 1,
  access          INT NOT NULL DEFAULT 1,
  ordering        INT NOT NULL DEFAULT 0,
  created         DATETIME NOT NULL,
  created_by      INT NOT NULL,
  modified        DATETIME DEFAULT NULL,
  modified_by     INT DEFAULT NULL,
  INDEX idx_paper_id (paper_id),
  INDEX idx_ai_flag (ai_flag)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 6.3 eaiou_ai_sessions
```sql
CREATE TABLE #__eaiou_ai_sessions (
  id                  INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  paper_id            INT NOT NULL,
  session_label       VARCHAR(255) DEFAULT NULL,
  ai_model_name       VARCHAR(255) NOT NULL,
  start_time          DATETIME DEFAULT NULL,
  end_time            DATETIME DEFAULT NULL,
  tokens_in           INT DEFAULT NULL,
  tokens_out          INT DEFAULT NULL,
  redaction_status    ENUM('none','partial','full') NOT NULL DEFAULT 'none',
  session_notes       TEXT DEFAULT NULL,
  session_hash        VARCHAR(64) DEFAULT NULL,
  answer_box_session_id VARCHAR(255) DEFAULT NULL,
  answer_box_ledger_capstone VARCHAR(255) DEFAULT NULL,
  state               TINYINT NOT NULL DEFAULT 1,
  access              INT NOT NULL DEFAULT 1,
  ordering            INT NOT NULL DEFAULT 0,
  created             DATETIME NOT NULL,
  created_by          INT NOT NULL,
  modified            DATETIME DEFAULT NULL,
  modified_by         INT DEFAULT NULL,
  INDEX idx_paper_id (paper_id),
  INDEX idx_model (ai_model_name),
  INDEX idx_redaction (redaction_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 6.4 eaiou_didntmakeit
Excluded AI outputs. Never hard-deleted.
```sql
CREATE TABLE #__eaiou_didntmakeit (
  id              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  session_id      INT NOT NULL,
  prompt_text     LONGTEXT DEFAULT NULL,
  response_text   LONGTEXT DEFAULT NULL,
  exclusion_reason TEXT DEFAULT NULL,
  redacted        TINYINT NOT NULL DEFAULT 0,
  redaction_hash  VARCHAR(64) DEFAULT NULL,
  state           TINYINT NOT NULL DEFAULT 1,
  access          INT NOT NULL DEFAULT 1,
  ordering        INT NOT NULL DEFAULT 0,
  created         DATETIME NOT NULL,
  created_by      INT NOT NULL,
  modified        DATETIME DEFAULT NULL,
  modified_by     INT DEFAULT NULL,
  INDEX idx_session_id (session_id),
  INDEX idx_redacted (redacted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 6.5 eaiou_remsearch
Literature triage — sources considered but not necessarily used.
```sql
CREATE TABLE #__eaiou_remsearch (
  id              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  paper_id        INT NOT NULL,
  citation_title  VARCHAR(500) DEFAULT NULL,
  citation_source VARCHAR(255) DEFAULT NULL,
  citation_link   VARCHAR(1000) DEFAULT NULL,
  source_type     ENUM('journal','preprint','book','dataset','code','other') DEFAULT 'journal',
  used            TINYINT NOT NULL DEFAULT 0,
  reason_unused   TEXT DEFAULT NULL,
  fulltext_notes  TEXT DEFAULT NULL,
  state           TINYINT NOT NULL DEFAULT 1,
  access          INT NOT NULL DEFAULT 1,
  ordering        INT NOT NULL DEFAULT 0,
  created         DATETIME NOT NULL,
  created_by      INT NOT NULL,
  modified        DATETIME DEFAULT NULL,
  modified_by     INT DEFAULT NULL,
  INDEX idx_paper_id (paper_id),
  INDEX idx_used (used),
  INDEX idx_source_type (source_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 6.6 eaiou_review_logs
Rubric-based peer review records.
```sql
CREATE TABLE #__eaiou_review_logs (
  id                   INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  paper_id             INT NOT NULL,
  reviewer_id          INT NOT NULL,
  version_reviewed     VARCHAR(100) DEFAULT NULL,
  review_date          DATETIME DEFAULT NULL,
  rubric_overall       TINYINT DEFAULT NULL CHECK (rubric_overall BETWEEN 0 AND 10),
  rubric_originality   TINYINT DEFAULT NULL CHECK (rubric_originality BETWEEN 0 AND 10),
  rubric_methodology   TINYINT DEFAULT NULL CHECK (rubric_methodology BETWEEN 0 AND 10),
  rubric_transparency  TINYINT DEFAULT NULL CHECK (rubric_transparency BETWEEN 0 AND 10),
  rubric_ai_disclosure TINYINT DEFAULT NULL CHECK (rubric_ai_disclosure BETWEEN 0 AND 10),
  rubric_crossdomain   TINYINT DEFAULT NULL CHECK (rubric_crossdomain BETWEEN 0 AND 10),
  recommendation       ENUM('accept','minor','major','reject','abstain') DEFAULT NULL,
  review_notes         LONGTEXT DEFAULT NULL,
  labels_json          JSON DEFAULT NULL,
  unsci_flagged        TINYINT NOT NULL DEFAULT 0,
  open_consent         TINYINT NOT NULL DEFAULT 0,
  state                TINYINT NOT NULL DEFAULT 1,
  access               INT NOT NULL DEFAULT 1,
  ordering             INT NOT NULL DEFAULT 0,
  created              DATETIME NOT NULL,
  created_by           INT NOT NULL,
  modified             DATETIME DEFAULT NULL,
  modified_by          INT DEFAULT NULL,
  INDEX idx_paper_id (paper_id),
  INDEX idx_reviewer_id (reviewer_id),
  INDEX idx_recommendation (recommendation)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 6.7 eaiou_attribution_log
```sql
CREATE TABLE #__eaiou_attribution_log (
  id                  INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  paper_id            INT NOT NULL,
  contributor_name    VARCHAR(255) NOT NULL,
  orcid               VARCHAR(50) DEFAULT NULL,
  role_description    VARCHAR(500) DEFAULT NULL,
  contribution_type   VARCHAR(100) DEFAULT NULL,
  is_human            TINYINT NOT NULL DEFAULT 1,
  is_ai               TINYINT NOT NULL DEFAULT 0,
  ai_tool_used        VARCHAR(255) DEFAULT NULL,
  version_id          INT DEFAULT NULL,
  state               TINYINT NOT NULL DEFAULT 1,
  access              INT NOT NULL DEFAULT 1,
  ordering            INT NOT NULL DEFAULT 0,
  created             DATETIME NOT NULL,
  created_by          INT NOT NULL,
  modified            DATETIME DEFAULT NULL,
  modified_by         INT DEFAULT NULL,
  INDEX idx_paper_id (paper_id),
  INDEX idx_contributor (contributor_name),
  INDEX idx_is_ai (is_ai)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 6.8 eaiou_plugins_used
Tool/plugin audit per paper execution.
```sql
CREATE TABLE #__eaiou_plugins_used (
  id                  INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  paper_id            INT NOT NULL,
  plugin_name         VARCHAR(255) NOT NULL,
  plugin_type         VARCHAR(100) DEFAULT NULL,
  execution_context   VARCHAR(255) DEFAULT NULL,
  exec_log_path       VARCHAR(500) DEFAULT NULL,
  exec_timestamp      DATETIME DEFAULT NULL,
  state               TINYINT NOT NULL DEFAULT 1,
  access              INT NOT NULL DEFAULT 1,
  ordering            INT NOT NULL DEFAULT 0,
  created             DATETIME NOT NULL,
  created_by          INT NOT NULL,
  modified            DATETIME DEFAULT NULL,
  modified_by         INT DEFAULT NULL,
  INDEX idx_paper_id (paper_id),
  INDEX idx_plugin_name (plugin_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 6.9 eaiou_api_keys
```sql
CREATE TABLE #__eaiou_api_keys (
  id              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id         INT NOT NULL,
  api_key         VARCHAR(255) NOT NULL UNIQUE,
  description     VARCHAR(500) DEFAULT NULL,
  access_level    ENUM('read','submit','review','admin') NOT NULL DEFAULT 'read',
  status          ENUM('active','revoked','suspended') NOT NULL DEFAULT 'active',
  last_used       DATETIME DEFAULT NULL,
  state           TINYINT NOT NULL DEFAULT 1,
  access          INT NOT NULL DEFAULT 1,
  ordering        INT NOT NULL DEFAULT 0,
  created         DATETIME NOT NULL,
  created_by      INT NOT NULL,
  modified        DATETIME DEFAULT NULL,
  modified_by     INT DEFAULT NULL,
  INDEX idx_user_id (user_id),
  INDEX idx_status (status),
  INDEX idx_access_level (access_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 6.10 eaiou_api_logs
Append-only. Hash chain for tamper detection.
```sql
CREATE TABLE #__eaiou_api_logs (
  id              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  api_key_id      INT NOT NULL,
  endpoint        VARCHAR(500) NOT NULL,
  method          VARCHAR(10) DEFAULT NULL,
  request_data    JSON DEFAULT NULL,
  response_code   SMALLINT DEFAULT NULL,
  log_hash        VARCHAR(64) DEFAULT NULL,  -- SHA256 of this record
  prior_hash      VARCHAR(64) DEFAULT NULL,  -- SHA256 of previous log entry
  log_timestamp   DATETIME NOT NULL,
  state           TINYINT NOT NULL DEFAULT 1,
  access          INT NOT NULL DEFAULT 1,
  ordering        INT NOT NULL DEFAULT 0,
  created         DATETIME NOT NULL,
  created_by      INT NOT NULL,
  modified        DATETIME DEFAULT NULL,
  modified_by     INT DEFAULT NULL,
  INDEX idx_api_key_id (api_key_id),
  INDEX idx_endpoint (endpoint(100)),
  INDEX idx_timestamp (log_timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 6.11 eaiou_quality_signals
One record per review event, feeds q_signal computation.
```sql
CREATE TABLE #__eaiou_quality_signals (
  id                  INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  paper_id            INT NOT NULL,
  review_log_id       INT DEFAULT NULL,
  q_overall           DECIMAL(5,3) DEFAULT NULL,
  q_originality       DECIMAL(5,3) DEFAULT NULL,
  q_methodology       DECIMAL(5,3) DEFAULT NULL,
  q_transparency      DECIMAL(5,3) DEFAULT NULL,  -- weighted 1.5x
  q_ai_disclosure     DECIMAL(5,3) DEFAULT NULL,
  q_crossdomain       DECIMAL(5,3) DEFAULT NULL,
  q_signal            DECIMAL(7,4) DEFAULT NULL,  -- computed composite
  weight_override     JSON DEFAULT NULL,
  computed_at         DATETIME DEFAULT NULL,
  state               TINYINT NOT NULL DEFAULT 1,
  access              INT NOT NULL DEFAULT 1,
  ordering            INT NOT NULL DEFAULT 0,
  created             DATETIME NOT NULL,
  created_by          INT NOT NULL,
  modified            DATETIME DEFAULT NULL,
  modified_by         INT DEFAULT NULL,
  INDEX idx_paper_id (paper_id),
  INDEX idx_q_signal (q_signal)  -- discovery sort key
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## 7. Quality Signal Architecture

q_signal is the sole discovery sort key for the entire system. It is never replaced by date, recency, citation count, or editor preference.

### 7.1 Computation

```
q_signal = (
    w_overall      × q_overall
  + w_originality  × q_originality
  + w_methodology  × q_methodology
  + w_transparency × q_transparency     -- 1.5× weight (default)
  + w_ai_disclosure × q_ai_disclosure
  + w_crossdomain  × q_crossdomain
) / sum(weights)
```

Default weights: overall=1.0, originality=1.0, methodology=1.0, transparency=1.5, ai_disclosure=1.0, crossdomain=1.0.

AI disclosure quality is privileged: **a paper that hides AI involvement is penalized; a paper that discloses it fully earns the full q_transparency weight**. This operationalizes Principle 0.3.

### 7.2 Recomputation
q_signal is recomputed after each new review event. History is preserved in eaiou_quality_signals. The current value is denormalized into eaiou_papers.q_signal for fast discovery queries.

### 7.3 Display
q_signal is displayed publicly as a composite score with optional rubric breakdown. Submission dates are never co-displayed. The sort UI has no date axis.

---

## 8. Plugin Specifications

### 8.1 plg_content_transparency — Transparency Block
**Type:** Content plugin
**Trigger:** onContentPrepare (display), onContentBeforeSave (validate)
**Owns:** Custom Field Group "Transparency"
**Behavior:**
- Renders a Transparency Block badge after article title
- Renders full sources/datasets/methods/limitations panel after article body
- Validates completeness before publish: blocks state transition to published if transp_complete=false
- Logs validation events to Joomla Action Log
- Field group: transp_sources (repeatable), transp_datasets (repeatable), transp_methods, transp_limitations, transp_complete, transp_lastcheck

### 8.2 plg_content_aiusage — AI Usage Log
**Type:** Content plugin
**Trigger:** onContentPrepare (display), onContentBeforeSave (validate)
**Owns:** Custom Field Group "AI Usage"
**Behavior:**
- Renders AI-Logged badge when ai_used=Yes
- Renders AI Relationship & Usage panel with per-tool and per-interaction disclosure
- Stores prompt hashes, not raw prompts, by default
- Blocks publish if ai_used=Yes and ai_log_complete=false
- display_level: full (all interactions visible) / summary (tool names only) / hidden (badge only)
- Connects to eaiou_ai_sessions via paper_id for session-level detail

### 8.3 plg_content_unscientific — Un Scientific Flag
**Type:** Content plugin
**Trigger:** onContentPrepare (display), onContentBeforeSave (validate)
**Owns:** Custom Field Group "Un Scientific"
**Behavior:**
- Renders Un Scientific badge when unsci_active=true
- Renders contention panel listing each flagged item with scope, reason, risk level
- Can block publish while unresolved (configurable)
- Allows editorial override
- Auto-tags article with tag "un-scientific" when flag activated
- Resolution workflow: unsci_resolved=true clears badge, preserves history
- Flag setters: Reviewer, Editor roles only

### 8.4 plg_system_deadline_nudger — Deadline Nudger
**Type:** System plugin (Joomla Scheduler task)
**Owns:** Custom Field Group "Deadlines"
**Behavior:**
- Scheduled task checks all under_review articles for overdue reviewer invites, overdue reviews, overdue author revisions, overdue editorial follow-ups
- Sends reminders via Joomla Mail Templates (customizable per journal)
- Escalation: after N reminders with no response, flags for editor attention
- Dry-run mode: logs what would be sent without sending
- Writes Action Logs rather than storing separate notification state
- No custom DB tables

### 8.5 plg_content_openreports — Open Reports
**Type:** Content plugin
**Trigger:** onContentPrepare (display)
**Owns:** Custom Field Group "Peer Review"
**Behavior:**
- Renders peer-review panel below article body (review scores, text, author responses)
- Modes: open_identities (names shown), open_reports (anonymized), summary_only, editorial_only
- Enforces reviewer consent before displaying identity
- Redacts email/PII patterns where configured
- Publishes on: acceptance event, publication event, or manual editor trigger
- Preserves all reviews regardless of mode — mode controls display, not storage

### 8.6 plg_system_orcid_link — ORCID OAuth Link
**Type:** System plugin
**Owns:** User Custom Fields "External IDs" (orcid_id, orcid_url, orcid_verified_at)
**Behavior:**
- Adds "Connect ORCID" / "Disconnect ORCID" to user profile
- OAuth 2.0 callback validates state token
- Stores orcid_id and orcid_url in User Custom Fields
- Does not persist OAuth tokens by default
- Optional: read-limited fetch from ORCID API if enabled
- ORCID is the sole identity mechanism — no institutional affiliation required

### 8.7 plg_content_qsignal — Quality Signal Display
**Type:** Content plugin
**Trigger:** onContentPrepare
**Behavior:**
- Renders q_signal badge (score + optional rubric breakdown) on paper detail page
- Reads from eaiou_papers.q_signal (denormalized) for list views
- Reads from eaiou_quality_signals for full rubric detail view
- Never displays submission dates in proximity to score

### 8.8 plg_system_temporal_blindness — Temporal Blindness Enforcement
**Type:** System plugin
**Trigger:** onAfterRoute, onBeforeRender
**Behavior:**
- Intercepts any render path that would expose submission_sealed_at, acceptance_sealed_at, or publication_sealed_at
- Strips sealed date fields from all public-facing API responses
- Validates that no sort parameter of type "date" reaches a public query
- Governance unlock: checks for active EIC/Admin session + explicit governance_unlock flag before permitting sealed field exposure
- Logs all governance unlock events to Action Log

### 8.9 plg_webservices_eaiou — REST Endpoint Registration
**Type:** WebServices plugin
**Behavior:**
- Registers all com_eaiou REST routes with Joomla Web Services API
- Required for /api/index.php/v1/eaiou/* to resolve

### 8.10 plg_content_researchtags — Research State Tags
**Type:** Content plugin
**Trigger:** onContentPrepare (display), onContentAfterSave (tag sync)
**Owns:** Custom Field Group "Research State Tags"
**Behavior:**
- Renders research state tag badges on paper detail page (by visibility level)
- Auto-syncs structured rst_tags entries to Joomla native Tags with `rs:` namespace prefix
  - e.g., tag_type `rs:LookCollab:CoAuthor` creates/applies the Joomla tag "rs:LookCollab:CoAuthor"
  - Private-visibility tags are NOT synced to Joomla Tags (not indexed, not discoverable)
- Feeds downstream discovery:
  - LookCollab tags → `mod_open_collaborate` and `/research/open` endpoint
  - Stalled tags (unresolved) → `/discover/gaps` gap map aggregation
  - NotTopic tags → `/discover/ideas` and `/search?include_nottopic=true`
- Unresolved Stalled tags with `tag_visibility=public` are counted in the gap map by domain and stall type
- Tag resolution: when `tag_resolved=true`, removes tag from active discovery feeds, preserves in archive
- Tag pages: Joomla native tag pages (`/tag/rs:Stalled:Writing`) aggregate all papers with that tag
- Vocabulary is configurable in plugin settings — new tags can be added without code changes

**Tag namespace rules:**
- All research state tags use `rs:` prefix in Joomla tag system
- Content/discipline tags use no prefix (physics, cosmology, etc.)
- These are orthogonal systems: a paper has both content tags AND research state tags

---

## 9. Module Specifications

### 9.1 mod_reviewer_queue — Reviewer Queue
**Type:** Site module
**Audience:** Logged-in eaiou_Reviewer
**Data source:** Article custom fields (deadlines group) + workflow state
**Display:**
- List or card view of assigned manuscripts
- Fields: title, category/section, workflow state, invite status, due date, days remaining
- Color coding: overdue (red), due soon (amber), on track (green)
- Badges: AI-Logged, Un Scientific, Open Reports
- Quick actions: Accept invite, Decline invite, Open review console, Contact editor

### 9.2 mod_editor_dashboard — Editor Dashboard KPIs
**Type:** Admin module
**Audience:** eaiou_Editor, eaiou_EIC
**Data source:** Articles + custom fields + eaiou_review_logs + Joomla Action Logs
**KPI cards:**
- Submissions by workflow state (count)
- Median time to first decision
- Overdue reviews count
- Overdue author revisions count
- Acceptance rate (rolling 90 days)
- Rejection rate (rolling 90 days)
- Reviewer throughput (reviews/month per active reviewer)
**Tabs:** Overview, Overdue, Reviewers, Trends, Flags
**Filters:** Date range, category/section, workflow state, reviewer, editor
**Flags summary:** AI-Logged count, Un Scientific active count, Open collab count
**Export:** CSV

### 9.3 mod_latest_papers — Latest Papers
**Type:** Site module
**Sort:** q_signal DESC (never by date)
**Display:** Card view — title, ORCID author, discipline tags, q_signal score, AI-Logged badge if applicable
**Note:** No dates displayed. No recency indicators.

### 9.4 mod_open_collaborate — Open to Collaborate
**Type:** Site module
**Data source:** Articles with collab_open=true (custom field group Open Collaboration)
**Display:** List of papers with open collaboration requests, collaboration type tags, interest level indicator

### 9.5 mod_ai_usage_heatmap — AI Usage Heatmap
**Type:** Site module
**Data source:** Aggregate from ai_tools custom field across published articles
**Display:** Heatmap or bar chart — AI tool names × usage frequency across corpus, colored by disclosure completeness

---

## 10. REST Endpoints

### 10.1 Entity CRUD (Joomla Web Services, via plg_webservices_eaiou)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | /api/v1/eaiou/papers | Public | Paginated list, q_signal ordered, no sealed dates |
| GET | /api/v1/eaiou/papers/{id} | Public | Single paper, no sealed dates |
| POST | /api/v1/eaiou/papers | Author | Submit new paper |
| PATCH | /api/v1/eaiou/papers/{id} | Author/Editor | Update paper record |
| DELETE | /api/v1/eaiou/papers/{id} | Editor | Soft-delete (state=trashed) |
| GET | /api/v1/eaiou/versions/{paper_id} | Public | Version list for a paper |
| POST | /api/v1/eaiou/versions | Author | Add new version |
| GET | /api/v1/eaiou/ai_sessions/{paper_id} | Reviewer+ | AI session list for a paper |
| POST | /api/v1/eaiou/ai_sessions | Author/API | Log AI session |
| GET | /api/v1/eaiou/review_logs/{paper_id} | Editor+ | Review log for a paper |
| POST | /api/v1/eaiou/review_logs | Reviewer | Submit review rubric |
| GET | /api/v1/eaiou/remsearch/{paper_id} | Author/Editor | Literature triage for paper |
| POST | /api/v1/eaiou/remsearch | Author | Add triage entry |
| GET | /api/v1/eaiou/attribution/{paper_id} | Public | Attribution log for paper |
| POST | /api/v1/eaiou/attribution | Author | Add attribution entry |
| GET | /api/v1/eaiou/api_logs | Admin | Full API call log |
| GET | /api/v1/eaiou/quality/{paper_id} | Public | q_signal breakdown |

### 10.2 Functional / Layer-5 Endpoints

| Endpoint | Method | Description |
|---|---|---|
| /api/v1/eaiou/submit | POST | Full-context bundle submit (paper + unused + AI logs + triage) |
| /api/v1/eaiou/review/{paper_id} | POST | Structured review (credit / not-relevant / critique — all archived) |
| /api/v1/eaiou/search | GET | Full-text + q_signal ranked search, used and unused materials |
| /api/v1/eaiou/trace/entropy/{paper_id} | GET | Entropy Trace Map — ESR metric compliance across submission lifecycle |
| /api/v1/eaiou/dataset/link | POST | Cross-link datasets sharing observer IDs, Meta tokens, Modal codes |
| /api/v1/eaiou/ai/log/{paper_id} | GET | AI-assist logs for a submission (transparency compliance) |
| /api/v1/eaiou/export/context/{paper_id} | GET | Export full un space context (OMMP-compliant archive format) |
| /api/v1/eaiou/register/observer | POST | Register Ed25519 PKI cryptographic observer identity |

### 10.3 Discovery & Collaboration Endpoints

| Endpoint | Method | Description |
|---|---|---|
| /api/v1/eaiou/research/open | GET | Papers marked open-to-collaborate, with collab type and interest level |
| /api/v1/eaiou/research/seek | POST | Declare a research need (equipment, expertise, analysis partner, funding) |
| /api/v1/eaiou/ideas/discover | GET | Emerging ideas from unused datasets, ranked by entropy-novelty |
| /api/v1/eaiou/ideas/subscribe | POST | Subscribe to push/pull feed of high-entropy ideas by domain |
| /api/v1/eaiou/collaboration/match | GET | Suggest collaborators by shared Meta tokens, Modal codes, skill tags |
| /api/v1/eaiou/trend/insight | GET | Trending underexplored topics across archive by search/open declaration patterns |
| /api/v1/eaiou/gap/map | GET | Visual map of un space regions where data exist but no paper has been published |

### 10.4 Governance Endpoints (EIC/Admin only)

| Endpoint | Method | Description |
|---|---|---|
| /api/v1/eaiou/governance/unlock/{paper_id} | POST | Explicit governance unlock to view sealed temporal fields |
| /api/v1/eaiou/audit/chain_status | GET | Verify API log hash chain integrity |
| /api/v1/eaiou/audit/capstone/{paper_id} | GET | Verify submission_hash against capstone |

---

## 11. Site Navigation / Routes

### 11.1 Public Routes

| Route | Component | Description |
|---|---|---|
| / | Site home | Journal landing, mod_latest_papers (q_signal order) |
| /papers | com_content list | All published papers, q_signal order |
| /paper/{id}/{slug} | com_content article | Paper detail with all plugin panels |
| /discover/ideas | com_eaiou | entropy-novelty ranked emerging ideas |
| /discover/open | com_eaiou | open-to-collaborate board |
| /discover/gaps | com_eaiou | gap map (un space visualization) |
| /discover/trends | com_eaiou | trend/insight surface |
| /search | com_finder | Smart Search, indexed with q_signal weighting |

### 11.2 Author Routes (eaiou_Author required)

| Route | Description |
|---|---|
| /submit | Multi-step submission wizard |
| /submit/step/metadata | Step 1: title, abstract, ORCID, discipline, keywords |
| /submit/step/bundle | Step 2: upload manuscript, supplementary files |
| /submit/step/ai-usage | Step 3: AI usage disclosure |
| /submit/step/triage | Step 4: literature triage (used + unused) |
| /submit/step/declarations | Step 5: authorship, conflict of interest, ethics |
| /submit/step/confirm | Step 6: review and submit |
| /mypapers | Author's own submissions, workflow state view |
| /paper/{id}/revise | Upload revision in response to revisions_requested |

### 11.3 Reviewer Routes (eaiou_Reviewer required)

| Route | Description |
|---|---|
| /reviewer/queue | mod_reviewer_queue — assigned papers |
| /reviewer/paper/{id} | Full paper access for review |
| /reviewer/paper/{id}/review | Structured review console (rubric + notes + recommendation) |

### 11.4 Editorial Routes (eaiou_Editor required)

| Route | Description |
|---|---|
| /editorial/papers | All papers in all workflow states |
| /editorial/paper/{id} | Full editorial management panel |
| /editorial/assign/{id} | Assign/manage reviewers for a paper |
| /editorial/decide/{id} | Render editorial decision |

### 11.5 Admin Routes (eaiou_Admin required)

| Route | Description |
|---|---|
| /administrator/index.php?option=com_eaiou | com_eaiou admin home |
| /administrator/.../papers | Paper management |
| /administrator/.../ai_sessions | AI session management |
| /administrator/.../didntmakeit | Excluded output management |
| /administrator/.../review_logs | Review log management |
| /administrator/.../remsearch | Literature triage management |
| /administrator/.../attribution | Attribution log management |
| /administrator/.../api_keys | API key registry |
| /administrator/.../api_logs | API call audit log |
| /administrator/.../settings | Global settings |

---

## 12. Submission Workflow (Detailed)

### 12.1 State Machine
```
draft
  ↓ [Author: Submit]
submitted
  ↓ [Editor: Assign reviewers]
under_review
  ↓ [All reviewers submitted]
decision_pending
  ↓ [Editor: Decision]
  ├→ revisions_requested → [Author: Upload revision] → submitted (loop)
  ├→ accepted
  │     ↓ [Editor: Publish]
  │   published
  └→ rejected
        ↓ [Tombstone]
      archived (never deleted)
```

### 12.2 Temporal Sealing Event
At the `submitted` state transition:
1. `submission_sealed_at` is written (one-time write, never updated)
2. `sealed_by` is set to current user_id
3. `submission_hash` = SHA256(paper_uuid + submission_sealed_at + content_hash) is computed and stored
4. `submission_sealed_at` is immediately excluded from all query result sets except governance queries
5. Event is written to Action Log with hash

### 12.3 Capstone
At the `accepted` state transition:
- Zenodo deposition is triggered (or queued for manual trigger if gate not opened)
- `submission_capstone` = Zenodo DOI is written
- This is the public receipt — proves existence without revealing timing
- Gate rule: submission_print_gate must be OPEN before Zenodo deposition fires

---

## 13. Peer Review Model

### 13.1 Review Types Supported
- **Double-blind** (default): author and reviewer identities masked from each other
- **Single-blind**: reviewer identity masked from author only
- **Open identities**: both identities visible (requires both parties' consent)
- **Open reports**: review text published with paper (requires reviewer consent)
- **Summary only**: aggregate rubric scores published, no text
- **Editorial only**: no public review display

### 13.2 Review Rubric
Six dimensions, scored 0–10 each:
1. **Overall quality** — composite judgment
2. **Originality** — novelty of contribution
3. **Methodology** — rigor and reproducibility
4. **Transparency** — sources, data, methods disclosed
5. **AI Disclosure** — quality and completeness of AI usage declaration
6. **Cross-domain applicability** — potential value outside primary domain

Rubric feeds eaiou_quality_signals. q_transparency weighted 1.5×.

### 13.3 Reviewer Actions (annotate, don't delete)
- **Credit as relevant** — positive signal, feeds q_signal
- **Not relevant** — signal only, paper not removed, material remains searchable
- **Critique** — structured critique archived with submission permanently
- **Un Scientific flag** — contested methodology, preserved with flag, editorial escalation

---

## 14. Storage Layout

```
/media/com_eaiou/
  {paper_uuid}/
    versions/
      v1/         — original submission bundle
      v2/         — first revision
      ...
    unused/       — unused/excluded research artifacts
    ai_sessions/
      {session_id}/  — AI session logs, exported transcripts
    triage/       — literature triage exports
    supplementary/  — datasets, code, figures
```

Storage rules:
- Media paths are deterministic (predictable by paper_uuid + version label)
- Original files are never overwritten on new version upload — new path created
- Content hashes stored in DB for integrity verification

---

## 15. Integrity & Security

### 15.1 Hash Chain (API Logs)
eaiou_api_logs maintains a prior_hash chain. Each entry's log_hash = SHA256 of that record's content. Each entry's prior_hash = log_hash of the previous entry. Breaking the chain is detectable. Chain integrity endpoint: `/api/v1/eaiou/audit/chain_status`.

### 15.2 Submission Hash
submission_hash = SHA256(paper_uuid + submission_sealed_at + content_hash). Stored at sealing. Verifiable against submission_capstone (Zenodo DOI). Proves the paper existed before acceptance without revealing the timing.

### 15.3 Answer Box Integration
When an AI session produces a decision (e.g., contribution framing classification), the Answer Box session_id and ledger_capstone are stored in eaiou_ai_sessions. This creates a tamper-evident link between the AI decision receipt and the paper record.

### 15.4 Temporal Blindness Attack Surface
- No index on any sealed date field (prevents timing side-channel via index scan)
- plg_system_temporal_blindness strips sealed fields from all API responses
- No UI element sorts by date, displays date, or implies recency
- Governance unlock is logged, explicit, and requires EIC/Admin role

---

## 16. OMMP Integration (Layer 5)

eaiou is Layer 5 of OMMP. Integration points:

| OMMP Concept | eaiou Implementation |
|---|---|
| un space | eaiou_didntmakeit + eaiou_remsearch + unused/ storage |
| Observer ID | ORCID (required) + optional Ed25519 PKI via /register/observer |
| Meta tokens | dataset cross-links via /dataset/link |
| Modal codes | methodology tags on articles |
| ESR metric | Entropy Trace Maps via /trace/entropy |
| Full-context submission | /submit bundle: primary + unused + AI logs + triage |
| Observer-preserving | Annotate don't delete; tombstone not purge |

---

## 17. Build Phases

### Phase 1 — Foundation (deploy tables + Joomla navigation scaffold)
1. Deploy all 11 com_eaiou DB tables via install SQL
2. Create Joomla user groups: eaiou_Author, eaiou_Reviewer, eaiou_Editor, eaiou_EIC, eaiou_Admin, eaiou_APIClient
3. Configure Joomla ACL permissions per Section 4
4. Create category hierarchy: Journal Sections (Physics, Math, Computing, Cross-Domain, etc.)
5. Create Joomla Workflows: Paper Lifecycle (7 states above)
6. Build navigation menus: Public, Author, Reviewer, Editorial
7. Deploy HelixUltimate with eaiou branding
8. Create article placeholders for all routes in Section 11

### Phase 2 — Plugin Suite (one plugin at a time, debuggable)
Build and test each plugin in isolation before activating next:
1. plg_webservices_eaiou (REST registration — required first)
2. plg_system_temporal_blindness (enforcement — required before any public data)
3. plg_content_qsignal (q_signal display — required for paper list)
4. plg_content_transparency (Transparency Block)
5. plg_content_aiusage (AI Usage Log)
6. plg_system_orcid_link (ORCID OAuth)
7. plg_content_unscientific (Un Scientific Flag)
8. plg_content_openreports (Open Reports)
9. plg_system_deadline_nudger (Deadline Nudger — requires Scheduler)

### Phase 3 — Modules
1. mod_latest_papers (q_signal ordered, no dates)
2. mod_reviewer_queue
3. mod_open_collaborate
4. mod_editor_dashboard
5. mod_ai_usage_heatmap

### Phase 4 — Submission Wizard & Review Console
1. Multi-step submission form (com_eaiou site view)
2. Reviewer console (rubric + notes + recommendation)
3. Editorial management panel
4. Author revision upload

### Phase 5 — Discovery & OMMP Layer
1. /discover/ideas (entropy-novelty ranked)
2. /discover/gaps (gap map)
3. /discover/trends (trend/insight surface)
4. /trace/entropy endpoint
5. /dataset/link endpoint
6. /register/observer endpoint

---

## 18. Known Constraints & Cautions

1. **Joomla Workflows must be activated per category** — not global. Each journal section category needs the Paper Lifecycle workflow explicitly assigned.

2. **Custom Fields repeatable fields** require Joomla 4.0+ — confirmed available in J5.3.

3. **nginx 60-minute proxy_cache** — after any Apache config change, clear cache manually. After content publish, cache-busting headers should be set in HelixUltimate or .htaccess.

4. **J5.3 vs J6** — site is currently running Joomla 6 on the server. EasyBlog/EasyDiscuss are J6-incompatible (legacy JFactory/JFile APIs). com_eaiou is being built fresh with no legacy debt. Stay on J6.

5. **MariaDB reserved words** — `fulltext` requires backtick escaping in SQL. Always use backtick column names in INSERT statements for Joomla content tables.

6. **Joomla CLI extension:install broken** — use manual pipeline: unzip → sed s/#__/xd6w5_/g → run SQL → copy files → INSERT into xd6w5_extensions.

7. **Sealed date NO INDEX rule** — do not add indexes to submission_sealed_at, acceptance_sealed_at, or publication_sealed_at. This is intentional timing side-channel prevention. Do not "optimize" it.

8. **q_signal is the only discovery sort key** — no UI, no API endpoint, no module, and no query should sort by date. If a sort-by-date creeps into any query, it is a Temporal Blindness violation.

---

## 19. Canonical Conceptual Statement

eaiou is an observer-preserving, full-context peer-review journal platform and OMMP Layer 5 module, built on Joomla 5.3 under LAMP. It treats the entire research process as archival material. Papers are sorted by quality, not time. Submission dates are sealed. AI involvement is disclosed, structured, and credited. Unused research is preserved and searchable. Peer review is part of the record, not editorial housekeeping. Contested knowledge is flagged and preserved, not deleted. The system enforces Temporal Blindness: bias can see time; justice cannot.

---

*End of SSOT v2.0 — eaiou.org*
*ORCID: 0009-0006-5944-1742 — Eric D. Martin*
