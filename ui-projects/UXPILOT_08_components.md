# UXPILOT_08 — atomic components

**Tokens, schemas, shells:** see `UXPILOT_00_design_system.md`.
**Module shell:** `UXPILOT_00 §7`. **Badge schema:** `UXPILOT_00 §8`. **Chrome:** `UXPILOT_07`.

This file specifies every atomic component referenced across `UXPILOT_01..05` (pages), `UXPILOT_06` (modules), and `UXPILOT_07` (chrome). Per-page prompts cite component names from this file rather than restating sizes, paddings, or states.

Components below render in light mode. Dark tokens defined in `UXPILOT_00 §4`; dark variants follow the same geometry, with `--ink/paper/surface` swapped per token.

---

## 1. Buttons

All buttons are mono UPPERCASE, 11pt, letterspacing 0.06em, height 32px (default) or 28px (compact) or 40px (hero). Padding 0 14px (default), 0 10px (compact), 0 20px (hero). Radius 3px. Focus ring 2px `--river-ll` outer.

| Variant | Background | Text | Border | Hover | Active | Disabled |
|---|---|---|---|---|---|---|
| `btn-primary` | `--river` | `--paper` | none | bg → `--river-l` | bg → `--ink` | bg `--paper3`, text `--ink3` |
| `btn-outline` | transparent | `--river` | 1px `--river` | bg `--river-ll` | border `--ink` | border `--paper3`, text `--ink3` |
| `btn-ghost` | transparent | `--ink2` | none | bg `--paper2` | bg `--paper3` | text `--ink3` |
| `btn-danger` | `--coral` | `--paper` | none | bg darken 8% | bg `--ink` | bg `--paper3` |
| `btn-icon` | transparent | `--ink2` | none | bg `--paper2` | bg `--paper3` | text `--ink3` |

**Icon-only:** square 32×32px (default), single mono glyph centered, no text. Aria-label required.
**Icon + label:** glyph 14px left, 8px gap, label right; total padding 0 12px.
**Loading state:** label replaced by mono `…` spinner; cursor `wait`; click suppressed; no spinner image (no PNGs).

**Acceptance:**
- Never two filled `--river` primary buttons in the same view zone — only one.
- Hero buttons (40px) appear only in hero bands, modal footers, and submission wizard CTA. Never inside cards or modules.
- Group spacing: 8px between adjacent buttons. Vertical button stacks not allowed except in modals.

---

## 2. Inputs

Mono 13pt input text, 1px `--paper3` border, radius 3px, height 32px (default) or 40px (form), bg `--paper`, placeholder `--ink3`. Focus ring 2px `--river-ll` + 1px `--river` border swap.

| Variant | Type | Notes |
|---|---|---|
| `input-text` | Spectral 16pt content text | Used for prose fields (title, abstract, comment). |
| `input-mono` | JetBrains Mono 13pt | Used for IDs, tags, search, code. Default for filters. |
| `input-search` | mono 13pt + magnifier glyph left, clear glyph right | Header search uses this. |
| `textarea` | Spectral 16pt, line-height 1.6 | Min 4 rows, vertical resize only. Manuscript fields use 12 rows. |
| `select` | mono 13pt + chevron-down `--ink3` right | Native menu fallback; styled menu uses dropdown component. |
| `multiselect` | chip wrap inside input shell | Adds chips on Enter; backspace removes last. |
| `checkbox` | 16×16 square, 1px `--paper3` border, `--river` fill on check | Mono 13pt label right, 8px gap. |
| `radio` | 16×16 circle, same colors as checkbox | Group radio vertical 8px gap. |
| `toggle` | 36×20 pill, knob 16×16 | Off: bg `--paper2`. On: bg `--river`. Animation 120ms ease. |
| `slider` | 4px track `--paper3`, fill `--river`, thumb 14×14 `--surface` border 1px `--river` | Mono 11pt value indicator above thumb. |
| `file` | dashed 1px `--paper3` border, mono 13pt prompt "drop or click — pdf, max 50 MB" | Hover: border `--river`. |

**Label:** mono 11pt UPPERCASE tracking-wide `--ink2` above input, 6px gap.
**Helper text:** mono 11pt `--ink3` below input, 4px gap. Errors: `--coral`, with mono prefix `error · ` then message in Spectral 13pt.
**Required marker:** mono `·` in `--coral` after the label.

**Acceptance:**
- No floating labels. No inside-input labels.
- No combined "label-as-placeholder" inputs — every field has a visible mono label above it.
- Spectral input only for prose; mono input for everything else.

---

## 3. Chips & pills

Three families. All radius 3px, height 18px (badge), 24px (chip), 28px (filter-chip).

### 3.1 Badges
Defined in `UXPILOT_00 §8`. Status, role, governance markers. Static — no click behavior except on the AI-Logged badge (deep-links to ai_session_log tab on parent paper).

### 3.2 Tag pills (`rs:*`)
- Mono 10pt lowercase, height 18px, padding 0 6px.
- Prefix `rs:` rendered `--ink3`; suffix rendered `--ink`.
- Background `--surface`, border 1px `--paper3`.
- Hover: border `--river`, cursor pointer.
- Click → `/tag/{tag-name}`.

### 3.3 Filter chips
Used in filter rails (`/papers`, `/discover/*`, `/reviewer/queue`, `/editorial/papers`, admin manager rails).

- Mono 11pt UPPERCASE, height 28px, padding 0 12px.
- Inactive: bg `--surface`, border 1px `--paper3`, text `--ink2`.
- Active: bg `--river-ll`, border 1px `--river`, text `--river`.
- Hover (inactive): bg `--paper2`. Hover (active): bg shifted `--river-ll` 80%.
- Multi-select group: chip cluster with 6px gap, wraps; clear-all link mono 10pt `--ink3` "clear (N)".

**Workflow state chip:** see `UXPILOT_00 §8` (height 24px variant). Used in tables, paper masthead, list rows.

**IntelliD pill:** mono 11pt, height 18px, padding 0 6px, bg `--surface`, border 1px `--paper3`. Format `INT-XXXX`. Hover: border `--river`. Click → user profile (ACL-gated).

---

## 4. Tabs

Horizontal tab strip. 40px tall, `--surface` bg, 1px bottom `--paper3` baseline.

- Tab item: mono 12pt UPPERCASE tracking-wide, padding 0 16px, height 40px, color `--ink2`.
- Active: text `--ink`, 2px bottom border `--river` (overlays the baseline).
- Hover: text `--ink`, 1px bottom hairline `--ink3`.
- Disabled: text `--ink3`, no hover.
- Count suffix (optional): mono 10pt `--ink3` after label, e.g., `MANUSCRIPT (3)`.

**Vertical tabs (used in admin manager detail views):** 32px tall items, left-rail 1px `--paper3` border, active item 2px left border `--river`.

**Acceptance:**
- Tab content area starts 16px below the strip.
- Tab change does not trigger full page reload (alpine + fetch).
- URL hash reflects active tab: `#manuscript`, `#sources`, `#ai-usage`, `#open-reports`, `#attribution`.

---

## 5. Tables (admin list-manager pattern)

Used by every `view=*` admin page in `UXPILOT_05`. Spec consolidated here.

**Frame:** 1px `--paper3` border, radius 4px, bg `--surface`. Tables overflow horizontally inside the frame; sticky header.

**Header row:** 36px tall, bg `--paper2`, 1px bottom `--paper3`. Mono 11pt UPPERCASE tracking-wide `--ink2`. Sortable columns show a 6px chevron right; active sort `--river`.

**Body row:** 48px tall (default) or 56px (with badges/sparkline). Bg `--surface`. 1px bottom `--paper3` between rows. Cells padded 12px horizontal, 8px vertical.
- Mono columns: IDs, hashes, counts, scores. JetBrains Mono 13pt.
- Spectral columns: titles, names, descriptions. Spectral 14pt.
- Hover row: bg `--paper2` (subtle), no border change. Cursor pointer if row links.
- Selected row (with row-checkbox): bg `--river-ll`.

**Sticky-left column:** title or primary identifier; 1px right `--paper3`, bg inherits row.

**Footer row:** 40px tall, bg `--paper2`, 1px top `--paper3`. Pagination right (component §10). Selection summary left, mono 11pt: `2 selected · clear`.

**Cell types:**
| Type | Render |
|---|---|
| ID | mono 13pt `--ink2` |
| Title | Spectral 14pt link `--ink` |
| State chip | workflow chip (see 00 §8) |
| Q score | mono 13pt + 60×4 q bar `--river` right of value |
| Count | mono 13pt right-aligned |
| Sparkline | inline 60×16 SVG, see `UXPILOT_09` |
| Action menu | `…` icon-button right; opens dropdown |
| Tags | wrap up to 3 chips; "+N" overflow chip |

**No date columns.** Sealed-time visible only when UNKINT projection active (renders mono 13pt with 1px `--coral` left border on cell).

**Empty state:** centered Spectral 14pt italic `--ink3` "no rows match" + reset-filters link mono 11pt `--river`. 200px min height.

**Loading state:** 8 skeleton rows (see §15).

---

## 6. Modals

Modal shell:
- Centered, max-width 640px (default), 480px (compact confirm), 880px (wide form).
- Bg `--surface`, radius 8px, shadow `0 6px 24px rgba(14,13,11,0.08)`.
- Backdrop bg `rgba(14,13,11,0.45)`.
- Padding 0 (header/body/footer have own padding).

**Modal header:** 64px tall, padding 24px, 1px bottom `--paper3`. Title Spectral 600 22pt `--ink` left; close icon-button right.
**Modal body:** padding 24px. Spectral 16pt content; mono for IDs / fields. Max body height `70vh`, scroll inside.
**Modal footer:** 64px tall, padding 16px 24px, 1px top `--paper3`, bg `--paper2`. Buttons right-aligned, gap 8px. Primary right-most.

**Variants:**
- `modal-confirm` (compact, 480px): single message Spectral 16pt, two buttons (cancel ghost, confirm primary or danger).
- `modal-form` (default, 640px): scrollable form, primary submit.
- `modal-wide` (880px): used for governance unlock justification (UNKINT activation, see `UXPILOT_07 §7`).

**Open animation:** 120ms ease-in opacity 0 → 1; modal scale 0.98 → 1.0. No translate.
**Close:** ESC, backdrop click, close button. Form modals confirm before close if dirty.

**Acceptance:**
- Never nested modals. Never modal-on-modal.
- TAGIT session lock and UNKINT activation are full modals — never dropdowns or popovers.

---

## 7. Drawers (off-canvas)

Slide-in panel from edge. Used for: mobile primary nav, paper-detail tab content on mobile, admin filter rails (when collapsed), TAGIT session structural map (mobile), submit wizard preview.

- Width 360px (right side default) or 320px (left side, mobile nav). Full-height.
- Bg `--surface`, 1px edge border `--paper3`, no radius (flush to edge).
- Header 56px tall, 1px bottom `--paper3`: mono 11pt UPPERCASE label left, close icon-button right.
- Body padding 16px, scroll vertical.
- Backdrop bg `rgba(14,13,11,0.30)` (lighter than modal).

**Open animation:** 200ms ease-out translateX `-100% → 0` (or `100% → 0` for right-side).
**Close:** ESC, backdrop click, close button, swipe (mobile only).

---

## 8. Toasts

Transient bottom-right notification. Stack up to 3.

- Width 360px, padding 12px 16px, radius 4px, 1px border, bg per variant, shadow `0 6px 24px rgba(14,13,11,0.08)`.
- Bottom 24px, right 24px, gap 8px between stacked toasts.
- Icon glyph 14px left, content right (Spectral 14pt title + mono 11pt detail).
- Close icon-button top-right (12×12).

| Variant | Bg | Border | Icon |
|---|---|---|---|
| `toast-info` | `--river-ll` | `--river` | river-curve glyph |
| `toast-success` | `--sage-l` | `--sage` | check glyph |
| `toast-warn` | `--amber-l` | `--amber` | bang glyph |
| `toast-error` | `--coral-l` | `--coral` | x glyph |

**Lifecycle:** appear 200ms ease-out translateY 8 → 0; dwell 5s (info/success), 8s (warn), persistent (error — manual dismiss). Hover pauses dwell timer.

**Acceptance:**
- Toasts never carry calls-to-action that change global state. For confirm flows, use modals.
- "UNKINT projection expired. HUMINT view restored." renders as `toast-info`.

---

## 9. Dropdowns & menus

Used for: header `Discover ▾` and role nav (covered in `UXPILOT_07 §3.2`); table action menus; auth widget; `…` overflow menus across cards.

**Menu shell:**
- Bg `--surface`, 1px `--paper3` border, radius 4px, shadow `0 6px 24px rgba(14,13,11,0.08)`.
- Min-width 180px. Padding 4px 0.
- Open below trigger by default; flip up if not enough space.

**Menu item:**
- Height 32px, padding 0 12px, mono 12pt `--ink2`.
- Hover: bg `--paper2`, text `--ink`.
- Active/selected: bg `--river-ll`, text `--river`, with mono check glyph right.
- Disabled: text `--ink3`, no hover.
- Destructive item: text `--coral`, hover bg `--coral-l`.

**Section divider:** 1px `--paper3`, 4px vertical margin.
**Section label:** mono 10pt UPPERCASE tracking-wide `--ink3`, padding 4px 12px.

**Trigger styles:**
- Header nav `▾`: glyph mono `--ink3` after label.
- Action `…`: icon-button square 28×28.
- Auth IntelliD pill: full pill clickable with mono `▾` glyph right.

---

## 10. Pagination

Used at: `/papers`, `/discover/*`, `/reviewer/queue`, `/editorial/papers`, every admin manager view, every list module footer with view-all.

- Right-aligned in table footer or list footer. Padding 8px 0.
- Mono 11pt: `page 1 of 47`. `--ink3`.
- Prev / Next chevrons: icon-buttons 28×28, glyph `--river`. Disabled state: glyph `--paper3`.
- Optional jump-to-page input: mono input 60px wide, height 28px. Submit on Enter.

**No page-size selector.** Page size locked at 20 (cards) or 50 (table rows). Doctrine: discovery scope is fixed to prevent dragnet behavior.

**Infinite scroll:** not used in eaiou. Pagination is the only paging primitive (per doctrine — every list is bounded).

---

## 11. Accordions

Used for: paper detail tab inner sections, admin Settings panes, doctrine page sections.

- Header 40px tall, 1px bottom `--paper3`, padding 0 16px. Mono 12pt UPPERCASE tracking-wide `--ink2` left; chevron-right glyph `--ink3` rotates 90° when open.
- Body padding 16px, bg `--surface`, 1px top `--paper3` (already there from header).
- Hover header: bg `--paper2`, chevron `--ink`.
- Open animation: 160ms ease-out height 0 → auto.

**Group:** vertically stacked accordions form a panel; first header has 1px top `--paper3`. Persist open state in localStorage per `(user, page, accordion-id)`.

---

## 12. Steppers

Used for submission wizard (`UXPILOT_02 §Submit wizard`).

- Horizontal layout, full-width, 56px tall, bg `--paper2`, 1px bottom `--paper3`.
- Each step: 32×32 circle (mono 13pt step number) + label (Spectral 14pt right of circle, 8px gap).
- 1px `--paper3` connector between steps, 16px gap each side.

**States per step:**
| State | Circle bg | Circle border | Label color |
|---|---|---|---|
| pending | `--paper` | 1px `--paper3` | `--ink3` |
| active | `--surface` | 2px `--river` | `--ink` |
| complete | `--river` | none | `--ink2` (with mono check glyph in circle, `--paper`) |
| error | `--coral-l` | 1px `--coral` | `--coral` |

**Mobile:** collapses to "step 2 of 5 — Sources" mono 13pt with 4px progress bar `--river` below. Tap label opens drawer of all steps.

---

## 13. Tooltips

Floating mono hint. Used widely (q_signal value, IntelliD on hover, sort doctrine note, etc.).

- Bg `--ink` (yes — inverted), text `--paper`, padding 6px 10px, radius 3px, mono 11pt.
- Max width 240px. Wraps at edges.
- Arrow 6×6 triangle pointing to trigger.
- Delay open 400ms, close 100ms. No animation beyond opacity 0 → 1 (120ms).

**Variants:**
- `tooltip-info` (default — inverted ink/paper).
- `tooltip-warn` (`--amber` bg, `--ink` text). Used for doctrine reminders ("Sort by date is governance-locked").
- `tooltip-error` (`--coral` bg, `--paper` text). Used for input-level errors that don't have inline space.

**Acceptance:**
- Tooltips never carry interactive elements (no buttons, no links inside).
- For interactive content, use popovers (not specified separately — modal or dropdown handles those cases).

---

## 14. Avatars

**Avatars do not exist in eaiou.**

Identity surfaces use the IntelliD pill (mono `INT-XXXX`) only. ORCID badge is the one exception — it is a 14×14 mono glyph in `--orcid` next to a name string but only on author profile pages where ORCID linkage is explicit.

This is intentional doctrine — see `UXPILOT_PROMPT_EAIOU.md §Observer-Dependent Presentation`. UXPilot mockups must render no profile photos, no initials circles, no avatar placeholders. If a card or row needs a "by" indicator, render the IntelliD pill.

---

## 15. Skeletons

Loading placeholders. Used across every page that fetches.

- Bg `--paper2`. No animation (no shimmer, no pulse). Doctrine: skeletons are honest about absence — they don't perform energy.
- Radius matches the element they replace (3px for chips, 4px for cards, 18px for IntelliD pills).
- Heights mirror the element being replaced exactly.

**Common skeleton shapes:**
| Skeleton | Shape |
|---|---|
| Card row (paper) | 96px × 100% block |
| Card row (queue) | 64px × 100% |
| Chip | 18px × 64px |
| Sparkline | 16px × 60px |
| Table row | 48px × 100%, with 4 inner blocks at column widths |
| Module body | 3 stacked rows of 36px each, with 8px gap |

**Acceptance:**
- Skeletons render only during initial fetch — not on tab switches or filter changes (those use a 200ms opacity dim instead).
- Skeleton count matches expected result count where possible (5 latest papers → 5 skeletons; 8 dashboard cards → 8 skeletons).

---

## 16. Icons

Mono icon system — not a font, not an icon library. Every icon is a single-color SVG path rendered inline at 14px (default) or 16px (header/footer chrome) or 12px (inline indicators).

**Color rule:** every icon inherits `currentColor`. Default `--ink2`. In active state, `--river`. In coral state (errors, danger), `--coral`.

**Icon catalog (used across UXPilot prompts):**

| Token | Glyph | Use |
|---|---|---|
| `icon-river-curve` | wavy line | Brand glyph (header) |
| `icon-search` | magnifier | Header search input |
| `icon-x` | crossed lines | Close (modals, drawers, chips) |
| `icon-check` | check | Form success, complete steppers |
| `icon-bang` | exclamation | Warnings |
| `icon-info` | i circle | Info |
| `icon-chevron-right` | > | Pagination, accordions, breadcrumbs |
| `icon-chevron-down` | v | Dropdown triggers |
| `icon-chevron-up` | ^ | Sort indicator |
| `icon-dots-h` | ⋯ | Action menu trigger |
| `icon-arrow-right` | → | Footer "view all" links |
| `icon-shell-fixed` | ┃▣ ┃ | Shell toggle (fixed) |
| `icon-shell-wide` | ▣ ▣ ▣ | Shell toggle (wide) |
| `icon-lock` | padlock | Sealed badges, governance unlocks |
| `icon-eye` | eye | Observer projection chip |
| `icon-orcid` | orcid roundel | ORCID badge (only place `--orcid` is used) |

**Acceptance:**
- No emoji. Never. (Aesthetic + accessibility doctrine.)
- No filled-with-color icons. All icons stroke-only or 1-bit fill in `currentColor`.
- No icon-only buttons in module bodies (always paired with a label nearby — except `icon-x` close).

---

## 17. Banners (page-level)

Defined in `UXPILOT_07 §10`. Briefly recapped here for component completeness:

- Full-width, 4px left border in variant accent, padding 12px 24px.
- Bg in variant `--*-l` wash. Text Spectral 14pt `--ink`.
- Right-side dismiss icon-button (`icon-x`) where dismissable.
- Stack ≤ 3; overflow chip "+N more".

See §10 of `UXPILOT_07` for full variant table.

---

## 18. Code blocks (manuscript content + USO record viewer)

For: paper detail manuscript tab, USO record read-only page, doctrine page code samples.

- Bg `--paper2`, 1px `--paper3` border, radius 4px, padding 12px 16px.
- JetBrains Mono 13pt `--ink`, line-height 1.5.
- Pre-wrap, horizontal scroll within the frame.
- Optional copy icon-button top-right; mono 10pt label "copy" in tooltip on hover.
- Optional language label top-left mono 10pt UPPERCASE `--ink3`.

**Inline code** (within prose): JetBrains Mono 14pt `--ink`, bg `--paper2`, padding 1px 4px, radius 2px.

---

## 19. Card variants

Beyond the module shell (`UXPILOT_00 §7`):

| Variant | Use | Differences from module shell |
|---|---|---|
| `card-paper` (river-band, list) | Paper list rows on `/`, `/papers`, `/search`, `/tag/{name}` | No header bar; padding 16px direct. 1px border `--paper3`, hover border `--ink3`. |
| `card-kpi` (dashboard tile) | Editorial dashboard 6-card grid | Header bar mono 10pt UPPERCASE `--ink3`; body 80px tall with single big-number Spectral 36pt + sparkline below. |
| `card-stat` (compact tile) | Admin manager footer stat strip | 64px tall, single mono number + label below. No header bar. |
| `card-confirm` (modal-confirm body) | Inside `modal-confirm` | No frame (modal provides). Spectral 16pt centered. |
| `card-empty` (empty state) | Inside table or list when empty | Centered Spectral 14pt italic + reset link. 200px min height. |

Cards inherit the same hairline aesthetic. No drop shadows except on modals (covered in §6) and toasts (§8).

---

## 20. Form pattern (submission wizard, login, register, comment forms)

Used as the spine for `/submit`, `/login`, `/register`, `/forgot-password`, `/reset-password`, and any inline comment form.

**Form frame:**
- Centered column 480px (auth pages), 720px (submit wizard step body), full-width within drawer (drawer forms).
- Section gap 24px between fieldsets.
- Fieldset header: mono 11pt UPPERCASE tracking-wide `--ink2`, 1px bottom `--paper3`, padding 0 0 8px 0.

**Field stack:** label (mono 11pt UPPERCASE) → input → helper / error (mono 11pt). 12px gap between fields.

**Form footer:**
- 1px top `--paper3`.
- Padding 24px 0.
- Buttons right-aligned. Primary right-most. Secondary "save draft" ghost left.
- For wizard: "← back" ghost left, "next →" primary right. "Cancel" link mono 11pt far-left.

**Validation:**
- Inline on blur; not on every keystroke.
- Submit attempts with errors: scroll to first error field; focus it; render coral toast "1 field needs your attention".
- Errors render below input as mono 11pt `--coral`.

**Auth-specific copy:**
- Login: "sign in to eaiou" Spectral 300 36pt centered. Helper mono "sealed timestamps stay sealed. you stay HUMINT."
- Register: "claim your IntelliD" Spectral 300 36pt centered. Helper "your IntelliD is generated at submission and bound to your email. ORCID optional."
- Forgot: minimal — email input + submit. Confirmation Spectral 16pt italic.

---

## 21. Inline data renderers (single-line patterns)

Reusable single-line metadata renderers used inside cards, table rows, and module bodies.

| Renderer | Format |
|---|---|
| `q-bar-inline` | Mono `0.847` + 60×4 q bar `--river` to right (gap 6px). |
| `q-bar-with-rank` | `0.847 · #4` mono with bar to right. |
| `intellid-list` | mono `INT-9F2A · INT-A831 · INT-7C04` — middot separator `--ink3`. |
| `tag-cluster` | wrap of tag pills, max 3 visible, "+N" overflow chip. |
| `state-row` | workflow state chip + 2-3 badge chips inline, gap 6px. |
| `cycle-stamp` | mono 10pt UPPERCASE `--ink3` `cycle q4 · doctrine v2.0`. Used in chrome footer + capstone. |
| `relative-bar` | 7-segment mono `▣▣▣▢▢▢▢` for relative-window indicators. Sage / amber / coral by position. |
| `count-detail` | mono `47 papers · 312 sessions` — middot separator `--ink3`. |

**Acceptance:**
- These never carry their own borders or backgrounds — they live inside other components.
- Width: never explicit; always inherits parent.

---

## 22. Component-to-page reference matrix

Summary of which components appear on which pages. Use this to check coverage when generating a mockup.

| Page family | Buttons | Inputs | Tabs | Tables | Modals | Drawers | Steppers | Charts |
|---|---|---|---|---|---|---|---|---|
| Public list (`/`, `/papers`, `/search`) | filter chips · ghost · pagination | search · filter rail | — | — | — | mobile-nav | — | sparklines, q-bars |
| Paper detail (`/paper/{id}`) | secondary CTAs · share · open report | — | manuscript / sources / ai / open / attribution | — | governance unlock · share | mobile-tab content | — | q-bar, ai-heatmap mini, intellid-graph |
| Author (`/mypapers`, `/submit`) | primary "submit" · save draft ghost | full form | tabs on workspace | — | confirm · export-context | submit-wizard mobile | submit wizard | sparklines, q-bar |
| Reviewer (`/reviewer/*`) | accept · decline · submit-review · TAGIT-ASK · TAGIT-GOBACK | rubric inputs · comment forms | criteria tabs · session log tab | queue table | confirm · TAGIT-session | structural-map (mobile) | — | rubric scale, time-bar |
| Editor (`/editorial/*`) | assign · decide · escalate · primary | filter rail · decide form | papers / decisions tabs | papers table · decision history | reviewer-assignment · decision-confirm | filter rail (mobile) | — | editor dashboard sparklines, gap_map |
| Admin (com_eaiou) | manager actions · primary save | filter rails · settings forms | settings tabs · session detail tabs | every manager view | confirm · sealed-audit unlock | filter rail collapse | — | KPI grid, ai-heatmap, gap_map, intellid-graph |
| Auth pages | primary signin · register · ghost cancel | minimal form | — | — | — | — | — | — |
| Doctrine, About | — | — | section accordions | — | — | — | — | — |

---

## 23. Acceptance criteria for any UXPilot mockup using these components

1. Buttons: no two filled `--river` primaries side-by-side. Hero size only in hero bands and modal footers.
2. Inputs: every field has a visible mono label above it. No floating labels.
3. Tables: no date columns in HUMINT view. UNKINT-only fields render with 1px `--coral` left border.
4. Modals: never nested. ESC and backdrop click both close.
5. Drawers: edge-flush, no radius. Slide animation 200ms ease-out.
6. Toasts: top of stack ≤ 3. Errors persistent (manual dismiss).
7. Tooltips: never carry interactive elements.
8. Avatars: never. IntelliD pill only.
9. Skeletons: no animation. No shimmer. No pulse.
10. Icons: no emoji, no filled glyphs. `currentColor` only.
11. Pagination: locked page size. No page-size selector. No infinite scroll.
12. Steppers: only on submit wizard.

---

## 24. Citation rules (echoing `UXPILOT_00 §11`)

- Per-page prompts in `UXPILOT_01..05` cite components by name from this file: "Filter rail uses `filter-chip` group per `UXPILOT_08 §3.3`."
- Module bodies in `UXPILOT_06` cite renderers from this file: "footer link uses `count-detail` renderer per `UXPILOT_08 §21`."
- Chrome in `UXPILOT_07` cites buttons / icons from this file: "auth widget uses `btn-outline` and `btn-primary` per `UXPILOT_08 §1`."

---

## End of `UXPILOT_08_components.md`

Next file: `UXPILOT_09_dataviz.md` — chart geometry per visualization (sparkline, segmented bar, heatmap, network graph, scale bars, entropy trace).
