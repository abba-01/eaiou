# UXPilot Prompt — eaiou Writing Surface

**Title:** eaiou Author Editor — Manuscript Writing Surface

---

## Frame

This is the **canonical source-of-truth** zone of the authoring workflow. The author writes here. Everything else (IID modules, outputs, suggestions) is auxiliary. The writing surface owns the manuscript; the rest are advisors.

The author should be able to forget the IID modules exist when they want to. The writing experience must not be cluttered or hijacked by AI affordances. The IID sidebar is always-on but visually quiet when not in use.

---

## Layout dimensions

- Default width: **65–75% of viewport** at desktop sizes
- IID sidebar: 25% (fixed)
- Output panel: collapsible drawer (default closed; appears as a 30% right-side overlay when invoked)
- Below 1280px viewport: sidebar collapses to icon-rail; below 768px: stacks vertically

---

## Sections of the writing surface

1. **Title bar** — manuscript title (editable inline), save state indicator (saved / saving / unsaved), word count, target venue (if set), DOI (if claimed)
2. **Section navigator** — left rail with collapsible section list (Abstract / Introduction / Methods / Results / Discussion / References / etc.); user-defined sections supported; click jumps to anchor; drag-reorder
3. **Editor body** — rich-text editor (markdown-backed), supports headings, lists, blockquotes, code blocks, math (LaTeX), inline citations
4. **Footer ribbon** — always-visible row showing recent IID outputs as tiny chips ("Mae checked clarity 3 min ago"), click-to-expand
5. **Bottom-status bar** — current section, character/word count for selection, current cursor position, autosave timestamp

---

## Editor capabilities

- Markdown-with-extensions input (LaTeX math, footnotes, tables, fenced code)
- Live preview toggle (split-view OR rendered-only OR source-only)
- Citation insertion via `@` mention popover that searches a personal references library + recent papers
- Section-anchor links auto-generated from headings
- Selection-to-IID context menu (right-click or keyboard equivalent): "Send selection to Mae →" with sub-menu of action verbs
- Track changes mode (optional; off by default)
- Comments / margin notes that can be attributed either to the author or to a specific IID output

---

## IID-aware editor affordances (subtle, non-intrusive)

- **Selection-to-action** — when text is selected, a small floating action bar appears above the selection with quick-access IID verbs (Check clarity, Suggest journal, etc.) — Markdown-Slack-style. Tappable / clickable / keyboard-shortcuttable.
- **Section-level IID summary chips** — when an IID has produced output for a specific section, a small indicator pill appears in the section navigator (e.g., "Methods: 2 IID notes"). Click → output panel filtered to that section's outputs.
- **Inline IID-suggested edits as comments** — when an IID returns suggested rewording, it lands as a margin comment on the relevant paragraph, NOT as direct edits. The author has to accept/decline. Manuscript text never auto-changes.
- **No predictive autocomplete from IIDs.** The editor is an editor. AI-tab-completion-style features are explicitly OFF here — they undermine the IID-isolation discipline (autocomplete blends suggestions into the text without disclosure).

---

## Saving + sync

- **Local autosave** every 5 seconds to localStorage + IndexedDB (resilient to network drop)
- **Server sync** every 30 seconds via PATCH to `/api/v1/manuscripts/{id}`
- Manual "Save now" via Cmd/Ctrl+S
- Conflict resolution: server timestamps; if conflict, prompt author with diff
- Version snapshot taken on every IID action (so the author can see "what was the manuscript text when Mae did this scope_check?")

---

## Top-bar IID disclosure summary (CRITICAL)

The title bar contains a small **IID Activity** chip that summarizes:

- N IID outputs in this session
- M IIDs active (Mae, OpenAI when wired, etc.)
- Total cost / credits used this session

Click → opens a side drawer showing the full IID disclosure roster:
- Each IID with its model_family, current instance_hash, current rate-limit status
- "Disable provider" toggle per IID (provider-isolation: author can disable Mae without affecting other providers)
- Link to the audit-log export

This makes the active-IIDs visible at all times. Authors should never wonder which IIDs are running.

---

## Out of scope for this view

- Reviewer/editor UI (separate UXPILOT_03 / 04 files)
- Public-facing manuscript browse (UXPILOT_01)
- Admin (UXPILOT_05)
- The IID sidebar internals — see UXPILOT_AUTHORING_02
- The output panel internals — see UXPILOT_AUTHORING_03
- Subscription/billing UI — see Quick Reviews sidebar in eaiou main UI (separate file)

---

## Output requested from UXPilot

1. Full editor view, default state, no IID activity yet
2. Editor with text selected and the floating IID action bar visible
3. Editor with section navigator showing IID-output indicator pills
4. Top bar IID Activity drawer expanded
5. Mobile / narrow-viewport layout (collapsed sidebar)
6. Conflict-resolution diff modal
