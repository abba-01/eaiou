# UXPilot Prompt — eaiou IID Module Sidebar

**Title:** eaiou IID Module Sidebar — Multi-Provider Author Assistance Surface

---

## Frame

This is the **right-side rail** that sits next to the writing surface. Each card in the sidebar is **one IID provider's module**. Today only one card is fully wired (Mae / Anthropic). Future cards (OpenAI, Gemini, custom) will plug in via the same module pattern.

**Critical:** these are independent modules running side-by-side, never chained. The author chooses which to invoke. The sidebar surfaces the choice without making it.

---

## Card structure (per IID provider)

Each module card has six zones, top to bottom:

```
┌───────────────────────────────────────┐
│  [provider chip]  Mae                  │  ← provider chip (color-coded)
│  Anthropic claude-sonnet-4-6          │  ← model family (sub-line)
│  ────────────────────────────────────  │
│  Status: idle   |   12/50 calls used   │  ← state + quota
│  ────────────────────────────────────  │
│  ▼ Actions (clickable)                 │  ← action verbs
│    [Run scope_check]      $0.07       │
│    [Run journal_select]   $0.07       │
│    [Run clarity_check]    $0.07       │
│    [Run methods_check]    $0.14       │
│    [Run reference_audit]  $0.10       │
│    [Run outline_check]    $0.07       │
│    [Run full_review]      $0.70       │
│  ────────────────────────────────────  │
│  ▼ Disclosure                          │  ← SAID-framework block
│    instance_hash: abc1234              │
│    session opened: now                 │
│    [View full disclosure]              │
│  ────────────────────────────────────  │
│  [Settings]  [Disable]  [Help]         │  ← per-card controls
└───────────────────────────────────────┘
```

---

## Zones in detail

### Zone 1 — Provider chip + branding

- **Provider chip:** colored token (Mae = warm-gold, OpenAI = green, Gemini = blue, Llama = purple, custom = neutral-gray)
- **Provider name** in card-title typography
- **Model family** below in smaller text (claude-sonnet-4-6, gpt-4o, gemini-pro, etc.)
- Optional: tiny logo icon (Anthropic glyph for Mae, OpenAI glyph for GPT, etc.) — but secondary to the text label

### Zone 2 — Status + quota

- **Status:** idle / running / disabled / error / stub
- **Quota:** "12/50 calls used today" or "Unlimited (Pro tier)" or "Out of quota — upgrade"
- **Latency expectation:** small text "typical 5–15s" so author knows what to expect
- If error: error message + retry button inline

### Zone 3 — Actions (verb buttons)

- One button per action verb the IID supports
- Each button shows the **price** alongside the verb
- Buttons are full-width, stacked, easy to scan
- **Hover state:** shows expected output preview ("returns: in_scope boolean + reasoning paragraph + similar papers")
- **Click:** opens the action modal (see UXPILOT_AUTHORING_05_actions.md)
- **Disabled state:** buttons gray out when out of quota / provider down / no API key

### Zone 4 — Disclosure (SAID-framework block)

- **instance_hash:** the sealed session fingerprint (8-char prefix shown, full available on click)
- **Session opened:** when this IID's session for the current page started (helps audit reproducibility)
- **Active CosmoID:** if the manuscript has a CosmoID, the disclosure references it
- **[View full disclosure]:** opens a drawer with the full IntelliId record, all outputs from this IID this session, all costs

This block is **always visible**, never collapsible. It is doctrine, not UI noise.

### Zone 5 — Per-card controls

- **Settings:** opens per-IID config (which actions enabled, custom prompt prefixes if supported, rate-limit override, etc.)
- **Disable:** removes the card from the sidebar for this session (provider-isolation; author can drop any IID without affecting others)
- **Help:** opens documentation for what the IID is, what it costs, what its outputs look like

---

## Sidebar behavior

### Card ordering

- **Default order:** alphabetical by provider name (Mae, OpenAI, Gemini, ...)
- **Author can drag-reorder** to put preferred providers at top
- Future: usage-frequency-sorted option (most-used at top)

### Adding a new provider

- Below the last card, a "**+ Add IID Module**" button
- Click → modal listing supported providers + "Custom (advanced)"
- Each provider requires its own API key entered in eaiou's settings (provider-isolation: keys are NEVER shared across providers)
- Once added, the new card appears in the sidebar; previously-added providers persist across sessions

### Card collapse / expand

- Each card has a collapse caret in the top-right corner
- Collapsed cards show only the provider chip + status + quota
- Author can collapse cards they're not actively using; the sidebar stays manageable as more providers are added
- State is persisted per-author per-manuscript

### Sidebar collapse (whole rail)

- The entire IID sidebar can be collapsed to an **icon rail** (just provider chips, no content) via a toggle in the top bar
- Useful when the author wants maximum editor focus
- Outputs still arrive in the output panel; sidebar just goes quiet visually

---

## "Coming soon" placeholders

For providers not yet wired:

- Card renders in a **muted style** (grayed colors, no clickable buttons)
- Header shows the provider chip as normal
- Body says: **"OpenAI module — coming as a separate IID module. Plug-in pattern is open; eaiou welcomes external IID providers via the partner-API key system."**
- A "Notify me when ready" button to opt into rollout updates
- This visible-from-day-one pattern signals to authors AND to provider-relations that eaiou is provider-agnostic by architecture, not by retrofit

---

## ToS-compliance affordances (CRITICAL)

The sidebar must visibly demonstrate provider-isolation:

1. **Each card is its own bordered, color-coded surface.** No merged "AI helper" UI.
2. **No "Run all IIDs at once" button.** Multi-IID parallel runs require explicit per-IID selection.
3. **No "synthesize" button.** If the author wants synthesis across IIDs, they write it themselves in the editor.
4. **No automatic IID chaining anywhere.** The sidebar doesn't have a "send to next IID" affordance even within the same provider.
5. **Quota / billing per-provider.** Author always sees their per-IID usage; no shared usage pool that obscures which provider is consuming what.

---

## Empty state (no IIDs configured)

- The sidebar shows a single onboarding card:
  - "**Add an IID module to get started.** Mae (Anthropic) is recommended for first-time setup."
  - Big primary button: "Add Mae module"
  - Secondary text: "You can add OpenAI, Gemini, or custom providers later. Each runs independently and discloses itself per the SAID framework."

---

## Output requested from UXPilot

1. Full sidebar with one wired Mae card + one "coming soon" OpenAI card placeholder
2. The Mae card in expanded vs collapsed states
3. The Mae card in each lifecycle state (idle / running / complete / error / disabled / stub)
4. Add-IID-Module modal showing provider menu
5. Empty-state onboarding card
6. Sidebar collapsed to icon rail
7. Mobile / narrow-viewport layout (sidebar becomes a bottom drawer)
