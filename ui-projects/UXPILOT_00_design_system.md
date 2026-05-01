# UXPILOT_00 — eaiou design system (foundation)

**Companion to:** `UXPILOT_PROMPT_EAIOU.md` (philosophical canon — IntelliD, TAGIT, observer projection, temporal blindness).
**Cited by:** every per-page prompt file (`UXPILOT_01..07`, `UXPILOT_99_index.md`).
**Build target:** light mode. Dark tokens defined; not built out.

---

## 1. Aesthetic anchor

**Reference:** "Academic editorial meets tylervigen.com spurious correlations."
- Editorial: Spectral serif, generous whitespace, hairline rules, no drop shadows, mono metadata.
- Dataviz: every page surfaces at least one chart/sparkline/segmented bar. Charts use the accent palette as data colors, not as decoration.
- Unified, not monochrome: the river-blue (`--river`) anchors every page; amber/sage/coral/violet appear only in tags, badges, and chart segments.
- No gradients, no glassmorphism, no glow effects. 1px hairlines and one-step elevation maximum.

---

## 2. Typography

| Use | Family | Weight(s) | Size scale | Notes |
|---|---|---|---|---|
| Display headlines | **Spectral** | 300, 400 | 56 / 44 / 36 | Letterspacing -0.01em. Italic 400 for editorial pull-quotes. |
| Body / article | **Spectral** | 400 | 18 / 16 | Line-height 1.65. Italic 400 italic for emphasis. |
| Section subhead | **Spectral** | 600 | 22 / 20 | Used for module titles inside cards. |
| Metadata / labels / code | **JetBrains Mono** | 400, 500, 700 | 14 / 12 / 11 | UPPERCASE tracking-wide for section labels. Lowercase with full punctuation for code/tokens. |
| Captions / footers | **JetBrains Mono** | 400 | 11 / 10 | `--ink3`. |

**Pairing rule:** Spectral for content the human reads; mono for what the machine wrote (IDs, tokens, hashes, timestamps where allowed by ACL, q_signal values, tag names).

---

## 3. Color tokens — light (default build)

| Token | Hex | Role |
|---|---|---|
| `--ink` | `#0e0d0b` | Primary text |
| `--ink2` | `#3a3832` | Secondary text |
| `--ink3` | `#7a7670` | Tertiary / hint |
| `--paper` | `#f7f4ef` | Page background |
| `--paper2` | `#ede9e1` | Section divider, module header backdrop, skeletons |
| `--paper3` | `#e0dbd0` | 1px borders, disabled state |
| `--surface` | `#ffffff` | Card / panel / input background |
| `--river` | `#1a4a6b` | Primary accent — links, primary buttons, focus ring, q_signal bars |
| `--river-l` | `#2d6e9e` | Hover / active variant of river |
| `--river-ll` | `#e8f1f7` | River wash — selected row, info banner |
| `--amber` | `#c47c0a` | Warning — due-soon, AI-Logged, attention |
| `--amber-l` | `#fdf0d0` | Amber wash |
| `--sage` | `#3a6b4a` | Success — accepted, on-track, resolved |
| `--sage-l` | `#e8f2ec` | Sage wash |
| `--coral` | `#b84832` | Error — overdue, rejected, conflict, [VULNERABILITY] |
| `--coral-l` | `#faeae6` | Coral wash |
| `--violet` | `#4a3278` | Info / AI / Un Scientific / [FORK] |
| `--violet-l` | `#ede8f7` | Violet wash |
| `--orcid` | `#a6ce39` | ORCID brand — fixed both modes, used only on ORCID badge |

---

## 4. Color tokens — dark (defined, not built)

| Token | Hex |
|---|---|
| `--ink` | `#f2efe8` |
| `--ink2` | `#c8c4bb` |
| `--ink3` | `#8a8680` |
| `--paper` | `#141210` |
| `--paper2` | `#1e1c1a` |
| `--paper3` | `#2e2b28` |
| `--surface` | `#1e1c1a` |
| `--river` | `#4a8abf` |
| `--river-l` | `#6aaad8` |
| `--river-ll` | `#1a3550` |
| `--amber` | `#d4920e` |
| `--amber-l` | `#2a2010` |
| `--sage` | `#4a8a5e` |
| `--sage-l` | `#1a2a1e` |
| `--coral` | `#d45a40` |
| `--coral-l` | `#2a1510` |
| `--violet` | `#7060b0` |
| `--violet-l` | `#1e1830` |

**Build rule:** dark palette is implemented in `:root[data-theme="dark"]` token override. UXPilot prompts target light. Theme toggle deferred.

---

## 5. Spacing & layout primitives

| Token | Value | Use |
|---|---|---|
| `--space-1` | 4px | Inline gap, badge inner padding |
| `--space-2` | 8px | Stack rhythm inside cards |
| `--space-3` | 12px | Card internal padding (compact) |
| `--space-4` | 16px | Card internal padding (default) |
| `--space-5` | 24px | Section gap |
| `--space-6` | 32px | Page section break |
| `--space-7` | 48px | Major rail break / page top |
| `--space-8` | 80px | Hero / footer breathing room |

**Border radius:** `--r-sm 3px` (chips, inputs) · `--r-md 4px` (cards, modules) · `--r-lg 8px` (modals, panels). Never higher than 8px.
**Hairlines:** 1px `--paper3`. Use as section dividers, card borders, table rules.
**Elevation:** maximum one step. Modals: `0 6px 24px rgba(14,13,11,0.08)`. Cards: no shadow — borders only.

---

## 6. Layout shells (full spec in `UXPILOT_07_layout_shells.md`)

| Shell | Max content width | Sidebar | Wide-mode extras |
|---|---|---|---|
| **Fixed** (default) | 960px centered | Right rail 320px (collapsible to 0 below 1024px) | — |
| **Wide** | edge-to-edge with 32px gutters | Right rail 360px + pull-down extras | intellid_graph · appreciated_scale · ai_usage_heatmap (when not in main) · trending_ideas |

**Toggle:** persists in localStorage key `eaiou.shell`. Header chrome contains an icon-toggle (┃▣ ┃ vs ▣▣▣) + label "fixed | wide".

**Header (every page):** logo eaiou (Spectral 300, 24pt) · primary nav · search (mono input) · observer-projection indicator (`HUMINT` chip in mono uppercase, click to view UNKINT for those with ACL) · auth widget. 64px tall, 1px bottom border `--paper3`, surface bg.

**Footer (every page):** dense link grid in mono 11pt. About · Doctrine · ORCID · REST API · Status · Privacy · Sealed Audit (admin only). Background `--paper2`, top border 1px `--paper3`. 48px tall.

---

## 7. Module schema (full per-module specs in `UXPILOT_06_modules.md`)

Every module renders as a card with this structure:

```
┌─────────────────────────────────────────┐
│ [mono uppercase 11pt] MODULE NAME       │  ← header bar, --paper2 bg, 8px tall
├─────────────────────────────────────────┤
│                                         │
│   [Spectral or dataviz body]            │  ← content area, --surface bg
│                                         │
├─────────────────────────────────────────┤
│ [mono 10pt --ink3] count · view all →   │  ← footer link, optional
└─────────────────────────────────────────┘
```

- Card border: 1px `--paper3`, radius 4px.
- Header label: JetBrains Mono 11pt UPPERCASE, letterspacing 0.06em, `--ink2`.
- Body padding: 16px.
- Module width: fills its rail column; never explicit width inside spec.
- Collapsible: header click toggles content. Persistent in localStorage per module.

---

## 8. Badge schema

Badges are inline pills, mono 10pt, height 18px, padding 0 6px, radius 3px.

| Badge | Background | Text color | Border | Use |
|---|---|---|---|---|
| AI-Logged | `--violet-l` | `--violet` | 1px `--violet` 20%a | `ai_used = true` |
| Open Reports | `--river-ll` | `--river` | 1px `--river` 20%a | `or_enabled = true` |
| ORCID | `--surface` | `--ink` | 1px `--orcid` | author has linked ORCID |
| Sealed | `--paper2` | `--ink2` | 1px `--paper3` | `submission_sealed_hash present` |
| Transparency | `--sage-l` | `--sage` | 1px `--sage` 20%a | `transp_complete = true` |
| Un Scientific | `--coral-l` | `--coral` | 1px `--coral` 20%a | `unsci_active = true` |
| AI-Hybrid | `--violet-l` | `--violet` | 1px `--violet` 20%a | `authorship_mode = hybrid` |
| Replication | `--paper2` | `--ink2` | 1px `--paper3` | `rs:Replication` present |
| Null Result | `--paper2` | `--ink2` | 1px `--paper3` | `rs:NullResult` present |

Tag pills (`rs:*`) follow the same shape, mono 10pt lowercase, prefix `rs:` is dimmed `--ink3`, suffix is full ink. Click → tag landing page.

Workflow state chips: same shape, slightly larger (mono 11pt). Color encoding:
- `draft` → `--paper2 / --ink2`
- `submitted` → `--river-ll / --river`
- `under_review` → `--amber-l / --amber`
- `revisions_requested` → `--amber-l / --amber` with dashed border
- `decision_pending` → `--violet-l / --violet`
- `accepted` → `--sage-l / --sage`
- `published` → `--sage / --paper` (filled, sage bg, paper text)
- `archived` → `--ink3 / --paper`
- `rejected` → `--coral-l / --coral`

---

## 9. Per-page prompt schema (all `UXPILOT_01..05` files use this)

Every page entry follows this structure verbatim. UXPilot can be fed any single block as a self-contained prompt.

```
### Page: <name>
**Role / ACL:** <Public | eaiou_Author | eaiou_Reviewer | eaiou_Editor | eaiou_EIC | eaiou_Admin | eaiou_APIClient>
**URL:** </path>
**Joomla source:** <article | menu item | com_eaiou view | plugin endpoint>
**Layout shell:** <fixed | wide-default | both — defer to UXPILOT_07>
**Modules (right rail):** <comma list — defer to UXPILOT_06>
**Wide-mode pull-down extras:** <comma list>
**Typography:** Spectral content + JetBrains Mono metadata (defer to UXPILOT_00 §2)
**Palette:** light; tokens — `--ink`, `--paper`, `--river`, `--amber`, `--sage`, `--coral`, `--violet` (defer to UXPILOT_00 §3)

**Page blocks (top → bottom):**
1. <block name> — <type, content, sample copy, dataviz spec>
2. ...

**Tags / badges rendered:** <comma list of badge tokens from UXPILOT_00 §8>
**States:** loading | empty | error | success | sealed (specify what each shows)
**Sample data (max 2 sentences):** <one or two illustrative items>
**Interactions:** <hover, click, modal, form, sortable, filter, drag>
**Observer projection note:** <HUMINT default surface vs UNKINT differential — what fields appear/disappear>
**ACL governance unlock note:** <if any sealed temporal data is reachable here, how it's gated>
```

---

## 10. Reconciliation table — eaiou (FastAPI/Joomla) vs eaiou-admin (Laravel)

| Surface | eaiou canonical | eaiou-admin current | Resolution rule |
|---|---|---|---|
| Typography | Spectral + JetBrains Mono | DM Sans (Tailwind extend) | Standardize on Spectral + Mono. DM Sans deprecated; Tailwind extend should add Spectral as `font-serif` + JetBrains Mono as `font-mono`. |
| Primary palette | 7-hue token set (river/amber/sage/coral/violet) | 5-stop primary grayscale | Adopt eaiou tokens wholesale. Replace Tailwind primary 50–900 with `var(--river-*)` etc. |
| CSS variables | `--ink, --paper, --river, ...` (19 tokens) | `--ds-bg, --ds-surface, --ds-border, --ds-ink-1/2/3` (6 tokens) | Migrate eaiou-admin to canonical 19-token set; keep `--ds-*` aliases for legacy view files. |
| Spacing | 4px grid (Tailwind default) | 4px grid (Tailwind default) | Already aligned. |
| Border radius | 3 / 4 / 8px | Tailwind `rounded-md`, `rounded-lg` | Map: `rounded-sm` → 3px, `rounded-md` → 4px, `rounded-lg` → 8px. |
| Component naming | `.module-panel`, `.badge-*`, `.tag-pill` | Blade components (`primary-button`, `dropdown`, `modal`, `nav-link`) | Keep Blade names. Add CSS class equivalents for Jinja/standalone HTML. Document mapping inline in `UXPILOT_07`. |
| Page chrome | Joomla-driven nav + plugin-rendered chrome | Laravel Breeze nav + dropdown | Migrate Laravel chrome to match Joomla shell semantics: same logo placement, same observer-projection indicator, same fixed/wide toggle. |

**Out of scope for these prompts:** Tailwind config migration. Flagged here, executed in a follow-up after UXPilot mockups land.

---

## 11. Citation rules

- `UXPILOT_00` is the only file that defines tokens, schemas, and shells. Every other file says "defer to `UXPILOT_00 §<n>`" rather than restating.
- `UXPILOT_PROMPT_EAIOU.md` is the only file that defines IntelliD, TAGIT, observer projection, and temporal blindness. Per-page prompts cite it: "Apply observer projection per `UXPILOT_PROMPT_EAIOU.md §Observer-Dependent Presentation`."
- Modules are defined once in `UXPILOT_06_modules.md`. Page prompts list module names; UXPilot fetches the spec from `UXPILOT_06`.

---

## 12. Acceptance criteria for any UXPilot output generated from these prompts

A mockup is acceptable when:

1. Spectral renders for every body and headline. JetBrains Mono renders for every metadata field, ID, tag, and badge.
2. Backgrounds use `--paper` (page) and `--surface` (cards) — never flat color blocks.
3. River-blue `--river` is the dominant accent. Amber / sage / coral / violet appear only in badges, tags, and dataviz segments.
4. No timestamps in HUMINT view. No "posted X ago" copy. No date columns in tables (unless behind explicit governance unlock).
5. Sort indicators show "by q_signal" — never "by date".
6. Author identity rendered as IntelliD (e.g., `INT-9F2A`) in mono, never as a name string in HUMINT view.
7. Hairline borders (1px `--paper3`). No drop shadows on cards.
8. Dataviz: at least one chart per dashboard page. Color encoding follows the palette table in §8.
9. Both fixed and wide layouts are coherent. Wide pull-down modules don't overflow.
10. Footer carries the observer-projection chip and the sealed-audit link (admin only).

---

## 13. Open items (flagged for Eric)

- Theme toggle: when does dark mode get built? (Tokens are ready; mockups are not.)
- Joomla template integration: which HelixUltimate template positions does each module bind to? (Spec in `UXPILOT_07` references positions but final mapping waits on Joomla template install verification.)
- ORCID brand color (`--orcid #a6ce39`): confirm exact ORCID brand-spec value (verified once, OK to lock).
- Dataviz library choice: light wrapper around D3 vs Chart.js vs raw SVG. Mockups assume raw SVG — UXPilot will render shapes.
