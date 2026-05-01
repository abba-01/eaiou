# UXPILOT_01 — public & guest pages

**Tokens, schemas, shells:** see `UXPILOT_00_design_system.md`.
**Philosophical canon:** see `UXPILOT_PROMPT_EAIOU.md`.
**Modules referenced by name:** see `UXPILOT_06_modules.md`.
**Layout shells:** see `UXPILOT_07_layout_shells.md`.

---

### Page: Home / Landing
**Role / ACL:** Public.
**URL:** `/`
**Joomla source:** menu item type "featured articles" filtered by q_signal DESC.
**Layout shell:** both (toggle visible). Default fixed.
**Modules (right rail):** `mod_open_collaborate`, `mod_ai_usage_heatmap`, `mod_trending_ideas`.
**Wide-mode pull-down extras:** `mod_gap_map`, `mod_intellid_graph`, `mod_appreciated_scale`.

**Page blocks (top → bottom):**
1. **Header chrome** — defer to `UXPILOT_07 §Header`. Logo "eaiou" Spectral 300 24pt, primary nav "Papers · Discover · Search · About", search input mono 13pt placeholder "grep tag: rs:", `HUMINT` chip, login/register links.
2. **Hero band (full-width, 280px tall, `--paper` bg, no image):**
   - Centered headline (Spectral 300, 56pt, `--ink`): *Follow the river. Sort by quality, not by clock.*
   - Sub (Spectral 400 italic, 22pt, `--ink2`, max 720px width): *An observer-preserving, full-context peer-review journal. Submission dates are sealed. Discovery is by q_signal.*
   - Right side of hero (320px wide card, `--surface`, 1px `--paper3` border, radius 4px): "river state — today's top q_signal" — single horizontal bar 4px tall in `--river`, scale 0–1, value at 0.847; below the bar in mono 11pt: paper title (Spectral 16pt, link), IntelliD (mono `INT-9F2A`), q chip (sage-l fill).
3. **River band (centered column 720px, fixed-mode; full-width cards in wide-mode):**
   - Section label (mono 11pt UPPERCASE tracking-wide, `--ink3`): `FOLLOWING THE RIVER`.
   - 8–12 paper cards stacked, each card 1px border `--paper3`, radius 4px, padding 16px:
     - Row 1 — left: badges row (AI-Logged, Open Reports, ORCID, Sealed); right: q_signal bar (80px wide, 4px tall, `--river`) + q value mono 12pt.
     - Row 2 — title (Spectral 600, 24pt, `--ink`, link).
     - Row 3 — authors (mono 11pt, `--ink2`): `INT-9F2A · INT-A831 · INT-7C04`.
     - Row 4 — abstract preview (Spectral 16pt, `--ink2`, 3-line clamp, 1.6 line-height).
     - Row 5 — `rs:*` tag chips wrap; section/discipline tag (sans, larger).
     - **No dates anywhere.** No "posted X ago".
4. **Discovery promo strip (3 columns, 200px tall, mono labels):**
   - `/discover/ideas` — line graph icon (16 dots ranked by entropy-novelty), "Emerging ideas from un space".
   - `/discover/gaps` — 5 horizontal bars of varying length (gap density), "Where the river stops".
   - `/discover/open` — 3 dots clustered + 1 outside, "Open collaboration requests".
5. **Footer chrome** — defer to `UXPILOT_07 §Footer`.

**Tags / badges rendered:** AI-Logged, Open Reports, ORCID, Sealed, Transparency; `rs:Replication`, `rs:NullResult`, `rs:LookCollab` chips on cards as applicable.
**States:**
- loading → 6 skeleton cards (paper2 fill, no shimmer; static).
- empty → "the river is rising" placeholder card with 64pt italic Spectral and a 1px hairline river bar at 0.000 — should not normally appear.
- error → `--coral` 1px top stripe, copy in mono 12pt: "river feed unavailable — try /papers".
**Sample data (max 2 sentences):** "Sealed-time effects on peer review participation rates" by `INT-9F2A · INT-A831` · q=0.847 · AI-Logged · Open Reports. "Methodology gaps in cross-domain replication: a NotTopic study" by `INT-7C04` · q=0.812 · Replication · Sealed.
**Interactions:**
- Card hover → 1px `--paper3` border darkens to `--ink3`; q bar grows 1px; cursor pointer.
- Click → paper detail page.
- Right-rail modules collapse/expand via header click.
- Wide-mode toggle in header chrome → reflows to wide; pull-down extras animate in (200ms ease).
**Observer projection note:** HUMINT default. UNKINT view (admin/EIC) replaces IntelliDs with full ORCID, surfaces sealed timestamps inline, adds tensor-coordinate column. Toggle in chrome, requires governance unlock.
**ACL governance unlock note:** Sealed dates not reachable on this page even for admin without explicit governance unlock at `/administrator/.../com_eaiou`.

---

### Page: Papers list
**Role / ACL:** Public.
**URL:** `/papers`
**Joomla source:** Joomla category list view (com_content) filtered, sort overridden to q_signal.
**Layout shell:** both. Default fixed.
**Modules:** `mod_latest_papers`, `mod_ai_usage_heatmap`, `mod_open_collaborate`.
**Wide-mode pull-down extras:** `mod_trending_ideas`, `mod_gap_map`.

**Page blocks:**
1. **Header chrome.**
2. **Page title strip** — Spectral 300, 36pt, `--ink`: "Papers". Sub (mono 11pt UPPERCASE, `--ink3`): `SORTED BY Q_SIGNAL — NEVER BY DATE`.
3. **Filter rail (sticky top, 56px tall, `--paper2` bg, 1px bottom `--paper3`):**
   - Discipline chip group (multi-select): Physics · Cosmology · Computing · Mathematics · Biophysics · Statistics · Cross-Domain.
   - Workflow state chip group: Published (default) · Accepted · Archived.
   - `rs:*` tag dropdown (mono input): "filter by rs: tag".
   - Open-Reports toggle (mono switch).
   - AI-Usage filter: All · AI-Logged · Human-Only · Hybrid.
   - Q-signal min slider (range 0.0–1.0, default 0.0). Mono value indicator.
   - Sort dropdown (locked to "q_signal DESC"; click → tooltip "Sort by date is governance-locked. See doctrine.").
4. **Results list (centered column or grid):**
   - Card list identical to home river-band cards.
   - Pagination at bottom: mono 11pt "page 1 of 47" with prev/next chevrons in `--river`. No page-size selector — fixed at 20.
5. **Footer chrome.**

**Tags / badges rendered:** all paper-level badges + state chips for non-published filter.
**States:**
- loading → 20 skeleton cards.
- empty (filter excludes everything) → mono 14pt "no papers match — your filter is too narrow. Reset filters →".
- error → coral stripe + mono message.
**Sample data:** Filtered to "Physics + AI-Logged + min q 0.7" → 12 results, top one "Quantum decoherence in N/U algebra reductions" q=0.891 · IntelliD INT-3F12 · AI-Logged · Open Reports.
**Interactions:**
- Filter chips toggle. URL query updates without full reload (alpine + fetch).
- Card hover/click identical to home.
- Sort dropdown shows the doctrine tooltip on date-sort attempt.
**Observer projection note:** HUMINT default. UNKINT adds a "submitted" column hidden behind governance unlock.

---

### Page: Paper detail
**Role / ACL:** Public for `state=published` papers; ACL-restricted otherwise.
**URL:** `/paper/{id}/{slug}`
**Joomla source:** com_content article view + custom field rendering + plg_content_* enrichment.
**Layout shell:** both. Default fixed; wide-mode shows extra rails.
**Modules:** `mod_latest_papers` (titled "More from this q_signal range"), `mod_open_collaborate`.
**Wide-mode pull-down extras:** `mod_ai_usage_heatmap` (paper-scoped, not global), `mod_intellid_graph` (this paper's contributor breakdown), `mod_appreciated_scale`.

**Page blocks:**
1. **Header chrome.**
2. **Paper masthead (full-width band, `--paper` bg, 1px bottom `--paper3`):**
   - Title (Spectral 300, 44pt, `--ink`, max 880px): *Sealed-time effects on peer review participation rates*.
   - Authors row: each author rendered as IntelliD pill (mono 13pt, `--surface` bg, 1px `--paper3`, radius 3px); ORCID badge inline if linked. Hover IntelliD → tooltip with author display name + affiliation if author chose `or_mode = open_identities`.
   - Badge row: AI-Logged, Open Reports, ORCID, Sealed, Transparency, AI-Hybrid.
   - q_signal display: horizontal bar 200px wide, 6px tall in `--river`, value 0.847; mono 13pt label "q=0.847" on right.
   - Discipline tags + `rs:*` tag pills wrap below.
   - **No submission/publication date in masthead.** Capstone DOI rendered if present (mono 11pt link, `--river`).
3. **Action rail (sticky right, 240px wide on fixed; absorbed into right rail in wide):**
   - Buttons (vertical stack, mono 12pt UPPERCASE):
     - PRIMARY: `Cite` (`--river` filled, white text). Opens modal with BibTeX, RIS, plain.
     - `Download bundle` (outline, 1px `--river`). Opens manifest of full-context bundle.
     - `Open Reports →` (outline, jumps to reviews section).
     - `AI Usage Log →` (outline, jumps to AI section).
     - `Didn't Make It →` (outline, gated — admin only).
     - `Cross-domain links` (outline, jumps to /dataset/link).
4. **Tab strip (sticky below masthead, 48px tall, `--paper2` bg):**
   Tabs: Abstract · Manuscript · Sources · Datasets · Methods · AI Usage · Open Reports · Versions · Attribution · NotTopic Index.
   Active tab: 2px bottom `--river`. Inactive: `--ink3`. Click → smooth scroll, no reload.
5. **Content stream (centered 720px on fixed, 880px on wide):**
   - **Abstract:** Spectral 18pt 1.65 line-height, drop-cap in `--river` for first character.
   - **Manuscript:** Spectral 16pt body, embedded figures (full-width inset), pull-quotes in italic Spectral 22pt with 4px `--river` left border, code blocks in JetBrains Mono with `--paper2` bg.
   - **Sources (Transparency Block):** table — citation title, type chip (peer-reviewed / preprint / dataset / web / other), used (sage check or coral X), reason if unused (mono italic).
   - **Datasets:** card grid — title, link, license chip, availability chip, embed preview if compatible.
   - **Methods:** Spectral 16pt prose; method tags inline as mono pills.
   - **AI Usage:** ai_relationship_statement at top in `--violet-l` callout; below that a table — vendor, model, version, mode (Generated/Assisted/None), endpoint, contribution_scope (chip), risk_flags (chips), redactions (mono link "view"). At bottom: link to full session log if `ai_display_level = full`.
   - **Open Reports:** if `or_enabled` — accordion list, each review entry: reviewer IntelliD or display-name (per consent), recommendation chip (Accept / Minor / Major / Reject), per-rubric scores as mini-bars (5-point scale, sage→coral gradient), narrative text in Spectral 16pt, author response thread below in violet-l callout.
   - **Versions:** vertical timeline — version label, file path mono link, AI-authorship boolean (violet badge), generation notes Spectral 14pt italic. **No dates.**
   - **Attribution:** card grid — contributor IntelliD, role description, contribution type, AI/human badge, ai_tool_used (mono link). 
   - **NotTopic Index:** banner explaining "what is not on topic here is someone else's topic"; filtered list of `rs:NotTopic:*` artifacts from this paper, each linked to /discover/ideas.
6. **Right rail (modules listed above).**
7. **Footer chrome.**

**Tags / badges rendered:** all listed plus per-section state chips.
**States:**
- loading → masthead skeleton + tab strip placeholder.
- error (404) → "this paper is sealed or never existed" mono message + link to /papers.
- locked (paper not in published state for current user) → masthead only + lock icon + mono message "this paper is in `under_review`. Login as reviewer or wait for publication."
**Sample data:** Title above; abstract begins "We test whether sealing submission dates changes the rate at which reviewers accept invitations…". AI Usage shows Claude 4.5 (assisted, prose-polish, low-risk) and GPT-4o (generated, statistical-narrative, contribution_scope: section §3.2, risk_flags: numerical).
**Interactions:**
- Tab clicks scroll smoothly; URL hash updates.
- Citation modal: copy-to-clipboard buttons, mono confirmation toast.
- Bundle download: opens manifest panel, then triggers archive download.
- Author IntelliD hover: tooltip shows display name only if the author opted in (`or_mode` covers reviewer identity, but author-side ORCID display has its own toggle).
- AI Usage row click: opens redaction-aware session log modal.
**Observer projection note:** HUMINT default. UNKINT view (governance unlock required) adds: sealed timestamps inline, full ORCID, tensor coords, and the unredacted didntmakeit corpus link.
**ACL governance unlock note:** "Didn't Make It" tab disabled for everyone except eaiou_EIC and eaiou_Admin and only after governance unlock click in admin.

---

### Page: Discover — Ideas (un space)
**Role / ACL:** Public.
**URL:** `/discover/ideas`
**Joomla source:** com_eaiou view "ideas" → /api/v1/eaiou/ideas/discover ranked by entropy-novelty.
**Layout shell:** both. Default wide.
**Modules:** `mod_trending_ideas`, `mod_open_collaborate`, `mod_gap_map`.
**Wide-mode pull-down extras:** `mod_intellid_graph`, `mod_ai_usage_heatmap`.

**Page blocks:**
1. **Header chrome.**
2. **Page band:** Spectral 300, 36pt: "Ideas in un space". Sub Spectral italic 18pt: "What is not on topic here is someone else's topic." Mono 11pt label `RANKED BY ENTROPY-NOVELTY`.
3. **Filter rail:** discipline multi-select; `rs:NotTopic:*` sub-tag filter (Tangent · AbandonedHypothesis · Contradiction · NullResult · AnotherField · FutureWork); novelty range slider; "include only resolved" toggle.
4. **Idea list (full-width cards, larger gutters than papers):**
   - Each card 1px border `--paper3`, radius 4px, padding 24px:
     - Row 1: parent paper title (Spectral 600, 18pt) + paper link (mono `--river`).
     - Row 2: idea title or excerpt (Spectral 400, 22pt italic) — this is the un-space artifact.
     - Row 3: NotTopic sub-tag chip + entropy-novelty score (mono 13pt, accompanied by 80px horizontal bar `--violet`).
     - Row 4: author IntelliD list, contributor count, "linked from N papers" (mono 11pt).
     - Row 5: cross-domain hint — chip showing the dominant cross-domain tag if any (e.g., `rs:CrossDomain`).
   - Pagination same as papers list.
5. **Footer chrome.**

**Tags / badges rendered:** `rs:NotTopic:*`, `rs:CrossDomain`, `rs:NullResult`, AI-Logged.
**States:** loading skeletons, empty mono message "un space is empty for these filters", error coral stripe.
**Sample data:** "Sphinx-shaped ridge alignment in JPL Twin Peaks catalog imagery — abandoned in [parent paper title]. Entropy-novelty 0.73, cross-domain tag rs:NotTopic:AnotherField."
**Interactions:** chip filters update URL; click idea card → opens un-space artifact modal (preview text + parent paper context + "claim for follow-up paper" CTA → /submit pre-filled).
**Observer projection note:** HUMINT default. UNKINT adds didntmakeit-link column.

---

### Page: Discover — Open Collaboration
**Role / ACL:** Public.
**URL:** `/discover/open`
**Joomla source:** com_eaiou view "open" → /api/v1/eaiou/research/open returning all `rs:LookCollab*` and `collab_open=true` papers.
**Layout shell:** both. Default fixed.
**Modules:** `mod_open_collaborate`, `mod_trending_ideas`, `mod_ai_usage_heatmap`.

**Page blocks:**
1. **Header chrome.**
2. **Page band:** "Open Collaboration" Spectral 300 36pt. Sub mono "BIDIRECTIONAL: HUMAN ↔ AI ↔ INSTITUTION".
3. **Filter rail:** Collaboration type chip group (Co-Author · Data Partner · Domain Expert · Equipment · Funding · Statistician · Coder · Reviewer · Replication); interest level chip (High · Medium · Low); discipline multi-select.
4. **Two-column layout (fixed mode collapses to one):**
   - Left col: open requests list, each card with parent paper title + LookCollab sub-tag chip + collab_seek text in italic Spectral + interest level pill + IntelliD + "connect →" button (mono UPPERCASE on `--river` outline).
   - Right col: same as right rail with extra "How to connect" mono callout linking to /research/seek for posting your own.
5. **Footer.**

**Tags / badges rendered:** `rs:LookCollab:*`, AI-Logged, ORCID.
**States:** standard.
**Sample data:** "Need a Statistician for replication of MN-26-1117-P (Hubble tension scoring)." IntelliD INT-9F2A · interest=high · `rs:LookCollab:Statistician` · ORCID · Sealed.
**Interactions:** "connect →" opens secure messaging modal (TAGIT-aware, see `UXPILOT_PROMPT_EAIOU.md`); requires login.
**Observer projection note:** HUMINT only.

---

### Page: Discover — Gaps (Gap Map)
**Role / ACL:** Public.
**URL:** `/discover/gaps`
**Joomla source:** com_eaiou view "gaps" → /api/v1/eaiou/gap/map aggregating `rs:Stalled:*` density.
**Layout shell:** wide-default (the chart needs space).
**Modules:** `mod_gap_map` (full-bleed, not in rail), `mod_trending_ideas`, `mod_open_collaborate`.

**Page blocks:**
1. **Header chrome.**
2. **Page band:** "Gap Map" Spectral 300 36pt. Sub italic Spectral 18pt: "Where the river stops."
3. **Main viz (centered, max 1200px wide, 480px tall):**
   - Heatmap grid: rows = disciplines, columns = stall types (Literature · Data · Analysis · Writing · Funding · Equipment · Methodology · Collaboration · Ethics · Compute · Reproducibility).
   - Each cell shows stall density: 0 = `--paper2`, increasing through `--amber-l` → `--amber` → `--coral`. Cell label mono 11pt count.
   - Right axis: `--ink3` mono labels with discipline names.
   - Top axis: stall types in mono uppercase, rotated 30°.
4. **Drill-down panel (below the heatmap, 1px top border):**
   - Click a cell → panel slides up with the list of stalled papers from that intersection. Cards same as `mod_open_collaborate` but with "what's blocking" callout in `--coral-l`.
5. **Aggregate stats strip (mono 13pt, `--paper2` bg, 64px tall):**
   - Total stalled artifacts · Most common stall type · Most stalled discipline · Resolution rate (last cycle).
6. **Footer.**

**Tags / badges rendered:** `rs:Stalled:*`, `rs:LookCollab:*` (when stall pairs with LookCollab).
**States:** loading → heatmap skeleton with `--paper2` cells; empty → "the river isn't stopping anywhere right now"; error → coral stripe.
**Sample data:** Cosmology × Methodology cell shows 23 stalls; click → list includes "Cannot define a closed-form for the EB carrier on N/U pairs above rank 4" stalled by IntelliD INT-A831, with `rs:LookCollab:DomainExpert`.
**Interactions:** cell click → drill panel slides up; cell hover → tooltip with mono count + density rank; clicking aggregate stats links to filtered /papers list.
**Observer projection note:** HUMINT only.

---

### Page: Discover — Trends
**Role / ACL:** Public.
**URL:** `/discover/trends`
**Joomla source:** com_eaiou view "trends" → /api/v1/eaiou/trend/insight aggregating un-space search queries + open declarations.
**Layout shell:** both. Default wide.
**Modules:** `mod_trending_ideas` (full-bleed), `mod_gap_map`, `mod_ai_usage_heatmap`.

**Page blocks:**
1. **Header chrome.**
2. **Page band:** "Trends" Spectral 300 36pt. Sub italic 18pt: "What the field is asking that hasn't been answered."
3. **Trend list (numbered, 1–25, full-width entries):**
   - Each row 80px tall, 1px bottom `--paper3`:
     - Rank (mono 700, 36pt, `--ink3`, fixed-width 80px).
     - Trend phrase (Spectral 22pt, `--ink`, link).
     - Mini-spark (60px wide, 12px tall, line in `--violet` tracking entropy-novelty over recent cycles — no x-axis labels).
     - Discipline chip + entropy-novelty mono value.
     - Action chip: "ask →" (open /submit pre-filled) or "find collaborator →" (jump to /discover/open with filter applied).
4. **Subscribe band (footer-adjacent, `--paper2` bg):**
   - Mono 13pt: "subscribe to a trend" → email input (mono) + discipline multi-select + "feed me" button (`--river` outline).
5. **Footer.**

**Tags / badges rendered:** discipline tags, `rs:Exploratory`, `rs:OpenQuestion`.
**States:** loading skeletons; empty "no trends — the field is asleep"; error standard.
**Sample data:** "1. Why does sealed-time peer review change reviewer participation?" entropy-novelty 0.91, cosmology+social-sci cross.
**Interactions:** subscribe form requires login; "ask" pre-fills /submit metadata stage.
**Observer projection note:** HUMINT only.

---

### Page: Search
**Role / ACL:** Public.
**URL:** `/search?q=`
**Joomla source:** Smart Search override + com_eaiou unified search across articles, didntmakeit (gated), Joomla Tags, NotTopic index.
**Layout shell:** fixed-default.
**Modules:** `mod_trending_ideas`, `mod_open_collaborate`.

**Page blocks:**
1. **Header chrome.**
2. **Search bar (sticky top, 80px tall, `--surface` bg, 1px bottom `--paper3`):**
   - Large mono input 18pt, placeholder `grep tag: rs:NotTopic:AnotherField OR title: "hubble"`.
   - Filter chips below: Type (Paper · Idea · Tag · Author IntelliD · Dataset) · Discipline · `rs:*` · Open-Reports.
   - Result count + sort selector (q_signal · entropy-novelty · best-match).
3. **Results list (centered 720px, fixed mode):**
   - Each result type renders differently:
     - **Paper:** standard paper card.
     - **Idea (un-space):** smaller card, italic title, NotTopic sub-tag chip, parent-paper link.
     - **Tag landing:** wide row with mono tag name, count of papers, link to tag page.
     - **Author IntelliD:** mono pill + paper count + dominant disciplines.
     - **Dataset:** card with title, license, availability, embed preview.
   - Mixed result types interleave by best-match.
4. **Footer.**

**Tags / badges rendered:** all standard plus highlighted match tokens in mono `--river`.
**States:**
- empty query → recent + popular searches list (mono).
- empty results → "river found no current — try removing a filter".
- loading → 5 skeletons.
- error → coral stripe with mono message.
**Sample data:** Query `tag:rs:Stalled:Methodology AND discipline:cosmology` → 23 papers, top: "EB carrier on N/U pairs — methodology gap" by INT-A831.
**Interactions:** typing debounce 200ms; chip filters update URL; result-type icons in mono on left of each result; keyboard arrow navigation between results.
**Observer projection note:** HUMINT default. UNKINT exposes didntmakeit search results (admin/EIC only) marked with violet "didntmakeit" chip.

---

### Page: Tag landing
**Role / ACL:** Public.
**URL:** `/tag/{tag-name}` (e.g., `/tag/rs:LookCollab:Statistician`)
**Joomla source:** com_tags view + plg_content_researchtags context enrichment.
**Layout shell:** fixed.
**Modules:** `mod_open_collaborate`, `mod_trending_ideas`.

**Page blocks:**
1. **Header chrome.**
2. **Tag masthead (`--paper` bg, 200px tall):**
   - Tag pill rendered large: mono 36pt, "rs:" prefix dimmed `--ink3`, suffix full ink.
   - Description (Spectral italic 18pt): "Need statistical expertise. The author is asking for a partner to take this forward."
   - Stats row (mono 13pt): paper count · resolved count · dominant disciplines · gap-map percentile.
3. **Sub-tag siblings strip:**
   - Other LookCollab tags shown as chips (CoAuthor · DataPartner · DomainExpert · Equipment · Funding · Statistician (current, filled) · Coder · Reviewer · Replication).
4. **Paper list (river-band cards) tagged with this tag.**
5. **Footer.**

**Tags / badges rendered:** the focal tag rendered prominently; sibling tags as inactive chips.
**States:** standard.
**Sample data:** rs:LookCollab:Statistician → 12 papers, 5 resolved.
**Interactions:** sibling chip click → navigate to that tag landing.
**Observer projection note:** HUMINT only.

---

### Page: Auth — Login
**Role / ACL:** Public.
**URL:** `/login`
**Joomla source:** com_users login view.
**Layout shell:** fixed, no sidebars.

**Page blocks:**
1. **Header chrome (slim — 48px, no nav).**
2. **Centered card (480px wide, `--surface` bg, 1px `--paper3`, radius 8px, padding 32px):**
   - Title (Spectral 300, 28pt): "Sign in".
   - Sub (Spectral italic 14pt, `--ink2`): "Your IntelliD persists. Your sessions don't."
   - Form fields (mono labels 11pt UPPERCASE, Spectral 16pt inputs, 1px `--paper3` border, radius 3px):
     - Username or ORCID iD.
     - Password (with show/hide eye in mono).
     - "Remember IntelliD on this device" checkbox.
   - Primary button (full-width, `--river` filled, white text, mono UPPERCASE 12pt): "Sign in".
   - Secondary link row (mono 11pt): "Sign in with ORCID" (orcid green outline) · "forgot password" · "register".
3. **Doctrine sidebar callout (`--paper2` bg, italic Spectral 14pt, 4px left `--river` border):** "Submission dates are sealed. Discovery is by q_signal. The river does not care about the clock."
4. **Footer chrome (slim).**

**Tags / badges rendered:** none.
**States:**
- loading → button text → spinner mono dots.
- error → form field 1px `--coral` border + mono 11pt `--coral` message inline.
- success → redirect to /dashboard or original target.
- locked (after N failures) → mono 11pt warning, link to /forgot-password.
**Sample data:** username: `intelliD-9F2A` (or ORCID).
**Interactions:** submit on enter; tab order; show/hide password.
**Observer projection note:** N/A (pre-auth).

---

### Page: Auth — Register
**Role / ACL:** Public.
**URL:** `/register`
**Joomla source:** com_users registration + plg_system_orcid_link.
**Layout shell:** fixed, no sidebars.

**Page blocks:**
1. **Slim header.**
2. **Centered card (560px wide):**
   - Title "Receive an IntelliD".
   - Sub italic: "An IntelliD is an opaque coordinate. It persists. It reveals nothing."
   - Step indicator (mono): 1 of 3 — Account · 2 — ORCID · 3 — Doctrine ack.
   - **Step 1 — Account:**
     - Display handle (Spectral): defaults to suggested IntelliD (e.g., `INT-9F2A`); user can edit only if they reject the system-suggested one (mono note: "this is not your name. It is your coordinate.").
     - Email · Password · Confirm password.
     - Primary button "Continue".
   - **Step 2 — ORCID:**
     - "Link ORCID" button (orcid green); skippable but warned.
     - On success → ORCID iD displayed mono, badge ORCID rendered.
   - **Step 3 — Doctrine acknowledgement:**
     - Three checkbox lines (Spectral 14pt) referencing the SAID guardrails: temporal blindness, AI-as-collaborator, full-context preservation.
     - Primary button "Receive IntelliD".
3. **Doctrine sidebar callout (same as login).**
4. **Footer.**

**Tags / badges rendered:** ORCID badge appears post-link.
**States:** standard form states.
**Sample data:** Suggested IntelliD `INT-9F2A`, ORCID `0009-0006-5944-1742` linked.
**Interactions:** step navigation; ORCID popup window; final button shows "Welcome — your IntelliD is INT-9F2A" toast then redirects to /dashboard.
**Observer projection note:** N/A.

---

### Page: Auth — Forgot password
**Role / ACL:** Public. URL `/forgot-password`. Slim shell. Single card with email input, primary button "Send reset link", success state inline mono message. Doctrine callout retained.

### Page: Auth — Reset password
**Role / ACL:** Public. URL `/reset-password?token=`. Slim shell. Card with new password + confirm; primary button "Reset and sign in"; auto-login on success.

---

### Page: 404 Not Found
**Role / ACL:** Public.
**URL:** any unmatched.
**Layout shell:** fixed, no sidebars.

**Page blocks:**
1. **Slim header.**
2. **Centered band (max 720px):**
   - Mono 11pt UPPERCASE: `404 — RIVER DIVERTED`.
   - Spectral 300 56pt: "This path doesn't reach the river."
   - Spectral italic 18pt: "The current may have moved. The artifact may be sealed. The address may be a typo."
   - Three CTAs (mono outline buttons): "Go to papers" · "Search" · "Discover ideas".
3. **Footer.**

**States:** static.
**Observer projection note:** HUMINT only.

---

### Page: About
**Role / ACL:** Public.
**URL:** `/about`
**Layout shell:** fixed.
**Modules:** none (or `mod_latest_papers` in wide).

**Page blocks:**
1. **Header chrome.**
2. **Two-column band:**
   - Left col (max 560px): Spectral 300 36pt "About eaiou". Body Spectral 18pt 1.65 line-height. Drop-cap. Three sections: "Why sealed time", "Why full context", "Why IntelliDs". Each with Spectral 600 22pt subhead.
   - Right col (sidebar 280px): mono fact list — "founded · governance · doctrine · open-source · ORCID".
3. **Doctrine link strip** — mono UPPERCASE band, links to /doctrine and /privacy and /api.
4. **Footer.**

**Sample data (max 2 sentences):** "Submission dates are sealed because timestamp + domain + institution = identifiable. eaiou prevents the third leg of that tripod from reaching the discovery surface."
**Observer projection note:** HUMINT only.

---

### Page: Doctrine
**Role / ACL:** Public.
**URL:** `/doctrine`
**Layout shell:** fixed.

**Page blocks:**
1. **Header.**
2. **Title band:** Spectral 300, 44pt: "Doctrine". Sub italic: "Six principles. Loaded into every page."
3. **Six numbered sections (Spectral 600, 24pt for headings; body Spectral 18pt 1.65):**
   - 0.1 Sort by quality (the river).
   - 0.2 Temporal blindness.
   - 0.3 AI as participant.
   - 0.4 Full-context preservation.
   - 0.5 Plugin-per-feature debuggability.
   - 0.6 OMMP Layer 5 module.
4. **Footer.**

**Tags / badges rendered:** none.
**Sample data:** Each principle has 2-sentence pull-quote in italic Spectral 22pt with `--river` left border. (Source for each pull-quote: `/repos/eaiou/SSOT.md` §0.1–0.6.)
**Observer projection note:** HUMINT only.

---

## End of `UXPILOT_01_public.md`

Next file: `UXPILOT_02_author.md` — author surfaces (submit wizard, my-papers, workspace, revise).
