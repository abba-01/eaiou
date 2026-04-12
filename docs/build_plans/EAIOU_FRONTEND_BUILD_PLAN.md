# EAIOU — Frontend Build Plan (Claude Code Lockfile)

**Version:** 1.0.0 — 2026-04-12
**Author:** Eric D. Martin — ORCID: 0009-0006-5944-1742
**Purpose:** This document is the SINGLE AUTHORITATIVE REFERENCE for building every frontend view in the eaiou platform. Claude Code MUST follow this document exactly. No improvisation. No deviation from the design system. No guessing at layouts.
**Status:** CANONICAL — resolve all ambiguity against this file.

---

## 0. RULES FOR CLAUDE CODE

1. **Read this entire file before writing any code.**
2. **Every view uses the design system defined in Section 1.** No other fonts. No other colors. No other spacing. No exceptions.
3. **Every page has the nav, a full left column, a full right sidebar, and the footer.** No blank columns. No empty sidebars. If you cannot find content for a column, re-read the view spec — the content is listed.
4. **Build views in the order specified in Section 4.** Do not skip ahead.
5. **Use the exact CSS class names from Section 1.** Do not invent new class names unless they are namespaced under an existing element (e.g., `.paper-card-status` extends `.paper-card`).
6. **No dates in public views.** The Temporal Blindness Doctrine (Section 2) forbids displaying submission_sealed_at, acceptance_sealed_at, or publication_sealed_at on any public-facing page. q_signal is the ONLY sort key.
7. **Populate with realistic sample data.** Use the example papers from the wireframes (Hubble Tension, Partition of Cosmological Tensions, UHA Spatial Encoding). Do not use "Lorem ipsum."
8. **Every sidebar module has a header bar with module-title and a badge-tag label.** No naked content in sidebars.
9. **Test each view visually before moving to the next.** If it does not match the wireframe proportions, fix it before proceeding.
10. **When in doubt, match the wireframe from Batch 1 exactly.** The HTML mockup file `eaiou_design_system_mockup.html` is the visual ground truth.

---

## 1. DESIGN SYSTEM (IMMUTABLE)

### 1.1 Fonts

```
--serif: 'Spectral', Georgia, serif;        /* reading, titles, body text */
--mono: 'JetBrains Mono', monospace;        /* UI labels, metadata, codes, badges */
```

Import: `https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,300;0,400;0,600;1,300;1,400&family=JetBrains+Mono:wght@400;500&display=swap`

**Usage rules:**
- Hero titles: Spectral 300, 38–52px, letter-spacing -0.03em
- Article titles: Spectral 300, 26–36px, letter-spacing -0.02em
- Paper card titles: Spectral 400, 15–17px
- Body text: Spectral 400, 14–16px, line-height 1.75
- ALL labels, badges, metadata, nav links, buttons: JetBrains Mono 400/500, 9–12px, uppercase, letter-spacing 0.04–0.12em

### 1.2 Colors

```css
--ink: #0e0d0b;          /* primary text, nav background */
--ink2: #3a3832;         /* secondary text */
--ink3: #7a7670;         /* muted text, labels */
--paper: #f7f4ef;        /* page background */
--paper2: #ede9e1;       /* section backgrounds */
--paper3: #e0dbd0;       /* borders, dividers */
--river: #1a4a6b;        /* primary accent (deep blue) */
--river-l: #2d6e9e;      /* buttons, active states */
--river-ll: #e8f1f7;     /* transparency block bg */
--amber: #c47c0a;        /* warnings, due-soon */
--amber-l: #fdf0d0;      /* warning backgrounds */
--sage: #3a6b4a;         /* success, done, accept */
--sage-l: #e8f2ec;       /* success backgrounds */
--coral: #b84832;        /* danger, overdue, reject */
--coral-l: #faeae6;      /* danger backgrounds */
--violet: #4a3278;       /* AI-related, purple accent */
--violet-l: #ede8f7;     /* AI backgrounds */
```

### 1.3 Element Classes (Use EXACTLY these)

**Navigation:** `nav`, `nav-brand`, `nav-links`, `nav-link`, `nav-link.active`, `nav-right`, `nav-badge`, `nav-badge.primary`

**Hero:** `hero`, `hero-inner`, `hero-kicker`, `hero-title`, `hero-sub`, `hero-actions`, `hero-doctrine`

**Buttons:** `btn`, `btn-primary`, `btn-secondary`, `btn-danger`

**Section labels:** `section-label` (mono 10px, uppercase, border-bottom 0.5px)

**Dividers:** `section-divider`, `divider-title`, `divider-rule`

**Badges:**
- `badge badge-transparency` — blue, ◈ prefix
- `badge badge-ai` — violet, ⬡ prefix
- `badge badge-unsci` — coral, ⚑ prefix
- `badge badge-collab` — sage, ⊕ prefix
- `badge badge-sealed` — gray, ⬛ prefix
- `badge badge-tag` — transparent border, for rs: tags

**Paper cards:** `paper-card`, `paper-card-title`, `paper-card-meta`, `paper-card-abstract`, `paper-card-footer`, `paper-card-tags`, `paper-card-qsig`

**Q Signal:** `qsig`, `qsig-bar`, `qsig-dot`, `qsig-score`, `qsig-label`

**Module panels:** `module-panel`, `module-header`, `module-title`, `module-body`

**Queue items:** `queue-item`, `queue-item-title`, `queue-item-meta`, `due-pill`, `due-ok`, `due-warn`, `due-late`

**KPI cards:** `kpi-grid`, `kpi-card`, `kpi-label`, `kpi-value`, `kpi-trend`

**Transparency blocks:** `transp-block`, `transp-header`, `transp-header-title`, `transp-body`, `transp-row`, `transp-row-label`

**Article view:** `article-header`, `article-title`, `article-byline`, `article-badges`, `article-body`

**Forms:** `form-step`, `step-header`, `step-num`, `step-title`, `field-group`, `field-label`, `field-input`, `field-textarea`

**Search:** `search-bar`, `search-input`, `search-filters`, `filter-chip`, `filter-chip.active`

**Workflow tracker:** `workflow`, `wf-state`, `wf-dot`, `wf-dot.active`, `wf-dot.done`, `wf-line`, `wf-line.done`, `wf-name`, `wf-name.active`, `wf-name.done`

**Gap map:** `gap-map-cell`, `gap-bar`, `gap-label`

**ORCID:** `orcid-badge`, `orcid-dot`

**Research state tags:** `rs-tag`, `rs-collab`, `rs-stalled`, `rs-nottopic`

**Hash chain:** `hash-chain`, `hash-entry`, `hash-id`, `hash-val`, `hash-status`

**Layouts:**
- `layout` — 2-column: `1fr 260px` (main + sidebar)
- `layout-3col` — 3-column: `220px 1fr 260px` (left nav + main + sidebar)
- `grid-2` — 2 equal columns
- `grid-3` — 3 equal columns

**Tables:** `data-table` with `th` and `td` styling

**Tabs:** `tab-bar`, `tab`, `tab.active`

**Footer:** dark ink background, serif brand left, mono metadata right

### 1.4 Spacing Constants

- Page padding: 20–24px horizontal
- Sidebar padding: 14–16px
- Card padding: 16–20px
- Module gap in sidebar: 14px between panels
- Paper card gap: 10–12px vertical
- Badge gap: 3–4px horizontal
- Border radius: 2–4px (never round, never sharp-0)
- All borders: 0.5px solid var(--paper3) unless accent-colored

---

## 2. DOCTRINE CONSTRAINTS

### 2.1 Temporal Blindness
- **NEVER display** `submission_sealed_at`, `acceptance_sealed_at`, `publication_sealed_at` on ANY public or reviewer view.
- **NEVER sort** any list by date. Sort by `q_signal DESC` only.
- The sealed date exists in the database. It is rendered ONLY on governance views (EIC/Admin with explicit unlock).
- No "recency" indicators. No "newest first." No "published on [date]."

### 2.2 Sort Principle
- All paper lists, search results, and discovery surfaces sort by `q_signal DESC`.
- The only exception is the reviewer queue (sorted by due date for operational purposes — but the due date is a workflow field, NOT a submission date).

### 2.3 Full-Context Preservation
- Every view that shows a paper MUST show badges for: Transparency, AI-Logged, Un Scientific, Open Collab, Research State Tags — when those fields are populated.
- The "Didn't Make It" section is NEVER hidden. It is part of the archival record.

### 2.4 Principle 1 — Treat Things That Can Talk Like Humanity
- AI contributors appear in Attribution logs with their model name.
- AI sessions are browsable. AI-generated versions are flagged but not suppressed.

---

## 3. NAVIGATION STRUCTURE

### 3.1 Public Nav (unauthenticated)
```
[eaiou brand] | Discover | Papers | Ideas | Gaps | Trends | [Log in] [Submit Paper]
```

### 3.2 Author Nav (eaiou_Author)
```
[eaiou brand] | Discover | Submit | My Papers | Ideas | Gaps | [Username] [Submit Paper]
```

### 3.3 Reviewer Nav (eaiou_Reviewer)
```
[eaiou brand] | Discover | Review | My Reviews | Ideas | Gaps | [Username]
```

### 3.4 Editor Nav (eaiou_Editor)
```
[eaiou brand] | Discover | Editorial | Papers | Reviewers | Decisions | [Username badge:Editor]
```

### 3.5 Admin Nav (eaiou_Admin)
```
[eaiou brand] | Dashboard | Papers | Users | API Keys | API Logs | Settings | [Username badge:Admin]
```

---

## 4. VIEW BUILD ORDER AND SPECIFICATIONS

Each view below specifies:
- **Route** and ACL
- **Left column** content (main area)
- **Right sidebar** modules (MUST be populated — no blanks)
- **Key elements** from the design system to use
- **Data** to populate

### PHASE 1 — PUBLIC VIEWS (8 views)

---

#### VIEW 01: Home / Landing Page
**Route:** `/` **ACL:** Public
**Template:** `app/templates/index.html`

**Structure:**
1. Nav (public variant)
2. Hero section (dark ink bg)
   - Kicker: "OBSERVER-PRESERVING PEER REVIEW · OMMP LAYER 5"
   - Title: "Science sorted by quality. *Not time.*"
   - Subtitle: explains sealed dates + quality signal
   - 3 buttons: Submit a paper, Browse corpus, Explore gaps →
   - Doctrine quote block: "You do not read science by time."
3. Main layout (2-column: content + sidebar)

**Left column:**
- `section-label`: "Latest Papers · q_signal order · mod_latest_papers"
- `search-bar` with placeholder text
- `search-filters`: All papers, AI-Logged, Open Collab, Null Result, Cross-Domain, rs:Stalled, include un-space
- 3 paper-cards with full badges, q_signal scores, ORCID metadata

**Right sidebar (4 module-panels):**
1. Gap Map (gap-map-cell grid, 5 domains)
2. Open to Collaborate (2 queue-items with rs-tags)
3. AI Usage Heatmap (horizontal bar chart, 4 models)
4. Trending Ideas (2 queue-items with entropy context)

**Footer:** dark, brand left, ORCID + SSOT version right

---

#### VIEW 02: Papers List / Browse Corpus
**Route:** `/papers` **ACL:** Public
**Template:** `app/templates/papers/list.html`

**Left column:**
- `section-label`: "All Published Papers · q_signal DESC · no dates"
- search-bar + expanded search-filters (by discipline)
- Result count line (mono, muted)
- 4+ paper-cards, decreasing q_signal
- Pagination (btn group)

**Right sidebar (4 module-panels):**
1. Categories (list with counts)
2. Gap Map mini
3. Open to Collaborate
4. AI Usage Heatmap

---

#### VIEW 03: Paper Detail / Article Reader
**Route:** `/paper/{id}/{slug}` **ACL:** Public
**Template:** `app/templates/papers/detail.html`

**Full-width header:**
- Workflow tracker (wf-state dots showing publication state)
- article-byline (ORCID, author name, discipline)
- article-title (Spectral 26px)
- article-badges row (transparency, ai-logged, research state tags, qsig inline)

**Left column (article-body, max-width ~640px):**
- 2 paragraphs of sample body text
- Transparency Block (transp-block with river color)
- AI Usage Block (transp-block with violet color)
- Open Reports Block (transp-block with sage color, 2 reviewer entries)

**Right sidebar (5 sections, no module-panel wrapper needed — use section-labels):**
1. Integrity Chain (hash-chain: SEALED, CAPSTONE, HASH entries)
2. q_signal Breakdown (5 bar charts: Transparency ×1.5, AI Disclosure, Originality, Methodology, Cross-Domain + composite score box)
3. Research State Tags (3 rs-tags)
4. Version History (v2 current, v1 original)
5. Attribution (human author + AI contributor)

---

#### VIEW 04: Search Results
**Route:** `/search` **ACL:** Public
**Template:** `app/templates/papers/search.html`

**Left column:**
- search-bar (pre-filled with query)
- search-filters (expanded, with "include un-space" toggle)
- Result count
- Paper cards (some with rs:NotTopic highlighting for un-space results)

**Right sidebar:**
1. Search Tips (module-panel with mono text guidance)
2. Related Ideas (queue-items from discover/ideas)
3. Gap Map (filtered to search domain)

---

#### VIEW 05: Discover Ideas
**Route:** `/discover/ideas` **ACL:** Public
**Template:** from com_eaiou

**Dark mini-hero:** "Emerging ideas from *unused* datasets"

**Left column:**
- search-bar for un-space
- search-filters: rs:NotTopic, rs:NullResult, rs:AbandonedHypothesis, rs:Contradiction, rs:FutureWork, rs:OpenQuestion
- Idea cards (paper-card variant with violet left border + entropy score)

**Right sidebar:**
1. Entropy-Novelty Score explainer
2. Subscribe to Ideas (domain filter chips + subscribe button)
3. Gap Map
4. Open Questions (queue-items)

---

#### VIEW 06: Discover Gaps
**Route:** `/discover/gaps` **ACL:** Public
**Template:** from com_eaiou

**Left column:**
- Full-width gap map visualization (grid of gap-map-cells, larger format)
- Each cell: domain label, bar height = stall count, opacity = severity
- Below: list of top stalled items (paper-cards with rs:Stalled tags, stall type breakdown)

**Right sidebar:**
1. Stall Type Legend (list of rs:Stalled subtypes with counts)
2. Most Active Gaps (queue-items)
3. Open to Collaborate (filtered to stalled papers)
4. Contribute (CTA to submit against a gap)

---

#### VIEW 07: Discover Trends
**Route:** `/discover/trends` **ACL:** Public
**Template:** from com_eaiou

**Left column:**
- Trend cards (paper-card variant with sparkline SVGs showing search/declaration volume)
- Each shows: topic name, paper count, stall count, entropy indicator

**Right sidebar:**
1. Trending Topics (ranked list)
2. Rising Domains (bar visualization)
3. Subscribe to Trends
4. Gap Map (correlated)

---

#### VIEW 08: Discover Open / Collaborate Board
**Route:** `/discover/open` **ACL:** Public
**Template:** from com_eaiou

**Left column:**
- search-filters: rs:LookCollab subtypes (CoAuthor, DataPartner, DomainExpert, etc.)
- Collaboration cards (paper-card variant with sage left border, collab_type + interest_level)
- Each card shows: paper title, author ORCID, what they seek, interest level

**Right sidebar:**
1. Collaboration Types (count by type)
2. Your Expertise Match (if logged in — otherwise "Log in to see matches")
3. Gap Map
4. Declare a Research Need (CTA button → /research/seek)

---

### PHASE 2 — AUTHOR VIEWS (8 views)

---

#### VIEW 09: Submission Wizard — Step 1: Metadata
**Route:** `/submit/step/metadata` **ACL:** eaiou_Author
**Template:** `app/templates/author/intake.html`

**Top:** 6-step wizard progress bar (Metadata active, rest pending)

**Left column (form-step container):**
- step-header: "1 · Paper Metadata"
- grid-2 form layout:
  - Left: Title*, ORCID* (with verified badge), Discipline*, Keywords
  - Right: Abstract* (tall textarea), Authorship Mode (radio: Human/AI/Hybrid), Research State Tags (filter-chips for optional tags)
- Bottom: Continue to Bundle → button

**Right sidebar:**
1. Submission Guide (checklist: ORCID, transparency, AI disclosure, triage, declarations)
2. Temporal Blindness notice ("Your submission date will be sealed")
3. Integrity info (SHA256 hash, Zenodo capstone)

---

#### VIEW 10: Submission Wizard — Step 2: Bundle Upload
**Route:** `/submit/step/bundle` **ACL:** eaiou_Author

**Left column:**
- step-header: "2 · Upload Bundle"
- File upload zones: Manuscript (required), Supplementary files, Datasets, Code, Unused artifacts (with explanation)
- Each zone: drag-drop area with file-type restrictions listed

**Right sidebar:**
1. Bundle Requirements (what goes where)
2. Storage Layout preview (/media/com_eaiou/{paper_id}/...)
3. File size limits

---

#### VIEW 11: Submission Wizard — Step 3: AI Usage
**Route:** `/submit/step/ai-usage` **ACL:** eaiou_Author

**Left column:**
- step-header: "3 · AI Usage Disclosure"
- Radio: AI was used? Yes/No
- If Yes: grid-2 with AI Vendor, Model, Usage Mode, Contribution Scope, Prompt Summary, Human Oversight

**Right sidebar:**
1. AI Disclosure Policy summary
2. What gets logged (session hash, not raw prompts)
3. Display level options (Full/Summary/Hidden)

---

#### VIEW 12: Submission Wizard — Step 4: Literature Triage
**Route:** `/submit/step/triage` **ACL:** eaiou_Author

**Left column:**
- step-header: "4 · Literature Triage (Remsearch)"
- Repeatable form: Citation Title, Source, DOI/Link, Source Type, Used? (Yes/No), Reason if unused
- Add Source button
- Existing entries shown as compact table

**Right sidebar:**
1. Why Remsearch Matters (explanation)
2. Source Types (journal, preprint, book, dataset, code, other)
3. Remsearch Compliance (progress indicator)

---

#### VIEW 13: Submission Wizard — Step 5: Declarations
**Route:** `/submit/step/declarations` **ACL:** eaiou_Author

**Left column:**
- step-header: "5 · Declarations"
- Authorship declaration (checkbox + attribution list)
- Conflict of interest statement (textarea)
- Ethics/IRB declaration (radio + reference number)
- Open Collaboration toggle (collab_type, interest_level, notes)

**Right sidebar:**
1. Declaration Requirements
2. CRediT Roles reference
3. Open Collaboration explanation

---

#### VIEW 14: Submission Wizard — Step 6: Confirm & Submit
**Route:** `/submit/step/confirm` **ACL:** eaiou_Author

**Left column:**
- step-header: "6 · Review & Submit"
- Summary of all steps (read-only preview of metadata, bundle files, AI usage, triage entries, declarations)
- Temporal Blindness notice (prominent): "Your submission date will be sealed at the moment of submission. It will never be displayed publicly."
- Final submit button (btn-primary, full width)

**Right sidebar:**
1. Pre-submission Checklist (all green checks or red warnings)
2. What Happens Next (workflow: submitted → editor assigns → under review)
3. Integrity: "SHA256 hash will be computed. Zenodo capstone on acceptance."

---

#### VIEW 15: My Papers (Author Dashboard)
**Route:** `/mypapers` **ACL:** eaiou_Author
**Template:** `app/templates/author/dashboard.html`

**Left column:**
- section-label: "Your Submissions · workflow state view"
- tab-bar: All, Draft, Under Review, Published
- Paper cards with workflow tracker per card, status badges, action buttons (View Status, Upload Revision, Continue Editing)
- Papers with revisions_requested get coral left border + warning text

**Right sidebar:**
1. Author Profile (ORCID badge, name, submission count)
2. Notifications (3 notif-items with colored dots)
3. Your q_signal Average (large number display)

---

#### VIEW 16: Paper Revise
**Route:** `/paper/{id}/revise` **ACL:** eaiou_Author
**Template:** from com_eaiou

**Left column:**
- Paper title + current workflow state (revisions_requested)
- Editor's revision notes (read-only transp-block)
- Reviewer comments summary (read-only)
- Upload Revised Manuscript (file upload zone)
- Response to Reviewers (textarea)

**Right sidebar:**
1. Revision Requirements (what editor asked for)
2. Version History (v1 original, v2 will be created)
3. Deadline (due-pill with days remaining)

---

### PHASE 3 — REVIEWER VIEWS (3 views)

---

#### VIEW 17: Reviewer Queue
**Route:** `/reviewer/queue` **ACL:** eaiou_Reviewer

**Left column:**
- section-label: "Your Review Assignments · mod_reviewer_queue"
- tab-bar: Active, Pending Invite, Completed
- Assignment cards with due-pills (due-ok/warn/late), badges, action buttons

**Right sidebar:**
1. Reviewer Stats (kpi-grid: Reviews Done, Active, Overdue, Avg Score)
2. Pending Invite (with Accept/Decline buttons)
3. Review Rubric Guide (6 dimensions listed)

---

#### VIEW 18: Review Console
**Route:** `/reviewer/paper/{id}/review` **ACL:** eaiou_Reviewer

**Context bar:** "Reviewing: [Paper Title] · v2"

**Left column:**
- Rubric form (6 sliders 0–10 with live score display):
  - Overall Quality, Originality, Methodology, Transparency (×1.5 label), AI Disclosure, Cross-Domain
- Recommendation (filter-chips: Accept, Minor, Major, Reject, Refer)
- Review Notes (textarea)
- Un Scientific Flag (radio: No / Yes)
- Open Review Consent (radio: Open identity / Anonymous)
- Save Draft + Submit Review buttons

**Right sidebar:**
1. Paper Summary (title, ORCID, badges)
2. AI Usage (read-only transp-rows)
3. Transparency (read-only transp-rows)
4. Version info

---

#### VIEW 19: Reviewer Paper Access
**Route:** `/reviewer/paper/{id}` **ACL:** eaiou_Reviewer

Same as VIEW 03 (Paper Detail) but with:
- "Open Review Console" button in header
- No public comments visible (reviewer sees only their own prior reviews if any)
- Full AI session logs visible in sidebar

---

### PHASE 4 — EDITORIAL VIEWS (4 views)

---

#### VIEW 20: Editorial Papers List
**Route:** `/editorial/papers` **ACL:** eaiou_Editor

**Left column:**
- KPI row (kpi-grid 4 columns: Submitted, Under Review, Decision Pending, Overdue)
- tab-bar: All, Submitted, Under Review, Decision, Revisions, Accepted, Published
- data-table: Paper, Status, Reviewers (count + completion), Flags, Actions

**Right sidebar:**
1. Editor Dashboard (kpi-grid: TTFD Median, Accept Rate + sparkline chart)
2. Overdue Actions (queue-items with Nudge buttons)
3. Flags Summary (AI-Logged count, Un Sci count, Collab count)

---

#### VIEW 21: Editorial Paper Management
**Route:** `/editorial/paper/{id}` **ACL:** eaiou_Editor

**Left column:**
- Paper header (title, ORCID, status badge, all badges)
- Workflow tracker (full state machine)
- Tabs: Overview | Reviews | AI Logs | Triage | Attribution | Versions
- Under Overview: paper metadata summary, author info, submission stats

**Right sidebar:**
1. Quick Actions (Assign Reviewers, Request Revision, Publish)
2. Reviewer Assignments (list with status)
3. Integrity Chain
4. Governance Unlock button (for sealed dates — EIC/Admin only)

---

#### VIEW 22: Reviewer Assignment
**Route:** `/editorial/assign/{id}` **ACL:** eaiou_Editor

**Left column:**
- Paper title + discipline
- Current reviewers (if any) with status
- Reviewer search/selection (search-bar for reviewer database)
- Suggested reviewers (based on expertise match)
- Assignment form: reviewer, due date, notes

**Right sidebar:**
1. Paper Requirements (discipline, methodology type)
2. Conflict Detection warnings
3. Reviewer Pool Stats (available count, avg response time)

---

#### VIEW 23: Editorial Decision
**Route:** `/editorial/decide/{id}` **ACL:** eaiou_Editor

**Left column:**
- Review summaries (2 review cards with scores, recommendations, notes)
- Decision form:
  - Decision chips: Accept, Minor Revisions, Major Revisions, Reject
  - Editor Notes to Author (textarea)
  - Save Draft + Accept & Notify + Publish Now buttons

**Right sidebar:**
1. Workflow State (tracker showing current position)
2. Paper Metadata (author, ORCID, category, version, authorship mode)
3. Integrity Chain (hash entries)
4. Capstone Gate (status: OPEN/CLOSED + Ready indicator)

---

### PHASE 5 — ADMIN VIEWS (5 views)

---

#### VIEW 24: Admin Dashboard
**Route:** `/administrator/index.php?option=com_eaiou` **ACL:** eaiou_Admin

**Left column:**
- KPI grid (6 cards: Total Papers, Published, Under Review, Overdue, Active Reviewers, API Calls/30d)
- Submissions trend (SVG sparkline, 30d)
- Recent Activity stream (notif-items: latest actions from Action Logs)

**Right sidebar:**
1. System Health (server status indicators)
2. Quick Links (Papers, Users, API Keys, Settings, API Logs)
3. Hash Chain Status (verified/broken indicator)
4. Scheduler Status (last nudger run, next scheduled)

---

#### VIEW 25: Admin API Keys
**Route:** `/administrator/.../api_keys` **ACL:** eaiou_Admin

**Left column:**
- section-label: "API Key Registry"
- data-table: Key (masked), Description, User, Access Level, Status, Last Used, Actions
- Add New Key button

**Right sidebar:**
1. Access Levels (read, submit, review, admin — with descriptions)
2. Usage Stats (total keys, active, revoked)
3. Security Notes

---

#### VIEW 26: Admin API Logs
**Route:** `/administrator/.../api_logs` **ACL:** eaiou_Admin

**Left column:**
- section-label: "API Call Audit Log · append-only · hash chain"
- Filters: endpoint, response code, date range
- data-table: ID, Endpoint, Method, Response Code, Hash, Prior Hash, Timestamp
- Chain integrity indicator at top

**Right sidebar:**
1. Hash Chain Verification (status: intact/broken + last verified)
2. Endpoint Summary (top endpoints by call count)
3. Error Rate (percentage of non-200 responses)

---

#### VIEW 27: Admin Users
**Route:** `/administrator/.../users` **ACL:** eaiou_Admin

**Left column:**
- data-table: Name, Email, ORCID, Groups (badges), Status, Last Login, Actions
- Filters: by group, status, ORCID linked

**Right sidebar:**
1. User Groups (eaiou_Author, Reviewer, Editor, EIC, Admin, APIClient — with counts)
2. ORCID Coverage (% of users with linked ORCID)
3. Add User button

---

#### VIEW 28: Admin Settings
**Route:** `/administrator/.../settings` **ACL:** eaiou_Admin

**Left column:**
- tab-bar: General, Workflows, Quality Signal, Plugins, Storage, API
- Under General: Site name, brand settings, default q_signal weights
- Under Workflows: state machine visualization, transition rules
- Under Quality Signal: weight sliders for each rubric dimension
- Under Plugins: enable/disable toggles for each eaiou plugin
- Under Storage: media root path, file size limits
- Under API: rate limits, allowed origins, throttle settings

**Right sidebar:**
1. Current Configuration Summary (key settings listed)
2. SSOT Version (current v2.0)
3. Doctrine Reminders (Temporal Blindness, Sort Principle)

---

### PHASE 6 — AUTHENTICATION & SYSTEM VIEWS (5 views)

---

#### VIEW 29: Login
**Route:** `/login` **ACL:** Public

**Centered card layout (no sidebar):**
- eaiou brand
- Email/username field
- Password field
- Login button
- "Connect with ORCID" button (green ORCID badge style)
- Register link, Forgot password link

---

#### VIEW 30: Register
**Route:** `/register` **ACL:** Public

**Centered card layout:**
- Name, Email, Password, Confirm Password
- "Connect ORCID" optional
- Role request (Author by default)
- Terms acceptance checkbox
- Register button

---

#### VIEW 31: ORCID Profile Page
**Route:** user profile **ACL:** Registered

**Left column:**
- ORCID badge (large)
- Connect/Disconnect ORCID button
- User info: name, email, groups, linked ORCID
- Papers authored (list)

**Right sidebar:**
1. ORCID Verification Status
2. Your Roles (badges for groups)
3. Activity Summary

---

#### VIEW 32: 404 Not Found
**Route:** any invalid **ACL:** Public

**Centered layout:**
- Large "404" in Spectral 300
- "Page not found" subtitle
- Search bar
- Link back to home

---

#### VIEW 33: 500 Server Error
**Route:** error **ACL:** Public

**Centered layout:**
- Large "500" in Spectral 300
- "Something went wrong" subtitle
- Contact info

---

### PHASE 7 — POLICY PAGES (4 views)

---

#### VIEW 34: Temporal Blindness Policy
**Route:** `/policy/temporal-blindness` **ACL:** Public

**Left column (article-body style):**
- Full text of the Temporal Blindness Doctrine
- The SAID witness statement
- Access model table

**Right sidebar:**
1. Key Principles (bullet summary)
2. Related: Sort Principle
3. ORCID: 0009-0006-5944-1742

---

#### VIEW 35: AI Disclosure Policy
#### VIEW 36: Open Access Policy
#### VIEW 37: Intelligence Blindness Policy

Same structure as VIEW 34: article-body left, principle summary sidebar right.

---

## 5. SIDEBAR MODULE INVENTORY (PER VIEW)

Every sidebar module MUST use `module-panel` with `module-header` (containing `module-title` + optional `badge-tag`) and `module-body`. No naked content in sidebars. No empty sidebars. Every view with a sidebar gets AT LEAST 3 modules.

### VIEW 01 — Home
| # | Module | Content |
|---|--------|---------|
| 1 | Gap Map | gap-map-cell grid, 5 domains (Cosmo, CS, Math, Bio, Stats) |
| 2 | Open to Collaborate | 2 queue-items with rs-tags + interest level |
| 3 | AI Usage Heatmap | horizontal bars: Claude, GPT-4, Gemini, No AI — with % |
| 4 | Trending Ideas | 2 queue-items with paper count + entropy context |

### VIEW 02 — Papers List
| # | Module | Content |
|---|--------|---------|
| 1 | Categories | list with paper counts per discipline |
| 2 | Gap Map | gap-map-cell grid, 5 domains |
| 3 | Open to Collaborate | 2 queue-items with rs-tags |
| 4 | AI Usage Heatmap | compact horizontal bars |

### VIEW 03 — Paper Detail
| # | Module | Content |
|---|--------|---------|
| 1 | Integrity Chain | hash-chain: SEALED, CAPSTONE, HASH entries with ✓ |
| 2 | q_signal Breakdown | 5 progress bars (Transparency ×1.5, AI Disclosure, Originality, Methodology, Cross-Domain) + composite score box |
| 3 | Research State Tags | 3 rs-tags (NullResult, CrossDomain, Stalled:Data resolved) |
| 4 | Version History | v2 (current) with AI badge, v1 (original) |
| 5 | Attribution | human author line + AI contributor line with model name |

### VIEW 04 — Search Results
| # | Module | Content |
|---|--------|---------|
| 1 | Search Tips | mono text: how to use filters, un-space toggle |
| 2 | Related Ideas | 2 queue-items from /discover/ideas relevant to query |
| 3 | Gap Map | gap-map-cell grid filtered to search domain |

### VIEW 05 — Discover Ideas
| # | Module | Content |
|---|--------|---------|
| 1 | Entropy-Novelty Score | serif explanation of scoring 0.0–1.0 |
| 2 | Subscribe to Ideas | domain filter-chips + "Subscribe to Feed" btn-primary |
| 3 | Gap Map | gap-map-cell grid, 4 domains |
| 4 | Open Questions | 2 queue-items with rs:OpenQuestion labels |

### VIEW 06 — Discover Gaps
| # | Module | Content |
|---|--------|---------|
| 1 | Stall Type Legend | list of rs:Stalled subtypes with counts (Data, Methodology, Funding, etc.) |
| 2 | Most Active Gaps | 3 queue-items ranked by stall density |
| 3 | Open to Collaborate | queue-items filtered to stalled papers |
| 4 | Contribute | CTA: "Submit a paper against this gap" → btn-primary to /submit |

### VIEW 07 — Discover Trends
| # | Module | Content |
|---|--------|---------|
| 1 | Trending Topics | ranked list with sparkline indicators |
| 2 | Rising Domains | compact vertical bar visualization |
| 3 | Subscribe to Trends | domain chips + subscribe button |
| 4 | Gap Map | correlated to trending topics |

### VIEW 08 — Discover Open / Collaborate Board
| # | Module | Content |
|---|--------|---------|
| 1 | Collaboration Types | count by type (CoAuthor, DataPartner, DomainExpert, etc.) |
| 2 | Your Expertise Match | "Log in to see matches" (or matched items if authenticated) |
| 3 | Gap Map | gap-map-cell grid |
| 4 | Declare a Research Need | CTA: btn-primary → /research/seek form |

### VIEW 09 — Submit Step 1: Metadata
| # | Module | Content |
|---|--------|---------|
| 1 | Submission Guide | checklist: ORCID ✓, Transparency ✓, AI Disclosure ✓, Triage ✓, Declarations ✓ |
| 2 | Temporal Blindness Notice | "Your submission date will be sealed" + badge-sealed |
| 3 | Integrity | "SHA256 hash computed at submission. Zenodo capstone on acceptance." |

### VIEW 10 — Submit Step 2: Bundle Upload
| # | Module | Content |
|---|--------|---------|
| 1 | Bundle Requirements | what goes in each zone (manuscript, data, code, unused) |
| 2 | Storage Layout | mono text showing /media/com_eaiou/{paper_id}/... tree |
| 3 | File Limits | max sizes, allowed formats |

### VIEW 11 — Submit Step 3: AI Usage
| # | Module | Content |
|---|--------|---------|
| 1 | AI Disclosure Policy | summary of what gets logged |
| 2 | What Gets Stored | "Session hash, not raw prompts" — privacy note |
| 3 | Display Level Options | Full / Summary / Hidden explanation |

### VIEW 12 — Submit Step 4: Literature Triage
| # | Module | Content |
|---|--------|---------|
| 1 | Why Remsearch Matters | serif explanation of literature audit |
| 2 | Source Types | list: journal, preprint, book, dataset, code, other |
| 3 | Remsearch Compliance | progress indicator (X of Y required fields complete) |

### VIEW 13 — Submit Step 5: Declarations
| # | Module | Content |
|---|--------|---------|
| 1 | Declaration Requirements | what must be checked/filled |
| 2 | CRediT Roles Reference | list of contribution types |
| 3 | Open Collaboration | explanation of collab_type and interest_level |

### VIEW 14 — Submit Step 6: Confirm
| # | Module | Content |
|---|--------|---------|
| 1 | Pre-submission Checklist | green ✓ or red ✗ per step (metadata, bundle, AI, triage, declarations) |
| 2 | What Happens Next | workflow: submitted → editor assigns → under review |
| 3 | Integrity Notice | "SHA256 hash will be computed. Zenodo capstone on acceptance." + Temporal Blindness reminder |

### VIEW 15 — My Papers (Author Dashboard)
| # | Module | Content |
|---|--------|---------|
| 1 | Author Profile | ORCID badge, name, "4 submissions · 2 published" |
| 2 | Notifications | 3 notif-items with colored dots (coral=revision, river=review, sage=published) |
| 3 | Your q_signal Average | large mono number centered, "across N published papers" |

### VIEW 16 — Paper Revise
| # | Module | Content |
|---|--------|---------|
| 1 | Revision Requirements | editor's specific requests summarized |
| 2 | Version History | v1 (original), v2 (will be created on upload) |
| 3 | Deadline | due-pill with days remaining + color coding |

### VIEW 17 — Reviewer Queue
| # | Module | Content |
|---|--------|---------|
| 1 | Reviewer Stats | kpi-grid 2×2: Reviews Done, Active, Overdue, Avg Score |
| 2 | Pending Invite | queue-item with Accept/Decline btn pair |
| 3 | Review Rubric Guide | 6 dimensions listed with ×1.5 note on Transparency |

### VIEW 18 — Review Console
| # | Module | Content |
|---|--------|---------|
| 1 | Paper Summary | title (serif 13px), ORCID, transparency + AI badges |
| 2 | AI Usage (read-only) | transp-rows: Tools, Sessions, Excluded, Disclosure level |
| 3 | Transparency (read-only) | transp-rows: Sources used/excluded, Datasets, Completeness |
| 4 | Version Info | "Reviewing: v2 (revised)" + "Previous: v1 (original)" |

### VIEW 19 — Reviewer Paper Access
| # | Module | Content |
|---|--------|---------|
| 1 | Integrity Chain | hash-chain entries |
| 2 | q_signal Breakdown | 5 progress bars + composite |
| 3 | AI Session Logs | list of sessions with model names + token counts |
| 4 | Research State Tags | rs-tag list |
| 5 | Version History | version list |

### VIEW 20 — Editorial Papers List
| # | Module | Content |
|---|--------|---------|
| 1 | Editor Dashboard | kpi-grid: TTFD Median, Accept Rate + SVG sparkline |
| 2 | Overdue Actions | queue-items with paper title, assignee, "Nudge" btn |
| 3 | Flags Summary | badge counts: AI-Logged, Un Sci., Collab |

### VIEW 21 — Editorial Paper Management
| # | Module | Content |
|---|--------|---------|
| 1 | Quick Actions | btn group: Assign Reviewers, Request Revision, Publish |
| 2 | Reviewer Assignments | list of assigned reviewers with invite status + due |
| 3 | Integrity Chain | hash-chain entries |
| 4 | Governance Unlock | btn (EIC/Admin only) to view sealed temporal fields |

### VIEW 22 — Reviewer Assignment
| # | Module | Content |
|---|--------|---------|
| 1 | Paper Requirements | discipline, methodology type, keywords |
| 2 | Conflict Detection | warnings if potential conflicts found |
| 3 | Reviewer Pool Stats | available count, avg response time, decline rate |

### VIEW 23 — Editorial Decision
| # | Module | Content |
|---|--------|---------|
| 1 | Workflow State | workflow tracker (wf-dots showing current position) |
| 2 | Paper Metadata | transp-rows: Author, ORCID, Category, Version, Authorship Mode |
| 3 | Integrity Chain | hash-chain: SEALED, HASH entries |
| 4 | Capstone Gate | status: "Gate: OPEN" + "✓ Ready" indicator |

### VIEW 24 — Admin Dashboard
| # | Module | Content |
|---|--------|---------|
| 1 | System Health | status indicators (green dots: DB, Apache, PHP, Redis) |
| 2 | Quick Links | linked list: Papers, Users, API Keys, Settings, API Logs |
| 3 | Hash Chain Status | "Verified ✓" or "Broken ✗" with last check time |
| 4 | Scheduler Status | last nudger run time, next scheduled, emails sent count |

### VIEW 25 — Admin API Keys
| # | Module | Content |
|---|--------|---------|
| 1 | Access Levels | list: read, submit, review, admin — with 1-line descriptions |
| 2 | Usage Stats | kpi-cards: Total Keys, Active, Revoked |
| 3 | Security Notes | mono text: key rotation, hash storage, never store raw |

### VIEW 26 — Admin API Logs
| # | Module | Content |
|---|--------|---------|
| 1 | Hash Chain Verification | status: intact/broken + timestamp of last verification |
| 2 | Endpoint Summary | top 5 endpoints by call count (mono list) |
| 3 | Error Rate | percentage of non-200 responses with trend |

### VIEW 27 — Admin Users
| # | Module | Content |
|---|--------|---------|
| 1 | User Groups | list with counts per group (Author, Reviewer, Editor, EIC, Admin, APIClient) |
| 2 | ORCID Coverage | "X% of users have linked ORCID" with progress bar |
| 3 | Add User | btn-primary: "Create User" |

### VIEW 28 — Admin Settings
| # | Module | Content |
|---|--------|---------|
| 1 | Current Configuration | key settings: q_signal weights, active plugins, storage path |
| 2 | SSOT Version | "v2.0 — 2026-04-07" |
| 3 | Doctrine Reminders | Temporal Blindness + Sort Principle one-liners |

### VIEW 31 — ORCID Profile
| # | Module | Content |
|---|--------|---------|
| 1 | ORCID Verification Status | verified/unverified + link date |
| 2 | Your Roles | badges for assigned groups |
| 3 | Activity Summary | papers submitted, reviews completed, q_signal avg |

### VIEWS 29, 30, 32, 33 — Login, Register, 404, 500
These use centered card layouts with NO sidebar. No module-panels needed.

### VIEWS 34–37 — Policy Pages
| # | Module | Content |
|---|--------|---------|
| 1 | Key Principles | 3–5 bullet summary of the policy |
| 2 | Related Policies | links to other policy pages |
| 3 | ORCID | "0009-0006-5944-1742 — Eric D. Martin" |

---

## 6. FILE DELIVERY STRUCTURE

Each view produces one HTML file. The shared CSS goes in a single `eaiou-design-system.css` file. Structure:

```
/home/eaiou/public_html/templates/eaiou/
├── css/
│   └── eaiou-design-system.css        ← ALL design system CSS
├── views/
│   ├── 01_home.html
│   ├── 02_papers_list.html
│   ├── 03_paper_detail.html
│   ├── 04_search.html
│   ├── 05_discover_ideas.html
│   ├── 06_discover_gaps.html
│   ├── 07_discover_trends.html
│   ├── 08_discover_open.html
│   ├── 09_submit_metadata.html
│   ├── 10_submit_bundle.html
│   ├── 11_submit_ai_usage.html
│   ├── 12_submit_triage.html
│   ├── 13_submit_declarations.html
│   ├── 14_submit_confirm.html
│   ├── 15_my_papers.html
│   ├── 16_paper_revise.html
│   ├── 17_reviewer_queue.html
│   ├── 18_review_console.html
│   ├── 19_reviewer_paper.html
│   ├── 20_editorial_papers.html
│   ├── 21_editorial_paper.html
│   ├── 22_editorial_assign.html
│   ├── 23_editorial_decide.html
│   ├── 24_admin_dashboard.html
│   ├── 25_admin_api_keys.html
│   ├── 26_admin_api_logs.html
│   ├── 27_admin_users.html
│   ├── 28_admin_settings.html
│   ├── 29_login.html
│   ├── 30_register.html
│   ├── 31_orcid_profile.html
│   ├── 32_404.html
│   ├── 33_500.html
│   ├── 34_policy_temporal_blindness.html
│   ├── 35_policy_ai_disclosure.html
│   ├── 36_policy_open_access.html
│   └── 37_policy_intelligence_blindness.html
└── wireframe_atlas/
    └── eaiou_wireframes_batch1.html    ← Reference (already built)
```

---

## 7. BUILD CHECKLIST

Claude Code: check off each item as you complete it. Do not proceed to the next phase until the current phase is fully checked.

### Phase 1 — Public Views
- [ ] VIEW 01: Home
- [ ] VIEW 02: Papers List
- [ ] VIEW 03: Paper Detail
- [ ] VIEW 04: Search
- [ ] VIEW 05: Discover Ideas
- [ ] VIEW 06: Discover Gaps
- [ ] VIEW 07: Discover Trends
- [ ] VIEW 08: Discover Open

### Phase 2 — Author Views
- [ ] VIEW 09: Submit Step 1
- [ ] VIEW 10: Submit Step 2
- [ ] VIEW 11: Submit Step 3
- [ ] VIEW 12: Submit Step 4
- [ ] VIEW 13: Submit Step 5
- [ ] VIEW 14: Submit Step 6
- [ ] VIEW 15: My Papers
- [ ] VIEW 16: Paper Revise

### Phase 3 — Reviewer Views
- [ ] VIEW 17: Reviewer Queue
- [ ] VIEW 18: Review Console
- [ ] VIEW 19: Reviewer Paper

### Phase 4 — Editorial Views
- [ ] VIEW 20: Editorial Papers
- [ ] VIEW 21: Editorial Paper
- [ ] VIEW 22: Reviewer Assignment
- [ ] VIEW 23: Editorial Decision

### Phase 5 — Admin Views
- [ ] VIEW 24: Admin Dashboard
- [ ] VIEW 25: API Keys
- [ ] VIEW 26: API Logs
- [ ] VIEW 27: Users
- [ ] VIEW 28: Settings

### Phase 6 — Auth & System
- [ ] VIEW 29: Login
- [ ] VIEW 30: Register
- [ ] VIEW 31: ORCID Profile
- [ ] VIEW 32: 404
- [ ] VIEW 33: 500

### Phase 7 — Policy Pages
- [ ] VIEW 34: Temporal Blindness
- [ ] VIEW 35: AI Disclosure
- [ ] VIEW 36: Open Access
- [ ] VIEW 37: Intelligence Blindness

---

## 8. VERIFICATION CRITERIA

For EACH view, Claude Code must verify:

1. **Nav** matches the ACL variant (public/author/reviewer/editor/admin)
2. **Left column** is fully populated — no placeholder text, no empty areas
3. **Right sidebar** has at least 3 module-panels — no blanks
4. **Footer** is present
5. **No dates** are displayed on public views (Temporal Blindness)
6. **Badges** are present where data exists (transparency, AI, unsci, collab, tags)
7. **q_signal** is the sort key — not date, not recency
8. **Typography** uses only Spectral and JetBrains Mono
9. **Colors** use only the CSS variables from Section 1.2
10. **Responsive** — layout degrades gracefully (sidebar stacks below on mobile)

---

*End of EAIOU Frontend Build Plan v1.0.0*
*ORCID: 0009-0006-5944-1742 — Eric D. Martin*
*Temporal Blindness enforced. q_signal is the river.*
