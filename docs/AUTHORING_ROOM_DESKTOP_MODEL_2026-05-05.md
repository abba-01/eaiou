# EAIOU Authoring — Room / Desktop / Sidebar / Drawer Model

**Date:** 2026-05-05 00:02 PDT
**Status:** Specifies the structural model for the authoring portion of the site.
**Authors:** Eric D. Martin (architecture), Mae (transcription)
**Supersedes:** Single-shell shape implied in `AUTHORING_DESIGN_v3_journal_rail_lock_2026-05-02.md`. The Design v3 lock principles still apply on top of this structural model.
**Companion to:** `AUTHORING_DESIGN_v3_journal_rail_lock_2026-05-02.md`, `AUTHORING_FRONTEND_IMPL_2026-05-01.md`, `AUTHORING_WORKFLOW_IMPL_2026-05-01.md`.

---

## 1. Hierarchy

```
User
└── Resource Room                  (single per user; canonical landing post-login)
    ├── Desktops                    (one per manuscript)
    │   ├── Sidebar slots           (1+1 baseline; 2+2 premium)
    │   ├── Center component view   (the writing surface or stage view)
    │   └── Footer module drawer    (per-desktop module palette)
    ├── Shared Libraries            (cross-user collections; collaborator-shared)
    └── Collaborators               (people the user writes with)
```

The Resource Room is the **only persistent landing** for an authenticated user. Desktops, libraries, and collaborators are room-level objects.

A Desktop is created when a user begins authoring a manuscript. There is exactly one Desktop per manuscript. A user can have many Desktops (one per manuscript in flight).

## 2. Viewport Width — fluid, no fixed widths

**All authors start out wide.** The authoring surface uses the full viewport at all times. There is no fixed-width container, no centered max-width content area.

| Viewport class | Layout |
|---|---|
| Mobile / narrow      | center column only; sidebars collapse to drawer/overlay |
| Tablet / mid         | 1 left sidebar + center + 1 right sidebar (baseline) |
| Desktop computer     | optional 2 left + center + 2 right (premium tier) |

## 3. Sidebar Architecture

**Baseline (every authenticated author, every viewport class that supports sidebars):**

- 1 fixed left sidebar
- 1 fixed right sidebar
- 1 center component view

**Premium extension (computer-class viewport, paid tier only):**

- +1 second left sidebar
- +1 second right sidebar

Maximum at the desktop tier: **2 left + center + 2 right** (5 columns).

The fixed baseline (1+1+1) is non-negotiable — every authenticated author has it on any viewport that fits.

The premium extension (2+2+1) is a paid tier gate. The rationale: the second left + second right sidebars are needed to give simultaneous space to **collaborators** (one extra rail) and **intelligence** (IID provider modules in another extra rail). Free / baseline tier users have these features but multiplexed into the single left + single right sidebar.

## 4. Sidebar Content — Module Slot Pattern

Each sidebar position is a **slot**. A slot can hold any compatible **module** dragged from the footer drawer (§5).

Default slot contents on a fresh manuscript Desktop:

| Slot | Default module |
|---|---|
| Left 1  | Section Navigator (manuscript sections, version timeline) |
| Right 1 | IID Provider Modules (configured providers + their actions) |
| Left 2  (premium) | empty — author drags in (e.g., Collaborators panel) |
| Right 2 (premium) | empty — author drags in (e.g., second IID provider, or Coverage tracker) |

Authors can re-arrange any slot at any time by dragging modules in / out via the drawer (§5).

Slot layout state persists per-user-per-Desktop (one configuration saved per manuscript).

## 5. Module Drawer

A pull-up drawer at the bottom of every Desktop (and the Resource Room).

**Closed state:**
- Single horizontal tab at the footer center, labeled "Modules"
- Footer otherwise minimal

**Opening interaction:**
- User pulls the tab UP (drag, click, or keyboard shortcut)
- The drawer rises and stretches across the full width of the viewport
- Displays a horizontal palette of all available modules, tagged

**Open state contents:**
- Horizontal scroll of module cards (tagged)
- Filter / sort by tag (Section Navigator, IID Providers, Collaborators, Coverage, Wheelhouse, Notifications, etc.)
- Search box for modules by name
- Each module shows: name, tag, brief description, "in use" badge if currently placed in a slot

**Drag interactions:**
- Drag a module from drawer → drop on any compatible sidebar slot → slot displays the module
- Drag a module from a slot → drop on drawer → slot returns to empty
- Drag a module from one slot to another → re-arrange
- Drag a module in-use to drawer when slot already empty → no-op (graceful)

**Per-tag slot compatibility (initial rules; refine in next pass):**
- All modules can go in any slot **with one exception:** the IID Drawer / IID Conversation Thread is restricted to the right rail (left rail does not support it; it's wired against the right-side IID provider list)

**Drawer state persistence:**
- The author's last sidebar layout (which modules in which slots) saves per-Desktop
- The drawer's open/closed state is session-only (defaults to closed on Desktop open)

## 6. Tier Gating (Pricing)

**Free / Baseline tier:**
- Resource Room (full)
- Unlimited Desktops (one per manuscript)
- 1 left + 1 right sidebar per Desktop
- Module drawer (full module catalog access)
- Wheelhouse, Coverage, IID dispatch, Section Navigator, etc. — all available, just multiplexed into 1+1 sidebars

**Premium / Paid tier extension:**
- All of baseline, PLUS
- 2nd left sidebar slot per Desktop
- 2nd right sidebar slot per Desktop
- Rationale: simultaneous Collaborators rail + IID rail without crowding

The upgrade prompt should appear contextually — when the user has all four sidebar slots populated AND tries to drag a fifth module into a sidebar — not as an interrupt-prompt or upsell on entry. (Refusal-as-architecture per Design v3 §7 also means the Resource Room does not sell.)

## 7. Resource Room — surface composition

### 7.1 Empty / nothing-configured state

- Top strip: brand wordmark, room title, user avatar + menu
- Left sidebar (fixed baseline): empty; affordance "drag a module from the drawer below"
- Center: welcome line + "Begin writing" primary action + three placeholder rows (Desktops, Shared Libraries, Collaborators) each with "+ create" affordance
- Right sidebar (fixed baseline): empty; same affordance as left
- Footer drawer tab (closed by default)

### 7.2 Configured state

- Top strip: same
- Left sidebar: author's configured modules (e.g., quick-jump to recent manuscript)
- Center:
  - Active Desktops list (one row per manuscript Desktop, click to enter)
  - Shared Libraries list (one row per library)
  - Collaborators list (one row per collaborator + status)
  - "+ create" affordances retained for new desktop / library / invite
- Right sidebar: author's configured modules (e.g., notifications feed, Wheelhouse)
- Footer drawer tab (closed by default)

## 8. Desktop — surface composition (per manuscript)

The Desktop hosts the 12 authoring stages (Path Choice → Submit) per `AUTHORING_FRONTEND_IMPL_2026-05-01.md` §13. The center column changes as the manuscript progresses through stages; the sidebars provide stable reference modules across stages.

- Top strip: brand, manuscript title (editable inline), locked-journal chip, autosave indicator, avatar
- Left sidebar 1 (fixed baseline): default = Section Navigator
- Left sidebar 2 (premium): empty default; author drags in (typical: Collaborators)
- Center: current stage of the 12-stage flow OR Manuscript Editor body
- Right sidebar 1 (fixed baseline): default = IID Provider Modules
- Right sidebar 2 (premium): empty default; author drags in (typical: secondary IID provider, Coverage tracker, Out-of-SLA banner expanded view)
- Footer drawer tab (closed by default)

## 9. Action surface (no design language)

| Action | Source | Effect |
|---|---|---|
| Create Desktop | Resource Room "+ create" or "Begin writing" | New Desktop appears in Desktops list; if "Begin writing", also opens to Path Choice |
| Open Desktop | Resource Room (click a desktop row) | Leaves Resource Room; enters that Desktop's current stage |
| Pull module drawer | Footer tab | Drawer rises; module palette visible |
| Drag module to slot | Drawer → sidebar slot | Slot displays module; layout saves per-Desktop |
| Drag module out of slot | Sidebar slot → drawer | Slot empties; layout saves |
| Drag module slot-to-slot | Sidebar slot → another sidebar slot | Modules swap; layout saves |
| Begin writing (Resource Room) | Center action | Creates new Desktop + opens Path Choice |
| Locked-journal chip click | Desktop top strip | Opens journal-rail switch (forces RESTRUCTURED if outside candidate array) |
| Autosave indicator click | Desktop top strip | Opens version timeline |
| Avatar | Top strip | User menu (profile, settings, sign out) |

## 10. State persistence rules

- Sidebar layout (which modules in which slots) — per-user-per-Desktop
- Drawer open/closed — session-only (resets to closed)
- Manuscript content — autosaved 2s debounce
- Sidebar collapse / pin state — per-user-per-Desktop
- Tier (free / premium) — user-level account state; affects which slots are renderable

## 11. What this model does NOT specify (deferred)

- Visual / color / typography choices (separate post-wireframe pass)
- Specific keyboard shortcuts for drawer / sidebar interactions
- Mobile drawer behavior beyond "collapses to overlay"
- Tier upgrade flow (handled by separate billing module)
- Cross-Desktop pinning (whether a module can be in multiple Desktops simultaneously — open question)

---

*End. This document is the structural authoring shell. Design v3 lock principles (refusal-as-architecture, journal-rail-lock, mandatory IID disclosure, custom-by-chat) apply on top of it.*
