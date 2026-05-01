# UXPILOT_99 — master index

Every page surface across all UXPILOT prompt files, with role, URL, modules, and the file/§ that defines it. Use this index to:
- Find a specific page quickly.
- Verify the design system covers every URL listed in `/repos/eaiou/specs/EAIOU_feature_inventory.md`.
- Hand off a single self-contained UXPilot prompt: locate the page below, then paste the corresponding section from the cited file.

**Foundation files (always cited):**
- `UXPILOT_PROMPT_EAIOU.md` — philosophical canon (IntelliD, TAGIT, observer projection, temporal blindness)
- `UXPILOT_00_design_system.md` — tokens, typography, schemas
- `UXPILOT_06_modules.md` — module specs
- `UXPILOT_07_layout_shells.md` — chrome, shells, navigation
- `UXPILOT_08_components.md` — atomic components (buttons, inputs, tables, modals, drawers, etc.)
- `UXPILOT_09_dataviz.md` — chart geometry (q-bar, sparkline, segmented bar, heatmap, network graph, etc.)
- `UXPILOT_10_states.md` — state catalog & copy library (loading, empty, error, success, sealed)
- `UXPILOT_11_motion.md` — motion timings, focus rings, hover transitions, lifecycles

---

## 1. Master page index

| # | Page | Role / ACL | URL | Defined in | Right rail (default) | Wide-mode pull-down |
|---|---|---|---|---|---|---|
| 1 | Home / Landing | Public | `/` | UXPILOT_01 | open_collaborate · ai_usage_heatmap · trending_ideas | gap_map · intellid_graph · appreciated_scale |
| 2 | Papers list | Public | `/papers` | UXPILOT_01 | latest_papers · ai_usage_heatmap · open_collaborate | trending_ideas · gap_map |
| 3 | Paper detail | Public | `/paper/{id}/{slug}` | UXPILOT_01 | latest_papers (q-range) · open_collaborate | ai_usage_heatmap (paper) · intellid_graph · appreciated_scale |
| 4 | Discover — Ideas | Public | `/discover/ideas` | UXPILOT_01 | trending_ideas · open_collaborate · gap_map | intellid_graph · ai_usage_heatmap |
| 5 | Discover — Open Collaboration | Public | `/discover/open` | UXPILOT_01 | open_collaborate · trending_ideas · ai_usage_heatmap | — |
| 6 | Discover — Gap Map | Public | `/discover/gaps` | UXPILOT_01 | gap_map (full-bleed) · trending_ideas · open_collaborate | — |
| 7 | Discover — Trends | Public | `/discover/trends` | UXPILOT_01 | trending_ideas (full) · gap_map · ai_usage_heatmap | — |
| 8 | Search | Public | `/search?q=` | UXPILOT_01 | trending_ideas · open_collaborate | — |
| 9 | Tag landing | Public | `/tag/{tag-name}` | UXPILOT_01 | open_collaborate · trending_ideas | — |
| 10 | Login | Public | `/login` | UXPILOT_01 | — | — |
| 11 | Register | Public | `/register` | UXPILOT_01 | — | — |
| 12 | Forgot password | Public | `/forgot-password` | UXPILOT_01 | — | — |
| 13 | Reset password | Public | `/reset-password?token=` | UXPILOT_01 | — | — |
| 14 | 404 Not Found | Public | any | UXPILOT_01 | — | — |
| 15 | About | Public | `/about` | UXPILOT_01 | — / latest_papers | — |
| 16 | Doctrine | Public | `/doctrine` | UXPILOT_01 | — | — |
| 17 | My Papers | eaiou_Author | `/mypapers` | UXPILOT_02 | open_collaborate · trending_ideas | ai_usage_heatmap (author) · appreciated_scale |
| 18 | Paper Workspace | eaiou_Author / Editor | `/paper/{id}/workspace` | UXPILOT_02 | open_collaborate · appreciated_scale | intellid_graph · ai_usage_heatmap |
| 19 | Submit wizard | eaiou_Author | `/submit` | UXPILOT_02 | — (focus mode) | — |
| 20 | Revise upload | eaiou_Author | `/paper/{id}/revise` | UXPILOT_02 | open_collaborate (filtered) | — |
| 21 | Reviewer Queue | eaiou_Reviewer | `/reviewer/queue` | UXPILOT_03 | open_collaborate · trending_ideas | ai_usage_heatmap · intellid_graph |
| 22 | Reviewer Paper View | eaiou_Reviewer | `/reviewer/paper/{id}` | UXPILOT_03 | intellid_graph · appreciated_scale · open_collaborate | ai_usage_heatmap |
| 23 | Reviewer Rubric Console | eaiou_Reviewer | `/reviewer/paper/{id}/review` | UXPILOT_03 | — (focus) | intellid_graph |
| 24 | TAGIT Session (ASK↔GOBACK) | Reviewer + Author | `/session/{session_id}` | UXPILOT_03 | — / structural map | — |
| 25 | Reviewer Profile | eaiou_Reviewer | `/reviewer/profile` | UXPILOT_03 | — | — |
| 26 | Editorial Papers | eaiou_Editor+ | `/editorial/papers` | UXPILOT_04 | editor_dashboard · open_collaborate | ai_usage_heatmap · gap_map · intellid_graph |
| 27 | Paper Management Panel | eaiou_Editor+ | `/editorial/paper/{id}` | UXPILOT_04 | intellid_graph · appreciated_scale · open_collaborate | ai_usage_heatmap |
| 28 | Reviewer Assignment | eaiou_Editor+ | `/editorial/assign/{id}` | UXPILOT_04 | — (focus) | — |
| 29 | Decision Render | eaiou_Editor+ (some EIC-only) | `/editorial/decide/{id}` | UXPILOT_04 | — (focus) | — |
| 30 | Editor Settings | eaiou_EIC | `/editorial/settings` | UXPILOT_04 | — | — |
| 31 | Admin Dashboard | eaiou_Admin | `/administrator/index.php?option=com_eaiou&view=dashboard` | UXPILOT_05 | — / KPI grid | — |
| 32 | Papers manager | eaiou_Admin | `view=papers` | UXPILOT_05 (list-manager pattern) | left filter rail | — |
| 33 | AI Sessions manager | eaiou_Admin | `view=ai_sessions` | UXPILOT_05 | filter rail | — |
| 34 | AI Session detail | eaiou_Admin / EIC | `view=ai_session&id={id}` | UXPILOT_05 | — | — |
| 35 | Didn't Make It manager | eaiou_EIC / Admin | `view=didntmakeit` | UXPILOT_05 | filter rail | — |
| 36 | Didn't Make It detail | eaiou_EIC / Admin | `view=didntmakeit&id={id}` | UXPILOT_05 | — (gov unlock) | — |
| 37 | Remsearch manager | eaiou_Admin | `view=remsearch` | UXPILOT_05 | filter rail | — |
| 38 | Review Logs manager | eaiou_Admin | `view=review_logs` | UXPILOT_05 | filter rail | — |
| 39 | Versions manager | eaiou_Admin | `view=versions` | UXPILOT_05 | filter rail | — |
| 40 | Attribution manager | eaiou_Admin | `view=attribution` | UXPILOT_05 | filter rail | — |
| 41 | Quality Signals manager | eaiou_Admin | `view=quality_signals` | UXPILOT_05 | filter rail | — |
| 42 | Plugins Used (audit) | eaiou_Admin | `view=plugins_used` | UXPILOT_05 | filter rail | — |
| 43 | API Keys manager | eaiou_Admin | `view=api_keys` | UXPILOT_05 | filter rail | — |
| 44 | API Key detail | eaiou_Admin | `view=api_key&id={id}` | UXPILOT_05 | — | — |
| 45 | API Logs manager | eaiou_Admin | `view=api_logs` | UXPILOT_05 | filter rail | — |
| 46 | Templates manager | eaiou_Admin / EIC | `view=templates` | UXPILOT_05 | filter rail + preview | — |
| 47 | Modules manager | eaiou_Admin | `view=modules` | UXPILOT_05 | position map | — |
| 48 | Articles bridge view | eaiou_Admin | `view=articles_bridge` | UXPILOT_05 | — | — |
| 49 | Settings (component config) | eaiou_Admin | `view=options` | UXPILOT_05 | — | — |
| 50 | Sealed Audit (gov unlock) | eaiou_EIC / Admin | `view=sealed_audit` | UXPILOT_05 | — | — |

---

## 2. Module index (referenced from page table above)

| Module | Tier | Defined in |
|---|---|---|
| `mod_reviewer_queue` | canonical (SSOT §3.2) | UXPILOT_06 |
| `mod_editor_dashboard` | canonical | UXPILOT_06 |
| `mod_latest_papers` | canonical | UXPILOT_06 |
| `mod_open_collaborate` | canonical | UXPILOT_06 |
| `mod_ai_usage_heatmap` | canonical | UXPILOT_06 |
| `mod_gap_map` | design-derived (flag for SSOT promotion) | UXPILOT_06 |
| `mod_trending_ideas` | design-derived | UXPILOT_06 |
| `mod_intellid_graph` | design-derived | UXPILOT_06 |
| `mod_appreciated_scale` | design-derived | UXPILOT_06 |

---

## 3. Coverage cross-check vs feature inventory

This index covers every URL listed in `/repos/eaiou/specs/EAIOU_feature_inventory.md` plus the `/research/*`, `/ideas/*`, `/collaboration/*`, `/trend/*`, `/gap/*` REST endpoints (which surface as discover pages and modules), plus the 11 com_eaiou tables (each manifests as one admin manager view, plus detail views where they have unique workflows).

Inventory items NOT covered as a dedicated page (intentional — they are background processes or deep-linked endpoints, not first-class UI surfaces):
- `/trace/entropy` — Entropy Trace Map generation; surfaces as a chart embedded in paper detail (Sources tab) rather than a dedicated page.
- `/dataset/link` — cross-link panel embedded in paper detail (Datasets tab).
- `/ai/log` — embedded in paper detail (AI Usage tab) and reviewer paper view (AI Session Log tab).
- `/export/context` — invoked from My Papers action menu; modal flow, not a page.
- `/register/observer` — Ed25519 PKI registration; embedded in /reviewer/profile and /editorial/settings (not a separate page).
- `/research/seek` — surfaced as a modal flow from /discover/open ("post your own seek"), not a page.

---

## 4. ACL coverage check

| Group | Pages reachable |
|---|---|
| Public | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16 |
| Registered (base) | + auth pages, + read-only access to public set |
| eaiou_Author | + 17, 18, 19, 20 |
| eaiou_Reviewer | + 21, 22, 23, 24, 25, plus full reviewer-tier of 18 |
| eaiou_Editor | + 26, 27, 28, 29 |
| eaiou_EIC | + 30, + governance unlock surfaces (50) |
| eaiou_Admin | + 31..50 |
| eaiou_APIClient | API endpoints only (programmatic; no UI surfaces beyond the keys + logs visible to admin) |

Key permissions matrix lives in `/repos/eaiou/SSOT.md §4.3`. Per-page ACL details in each page's prompt entry.

---

## 5. UXPilot operating procedure

To generate a single mockup:

1. Find the page in the table above. Note the **defined-in** file.
2. Open that file (e.g., `UXPILOT_01_public.md`) and locate the page block by name.
3. Read the foundation citations at the top of the file.
4. Paste the **page block + the cited foundation sections** into UXPilot. Cited sections are typically:
   - `UXPILOT_00 §3` (color tokens, light)
   - `UXPILOT_00 §2` (typography)
   - `UXPILOT_00 §6` (layout shells)
   - `UXPILOT_00 §7` (module shell schema)
   - `UXPILOT_00 §8` (badge schema)
   - `UXPILOT_06 §<each named module>` (module specs)
   - `UXPILOT_07 §3, §4` (header + footer chrome)
   - `UXPILOT_08 §<components used>` (buttons, inputs, tables, modals, drawers, toasts)
   - `UXPILOT_09 §<charts referenced>` (chart geometry per visualization)
   - `UXPILOT_10 §2-§6` (state specs for the surface zone)
   - `UXPILOT_11 §17` (allowed animation list — anything else, remove)
   - `UXPILOT_PROMPT_EAIOU.md §Observer-Dependent Presentation` (HUMINT/UNKINT framing)
5. Adjust UXPilot's mockup size to one of: 1440×900 (fixed), 1920×1080 (wide), 768×1024 (tablet), 390×844 (mobile).
6. Validate the output against `UXPILOT_00 §12` + `UXPILOT_08 §23` + `UXPILOT_09 §22` + `UXPILOT_10 §14` + `UXPILOT_11 §18` (acceptance criteria).

---

## 6. Verification checklist (post-mockup)

For each generated mockup, confirm:

**Typography & color (UXPILOT_00):**
- [ ] Spectral renders for body and headlines.
- [ ] JetBrains Mono renders for IDs, tags, badges, metadata.
- [ ] Backgrounds use `--paper` (page) and `--surface` (cards).
- [ ] River-blue `--river` is the only solid accent appearing as button fills, links, and primary chart axes.
- [ ] Amber, sage, coral, violet appear only in tags, badges, chart segments — never as block backgrounds.

**Doctrine (UXPILOT_PROMPT_EAIOU + UXPILOT_07):**
- [ ] No timestamps, no "posted X ago", no date columns in HUMINT view.
- [ ] Sort labeled "by q_signal".
- [ ] Author identity is IntelliD pill in HUMINT view — never a name string.
- [ ] Observer-projection chip visible in header (HUMINT default).
- [ ] No avatar / profile photo / initials anywhere (per `UXPILOT_08 §14`).

**Layout (UXPILOT_07):**
- [ ] Header is 64px exactly, footer 48px exactly.
- [ ] Wide-mode pull-down extras only present in wide layouts ≥ 1280px.
- [ ] Right rail width 320px (fixed) or 360px (wide).
- [ ] No social-media icons in footer; categories rendered as mono UPPERCASE.

**Components (UXPILOT_08):**
- [ ] No two filled `--river` primary buttons in the same view zone.
- [ ] Every input has a visible mono label above it (no floating labels).
- [ ] Tables render no date columns in HUMINT view.
- [ ] Pagination uses fixed page size (no page-size selector).
- [ ] Hairline 1px borders. No drop shadows on cards.

**Dataviz (UXPILOT_09):**
- [ ] At least one chart/sparkline/bar exists per dashboard or paper page.
- [ ] Color encoding matches §20: river=primary, violet=AI, amber=warning, coral=error/late, sage=accepted/early.
- [ ] No 3D, no gradients, no glow on charts.
- [ ] Hairline 1px baselines/borders only on chart frames.

**States (UXPILOT_10):**
- [ ] Empty copy uses §3 library where applicable (Spectral italic poetic-honest).
- [ ] Errors never apologetic; coral accent only; always offer action.
- [ ] Success is quiet (toast or modal-confirm; no celebration).
- [ ] Sealed renders with `····` placeholder + sealed badge.

**Motion (UXPILOT_11):**
- [ ] Every animation in mockup appears in `UXPILOT_11 §17` allowed list.
- [ ] Focus rings use `--river-ll` uniformly.
- [ ] Reduced-motion preference handled.
- [ ] No background animations, parallax, or scroll-triggered reveals.

---

## 7. Open follow-ups (for Eric)

1. **SSOT promotion of design-derived modules** — once UXPilot mockups validate the four design-derived modules (`gap_map`, `trending_ideas`, `intellid_graph`, `appreciated_scale`), update `/repos/eaiou/SSOT.md §3.2` Module list.
2. **eaiou-admin Tailwind config migration** — replace primary 50–900 grayscale with canonical 19-token palette + Spectral/Mono fonts. Out of scope for this prompt set; planned as a follow-up commit on `/repos-private/eaiou-admin/` (manual upload by Eric per repo workflow rule).
3. **Dark-mode mockups** — tokens are defined; mockups deferred. When ready, re-run the same prompt set with palette directive switched to `:root[data-theme="dark"]`.
4. **TAGIT session backend** — `eaiou_tagit_sessions` table referenced but not in the original 11-table com_eaiou schema. Add to schema before TAGIT UI ships.
5. **USO record format** — single source of truth post-TRACK; needs format spec (mono YAML or JSON) before USO viewer page lands.
6. **Joomla template position binding** — verify HelixUltimate position names match the bindings in `UXPILOT_07 §2` (header-a/b/c, sidebar-right, sidebar-extra, content-top/bottom, footer-a/b).
7. **Mobile TAGIT timeline** — desktop-first; mobile composer works but structural map collapses; revisit if mobile reviewer use grows.

---

## End of `UXPILOT_99_index.md`

All thirteen UXPilot prompt files complete. Hand off to UXPilot per §5 above.

**File ledger (line counts as of last update):**
- `UXPILOT_PROMPT_EAIOU.md` — 256 (canon)
- `UXPILOT_00_design_system.md` — 250 (foundation tokens, schemas)
- `UXPILOT_01_public.md` — 461 (16 public pages)
- `UXPILOT_02_author.md` — 288 (4 author pages)
- `UXPILOT_03_reviewer.md` — 220 (5 reviewer pages)
- `UXPILOT_04_editor.md` — 231 (5 editor pages)
- `UXPILOT_05_admin.md` — 326 (20 admin pages)
- `UXPILOT_06_modules.md` — 309 (9 modules)
- `UXPILOT_07_layout_shells.md` — 307 (chrome, shells, observer-projection, session-lock)
- `UXPILOT_08_components.md` — 514 (atomic components — buttons, inputs, tables, modals, drawers, toasts, dropdowns, pagination, accordions, steppers, tooltips, skeletons, icons, banners, code, cards, forms)
- `UXPILOT_09_dataviz.md` — 502 (chart geometry — q-bar, sparkline, segmented bar, stacked bar, heatmap, network graph, ranked-list, KPI grid, relative-window glyph, rubric scale, multiplier, entropy trace, histogram, cycle slot timeline, color encoding, tooltip pattern)
- `UXPILOT_10_states.md` — 341 (state catalog — loading/empty/error/success/sealed/not_permitted/not_found/maintenance, copy library, voice rules)
- `UXPILOT_11_motion.md` — 371 (motion philosophy, timing catalog, focus rings, hover/active transitions, lifecycle specs, reduced-motion, allowed animation inventory)
- **Total: ~4,376 lines across 13 files.**
