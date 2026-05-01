# UXPILOT_03 — reviewer pages

**Tokens, schemas, shells:** see `UXPILOT_00_design_system.md`.
**Philosophical canon:** see `UXPILOT_PROMPT_EAIOU.md`.
**Modules:** see `UXPILOT_06_modules.md`.
**Shells:** see `UXPILOT_07_layout_shells.md`.

Reviewer role = `eaiou_Reviewer`. All surfaces require login + an active assignment for the paper viewed (except queue).

---

### Page: Reviewer Queue
**Role / ACL:** `eaiou_Reviewer`.
**URL:** `/reviewer/queue`
**Joomla source:** mod_reviewer_queue → `eaiou_review_logs` joined with `eaiou_papers` filtered to current reviewer's assignments.
**Layout shell:** both. Default fixed.
**Modules (right rail):** `mod_open_collaborate` filtered to reviewer's discipline, `mod_trending_ideas`.
**Wide-mode pull-down extras:** `mod_ai_usage_heatmap`, `mod_intellid_graph`.

**Page blocks:**
1. **Header chrome.**
2. **Page band:** Spectral 300, 36pt: "Reviewer queue". Sub mono UPPERCASE `INTELLI-D INT-9F2A · ACTIVE ASSIGNMENTS`.
3. **Stats strip (mono 13pt, `--paper2` bg, 64px tall, 1px bottom `--paper3`):**
   - Active · Due window remaining (rendered as relative bar `▣▣▣▢▢▢▢` with mono caption "early / mid / late") · Reviews submitted this cycle · Decline rate · Median completion (relative, no clock).
4. **Filter chip group:**
   - Status: All · Pending invitation · Accepted · In progress · Submitted · Declined.
   - Urgency: Early · Mid · Late · Overdue.
   - Discipline.
5. **Assignment cards (full-width 880px in fixed; grid in wide):**
   - Each card 1px border `--paper3`, padding 20px, 120px tall:
     - Top row: paper title (Spectral 600, 22pt, link disabled until accepted) + AI-Logged + Open Reports + Un Scientific flag (if any).
     - Mid row: anonymized author bar (mono `[author identity gated]`) — depends on or_mode.
     - Bottom row: relative-due bar (no date), `rs:*` tag chips, recommendation chip if started, action buttons.
   - Action buttons (mono UPPERCASE 11pt outline): `Accept` (sage outline) · `Decline` (coral outline) · `Open paper →` (river outline) · `Open review console →` (river filled, only when accepted).
6. **Review history accordion (collapsed, below queue):**
   - Mono 11pt UPPERCASE header `MY REVIEW HISTORY`. Click → expands to show past reviews this reviewer submitted. Each row: title (Spectral 14pt, link), recommendation chip, q_signal of paper at decision time, "open report" link if published. **No dates.**
7. **Footer chrome.**

**Tags / badges rendered:** Open Reports, AI-Logged, Un Scientific, `rs:*` (visibility filtered to reviewer-tier), workflow state chip.
**States:**
- loading → 4 skeleton cards.
- empty → mono 14pt "no active assignments. The river will route work to your IntelliD when it matches your discipline tags."
- error → coral stripe.
**Sample data (max 2 sentences):** Three assignments shown — top one "Sealed-time effects on peer review participation rates" mid-window, AI-Logged · Open Reports · `rs:Replication`. Author identity rendered as `[author identity gated — open at submission]` per `or_mode = open_identities` not yet authorized for HUMINT until reviewer accepts.
**Interactions:** Accept → confirmation modal explaining ASK↔GOBACK availability and the relative-due window; Decline → modal with reason picker (CoI · Workload · Outside expertise · Other); Open paper → /reviewer/paper/{id}; Open console → /reviewer/paper/{id}/review.
**Observer projection note:** HUMINT default. Author IntelliDs always visible (assignment requires it). Author display names gated by or_mode + reviewer accept.
**ACL governance unlock note:** N/A.

---

### Page: Reviewer Paper View
**Role / ACL:** `eaiou_Reviewer` with active assignment.
**URL:** `/reviewer/paper/{id}`
**Joomla source:** com_content article view with reviewer-tier overrides + plg_content_* full enrichment + AI session log unlocked.
**Layout shell:** wide-default (the paper is dense).
**Modules (right rail):** `mod_intellid_graph` (this paper), `mod_appreciated_scale`, `mod_open_collaborate` filtered to this paper's tags.
**Wide-mode pull-down extras:** `mod_ai_usage_heatmap` (paper-scoped).

**Page blocks:**
1. **Header chrome.**
2. **Reviewer banner (sticky top below chrome, 56px tall, `--river-ll` bg, 1px bottom `--river`):**
   - Mono 11pt UPPERCASE `REVIEWER VIEW · ASSIGNMENT ACTIVE · MID-WINDOW ▣▣▣▢▢▢▢`.
   - Right-aligned actions: `Open review console →` (`--river` filled, mono 12pt UPPERCASE) · `Decline assignment` (coral outline) · `Save in-progress notes` (outline).
3. **Paper masthead (same structure as public detail page; defer to `UXPILOT_01 §Paper detail`).** Differences for reviewer:
   - q_signal not yet computed (`q=—` placeholder).
   - Author IntelliDs visible. Display names visible per or_mode.
   - Capstone DOI hidden (not yet sealed at acceptance).
4. **Tab strip — extended for reviewer:**
   Tabs: Abstract · Manuscript · Sources · Datasets · Methods · AI Usage · Open Reports (existing, if mid-cycle) · Versions · Attribution · NotTopic Index · **AI Session Log (full)** · **Reviewer notes (private)** · **Un Scientific flag**.
   New reviewer-only tabs:
   - **AI Session Log:** every AI session ungated. Table — vendor, model, version, mode, contribution_scope, prompt_hash, output (linked), oversight, risk_flags, redactions. Mono throughout. Below table: link to full didntmakeit corpus for this paper (gated, opens modal).
   - **Reviewer notes (private):** Spectral textarea (full height of tab area). Mono helper line: "private to your IntelliD; not visible to other reviewers, editors, or authors."
   - **Un Scientific flag:** form to set/edit `unsci_*` fields. unsci_active toggle · entries repeatable · risk_level chip · requested_action select · resolution path (mono helper: "this flag becomes visible to editorial; if confirmed, becomes a paper-level Un Scientific badge").
5. **Sidebar inline (below right rail, only in wide):**
   - Mono 11pt header `ASK ↔ GOBACK`. List of any active TAGIT sessions for this paper, with one-click "open session →".
6. **Action footer (sticky bottom, 64px):** same as queue actions.

**Tags / badges rendered:** all paper badges + workflow chip `under_review` + Un Scientific (if set).
**States:**
- loading → masthead + tab skeleton.
- locked (assignment expired) → banner mono `--coral-l`: "your review window closed; submit anyway? Editor approval required."
**Sample data (max 2 sentences):** A reviewer mid-task sees the AI Session Log tab — 7 sessions, 3 with risk_flags (numerical, attribution, citation-fabrication-risk), 2 with redactions; the reviewer adds a note "session 4 prompt-hash 8f2a appears to have generated the §3.2 numerical claim — needs primary verification".
**Interactions:** tab nav same as public detail; Reviewer notes auto-saves; AI Session Log row click opens session detail modal with prompt + output preview; Un Scientific tab "save flag" triggers editorial notification (mono toast).
**Observer projection note:** Reviewer-tier HUMINT (extended). UNKINT not exposed at reviewer tier.

---

### Page: Reviewer Rubric Console
**Role / ACL:** `eaiou_Reviewer` with accepted assignment.
**URL:** `/reviewer/paper/{id}/review`
**Joomla source:** com_eaiou review controller writing to `eaiou_review_logs`.
**Layout shell:** wide-default (split-screen rubric + manuscript).
**Modules:** none in main rail (focus mode); `mod_intellid_graph` available in pull-down.

**Page blocks:**
1. **Header chrome (slim — 56px).**
2. **Console masthead (`--surface` bg, 1px bottom `--paper3`, 100px tall):**
   - Paper title Spectral 22pt + IntelliD authors mono 11pt + workflow chip + Open Reports chip if enabled.
   - Right side: relative-due indicator (`▣▣▣▢▢▢▢ MID`) + auto-save state mono.
3. **Two-column split (full-width):**
   - **Left col (50% width, max 700px):** manuscript reader.
     - Sticky tab nav at top: Manuscript · Sources · Datasets · AI Sessions · Notes.
     - Manuscript pane: Spectral 16pt 1.65 line-height. Right margin shows reviewer comment markers — click any paragraph → "comment here" affordance. Highlight selection → comment popup.
   - **Right col (50% width):** review rubric form.
     - **Section 1 — Recommendation (Spectral 600 18pt):** segmented radio (Accept · Minor revisions · Major revisions · Reject · Refer to editor). Each option has mono 11pt rationale below.
     - **Section 2 — Per-criterion scores (5-pt scale, rendered as 5 dots stacked into a horizontal bar):**
       - Originality
       - Methodology
       - Transparency
       - AI disclosure
       - Reproducibility
       - Writing quality
       - Overall (auto-computed mean, mono italic)
     - **Section 3 — Narrative (Spectral textarea):** "Reviewer commentary" with mono char counter. Min 200 chars.
     - **Section 4 — Per-section comments (collapsible list):** each comment links to a paragraph anchor in the manuscript pane.
     - **Section 5 — Open Reports consent:** checkbox "Publish my review with my IntelliD" (default off if `or_mode = summary_only`); shows `or_mode` constraint inline mono.
     - **Section 6 — Un Scientific check:** "Did you find a known-issue blocker requiring caveat?" toggle. If yes → opens Un Scientific flag form inline.
     - **Section 7 — Conflicts of interest:** "I declare no undisclosed conflicts" checkbox.
4. **Action footer (sticky, 80px tall):**
   - Left: `Save draft` outline · `Validate completeness` outline.
   - Right: `Submit review` `--river` filled (gated until rubric complete + narrative ≥ 200 chars + CoI checked).
   - Below buttons: mono 11pt completeness chips for each section (sage check / coral X).
5. **Footer chrome.**

**Tags / badges rendered:** workflow state, recommendation chip (preview as user selects).
**States:**
- loading skeleton.
- saved → toast mono "draft saved".
- submitted → modal mono "review submitted · sealed to review log · editor will be notified". Redirect to /reviewer/queue.
- error → coral stripe.
**Sample data (max 2 sentences):** A reviewer mid-rubric: Originality 4/5, Methodology 3/5 with a per-section comment "§3.2 derivation skips a step", Transparency 5/5, AI disclosure 5/5, Reproducibility 3/5, Writing 4/5; recommendation set to Minor revisions, narrative 380 chars. The Un Scientific toggle is on, with a low-risk entry pointing at §3.2.
**Interactions:** highlighting text in manuscript opens "Add comment" popup that creates a per-section comment row with anchor; rubric scores show a live small bar chart of all 6 dimensions on the right; submit triggers seal-and-write modal.
**Observer projection note:** Reviewer HUMINT only. The review will be projected to: (a) editor view in full; (b) author view per or_mode (open_reports → full text + IntelliD; summary_only → recommendation + per-rubric scores; editorial_only → editor-mediated summary).

---

### Page: ASK ↔ GOBACK Session
**Role / ACL:** `eaiou_Reviewer` (initiator) and paper author (responder), or other paired roles per TAGIT.
**URL:** `/session/{session_id}` (deep link from paper view or review console).
**Joomla source:** com_eaiou TAGIT session controller; sessions persisted in a `eaiou_tagit_sessions` table (referenced by `UXPILOT_PROMPT_EAIOU.md` core framing).
**Layout shell:** fixed; centered 880px column to keep TAGIT visible end-to-end.

**Page blocks:**
1. **Header chrome (slim).**
2. **Session masthead (sticky, 80px tall, `--surface` bg, 1px bottom `--paper3`):**
   - Mono 11pt UPPERCASE `TAGIT SESSION · LIVE`.
   - Spectral 22pt paper title link.
   - Participants pills row: initiator IntelliD (river) · responder IntelliD (sage) · observers count (mono).
   - Session lock indicator (mono UPPERCASE on `--river` chip): `SESSION LOCK · ENCRYPTED`.
   - Right actions: `Pause session` outline · `Lock & archive (TRACK)` `--river` filled.
3. **TAGIT timeline (full height of column):**
   - Each entry rendered as a vertical-thread card with mono prefix indicating its TAGIT phase:
     - `TASK ↳` — initial work statement (Spectral 16pt, `--paper2` bg).
     - `ASK ↳` — clarifying question (Spectral 16pt, `--river-ll` bg, 4px left `--river` border).
     - `GOBACK ↳` — response with results or further questions (Spectral 16pt, `--violet-l` bg, 4px left `--violet` border).
     - `IS ↳` — status checkpoint, often by Scorch (QC) (Spectral 16pt italic, `--amber-l` bg, 4px left `--amber` border).
     - `TRACK ↳` — completion lock (Spectral 16pt, `--sage-l` bg, 4px left `--sage` border).
   - Each card carries: phase chip · author IntelliD · message Spectral 16pt · attached files mono row · structural tags (`[FORK]`, `[SECURITY]`, `[VULNERABILITY]`, `[BOUNDARY]`, `[ASSUMPTION]`, `[OPEN]`, `[DISCARDED]`) inline as mono pills.
4. **Composer dock (sticky bottom, 200px tall, `--surface` bg, 1px top `--paper3`):**
   - Phase selector segmented control: `ASK · GOBACK · IS · TRACK`.
   - Spectral textarea 6 rows.
   - Inline tag inserter mono dropdown of structural tags.
   - File attach zone (mono dashed).
   - Send button: `--river` filled, mono UPPERCASE 12pt: phase-aware label ("Ask now", "Go back", "Mark IS", "TRACK & seal").
5. **Right rail (collapsible, 280px, only in wide):**
   - Mono header `STRUCTURAL MAP`. Renders the TAGIT tree visually — a vertical chain with branches at any FORK, links to siblings, and a final TRACK node. Click any node → scrolls timeline.
6. **USO record preview (footer band, 64px, `--paper2` bg):**
   - Mono 11pt: when TRACK is reached, this band shows the auto-generated USO record hash and a "view USO" link.

**Tags / badges rendered:** TAGIT phase chips, structural tags, session lock indicator.
**States:**
- live → session lock chip pulses (1px outline animation).
- paused → mono banner `--amber-l`: "session paused; resume from any participant".
- tracked (closed) → composer disabled; mono banner `--sage-l`: "session locked. USO record written."
**Sample data (max 2 sentences):** A reviewer (`INT-9F2A`) sends `ASK` "in §3.2 the derivation jumps from line 4 to line 6 — what's the intermediate step?" with `[OPEN]` tag. The author (`INT-A831`) replies with `GOBACK ↳` posting an attached LaTeX snippet and tagging `[FORK]` showing two valid intermediate paths.
**Interactions:**
- Phase selector enforces TAGIT cycle order (ASK before GOBACK; IS before TRACK); UI gently rejects out-of-order with mono inline message.
- Drag-attached files render as mono pill rows.
- Right-rail node click → scrolls timeline; also collapses/expands sub-threads.
- TRACK action shows confirmation modal with USO record summary; on confirm → seals session, writes USO record, redirects participants.
**Observer projection note:** HUMINT default. Each TAGIT entry's IntelliD is visible to participants; observers see anonymized initials only unless paper's `or_mode` permits identity.
**ACL governance unlock note:** USO record is the source of truth post-TRACK and is auditable by `eaiou_Admin` only via governance unlock.

---

### Page: Reviewer Profile / Settings (sub-surface)
**Role / ACL:** `eaiou_Reviewer`.
**URL:** `/reviewer/profile`
**Layout shell:** fixed.

**Page blocks:**
1. **Header chrome.**
2. **Centered card (640px):**
   - Title "Reviewer profile" Spectral 300 28pt.
   - Form (mono labels, Spectral inputs):
     - IntelliD (read-only, mono).
     - ORCID (link button if not linked; mono display if linked).
     - Discipline tags (multi-select).
     - Methodology tags (multi-select).
     - Workload preference: max active assignments (number input).
     - Availability toggle.
     - Decline reasons template (textarea, optional pre-filled boilerplate).
     - Open-Reports consent default (segmented).
   - Save button `--river` filled.
3. **Performance stats panel (mono 11pt):**
   - Reviews completed (cycle / lifetime).
   - On-time rate.
   - Decline rate.
   - Recommendation distribution (5-bar mini chart in palette).
   - Median completion (relative bar; never absolute time).
4. **Footer.**

**Sample data (max 2 sentences):** Profile shows discipline tags Cosmology + Statistics, max active 3, availability on; performance: 12 reviews completed lifetime, on-time 91%, recommendations distributed 25% Accept / 33% Minor / 25% Major / 17% Reject. Median completion bar shows mid-window across cycle.
**Observer projection note:** HUMINT only.

---

## End of `UXPILOT_03_reviewer.md`

Next file: `UXPILOT_04_editor.md` — editor list, paper management panel, assignment, decision render.
