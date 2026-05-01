# UXPILOT_07 — layout shells, chrome, navigation

**Tokens, schemas:** see `UXPILOT_00_design_system.md`.
**Modules referenced by name:** see `UXPILOT_06_modules.md`.

This file specifies the two layout shells (fixed and wide), the header/footer chrome that appears on every public-facing page, the observer-projection indicator, the session-lock indicator, and the navigation system.

---

## 1. Shell rules

| Property | Fixed (default) | Wide |
|---|---|---|
| Max content width | 960px centered | edge-to-edge with 32px left/right gutters |
| Main column | 640px | 720–960px (responsive within gutters) |
| Right rail | 320px | 360px |
| Pull-down extras column | — (n/a) | extra modules slide in below right rail |
| Header height | 64px | 64px |
| Footer height | 48px | 48px |
| Sticky elements | header, page-level filter bar | header, page-level filter bar, right rail (becomes scroll-locked) |
| Mobile collapse | right rail moves below content; modules stack | same as fixed; pull-down extras hidden behind a "more modules" chip |

**Toggle persistence:** localStorage key `eaiou.shell` with values `"fixed"` (default) or `"wide"`. Toggle lives in the header chrome (mono icon-toggle, see §3.4). The toggle also writes to a same-origin cookie so server-rendered pages can preempt the FOUC.

**Breakpoints:**
- Mobile: ≤ 640px (single column, header collapses to hamburger).
- Tablet: 641–1023px (single column with collapsible sidebar drawer).
- Desktop: ≥ 1024px (full shells active).
- Wide-mode minimum: ≥ 1280px (otherwise wide reverts to fixed automatically; toggle still visible).

---

## 2. Joomla template position bindings

The Joomla template (HelixUltimate) defines positions; eaiou modules bind to them.

| Position | Fixed | Wide | Used by |
|---|---|---|---|
| header-a | logo + primary nav | logo + primary nav | every page |
| header-b | search input | search input | every page |
| header-c | observer-projection chip + session-lock + shell toggle + auth widget | same | every page |
| topbar | breadcrumb + page title strip | breadcrumb + page title strip | every page |
| sidebar-right | primary right rail (modules) | primary right rail (modules) | every public page |
| sidebar-extra | — | wide-mode pull-down extras | wide-mode only |
| content-top | optional banners (governance unlock, doctrine reminders, system messages) | same | conditional |
| content-bottom | optional discovery promo strip | same | home, /papers |
| footer-a | dense link grid | dense link grid | every page |
| footer-b | observer-projection chip + sealed-audit link (admin) + status mono | same | every page |

**Admin shell (com_eaiou backend):** ignores fixed/wide toggle — always wide. Joomla admin's standard chrome positions apply (see `UXPILOT_05 §Admin chrome`).

---

## 3. Header chrome

64px tall, `--surface` bg, 1px bottom `--paper3`, sticky. Internal layout left → right:

### 3.1 Brand block (left, 240px wide)
- Logo glyph (24×24px, simple river-curve mark in `--river` — single-color SVG).
- Wordmark "eaiou" Spectral 300, 22pt, `--ink`, no italic, letterspacing -0.01em.
- Hover: glyph color shifts `--river` → `--river-l`; wordmark shifts `--ink` → `--ink2`.

### 3.2 Primary nav (center-left, flex, mono UPPERCASE 12pt tracking-wide)
**Public/guest:** `Papers · Discover ▾ · Search · About`.
**Registered (eaiou_Author):** `Papers · Discover ▾ · Search · My Papers · Submit`.
**eaiou_Reviewer:** add `Reviewer ▾` (Queue, Active reviews, Profile).
**eaiou_Editor:** add `Editorial ▾` (Papers, Assignments, Decisions, Settings — EIC only).
**eaiou_Admin:** add `Admin →` (links to /administrator/com_eaiou).

Active page nav item: 2px bottom border `--river`. Hover: 1px bottom hairline `--ink3`.

`Discover ▾` dropdown (mono, 220px wide, `--surface` bg, 1px `--paper3`, radius 4px, `0 6px 24px rgba(14,13,11,0.08)`):
- Ideas (un space)
- Open Collaboration
- Gaps (Gap Map)
- Trends

### 3.3 Search input (center-right, 280px wide)
- Mono 13pt input with placeholder `grep tag: rs:`.
- Background `--paper`, 1px `--paper3` border, radius 3px, height 32px.
- Magnifier icon `--ink3` left side.
- Focus state: 1px `--river` border + 2px `--river-ll` outer ring.
- Submit on Enter → /search?q=...

### 3.4 Right cluster (right side, mono 11pt UPPERCASE, gap 12px)
Ordered left → right:
1. **Observer-projection chip:** `HUMINT` (default). For users with `eaiou_EIC` or `eaiou_Admin` group, click → opens UNKINT confirm modal. While UNKINT active, chip becomes `UNKINT` filled `--coral-l` with mono "Nm REMAINING" countdown.
2. **Session-lock indicator:** appears only when an active TAGIT session exists for current user. Mono 11pt UPPERCASE chip `SESSION LOCK · ENCRYPTED` with subtle 1px river outline pulse animation. Click → opens active session.
3. **Shell toggle:** icon-toggle (`┃▣ ┃` for fixed, `▣ ▣ ▣` for wide), 32×32, hover bg `--paper2`. Mono micro-label below `FIXED` / `WIDE`.
4. **Auth widget:**
   - Logged out: `SIGN IN` outline button + `REGISTER` filled `--river`.
   - Logged in: IntelliD pill mono (e.g., `INT-9F2A`), click → dropdown (Profile · My Papers · Reviewer Queue [if reviewer] · Editorial [if editor] · Admin [if admin] · Sign out). Avatar deliberately absent (no identity surface).

### 3.5 Header acceptance criteria
- No date / clock / "last login" text. Ever.
- The IntelliD pill never resolves to a name string in HUMINT view.
- The shell toggle is always visible at desktop breakpoints.
- The observer-projection chip is always visible (and is `HUMINT` by default for everyone).

---

## 4. Footer chrome

48px tall, `--paper2` bg, 1px top `--paper3`. Two rows or compact single row depending on shell.

### 4.1 Footer row A (link grid, mono 11pt, `--ink2`):
Categories rendered in 4 columns (single row in compact mode):
- **About:** Doctrine · About · Contact · Status.
- **Discovery:** Papers · Ideas · Open · Gaps · Trends.
- **Account:** Sign in · Register · ORCID · IntelliD policy.
- **System:** REST API · Plugins · Modules · Privacy · Terms.

Each link 24px tall, hover color `--river`, active state 1px bottom hairline.

### 4.2 Footer row B (mono 10pt `--ink3`)
Left: `eaiou · Joomla 5.3 · com_eaiou v0.x.y · cycle q4 · doctrine v2.0`.
Right: observer-projection chip mirror · sealed-audit link (visible to admin only — coral chip) · build hash mono.

### 4.3 Footer acceptance criteria
- Links rendered as mono UPPERCASE for category headers, lowercase mono for items.
- No "© year" copyright string with absolute date — replaced with "doctrine v2.0".
- No social-media icons (intentionally — no avatars, no identity, no socialness).

---

## 5. Page title strip / topbar

Sits between header and content. 56px tall, `--surface` bg, 1px bottom `--paper3`. Three-zone layout:

| Zone | Content |
|---|---|
| Left | Breadcrumb mono 11pt UPPERCASE: `HOME / DISCOVER / IDEAS`. Each segment is a link except the active. |
| Center | Page title (Spectral 300, 28pt, `--ink`). May be omitted on dashboard pages where a hero band serves the purpose. |
| Right | Page-scoped action chip group (mono UPPERCASE 11pt outline) — e.g., "+ NEW SUBMISSION", "EXPORT CSV", "GOVERNANCE UNLOCK". |

**Page title strip can be hidden** on home, paper detail (where masthead replaces it), and submit wizard (where stepper replaces it).

---

## 6. Wide-mode pull-down extras

When wide is active and ≥ 1280px:
- The right rail expands to 360px and stacks the page's primary modules.
- Below the rail, additional modules slide down (200ms ease-in) labeled with a mono UPPERCASE 10pt header `MORE MODULES`.
- Pull-down modules are listed in `UXPILOT_06 §Module placement matrix` per page.
- A "collapse extras" link mono 11pt sits at the bottom of the pull-down section.

**Empty extras case:** if no pull-down modules apply, the section header is omitted.

---

## 7. Observer-projection mechanic (HUMINT / UNKINT)

The system supports **two projections** of the same data per `UXPILOT_PROMPT_EAIOU.md §Observer-Dependent Presentation`:

| Layer | Visible | Stripped |
|---|---|---|
| HUMINT (default) | content, progression state, tags, fork paths | timestamps, sealed metadata, IntelliD ↔ ORCID maps, raw audit chains |
| UNKINT (gov-unlock) | full structured metadata, audit chains, tensor coordinates, USO records | nothing |

**HUMINT chip behavior (default):**
- Mono 11pt UPPERCASE, `--paper2` bg, 1px `--paper3` border.
- Tooltip on hover: "you are seeing the human-presentation projection. timestamps and sealed metadata are not in this surface."

**UNKINT chip behavior (active):**
- Mono 11pt UPPERCASE, `--coral-l` bg, 1px `--coral` border, with mono `Nm REMAINING` countdown.
- Click again → modal "lock now? remaining time forfeited."
- On expiry → automatic relock + toast mono "UNKINT projection expired. HUMINT view restored."

**UNKINT activation flow:**
1. User clicks `HUMINT` chip (only `eaiou_EIC` or `eaiou_Admin`).
2. Modal opens: justification textarea (Spectral 16pt, min 80ch), scope select (this page · current paper · cycle), window select (5 / 10 / 15 min).
3. On confirm → second-key out-of-band approval (mail + admin-side prompt).
4. On approval → UNKINT projection enabled across all surfaces for the granted scope and window. Header chip changes; surfaces re-render with extra columns/fields.

**Across-page persistence:** UNKINT applies across navigation until the window expires. Sealed-audit access also requires the broader "Sealed audit" governance unlock (see `UXPILOT_05`).

**Acceptance criteria:**
- HUMINT default for every user, every session.
- No way to "remember" UNKINT preference. Each request is fresh.
- All UNKINT-only fields render with a 1px `--coral` left border in surfaces.

---

## 8. Session-lock indicator (TAGIT live session chrome)

When a user has an active TAGIT session (see `UXPILOT_03 §ASK ↔ GOBACK Session`):

**Header indicator:**
- Chip placed left of the observer-projection chip.
- Mono 11pt UPPERCASE: `SESSION LOCK · ENCRYPTED`.
- Background `--river-ll`, 1px border `--river`. Subtle 1px outer outline pulses (2s ease in/out).
- Click → /session/{session_id}.

**Page-level effect:**
- Any page the user visits shows a 4px sticky bottom strip in `--river-ll` with mono 11pt: `TAGIT session active · 3 ASKs awaiting response · open session →`.
- Strip vertical height + footer adjusts so it doesn't overlap. Animated dismiss when session is paused or TRACKed.

**No session active:** indicator absent.

---

## 9. Navigation system (graph-aware)

Navigation is graph-anchored, not tree-anchored. Per the philosophical canon, users enter through tags and follow contribution lineages.

### 9.1 Primary nav (header §3.2)

Already specified above.

### 9.2 Secondary nav (in-page, where applicable)

- **Tab strips** on paper detail, workspace, editorial paper management, reviewer paper view (see `UXPILOT_01..04`).
- **Filter rails** on list pages (Papers, Editorial, Reviewer Queue).
- **Stepper** on submission wizard.

### 9.3 Tag-based navigation overlay

Available globally via search (mono prefix `tag:` or `rs:`):
- Triggered by search input `tag:rs:NotTopic:AnotherField` or by clicking any tag pill anywhere in the system.
- Lands on `/tag/{tag-name}` (see `UXPILOT_01 §Tag landing`).
- Sibling-tag chip strip lets the user pivot between sub-tags.

### 9.4 Contribution-lineage navigation

- Author IntelliD pills (anywhere in the system) → user profile (gated to identity surface per ACL).
- "More from this q-range" module on paper detail → adjacent papers by q_signal.
- USO record links (post-TRACK) → /uso/{record_hash} read-only view (admin gov-unlock visible only).

### 9.5 Breadcrumbs

Mono 11pt UPPERCASE in topbar.
- Home / Papers / Paper Title.
- Home / Discover / Ideas.
- Home / My Papers / Paper Workspace.
- Home / Editorial / Paper / Decision.

Each breadcrumb segment is a link except the active.

### 9.6 Skip-links and accessibility

- Skip-link "skip to main content" mono 11pt, hidden until focused.
- All interactive elements meet WCAG 2.2 AA contrast on light tokens (river `#1a4a6b` on paper `#f7f4ef` → ratio 7.8:1).
- Keyboard navigation: tab order matches visual top-down/left-right order; focus ring 2px `--river-ll` outer.
- Screen-reader labels: every IntelliD pill has aria-label `IntelliD INT-9F2A`. Every tag has aria-label `tag rs:LookCollab:Statistician`.

---

## 10. Cross-page chrome banners (conditional)

These appear in `content-top` position when triggered:

| Banner | Trigger | Shape |
|---|---|---|
| Governance unlock active | UNKINT projection on, or sealed-audit unlock active | `--coral-l` bg, 4px `--coral` left, mono UPPERCASE 11pt + countdown |
| Submission window closing | Author with paper in `revisions_requested` mid-late window | `--amber-l` bg, 4px `--amber` left, Spectral italic 14pt with relative bar |
| TAGIT session active | At least one live session involving current user | `--river-ll` bg, 4px `--river` left, mono 11pt + open-session link |
| Doctrine refresh | First login after doctrine v-bump | `--violet-l` bg, 4px `--violet` left, Spectral italic 14pt + "review changes →" |
| System maintenance | Admin-set maintenance window | `--paper2` bg, 4px `--ink3` left, mono 11pt + relative-window |

**Stacking:** banners stack vertically; up to 3 visible, rest collapsed under "+N more notifications" chip.

---

## 11. Mobile shell (≤ 640px)

- Header collapses: brand + hamburger + auth pill. Nav moves into off-canvas drawer slid from left.
- Search becomes a full-width modal triggered from a mono icon in header.
- Right rail moves below main content; modules stack full-width.
- Wide toggle hidden; system enforces fixed.
- Observer-projection + session-lock chips appear inside hamburger menu first row.
- Footer becomes single column.

**Mobile acceptance:** every page must be reachable on mobile. The TAGIT session UI is the one notable surface that gets a "open in desktop for full TAGIT timeline" mono note when accessed from mobile (composer still works; structural map collapsed).

---

## 12. Print stylesheet (paper detail only)

- Hide header, footer, nav, sidebars, banners.
- Render masthead + abstract + manuscript + sources + AI usage + open reports + attribution.
- Spectral throughout; mono only for IDs and tags.
- No badges except inline `[AI-Logged]` etc as mono.
- Page-break before each tab section.
- Capstone DOI prominent at footer of print.
- **No dates anywhere.** Sealed timestamps absolutely never print.

---

## 13. Acceptance criteria for any UXPilot mockup that uses this shell

1. Header is exactly 64px, light surface, 1px bottom hairline, never a full block color stripe.
2. Footer is exactly 48px, `--paper2` bg, 1px top hairline, mono content only (no large headlines).
3. Brand glyph is a single-color river curve in `--river`. No gradient, no logo background fill.
4. Observer-projection chip is always present in HUMINT (default).
5. Shell toggle is always visible above mobile breakpoint.
6. Page title strip is 56px exactly when present.
7. Right rail starts at 320px (fixed) or 360px (wide); never wider.
8. Pull-down extras only render when wide is active AND ≥ 1280px AND the page is in the placement matrix.
9. No date/clock/relative-time string in chrome. Cycle slot label only.
10. Banners stack ≤ 3 with overflow chip.

---

## End of `UXPILOT_07_layout_shells.md`

Final file: `UXPILOT_99_index.md` — master index of every page across all files.
