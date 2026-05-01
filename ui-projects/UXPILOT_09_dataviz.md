# UXPILOT_09 — dataviz geometry

**Tokens:** see `UXPILOT_00_design_system.md §3` (light) and `§4` (dark).
**Components:** see `UXPILOT_08_components.md` for tables, tooltips, cards.
**Modules referenced:** see `UXPILOT_06_modules.md`.

This file specifies the geometry of every chart referenced across the prompt set. UXPilot mockups should render these as raw inline SVG — no chart library, no D3 runtime in the mockup. Live builds may wire to D3 / Chart.js later, but the visual spec stays here.

The aesthetic anchor (`UXPILOT_00 §1`) requires every dashboard or paper page to surface at least one chart. Charts use accent colors as data, never as decoration.

---

## 1. Universal chart rules

| Rule | Spec |
|---|---|
| Background | inherits parent (`--surface` inside cards, `--paper` inside hero/full-bleed) |
| Stroke width | 1px hairlines for axes/baselines; 1.5px for line series; 2px for emphasis line only |
| Type | JetBrains Mono 10pt for labels, 11pt for axis tick text; Spectral 14pt for chart title (when present, mostly absent) |
| Color | River `--river` is the dominant data color. Other accents only when categorical encoding requires (vendor breakdowns, contributor rotation). |
| Axes | Most charts axis-less. Where present: bottom + left only, 1px `--paper3`, no top/right rules. |
| Gridlines | None. Use a single 1px `--paper3` baseline if the chart needs grounding. |
| Legend | Inline mono labels next to series, never a boxed legend. |
| Animation | None on first load. Hover reveals tooltip only. No entry animation. |
| Tooltip | Use `tooltip-info` from `UXPILOT_08 §13` (mono 11pt, inverted `--ink` bg). |
| Empty state | Mono 11pt centered `--ink3` text — no chart frame rendered. |
| Loading | Skeleton block matching chart bounds, bg `--paper2`. |

**Acceptance:**
- No 3D, no isometric, no glow, no gradient fills.
- No emoji, no icon labels in axes.
- Color encoding is consistent across pages — `--river` always means q_signal/primary, `--violet` always means AI, `--amber` always means warning/attention, `--coral` always means error/overdue, `--sage` always means accepted/on-track.

---

## 2. q_signal bar

The most-rendered chart in the system. Single horizontal bar showing a paper's q_signal value (0.0–1.0).

**Geometry:**
- Width: 60px (inline in cards, table cells), 80px (paper masthead), 4px tall (default), 6px tall (paper masthead variant), 320px wide × 4px tall (river-state hero).
- Bar fill: `--river`.
- Track: `--paper3`, 1px hairline, full width.
- Value indicator: mono text adjacent to bar — left side for hero, right side for inline (e.g., `0.847`).
- No tick marks, no scale labels, no axis.

**Variants:**
| Variant | Width | Height | Use |
|---|---|---|---|
| `q-bar-inline` | 60px | 4px | Card rows, table cells |
| `q-bar-strong` | 80px | 4px | Paper detail masthead |
| `q-bar-hero` | 320px | 4px | Home river-state, paper detail hero |
| `q-bar-row` | 100% | 6px | Paper detail "rank position" full-width strip |

**Hover/tooltip:** mono `q=0.847 · rank #4 in cycle q4`.

**SVG sketch (60×4 inline variant):**
```
<svg viewBox="0 0 60 4" width="60" height="4">
  <rect x="0" y="0" width="60" height="4" fill="var(--paper3)" />
  <rect x="0" y="0" width="50.82" height="4" fill="var(--river)" />
</svg>
```
Width of fill = `q * 60`.

---

## 3. Sparkline (line)

Used in: editor dashboard (4 metric sparks), table inline (per row), trending_ideas mini-spark.

**Geometry:**
- Width 60px (inline) or 80px (dashboard) or 200px (full dashboard card variant).
- Height 16px (inline) or 24px (dashboard) or 40px (full).
- 1.5px stroke, no fill, no markers, no axis.
- Color: `--river` for primary metric; `--violet` for AI metrics; `--coral` for overdue/error metrics; `--amber` for at-risk/attention; `--sage` for accepted/on-track.
- Trend baseline (optional): mono 10pt mini-arrow ↑/↓/→ + percentage in same color.

**Smoothing:** none. Render as straight-segment polyline per data point.
**Sample density:** typical 12–24 points (one per cycle slot, or one per recent paper). No labels on individual points.

**Hover:** tooltip with mono `cycle q1: 12 · q2: 18 · q3: 22 · q4: 31 (current)`.

**SVG sketch (60×16):**
```
<svg viewBox="0 0 60 16" width="60" height="16">
  <polyline points="0,12 5,11 10,9 15,10 20,7 25,6 30,5 35,4 40,3 45,3 50,2 55,2 60,1"
            fill="none" stroke="var(--river)" stroke-width="1.5" />
</svg>
```

---

## 4. Segmented horizontal bar

Used in: `mod_ai_usage_heatmap` aggregate (vendor breakdown), state-distribution rows in admin tables, manuscript pipeline cycle-state strips.

**Geometry:**
- Full width of container, 32px tall (default), 24px (compact), 48px (full-bleed).
- 1px `--paper3` border around the whole bar.
- Each segment: solid fill, 1px right `--paper3` divider (last segment no divider).
- Mono 10pt labels inside each segment when ≥ 60px wide; otherwise label sits below in legend row.
- Labels: vendor name + percent, mono 10pt.

**Color encoding (AI vendor — violet family):**
- Anthropic: `--violet`
- OpenAI: `--violet` 80% alpha
- Google: `--violet` 60% alpha
- Mistral: `--violet` 40% alpha
- Open-weight: `--violet` 20% alpha
- Other: `--paper3`

**Color encoding (workflow state distribution):**
- draft: `--paper2`
- submitted: `--river-ll`
- under_review: `--amber-l`
- decision_pending: `--violet-l`
- accepted: `--sage-l`
- published: `--sage`
- rejected: `--coral-l`

**Hover segment:** tooltip with mono `Anthropic · 47 sessions · 38%`. Segment outline darkens 10%.

---

## 5. Stacked horizontal bar (contribution / `intellid_graph` paper-scoped)

Used in: `mod_intellid_graph` (paper-scoped), attribution tab on paper detail.

**Geometry:**
- Full width, 32px tall.
- Each segment 32px tall, 1px right `--paper3` divider, color from contributor rotation.
- Inside each segment: IntelliD pill (mono 10pt, see `UXPILOT_08 §3.3`) + percent (mono 10pt) + role chip (Author / AI / Reviewer-comment / Editor-edit). When segment < 80px, only IntelliD pill rendered; full label moves to tooltip.
- Below the bar: mono 10pt "5 contributors · 23% AI · 77% human".

**Contributor color rotation:**
- 1st: `--river`
- 2nd: `--sage`
- 3rd: `--amber`
- 4th: `--coral`
- 5th: `--violet`
- 6th+: cycle through with 60% alpha
- AI contributors: regardless of fill, get a 1px `--violet` outline (visible at 1.5px outset).

**Hover segment:** tooltip mono `INT-9F2A · Author · 41% · 8 commits · 12 USO records`.

---

## 6. Stacked vertical bar (contribution / `intellid_graph` user-scoped on /mypapers)

Used in: `mod_intellid_graph` user-scoped variant.

**Geometry:**
- Container 100% wide, 120px tall.
- Up to 8 vertical bars side-by-side, each 24px wide, 8px gap.
- Each bar 100px tall (max). Fill from bottom up by user's contribution percent.
- Color encoding: sage if user is primary author, amber if non-primary co-author, `--ink3` if review/edit only.
- Mono 10pt label below each bar: paper short-id (e.g., `MN-26-1117`).
- Pagination via tiny carousel arrows mono 10pt left/right of the bar group.

**Hover bar:** tooltip with mono `paper title · INT-9F2A · 41% contribution · primary author`.

---

## 7. Heatmap (gap_map full and compact)

### 7.1 Full heatmap (`/discover/gaps`, full-bleed in main column)

**Grid:** 11 stall-types (rows) × 5 disciplines (columns) = 55 cells.
**Cell:** 56px wide × 32px tall, 1px `--paper3` between cells.
**Cell fill:** density gradient `--paper2` → `--amber-l` → `--amber` → `--coral` (4-step quantile).
**Cell content:** mono 11pt count centered (e.g., `12`). Rendered `--ink2` on light fills, `--paper` on coral.

**Axes:**
- X (top): discipline labels mono 11pt UPPERCASE tracking-wide `--ink2`. Padding 8px below labels.
- Y (left): stall-type labels mono 11pt UPPERCASE `--ink2`. Right-align labels, 8px gap to grid.

**Legend:** below grid — 4 cells (`--paper2`, `--amber-l`, `--amber`, `--coral`) labeled mono 10pt `low · med-low · med-high · high`.

**Hover cell:** tooltip mono with `Cosmology · NotTopic:Bayesian · 12 stalled papers · top 3: paper-A, paper-B, paper-C`.
**Click cell:** drill to /discover/gaps?discipline=&stall_type=.

### 7.2 Compact heatmap (right rail, 320px wide)

5 horizontal bars stacked, one per discipline:
- Each bar 24px tall, full container width.
- Bar fill = aggregate stall density across all stall types (gradient `--paper2`→`--amber-l`→`--amber`→`--coral`).
- Mono 10pt label left (discipline), mono 10pt count right.

---

## 8. Network graph (intellid_graph wide-mode network variant)

Used in: paper detail wide-mode pull-down, `/editorial/paper/{id}` admin view.

**Geometry:**
- Container 360×200px (wide-mode pull-down) or 480×280px (admin detail).
- Force-directed layout, but rendered as a static frozen layout in the mockup.
- Nodes:
  - Paper (center): 16×16 circle, fill `--river`, 1px outline `--paper3`.
  - Authors / contributors: 12×12 circles, fill from contributor rotation (river/sage/amber/coral/violet), 1px outline `--paper3`.
  - AI sessions: 10×10 squares, fill `--violet`, 1px outline `--paper3`.
- Edges: 1px `--paper3` lines, no arrows.
- Labels: mono 10pt, IntelliD pill or session-hash truncated, placed adjacent to node with 4px gap.

**Acceptance:**
- Max 12 nodes visible. Overflow collapses into "+N" cluster node mono 10pt.
- No edge labels. No animation.
- For mockup purposes, place nodes at intuitive positions (paper center, contributors radial, AI sessions outer).

**Hover node:** tooltip mono with full IntelliD or session-hash + role + contribution detail.

---

## 9. Ranked-list mini-chart (trending_ideas compact)

Used in: `mod_trending_ideas` compact (right rail).

**Geometry:** 5 rows, each 36px tall.
- Rank: mono 700 14pt, fixed 32px wide column, `--ink3`.
- Idea phrase: Spectral 13pt, `--ink`, 1-line clamp, link.
- Mini-spark: 40×8 line in `--violet`, no fill.
- Entropy-novelty score: mono 10pt right-aligned, fixed 36px column.

**Score color rule:**
- ≥ 0.7: `--ink`
- 0.5–0.7: `--ink2`
- < 0.5: `--ink3`

**Full-mode variant** (used on `/discover/trends`): 25 rows, each 80px tall — see `UXPILOT_01 §Discover — Trends`.

---

## 10. Ranked-list full chart (trending_ideas full / `/discover/trends`)

**Geometry:** 25 rows, each 80px tall, full main-column width.
- Rank circle 32×32: 1px `--paper3` border, mono 700 14pt rank, `--ink2`. First-place rank fills `--violet-l` background.
- Idea phrase: Spectral 16pt 1-line + Spectral 12pt italic explanation 1-line below.
- Mini-spark inline: 80×16 line `--violet`.
- Entropy-novelty score + delta: mono 13pt + small ↑/↓ glyph + delta percent.
- Right side: tag chips up to 3 + "+N" overflow.

**Hover row:** subtle bg `--paper2`, cursor pointer.
**Click row:** drill to /search?q=trend:<id>.

---

## 11. Multi-stat sparkline panel (editor dashboard compact)

Used in: `mod_editor_dashboard` compact (right rail, /editorial/papers).

**Layout:** 4 stacked stat lines in card body. Each line 28px tall.
- Label: mono 11pt UPPERCASE `--ink3` left, fixed 96px column.
- Value: mono 700 16pt `--ink` next.
- Sparkline: 60×16 line in metric color, 8px gap from value.
- Optional delta: mono 10pt + arrow glyph to right.

**Stats:**
| Label | Color | Description |
|---|---|---|
| `UNDER REVIEW` | `--river` | Active count + 12-cycle spark |
| `DECISION PENDING` | `--violet` | Count + spark |
| `OVERDUE` (relative) | `--coral` | Count + spark |
| `MEDIAN TTFD` | sage if better than cycle target, coral if worse | Relative-bar (see §13) |

---

## 12. KPI grid (editor dashboard full / `/editorial/papers`)

Full dashboard variant — 6 cards in a 3×2 grid.

**Each card:** 200×160px, `card-kpi` from `UXPILOT_08 §19`. Body:
- Big number Spectral 36pt `--ink` centered (e.g., `47`).
- Sparkline 200×40 `--river` (or metric-colored) below the number.
- Mono 10pt label below sparkline, centered.

**6 KPIs (per `UXPILOT_04`):**
1. Active manuscripts (`--river`)
2. Submitted this cycle (`--river-l`)
3. Under review (`--amber`)
4. Decision pending (`--violet`)
5. Median time-to-first-decision relative-bar
6. Overdue reviews (`--coral`)

**Acceptance:**
- Cards render same height even when number digits vary.
- Sparkline range normalized per card (independent y-scale).

---

## 13. Relative-window bar (the `▣▣▣▢▢▢▢` glyph string)

Used everywhere a "where in the relative window" indicator is needed without exposing absolute time. Examples: reviewer queue card status, editor dashboard median TTFD, submission-window-closing banner.

**Glyph:** 7 mono characters total.
- Filled positions: `▣` (U+25A3, white square containing black small square — UPPERCASE in mono).
- Empty positions: `▢` (U+25A2, white square with rounded corners — visually open).

**Color encoding:**
- Position 1–2 (early): filled in `--sage`.
- Position 3–4 (mid): filled in `--amber`.
- Position 5–7 (late): filled in `--coral`.
- Empty positions: `--ink3`.

**Implementation:**
- Render as inline mono span, color applied per character.
- Mono 13pt default, mono 11pt compact.
- Tooltip mono: "you are 4 of 7 through this paper's review window".

**Acceptance:**
- Never shows absolute days/dates. Window is always relative.
- For "0 of 7" (just started): all empty positions `--ink3`.
- For "7 of 7" (final position): all filled in `--coral`.

---

## 14. Reviewer rubric scale (TAGIT review console)

Used in: `/reviewer/paper/{id}/review` rubric console.

**Per criterion:** horizontal 5-segment selector.
- Container 240px wide, 32px tall.
- 5 segments, each 48×32px, 1px `--paper3` border, no internal fill (default).
- Mono labels above each segment: `1 2 3 4 5`.
- Selected segment: bg `--river-ll`, border `--river`. Other segments unchanged.
- Hover non-selected: bg `--paper2`.
- Mono 11pt UPPERCASE label below: `INSUFFICIENT — EXEMPLARY` (left to right).

**Acceptance:**
- No emoji faces, no stars, no thumbs, no smiley scale.
- Numeric only. Color stays river family.
- Required state: selected = at least one. Submit blocks if any criterion unscored.

---

## 15. Mode breakdown (AI usage three-bar stack)

Used inside `mod_ai_usage_heatmap` aggregate body, below the segmented vendor bar.

**Geometry:** 3 horizontal bars stacked, each 8px tall, full container width, 4px vertical gap.
- Bar 1 — Generated: fill `--violet`, mono 10pt label right "generated · 38%".
- Bar 2 — Assisted: fill `--violet-l`, mono 10pt label right "assisted · 47%".
- Bar 3 — None / human-only: fill `--paper2`, mono 10pt label right "human-only · 15%".

**Hover bar:** tooltip mono with raw counts.

---

## 16. Multiplier indicator (`mod_appreciated_scale` cards)

Used in: appreciated_scale module body.

**Geometry per card row:**
- Multiplier value: mono 700 12pt `× 3.2` + UPPERCASE label `GAP DENSITY` mono 10pt below or beside.
- Color rule: `--coral` if ≥ 3.0; `--amber` if 1.5–3.0; `--ink2` if < 1.5.
- Adjacent: relative-window bar (see §13) for opportunity-age.
- Adjacent: urgency chip (high `--coral` / med `--amber` / low `--sage`).

**No bar chart.** Multiplier is a typographic-numeric primitive, not a chart.

---

## 17. Entropy Trace Map (paper detail Sources tab)

Surfaces the entropy trace endpoint `/trace/entropy` referenced in `UXPILOT_99 §3`. Embedded as a chart inside the paper detail Sources tab — not a standalone page.

**Geometry:**
- Container 100% wide, 240px tall.
- Polyline of entropy values (Spectral 12pt label left "entropy") over source-events (mono 10pt UPPERCASE labels along x-axis: `INGEST · CITE · DERIVE · COMPUTE · LOG · CITE · CITE · OUTPUT`).
- Y-axis: 0–1 scale, 1px `--paper3` baseline, no top rule. Mono 10pt tick labels at 0, 0.5, 1.0.
- Stroke 1.5px `--violet`. No fill.
- Markers at each event: 6×6 circle, `--violet` fill, 1px `--surface` outline.
- Vertical hairlines `--paper3` at each event for grounding.

**Annotations:**
- Above the line: mono 10pt UPPERCASE event label rotated 0° (no rotation; if cramped, every other label).
- Threshold band: 0.7–1.0 shaded `--coral-l` 30% to indicate "novelty zone"; below 0.3 shaded `--paper2` to indicate "noise zone".

**Hover marker:** tooltip mono `event: COMPUTE · entropy: 0.84 · session: INT-AI-7C04 · model: claude-opus-4.7`.

**Empty state:** "no entropy events traced for this paper" mono 11pt centered.

---

## 18. q_signal histogram (admin dashboard)

Used on admin dashboard top KPI strip and on /editorial/papers full dashboard.

**Geometry:**
- Container 360×120px.
- 20 bins (q ∈ [0, 1.0] in 0.05 increments), each bin 18px wide × variable height.
- Bin fill: `--river`. Bin border: 1px `--paper3` between bins.
- Y-axis: paper count, 1px `--paper3` baseline, mono 10pt max label only.
- X-axis: mono 10pt `0.0 — 1.0` labels at endpoints.

**Annotation overlay:** vertical 1px `--coral` line at q=0.5 (publication threshold). Mono 10pt UPPERCASE label `THRESHOLD` above the line, top-right.

**Hover bin:** tooltip mono `q ∈ [0.65, 0.70) · 12 papers · top: "Quantum decoherence in N/U algebra reductions"`.

---

## 19. Cycle slot timeline (admin manuscript pipeline)

Used on /editorial/papers paper-management view, optionally on /paper/{id}/workspace.

**Geometry:**
- Horizontal strip 100% wide, 40px tall.
- 8 cycle slots (representing the manuscript cycle from submission to publication).
- Each slot 12.5% wide, 1px `--paper3` between slots.
- Slot fill encodes state:
  - past slots (already traversed): `--paper2`
  - current slot: `--river-ll` with 1px `--river` outline + mono 11pt UPPERCASE label centered (state name)
  - future slots: `--paper`
  - skipped slots (e.g., expedited path): `--paper3` diagonal pattern
- Below: mono 10pt UPPERCASE labels for all 8 slot names: `SUBMIT · INITIAL · ASSIGN · REVIEW · DECIDE · REVISE · ACCEPT · PUBLISH`.

**Hover slot:** tooltip mono with slot meaning + relative-window bar (see §13) for that slot's progress.

**No date labels.** Slot is a logical position, not a calendar interval.

---

## 20. Color encoding reference (cross-chart)

Single-source-of-truth for what each accent color means inside dataviz.

| Color | Meaning | Used in |
|---|---|---|
| `--river` | Primary metric · q_signal · publication count · river-state | q-bars, sparklines (default), histogram bins, contributor rotation slot 1 |
| `--river-l` | Secondary primary metric variant | sparkline alternates, histogram secondary series |
| `--river-ll` | Selected state · selected row · current cycle slot | selection backgrounds |
| `--violet` | AI usage · entropy · AI session marker | ai-usage segmented bar, entropy trace, ai mode breakdown, AI nodes in graphs |
| `--violet-l` | AI assisted (mid-tier) | ai mode breakdown row 2 |
| `--amber` | Attention · at-risk · mid-window | gap-map mid density, sparkline at-risk, dashboard "overdue" warm-up |
| `--coral` | Overdue · error · threshold · late-window | gap-map high density, threshold lines, dashboard overdue, relative-bar late |
| `--sage` | Accepted · on-track · early-window · primary author | dashboard accepted, contributor primary author, relative-bar early |
| `--ink3` | Inactive · empty bin · no-data | skeleton bars, empty cells, no-AI baseline |
| `--paper2` | No-data background · empty band | histogram empty bins, gap-map low density |
| `--paper3` | Borders · gridlines · hairline baselines | every chart axis/baseline |

**Acceptance:**
- A chart should never use red (`--coral`) for "AI" or violet for "overdue". Color meaning is locked.
- Charts that need more than 5 categorical colors should switch to a sequential gradient using one accent + alpha steps (see ai_usage_heatmap §4).

---

## 21. Tooltip pattern across charts

Reuse `tooltip-info` from `UXPILOT_08 §13`.

**Standard fields per chart:**
| Chart | Tooltip fields |
|---|---|
| q-bar | `q=N · rank #N · cycle qN` |
| Sparkline | last value + delta percent + cycle slot |
| Segmented bar | category · raw count · percent |
| Stacked bar | IntelliD or vendor · raw count · percent · role |
| Heatmap cell | row label · column label · raw count · top items |
| Network node | full IntelliD or session-hash · role · contribution detail |
| Histogram bin | range · count · top item |
| Cycle slot | slot meaning · relative-bar position |

**No clock times in tooltips.** Cycle slot is the only temporal anchor allowed in HUMINT view. UNKINT projection adds raw timestamps to tooltips with mono 10pt prefix `unkint:` and 1px `--coral` left underline.

---

## 22. Acceptance criteria for any UXPilot mockup with charts

1. Every dashboard or paper page renders ≥ 1 chart.
2. Charts use accent colors as data, not as decoration. Backgrounds stay `--surface` or `--paper`.
3. Color meaning matches §20 (river=primary, violet=AI, amber=warning, coral=error/late, sage=accepted/early).
4. No 3D, no gradients, no glow.
5. Hairline 1px baselines/borders only. No drop shadows on chart frames.
6. No clock-time labels. No `posted X ago`. No `due in N days`.
7. Mono labels for axes / counts; Spectral only for chart titles (rare).
8. Hover tooltips use `tooltip-info` from `UXPILOT_08 §13`.
9. Empty states: mono text only, no chart frame.
10. Loading states: bg `--paper2` skeleton block matching chart bounds.

---

## 23. Citation rules

- Per-page prompts cite chart geometry by section: "Render q_signal bar per `UXPILOT_09 §2`."
- Modules cite by chart name: "Body uses ranked-list mini-chart per `UXPILOT_09 §9`."
- Color encoding is centralized in §20 — pages and modules cite §20 rather than restating.

---

## 24. Open dataviz questions (for Eric)

1. Library choice: raw SVG (current spec) vs D3 (when live) vs Chart.js. Mockup is raw SVG. Production library decision deferred.
2. q_signal color: `--river` is dominant. Consider `--river-l` for secondary q-bars where two q-bars appear in the same view (paper detail "this paper" + "rank in cycle").
3. Network graph: force-directed runtime cost vs static frozen layout. Current spec: frozen for mockup. Live decision deferred.
4. Entropy trace y-axis: 0–1 normalized vs raw entropy values. Current: normalized 0–1. Confirm with Eric before live wiring.
5. Cycle slot count: spec is 8 slots. SSOT calls for 7 in some places. Reconcile with `/repos/eaiou/SSOT.md §3.1`.

---

## End of `UXPILOT_09_dataviz.md`

Next file: `UXPILOT_10_states.md` — empty / loading / error / success / sealed state catalog and copy library.
