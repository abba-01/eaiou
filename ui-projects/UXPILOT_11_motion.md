# UXPILOT_11 — motion, focus, microinteractions

**Tokens:** see `UXPILOT_00_design_system.md`.
**Components:** see `UXPILOT_08_components.md` for buttons (§1), inputs (§2), modals (§6), drawers (§7), toasts (§8), tooltips (§13).
**States:** see `UXPILOT_10_states.md`.

This file consolidates motion timings, focus styles, hover behaviors, and microinteraction specs referenced ad-hoc across `UXPILOT_01..08`. Motion in eaiou is restrained — every animation is functional (signaling state change), never decorative.

---

## 1. Motion philosophy

Three rules:
1. **Functional only.** Animation signals state change (open/close, focus, validation). Never decoration.
2. **Honest pacing.** Skeleton placeholders do not animate (per `UXPILOT_10 §2`). Loading time is loading time, not a performance.
3. **Reducible.** Every animation respects `prefers-reduced-motion: reduce` per §11.

No glow effects. No bounce. No spring physics. No parallax. No scroll-triggered reveals. No background animation.

---

## 2. Timing catalog

| Token | ms | Easing | Use |
|---|---|---|---|
| `motion-instant` | 0 | — | Skeleton-to-content swap; tab content swap (cached) |
| `motion-tiny` | 80 | linear | Cursor changes, color swaps on hover |
| `motion-short` | 120 | ease-in | Modal open opacity 0→1; tooltip open; toast fade |
| `motion-default` | 160 | ease-out | Accordion expand/collapse; dropdown open |
| `motion-medium` | 200 | ease-out | Drawer slide in/out; pull-down extras (wide-mode) |
| `motion-long` | 280 | ease-in-out | Banner stack reflow when banners added/removed |
| `motion-pulse` | 2000 | ease-in-out | Session-lock indicator outline pulse (only) |

**Acceptance:**
- No timing exceeds 280ms for state changes.
- The 2s pulse is the longest animation in the system and applies *only* to TAGIT session-lock indicator chrome.

---

## 3. Easing curves

Native CSS easing only:
- `linear` for color transitions.
- `ease-in` for opening states (modal, tooltip, toast appear).
- `ease-out` for closing or settling states (drawer slide, accordion expand).
- `ease-in-out` for symmetrical reflows.

**No cubic-bezier custom curves.** No spring/bounce.

---

## 4. Focus rings

Standardized across every focusable element.

| Element | Focus ring spec |
|---|---|
| Buttons (all variants from `UXPILOT_08 §1`) | 2px outer ring `--river-ll`, 1px gap from button edge, total 4px outset |
| Inputs (all from `UXPILOT_08 §2`) | 2px outer ring `--river-ll` + 1px border swap to `--river` |
| Chips, filter chips | 2px outer ring `--river-ll`, 1px gap |
| Tab item | 2px outer ring `--river-ll` (does not affect the 2px bottom active indicator) |
| Table row | 2px inset ring `--river-ll` (since rows have borders, not outlines) |
| Cards (clickable) | 2px outer ring `--river-ll` |
| Module header (collapse trigger) | 2px outer ring `--river-ll` |
| Modal close button | 2px outer ring `--river-ll`, 1px gap |
| Drawer trigger | 2px outer ring `--river-ll` |
| Skip-link | 2px outer ring `--river-ll`, slides into view from top-left |

**Acceptance:**
- Focus is always visible. Never `outline: none` without replacement.
- Focus ring color is `--river-ll` regardless of element variant (including coral / sage / amber buttons — focus is uniform).
- Tab order matches visual top-down/left-right order per `UXPILOT_07 §9.6`.

---

## 5. Hover transitions

All hover transitions use `motion-tiny` (80ms linear) unless noted.

| Element | Hover effect |
|---|---|
| `btn-primary` | bg `--river` → `--river-l` |
| `btn-outline` | bg transparent → `--river-ll` |
| `btn-ghost` | bg transparent → `--paper2` |
| `btn-icon` | bg transparent → `--paper2` |
| Tab item (inactive) | text `--ink2` → `--ink`, 1px bottom hairline `--ink3` appears |
| Filter chip (inactive) | bg `--surface` → `--paper2` |
| Tag pill | border `--paper3` → `--river` |
| Table row (clickable) | bg `--surface` → `--paper2` |
| Card (clickable) | border `--paper3` → `--ink3`; q_signal bar height +1px |
| Module header | bg `--paper2` → unchanged (collapse chevron rotates if collapse trigger) |
| Brand glyph (header) | glyph `--river` → `--river-l`; wordmark `--ink` → `--ink2` |
| Header nav item | text → `--ink`, 1px bottom hairline `--ink3` |
| Footer link | text → `--river`, 1px bottom hairline appears |
| IntelliD pill | border `--paper3` → `--river` |
| Sparkline / chart node | tooltip appears (delay 400ms per `UXPILOT_08 §13`) |
| Heatmap cell | outline 1px `--ink2` (cell stays in place, outline draws inside) |

**Acceptance:**
- Cursor changes to pointer on every clickable element. Default cursor on non-clickable.
- Cursor `wait` only during button loading state.
- Cursor `not-allowed` on disabled buttons / inputs.
- Hovering does not enlarge or scale anything. The +1px q_signal bar grow is the only "size shift" allowed, and it's intentional.

---

## 6. Active / pressed states

Triggered on `:active` (pointer down).

| Element | Active treatment |
|---|---|
| Buttons (filled) | bg → `--ink` (full ink override) |
| Buttons (outline / ghost) | bg → `--paper3`, border → `--ink` |
| Filter chips | scale 1.0 → 0.98 over 80ms ease-in (the only scale animation in the system; release returns 1.0) |
| Tab item | brief 1px bottom border `--river` flash |

**Acceptance:**
- Active state is a brief feedback signal, not a sustained state. On release it returns to hover or default.
- The 0.98 scale on filter chips is the *only* allowed scale animation.

---

## 7. Modal lifecycle

(Reference: `UXPILOT_08 §6`.)

**Open:**
- Backdrop fade in 120ms ease-in (opacity 0 → 1).
- Modal: opacity 0 → 1 + scale 0.98 → 1.0, both 120ms ease-in.
- Focus moves to first focusable element in body (or close button if no body focusables).

**Close:**
- Modal opacity 1 → 0 + scale 1.0 → 0.98, 120ms ease-in.
- Backdrop opacity 1 → 0, 120ms ease-in.
- Focus returns to the trigger element that opened the modal.

**Acceptance:**
- ESC closes (with confirm if dirty form).
- Backdrop click closes (with confirm if dirty form).
- Body scroll locked while modal open. Restored on close.
- Never two modals stacked.

---

## 8. Drawer lifecycle

(Reference: `UXPILOT_08 §7`.)

**Open:**
- Backdrop fade in 200ms ease-out (opacity 0 → 1).
- Drawer slides in from edge: translateX `-100% → 0` (left-side) or `100% → 0` (right-side), 200ms ease-out.
- Focus moves to first focusable in drawer.

**Close:**
- Drawer slides out: translateX `0 → -100%` or `0 → 100%`, 200ms ease-out.
- Backdrop fade out 200ms ease-out.
- Focus returns to trigger.

**Mobile swipe-close:** track touch X delta; close at threshold 40% of drawer width or velocity threshold.

---

## 9. Toast lifecycle

(Reference: `UXPILOT_08 §8`.)

**Open:**
- New toast inserted at bottom of stack.
- Translate Y +8 → 0, opacity 0 → 1, 200ms ease-out.
- Existing stacked toasts shift up 8px each (smooth 200ms ease-out).

**Dwell:** 5s (info / success), 8s (warn), persistent (error). Hover pauses dwell timer.

**Close:**
- Translate X 0 → 16, opacity 1 → 0, 160ms ease-out.
- Stack collapses up.

**Acceptance:**
- Toasts never carry CTAs that change global state — only retry/dismiss.
- Stack never exceeds 3 visible. Older toasts dismissed automatically when limit reached (FIFO).

---

## 10. Tooltip lifecycle

(Reference: `UXPILOT_08 §13`.)

**Open:** delay 400ms after hover/focus. Opacity 0 → 1 over 120ms ease-in. Position recomputed each open.
**Close:** opacity 1 → 0 over 100ms ease-in. Delay 0 (immediate on hover/focus exit).
**Sticky tooltip:** if user keyboard-focuses the trigger (Tab), tooltip stays until blur.

**Acceptance:**
- Never open on click — only hover or focus.
- Delay prevents tooltip noise during rapid pointer movement.
- Tooltip never blocks the trigger element it points at.

---

## 11. Reduced motion preference

Every animation in this file respects `@media (prefers-reduced-motion: reduce)`:

| Default | Reduced-motion treatment |
|---|---|
| Modal open scale + opacity | Opacity only; no scale |
| Drawer slide | Instant position change (no transition) |
| Toast slide-in | Opacity only |
| Accordion expand | Instant (no height transition) |
| Pull-down extras (wide-mode) | Instant |
| Banner stack reflow | Instant |
| Session-lock pulse | Static (no pulse) |
| Filter chip active scale | Instant (no scale) |

**CSS implementation:**
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

**Acceptance:**
- Reduced-motion preference is detected per-session; honored without user opt-in inside the app.
- All chrome remains functional; the only perceptible difference is the absence of motion.

---

## 12. Cursor states

| Cursor | When |
|---|---|
| `default` | Text, non-interactive surfaces |
| `pointer` | Buttons, links, clickable cards, table rows (clickable), tag pills, filter chips, IntelliD pills |
| `text` | Text inputs, textareas, contenteditable |
| `wait` | Button in loading state |
| `not-allowed` | Disabled buttons / inputs |
| `crosshair` | Heatmap cells (gap_map full mode), entropy trace map markers |
| `grab` / `grabbing` | (Reserved — not currently used; would apply to draggable wizard step reorder if shipped) |

**Acceptance:**
- Cursor is the primary affordance signal alongside hover bg change. Both must agree.

---

## 13. Selection states

Text selection styling:
- Selection bg `--river-ll`, text `--ink`.
- No selection styling on the brand wordmark (`user-select: none` on the logo).
- Code blocks (`UXPILOT_08 §18`): selection bg `--river`, text `--paper`.

Row selection (table checkbox):
- Selected row bg `--river-ll`, no border change.
- Multi-select via shift-click extends from anchor row.
- "Select all" header checkbox toggles entire current page (not the entire result set — explicit "select all N matching" link appears in a banner above the table when used).

---

## 14. Validation microinteractions

Form field validation behaviors:

**On blur (default):**
- Run validator. If invalid, render inline error per `UXPILOT_08 §2`.
- No animation on the field; the error helper text below appears with 80ms opacity 0 → 1.

**On submit with errors:**
- Form scrolls to first error field over 200ms ease-out.
- That field gains focus.
- Toast `toast-error` appears: "1 field needs your attention" (or "N fields").
- Each invalid field briefly flashes its 1px border `--coral` for 400ms then settles.

**On valid submit:**
- Submit button enters loading state (`UXPILOT_08 §1`).
- On 2xx response: success treatment per `UXPILOT_10 §5` — toast or modal-confirm.

**Acceptance:**
- Never validate on every keystroke (creates noise).
- Real-time validation only for: password strength meter (registration), DOI uniqueness check (submit wizard).

---

## 15. Skeleton-to-content transition

(Per `UXPILOT_10 §10` — restated for completeness.)

- Skeleton elements are replaced with real content via instant swap. No fade, no translate.
- Page reflow allowed; skeletons sized to match expected content within tolerance.
- Tab and filter changes use 200ms opacity dim (1.0 → 0.6 → 1.0) instead of skeleton swap.

---

## 16. Page navigation transitions

- No page-level transition animation (no fade, no slide).
- URL change → new page renders. Header, footer, brand chrome stay in place (sticky chrome doesn't move).
- Right-rail modules render their own loading states independently per `UXPILOT_10 §11`.

**Acceptance:**
- The user should perceive navigation as instant in chrome and progressive in content.
- No "page transition" framework (Turbo, Inertia view transitions, etc.) is animated visually — only used for performance.

---

## 17. Stand-out animations (the explicit list)

The complete inventory of every animation in eaiou. If a UXPilot mockup includes any animation not on this list, it should be removed.

1. Modal open/close (opacity + 0.98 scale, 120ms).
2. Drawer slide in/out (translate X, 200ms).
3. Toast slide in/out (translate Y/X, 160–200ms).
4. Tooltip open/close (opacity, 100–120ms with 400ms open delay).
5. Accordion expand/collapse (height, 160ms).
6. Pull-down extras open/collapse (height, 200ms).
7. Banner stack reflow (200–280ms).
8. Filter chip active press (scale 0.98, 80ms).
9. Hover bg/border color transitions (80ms linear).
10. Validation error 1px border flash (400ms).
11. Submit-error scroll-to-field (200ms).
12. Session-lock indicator outline pulse (2000ms ease-in-out, only animation that loops).
13. Inline form-saved fade-out (3s opacity 1 → 0, success message after inline form save).
14. Skip-link slide-in from top-left when focused.
15. Wide-mode shell toggle reflow (200ms).
16. Sticky-bottom TAGIT session strip vertical reflow when session ends (160ms).

**Anything else: don't.**

---

## 18. Acceptance criteria for any UXPilot mockup with motion

1. Every animation in the mockup appears in §17. If not, remove it.
2. Timing values use only the tokens in §2 (80, 120, 160, 200, 280, 2000 ms).
3. Easing values use only `linear`, `ease-in`, `ease-out`, `ease-in-out`.
4. Focus rings use `--river-ll` (uniform across all variants).
5. Hover state changes use bg/border color only — never scale or translate (filter chip 0.98 active is the one exception).
6. Reduced-motion preference is respected.
7. Modal/drawer/toast lifecycles match §7/§8/§9 exactly.
8. No background animations. No parallax. No scroll-triggered reveals.
9. Cursor state matches interactivity at all times.
10. Validation animation is brief border flash + scroll, not field shake or red highlight pulse.

---

## 19. Citation rules

- Per-page prompts cite motion behavior by section: "Modal opens per `UXPILOT_11 §7`."
- Components in `UXPILOT_08` cite back to this file: "Lifecycle per `UXPILOT_11 §7`."
- Reduced-motion handling is centralized here — every component cites §11.

---

## 20. Open motion questions (for Eric)

1. The 2s session-lock pulse — is the loop count constrained, or does it pulse indefinitely while session is active? Current spec: indefinite while active. Confirm energy cost vs visibility tradeoff.
2. Filter chip active scale (0.98) — the only scale animation. Worth removing entirely for total consistency?
3. View transitions API (Chrome / Edge) — opt in for cross-document navigations?
4. Submit success — currently modal-confirm. Should publication / acceptance use a more substantial visual moment? Spec resists this; confirm.
5. Skeleton-to-content reflow — when content arrives larger than skeleton, the page jumps. Acceptable, or worth content-visibility lock?

---

## End of `UXPILOT_11_motion.md`

All four extension files written: `UXPILOT_08_components.md`, `UXPILOT_09_dataviz.md`, `UXPILOT_10_states.md`, `UXPILOT_11_motion.md`.
Next step: update `UXPILOT_99_index.md` to reference these four files in foundation list, citation pattern, and acceptance criteria.
