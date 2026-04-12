# EAIOU — Development Guide (Corrected for FastAPI + Laravel)

**Version:** 2.0.0 — 2026-04-12  
**Author:** Eric D. Martin — ORCID: 0009-0006-5944-1742  
**Purpose:** This is the corrected master walkthrough for building EAIOU from the current state to production using the **actual target architecture**:

- **FastAPI Python** = primary application layer
- **Laravel PHP** = backend/services layer
- **Claude Code** on `wy.eaiou.org` = implementation assistant
- **No Joomla assumptions**
- **No component/plugin/module vocabulary unless explicitly being migrated from legacy notes**

This document replaces the Joomla-style framing found in the earlier development guide and aligns with the corrected SSOT direction. The earlier guide repeatedly described a component-style CMS build with component installs, admin extension flows, categories, tags, workflows, and plugin/module packaging that no longer matches the intended platform. fileciteturn2file0

---

## 1. BEFORE YOU BEGIN

### 1.1 What You Have
- A server at `wy.eaiou.org`
- Claude Code installed on the server
- A partially built Python app in `06_source/eaiou_app/`
- A GitGap app in `06_source/gitgap_app/`
- Build plans, SSOT material, schemas, specs, and design references
- A prior development guide that still reflects a Joomla-style architecture and must not be treated as authoritative for implementation details fileciteturn2file0

### 1.2 What You Are Building
- A **FastAPI-first** EAIOU application
- A **Laravel backend/services** layer supporting admin operations, integrations, and service utilities
- A unified data model for:
  - papers
  - versions
  - AI sessions
  - Didn’t Make It
  - Remsearch
  - review logs
  - attribution log
  - plugins used
  - API keys
  - API logs
  - quality signals
- A forensic reading environment
- A research provenance and authorship integrity platform
- GitGap integration
- CommKit integration
- Role-aware public, author, reviewer, editorial, and admin experiences

### 1.3 Server Details
| Field | Value |
|---|---|
| Server | wy.eaiou.org |
| IP | 35.230.98.100 |
| SSH | `ssh yw` |
| cPanel user | eaiou |
| Doc root | `/home/eaiou/public_html` |
| DB prefix | `xd6w5_` |
| PHP | 8.2+ / ea-php84 available |
| DB | MariaDB 10.x |

### 1.4 Core Build Rule
If any older file assumes:
- Joomla
- `com_eaiou`
- component exports
- extension install flows
- Joomla workflows
- Joomla categories/tags/custom fields
- Joomla plugin or module packaging

that material is **legacy reference only** and must be translated into FastAPI + Laravel terms before implementation. The older guide contains those assumptions throughout. fileciteturn2file0

---

## 2. PHASE 0 — ORIENTATION

### Step 0.1: Read the corrected SSOT first
Use the corrected compiled SSOT as the current constitutional source.
Priority order:
1. Corrected EAIOU compiled SSOT
2. Corrected development guide
3. Build plans, after translating any legacy assumptions
4. Legacy historical material

### Step 0.2: Read the constitutional principles
Read:
- `02_constitutional/SSOT.md`
- `02_constitutional/TEMPORAL_BLINDNESS.md`

But do not automatically obey any implementation detail that assumes a component/CMS runtime. Preserve principles, not legacy platform bindings.

### Step 0.3: Read the build plans as product specs, not platform truth
Read:
- `01_build_plans/EAIOU_BACKEND_BUILD_PLAN.md`
- `01_build_plans/EAIOU_API_BUILD_PLAN.md`
- `01_build_plans/EAIOU_MCP_BUILD_PLAN.md`
- `01_build_plans/EAIOU_FRONTEND_BUILD_PLAN.md`
- `01_build_plans/EAIOU_COMMKIT_INTEGRATION_PLAN.md`

Interpret them this way:
- features = valid
- roles = valid
- data requirements = valid
- API intent = valid
- UI intent = valid
- Joomla implementation assumptions = not binding

### Step 0.4: Scan the existing source
Review:
- `06_source/eaiou_app/`
- `06_source/gitgap_app/`

Goal:
- identify reusable Python code
- identify GitGap interfaces
- identify dead-end legacy assumptions
- determine what Laravel actually needs to own

---

## 3. CANONICAL ARCHITECTURE

### 3.1 FastAPI Owns
- primary app logic
- public API surface unless explicitly routed through Laravel
- paper workflows
- provenance logic
- temporal blindness enforcement
- forensic reader APIs
- AI session recording logic
- Remsearch logic
- attribution logic
- quality signal calculation
- audit and integrity services
- MCP enforcement layer
- most user-facing business logic

### 3.2 Laravel Owns
- backend/services support
- admin utilities if assigned
- integration services
- queue/workbench support
- support tooling
- internal operational dashboards if assigned
- auth/session brokering only if deliberately chosen

### 3.3 Never Leave Undefined
Before building, explicitly decide:
- who owns auth
- who owns migrations
- who owns admin UI
- who owns public API namespace
- who owns queues/jobs
- who owns webhook processing
- who owns API key management

If any are unclear, mark them as **undecided** and resolve them before implementation.

---

## 4. PHASE 1 — DATABASE FOUNDATION

### Step 1.1: Deploy the canonical EAIOU tables
Use the canonical SQL after replacing the `#__` prefix.

Example:
```bash
ssh yw
sed 's/#__/xd6w5_/g' /path/to/eaiou_install_canonical.sql > /tmp/eaiou_tables.sql
mysql -u eaiou -p eaiou_db < /tmp/eaiou_tables.sql
```

### Step 1.2: Verify table creation
Run:
```sql
SHOW TABLES LIKE 'xd6w5_eaiou_%';
```

Expected logical coverage:
- papers
- versions
- ai_sessions
- didntmakeit
- remsearch
- review_logs
- attribution_log
- plugins_used
- api_keys
- api_logs
- quality_signals

### Step 1.3: Deploy GitGap tables if needed
Use the GitGap schema the same way and verify:
```sql
SHOW TABLES LIKE 'xd6w5_gitgap_%';
```

### Step 1.4: Write the migration ownership rule
Pick one:
- SQL canonical + manual migration workflow
- Alembic/FastAPI migration ownership
- Laravel migration ownership for shared tables
- split migration ownership with explicit scope boundaries

Do not let both stacks mutate the same tables casually.

---

## 5. PHASE 2 — ROLE AND ACL MODEL

### Step 2.1: Define roles at the application layer
Canonical roles:
- Public
- Author
- Reviewer
- Editor
- EIC
- Admin
- APIClient

### Step 2.2: Implement ACL in app logic
Do not rely on Joomla group inheritance language from the older guide. The earlier guide explicitly instructs creation of CMS user groups and permissions in admin UI, which should now be treated as role intent only, not implementation instructions. fileciteturn2file0

Implement role permissions in:
- FastAPI authorization layer
- Laravel admin/service layer if needed
- database-backed role mapping if required

### Step 2.3: Verify critical ACL rules
- Public cannot see sealed dates
- Authors can only edit their own papers
- Reviewers can only review assigned papers
- Editors can manage editorial flows
- EIC can perform governance unlock actions
- Admin has full system access
- API clients only get explicitly granted scopes

---

## 6. PHASE 3 — CORE DOMAIN IMPLEMENTATION

### Step 3.1: Papers
Implement:
- create
- update
- list
- detail
- archival/tombstone behavior
- status transitions
- authorship mode handling

### Step 3.2: Versions
Implement per-paper version tracking for:
- CH-A
- HAI-C
- FAI-H
- revision lineage

### Step 3.3: Remsearch
Implement:
- source capture
- used/excluded/disputed/deferred status
- review reason
- inclusion/exclusion reasoning
- reviewer flagging of omissions

### Step 3.4: AI Sessions
Implement:
- session metadata
- prompt/response storage policy
- model identity
- timestamps
- redaction support
- relationship to DidntMakeIt

### Step 3.5: Didn’t Make It
Implement:
- unused text fragments
- discarded outputs
- alternate drafts
- exclusion reasons
- reviewer/audit visibility policy

### Step 3.6: Attribution
Implement:
- section-level attribution
- human contribution logging
- AI contribution logging
- tool contribution logging

### Step 3.7: Review Logs
Implement:
- assignments
- rubric scores
- notes
- per-version review linkage
- decision support state

### Step 3.8: Quality Signals
Implement:
- q_signal computation
- rubric breakdown
- recalc triggers
- list-sort enforcement by q_signal

---

## 7. PHASE 4 — API LAYER

### Step 4.1: Build the API in tiers
Preserve the endpoint intent from the older guide, but implement it as FastAPI-first. The older guide describes 12 endpoint tiers and critical behaviors like rejecting date sort and firing temporal sealing on submission. Those behavioral requirements still stand even though the component/webservices framing does not. fileciteturn2file0

Tier groups:
1. Core system
2. Review + workflow
3. Authorship + AI
4. Transparency + Remsearch
5. Discovery + search
6. Gap / GitGap
7. Versioning + integrity
8. Admin control
9. Logging + audit
10. Notifications
11. System + infrastructure
12. API + external access

### Step 4.2: Critical API rules
- `paper.list` sorts by `q_signal DESC`
- date-based public sort is rejected
- workflow transition to submitted performs sealing behavior
- no sealed date fields in public responses
- no hard deletes
- every mutation is logged

### Step 4.3: Decide Laravel’s API role
Choose one:
- FastAPI exposes all app APIs; Laravel consumes/supports
- Laravel exposes admin/support APIs; FastAPI exposes domain APIs
- Laravel is API gateway; FastAPI is domain service behind it

Write this down before proceeding.

---

## 8. PHASE 5 — MCP / ENFORCEMENT LAYER

Implement the enforcement rules as application middleware/services, not CMS plugin behavior.

Required enforcement:
1. Temporal Blindness stripping
2. ACL gate before protected operations
3. Tombstone enforcement instead of hard delete
4. Action log on every mutation
5. q_signal sort enforcement
6. governance unlock restrictions

Map each frontend view to the correct enforcement-aware API calls.

---

## 9. PHASE 6 — FRONTEND APPLICATION

### Step 6.1: Extract the shared design system
Create a single shared design system stylesheet and component vocabulary based on the design references.

### Step 6.2: Build views in phases
Preserve the product view set from the older guide:
- public views
- author views
- reviewer views
- editorial views
- admin views
- auth/system views
- policy pages

But implement them as:
- FastAPI-served templates, or
- frontend app consuming FastAPI/Laravel APIs,
not as Joomla views/modules. The earlier guide specifies 37 views and strong layout rules that are still useful as product requirements. fileciteturn2file0

### Step 6.3: Verify all views
For every view:
- correct nav for role
- no empty sidebars
- footer present
- no public sealed dates
- q_signal used where required
- design system respected
- mobile degradation acceptable

---

## 10. PHASE 7 — COMMKIT INTEGRATION

Implement:
- right-side drawers
- modal workflows
- field-level writing guide triggers
- workspace guide entry points

Treat the older plan’s CommKit feature intent as valid, but implement it in the actual frontend stack rather than CMS modal/plugin assumptions. fileciteturn2file0

---

## 11. PHASE 8 — GITGAP INTEGRATION

### Step 8.1: Review GitGap source
Read `06_source/gitgap_app/` and document:
- schema
- API shape
- webhook behavior
- gap map rendering requirements

### Step 8.2: Implement sync and links
Implement:
- external gap sync
- paper ↔ gap linking
- gap map visualization
- discover gaps experience

---

## 12. PHASE 9 — HARDENING AND PRODUCTION

### Step 9.1: Integrity chain
Implement:
- `log_hash`
- `prior_hash`
- append-only API logs
- chain verification endpoint

### Step 9.2: Governance unlock
Implement restricted unlock flow for EIC/Admin only with mandatory action logging.

### Step 9.3: Rate limiting
Implement per-API-key and/or per-role throttles.

### Step 9.4: Security headers
Configure:
- HSTS
- CSP
- X-Frame-Options
- Referrer-Policy

### Step 9.5: Backup and restore
- daily DB backup
- restore test
- log retention review

### Step 9.6: Performance tuning
Tune:
- DB buffers
- PHP-FPM/Laravel resources as needed
- Python worker counts
- Redis if used
- queue concurrency if used

---

## 13. FINAL VERIFICATION CHECKLIST

### Temporal Blindness
- [ ] No sealed dates in public views
- [ ] No sealed dates in public API responses
- [ ] `paper.list` rejects date sort
- [ ] no public indexing behavior depends on sealed dates

### Quality Signal
- [ ] paper lists sort by `q_signal DESC`
- [ ] q_signal recomputes after review updates
- [ ] q_signal badge renders correctly

### Data Integrity
- [ ] sealing fires on submit
- [ ] API log chain is intact
- [ ] no hard deletes
- [ ] tombstone flow works

### ACL
- [ ] authors restricted to own papers
- [ ] reviewers restricted to assigned work
- [ ] editors can manage editorial work
- [ ] EIC/Admin governance unlock works correctly

### Frontend
- [ ] all target views render
- [ ] no empty sidebars where prohibited
- [ ] design system is consistent
- [ ] CommKit triggers work

### Integrations
- [ ] GitGap sync works
- [ ] plugin/tool logging works
- [ ] AI session logging works
- [ ] ORCID/external identity flows work if enabled

---

## 14. WHEN THINGS GO WRONG

### “I’m not sure what a field does”
Check the constitutional docs and the corrected SSOT first.

### “I’m not sure which layer should own this”
Do not guess.
Mark:
- undecided
- options
- preferred owner
- why

Then resolve before building.

### “A legacy build plan conflicts with the corrected SSOT”
The corrected SSOT wins.

### “I need to add something not in the plans”
Stop and ask Eric.

### “The old guide says to install a component/plugin/module”
Translate it first into one of:
- FastAPI service
- FastAPI router
- FastAPI middleware
- Laravel service
- Laravel admin tool
- frontend component
- queue worker
- integration job
- webhook handler

---

## 15. REPLACEMENT RULE

Do not describe the system as:
- a Joomla component
- a Joomla workflow
- a Joomla-native app
- a plugin/module-driven CMS build

Describe it as:
- a FastAPI primary app
- a Laravel backend/services layer
- Claude Code as the server-side implementation assistant
- a research integrity and provenance platform

---

*End of EAIOU Development Guide v2.0.0*  
*Corrected for FastAPI + Laravel architecture*  
*Temporal Blindness enforced. q_signal is still the river.*
