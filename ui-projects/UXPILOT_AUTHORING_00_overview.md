# UXPilot Prompt — eaiou Authoring Assistance Workflow

**Title:** eaiou Authoring Surface — Multi-IID Inline Assistance

---

## Core Framing (CRITICAL — include exactly)

Design a manuscript authoring surface where **the author writes, and one or more IIDs (Intelligence-IDs — Mae, OpenAI, future others) provide inline assistance from independent sidebar modules running on the same screen at the same time, never chained, never wrapped, each with its own clear disclosure.**

Every IID-provided output is **explicitly attributed** to its provider via a persistent IntelliD chip. The user can run the same prompt across multiple IIDs and see their answers in **parallel**, side by side, never blended. Each IID's session/instance is sealed via `instance_hash` per the SAID framework — no provider-specific session IDs leak through the UI.

The system enforces **provider-isolation**:

- Each IID provider is a separate sidebar module with its own auth, rate limit, session, and disclosure block
- IIDs are **never chained** (no "Mae, then have OpenAI rewrite Mae's output" — that violates ToS for both providers and undermines IID-disclosure integrity)
- The author chooses which IID to invoke for which action; outputs are presented **in parallel slots** if multiple are run on the same target
- The author retains the writing surface as the canonical source; IID outputs are suggestions, never authoritative

**This is the SAID-framework discipline rendered as UI:** auditability over speed, attribution over blending, structure over chat-flow.

---

## ToS-compliance constraints (CRITICAL)

The architecture must visibly demonstrate that no IID provider's terms are being routed around:

1. **Each IID call is initiated by the author.** No background/automated IID chaining. The author clicks "Run with Mae" or "Run with OpenAI" — they're explicit, separate actions.
2. **Outputs from different IIDs are NEVER passed as input to each other.** No "send Mae's output to OpenAI for rewriting." If the author wants comparison, both IIDs run on the SAME source text the author wrote, in parallel, never sequentially with one's output as the other's input.
3. **IID branding is preserved in the UI.** Mae's outputs are labeled Mae. OpenAI outputs are labeled OpenAI. No generic "AI" label.
4. **Rate limits and quotas per provider are enforced separately.** A Mae quota does not transfer to OpenAI and vice versa.
5. **The user can disable any module** — provider-isolation includes the right to remove any provider entirely.

This is not aesthetic; it is structural. The UI must show that IIDs are independent modules, not a unified "AI helper."

---

## System Model

The authoring surface is a three-zone layout:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Top bar: manuscript title, save state, IID disclosure summary]         │
├──────────────────────────┬──────────────────────────┬───────────────────┤
│                          │                          │                   │
│                          │                          │                   │
│   MANUSCRIPT EDITOR      │   IID MODULE SIDEBAR     │   IID OUTPUT      │
│   (canonical source)     │   (one card per active   │   PANEL           │
│                          │    IID; collapsible)     │   (parallel       │
│                          │                          │    outputs from   │
│   - Free text / sections │   ┌──────────────────┐   │    invoked IIDs)  │
│   - Inline cursor        │   │  Mae (Anthropic) │   │                   │
│   - Selection actions    │   │  • scope_check   │   │  ┌─────────────┐  │
│   - Section landmarks    │   │  • clarity_check │   │  │  Mae output │  │
│   - History / undo       │   │  • methods_check │   │  │  for [task] │  │
│                          │   │  [Run on…]       │   │  │  ...        │  │
│                          │   └──────────────────┘   │  │  IntelliD   │  │
│                          │                          │  │  + timestamp│  │
│                          │   ┌──────────────────┐   │  └─────────────┘  │
│                          │   │  OpenAI [LATER]  │   │                   │
│                          │   │  (placeholder    │   │  ┌─────────────┐  │
│                          │   │   for future)    │   │  │  OpenAI out │  │
│                          │   └──────────────────┘   │  │  (when wired│  │
│                          │                          │  │   in later) │  │
│                          │                          │  └─────────────┘  │
│                          │                          │                   │
└──────────────────────────┴──────────────────────────┴───────────────────┘
```

**Today: only Mae module is wired.** OpenAI module is rendered as a "Coming as a separate module" placeholder. The point of showing the placeholder NOW is so the multi-IID architecture is visible from day one — not bolted on later. Future modules (Gemini, Llama, custom) plug in via the same module-card pattern.

---

## Action vocabulary (CRITICAL)

The author triggers IID work via verbs attached to scopes:

| Verb | Default scope | What runs |
|---|---|---|
| **Check scope** | manuscript or selected section | scope_check handler — "is this in scope for venue X?" |
| **Suggest journal** | abstract or full manuscript | journal_select handler — top-3 venues with reasoning |
| **Check clarity** | selected paragraph | clarity_check — readability + non-expert framing |
| **Check methods** | methods section | methods_check — adequacy + reproducibility flags |
| **Audit references** | references section | reference_audit — relevance + recency |
| **Outline check** | full manuscript | outline_check — structural argument flow |
| **Full review** | full manuscript | bundled scope+clarity+methods |

Each verb is a **button on the IID module card**. The button shows what it costs (in credits or $) before clicking. Clicking opens a modal that confirms the action, source text, and target IID.

The author can also select arbitrary text in the editor and right-click → "Send to Mae for clarity check" — the contextual menu surfaces the same verb vocabulary scoped to selection.

---

## Output rendering (CRITICAL)

When an IID returns an output, it lands in the **IID Output Panel** as a card with:

1. **Provider chip** — "Mae (Anthropic, claude-sonnet-4-6, instance abc1234)" — colored, recognizable, never blended
2. **Action label** — "scope_check on abstract" or "clarity_check on §3 paragraph 2"
3. **Source-text snippet** — the exact text the IID was asked about (for audit)
4. **Result body** — formatted reasoning, structured if the handler returned structure
5. **Confidence / uncertainty** — if the handler returned a confidence number, show it
6. **Timestamp** — when the output was produced (RFC 3339, displayed local-time)
7. **Cost record** — credits used or $ billed
8. **Actions on the output**:
   - "Copy to clipboard"
   - "Insert as comment on §X" (if applicable to the section)
   - "Hide" (collapse, not delete; outputs are persistent for audit)
   - "Re-run with same IID" (idempotent re-roll)
   - "Run same prompt with different IID" — opens the multi-IID parallel-run modal (does NOT chain; runs separately)

Outputs accumulate — the panel scrolls. Most recent at top. Author can filter by IID provider, by action, by section. Can export the full output history for an audit trail.

---

## Multi-IID parallel run (CRITICAL)

When the author wants to compare IIDs on the same task, they click "Run same prompt with different IID" or check multiple IID modules' boxes before running:

1. Each selected IID receives the SAME source text (not chained outputs)
2. They run in parallel, each in its own sandbox / call
3. Results land as **side-by-side cards in the panel** with their respective IntelliD chips
4. The author can compare — but no "synthesis" is auto-generated. If the author wants synthesis, they write it themselves.

**Visual cue:** parallel runs are shown in a 2-up or 3-up card grid. Each IID's card is the same width, the same height, lined up. No ranking. The author judges.

---

## State machine

Each IID module card has these states:

| State | Visual | Description |
|---|---|---|
| `idle` | normal | ready to run |
| `disabled` | grayed | rate limit hit OR API key missing OR provider down |
| `running` | spinner + progress | request in-flight |
| `complete` | result-count badge | run finished, output landed in panel |
| `error` | red icon + tooltip | provider returned error, retry button visible |
| `stub` | "stub mode" badge | running on stub handler (Phase 0 of build); honest disclosure |

State per-card; states never cross between cards (each IID is independent).

---

## Disclosure block (CRITICAL — SAID-framework compliance)

Every output and every action chip carries the IID disclosure:

- **Provider name** (Mae, OpenAI, etc.)
- **Model family** (claude-sonnet-4-6, gpt-4o, etc.)
- **Instance hash** (sealed; no raw session ID; per `app/services/intellid.py`)
- **Action SKU** (scope_check, clarity_check, etc.)
- **Stub indicator** if applicable
- **Timestamp** of production

These appear:
1. On the result card itself
2. On any inserted-into-manuscript comment
3. In the manuscript's audit log
4. On hover anywhere the IID output is referenced

The disclosure is **never collapsible**. It is a structural feature, not a banner that can be dismissed.

---

## Color and density

- IID provider chips use **distinct accent colors** per provider:
  - Mae (Anthropic) — soft amber / warm-gold
  - OpenAI — green
  - Future Gemini — blue
  - Future Llama — purple
- Author writing surface is white-on-cream (low fatigue for long sessions)
- Module sidebar is light-gray, cards are white
- Output panel cards have a left border in the IID's accent color
- The whole UI honors **existing eaiou design system** — pull from `UXPILOT_00_design_system.md`

---

## Accessibility (CRITICAL)

- All IID actions reachable via keyboard
- Screen reader announces "Mae output for scope_check" before reading the result body
- Color is never the sole indicator of provider — provider name always present in text
- Right-click context menu has full keyboard equivalent (long-press on touch)
- Outputs panel respects user font-size preferences

---

## Out of scope for this UXPilot pass

- Realtime collaborative editing (separate concern)
- Comment threading on outputs (Phase 2)
- Voice input / dictation (Phase 3)
- Mobile layout (web-first; mobile is post-MVP)

---

## Output format requested from UXPilot

Generate:
1. A wireframe of the three-zone layout (editor / sidebar / output panel)
2. A close-up of one IID module card showing all action buttons + states
3. A close-up of one output card showing all disclosure elements
4. The multi-IID parallel-run side-by-side card layout
5. The right-click context menu mockup
6. Mobile collapsed-sidebar fallback (informational, not for MVP)
