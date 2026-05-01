# UXPILOT_05 — admin (com_eaiou backend) pages

**Tokens, schemas, shells:** see `UXPILOT_00_design_system.md`.
**Philosophical canon:** see `UXPILOT_PROMPT_EAIOU.md`.
**Modules:** see `UXPILOT_06_modules.md`.
**Shells:** see `UXPILOT_07_layout_shells.md`.

Admin role = `eaiou_Admin` (also `eaiou_EIC` for governance-unlock surfaces). All admin URLs are Joomla backend: `/administrator/index.php?option=com_eaiou&view=<view>`.

---

## Admin chrome (applies to every admin surface)

**Layout shell:** Joomla's standard admin shell (top toolbar, left submenu, content area, status bar). Adapt the canonical eaiou tokens to the admin shell. No fixed/wide toggle in admin — admin is always wide.

**Header chrome (top bar, 56px tall, `--surface` bg, 1px bottom `--paper3`):**
- Left: Joomla "System ▾ Users ▾ Menus ▾ Content ▾ Components ▾ Extensions ▾ Help ▾" mono 12pt.
- Center: Spectral 300 18pt "com_eaiou" + active view name mono 11pt UPPERCASE.
- Right: governance-unlock indicator (mono UPPERCASE chip — `LOCKED` `--paper2` / `UNLOCKED · 14m REMAINING` `--coral-l` if active), admin user IntelliD pill, sign-out.

**Submenu (left rail, 220px wide, `--paper2` bg, 1px right `--paper3`):**
Sticky, scrolls independently.
Sections (mono 11pt UPPERCASE labels, Spectral 14pt items):
- DASHBOARD
- PAPERS
- AI SESSIONS
- DIDN'T MAKE IT
- REMSEARCH (literature triage)
- REVIEW LOGS
- VERSIONS
- ATTRIBUTION
- QUALITY SIGNALS
- PLUGINS USED (audit)
- API KEYS
- API LOGS
- TEMPLATES (decision letters, mail)
- ARTICLES (Joomla bridge view)
- MODULES (rendering audit)
- SETTINGS
- SEALED AUDIT (governance — coral chip, requires unlock)

Active item: 4px left `--river` border + `--river-ll` bg.

**Toolbar (sticky below header, 56px tall, `--paper2` bg):**
Per-view actions rendered as mono UPPERCASE 12pt outline buttons with leading icons. Default toolbar buttons (vary by view):
`+ NEW · EDIT · DUPLICATE · PUBLISH · UNPUBLISH · ARCHIVE · TRASH · CHECK IN · BATCH · OPTIONS · HELP`. Filters and search live to the right.

**Content area:** primary work surface. Defaults to a list manager (table with filter rail + status sidebar) per Joomla convention; we extend this below.

**Status bar (bottom, 32px, `--paper2` bg, 1px top `--paper3`):**
Mono 11pt — record count · selected count · governance-unlock countdown (if active) · backup status · cache status · "Joomla 5.3.x · com_eaiou v0.x.y".

**Default acceptance criteria (admin):**
1. Joomla 5.3 admin shell semantics preserved (top bar, submenu, toolbar, content, status bar).
2. eaiou tokens applied throughout (Spectral / JetBrains Mono / 19-token palette).
3. No flat block colors. Hairlines only.
4. Sealed temporal data only visible after governance unlock (mono dual-key flow).
5. Every list view supports column show/hide, sort, filter, pagination, batch actions, export to CSV.

---

## List-manager pattern (used by most admin views)

This pattern applies to: Papers, AI Sessions, Didn't Make It, Remsearch, Review Logs, Versions, Attribution, Quality Signals, Plugins Used, API Keys, API Logs, Templates, Modules.

**Page blocks (apply to each listed view):**
1. **Admin chrome (header + submenu).**
2. **Toolbar:** view-specific actions per "Toolbar overrides" table below.
3. **Filter rail (sticky, 56px, `--paper2` bg):** view-specific filters per "Filter rail overrides".
4. **Two-column body:**
   - **Left col (220px wide, `--paper2` bg):** "Filter options" sidebar — additional filters in a vertical stack with mono 11pt UPPERCASE labels (Joomla pattern).
   - **Right col (rest):** list table. Columns per "Columns" override below. All tables use:
     - mono UPPERCASE 11pt headers, click to sort.
     - row checkbox first column.
     - row hover `--paper2`.
     - 1px bottom `--paper3` per row.
     - state chip column near the end.
     - action column on far right (3-dot menu).
5. **Pagination strip (32px, mono 11pt, `--paper2` bg):** "1–20 of 312 · 20 per page · prev | next".
6. **Status bar.**

**Toolbar overrides per view:**

| View | Extra toolbar buttons |
|---|---|
| Papers | `+ NEW · EDIT · ASSIGN REVIEWERS · DECIDE · TRANSITION STATE · GOVERNANCE UNLOCK · EXPORT BUNDLE` |
| AI Sessions | `EDIT · REDACT · ATTACH TO PAPER · EXPORT JSON` |
| Didn't Make It | `EDIT · REDACT · UNREDACT (gov unlock) · CROSS-LINK · EXPORT JSON` |
| Remsearch | `+ NEW · EDIT · MARK USED · MARK UNUSED · IMPORT BIBTEX` |
| Review Logs | `EDIT · OPEN REVIEW · OPEN PAPER · EXPORT CSV` |
| Versions | `+ NEW VERSION · EDIT · COMPARE TWO · OPEN PAPER · DOWNLOAD` |
| Attribution | `+ NEW · EDIT · LINK TO USER · EXPORT JSON` |
| Quality Signals | `RECOMPUTE · EDIT WEIGHTS · EXPORT CSV` |
| Plugins Used | `EDIT · LINK TO PAPER · EXPORT JSON` |
| API Keys | `+ NEW · EDIT · ROTATE · REVOKE · EXPORT (REDACTED)` |
| API Logs | `EXPORT CSV · CLEAR ARCHIVE (gov unlock)` |
| Templates | `+ NEW · EDIT · DUPLICATE · ACTIVATE · DEACTIVATE · PREVIEW` |
| Modules | `+ NEW · EDIT · DUPLICATE · PUBLISH · UNPUBLISH · POSITION MAP` |

**Filter rail overrides per view:** in addition to common (search, state, access, language).

| View | Extra filter chips |
|---|---|
| Papers | discipline · workflow state · authorship_mode · transparency_complete · ai_log_complete · `rs:*` · sealed (gov-only) |
| AI Sessions | vendor · model · mode · risk-flag presence · contribution_scope text |
| Didn't Make It | reason category · redacted (boolean) · linked-paper · cross-domain candidate (boolean) |
| Remsearch | source_type · used (boolean) · linked-paper · discipline |
| Review Logs | reviewer_id · paper_id · recommendation · per-criterion score range |
| Versions | linked-paper · ai_authorship · version label range |
| Attribution | contribution_type · ai_or_human · ai_tool_used |
| Quality Signals | computation cycle · weight set · score range |
| Plugins Used | plugin_name · plugin_type · execution_context |
| API Keys | access_level · status · owner |
| API Logs | endpoint · response_code · key_id · time-bucket (relative bar) |
| Templates | template_type (decision / mail / system) · active boolean |
| Modules | position · group · published boolean |

**Columns overrides per view:**

| View | Default columns (left → right) |
|---|---|
| Papers | checkbox · title · paper_uuid (mono) · authorship_mode · workflow state · q_signal · discipline · authors (intelliD pills) · transparency_complete · ai_log_complete · `rs:*` · sealed (gov chip) · action |
| AI Sessions | checkbox · session_label · paper link · vendor · model · version · mode · contribution_scope · risk_flags · redaction_status · session_hash (mono) · action |
| Didn't Make It | checkbox · session link · paper link · prompt preview (clamp 1) · reason_excluded · redacted · cross-link suggestions count · action |
| Remsearch | checkbox · paper link · citation_title · source_type · used · reason · discipline · action |
| Review Logs | checkbox · paper link · reviewer IntelliD · review_date_relative · version_reviewed · recommendation · per-criterion mini-bars · action |
| Versions | checkbox · paper link · version label · file path · ai_authorship · model_name · generation notes (clamp 1) · action |
| Attribution | checkbox · paper link · contributor_name (or IntelliD) · role · contribution_type · ai_or_human · ai_tool_used · action |
| Quality Signals | checkbox · paper link · q_signal · computation cycle · weight set · sub-scores mini-bar (originality / methodology / transparency / ai-disclosure / reproducibility / writing) · action |
| Plugins Used | checkbox · paper link · plugin_name · plugin_type · execution_context · run count · action |
| API Keys | checkbox · description · key (mono masked, copy icon) · owner IntelliD · access_level · status · action |
| API Logs | checkbox · endpoint · key_id · response_code · request_data (clamp 1, mono) · time-bucket bar · action |
| Templates | checkbox · template name · type · active · last edited cycle (relative) · action |
| Modules | checkbox · title · position · group · published · ordering · action |

---

## Unique admin views (full prompt)

### Page: Admin Dashboard
**Role / ACL:** `eaiou_Admin`+.
**URL:** `/administrator/index.php?option=com_eaiou&view=dashboard`

**Page blocks:**
1. **Admin chrome.**
2. **KPI grid (full-width, 6 cards × 2 rows, 1px `--paper3`, padding 20px):**
   - Active papers (count + sparkline 8 cycles `--river`)
   - Active reviews (count + spark `--amber`)
   - Active AI sessions (count + spark `--violet`)
   - Didn't-Make-It corpus size (count + cumulative line `--violet`)
   - API calls last cycle (count + spark `--river`)
   - Open governance audits (count + spark `--coral`)
   - Plugins published (count chip per plugin name, mono row)
   - Modules rendered (count chip per module name)
   - Mail templates active (count + warnings count)
   - Cache hit rate (donut sage/coral)
   - DB size (relative bar with mono GB label)
   - Backup status (sage tick / amber / coral)
3. **Recent activity stream (full-width band):**
   - Mono 11pt header `RECENT ACTIVITY (REVERSE-SEALED — INTERNAL ONLY)`.
   - Stacked rows of system events: state transitions, decisions, governance unlocks, API key actions, plugin enable/disable. Each row: relative-time bar (admin sees raw cycle slot, not absolute) · IntelliD · action chip · target · mono note.
4. **Doctrine reminder strip (`--paper2` bg, italic Spectral 14pt, 4px `--river` left border):** "Sealed timestamps are visible to admin only after governance unlock. Public discovery never sees them."
5. **Status bar.**

**States:** standard.
**Sample data (max 2 sentences):** Top-row KPIs show 312 active papers (trending up), 47 active reviews (flat), 89 AI sessions (trending up), and 4 open governance audits flagged coral. The activity stream's most recent row reads "EIC `INT-3F12` issued governance unlock for paper `paper_uuid:8f2a-...` · scope: sealed_acceptance · 14m window".
**Observer projection note:** Admin/EIC view. UNKINT toggle exposes raw timestamps in activity stream (governance unlock required).

---

### Page: AI Sessions detail (per-row)
**Role / ACL:** `eaiou_Admin`, `eaiou_EIC`.
**URL:** `/administrator/index.php?option=com_eaiou&view=ai_session&id={id}`

**Page blocks:**
1. **Admin chrome + breadcrumb mono.**
2. **Detail card (full-width, `--surface` bg, 1px `--paper3`, padding 24px):**
   - Title row: paper link · session_label · model · mode · vendor · version.
   - Stats grid (mono 13pt): start_token_count · end_token_count · prompt count · output count · risk_flags chips.
   - Prompt list (collapsible accordion entries):
     - Each entry: prompt_hash (mono) · prompt text (Spectral 14pt, redaction-aware) · output text · output_type chip · contribution_scope · oversight chip · risk_flags · redactions textarea (read-only unless gov unlock).
   - Cross-links panel:
     - Mono 11pt header `CROSS-DOMAIN LINKS`.
     - List of suggested links to didntmakeit corpus + un-space artifacts where this session's prompts/outputs match.
3. **Action toolbar:** Redact · Unredact (gov-unlock) · Cross-link · Export JSON · Attach to paper.
4. **Status bar.**

**States:**
- redacted → entry shows `[REDACTED]` mono pill in `--coral`; click → modal explaining redaction reason + redacted-by IntelliD.
- gov-unlocked → entry shows raw text + amber banner "Governance unlock active · 14m remaining".
**Sample data (max 2 sentences):** Session detail shows 7 prompts, 2 redacted, 1 cross-linked to a didntmakeit entry in another paper; the cross-link panel suggests "high-similarity (0.83) to ai_session 4f8a in paper paper_uuid:c1d2-…".
**Observer projection note:** Admin/EIC HUMINT. UNKINT exposes redacted content under governance unlock only.

---

### Page: Didn't Make It detail (per-row)
**Role / ACL:** `eaiou_EIC`, `eaiou_Admin`.
**URL:** `/administrator/index.php?option=com_eaiou&view=didntmakeit&id={id}`

**Page blocks:**
1. **Admin chrome + breadcrumb.**
2. **Detail card:**
   - Header: parent session link · parent paper link · reason_excluded chip · redaction state chip.
   - Prompt + response side-by-side (Spectral 14pt, 50/50 split). Redacted by default — large `[CONTENT REDACTED — GOVERNANCE UNLOCK REQUIRED]` overlay; "Request unlock" button (mono UPPERCASE coral outline).
   - Cross-domain candidates list: mono table of similar didntmakeit entries from other papers, with similarity scores and "open candidate" links.
   - Penicillin metaphor callout (`--violet-l` bg, italic Spectral 14pt, 4px violet left): "What didn't make it here may be primary somewhere else. Don't delete; cross-link."
3. **Action toolbar:** Unredact (dual-key) · Cross-link to another paper · Export JSON.

**States:** redacted (default) / unlocked / cross-linked.
**Sample data (max 2 sentences):** Entry shows reason "low-confidence numerical output flagged at oversight=manual"; cross-domain candidates panel suggests one match in paper `paper_uuid:c1d2-…` at similarity 0.78. Unlock button reveals the prompt+response after dual-key confirmation.
**Observer projection note:** Admin/EIC only. Unredacted content reachable strictly via dual-key governance unlock with 15-minute window.

---

### Page: API Key detail
**Role / ACL:** `eaiou_Admin`.
**URL:** `/administrator/index.php?option=com_eaiou&view=api_key&id={id}`

**Page blocks:**
1. **Admin chrome.**
2. **Detail card:**
   - Description (Spectral 16pt) editable.
   - Key (mono, masked by default — `eaiou_xx....xxxx_x9F2A`); rotate button + copy-mask-on-copy toast.
   - Owner IntelliD pill (link to user).
   - Access level segmented (read · read+submit · read+submit+review · admin); changing requires admin confirm modal.
   - Status segmented (active · suspended · revoked).
   - Quotas mono table (rate limit per cycle bucket, total quota cycle, current usage bar).
   - Recent log preview: 20 most recent calls (mini-table; clicking opens API Logs filtered by this key).
3. **Action toolbar:** Rotate · Revoke · Suspend · Resume · Export (redacted).

**States:** active / suspended / revoked.
**Sample data:** Key `eaiou_xx....x9F2A` linked to `INT-9F2A` at access_level read+submit, current usage 18% of cycle quota, 47 recent calls all 200 OK.
**Observer projection note:** Admin only.

---

### Page: Sealed Audit (governance unlock surface)
**Role / ACL:** `eaiou_EIC`, `eaiou_Admin` — requires governance unlock dual-key.
**URL:** `/administrator/index.php?option=com_eaiou&view=sealed_audit`

**Page blocks:**
1. **Admin chrome.**
2. **Pre-unlock surface (default state):**
   - Centered card 560px, `--coral-l` bg, 4px `--coral` left border:
     - Spectral 300 28pt: "Sealed audit".
     - Spectral italic 14pt: "Sealed timestamps are isolated from discovery. Unlock requires dual-key authorization."
     - Form: primary admin password input · second-key requester (mono dropdown) · justification textarea (Spectral 16pt, min 80ch) · expected window (segmented 5/10/15 min) · scope select (single paper · cycle · global).
     - Action: `Request unlock` (`--river` filled). Triggers second-key out-of-band approval flow (mail + admin notification).
3. **Post-unlock surface:**
   - Banner mono UPPERCASE on `--coral-l`: `UNLOCKED · 14m REMAINING · SCOPE: paper_uuid 8f2a-... · JUSTIFICATION VIEWABLE BY EIC`.
   - Audit table — all sealed timestamps for the unlocked scope: paper_uuid · submission_sealed_at (mono raw timestamp) · sealed_by IntelliD · acceptance_sealed_at · publication_sealed_at · capstone DOI · submission_hash (mono).
   - Below table: "Unlock log" — every prior unlock event for this scope (mono rows: requester, approver, justification, scope, when).
4. **Action toolbar:** Lock now · Extend window (one-time +5m, requires re-approval) · Export audit (CSV with hashes only by default).

**States:** locked (default) / unlocking / unlocked / lock-expired.
**Sample data (max 2 sentences):** Locked state default. Unlocking flow requires EIC `INT-3F12` to enter justification "review reproducibility complaint filed by reviewer INT-9F2A on paper paper_uuid:8f2a-..." and the second-key admin approves out-of-band; post-unlock the audit table reveals submission_sealed_at = 2026-04-12 17:03:21Z.
**Observer projection note:** UNKINT only. The sealed timestamps never leave this surface and are not indexed.
**ACL governance unlock note:** This is THE governance unlock surface. Every other admin "gov unlock" link routes here scoped appropriately.

---

### Page: Settings (component config)
**Role / ACL:** `eaiou_Admin`.
**URL:** `/administrator/index.php?option=com_eaiou&view=options`

**Page blocks:**
1. **Admin chrome.**
2. **Tab strip:** General · Workflow · ACL · Plugins · Mail templates · API · Quality signals · Backups · About.
3. **Tab content (Joomla form pattern):** vertical stacked form groups; each setting has a mono helper line.
4. **Action toolbar:** Save · Save & Close · Save as Copy · Restore Defaults.

**Notable settings (sample):**
- Sort principle (read-only — locked to "q_signal").
- Temporal blindness enforcement (read-only — always on).
- AI participation policy (segmented disclose-required / disclose-optional / disclose-prohibited — current: disclose-required).
- Default `or_mode` for new submissions.
- Quality signal weights JSON.
- Mail SMTP config (Joomla core).
- API rate limit defaults.
- Backup cadence (mono interval picker — relative slots only).

**States:** dirty (unsaved) / saved / error.
**Sample data:** Quality signal weights JSON `{"originality":0.2,"methodology":0.2,"transparency":0.15,"ai_disclosure":0.15,"reproducibility":0.15,"writing":0.15}`.
**Observer projection note:** Admin only.

---

### Page: Templates manager (decision letters + mail)
**Role / ACL:** `eaiou_Admin`, `eaiou_EIC`.
**URL:** `/administrator/index.php?option=com_eaiou&view=templates`

This view follows the list-manager pattern with one extension:
- **Edit form (when editing a single template):** Spectral 16pt rich-text + mono 12pt token panel showing available variables (`{paper_title}`, `{author_intelliD}`, `{relative_window}`, `{recommendation}`, `{q_signal_preview}`, `{capstone_doi}`, `{open_reports_link}`). Drag tokens into the editor; token rendered as mono pill.
- **Preview pane (right, 320px):** renders sample variables substituted in. Toggle between author-letter view and reviewer-invitation view.

---

### Page: Modules manager
**Role / ACL:** `eaiou_Admin`.
**URL:** `/administrator/index.php?option=com_eaiou&view=modules`

This view follows list-manager pattern with one extension:
- **Position map preview (right rail, 320px):** schematic of HelixUltimate template positions (header-a/b/c, sidebar-left/right, content-top/bottom, footer-a/b/c) with each module rendered as a labeled rectangle in its assigned position. Click a position → list of modules occupying it. Click a module → opens edit form.

---

### Page: Articles bridge view
**Role / ACL:** `eaiou_Admin`.
**URL:** `/administrator/index.php?option=com_eaiou&view=articles_bridge`

**Page blocks:**
1. Admin chrome.
2. Bridge intro band (mono 11pt UPPERCASE label, Spectral 14pt body): "This view links com_content articles to com_eaiou paper records. Each row shows article_id ↔ paper_uuid mapping and divergence flags."
3. Table:
   - Columns: checkbox · article_id (mono link to `com_content` edit) · paper_uuid (mono link to com_eaiou paper edit) · article state (chip) · paper status (chip) · divergence (sage check / coral X) · divergence reason · action.
4. Toolbar: Refresh bridge · Re-link · Export divergence report.

**States:** synced / divergent / orphan.
**Sample data:** 312 synced, 4 divergent (3 paper-state ahead of article-state, 1 article missing paper record).
**Observer projection note:** Admin only.

---

## End of `UXPILOT_05_admin.md`

Next file: `UXPILOT_06_modules.md` — sidebar/dashboard module specs.
