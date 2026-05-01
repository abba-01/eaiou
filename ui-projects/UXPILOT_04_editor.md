# UXPILOT_04 — editor pages

**Tokens, schemas, shells:** see `UXPILOT_00_design_system.md`.
**Philosophical canon:** see `UXPILOT_PROMPT_EAIOU.md`.
**Modules:** see `UXPILOT_06_modules.md`.
**Shells:** see `UXPILOT_07_layout_shells.md`.

Editor role = `eaiou_Editor` (inherits `eaiou_Reviewer`). EIC = `eaiou_EIC` (inherits `eaiou_Editor`). All editor surfaces require login + editor group membership.

---

### Page: Editorial Papers (list / dashboard)
**Role / ACL:** `eaiou_Editor` and above.
**URL:** `/editorial/papers`
**Joomla source:** com_eaiou editor view → all `eaiou_papers` joined with article state, plus mod_editor_dashboard KPI feed.
**Layout shell:** wide-default (KPI dashboard needs space).
**Modules (right rail):** `mod_editor_dashboard` (full version, takes over the rail in fixed; full-bleed in wide), `mod_open_collaborate`.
**Wide-mode pull-down extras:** `mod_ai_usage_heatmap`, `mod_gap_map`, `mod_intellid_graph`.

**Page blocks:**
1. **Header chrome.**
2. **Page band:** Spectral 300, 36pt: "Editorial". Sub mono UPPERCASE `EIC INTELLI-D INT-3F12 · CYCLE q4`.
3. **KPI strip (full-width, 140px tall, 1px bottom `--paper3`, `--surface` bg):**
   - 6 cards in horizontal grid, each 1px `--paper3`, padding 16px:
     - **Under review** — count (Spectral 600, 36pt, `--ink`); 60-px sparkline of last 8 cycles (line in `--river`, no axis labels); mono 11pt label.
     - **Decision pending** — count + sparkline `--violet`.
     - **Overdue (relative)** — count + sparkline `--coral`. Relative-only, no clock.
     - **Median TTFD (time-to-first-decision, relative bar `▣▣▣▢▢▢▢`)** — large relative bar + percentile mono.
     - **Acceptance rate (cycle)** — donut chart 80px diameter (sage = accepted, ink3 = rejected) + percentage mono center.
     - **Reviewer pool active** — count + small intellid-graph mini (8 dots colored by activity tier).
4. **Action strip (right-aligned, 56px tall, `--paper2` bg):**
   - Primary `+ ASSIGN BATCH` (`--river` filled) → opens batch assignment modal (multi-select queue).
   - Secondary `Export queue (CSV)` outline.
   - Secondary `Settings →` outline → /editorial/settings.
5. **Tab strip (sticky, 48px tall):**
   Tabs: All · Submitted · Under review · Revisions requested · Decision pending · Accepted · Published · Rejected · Archived · Flagged (Un Scientific).
   Each tab shows count chip mono.
6. **Filter rail (sticky beneath tab strip, 56px tall, `--paper2` bg):**
   - Discipline multi-select.
   - `rs:*` filter.
   - AI-Logged toggle.
   - Open Reports toggle.
   - Reviewer assignment status: All · Has assignments · Needs assignments · Has overdue.
   - Sort: q_signal DESC (default) · workflow age (relative bar) · reviewer load.
7. **Paper table (full-width):**
   - Columns (mono UPPERCASE 11pt headers):
     - Title · State · Authors · Reviewers (assigned/accepted/in/done) · `rs:*` · Open Reports · AI-Logged · q_signal · Action.
   - Title col: link + abstract preview clamped 1 line.
   - State col: workflow chip per `UXPILOT_00 §8`.
   - Authors col: IntelliD pills (max 3 visible, +N overflow).
   - Reviewers col: composite indicator — fraction bar 4 segments (assigned / accepted / in-progress / done) colored sage→amber→coral by remaining-window pressure.
   - Action col: 3-dot menu — Manage · Assign reviewers · Decide · View as reviewer · View as author · Open governance audit.
   - Row hover: subtle `--paper2` background.
   - Flagged-row indicator: 4px left border `--coral` if Un Scientific or major-revision-overdue.
8. **Aggregate footer band (32px, mono 11pt, `--paper2` bg):**
   - "Showing 47 of 312 papers · q ≥ 0.000 · cycle q4 · sealed audit available with governance unlock".
9. **Footer chrome.**

**Tags / badges rendered:** workflow chips, AI-Logged, Open Reports, Un Scientific, ORCID, `rs:*`, Sealed.
**States:**
- loading → KPI skeletons + 10 row skeletons.
- empty (filter excludes everything) → mono "no papers in this slice — adjust filters".
- error → coral stripe.
**Sample data (max 2 sentences):** KPI strip shows 47 under-review (sparkline trending up), 12 decision-pending, 4 overdue (relative); a flagged row at the top renders "Sealed-time effects on peer review participation rates" with reviewers 3/2/1/0 (one missing), `rs:Replication`, AI-Logged, q=— · action menu open. Table is sorted by q_signal but shows a coral 4px stripe on the left of the flagged row.
**Interactions:**
- Tab click → URL state update + filter chip preset.
- Row click → /editorial/paper/{id} (manage panel).
- 3-dot menu items navigate to deep links.
- KPI sparkline hover → tooltip mono with cycle slot count.
- Batch select via row checkbox column (when in "Assign batch" mode); mono toolbar appears.
**Observer projection note:** Editor HUMINT (full identity surface for assigned reviewers and authors). UNKINT toggle exposes sealed timestamps (governance unlock required at EIC tier) and tensor coords.
**ACL governance unlock note:** A "governance audit" link in the action menu opens a modal requiring an EIC governance unlock (mono dual-key prompt) to reveal sealed dates for that one paper.

---

### Page: Paper Management Panel
**Role / ACL:** `eaiou_Editor`+.
**URL:** `/editorial/paper/{id}`
**Joomla source:** com_eaiou paper view in editor mode.
**Layout shell:** wide-default.
**Modules (right rail):** `mod_intellid_graph` (this paper), `mod_appreciated_scale`, `mod_open_collaborate`.
**Wide-mode pull-down extras:** `mod_ai_usage_heatmap` (paper-scoped).

**Page blocks:**
1. **Header chrome.**
2. **Editor banner (sticky 56px, `--river-ll` bg):**
   - Mono UPPERCASE `EDITORIAL VIEW · MANAGEMENT PANEL`.
   - Right actions: `Quick decide →` (`--river` filled, jumps to /editorial/decide/{id}) · `Assign reviewers →` outline · `Open as reviewer` outline · `Governance audit` (coral outline, EIC only).
3. **Paper masthead (same as reviewer view; full identity unlocked).**
4. **Tab strip — extended editor tabs:**
   Tabs: Overview · Manuscript · Sources · AI Usage · Open Reports · Versions · Attribution · NotTopic · **Reviewers** · **Decisions log** · **Editor notes (private)** · **Sealed audit (EIC + governance unlock)**.
   - **Overview tab** is the default landing; aggregates everything in a dashboard layout:
     - Top: KPI cards specific to this paper — relative review window, reviewer participation %, AI-risk flags count, transparency completeness %, q_signal preview (computed; mono).
     - Mid: stacked timeline of state transitions (Spectral nodes connected by hairlines, no dates — only relative ordering).
     - Bottom: alerts band — any Un Scientific entries, any overdue reviewers, any pending author response on revisions. Each alert is a `--amber-l` or `--coral-l` strip with anchor link.
   - **Reviewers tab:** table of all reviewers assigned (current + historical):
     - IntelliD · status chip (Pending / Accepted / In progress / Submitted / Declined / Overdue) · recommendation chip (preview if reviewer in progress) · per-criterion mini-bars · "View review →" link · "Send reminder" button (mono outline) · "Reassign" 3-dot menu.
   - **Decisions log:** vertical stack — every editor decision on this paper (revision request, accept, reject, withdraw, etc.). Each entry: action chip + editor IntelliD + Spectral 14pt note + mono 11pt anchor to the decision letter modal.
   - **Editor notes (private):** Spectral textarea (full tab height); not visible to authors or reviewers.
   - **Sealed audit:** disabled chip until EIC governance unlock; on unlock → table of sealed timestamps (submission, acceptance, publication) with hashes mono.
5. **Right rail with modules.**
6. **Action footer (sticky bottom, 64px):**
   - Left: state chip + relative window indicator.
   - Right: `Save editor notes` outline · `Send to authors (revisions)` outline · `Decide →` `--river` filled.
7. **Footer chrome.**

**Tags / badges rendered:** all paper badges + workflow + Un Scientific + per-reviewer status chips.
**States:**
- loading → tab skeleton.
- decision-locked → all action buttons disabled with mono banner: "decision finalized; open new appeal at /editorial/appeal/{id}".
**Sample data (max 2 sentences):** Overview tab shows 4 reviewers — 2 submitted (recommendations Minor + Major), 1 in progress, 1 declined; 1 Un Scientific entry low-risk on §3.2; transparency 100%, AI log 100%, q_signal preview 0.81. Alerts band shows a single amber strip "Reviewer 4 declined — replacement assignment recommended".
**Interactions:** tab switch persists; "Send reminder" opens mono modal with templated message and a one-click send; "Reassign" opens reviewer search modal (same as /editorial/assign); EIC governance unlock requires dual-key flow modal.
**Observer projection note:** Editor HUMINT (full identity surface). UNKINT toggle adds sealed audit columns to several tabs (EIC only after unlock).

---

### Page: Reviewer Assignment
**Role / ACL:** `eaiou_Editor`+.
**URL:** `/editorial/assign/{id}` (or `/editorial/assign/batch` for bulk)
**Joomla source:** com_eaiou assign controller; reviewer pool from `#__users` filtered by group `eaiou_Reviewer`, joined with reviewer profile (discipline tags, workload, performance).
**Layout shell:** wide.
**Modules:** none (focus surface).

**Page blocks:**
1. **Header chrome.**
2. **Assignment masthead (`--surface` bg, 100px tall, 1px bottom `--paper3`):**
   - Spectral 22pt: "Assign reviewers — *<paper title>*".
   - Discipline + `rs:*` tags pulled from paper rendered as inactive chips with mono helper "matched suggestion criteria".
   - Right side: required-reviewer count (number stepper, default 3), relative deadline window picker (segmented Early / Mid / Late).
3. **Two-column layout:**
   - **Left col (60%): suggestion list** sorted by match score desc.
     - Each row: reviewer IntelliD pill · discipline tags · methodology tags · workload bar (`▣▣▣▢▢▢▢`) · performance mini-stats (mono — completed N, on-time %, decline %) · CoI flag if any (coral chip).
     - Match score: mono 13pt + 60px horizontal bar `--river`. Score weighted from discipline overlap + workload available + performance + recent activity.
     - Action: `+ Invite` button (`--river` filled, mono UPPERCASE 11pt).
     - Filter strip at top of col: discipline overlap min slider, workload max, exclude-CoI toggle, exclude-recent-coauthor toggle, min-performance toggle.
   - **Right col (40%): assignment basket** — sticky:
     - Mono header `INVITED` count chip.
     - Stack of invited reviewers' IntelliD cards with relative-deadline pill and "Remove" mono outline.
     - Below: invitation message template (Spectral textarea) — pre-filled mono variables `{paper_title}`, `{relative_window}`.
     - Send-invites action: `--river` filled, mono UPPERCASE 14pt: `Send N invitations`.
4. **Conflict-of-interest alerts strip (sticky bottom, 64px, `--coral-l` bg if any CoI flagged):**
   - Mono 11pt: "2 potential CoIs flagged (co-authorship within 24 months, same institution). Review before sending."
5. **Footer chrome.**

**Tags / badges rendered:** discipline tags, `rs:*`, CoI flags, performance stats.
**States:**
- loading → 8 suggestion skeletons.
- empty (no matches) → mono "no qualified reviewers found — broaden discipline or lower workload threshold".
- error → coral stripe.
- sent → mono toast with count of invitations queued + relative-window summary.
**Sample data (max 2 sentences):** Suggestions list ranks `INT-9F2A` first (match 0.91, discipline overlap Cosmology+Statistics, workload mid, performance 91% on-time) and shows 2 of 12 candidates flagged for potential CoI; the editor invites three reviewers and adjusts the window to Mid. The invitation message is pre-filled with the paper title and relative window indicator.
**Interactions:**
- Filter sliders re-rank list live.
- "+ Invite" moves the row from suggestion list into basket; basket card carries the same intelliD.
- Drag-and-drop alternative: drag suggestion card onto basket.
- Bulk-mode (`/editorial/assign/batch`): table view of papers with "auto-suggest" mass action that pre-fills baskets per paper.
- Send-invites triggers TAGIT TASK creation per reviewer (see `UXPILOT_PROMPT_EAIOU.md`).
**Observer projection note:** Editor HUMINT. Reviewer ORCID and full names visible to editor (assignment requires it).

---

### Page: Decision Render
**Role / ACL:** `eaiou_Editor`+ (some decisions EIC-only per ACL).
**URL:** `/editorial/decide/{id}`
**Joomla source:** com_eaiou decide controller; writes to article state + `eaiou_review_logs` summary + decision letter template.
**Layout shell:** fixed 1080px-centered (formal document feel).
**Modules:** none.

**Page blocks:**
1. **Header chrome.**
2. **Decision masthead (`--surface` bg, 120px tall, 1px bottom `--paper3`):**
   - Spectral 300 32pt: "Decision — *<paper title>*".
   - Mono UPPERCASE `EDITOR INTELLI-D INT-3F12 · DECISION QUEUE OPEN`.
   - Right side: relative window status, q_signal preview, current state chip.
3. **Decision form (centered 720px):**
   - **Section 1 — Decision (Spectral 600 18pt):** segmented radio (Accept · Accept with minor revisions · Accept with major revisions · Revise & resubmit · Reject · Refer to EIC). Each option shows mono 11pt impact note.
   - **Section 2 — Letter to author (Spectral textarea):**
     - Pre-filled from template by decision (mono helper: "edit freely; reviewer comments will be auto-attached").
     - Toolbar mono 11pt UPPERCASE: `BOLD · ITALIC · QUOTE · INSERT REVIEWER N · INSERT TAG`.
     - Char counter mono.
   - **Section 3 — Reviewer comments to attach:** checklist — each reviewer's comments toggleable in/out; per-reviewer redaction options.
   - **Section 4 — Open Reports publication:** if paper has `or_enabled` — radio (publish all reviews · publish summary only · editorial gating). Shows constraint per `or_mode`.
   - **Section 5 — Public statement (Spectral textarea):** optional, only for accept; appears on the published paper as editor's note.
   - **Section 6 — Internal notes:** Spectral textarea, EIC-only field.
4. **Preview pane (sticky right, 320px, `--paper2` bg):**
   - Mono header `LETTER PREVIEW`.
   - Renders the decision letter as it will appear to the author. Spectral 14pt body, mono 11pt header band.
   - Below: a checklist of post-decision actions auto-triggered (state transition, mail templates, capstone DOI request if accepting, archive transition if rejecting).
5. **Action footer (sticky 80px):**
   - Left: `Save draft decision` outline.
   - Right: `Submit decision & seal` `--river` filled, mono UPPERCASE 14pt; gated until letter ≥ 200 chars + reviewer attachments selected + decision selected. EIC-only decisions show extra dual-key confirmation modal.
6. **Footer chrome.**

**Tags / badges rendered:** workflow chip current + post-decision target chip; Un Scientific carryover badge if applicable.
**States:**
- loading → form skeleton.
- saved → mono toast.
- submitted → modal with capstone summary (if accept), USO record link, redirect to /editorial/papers.
- error → coral stripe.
**Sample data (max 2 sentences):** Decision set to "Accept with minor revisions" with letter pre-filled including 3 reviewer comments attached and 1 redacted (CoI overlap); preview shows acceptance language and a relative-window deadline for revisions; q_signal preview moves from 0.81 → 0.87 after decision applies. The Open Reports publication is set to "publish all reviews" per the paper's or_mode = open_identities.
**Interactions:** decision chip change → letter template auto-swaps with confirmation modal preserving any custom edits; reviewer attachment toggle updates preview; submit triggers seal-and-write modal (sealed acceptance/rejection time, capstone DOI request, mail send queue).
**Observer projection note:** Editor HUMINT for the decision form; the resulting decision letter projects per `or_mode` to the author and (if open_reports) to the public paper detail page.
**ACL governance unlock note:** EIC-only decisions (Refer to EIC, Reject after revisions, Override) require dual-key confirmation. The sealed acceptance time becomes part of governance audit only.

---

### Page: Editor Settings (sub-surface)
**Role / ACL:** `eaiou_EIC` only.
**URL:** `/editorial/settings`
**Layout shell:** fixed.

**Page blocks:**
1. **Header chrome.**
2. **Title:** "Editorial settings" Spectral 300 28pt.
3. **Settings groups (Spectral 600 18pt subheads):**
   - **Workflow defaults:** default reviewer count, default relative-window per state, decision template per outcome.
   - **Reviewer pool defaults:** discipline mapping rules, default match-score weights, CoI lookback months, exclude-recent-coauthor default.
   - **Open Reports defaults:** default `or_mode` for new submissions; override allowance per author.
   - **AI Usage defaults:** required `ai_display_level` minimum; risk-flag policy.
   - **Governance unlock policy:** EIC dual-key requirement; sealed-audit audit log retention.
4. **Save button (`--river` filled).**
5. **Footer chrome.**

**Sample data:** `default reviewer count = 3, default window = mid, default or_mode = open_reports, ai_display_level minimum = summary, dual-key required for sealed unlock`.
**Observer projection note:** EIC HUMINT only.

---

## End of `UXPILOT_04_editor.md`

Next file: `UXPILOT_05_admin.md` — admin (com_eaiou backend) surfaces.
