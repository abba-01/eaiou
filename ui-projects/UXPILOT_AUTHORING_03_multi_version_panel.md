# UXPilot Prompt — eaiou IID Output Panel + Multi-Version Display

**Title:** eaiou Output Panel — Parallel IID Outputs, No Blending

---

## Frame

This is the **right-side output panel** that opens when an IID returns a result. It's a drawer-style overlay (default closed; auto-opens on first output of a session; can be pinned open).

The panel's job is to **display IID outputs without blending them**, support side-by-side comparison when multiple IIDs run on the same task, and preserve the full audit trail of what was run, by which provider, on what source text, and when.

---

## Layout

```
┌──────────────────────────────────────────────────────────┐
│  IID Outputs                          [filter] [close]    │
│  ────────────────────────────────────────────────────────  │
│                                                            │
│  Filter: [All providers ▾] [All actions ▾] [Section ▾]    │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ [Mae chip] scope_check on §Abstract        2 min ago│   │
│  │  ──────────────────────────────────────────────────  │   │
│  │  Source: "We propose a multidimensional intake..."   │   │
│  │  Result:                                              │   │
│  │    in_scope: true (confidence 0.84)                   │   │
│  │    Reasoning: The abstract aligns with the venue's   │   │
│  │    forensic-clinical scope...                         │   │
│  │    Similar papers: [10.xxx/yyy] [10.zzz/abc]         │   │
│  │  Disclosure: claude-sonnet-4-6 / inst abc1234         │   │
│  │  Cost: $0.07 (paid via Pro subscription credit)       │   │
│  │  [Copy] [Insert as comment] [Hide] [Re-run] [+IID]    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ [Mae chip] [OpenAI chip]  Side-by-side comparison    │   │
│  │  Action: clarity_check on §Methods paragraph 2       │   │
│  │  ┌───────────────────┬──────────────────────────┐    │   │
│  │  │  Mae output       │  OpenAI output           │    │   │
│  │  │  ...              │  ...                     │    │   │
│  │  │  IntelliD abc1234 │  IntelliD def5678        │    │   │
│  │  │  $0.07 / 8s       │  $0.05 / 6s              │    │   │
│  │  └───────────────────┴──────────────────────────┘    │   │
│  │  [Both ran on identical source text — no chaining]   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                            │
│  [Older outputs collapsed]                                 │
│                                                            │
│  ────────────────────────────────────────────────────────  │
│  Session totals: 4 outputs, 2 IIDs, $0.28 spent            │
│  [Export audit log] [Filter by session]                    │
└──────────────────────────────────────────────────────────┘
```

---

## Output card structure (single-IID)

Each card is a self-contained record of one IID-action invocation:

1. **Header strip:**
   - Provider chip (color-coded)
   - Action verb (e.g., "scope_check on §Abstract")
   - Relative timestamp ("2 min ago"; absolute on hover)

2. **Source-text block** (collapsible):
   - The exact source text the IID was given
   - Section reference (which section of the manuscript)
   - Word count

3. **Result body:**
   - Structured if the handler returned structure (in_scope: true, confidence: 0.84, reasoning, similar_papers list)
   - Free text if the handler returned prose
   - Markdown rendering supported (some handlers may return formatted output)

4. **Disclosure block** (always visible; never collapsible):
   - Provider, model_family, instance_hash (sealed; 8-char prefix; full on click)
   - Action SKU
   - Stub indicator if applicable
   - Production timestamp
   - Server fingerprint (host that ran the call)

5. **Cost record:**
   - Amount in $
   - Billing path (subscription credit / Stripe meter event / partner key)
   - Wholesale rate if partner-keyed

6. **Action buttons:**
   - **Copy** — copies the result body to clipboard
   - **Insert as comment** — adds the output as a margin comment on the relevant manuscript section
   - **Hide** — collapses the card (NOT delete; outputs are immutable for audit)
   - **Re-run with same IID** — fires the same SKU on the same source text again (idempotent; new output card produced)
   - **+IID** — opens the multi-IID-parallel-run modal to run the same prompt with another IID

---

## Multi-IID parallel-run card

When the author runs the same SKU + source-text across 2+ IIDs, results land as a **side-by-side comparison card** with:

- Header showing all IID chips + the shared action verb
- Each IID's output as a column (2-up at desktop; 3-up if 3 IIDs; vertical stack on narrow viewports)
- Each column has its own disclosure block, cost record, and action buttons
- Below all columns: **a banner: "Both ran on identical source text — no chaining occurred"** — explicit ToS-compliance breadcrumb

**Critical:** the comparison card does NOT auto-generate a "synthesis" or "consensus" output. If the author wants synthesis, they:
- Read the columns
- Decide what they think
- Write their own paragraph in the editor
- That paragraph is theirs, not an IID's

This preserves IID-isolation. The platform is provider-agnostic infrastructure; it does not blend.

---

## Filters

The panel has filter controls at the top:

- **By provider:** All / Mae / OpenAI / [each configured IID]
- **By action:** All / scope_check / journal_select / clarity_check / methods_check / reference_audit / outline_check / full_review
- **By section:** All / §Abstract / §Introduction / §Methods / etc. (manuscript-aware)
- **By time:** This session / Today / Last 7 days / All time
- **By cost:** Free (subscription credit) / Paid

Filters compose. Clicking provider chips at the top of an output card auto-applies that filter.

---

## Output ordering

- Default: most-recent first (timestamp-descending)
- Author can toggle: most-recent / oldest-first / by-section (groups outputs under their section anchors)
- Within a manuscript, all outputs across all sessions are accessible (paginated)

---

## Hide vs delete

- Outputs are **immutable** — they cannot be deleted by the author (audit-trail discipline)
- Hide collapses the card; the card is still in the audit log and exportable
- "Show hidden" toggle restores them visually
- Admin-level ops can mark an output as "withdrawn" for compliance reasons (e.g., the source text was redacted post-hoc); withdrawn outputs show a redacted-source notice but the IID's response is preserved

---

## Insert-as-comment

When the author clicks "Insert as comment" on an output:
- A margin-comment is added to the manuscript at the section/paragraph the IID's output relates to
- The comment is **labeled with the full IID disclosure** ("Mae (claude-sonnet-4-6, inst abc1234), scope_check, [date]")
- The comment body is the IID's result — verbatim
- Author can reply to the comment, mark it as resolved, or delete the comment (the original output card persists in the panel even if the comment is deleted)

This makes the IID's contribution visible inline AND attributable AND removable — no silent integration.

---

## Audit-log export

Bottom of panel: **[Export audit log]**

Generates a JSON or CSV file with every IID interaction in the manuscript's history:
- Every output card
- Source text given
- Result returned
- Disclosure metadata
- Cost
- Author actions on the output (insert / hide / re-run)
- Timestamps

Used for: forensic / academic-integrity audits, replication, partner-key billing reconciliation, SAID-framework reporting.

---

## Output-panel state machine

| State | Visual |
|---|---|
| Empty (no outputs in session) | Friendly placeholder with onboarding text and a "Start by clicking 'Run scope_check' in the Mae sidebar" hint |
| Has outputs, idle | Output cards listed, filters available |
| New output landing | Brief slide-in animation; the card highlights for 2 seconds then settles |
| Loading more (paginated) | Spinner at bottom |
| Multi-IID parallel running | Comparison card placeholder shows progress per IID column |

---

## Output requested from UXPilot

1. Full output panel with 5-6 mixed cards (some single-IID, one multi-IID comparison)
2. Single-IID output card close-up showing all six zones
3. Multi-IID side-by-side comparison card close-up
4. Filter controls expanded
5. Empty state with onboarding text
6. Mobile / narrow-viewport layout (panel as full-screen overlay with back button)
7. Export audit-log modal preview
