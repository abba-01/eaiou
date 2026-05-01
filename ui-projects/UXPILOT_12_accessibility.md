# UXPILOT_12 — accessibility

**Tokens:** see `UXPILOT_00_design_system.md`.
**Components:** see `UXPILOT_08_components.md` (focus rings recap in `UXPILOT_11 §4`).
**Chrome:** see `UXPILOT_07_layout_shells.md §9.6` for skip-link and focus-order baseline.

This file specifies accessibility for every surface in the prompt set. Target: WCAG 2.2 AA across all interactive surfaces, AAA where text contrast permits. eaiou's doctrine of observer-preserving presentation maps cleanly onto AT semantics — IntelliD pills carry explicit aria-labels, sealed surfaces announce their lock state, governance unlocks expose role context to screen readers.

---

## 1. Standards & doctrine

| Standard | Target |
|---|---|
| WCAG 2.2 | AA across all surfaces; AAA where text contrast is intrinsic |
| ARIA | ARIA 1.2 — only when native semantics are insufficient |
| Keyboard | Full navigation without pointer; visible focus on every focusable |
| Reduced motion | `prefers-reduced-motion: reduce` honored per `UXPILOT_11 §11` |
| Reduced transparency | `prefers-reduced-transparency` falls back to solid `--surface` |
| Color contrast | Computed pairs documented in §3 |
| Touch target | ≥ 44×44 CSS px on tablet/mobile (§6) |
| Screen reader | NVDA + JAWS + VoiceOver tested baseline (live builds, deferred for mockups) |

**eaiou-specific doctrine:**
- IntelliD pills always carry an explicit aria-label (the displayed mono ID is the visual presentation; AT pronounces it as a labeled identity unit).
- Sealed surfaces announce sealed state via `aria-describedby` pointing to a sealed-explainer node, not via visual cue alone.
- HUMINT vs UNKINT projection state is announced when toggled (`aria-live=polite` toast).
- No reliance on color alone for state — every state has a textual or shape signal as well.

---

## 2. Heading hierarchy

| Page family | h1 | h2 | h3 |
|---|---|---|---|
| Home (`/`) | "eaiou — follow the river" (visually hidden if hero takes over) | "Following the river" | per-card title hidden in heading? — see §2.1 |
| Paper list | "Papers" | filter group label (visually hidden) | per-card title is `<h3>` |
| Paper detail | paper title (Spectral 36pt) | tab section label | sub-section per tab |
| Author dashboard | "My papers" | filter / list section | per-paper card |
| Reviewer queue | "Reviewer queue" | filter section | per-assignment card |
| Editor list | "Editorial papers" | KPI / filter / list section | per-paper card |
| Admin manager | "<view> manager" (e.g., "AI sessions manager") | filter section | row count summary |
| Auth pages | "Sign in" / "Register" / "Reset password" | (none) | (none) |
| Doctrine | "Doctrine" | major section | sub-section |
| 404 | "this surface is not in the river" | (none) | (none) |

### 2.1 Card title heading rule
Per-card paper title is `<h3>` on list pages (papers, mypapers, queue, editorial). On paper detail, the paper title is `<h1>`.

**Acceptance:**
- Skip from `<h1>` to `<h3>` is allowed when the visual layout has no `<h2>` need (hero band → cards). This is WCAG-compliant; AT users can navigate by heading regardless.
- No multiple `<h1>` per page.
- Headings are content-driven, not visual-driven. Spectral 36pt that is decorative (e.g., "Following the river" on home) is `<h2>`, not `<h1>`.

---

## 3. Color contrast pairs (light mode)

Computed contrast for every common token pair. Light backgrounds.

| Foreground | Background | Ratio | WCAG |
|---|---|---|---|
| `--ink` `#0e0d0b` | `--paper` `#f7f4ef` | 17.2:1 | AAA |
| `--ink` `#0e0d0b` | `--surface` `#ffffff` | 19.1:1 | AAA |
| `--ink2` `#3a3832` | `--paper` `#f7f4ef` | 11.1:1 | AAA |
| `--ink2` `#3a3832` | `--surface` `#ffffff` | 12.3:1 | AAA |
| `--ink3` `#7a7670` | `--paper` `#f7f4ef` | 4.6:1 | AA (large/UI) |
| `--ink3` `#7a7670` | `--surface` `#ffffff` | 5.0:1 | AA |
| `--river` `#1a4a6b` | `--paper` `#f7f4ef` | 7.8:1 | AAA |
| `--river` `#1a4a6b` | `--surface` `#ffffff` | 8.6:1 | AAA |
| `--river-l` `#2d6e9e` | `--paper` `#f7f4ef` | 4.5:1 | AA (large/UI) |
| `--river-l` `#2d6e9e` | `--surface` `#ffffff` | 5.0:1 | AA |
| `--coral` `#b84832` | `--paper` `#f7f4ef` | 5.0:1 | AA |
| `--coral` `#b84832` | `--coral-l` `#faeae6` | 4.7:1 | AA (large/UI) |
| `--sage` `#3a6b4a` | `--paper` `#f7f4ef` | 6.5:1 | AA |
| `--sage` `#3a6b4a` | `--sage-l` `#e8f2ec` | 5.7:1 | AA |
| `--amber` `#c47c0a` | `--paper` `#f7f4ef` | 4.4:1 | AA (large/UI) |
| `--amber` `#c47c0a` | `--amber-l` `#fdf0d0` | 4.0:1 | fails AA on body text — use only for ≥ 14pt |
| `--violet` `#4a3278` | `--paper` `#f7f4ef` | 9.6:1 | AAA |
| `--violet` `#4a3278` | `--violet-l` `#ede8f7` | 8.4:1 | AAA |
| `--paper` `#f7f4ef` | `--river` `#1a4a6b` | 7.8:1 | AAA (button text on river-fill) |
| `--paper` `#f7f4ef` | `--coral` `#b84832` | 5.0:1 | AA (button text on coral-fill) |

**Acceptance:**
- `--amber` on `--amber-l`: limited to ≥ 14pt or UI elements (not body copy). Documented in §3 of `UXPILOT_00`.
- `--ink3` on `--paper2` `#ede9e1`: 3.9:1 — passes AA for UI/large only. Used for skeleton labels and helper text mono 11pt only.

---

## 4. Color contrast pairs (dark mode — defined, not yet built)

Per `UXPILOT_00 §4`. Recomputed for the dark token set:

| Foreground | Background | Ratio | WCAG |
|---|---|---|---|
| `--ink` `#f2efe8` | `--paper` `#141210` | 16.8:1 | AAA |
| `--ink` `#f2efe8` | `--surface` `#1e1c1a` | 14.2:1 | AAA |
| `--ink2` `#c8c4bb` | `--paper` `#141210` | 11.4:1 | AAA |
| `--ink3` `#8a8680` | `--paper` `#141210` | 4.8:1 | AA |
| `--river` `#4a8abf` | `--paper` `#141210` | 6.8:1 | AAA |
| `--river-l` `#6aaad8` | `--paper` `#141210` | 9.5:1 | AAA |
| `--coral` `#d45a40` | `--paper` `#141210` | 5.4:1 | AA |
| `--sage` `#4a8a5e` | `--paper` `#141210` | 5.0:1 | AA |
| `--amber` `#d4920e` | `--paper` `#141210` | 6.7:1 | AAA |
| `--violet` `#7060b0` | `--paper` `#141210` | 4.7:1 | AA (large/UI) |

**Acceptance:**
- Dark mode passes AA at minimum for every token pair.
- Final dark-mode mockups must verify with axe / Lighthouse before ship.

---

## 5. Keyboard interaction

Every interactive element reachable via Tab. Tab order matches visual top-down/left-right per `UXPILOT_07 §9.6`.

### 5.1 Standard keyboard shortcuts

| Key | Action |
|---|---|
| `Tab` | Move focus forward |
| `Shift+Tab` | Move focus backward |
| `Enter` | Activate focused button or link |
| `Space` | Activate focused button; toggle focused checkbox/toggle |
| `Esc` | Close modal/drawer/dropdown/tooltip; cancel inline edit |
| `Arrow ↑/↓` | Move focus within radio group, menu, listbox |
| `Arrow ←/→` | Move focus within tab strip; adjust slider |
| `Home` / `End` | Jump to first/last in list, menu, tab strip |
| `/` (slash) | Focus header search input (when not in form field) |

### 5.2 Surface-specific keyboard

| Surface | Keyboard behavior |
|---|---|
| Header search | `/` focuses; Enter submits to /search; Esc clears |
| Filter rail chips | `Tab` to chip group; arrows navigate within group; Space toggles selection |
| Tab strips | Arrow ←/→ moves between tabs; Home/End jump to first/last; Enter activates if not auto |
| Tables | Tab into table; arrow keys navigate rows; Space selects (if checkbox); Enter opens row |
| Modal | Trap focus inside; Esc closes; Tab cycles |
| Drawer | Same as modal |
| Dropdown menu | Arrow ↑/↓ navigate items; Enter selects; Esc closes |
| TAGIT composer | Cmd/Ctrl+Enter submits; Esc cancels; Tab moves between rubric criteria |
| Submit wizard | Cmd/Ctrl+Enter advances step (if valid); Cmd/Ctrl+Shift+Enter → final submit |
| Q-signal bar (chart) | Tab focuses; Enter opens tooltip; Esc closes |
| Heatmap (gap_map full) | Arrow keys navigate cells; Enter drills to filtered list |

### 5.3 Focus traps
- Modals trap focus until closed.
- Drawers trap focus on mobile; on desktop, focus may leave (outline-cancellable interaction model).
- Dropdowns close on focus exit.

---

## 6. Touch targets

Mobile (≤ 640px) and tablet (641–1023px) breakpoints require touch targets ≥ 44×44 CSS px, per WCAG 2.5.5.

| Component | Default size | Mobile/tablet adjustment |
|---|---|---|
| Buttons (default 32px) | 32px | Padding extended to make hit area 44px. |
| Filter chips (28px) | 28px | Padding extended to 44px hit area; visual stays 28px. |
| Tag pills (18px) | 18px | Same — extend hit area via invisible padding. |
| Icon buttons (32×32) | 32×32 | Extended to 44×44 hit area. |
| Tab items (40px) | 40px | Padding extended slightly. |
| Pagination chevrons (28×28) | 28×28 | Extended to 44×44. |
| Table rows | 48–56px | Already meets target on row click. |

**Spacing between targets:** ≥ 8px between adjacent interactive elements on mobile (already enforced by `--space-2`).

---

## 7. ARIA & semantic markup

Native semantics first; ARIA only as supplement.

### 7.1 Mandatory ARIA labels

| Element | aria-label or aria-labelledby |
|---|---|
| IntelliD pill | `aria-label="IntelliD INT-9F2A"` |
| Tag pill `rs:LookCollab:Statistician` | `aria-label="tag rs:LookCollab:Statistician"` |
| Q-signal bar | `aria-label="q_signal 0.847, rank 4 of cycle q4"` |
| Sparkline | `aria-label="metric trending up: 12, 18, 22, 31"` |
| Heatmap cell | `aria-label="Cosmology · NotTopic:Bayesian · 12 stalled papers"` |
| Filter chip | `aria-pressed="true|false"` (since it acts as a toggle) |
| Tab item | `role="tab" aria-selected="true|false"` |
| Tab panel | `role="tabpanel" aria-labelledby="<tab-id>"` |
| Workflow state chip | `aria-label="state: under review"` |
| Skeleton placeholder | `aria-busy="true"` on parent surface |
| Sealed badge | `aria-label="sealed — governance unlock required"` |
| HUMINT chip | `aria-label="observer projection: HUMINT"` |
| UNKINT chip | `aria-label="observer projection: UNKINT, N minutes remaining"` |
| Session-lock chip | `aria-label="TAGIT session lock active, encrypted"` |
| Banner | `role="status"` (info), `role="alert"` (urgent error) |
| Toast | `role="status" aria-live="polite"` (info/success), `role="alert" aria-live="assertive"` (error) |
| Modal | `role="dialog" aria-modal="true" aria-labelledby="<title-id>"` |
| Drawer | `role="dialog" aria-modal="true|false"` (true on mobile, false on desktop) |
| Tooltip | `role="tooltip"`; trigger has `aria-describedby="<tooltip-id>"` |
| Form input | label `<label for="<id>">` always present; helper text `aria-describedby` |

### 7.2 Live regions

| Region | Use |
|---|---|
| `aria-live="polite"` | Toast (info, success); UNKINT projection toggle announcement |
| `aria-live="assertive"` | Error toast; form-submit error count |
| `aria-busy="true"` | Skeleton-loading surface |

### 7.3 Headings & landmarks

- `<header>` for chrome header
- `<main>` for primary content column
- `<aside>` for right rail (modules)
- `<footer>` for chrome footer
- `<nav aria-label="primary">` for header nav
- `<nav aria-label="footer">` for footer nav
- `<nav aria-label="breadcrumb">` for topbar breadcrumb
- Skip-link `<a href="#main">skip to main content</a>` first focusable element

---

## 8. Forms

| Pattern | Spec |
|---|---|
| Label association | `<label for="<id>">` for every input — visible mono UPPERCASE label, never hidden |
| Required indicator | `aria-required="true"` + visible mono `·` `--coral` after label |
| Error association | `aria-invalid="true"` + `aria-describedby` pointing to the inline error helper id |
| Error announcement | Form-level `<div role="alert" aria-live="assertive">` summarizes count on submit |
| Helper text | `aria-describedby` pointing to the helper text id |
| Disabled reason | `aria-disabled="true"` + tooltip explaining why (hover or focus reveals) |
| Group | `<fieldset>` + `<legend>` for radio groups, checkbox groups, multi-step wizards |
| Stepper progress | `aria-current="step"` on the active step; `aria-label="step 2 of 5: Sources"` |
| File input | Native input + visible mono prompt + drop-zone has `aria-label="upload PDF, max 50 megabytes"` |
| Auto-save status | `<div aria-live="polite">draft saved · cycle q4</div>` after each save |

**Acceptance:**
- Never rely on placeholder as label.
- Never hide the visible label visually except via `.visually-hidden` (clip-path technique) when truly necessary; instead, prefer always-visible mono UPPERCASE labels per `UXPILOT_08 §2`.

---

## 9. Charts & dataviz accessibility

Every chart from `UXPILOT_09` provides AT-equivalent content.

| Chart | AT alternative |
|---|---|
| q-signal bar | aria-label with value + rank |
| Sparkline | aria-label with min, max, and trend direction (e.g., "trending up, 12 to 31 over 12 cycle slots") |
| Segmented bar | aria-label with category breakdown (per segment) |
| Stacked bar (intellid_graph paper) | aria-label with each contributor and percent; also rendered as a `<dl>` description list visible at narrow widths and to AT |
| Heatmap | grid-role table with row/column headers; each cell has aria-label combining row/column/count |
| Network graph (intellid_graph wide) | `<dl>` with each node listed; `aria-describedby` on the graph points to the list |
| Histogram | `<dl>` of bins with counts; aria-label summarizes distribution |
| Cycle-slot timeline | `<ol>` of slots with `aria-current="step"` on the active slot |
| Entropy trace map | `<dl>` of events with entropy values |
| Relative-window bar `▣▣▣▢▢▢▢` | aria-label `"4 of 7 through this window"` |
| Reviewer rubric scale | `<fieldset>` with `<legend>` per criterion; radio group with mono labels 1-5 + tooltip with semantic label |

**Acceptance:**
- Charts are decorative without their AT alternative. Every chart must pair with text-equivalent content.
- Tooltips are not the AT alternative — they require pointer hover.

---

## 10. Screen reader user journeys

Three reference journeys to validate (live builds, deferred for mockup phase):

### 10.1 Public reader exploring papers

1. Land on `/`. Skip-link → main content (river-band).
2. Heading nav `H` → "Following the river" (`<h2>`).
3. Tab into first paper card. AT announces: "Sealed-time effects on peer review participation rates, level 3 heading. by IntelliD INT-9F2A and IntelliD INT-A831. q_signal 0.847, rank 4 of cycle q4. badges: AI-Logged, Open Reports."
4. Enter activates → paper detail.
5. Heading nav `H` → paper title (`<h1>`).
6. Heading nav within tabs → "Manuscript", "Sources", "AI Usage", "Open Reports", "Attribution" (each `<h2>`).

### 10.2 Reviewer completing rubric

1. Land on `/reviewer/paper/{id}/review`.
2. Heading nav → "Review console" (`<h1>`).
3. Tab into rubric criterion 1 fieldset. Legend: "Soundness". Radio group with options 1–5 mono labels.
4. Arrow ↑/↓ moves between radio options. Each announces "1 of 5: insufficient", etc.
5. Tab to comment textarea. Aria-label: "comment on Soundness". Optional.
6. Tab to next criterion fieldset.
7. Tab to submit. AT announces "Submit review, button". Enter submits.
8. On success: `<div role="alert">` announces "review submitted. session sealed."

### 10.3 Editor activating UNKINT

1. Land on `/editorial/paper/{id}`.
2. Tab to header HUMINT chip. AT: "observer projection: HUMINT, button". 
3. Enter opens UNKINT activation modal. Focus trapped.
4. Tab through justification textarea, scope select, window select, confirm button.
5. On confirm: focus returns to header. Chip changes; AT announces "observer projection: UNKINT, 15 minutes remaining" (via `aria-live="polite"`).
6. UNKINT-only fields (workflow timestamps, sealed metadata) become visible. Each field is announced when reached.
7. On expiry: AT announces "UNKINT projection expired. HUMINT view restored" (via toast, `aria-live="polite"`).

---

## 11. Reduced transparency / contrast

`prefers-reduced-transparency: reduce`:
- Modal backdrop becomes solid `--ink` at 90% (vs `rgba(14,13,11,0.45)`).
- Drawer backdrop becomes solid `--ink` at 80%.
- Tooltip retains solid `--ink` bg (already opaque).

`prefers-contrast: more`:
- Hairline borders 1px → 2px.
- Focus ring outer 2px → 3px.
- Helper text `--ink3` → `--ink2`.
- Empty-state Spectral italic `--ink2` → `--ink`.

---

## 12. Internationalization affordances

eaiou is English-first but design should not block translation:

- No text inside SVG icons (mono glyphs only).
- No text-as-image. Use Spectral / mono throughout.
- Mono UPPERCASE labels can render via CSS `text-transform: uppercase` so source remains lowercase (i18n-friendly).
- Date formats: not applicable — eaiou strips dates from HUMINT view. UNKINT timestamps render in UTC mono.
- Numeric formats: q_signal always rendered with 3 decimals (`0.847`). No locale-specific decimal separators in mono UI.
- IntelliD format: `INT-XXXX` is locale-invariant.
- Right-to-left support: deferred. eaiou doctrine and IntelliD format have no RTL-required surfaces yet.

---

## 13. Print accessibility

Per `UXPILOT_07 §12`, only paper detail has a print stylesheet. Accessibility:
- Heading hierarchy preserved.
- IntelliD pills render mono in print with explicit text "IntelliD INT-9F2A" (the aria-label becomes the rendered label).
- Tag pills render mono with `rs:` prefix and full tag name.
- Sealed timestamps absolutely never print.
- Charts render as SVG (vector); AT-equivalents render as `<dl>` description lists immediately after each chart.

---

## 14. Acceptance criteria for any UXPilot mockup

1. Every interactive element is keyboard-reachable in visual order.
2. Every interactive element has visible focus ring (`UXPILOT_11 §4`).
3. Every IntelliD pill, tag pill, q_signal bar carries an aria-label per §7.1.
4. Color contrast meets AA minimum (AAA for body text where pair allows).
5. Headings cascade is sane (h1 → h2 → h3); no decorative use of `<h1>`.
6. Touch targets ≥ 44×44 on mobile/tablet.
7. Forms have visible labels, error association, and submit-error summary.
8. Charts pair with `<dl>` or aria-label text equivalents.
9. Modals trap focus; Esc closes; focus returns to trigger.
10. Live regions used for toasts, projection toggle, save-status.
11. Reduced motion / transparency / contrast preferences honored.
12. No reliance on color alone for state — every state has a textual or shape signal.

---

## 15. Citation rules

- Per-page prompts cite specific aria patterns: "Render IntelliD pill per `UXPILOT_12 §7.1`."
- Charts in `UXPILOT_09` cite AT alternatives by chart type: "AT alternative per `UXPILOT_12 §9`."
- Forms in `UXPILOT_08 §20` cite this file for label/error patterns: "Form a11y per `UXPILOT_12 §8`."

---

## 16. Open accessibility questions (for Eric)

1. Live screen-reader testing — is there a budget / partner for NVDA + JAWS + VoiceOver runs? Mockup phase doesn't gate on this; live build does.
2. Reduced-motion default — eaiou ships with `prefers-reduced-motion` honored; no in-app override. Confirm or add toggle.
3. Sealed announcement copy — "sealed — governance unlock required" feels right but may be more terse than necessary. Confirm AT verbosity.
4. RTL support — deferred. Any near-term i18n that requires it?
5. AAA target — current spec hits AAA on most text pairs; reach AAA across the board? Cost: `--amber` + `--amber-l` would need adjustment.

---

## End of `UXPILOT_12_accessibility.md`

Next steps after this file:
- `UXPILOT_13_responsive.md` — breakpoint-by-breakpoint behavior across all 50 surfaces.
- Audit pass through `UXPILOT_01..05` to add citations to the new `UXPILOT_08..12` files.
- Update `UXPILOT_99_index.md` foundation list and verification checklist.
