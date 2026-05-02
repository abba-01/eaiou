# UXPilot Authoring-Workflow Index

**Created:** 2026-05-01 evening PDT
**For wireframing the eaiou inline-IID-assistance authoring surface**

---

## Files in this set

| # | File | Covers |
|---|---|---|
| 00 | UXPILOT_AUTHORING_00_overview.md | Master frame: three-zone layout (editor / IID sidebar / output panel), ToS-compliance principles, action vocabulary, multi-IID parallel-run rule, disclosure doctrine |
| 01 | UXPILOT_AUTHORING_01_writing_surface.md | Manuscript editor: title bar, section navigator, editor body, footer chips, IID-aware affordances, saving + sync, IID activity drawer in top bar |
| 02 | UXPILOT_AUTHORING_02_iid_sidebar.md | Right-rail IID module sidebar: per-provider cards, action verbs with prices, status + quota, disclosure block, Add-IID flow, "coming soon" placeholders, sidebar collapse |
| 03 | UXPILOT_AUTHORING_03_multi_version_panel.md | Output panel: card structure for single-IID outputs, side-by-side comparison cards for multi-IID parallel runs, filters, audit-log export, hide vs delete |
| 04 | UXPILOT_AUTHORING_04_module_registry.md | Module registry settings: list of configured IIDs, Add/Configure/Disable/Remove flows, custom IID provider setup, SAID-framework integration |
| 05 | UXPILOT_AUTHORING_05_actions.md | Action confirmation modals: source-text preview, cost surfacing, idempotency, multi-IID parallel-run modal, selection-driven invocation, disabled-action error variants |
| 06 | UXPILOT_AUTHORING_06_states.md | Lifecycle states: IID module card states, output card states, action modal states, sidebar collapse states, output panel states; visual-design rules |
| 07 | UXPILOT_AUTHORING_07_disclosure.md | SAID-framework disclosure UI: schema, compact + expanded renderings, manuscript-level roster, auto-generated AI-use-disclosure paragraph for journal submissions |
| 08 | UXPILOT_AUTHORING_08_versioning.md | Manuscript snapshot timeline + IID-output lineage: snapshot triggers, version timeline UI, output lineage cross-reference, stale-output banners, export packaging |

---

## Suggested wireframe order

If you're feeding these to UXPilot in sequence, this order produces the cleanest mental model:

1. **00 overview** first — UXPilot needs the three-zone layout + provider-isolation principle as context for everything else
2. **01 writing surface** — establishes the editor-as-canonical-source frame
3. **02 IID sidebar** — establishes the per-provider card pattern
4. **03 output panel** — establishes the parallel-not-blended output rendering
5. **05 actions** — fills in the modal pattern
6. **06 states** — fills in the visual rules across everything
7. **07 disclosure** — locks SAID-framework rendering across all surfaces
8. **08 versioning** — adds the temporal dimension
9. **04 module registry** — settings; can come last, it's not on the main flow

---

## Brand + design system

These files inherit from the existing eaiou design system:
- `UXPILOT_00_design_system.md` — typography, color, spacing, component primitives
- `UXPILOT_06_modules.md` — generic module pattern (this set extends it for IID-specific cards)
- `UXPILOT_07_layout_shells.md` — three-zone layout shells (this set instantiates one for the authoring workflow)
- `UXPILOT_08_components.md` — buttons, modals, drawers, tables, chips
- `UXPILOT_10_states.md` — generic state visuals (this set extends with IID-lifecycle states)
- `UXPILOT_11_motion.md` — animation rules (output card slide-in, modal transitions)
- `UXPILOT_12_accessibility.md` — keyboard, screen reader, color-not-sole-indicator rules

---

## Key invariants across all files

1. **IID-isolation:** every IID is a separate module with its own card, color, disclosure, quota, settings
2. **No chaining:** IIDs never receive each other's outputs as input; multi-IID runs are parallel, not sequential
3. **Author owns the manuscript:** IIDs are advisory; nothing is auto-inserted; suggestions require explicit acceptance
4. **Disclosure is doctrine:** every IID interaction carries full attribution; never collapsible, never dismissible
5. **Audit-trail immutability:** outputs can be hidden but not deleted; admin compliance can redact source but never erase the record
6. **Cost transparency:** every action shows its $ cost before invocation; cost surfacing is part of the consent flow
7. **Provider-agnostic by architecture:** the system is designed for many IIDs; today only Mae is wired but OpenAI / Gemini / custom plug in via the same module pattern from day one
8. **SAID-framework compliance:** Stripped (sealed instance_hash), Audited (full log), Identified (named provider + model), Disclosed (always-visible, never-collapsible disclosure block)

---

## What UXPilot should NOT generate

- Marketing landing pages (separate concern)
- Reviewer / editor / admin UIs (separate UXPILOT_03 / 04 / 05 files)
- Public manuscript browse (UXPILOT_01_public.md handles)
- Subscription / billing UI (use eaiou's existing Quick Reviews sidebar pattern from `manusights_competitor_mvp_plan.md`)
- Mobile-first layouts (these files specify desktop-primary; mobile shown as informational fallback)
- Auto-completion / inline AI text-prediction features (explicitly out of scope; undermines IID-isolation)
- Synthesized "consensus" output across IIDs (explicitly out of scope; author owns synthesis)

---

## Pairing with eaiou existing files

These authoring-workflow files complement the existing eaiou UXPilot set. The full eaiou design surface (post-merge) is:

- **Foundations:** UXPILOT_00 design system + UXPILOT_07 layout shells + UXPILOT_08 components + UXPILOT_10 states + UXPILOT_11 motion + UXPILOT_12 accessibility
- **Public-facing:** UXPILOT_01 public + UXPILOT_99 index
- **Author surface (extended by this set):** UXPILOT_02 author + UXPILOT_AUTHORING_00–08
- **Reviewer surface:** UXPILOT_03 reviewer
- **Editor surface:** UXPILOT_04 editor
- **Admin surface:** UXPILOT_05 admin
- **Modules:** UXPILOT_06 modules
- **Data viz:** UXPILOT_09 dataviz

---

## Next steps for Eric tonight (before sleep)

1. Paste UXPILOT_AUTHORING_00 into UXPilot first to set the architectural frame
2. Generate wireframes from 01 → 02 → 03 in order
3. Iterate on the IID sidebar card visual until you like it (it's the load-bearing element)
4. Save the generated mockups to /scratch/repos/eaiou/ui-projects/eaiou_authoring_*.html
5. Push to droplet via existing eaiou repo (`git push origin main`)
6. Sleep. The build sequence on the backend continues regardless of which mockup variant you settle on; the API contract doesn't change.
