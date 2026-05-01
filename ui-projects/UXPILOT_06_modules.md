# UXPILOT_06 — sidebar & dashboard modules

**Tokens, schemas, shells:** see `UXPILOT_00_design_system.md`.
**Module shell schema:** `UXPILOT_00 §7`.

Two tiers:
- **Canonical** (5) — defined in `/repos/eaiou/SSOT.md §3.2`: `mod_reviewer_queue`, `mod_editor_dashboard`, `mod_latest_papers`, `mod_open_collaborate`, `mod_ai_usage_heatmap`.
- **Design-system-derived** (4) — referenced across page mockups in `/repos/eaiou/ui-projects/eaiou_ds_*.html`, not yet promoted to SSOT canon: `mod_gap_map`, `mod_trending_ideas`, `mod_intellid_graph`, `mod_appreciated_scale`. Flagged for SSOT promotion review.

Every module renders inside the card shell from `UXPILOT_00 §7` and obeys these rules:
- Header bar (`--paper2` bg) carries the module name in mono UPPERCASE.
- Body padding 16px.
- Footer link optional ("count · view all →" mono 10pt `--ink3`).
- Header click toggles collapse; collapse state persists in localStorage per `(user, module, page)`.
- All modules support both fixed-mode width (320px) and wide-mode width (360px). Layouts inside should reflow gracefully.

---

## CANONICAL MODULES

---

### `mod_reviewer_queue`
**ACL / context:** `eaiou_Reviewer`+ only. Shown on home, /papers, /reviewer/queue, /reviewer/paper/{id}, /reviewer/paper/{id}/review (right rail or pull-down).
**Joomla position bindings:** sidebar-right (default), sidebar-extra (wide pull-down).
**Data source:** `eaiou_review_logs` joined `eaiou_papers`, filtered to `current_user_id`.

**Header label:** `MY REVIEW QUEUE`.
**Body (per ACL):**
- For reviewer with active assignments: stack of up to 5 cards, each 64px tall:
  - Row 1: paper title (Spectral 14pt, link, 1-line clamp).
  - Row 2: relative-window bar (`▣▣▣▢▢▢▢` mono, 6px tall) + status chip (Pending / Accepted / In progress / Submitted) + recommendation chip if started.
- Below the stack: footer link mono 10pt: "N active · view queue →".

**Empty state:** mono 11pt centered: "no active assignments".
**Loading:** 3 skeleton rows in `--paper2`.
**Error:** mono 11pt `--coral`: "queue unavailable".

**Interactions:**
- Card hover → 1px border darkens; cursor pointer.
- Card click → /reviewer/paper/{id}.
- Footer "view queue" → /reviewer/queue.

**Color encoding:** relative-window bar — sage segment if early, amber if mid, coral if late. Bar segments not animated.
**Observer projection note:** HUMINT only (reviewer's own context).

---

### `mod_editor_dashboard`
**ACL / context:** `eaiou_Editor`+. Shown on /editorial/papers (full version takes over the rail) and admin dashboard.
**Joomla position bindings:** sidebar-right (compact), content-top (full).
**Data source:** aggregate query across `eaiou_papers`, `eaiou_review_logs`, `eaiou_quality_signals`.

**Header label:** `EDITORIAL KPIs · CYCLE q4`.
**Body (compact mode):**
- 4 stacked stat lines (mono 13pt + mini bar):
  - Under review · count + 60-px sparkline `--river`.
  - Decision pending · count + sparkline `--violet`.
  - Overdue (relative) · count + sparkline `--coral`.
  - Median TTFD (relative bar `▣▣▣▢▢▢▢`).
- Footer link: "open dashboard →" → /editorial/papers.

**Body (full mode — used only on dashboard pages):**
- 6 cards in a 3×2 grid (full bleed). Same 6 cards as `UXPILOT_04 §Editorial Papers` KPI strip.

**Empty state:** "no editorial activity this cycle".
**Loading:** skeleton bars.
**Error:** mono `--coral`.

**Interactions:**
- Card hover → tooltip mono with raw count + cycle-window summary.
- Click on a card → drill to /editorial/papers filtered by that state.

**Color encoding:**
- Sparklines: river / violet / coral / amber per metric category.
- Median TTFD bar: sage if better than cycle target, coral if worse. Cycle target rendered as a hairline tick.
**Observer projection note:** Editor HUMINT (full identity counts). UNKINT toggle adds raw timestamp axes (gov unlock).

---

### `mod_latest_papers`
**ACL / context:** Public. Shown on home, /papers, /paper/{id}, /search.
**Joomla position bindings:** sidebar-right (default), content-bottom (wide-mode pull).
**Data source:** com_content articles in `published` state, sorted q_signal DESC, limit 5.

**Header label:** `RIVER STATE · TOP Q_SIGNAL` (or `MORE FROM THIS Q-RANGE` on paper detail).
**Body:**
- 5 card rows, each 56px tall:
  - Row 1: title (Spectral 14pt, link, 1-line clamp).
  - Row 2: q_signal bar (60px wide, 4px tall, `--river`) + q value mono 11pt + AI-Logged chip + Open Reports chip if applicable.
- Footer: mono 10pt "view all papers →".

**Empty state:** "the river is dry — no published papers" (rare).
**Loading:** 5 skeleton rows.
**Error:** mono `--coral`.

**Interactions:** card click → /paper/{id}; q_signal bar tooltip → "q=0.847 · rank #4".
**Color encoding:** q bar `--river` only.
**Observer projection note:** HUMINT only. **No date column.**

---

### `mod_open_collaborate`
**ACL / context:** Public. Shown on home, /papers, /paper/{id} (this paper), /discover/open, /reviewer/queue (filtered to discipline), /editorial/papers, /mypapers (filtered to author).
**Joomla position bindings:** sidebar-right (default), sidebar-extra (wide pull).
**Data source:** `rs:LookCollab*` filter + `collab_open=true`.

**Header label:** `OPEN COLLABORATION`.
**Body:**
- 3 card rows (4 if wide), each 72px tall:
  - Row 1: paper title (Spectral 14pt, link, 1-line clamp) + LookCollab sub-tag chip.
  - Row 2: collab_seek phrase (Spectral 12pt italic, 1-line clamp, `--ink2`) + interest level pill (high/med/low color: coral/amber/sage).
  - Row 3: IntelliD pill + "connect →" mini button (mono UPPERCASE 10pt outline `--river`).
- Footer: mono 10pt "view all open requests →".

**Empty state:** "no open requests in this slice".
**Loading:** 3 skeleton rows.
**Error:** mono `--coral`.

**Interactions:**
- Connect → opens secure messaging modal (login required).
- Card click → parent paper detail.
**Color encoding:** interest pill — coral high · amber medium · sage low (intentionally inverted from urgency: high interest = coral as "hot").
**Observer projection note:** HUMINT only.

---

### `mod_ai_usage_heatmap`
**ACL / context:** Public (aggregate); paper-scoped variant on /paper/{id}.
**Joomla position bindings:** sidebar-right (default), content-top (wide pull).
**Data source:** aggregate `eaiou_ai_sessions` joined `eaiou_papers` with discipline filter (or paper filter).

**Header label:** `AI USAGE HEATMAP` (or `AI USAGE — THIS PAPER`).
**Body (aggregate mode):**
- Segmented horizontal bar chart, 32px tall, 100% wide:
  - Segments by vendor (`Anthropic`, `OpenAI`, `Google`, `Mistral`, `Open-weight`, `Other`).
  - Segment color: violet variants — `--violet`, `--violet 80%`, `--violet 60%`, `--violet 40%`, `--violet 20%`, `--paper3`.
  - Each segment labeled mono 10pt with vendor name and percentage.
- Below the bar: mode breakdown — three small bars stacked (Generated / Assisted / None) in `--violet`, `--violet-l`, `--paper2`.
- Footer: mono 10pt "47 papers · 312 sessions · cycle q4".

**Body (paper-scoped):**
- Vertical list of tools used: vendor + model + mode chip + risk_flags chips. 5 rows max.
- Below: mini "didntmakeit count" indicator: 7 excluded outputs (mono with link to gated detail).

**Empty state:** "no AI usage logged in this slice".
**Loading:** skeleton bars.
**Error:** mono `--coral`.

**Interactions:**
- Segment hover → tooltip mono with raw session count + model breakdown.
- Click → drill to /search?q=ai_vendor:<vendor>.
**Color encoding:** violet family for AI; ink/paper for non-AI.
**Observer projection note:** HUMINT default. UNKINT toggle adds session-hash overlay (admin/EIC).

---

## DESIGN-SYSTEM-DERIVED MODULES (flag for SSOT promotion)

---

### `mod_gap_map`
**ACL / context:** Public. Shown on home (small), /discover/gaps (full-bleed), /editorial/papers (compact).
**Joomla position bindings:** content-top (large), sidebar-right (compact).
**Data source:** `rs:Stalled:*` aggregate from rst_tags joined `eaiou_papers`.

**Header label:** `GAP MAP · WHERE THE RIVER STOPS`.
**Body (compact mode):**
- 5 horizontal bars, each labeled by discipline (mono 11pt):
  - Bar fill = aggregate stall density across all stall types in that discipline.
  - Color encoding: `--paper2` → `--amber-l` → `--amber` → `--coral` by density.
  - Mono 10pt tail label = count.
- Footer: mono 10pt "view full gap map →" → /discover/gaps.

**Body (full mode — used on /discover/gaps only):**
- 11×5 heatmap grid (stall-types × disciplines). Defer to `UXPILOT_01 §Discover — Gaps`.

**Empty state:** "no gaps in this slice — the river is flowing freely".
**Loading:** 5 skeleton bars.
**Error:** mono `--coral`.

**Interactions:** bar click → /discover/gaps?discipline=<name>; bar hover → tooltip with top 3 stall types in that discipline.
**Color encoding:** density gradient paper2→amber-l→amber→coral. No accent color besides amber/coral.
**Observer projection note:** HUMINT only.

---

### `mod_trending_ideas`
**ACL / context:** Public. Shown on home, /discover/trends (full), /discover/ideas, /search.
**Joomla position bindings:** sidebar-right (default), content-mid (wide pull).
**Data source:** entropy-novelty aggregator over un-space + open declarations + recent searches.

**Header label:** `TRENDING IDEAS · ENTROPY-NOVELTY`.
**Body (compact mode):**
- 5 ranked rows, each 36px:
  - Rank (mono 700, 14pt, fixed 32px, `--ink3`).
  - Idea phrase (Spectral 13pt, `--ink`, 1-line clamp, link).
  - Mini-spark (40px wide, 8px tall, line in `--violet`).
  - Entropy-novelty mono 10pt (e.g., `0.91`).
- Footer: mono 10pt "view all trends →" → /discover/trends.

**Body (full mode — used on /discover/trends only):**
- 25 ranked rows, each 80px tall (defer to `UXPILOT_01 §Discover — Trends`).

**Empty state:** "no trends — the field is asleep".
**Loading:** 5 skeleton rows.
**Error:** mono `--coral`.

**Interactions:** row click → trend landing page (or filter view); rank hover → tooltip with entropy-novelty + cycle slot trend.
**Color encoding:** spark line `--violet`. Entropy-novelty value text color: `--ink` ≥ 0.7, `--ink2` 0.5–0.7, `--ink3` < 0.5.
**Observer projection note:** HUMINT only.

---

### `mod_intellid_graph`
**ACL / context:** Wide-mode only (pull-down). Paper-scoped on /paper/{id} and /editorial/paper/{id}; user-scoped on /mypapers.
**Joomla position bindings:** sidebar-extra (wide pull-down only).
**Data source:** attribution + ai_session aggregate per paper or per user.

**Header label:** `INTELLI-D GRAPH · CONTRIBUTION`.
**Body (paper-scoped):**
- Stacked horizontal bar showing % contribution by IntelliD (human + AI):
  - Each segment 32px tall, color from accent rotation (river → sage → amber → coral → violet).
  - Each segment labeled with IntelliD pill + percent + AI/Human badge.
- Below the bar: mono 10pt total contributors count + AI-fraction mono 10pt.
- Footer: mono 10pt "view full attribution →" → paper detail Attribution tab.

**Body (user-scoped — on /mypapers):**
- Vertical bar per paper authored (max 8 visible; pagination via tiny carousel arrows mono):
  - Each bar shows that user's % contribution to the paper.
  - Color: sage if author is primary, amber if non-primary, ink3 otherwise.
- Footer: mono 10pt "view all papers →" → /mypapers.

**Empty state:** "no attribution data".
**Loading:** 3 skeleton bars.
**Error:** mono `--coral`.

**Interactions:** segment hover → tooltip with IntelliD + role + contribution_type; segment click → person profile (if linked) or paper attribution tab.
**Color encoding:** accent rotation (river/sage/amber/coral/violet) for each contributor; AI contributors get a 1px violet outline regardless of fill.
**Observer projection note:** HUMINT default. UNKINT exposes session-hashes inline.

---

### `mod_appreciated_scale`
**ACL / context:** Wide-mode only (pull-down). Paper-scoped on /paper/{id}, author-scoped on /mypapers, gap-context on editor pages.
**Joomla position bindings:** sidebar-extra.
**Data source:** gap-map matches + LookCollab matches + cross-domain candidates from didntmakeit.

**Header label:** `APPRECIATED SCALE · GAPS THIS PAPER ADDRESSES`.
**Body:**
- 3 opportunity cards, each 80px tall:
  - Row 1: opportunity phrase (Spectral 13pt italic, 2-line clamp).
  - Row 2: multiplier mono 12pt (e.g., `×3.2 GAP DENSITY`) + age relative bar (`▣▣▣▢▢▢▢`) + urgency chip (high/med/low — coral/amber/sage).
  - Row 3: mono 10pt `5 STALLED PAPERS · 2 LOOKCOLLAB · 1 CROSS-DOMAIN`.
- Footer: mono 10pt "view gap map →" → /discover/gaps with relevant filter.

**Empty state:** "no appreciated-scale matches yet".
**Loading:** 3 skeleton cards.
**Error:** mono `--coral`.

**Interactions:** card click → /discover/gaps?gap=<id>; chip hover → tooltip with raw counts.
**Color encoding:** urgency chip — coral high · amber med · sage low. Multiplier text color: `--coral` if ≥ 3, `--amber` if 1.5–3, `--ink2` < 1.5.
**Observer projection note:** HUMINT only.

---

## Module placement matrix (by page)

| Page | Right rail (fixed default) | Wide-mode pull-down extras |
|---|---|---|
| `/` (Home) | open_collaborate · ai_usage_heatmap · trending_ideas | gap_map · intellid_graph · appreciated_scale |
| `/papers` | latest_papers · ai_usage_heatmap · open_collaborate | trending_ideas · gap_map |
| `/paper/{id}` | latest_papers (q-range) · open_collaborate (this paper) | ai_usage_heatmap (paper) · intellid_graph · appreciated_scale |
| `/discover/ideas` | trending_ideas · open_collaborate · gap_map | intellid_graph · ai_usage_heatmap |
| `/discover/open` | open_collaborate · trending_ideas · ai_usage_heatmap | — |
| `/discover/gaps` | gap_map (full-bleed in main) · trending_ideas · open_collaborate | — |
| `/discover/trends` | trending_ideas (full-bleed in main) · gap_map · ai_usage_heatmap | — |
| `/search` | trending_ideas · open_collaborate | — |
| `/mypapers` | open_collaborate (filtered) · trending_ideas | ai_usage_heatmap (author) · appreciated_scale |
| `/paper/{id}/workspace` | open_collaborate (filtered to this paper) · appreciated_scale | intellid_graph · ai_usage_heatmap (this paper) |
| `/submit` (wizard) | — (focus mode) | — |
| `/paper/{id}/revise` | open_collaborate (filtered) | — |
| `/reviewer/queue` | open_collaborate · trending_ideas | ai_usage_heatmap · intellid_graph |
| `/reviewer/paper/{id}` | intellid_graph (this paper) · appreciated_scale · open_collaborate | ai_usage_heatmap (paper) |
| `/reviewer/paper/{id}/review` | — (focus mode) | intellid_graph |
| `/editorial/papers` | editor_dashboard (full takes over rail) · open_collaborate | ai_usage_heatmap · gap_map · intellid_graph |
| `/editorial/paper/{id}` | intellid_graph · appreciated_scale · open_collaborate | ai_usage_heatmap |
| `/editorial/assign/{id}` | — (focus mode) | — |
| `/editorial/decide/{id}` | — (focus mode) | — |

---

## Canonical promotion checklist (for SSOT update post-mockup-acceptance)

When UXPilot mockups validate the design-system-derived modules, the following SSOT changes should be made (out of scope for this prompt set):

- Add to `/repos/eaiou/SSOT.md §3.2` Module list (canonical):
  - `mod_gap_map`
  - `mod_trending_ideas`
  - `mod_intellid_graph`
  - `mod_appreciated_scale`
- Add corresponding plg_content_* or plg_system_* feeders if data-source plugins are required (e.g., `plg_system_gap_aggregator`).
- Add cache layer note (these are aggregate reads — should hit nginx 60-min cache or a dedicated component cache).

---

## End of `UXPILOT_06_modules.md`

Next file: `UXPILOT_07_layout_shells.md` — fixed and wide layouts, header/footer chrome, observer-projection indicator, session-lock indicator, navigation system.
