# UXPilot Script — eaiou Multi-IID Authoring Surface

**Single consolidated prompt. Content + Modules + Menus + Actions.**

---

## Frame

Design the eaiou author writing surface where authors compose manuscripts AND invoke one or more independent IID (Intelligence-ID) provider modules to prepare and route the manuscript for peer-review submission. IID modules — Mae (Anthropic) today, OpenAI / Gemini / custom future — run **side-by-side, in parallel, never chained**. Each carries its own attribution. The author is the canonical source of the manuscript; IIDs are advisory.

The purpose of this surface is **article submission to peer review** — the author drafts, the IIDs assist (scope, clarity, methods, journal-fit, references), and the platform routes the finished manuscript through eaiou's submission pipeline. Inline IID assistance is the differentiator vs. consumer-checkout services like Manusights.

---

## Visual baseline — Metronic v9.4.10 (layout-1) + ReadEase color tokens & PWA layer

eaiou's authoring surface is a SaaS admin app, not a consumer e-book reader. The right shell is **Metronic v9.4.10's `layout-1`** (left fixed sidebar + fixed top header + main content). It ships ~1,175 pre-built HTML pages across 10 demo themes plus 17 starter-kit layout shells, all in Tailwind 3 + vanilla JS. eaiou drops in cleanly on top of FastAPI + Jinja2 because the demos are pure HTML — no React/Next required.

ReadEase is no longer the layout backbone, but stays useful as: (1) **color token source** (the y50/y75/y200/y300/b300/n40-n900 palette already proven on the responsive shell at `/tmp/eaiou-shell.html`), (2) **PWA scaffolding pattern** (service worker, manifest, offline-capable editor — Metronic ships SaaS-admin patterns, not PWA), and (3) **reader-view typography** (the manuscript-reading column for reviewers borrows from `book-trial-reading.html`). Everything else in ReadEase (e-book purchase flows, genre filters, audiobooks) drops as wrong-domain.

The Metronic kit ships at `/scratch/repos/eaiou/ui-projects/metronic/metronic-v9.4.10/`:
- `metronic-tailwind-html-starter-kit/dist/html/layout-1/` — clean shell (~6.5K lines), the eaiou layout backbone
- `metronic-tailwind-html-demos/dist/html/demo1/` — 122 fully-built pages in the same shell, source of pre-designed components/widgets/page templates we adapt
- Other variants (React, Next.js, Figma) ignored — eaiou is HTML+Tailwind+Jinja2

### Why layout-1 (and not layout-3 / layout-5 / layout-7 / layout-10)

| Layout | Sidebar | Header | Fit for eaiou |
|---|---|---|---|
| **layout-1** | **Full-width fixed left sidebar (collapsible to icon rail)** | **Fixed top with secondary toolbar** | **CHOSEN — adds mirrored right sidebar for IID outputs** |
| layout-3 | Icon-only 58px sidebar + sub-navbar | Compact | Too dense for a writing surface |
| layout-5 | 200px fixed sidebar | 54px header | Workable but layout-1's collapsible sidebar is better for FIXED+WIDE toggle |
| layout-7 | No sidebar (mega-menu top) | Mega-menu | Marketing-app pattern — wrong for editor |
| layout-10 | Dark sidebar, rounded inset | Standard | Visual style, not a structural fit; we'll borrow the dark-sidebar variant for color-mode toggle later |

**Decision:** `layout-1` is the eaiou shell. Right sidebar is added as a mirror of left's pattern (`kt-sidebar` class system applied to the opposite side; Metronic's drawer system supports both edges natively).

### What we adopt from Metronic (the layout, the components, the page templates)

Direct page-mapping (Metronic demo1 → eaiou). The naming convention `html/layout-1/...` refers to the starter kit; `html/demo1/...` refers to the 122-page demo built on layout-1.

| Metronic page (demo1) | eaiou adaptation |
|---|---|
| `dashboards/dark-sidebar.html` (and its sibling light variant) | Author dashboard — list of in-flight manuscripts, recent IID outputs, billing summary |
| `account/api-keys.html` | **IID provider API key configuration** — drop-in for Mae/OpenAI/Gemini/custom keys |
| `account/integrations.html` | **IID provider list / enable-disable per provider** |
| `account/settings.html` (and account/* siblings: appearance, notifications, activity) | Per-author settings (eaiou + IID config + billing) |
| `account/invite-a-friend.html` | Co-author invitation flow |
| `account/notifications.html` | In-app activity log (review submitted, IID output complete, etc.) |
| `user-table/app-roster.html` | **IID activity roster** (per-output table with provider, model, instance_hash, cost, timestamp) |
| `public-profile/activity.html`, `network.html`, `works.html`, `teams.html` | Author public profile + ORCID + co-authored manuscripts + collaborator network |
| `network/get-started.html` | First-time IID-module setup wizard (choose your IID provider, enter API key, pick enabled actions) |
| `authentication/welcome-message-2.html` (and authentication/* siblings) | eaiou auth flow with IID-disclosure-on-signup language injected |
| `store-client/home.html`, `store-client/product-details.html`, `store-client/shopping-cart.html`, `store-client/order-receipt.html` | **checksubmit storefront**: product catalog (8 SKUs), per-SKU detail, cart, order receipt — all the storefront pages already built |
| `store-client/my-orders.html` | Author's order history (completed reviews, in-flight reviews) |
| `store-client/search-results-grid.html`, `search-results-list.html` | **Manuscript-corpus search** (Phase 2 Crossref retrieval results) |
| `plugins/fullcalendar.html` | Submission deadline / venue calendar |

ReadEase pages mapping (still useful, but for content-archive/reader-view contexts, not layout):

| ReadEase page | eaiou adaptation |
|---|---|
| `index.html`, `home.html` | eaiou landing + author dashboard |
| `sign-in.html`, `sign-up.html`, `forgot-password.html`, `verify-otp.html`, `reset-successfully.html` | eaiou auth flow (drop-in with IID-disclosure-on-signup language) |
| `choose-favourite-books.html`, `choose-interest.html` | First-time IID-module setup wizard (choose your IID provider, enter API key, pick enabled actions) |
| `library.html` | Author's manuscript library |
| `book-details.html` | Manuscript-details page (metadata, tags, IID activity summary, history) |
| `book-trial-reading.html` | Manuscript-reader view (used by reviewers; clean reading column, generous typography) |
| `books.html`, `category-page.html` | Browse by tag / topic (manuscripts, not books) |
| `profile.html`, `edit-profile.html` | Author profile + ORCID linking |
| `settings.html`, `notification-settings.html`, `language-settings.html` | Per-author settings (extend with **IID Module Registry** page) |
| `notifications.html` | eaiou notifications (review submitted, comment received, IID action complete) |
| `about-us.html`, `privacy-policy.html`, `help-center.html` | Static pages — keep ReadEase's chrome, swap copy |

**Drop-as-irrelevant from ReadEase:** `audiobooks.html`, `listen-audiobooks.html`, `authors-page.html`, `author-details.html` (different domain — book authors), `checkout.html`, `add-new-card.html`, `payment-successfully.html` (Stripe Checkout + Metronic store-client cover ours).

### Metronic-side adoptions (the bulk)

- **`layout-1` shell** — left fixed sidebar (collapsible to icon rail) + fixed top header + main content. Add a mirrored right sidebar of the same `kt-sidebar` pattern for IID outputs.
- **Metronic's `kt-*` class system** — `kt-sidebar`, `kt-sidebar-fixed`, `kt-header-fixed`, `kt-sidebar-collapse`, `kt-drawer` (for off-canvas behavior on narrow viewports), `kt-menu` (accordion sidebar nav), `kt-modal`, `kt-toggle-active` (icon flip on collapse). All Tailwind-utility-driven; no JS framework dependency.
- **Light + dark theme via `data-kt-theme-mode` attribute** — toggle persists in `localStorage` (Metronic's existing pattern at the top of `layout-1/index.html`); maps to ReadEase's color tokens via CSS-variable layer.
- **Component library** — buttons (`kt-btn`, `kt-btn-outline`, `kt-btn-icon`), inputs, modals, accordion menus, dropdowns, scrollable wrappers (`kt-scrollable-y-hover`), badges, alerts. All pre-styled.
- **Apexcharts integration** — for dashboard widgets (manuscript-status charts, IID-cost-over-time charts, submission-pipeline funnels)
- **Keenicons icon set** — `ki-filled`, `ki-outline` glyphs already wired
- **Inter typeface** — already loaded in `layout-1`'s `<head>`; matches eaiou's existing spec

### ReadEase-side adoptions (kept narrow)

- **PWA scaffolding** (service worker, manifest, offline-capable editor) — Metronic doesn't ship PWA; we layer ReadEase's PWA setup on top of the Metronic shell
- **Reader-view typography** — `book-trial-reading.html`'s reading-column rules port to eaiou's center editor + reviewer manuscript-view
- **Color tokens** (y50/y75/y100/y200/y300, b300, n40-n900, plus dark variants) — already proven on `/tmp/eaiou-shell.html`; mapped through Tailwind CSS-variables (`--color-primary`, `--color-foreground`, etc.) so Metronic's existing theme machinery works unchanged
- **Chip-based filtering pattern** — used across manuscripts, outputs, sections (same chip styling as ReadEase's category pills)

### What we drop from Metronic

- React, Next.js, and Vite variants — eaiou is HTML+Tailwind+Jinja2; the demos in `metronic-tailwind-react-*` and `-nextjs-*` go unused
- Figma source files — no design tooling overhead (we work in HTML directly)
- Demos 2-10 — visual variants of the same `layout-1` shell with different color palettes; we pick demo1 + tweak via tokens, instead of carrying 10 demo trees
- Marketing landing pages (`saas` landing demos) — not part of the authoring surface
- `store-client` pages stay (mapped to checksubmit storefront), but other commerce demos drop

### What we drop from ReadEase

- E-book purchase + payment flows — we use Stripe metered + subscription (separate shape; documented in `manusights_competitor_mvp_plan.md`)
- Genre / language / age filters — not relevant for peer review
- Wishlist patterns — replaced by our manuscript library
- Multi-method payment checkout — Stripe Checkout handles this with its own UX
- Discover / recommendations algorithms — not part of MVP
- Neobrutalism variant — we want the academic-clean aesthetic, not neobrutalism

### What we add on top (eaiou-specific, no equivalent in either kit)

- **Mirrored right sidebar.** Metronic's `layout-1` has only a left sidebar; eaiou adds a right sidebar of the same `kt-sidebar` pattern (collapsible, drawer-on-narrow, ajax-removable) for IID provider modules + activity. The two sidebars are independently dismissible.
- **Multi-IID parallel-output rendering.** Each invoked IID renders its own card in the right sidebar simultaneously; no chaining, no synthesis. Provider chips with distinct colors (Mae=amber, OpenAI=green, Gemini=blue, Llama=purple, Custom=gray).
- **IID disclosure blocks per output card.** Mandatory, never collapsible (per ToS Compliance Doctrine §1 Rule 4). Provider name + model_family + instance_hash + timestamp visible on every output.
- **Action-verb buttons with cost surfaced.** Each IID action shows $X-per-call (or "with credit") inline on the button — e.g., "Run scope_check ($10 / 1 credit)". Maps to Metronic's button styling (`kt-btn` family) but with cost annotation.
- **Selection-to-IID floating bar.** Above any text selection in the editor, a floating action bar appears with provider-keyed action buttons. Pure addition.
- **Robust tagging system.** Cross-cutting chip-tags on manuscripts, outputs, sections, IID action types. Filterable and groupable across any list.
- **Audit-log export button.** Persistent in the IID activity panel — every IID interaction exportable as CSV/JSON for journal-submission cover letters and academic-integrity inquiries.

---

## Visual & layout direction

### Aesthetic

- **Clean light background** (warm cream / off-white, not pure white)
- **Subtle pin-stripe** background pattern at low contrast — academic-page texture, not loud
- **Inner shadows** on cells, cards, and module containers — soft inset shadow giving a slight let-in feel; outer shadows minimal
- **Academic accent colors** — red / yellow / green / blue used as highlight/state colors, not surface backgrounds
  - Red: error states, failure flags, "must-fix" tags
  - Yellow: cautions, "needs review", in-progress
  - Green: passing states, accepted, success
  - Blue: informational, IID outputs, neutral highlights
- **Rounded-rectangle buttons, 5px corner radius** — consistent across all actionable elements
- **Robust tagging system** — colored chip tags supporting multiple categories per item (status / scope / IID-provider / section / venue-target / etc.); chips support add/remove inline; tags filterable in any list

### Typography

- Serif body (academic feel) — Charter, Source Serif Pro, or similar
- Sans-serif UI chrome (top bar, buttons, menu labels) — Inter, Source Sans Pro, or similar
- Monospace for IID model identifiers, instance hashes, DOIs — JetBrains Mono or similar
- Body line-height generous (~1.6) for long-form reading

### Layout modes

The author can choose between two layout modes:

**FIXED mode (default for narrow viewports < 1280px):**
- Single column
- Editor takes full width
- IID sidebar collapses to bottom drawer or icon rail
- Output panel becomes a full-screen overlay when invoked

**WIDE mode (default for ≥ 1280px viewports):**
- Three columns: **left sidebar** | **center editor (canonical manuscript)** | **right sidebar**
- Both sidebars are **ajax-removable** — clicking a hide/show toggle slides the sidebar out without reloading the page; editor expands smoothly to fill
- Sidebars are independently dismissible — author can hide left only, right only, or both
- State persists per-author per-manuscript

### Sidebar contents in WIDE mode

**Left sidebar:**
- Section navigator (manuscript structure tree)
- Manuscript metadata (title, target venue, DOI status, submission state)
- Tag panel — show/edit tags applied to manuscript
- Version timeline (compact)

**Right sidebar:**
- IID provider module cards (one per configured IID)
- "+ Add IID Module" button at the bottom of cards
- IID Activity summary (counts, cost, expand to roster)

**Both sidebars are ajax-removable.** Click the toggle in the sidebar header to slide it out; click the rail toggle in the chrome to bring it back. No page reload. The editor center column rebalances width automatically.

### How this maps to Metronic's class system

- **FIXED mode** = body class `kt-sidebar-fixed kt-header-fixed` + `data-kt-drawer="true"` on the sidebars. On `< 1024px lg breakpoint`, Metronic's drawer system slides the sidebar in/out from the edge automatically.
- **WIDE mode** = same classes; at `lg` breakpoint and above, the sidebars become persistent panels with fixed width (`--sidebar-width`).
- **Sidebar collapse to icon rail** = body class `kt-sidebar-collapse` (toggled by the `data-kt-toggle-class="kt-sidebar-collapse"` button in Metronic's `sidebar_header`).
- **Right sidebar** = mirror of left sidebar pattern: same `kt-sidebar` classes with `border-s` swapped for `border-e` and a separate `id="sidebar_right"` + `id="sidebar_right_toggle"`. eaiou-side body class: `kt-sidebar-right-fixed` (we add this to the existing kt-* family for symmetry).
- **State persistence per-author per-manuscript** = `localStorage` keys: `kt-theme` (already in Metronic), plus eaiou-added `eaiou-sidebar-left-state` and `eaiou-sidebar-right-state` keyed on `(user_id, manuscript_id)`.

---

## Content

### Top bar
- Manuscript title (editable inline)
- Save state: saved / saving / unsaved
- Word count
- Target venue (set by author; optional)
- IID Activity chip — count of outputs this session, total cost, click → roster drawer
- User menu (settings, sign out)

### Left rail — Section Navigator
- Tree view of manuscript sections: Abstract, Introduction, Methods, Results, Discussion, References, plus user-defined
- Each section shows a small badge if any IID outputs exist for it ("Methods: 2 IID notes")
- Click section name → editor jumps to anchor; drag-reorder supported

### Center — Editor body
- Markdown-backed rich text (LaTeX math, citations, tables, code blocks)
- Selection-to-IID-action floating bar appears just above any text selection
- Margin comments visible when an IID output has been "Inserted as comment"
- Cursor position visible in footer

### Right rail — IID Module Sidebar
- One card per configured IID provider
- Below the cards: "+ Add IID Module" button

### Right drawer (overlay) — IID Output Panel
- Auto-opens on first output of session; can be pinned
- Lists output cards (most recent at top)
- Filter row: by provider / by action / by section / by time
- Footer: session totals + [Export audit log]

### Footer ribbon
- Recent IID outputs as compact chips ("Mae: clarity_check on §3 paragraph 2 — 3 min ago")
- Click chip → expands the relevant output card in the right drawer

---

## Modules

### IID Provider Module Card (each provider has one)

Stacked top to bottom:

1. **Provider chip** — colored token. Mae = warm-gold / Anthropic. OpenAI = green / OpenAI. Gemini = blue. Llama = purple. Custom = neutral-gray.
2. **Provider name + model family** — "Mae" header, "Anthropic claude-sonnet-4-6" subline
3. **Status + quota** — "idle | 12/50 calls used today" (or running / disabled / error / stub)
4. **Latency expectation** — "typical 5–15s"
5. **Action verb buttons** — one per enabled SKU; each button shows its $ cost; clicking opens the action confirmation modal
6. **Disclosure block** — "instance_hash: abc12345 | session opened: now"; always visible, never collapsible; [View full disclosure] link
7. **Per-card controls** — [Settings] [Disable] [Help]

States: idle / running (spinner + elapsed counter) / complete (last-run summary) / disabled / error / stub / unconfigured.

### IID Output Card (each output produces one)

Stacked top to bottom:

1. **Header strip** — provider chip + action label ("scope_check on §Abstract") + relative timestamp
2. **Source-text block** — collapsible; shows the exact text the IID was given + word count + section reference
3. **Result body** — structured if handler returned structure (in_scope, confidence, reasoning, similar_papers); markdown-rendered if prose
4. **Disclosure block** — Mae · claude-sonnet-4-6 · inst abc1234 · 2 min ago; expands to full record on click
5. **Cost record** — $0.07 via subscription credit (or Stripe meter, or partner key)
6. **Action buttons** — [Copy] [Insert as comment] [Hide] [Re-run] [+IID]

Variant — **Multi-IID Comparison Card** (for parallel runs):
- Header shows all participating IID chips + shared action verb
- Body has 2-up or 3-up columns, one per IID
- Each column has its own disclosure + cost + actions
- Banner: "All IIDs ran on identical source text — no chaining"
- No auto-synthesis — author writes synthesis themselves

### Add-IID Modal

- Provider radio buttons: Mae (recommended) / OpenAI (coming soon) / Gemini (coming soon) / Llama (coming soon) / Custom (advanced)
- API key input (paste from provider's dashboard)
- Daily call quota (default 50)
- Monthly $ cap (default $50)
- Enabled actions checklist (8 SKUs; all checked by default)
- Disclosure preview: "Mae (claude-sonnet-4-6, instance [generated on first call])"
- [Cancel] [Add module]

### Module Registry View (settings page)

- List of configured IID modules (cards, like sidebar but expanded)
- Per-module: configure / disable / remove buttons
- Add IID Module CTA at bottom

---

## Menus

### Top-bar menu
- Manuscript title (click → rename inline)
- Save state indicator (passive)
- IID Activity chip (click → IID Activity drawer)
- User menu: Profile / Settings / Module Registry / Audit Logs / Sign Out

### Section Navigator context menu (right-click on a section)
- Add subsection
- Rename
- Move to top / bottom
- View IID outputs for this section
- Delete section

### Editor selection floating bar (appears on text selection)
- "Mae: scope_check"
- "Mae: clarity_check"
- "Mae: methods_check"
- "+ More…" → opens full action selector menu with all enabled IIDs and SKUs

### Editor right-click context menu (extended menu)
- Cut / Copy / Paste / Select all
- Insert: link / image / citation / footnote / equation
- Send selection to IID:
   - Mae → scope_check / clarity_check / methods_check / outline_check / reference_audit
   - OpenAI → (coming soon, grayed)
- Compare across IIDs → opens multi-IID parallel-run modal

### IID module card menu
- Settings (per-module config)
- Disable (hide from sidebar; keep configuration)
- Help (link to provider docs)

### IID output card menu (the action buttons row)
- Copy (clipboard)
- Insert as comment (adds margin comment on relevant section)
- Hide (collapse; not delete)
- Re-run (same IID, same prompt, new output card)
- +IID (open multi-IID parallel-run modal scoped to this prompt)

### Output panel filter bar
- Provider: All / Mae / OpenAI / [each]
- Action: All / scope_check / journal_select / clarity_check / methods_check / reference_audit / outline_check / full_review / premium_review
- Section: All / §Abstract / §Introduction / §Methods / etc.
- Time: This session / Today / Last 7 days / All time

### IID Activity drawer (top-bar chip click)
- Per-IID: provider name + model + counts + cost + [Disable provider]
- Total: outputs across all IIDs + total spend
- [Export full audit log]

---

## Actions

### Action verb catalog (per SKU)

| Verb (button label) | Default scope | What it returns |
|---|---|---|
| Check scope | manuscript or selected section | in_scope:bool, confidence, reasoning, similar_papers |
| Suggest journal | abstract or full manuscript | recommended_venues:list (3 venues with reasoning) |
| Check clarity | selected paragraph | clarity_score, issues:list, suggested_rewordings |
| Check methods | methods section | adequacy:bool, gaps:list, reproducibility_flags |
| Audit references | references section | issues:list (off-topic, outdated, missing) |
| Check outline | full manuscript | structure_assessment, missing_sections, suggested_reordering |
| Full review | full manuscript | bundled scope+clarity+methods (~5min latency) |
| Premium review | full manuscript | depth review with possible human-in-loop disclosure (~24h) |

Each verb is a button on the IID provider's module card. Each button shows its $ price. Clicking opens the action confirmation modal.

### Action Confirmation Modal (every IID call passes through this)

Zones top to bottom:

1. Header: "Run scope_check with Mae" + close button
2. Provider summary: model_family + latency expectation + cost + billing path (subscription credit / Stripe meter / partner key)
3. Source-text preview: exact text the IID will see; collapsible if long; word count; author can narrow scope (e.g., paragraph instead of section) before running
4. Action-specific inputs: parameters required by the action — scope_check needs target venue dropdown; journal_select needs nothing; clarity_check is fine with just source text
5. Disclosure preview: the disclosure block that will be attached to the result
6. Buttons: [Cancel] [Run for $X.XX] — the price is in the button label so it's unmissable

### Multi-IID Parallel-Run Modal

Same as single-IID modal but:
- Provider section lists all selected IIDs (one row per IID with chip + cost)
- Total cost summed at bottom
- Source-text shown once with banner: "All selected IIDs will receive identical source text. No chaining."
- Run button: "Run with N IIDs for $X.XX"

### Output-card actions

- **Copy** — copies result body to clipboard
- **Insert as comment** — adds margin comment on relevant section, attributed to IID with full disclosure
- **Hide** — collapses card (immutable; never deletes)
- **Re-run with same IID** — produces new output card; original preserved with `superseded by` link
- **+IID** — opens multi-IID parallel-run modal pre-filled with same source + same SKU

### Auxiliary actions (in IID Activity drawer, settings, etc.)

- **Add IID Module** — opens Add-IID modal
- **Configure provider** — opens per-module config panel
- **Disable provider** — hides from sidebar; preserves configuration
- **Remove provider** — destroys configuration; preserves output history (immutable)
- **Rotate API key** — replace stored key without removing module
- **Export audit log** — generates JSON or CSV of every IID interaction
- **Save manuscript version** — manual snapshot with optional label
- **Restore version** — rollback editor to a prior snapshot

### Idempotency

Every action carries an Idempotency-Key. Re-clicking "Run" within 5 minutes returns the existing in-flight or completed action — never double-charges. Modal shows "This action is already running" if duplicate detected.

---

## Critical invariants for UXPilot output

1. Each IID is rendered as a SEPARATE bordered card with its own provider color
2. Output cards show full disclosure (provider, model, instance_hash) — never collapsible
3. Multi-IID comparison cards show side-by-side columns with the "no chaining" banner
4. No "synthesize" button anywhere in the UI
5. No automatic IID-on-IID handoff anywhere
6. No "AI helper" generic branding — every output names its specific IID
7. Cost is visible on every action button before invocation
8. Author can disable any provider without affecting others

---

## Output requested from UXPilot

Generate as a single composite design:

- Editor view with one Mae module card + OpenAI placeholder card in sidebar, output drawer closed
- Editor view with selection floating bar visible above selected text
- Action Confirmation Modal for scope_check
- Multi-IID Parallel-Run Modal for clarity_check on Mae + OpenAI
- Output drawer open with mix of single-IID cards + one multi-IID comparison card
- IID Activity drawer (top bar)
- Add-IID Modal
- Module Registry settings page
- Selection-to-IID right-click context menu
- IID output card menu (action buttons row close-up)

That's the complete set. No states/disclosure/versioning/accessibility files in this script — those are downstream visual concerns that follow from the content/module/menu/action structure above.
