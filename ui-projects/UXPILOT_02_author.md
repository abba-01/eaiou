# UXPILOT_02 — author pages

**Tokens, schemas, shells:** see `UXPILOT_00_design_system.md`.
**Philosophical canon:** see `UXPILOT_PROMPT_EAIOU.md`.
**Modules referenced:** see `UXPILOT_06_modules.md`.
**Shells:** see `UXPILOT_07_layout_shells.md`.

Author role = `eaiou_Author`. All surfaces require login; redirect unauth → `/login` with `?redirect=` query.

---

### Page: My Papers
**Role / ACL:** `eaiou_Author` (own records only).
**URL:** `/mypapers`
**Joomla source:** com_content articles filtered by `created_by = current_user_id` + com_eaiou.eaiou_papers join for status.
**Layout shell:** both. Default fixed.
**Modules (right rail):** `mod_open_collaborate` (filtered to author's discipline), `mod_trending_ideas`.
**Wide-mode pull-down extras:** `mod_ai_usage_heatmap` (author-scoped), `mod_appreciated_scale` (author's gap-map matches).

**Page blocks:**
1. **Header chrome.**
2. **Page title strip:** Spectral 300 36pt "My Papers". Sub mono UPPERCASE: `INTELLI-D INT-9F2A · ORCID 0009-0006-5944-1742`.
3. **CTA strip (right-aligned, 56px tall, `--paper2` bg):**
   - Primary button (`--river` filled, mono UPPERCASE 12pt): `+ NEW SUBMISSION` → `/submit`.
   - Secondary button (outline `--river`): `Import bundle` → /submit step-2 with bundle pre-load.
   - Tertiary mono link: `Download all my data (JSON)`.
4. **Status filter chip group (sticky below CTA):**
   - All · Draft · Submitted · Under Review · Revisions Requested · Decision Pending · Accepted · Published · Archived · Rejected.
   - Active chip filled `--river`, others 1px outline `--paper3`.
5. **Paper table (centered 880px in fixed; full-width in wide):**
   - Column headers (mono 11pt UPPERCASE, `--ink3`):
     - Title · State · q_signal · Reviewer-side activity · Open Reports · AI-Logged · `rs:*` · Action.
   - **No date columns** in HUMINT view.
   - Row height 64px, 1px bottom `--paper3`.
   - Title col: Spectral 600 16pt link + abstract preview (Spectral 14pt italic, 1-line clamp, `--ink2`).
   - State col: workflow chip per `UXPILOT_00 §8`.
   - q_signal col: 80px bar + mono 13pt value (only present for ≥accepted).
   - Reviewer-side activity col: small composite indicator — N invites sent / M accepted / K reviews in (mono).
   - Open Reports col: river chip if enabled, blank otherwise.
   - AI-Logged col: violet chip if `ai_used`.
   - `rs:*` col: chips wrap (max 3 visible, "+N" overflow).
   - Action col: 3-dot menu opening: Workspace · Revise · Withdraw · Download bundle · Delete (only for draft).
6. **Empty-state (no papers):**
   - Centered band 720px tall, Spectral italic 22pt: "No papers yet. The river is patient."
   - Two CTAs: "Start a submission →" and "Pre-fill from a trending idea →".
7. **Right rail with modules.**
8. **Footer chrome.**

**Tags / badges rendered:** workflow state chips, AI-Logged, Open Reports, ORCID, Sealed, `rs:*`.
**States:**
- loading → 6 skeleton rows.
- empty → see block 6.
- error → coral stripe + mono message.
**Sample data:** "Sealed-time effects on peer review participation rates" · `under_review` · q=— · 3/2/1 · Open Reports · AI-Logged · `rs:Replication`. Action menu shows "Workspace" disabled with tooltip "manuscript locked while under review".
**Interactions:** action-menu click → opens dropdown; row click anywhere except action col → /paper/{id}/workspace; status chip click → applies as a filter.
**Observer projection note:** HUMINT default. Author's own data — no UNKINT toggle relevant here. Sealed timestamps reachable only via separate "Sealed audit" tab gated to admin.

---

### Page: Paper Workspace
**Role / ACL:** `eaiou_Author` (own paper); also `eaiou_Editor`/`eaiou_EIC` (any paper, with editorial overlays).
**URL:** `/paper/{id}/workspace`
**Joomla source:** com_content article edit + com_eaiou paper context + plg_content_* enrichment in editable mode.
**Layout shell:** wide-default (manuscript editor needs space).
**Modules (right rail):** `mod_open_collaborate` filtered to this paper's `rs:LookCollab*`, `mod_appreciated_scale`.
**Wide-mode pull-down extras:** `mod_intellid_graph` (this paper's contributors), `mod_ai_usage_heatmap` (this paper).

**Page blocks:**
1. **Header chrome.**
2. **Workspace masthead (140px tall, `--surface` bg, 1px bottom `--paper3`):**
   - Title editable inline (Spectral 300, 36pt; on focus shows 1px `--river` underline + mono helper "title").
   - Workflow state chip + transition CTA (e.g., from `draft` → `Submit for review` button `--river` filled). Disabled chips show tooltip explaining the gate.
   - Stats row (mono 11pt): version v3 · authors 2 · sources 14 · datasets 3 · ai_sessions 7 · `rs:*` 4 · transparency_complete (sage check or coral X) · ai_log_complete (sage check or coral X).
3. **Tab strip (sticky, 48px tall, `--paper2` bg):**
   Tabs:
   - Manuscript
   - Metadata
   - Sources (Transparency)
   - Datasets
   - AI Usage
   - Un Scientific
   - Open Reports
   - Versions
   - Attribution
   - `rs:*` Tags
   - Open Collaboration
   - Sealed audit (admin-only — disabled chip for authors; tooltip "governance unlock")
4. **Tab content area (centered 880px):**
   - **Manuscript:** rich Markdown editor (Spectral 16pt). Left gutter shows section anchors. Right margin shows live `rs:*` tag suggestions and AI-usage flags inline. Toolbar mono 11pt UPPERCASE: `H1 · H2 · H3 · BOLD · ITALIC · CODE · QUOTE · TABLE · FOOTNOTE · TAG`.
   - **Metadata:** form (Spectral 16pt fields, mono labels): title · alias · introtext (abstract) · authors (multi-select with IntelliD search) · primary ORCID · discipline · category · keywords · DOI · authorship_mode (segmented: human / AI / hybrid).
   - **Sources (Transparency Block):** repeatable rows — citation title · source_type select (peer / preprint / dataset / web / other) · used (toggle) · reason if unused (textarea). Bottom: "Mark transparency complete" toggle. Color encode: rows with `used=false` show `--amber-l` left edge; `--coral-l` if no reason given.
   - **Datasets:** repeatable cards — title · link · type · license select · availability select · file upload zone (mono dashed border `--paper3`).
   - **AI Usage:** ai_used toggle at top. If on → tools repeatable (vendor select · model · version · mode segmented Generated/Assisted/None · endpoint · params JSON editor). Then interactions repeatable (prompt_hash mono · output_type · contribution_scope · oversight chip · risk_flags multi-chip · redactions textarea). Then ai_relationship_statement (Spectral textarea). Then ai_display_level segmented Full/Summary/Hidden. Bottom: "Mark AI log complete" toggle.
   - **Un Scientific:** unsci_active toggle (mono helper: "this paper carries a known issue requiring caveat — author-applied"). Repeatable entries — scope select · anchor · reason textarea · risk_level chip (low/medium/high) · requested_action select.
   - **Open Reports:** or_enabled toggle. or_mode segmented (open_identities · open_reports · summary_only · editorial_only). When reviews come in, list shown read-only; author can post responses inline.
   - **Versions:** vertical list — version label, file, AI-authorship boolean, generation notes. Add-version CTA mono outline button.
   - **Attribution:** repeatable contributors — name (or IntelliD) · role · contribution_type · AI/human radio · ai_tool_used (mono).
   - **`rs:*` Tags:** repeatable rst_tags — tag_type select (controlled vocab from SSOT §5.4) · tag_notes textarea · tag_scope select · tag_visibility segmented · resolved toggle · resolution_notes textarea. The tag_type select is searchable mono dropdown that shows the full controlled vocabulary grouped by category (LookCollab · NotTopic · Stalled · Other).
   - **Open Collaboration:** collab_open toggle · collab_type · collab_interest_level · collab_seek textarea · collab_notes textarea.
5. **Right rail with modules.**
6. **Action footer (sticky bottom, 64px tall, `--surface` bg, 1px top `--paper3`):**
   - Mono 11pt save state: "saved" (sage) or "unsaved" (amber) or "error" (coral).
   - Buttons: `Save draft` (outline) · `Validate completeness` (outline) · `Submit for review` (`--river` filled, gated until validation passes).
   - Gate criteria (mono helper line on hover): "transparency_complete + ai_log_complete + at least 1 source + manuscript ≥ 1000 words + ORCID linked + authorship_mode set".
7. **Footer chrome.**

**Tags / badges rendered:** every paper-level badge plus per-section completion chips.
**States:**
- loading → tab area skeleton.
- save-success → toast mono "saved · v3 retained".
- save-error → toast coral "save failed — your draft is not lost; offline copy retained in localStorage".
- locked (paper in `under_review`) → all editable fields read-only with mono banner: "This manuscript is locked while under review. Open a revision to edit."
**Sample data (max 2 sentences):** Workspace shows a paper at `revisions_requested` with the editor's letter visible in a `--violet-l` callout above the tab strip; a `Resubmit revision` button is the primary CTA. Authors get a 14-day window indicator (mono — but rendered as a relative bar `▣▣▣▢▢▢▢` instead of a literal date, per temporal-blindness).
**Interactions:**
- Tab switch persists draft state.
- Inline AI-usage flagger: writing prose with AI tools open → chrome shows mono indicator "AI-assist active — log this session?" with a one-click "Log session" button that opens the AI Usage tab pre-filled.
- "Validate completeness" runs the gate criteria server-side and renders any missing items as `--coral` chips with anchor links.
**Observer projection note:** Author sees their own HUMINT view. Editorial overlays appear when an editor opens the same workspace: read-only banner `EDITORIAL VIEW` mono UPPERCASE, plus extra "Reviewer-side notes" tab.
**ACL governance unlock note:** Sealed-audit tab disabled for author; only `eaiou_Admin` after governance unlock.

---

### Page: Submit — Wizard (6 steps)
**Role / ACL:** `eaiou_Author`.
**URL:** `/submit` (steps 1–6 are tabs within this URL with hash anchors).
**Joomla source:** com_eaiou submit controller backed by article create + plg_content_* metadata writers.
**Layout shell:** fixed-default, no right rail (focus mode).

**Global wizard chrome:**
- **Header chrome (slim — 56px, no nav).**
- **Stepper strip (sticky, 72px tall, `--surface` bg, 1px bottom `--paper3`):**
  - Six steps as horizontal pills with mono 11pt labels and a connecting hairline progress bar in `--river`:
    1. METADATA · 2. BUNDLE · 3. AI USAGE · 4. TRIAGE · 5. DECLARATIONS · 6. CONFIRM
  - Active step: `--river-ll` fill, `--river` border. Completed: `--sage` filled. Pending: `--paper3` outline.
  - Step click navigation only allowed for visited steps; future steps show tooltip "complete previous step first".
- **Save indicator (top-right of stepper):** mono 11pt — "auto-saved · v0.draft" (sage) / "saving…" / "offline — local copy".
- **Action footer (sticky bottom, 80px tall, `--surface` bg, 1px top `--paper3`):**
  - Left: `← Back to my papers` mono outline.
  - Right: `Save draft` outline · `Continue →` `--river` filled. Final step shows `Seal & Submit` instead.

---

#### Step 1 — Metadata
**Block content:**
1. Section header (Spectral 300 32pt): "Tell the river who is speaking."
2. Sub (Spectral italic 16pt, `--ink2`): "Authorship, identity, scope. The discipline tags are searchable. The IntelliD is yours."
3. Form fields (mono labels 11pt UPPERCASE; inputs Spectral 16pt; 1px `--paper3` border; radius 3px; vertical stack with 24px gap):
   - **Title** — text input, max 200ch.
   - **Alias / URL slug** — auto-derived from title; editable mono input.
   - **Abstract (introtext)** — Spectral textarea, 6 rows, max 2000ch with mono char counter.
   - **Authors** — multi-select pill input. Type IntelliD or ORCID; each entry renders as IntelliD pill with ORCID badge if linked. Primary author marker (radio) on one entry.
   - **Authorship mode** — segmented control: Human · AI · Hybrid. Selecting AI or Hybrid shows mono helper: "AI Usage step is now mandatory."
   - **Primary ORCID** — auto-filled from current user; editable.
   - **Discipline (Joomla category)** — select with hierarchy.
   - **Joomla tags (discipline + methodology)** — multi-select; suggestions from controlled vocabulary.
   - **DOI (if pre-registered)** — mono input, optional.
4. Validation: title ≥ 8ch · abstract ≥ 100ch · ≥ 1 author with ORCID · discipline selected.

---

#### Step 2 — Bundle
**Block content:**
1. Header: "Upload the full context." Sub italic: "Manuscript, supplementary materials, calibration data, exploratory notes — used and unused. The river archives the path, not just the destination."
2. **Manuscript upload zone:** dashed 1px `--paper3`, 200px tall, `--surface` bg, mono 13pt centered: "Drop manuscript here · .docx · .pdf · .tex · .md". On drop → file row with mono filename + size + preview link + remove (×).
3. **Supplementary materials repeatable:**
   - Each row: file drop · type select (figure / table / code / data / video / other) · caption Spectral input · license select.
4. **Sources (literature triage) — repeatable rows:**
   - citation_title · source_type select · used toggle · reason_unused textarea (shown only if used=false).
   - "Bulk import from BibTeX" mono outline button (modal).
5. **Datasets repeatable:**
   - title · link or upload · license · availability.
6. **NotTopic preservation banner (`--violet-l` bg, italic Spectral 14pt):** "Anything excluded? Tag it as `rs:NotTopic:*` so it's preserved as searchable un-space — not deleted."
7. Validation: manuscript present · ≥ 1 source · transparency_complete togglable.

---

#### Step 3 — AI Usage
**Block content:**
1. Header: "Log every AI in the room."
2. Sub italic: "Including the ones that didn't make it. AI is a participant — name it, log it, surface it."
3. **ai_used master toggle.** When off, step skipped (warning if authorship_mode = AI/Hybrid).
4. **AI tools repeatable cards:**
   - vendor select (Anthropic · OpenAI · Google · Mistral · open-weight · other) · model · version · mode segmented (Generated / Assisted / None) · endpoint · params JSON.
5. **AI interactions repeatable:**
   - prompt_hash (mono auto-generated) · output_type select · contribution_scope text · oversight chip · risk_flags multi-chip · redactions textarea.
6. **ai_relationship_statement** Spectral textarea — author's narrative on AI's role.
7. **ai_display_level** segmented (Full / Summary / Hidden) — controls public visibility.
8. **Excluded AI outputs (didntmakeit) repeatable:**
   - prompt · response · reason_excluded · redacted toggle. (These will land in `eaiou_didntmakeit` table, indexed but display-gated.)
9. **Mark AI log complete** toggle.
10. **Sample call-out box (`--violet-l`, italic Spectral 14pt):** "Even AI outputs that didn't make it stay in the archive — searchable, gated, never deleted. The penicillin metaphor: one person's discarded petri dish is another's discovery."

---

#### Step 4 — Triage
**Block content:**
1. Header: "Sort the river."
2. Sub italic: "Apply `rs:*` tags. Mark what's NotTopic, what's Stalled, what's Looking for collaboration. Visibility per tag."
3. **Tag composer (full-width 1px `--paper3` panel):**
   - Tag picker (searchable mono dropdown) grouped:
     - LookCollab ▾ (CoAuthor · DataPartner · DomainExpert · Equipment · Funding · Statistician · Coder · Reviewer · Replication)
     - NotTopic ▾ (AnotherField · FutureWork · Tangent · AbandonedHypothesis · Contradiction · NullResult)
     - Stalled ▾ (Literature · Data · Analysis · Writing · Funding · Equipment · Methodology · Collaboration · Ethics · Compute · Reproducibility)
     - Other ▾ (ForLater · OpenQuestion · NullResult · Replication · CrossDomain · Exploratory · Contradiction · UnderReconsideration)
   - On select → tag pill added to applied list with: notes textarea · scope select (whole-paper / section / artifact) · visibility segmented (public / reviewers / editorial / private) · resolved toggle.
4. **Auto-suggest panel (right side, 240px wide):**
   - Mono 11pt header `SUGGESTED FROM YOUR CONTENT`. Lists 3–5 tag suggestions inferred from manuscript text + sources, each with a one-click "apply".
5. **Live cross-link preview:** as tags applied, show how this paper will surface in /discover/ideas, /discover/gaps, /discover/open. Three preview cards.

---

#### Step 5 — Declarations
**Block content:**
1. Header: "Sign your context."
2. Six checkbox lines (Spectral 14pt, mono 11pt rationale below each):
   - [ ] Transparency complete (sources triaged, used/unused stated).
   - [ ] AI log complete (every tool, every session, every excluded output).
   - [ ] No undisclosed conflicts of interest.
   - [ ] Ethics / IRB clearance attached if applicable (link required).
   - [ ] ORCID iDs verified for all authors.
   - [ ] Doctrine acknowledged: temporal blindness, full-context preservation, AI as participant.
3. **Co-author verification panel:** for each non-primary author, show "verification pending" or "verified" chip. Send-verification button per author.
4. **Open Reports preference:** segmented control or_mode (open_identities · open_reports · summary_only · editorial_only). Mono helper per option.
5. **Open Collaboration declaration:** collab_open toggle · type · interest level · seek textarea.

---

#### Step 6 — Confirm
**Block content:**
1. Header: "Seal the submission."
2. Sub italic: "On submit, the timestamp is hashed and capstoned. From this point, your dates leave the discovery surface forever."
3. **Summary panel (`--paper2` bg, padding 24px, 1px `--paper3`):**
   - Title · authors · discipline · q_signal preview (computed from completeness signals; mono 13pt with bar).
   - Counts: sources N · datasets M · AI sessions K · `rs:*` tags applied · `rs:NotTopic` excluded items.
   - Completeness checklist (sage check / coral X) for: transparency, AI log, declarations, ORCID, ethics.
4. **Sealing animation panel (right side, 320px):**
   - Mono 11pt UPPERCASE `WHAT HAPPENS WHEN YOU SUBMIT`:
     - 1. SHA256(paper_uuid + sealed_at + content_hash) → submission_hash
     - 2. Hash anchored to Zenodo (capstone DOI returned)
     - 3. Article moves draft → submitted (Joomla workflow transition)
     - 4. Editorial assignment queued
     - 5. Submission date is sealed; never reaches HUMINT view
5. **Final action area:**
   - `Seal & Submit` button — large, full-width, `--river` filled, mono UPPERCASE 14pt. On click → modal "are you sure?" with sealed-state warning.
   - Below: `Review again ←` and `Save draft` outline buttons.

**Sample data (max 2 sentences):** A wizard mid-Step-3 shows two AI tools logged (Claude Sonnet 4.6 — assisted prose polish — low-risk; GPT-4o — generated draft of §3.2 — flagged for numerical review) and one didntmakeit entry ("attempted derivation of EB carrier on rank-5 N/U — abandoned"). The completeness gate at Step 6 shows all six declarations checked, q_signal preview at 0.71, and a single coral X next to ethics (linked to a fix-it CTA).
**Interactions:** auto-save on blur; step navigation; bulk imports; tag composer keyboard nav; submit confirm modal; on success → redirect to /paper/{id}/workspace with mono toast "Sealed and submitted. Capstone DOI: 10.5281/zenodo.XXXXXXX".
**Observer projection note:** HUMINT only.
**ACL governance unlock note:** Sealed timestamps not visible anywhere in the wizard; only the hash is shown post-seal.

---

### Page: Revise upload
**Role / ACL:** `eaiou_Author` (own paper) when state in (`revisions_requested`, `submitted`).
**URL:** `/paper/{id}/revise`
**Joomla source:** com_eaiou revise controller; transitions article state.
**Layout shell:** fixed.
**Modules:** `mod_open_collaborate` filtered to this paper.

**Page blocks:**
1. **Header chrome.**
2. **Banner (above masthead, `--violet-l` bg, padding 16px, italic Spectral 16pt, 1px `--violet` left border):**
   - Editor letter quoted in italic with mono attribution `— EDITOR INT-3F12`.
   - Required revisions list (rendered as numbered Spectral list).
   - Reviewer comments (collapsible, 1 per reviewer, mono `INT-####` byline).
3. **Two-column layout (centered 1080px):**
   - **Left col (640px):** revision diff editor — markdown editor with diff highlighting against the previous submission. Toolbar mono 11pt UPPERCASE: `H1 · H2 · BOLD · ITALIC · CODE · QUOTE · TABLE · TAG`. Each accepted change marks a green stripe in the gutter; each unaddressed reviewer comment marks an amber stripe.
   - **Right col (400px):** "Reviewer comments to address" — checklist of reviewer requests, each with anchor-to-section button. Below: "Author response" textarea (Spectral 16pt, 12 rows) tied to the per-review-id author_response field.
4. **AI Usage delta panel:** mono 11pt label `AI USAGE FOR REVISION`. Shows new tools / sessions / didntmakeit added since last version. Same form structure as Step 3 of the wizard.
5. **Action footer (sticky):**
   - `Save revision draft` outline · `Validate revision completeness` outline · `Submit revision (v+1)` `--river` filled.
   - Mono helper: "Submitting writes a new sealed-time and increments submission_version."

**Tags / badges rendered:** workflow chip `revisions_requested` highlighted; AI-Logged on any updated tools.
**States:**
- loading skeleton.
- error coral.
- locked (state changed to `decision_pending` while you were editing) → mono banner "Revisions period closed. Your draft is preserved in workspace."
**Sample data (max 2 sentences):** Editor letter in callout reads "We invite revisions. Reviewer 2 raises a methodology concern in §3.2 that we ask you to address." Revision draft shows 3 reviewer comments addressed (sage), 1 outstanding (amber); author response panel half-filled.
**Interactions:** anchor-to-section button scrolls editor; save-on-blur; submit triggers seal modal as in Step 6 of wizard.
**Observer projection note:** HUMINT default; reviewer-side comment IntelliDs visible only if `or_mode` permits.

---

## End of `UXPILOT_02_author.md`

Next file: `UXPILOT_03_reviewer.md` — reviewer queue, paper view, rubric console, ASK↔GOBACK session.
