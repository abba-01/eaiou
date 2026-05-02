# UXPilot Prompt — eaiou Action Verbs + Modals

**Title:** eaiou Action Vocabulary — Per-IID Action Modals + Confirm Flow

---

## Frame

Every IID-action invocation passes through a confirmation modal. This is doctrine, not friction: the modal is where the author sees exactly what will be sent, what it costs, and gives explicit consent. No background actions; no auto-runs. Each invocation is a deliberate act.

The modal also surfaces the **idempotency key** behavior so the author understands re-clicking won't double-charge.

---

## Eight action verbs (the SKU catalog)

Per `manusights_competitor_mvp_plan.md` §0.1:

| SKU | Verb | Default scope | Output shape |
|---|---|---|---|
| `scope_check` | "Check scope" | manuscript or selected section | in_scope:bool, confidence, reasoning, similar_papers |
| `journal_select` | "Suggest journal" | abstract or full manuscript | recommended_venues:list, excluded_venues |
| `clarity_check` | "Check clarity" | selected paragraph | clarity_score, issues:list, suggested_rewordings |
| `methods_check` | "Check methods" | methods section | adequacy:bool, gaps:list, reproducibility_flags |
| `reference_audit` | "Audit references" | references section | issues:list (off-topic, outdated, missing) |
| `outline_check` | "Check outline" | full manuscript | structure_assessment, missing_sections, suggested_reordering |
| `full_review` | "Full review" | full manuscript | bundled scope+clarity+methods, ~5min |
| `premium_review` | "Premium review" | full manuscript | depth review, may include human-in-loop disclosure, ~24h |

---

## Action confirmation modal

When the author clicks any action button:

```
┌────────────────────────────────────────────────────┐
│  Run scope_check with Mae                  [×]     │
│  ────────────────────────────────────────────────   │
│                                                     │
│  Provider: Mae (Anthropic, claude-sonnet-4-6)       │
│  Action: scope_check                                │
│  Latency target: 5–15 seconds                       │
│  Cost: $0.07 (covered by Pro subscription credit)   │
│                                                     │
│  ────────────────────────────────────────────────   │
│  Source text (what Mae will see):                   │
│  ┌────────────────────────────────────────────┐     │
│  │ §Abstract                                   │     │
│  │ "We propose a multidimensional intake      │     │
│  │  architecture for forensic-clinical use    │     │
│  │  that preserves the content of validated   │     │
│  │  1D instruments while changing the response│     │
│  │  surface from scalar endorsement to..."    │     │
│  │ [432 words; full text shown on expand]     │     │
│  └────────────────────────────────────────────┘     │
│                                                     │
│  Target venue (for scope_check):                    │
│  [Journal of Forensic Psychology      ▼]           │
│                                                     │
│  ────────────────────────────────────────────────   │
│  Disclosure block that will be attached to result:  │
│   Mae (claude-sonnet-4-6, instance abc1234)         │
│                                                     │
│  ────────────────────────────────────────────────   │
│  [Cancel]                          [Run for $0.07]  │
└────────────────────────────────────────────────────┘
```

---

## Modal zones

1. **Header:** action verb + provider name + close button
2. **Provider/action summary:** model_family, latency expectation, cost, billing path (subscription credit / Stripe meter / partner-key)
3. **Source-text preview:** the exact text the IID will see; collapsible if long; shows word count; author can edit the source-text scope right here (e.g., narrow to a paragraph rather than full section) before running
4. **Action-specific inputs:** parameters required by the action (e.g., `scope_check` needs a target venue dropdown; `journal_select` doesn't; `clarity_check` is fine with just the source text)
5. **Disclosure preview:** the disclosure block that will be attached to the output (transparency before invocation)
6. **Action buttons:** Cancel + Run-for-$X (the $ is in the button label so the cost is unmissable)

---

## Idempotency

Every action carries an **Idempotency-Key** (UUID generated client-side). If the author clicks "Run" twice within a short window:

- Second click is detected via the same Idempotency-Key
- Modal shows "This action is already running. Wait for the result or cancel."
- No double-charge

The key persists for 5 minutes; after that, a re-click counts as a new action (new key generated automatically).

---

## Multi-IID parallel-run modal

When the author wants to run the same SKU across multiple IIDs:

Either:
- Select multiple IID checkboxes in the sidebar before clicking action (sidebar shows checkbox per card when any action verb is hovered), OR
- Click "+IID" on an existing output card to run the same action with another IID

The multi-IID modal looks similar to the single-IID modal, but:
- **Provider section** lists all selected IIDs (one row per IID with chip + cost)
- **Total cost** is summed at the bottom
- **Source text is identical for all** — the modal shows the source ONE time, with a banner: "All selected IIDs will receive identical source text. No chaining."
- Run button: "Run with N IIDs for $X.XX"

After confirm, all selected IIDs run **in parallel** (separate API calls, separate sessions). Results land as a side-by-side comparison card in the output panel.

---

## Selection-driven action invocation (right-click / floating bar)

When the author has text selected in the editor:

- A floating action bar appears just above the selection
- Buttons: "Mae: scope_check / clarity_check / methods_check" + "+more"
- Clicking opens the action modal scoped to the selection (source text is pre-filled with the selected text)
- Right-click opens an extended menu with all enabled IID-action combinations
- Keyboard shortcuts available: Cmd+Shift+M for "Mae menu"; configurable per IID

This makes inline IID action a first-class affordance without cluttering the editor chrome.

---

## Disabled action handling

If the author tries to invoke an action they can't:

- **Out of quota:** modal shows "Quota exhausted for Mae today. Resets at [time]. Upgrade to Pro for higher limits or wait." with [Upgrade] and [Cancel] buttons.
- **Out of $ cap:** modal shows "$ cap hit for this month. [Raise cap] [Cancel]"
- **Provider down:** modal shows "Mae's API is currently unreachable. [Retry] [Cancel]" — eaiou pings provider health endpoint before opening
- **Stub mode (Phase 0):** modal shows "Mae is in stub mode for this action — you'll receive a placeholder result, not a real review. Real handler ships [date]. Continue?" with explicit [Continue with stub] [Cancel]

---

## Action history

Every confirmation modal action (run / cancel / parameter change) is logged. Author can review action history in settings → "Action history" — shows every action attempted, whether confirmed, what was run, and the resulting output.

---

## Output requested from UXPilot

1. Single-IID action confirmation modal (scope_check + Mae, with source-text preview)
2. Multi-IID parallel-run modal (Mae + OpenAI placeholder, source-text preview)
3. Floating action bar appearing above selected text
4. Right-click extended menu
5. Disabled-action error variants (out of quota, provider down, stub mode)
6. Action history log view (settings)
