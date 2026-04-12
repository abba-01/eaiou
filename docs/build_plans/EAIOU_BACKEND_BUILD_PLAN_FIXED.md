# EAIOU — Backend Build Plan (Corrected for FastAPI + Laravel)

**Version:** 2.0.0 — 2026-04-12  
**Author:** Eric D. Martin — ORCID: 0009-0006-5944-1742  
**Purpose:** This document is the corrected authoritative backend build plan for EAIOU using the actual target architecture:

- **FastAPI Python** = primary application layer
- **Laravel PHP** = backend/services layer
- **Claude Code** on `wy.eaiou.org` = implementation assistant
- **No Joomla component/plugin/module assumptions**
- **No CMS-native workflow, custom field, tag, or extension-install assumptions unless explicitly retained as legacy reference only**

This corrected plan preserves the valid product and data requirements from the earlier backend plan while removing the platform assumptions that treated the system as `com_eaiou`, a Joomla-native article layer, and a plugin/module-driven CMS implementation. The older backend plan explicitly did all of those things and should now be treated as legacy reference material, not direct implementation instruction. fileciteturn3file1

---

## 0. RULES FOR CLAUDE CODE

1. Read this entire file before writing code.
2. The corrected SSOT is the constitutional source. If any older build plan conflicts with it, the corrected SSOT wins.
3. Build in phase order. Do not skip dependency layers.
4. Preserve feature boundaries, but do not force them into legacy plugin packaging unless that packaging is intentionally reintroduced in the new architecture.
5. No hard deletes. Tombstone/archive wherever policy requires record preservation.
6. No public date sorting. Public discovery and paper listings sort by `q_signal DESC`.
7. No indexes on sealed temporal fields unless Eric explicitly changes the doctrine.
8. Test each backend domain in isolation before integrating it into orchestration or UI layers.
9. Log all state transitions, governance unlocks, review submissions, nudger sends, publish events, and other critical mutations.
10. Do not improvise architecture from old CMS-era terminology.

---

## 1. PLATFORM STACK (FIXED)

| Layer | Technology | Notes |
|---|---|---|
| OS | RHEL/AlmaLinux family on cPanel host | Production server |
| Web | Apache / reverse proxy stack as configured on host | Existing server environment |
| Python | FastAPI | Primary application layer |
| PHP | Laravel | Backend/services layer |
| Database | MariaDB 10.x | InnoDB, utf8mb4 |
| Host | wy.eaiou.org | Operational server |
| Doc root | `/home/eaiou/public_html` | Existing deployment root |
| DB prefix | `xd6w5_` | Replace `#__` placeholders accordingly |

### 1.1 Server Reality Rule
The older plan described a CMS-centric stack with:
- `com_eaiou`
- Joomla-native articles
- custom fields
- categories
- workflows
- plugin-per-feature packaging
- modules
- webservices plugin registration

Those assumptions are no longer canonical. They may still contain useful product logic, but they are not implementation truth. fileciteturn3file1

### 1.2 Deployment Rule
Backend deliverables should now be described as one of:
- FastAPI app/router/service/middleware/job
- Laravel service/controller/job/admin utility/integration
- shared database schema
- frontend-consumed API
- operational script

Do not describe new backend work as:
- component install
- plugin install
- module install
- Joomla workflow assignment
- category manager configuration
- custom field group ownership

---

## 2. CANONICAL IDENTIFIERS

| Field | Value |
|---|---|
| Brand name | eaiou |
| Site | eaiou.org |
| Operational host | wy.eaiou.org |
| DB table prefix | `#__eaiou_` logically, `xd6w5_eaiou_` physically |
| Media root | `/media/eaiou/{paper_uuid}/` or equivalent finalized storage root |
| API base | Must be finalized explicitly in the FastAPI/Laravel design |
| Author ORCID | 0009-0006-5944-1742 |

### 2.1 API Base Rule
The older backend and API plans assume a CMS-style base like `/api/index.php/v1/eaiou/`. That is now legacy unless you deliberately keep that route shape behind Apache/proxy rewriting. If retained, it should be treated as a compatibility path, not proof of CMS ownership. fileciteturn3file0 fileciteturn3file1

---

## 3. ARCHITECTURE

### 3.1 Primary Split

#### FastAPI owns
- core paper workflows
- primary application logic
- provenance logic
- temporal blindness enforcement
- public and domain APIs unless explicitly delegated
- forensic reader API support
- AI session handling
- Remsearch handling
- attribution logic
- q_signal computation
- audit/integrity logic
- orchestration-facing service endpoints
- discovery and gap logic unless explicitly delegated

#### Laravel owns
- backend/services support
- admin/support tooling
- integrations
- queue/workbench support if assigned
- operator-facing dashboards if assigned
- service wrappers where PHP is a better fit
- supporting auth/session services if deliberately chosen

### 3.2 Required Explicit Ownership Decisions
Before implementation begins, write down:
- who owns authentication
- who owns role storage
- who owns migrations
- who owns admin UI
- who owns public API namespace
- who owns webhooks
- who owns API key issuance
- who owns email/scheduler delivery
- who owns file ingestion/storage orchestration

If unclear, mark as **undecided** and resolve before coding.

### 3.3 Feature Boundary Principle
Preserve feature boundaries conceptually, but map them to actual implementation forms:
- transparency → API/resource/service/middleware
- AI usage → API/resource/service
- ORCID link → integration service
- open reports → review/publication service
- research tags/state → domain metadata service
- deadline nudger → scheduled job
- collaboration → paper metadata + discovery service

Do not force feature boundaries into legacy plugin packaging just because the older backend plan did so. fileciteturn3file1

---

## 4. DATABASE SCHEMA (11 TABLES)

Use the canonical schema as the authoritative logical database model. Preserve the 11-table coverage from the earlier plan, but implement it independent of CMS packaging. The older plan’s table set is still the best current domain model even though its surrounding implementation framing is wrong. fileciteturn3file1

### 4.1 `#__eaiou_papers`
Bridge/hub record for the archival paper object.

Key fields:
- id
- article/content bridge reference if retained, otherwise replace with canonical content reference strategy
- paper_uuid
- authorship_mode
- status
- submission_version
- doi
- authors_json
- submission_sealed_at
- sealed_by
- submission_hash
- submission_capstone
- acceptance_sealed_at
- publication_sealed_at
- bundle_path
- q_signal
- standard lifecycle fields

**Rule:** no public indexing or sort behavior built on sealed temporal fields.

### 4.2 `#__eaiou_versions`
Per-paper version lineage:
- paper_id
- label
- file_path
- content_hash
- ai_flag
- ai_model_name
- generated_at
- notes
- lifecycle fields

### 4.3 `#__eaiou_ai_sessions`
AI session records:
- paper_id
- session_label
- ai_model_name
- start_time
- end_time
- tokens_in
- tokens_out
- redaction_status
- session_notes
- session_hash
- answer_box_session_id
- answer_box_ledger_capstone
- lifecycle fields

### 4.4 `#__eaiou_didntmakeit`
Discarded or excluded AI/human-generated content:
- session_id
- prompt_text
- response_text
- exclusion_reason
- redacted
- redaction_hash
- lifecycle fields

### 4.5 `#__eaiou_remsearch`
Literature triage / reviewed-source ledger:
- paper_id
- citation_title
- citation_source
- citation_link
- source_type
- used
- reason_unused
- fulltext_notes
- lifecycle fields

### 4.6 `#__eaiou_review_logs`
Review events:
- paper_id
- reviewer_id
- version_reviewed
- review_date
- rubric_overall
- rubric_originality
- rubric_methodology
- rubric_transparency
- rubric_ai_disclosure
- rubric_crossdomain
- recommendation
- review_notes
- labels_json
- unsci_flagged
- open_consent
- lifecycle fields

### 4.7 `#__eaiou_attribution_log`
Contribution ledger:
- paper_id
- contributor_name
- orcid
- role_description
- contribution_type
- is_human
- is_ai
- ai_tool_used
- version_id
- lifecycle fields

### 4.8 `#__eaiou_plugins_used`
Rename conceptually if desired, but preserve purpose:
- paper_id
- plugin_name / tool_name
- plugin_type / tool_type
- execution_context
- exec_log_path
- exec_timestamp
- lifecycle fields

### 4.9 `#__eaiou_api_keys`
Programmatic access credentials:
- user_id
- api_key
- description
- access_level
- status
- last_used
- lifecycle fields

### 4.10 `#__eaiou_api_logs`
Append-only audit log:
- api_key_id
- endpoint
- method
- request_data
- response_code
- log_hash
- prior_hash
- log_timestamp
- lifecycle fields

**Rule:** no update or delete path in application logic.

### 4.11 `#__eaiou_quality_signals`
Quality signal event records:
- paper_id
- review_log_id
- q_overall
- q_originality
- q_methodology
- q_transparency
- q_ai_disclosure
- q_crossdomain
- q_signal
- weight_override
- computed_at
- lifecycle fields

---

## 5. RELATIONSHIPS

Core relationships preserved from the earlier plan:

- paper hub → versions
- paper hub → AI sessions
- paper hub → review logs
- paper hub → Remsearch
- paper hub → attribution log
- paper hub → tool/plugin usage log
- paper hub → quality signal records
- AI session → Didn’t Make It
- user → reviews
- user → API keys
- API key → API logs
- review log → quality signal record

Translate these into the actual ORM/data access patterns used by FastAPI and Laravel.

---

## 6. ROLE / ACL MODEL

### 6.1 Canonical Roles
- Public
- Registered
- Author
- Reviewer
- Editor
- EIC
- Admin
- APIClient

### 6.2 Permission Matrix (preserved logically)
| Action | Public | Author | Reviewer | Editor | EIC | Admin |
|---|---|---|---|---|---|---|
| View published papers | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| View q_signal breakdown | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| View sealed submission dates | ✗ | ✗ | ✗ | ✗ | governance only | governance only |
| Submit paper | ✗ | ✓ | — | ✓ | ✓ | ✓ |
| View own submission status | ✗ | ✓ | — | ✓ | ✓ | ✓ |
| Accept/decline review invite | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ |
| Submit review rubric | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ |
| Set Un Scientific flag | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ |
| Assign reviewers | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ |
| Accept/reject paper | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ |
| Publish paper | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ |
| Governance unlock sealed dates | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ |
| Manage API keys | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| View API logs | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| View AI session logs | ✗ | limited | ✓ | ✓ | ✓ | ✓ |
| View full Didn’t Make It content | ✗ | limited | limited metadata | limited | ✓ | ✓ |

### 6.3 Implementation Rule
Do not implement ACL via legacy CMS user-group instructions from the old backend plan unless you are deliberately mapping them into the new stack. The older plan’s group inheritance and admin config steps are role intent, not current implementation truth. fileciteturn3file1

---

## 7. DOMAIN MODEL AND STATE

### 7.1 Paper Object
A paper is now a domain object exposed through FastAPI and supported by Laravel services, not a CMS article by default.

The older plan explicitly mapped article fields like title, alias, introtext, fulltext, tags, categories, and workflows into “paper” behavior. Preserve only the useful domain semantics, not the CMS assumption. fileciteturn3file1

### 7.2 Workflow States
Canonical state machine remains:

- draft
- submitted
- under_review
- decision_pending
- revisions_requested
- accepted
- published
- archived / rejected tombstone path

### 7.3 Workflow Rules
- submit → temporal sealing event
- accepted → capstone trigger
- rejected → archive/tombstone, not hard delete
- publish → plugin/feature guards or equivalent service guards must pass
- all mutations logged

### 7.4 Research State Vocabulary
Preserve the research-state vocabulary and collaboration/stalled/not-topic semantics from the older plan, but implement them as platform-native metadata or domain tags, not necessarily CMS tags. fileciteturn3file1

---

## 8. BUILD PHASES (STRICT ORDER)

### PHASE 1 — Foundation
Goal: schema deployed, ownership decisions written, core services scaffolded, CRUD verified.

| Step | Task | Verification |
|---|---|---|
| 1.1 | Deploy all 11 `eaiou_*` tables | Tables exist with expected columns |
| 1.2 | Define role model in app/auth layer | Roles visible and enforceable |
| 1.3 | Write ACL policy mapping | Permission matrix implemented |
| 1.4 | Write workflow/state machine config | All states and transitions represented |
| 1.5 | Scaffold FastAPI domain services | CRUD/API tests pass for core objects |
| 1.6 | Scaffold Laravel support/services layer | Admin/integration utilities boot |
| 1.7 | Verify CRUD for all 11 entities | create/read/update/list/tombstone works |
| 1.8 | Build canonical navigation/role map for frontend integration | routes/menus align with corrected SSOT |

### PHASE 2 — Core Feature Services
Goal: implement feature boundaries as services/jobs/middleware.

| Step | Feature | Implementation Form | Verification |
|---|---|---|---|
| 2.1 | API route registration | FastAPI router structure | routes resolve |
| 2.2 | Temporal Blindness | middleware/service filter | sealed fields stripped, date sort blocked |
| 2.3 | q_signal | service + public exposure | badge/breakdown data available |
| 2.4 | Transparency | domain service | completeness enforcement works |
| 2.5 | AI Usage | domain service | disclosure enforcement works |
| 2.6 | ORCID Link | integration service | OAuth/linking works |
| 2.7 | Un Scientific | domain service | flagging/resolution works |
| 2.8 | Open Reports | review publication service | public/private modes work |
| 2.9 | Research state tagging | metadata/discovery service | discovery surfaces consume it |
| 2.10 | Open Collaboration | metadata/discovery service | collaboration data exposed |
| 2.11 | Deadline Nudger | scheduled job/service | dry-run then live notifications work |

### PHASE 3 — Submission + Review Operations
| Step | Task | Verification |
|---|---|---|
| 3.1 | Submission wizard backend support | all 6 steps persist and validate |
| 3.2 | Temporal sealing on submit | sealed fields + hashes written |
| 3.3 | Bundle importer/storage service | files land in canonical storage paths |
| 3.4 | Reviewer console backend | rubric submit works |
| 3.5 | q_signal recomputation on review event | paper q_signal updates |
| 3.6 | Editorial management services | reviewer assignment / decision flows work |
| 3.7 | Author revision upload flow | new versions created cleanly |
| 3.8 | Capstone trigger on acceptance | deposition/queue event fires |

### PHASE 4 — Discovery + Gap Layer
| Step | Task | Verification |
|---|---|---|
| 4.1 | discover/ideas | entropy-novelty ranked ideas returned |
| 4.2 | discover/gaps | gap map aggregation returned |
| 4.3 | discover/trends | trend data returned |
| 4.4 | discover/open | open collaboration data returned |
| 4.5 | entropy trace endpoint | ESR metric returned if retained |
| 4.6 | dataset link logic | cross-linking works if retained |
| 4.7 | observer registration | PKI/observer flow works if retained |

### PHASE 5 — Hardening + Production
| Step | Task | Verification |
|---|---|---|
| 5.1 | API log hash chain | log_hash/prior_hash computed |
| 5.2 | chain integrity endpoint | verified/broken status works |
| 5.3 | governance unlock | restricted and logged |
| 5.4 | rate limiting | throttles enforced |
| 5.5 | security headers | headers live |
| 5.6 | backup/recovery | restore tested |
| 5.7 | performance tuning | baseline acceptable |

---

## 9. BACKEND FILE STRUCTURE (CORRECTED)

This replaces the old `com_eaiou` file-tree assumption with implementation-neutral stack ownership.

```text
backend/
  fastapi/
    app/
      api/
      services/
      models/
      schemas/
      middleware/
      jobs/
      integrations/
      auth/
      db/
  laravel/
    app/
      Services/
      Jobs/
      Http/
      Console/
      Models/
      Support/
    routes/
    config/
shared/
  schemas/
  docs/
storage/
  media/
  bundles/
  logs/
```

### 9.1 Mapping Rule
Translate old backend-plan sections like:
- Controller
- Model
- Table
- View
- tmpl
- forms
- site/admin MVC

into:
- FastAPI routers/services/schemas/models
- Laravel services/controllers/jobs/support tools
- shared schema docs and storage strategy

The older file structure in the prior backend plan is legacy CMS packaging, not the new architecture. fileciteturn3file1

---

## 10. FEATURE OWNERSHIP MAP

| Feature | New Owner |
|---|---|
| Temporal Blindness | FastAPI middleware/service |
| q_signal compute | FastAPI service, possibly queued |
| Transparency enforcement | FastAPI domain service |
| AI disclosure enforcement | FastAPI domain service |
| ORCID linking | Laravel integration service or shared auth integration |
| Un Scientific flags | FastAPI review/domain service |
| Open Reports | FastAPI publication/review service |
| Research state metadata | FastAPI metadata/discovery service |
| Open Collaboration | FastAPI metadata/discovery service |
| Deadline nudger | Laravel job or shared scheduler job |
| API key issuance/logging | FastAPI/Laravel shared security ownership, explicitly chosen |
| Admin dashboard | Laravel or separate admin frontend, explicitly chosen |

---

## 11. VERIFICATION CHECKLIST

### Foundation
- [ ] all 11 tables exist
- [ ] ownership decisions written
- [ ] roles implemented
- [ ] ACL tested
- [ ] workflow represented in code

### Temporal Blindness
- [ ] no sealed dates in public responses
- [ ] no public date sorting
- [ ] no indexes on sealed fields

### Data Integrity
- [ ] submit triggers sealing
- [ ] acceptance triggers capstone flow
- [ ] no hard deletes
- [ ] append-only API logs enforced

### Reviews and q_signal
- [ ] review submission creates review log
- [ ] review submission creates quality signal event
- [ ] q_signal recomputes and denormalizes

### Discovery
- [ ] paper lists sort by q_signal
- [ ] gap/idea/collab surfaces work
- [ ] research-state metadata feeds discovery cleanly

### Integrations
- [ ] ORCID flow works if enabled
- [ ] GitGap sync works if enabled
- [ ] notifications work in dry-run then live mode

---

## 12. WHEN THINGS GO WRONG

### “The old backend plan says to install a component/plugin/module”
Translate it into:
- FastAPI router/service/middleware/job
- Laravel service/job/admin utility
- frontend-consumed API capability

Do not follow the packaging literally. The old plan is explicit about component/plugin/module construction, which is no longer canonical. fileciteturn3file1

### “I’m not sure who should own this feature”
Stop and mark:
- undecided
- options
- recommended owner
- reason

### “A legacy plan conflicts with the corrected SSOT”
The corrected SSOT wins.

### “I think I should optimize sealed date access”
Do not. That is doctrine-sensitive.

### “I want to hard delete stale records”
Do not. Tombstone/archive.

---

## 13. REPLACEMENT RULE

Do not describe this backend as:
- `com_eaiou`
- a Joomla-native article layer
- a CMS component
- a plugin suite
- a module-driven build
- a workflow/category/tag/custom-field admin configuration exercise

Describe it as:
- a FastAPI primary application backend
- a Laravel backend/services support layer
- a shared research integrity data platform
- an auditable provenance and peer-review system

---

*End of EAIOU Backend Build Plan v2.0.0*  
*Corrected for FastAPI + Laravel architecture*  
*Temporal Blindness enforced. q_signal remains the sort river.*
