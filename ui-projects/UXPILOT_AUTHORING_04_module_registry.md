# UXPilot Prompt — eaiou IID Module Registry + Onboarding

**Title:** eaiou IID Module Registry — How New Providers Plug In

---

## Frame

This is the **settings + onboarding surface** for adding/removing/configuring IID providers. Every IID is a registered module with its own credentials, quotas, and disclosure metadata. The registry is the structural surface that proves provider-isolation: each IID has its own row, its own settings, its own kill-switch.

---

## Two views

### View 1: Module Registry (settings → IID providers)

A list of all IID providers the author has configured:

```
┌──────────────────────────────────────────────────────────────┐
│  IID Module Registry            [+ Add IID]                  │
│  ──────────────────────────────────────────────────────────   │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐     │
│  │ [Mae chip] Mae (Anthropic)                  [Active] │     │
│  │ Model: claude-sonnet-4-6                              │     │
│  │ API key: ********xy7 (last 4)  [Rotate]               │     │
│  │ Quota: 50 calls/day, 12 used                          │     │
│  │ Enabled actions: 7/8  [Configure]                     │     │
│  │ Cost this month: $4.21                                 │     │
│  │ Disclosure: instance_hash sealed; full record visible │     │
│  │ [Edit] [Disable] [Remove]                              │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐     │
│  │ [OpenAI chip] OpenAI            [Coming as a module] │     │
│  │ Status: not configured (placeholder)                   │     │
│  │ Plug-in pattern is open. eaiou welcomes external IID   │     │
│  │ providers via the partner-API key system.              │     │
│  │ [Notify when ready]                                    │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐     │
│  │ [Custom chip] Custom IID Provider                      │     │
│  │ For advanced users: register a custom IID via API     │     │
│  │ [Documentation] [Add custom]                           │     │
│  └──────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

### View 2: Add-IID modal

When the user clicks "+ Add IID":

```
┌──────────────────────────────────────────────────┐
│  Add IID Module                          [×]      │
│  ──────────────────────────────────────────────   │
│                                                    │
│  Choose a provider:                                │
│                                                    │
│  ○ Mae (Anthropic)        — recommended            │
│  ○ OpenAI                 — coming soon            │
│  ○ Gemini (Google)        — coming soon            │
│  ○ Llama (Meta, hosted)   — coming soon            │
│  ○ Custom (advanced)      — via partner-key API    │
│                                                    │
│  ────────────────────────────────────────────      │
│  API key for [provider]: [________________]        │
│  ────────────────────────────────────────────      │
│  Daily call quota: [50] (default)                  │
│  Monthly $ cap:    [$50] (default)                 │
│  ────────────────────────────────────────────      │
│  Enabled actions: ☑ scope_check                    │
│                   ☑ journal_select                 │
│                   ☑ clarity_check                  │
│                   ... (all 8 by default)           │
│  ────────────────────────────────────────────      │
│  Disclosure preview:                               │
│   "Mae (claude-sonnet-4-6, instance [generated     │
│   on first call])"                                 │
│                                                    │
│  [Cancel]                            [Add module]  │
└──────────────────────────────────────────────────┘
```

---

## Per-module configuration (Configure button)

Opens a panel with:

- **Enabled actions** — checkboxes per SKU; disabled actions don't show their button on the sidebar card
- **Custom prompt prefix** (advanced; requires user to confirm awareness of ToS implications) — prepends a string to every action prompt for this IID; off by default
- **Rate limit override** — author can lower their own rate limit (cost protection); cannot raise above provider's hard limit
- **Cost cap** — monthly and per-call ceilings; calls beyond cap are blocked with a clear error
- **Latency timeout** — how long to wait before declaring the call failed (default 30s for micro-products, 5min for full_review)
- **Logging** — opt-in to enhanced logging of full prompt + response (off by default for privacy; on for users who want full audit)

---

## Per-module disable / remove

- **Disable:** module stays in the registry but is hidden from the sidebar; quotas reset on re-enable; disclosure history preserved
- **Remove:** module deleted from the registry; API key is cleared from eaiou's storage; disclosure history preserved (immutable audit)

Both actions require confirmation — neither is reversible without re-entering the API key.

---

## Custom IID provider (advanced)

For users who want to point at a self-hosted or third-party IID:

- Provider URL (must be HTTPS)
- Auth method (Bearer token / HMAC / mTLS)
- Action SKU mapping (which of eaiou's SKUs this provider supports)
- Request schema (eaiou wraps user-provided JSON Schema; eaiou validates incoming responses)
- Disclosure schema (the custom provider must return a disclosure block with at least: provider_name, model_family, instance_hash; eaiou rejects responses lacking it)

Documentation links to the partner-API contract Eric is shipping with the checksubmit MVP — same auth pattern, same SAID-framework discipline.

---

## SAID-framework integration

Every module config writes its disclosure metadata into the eaiou IntelliId table on first call. The IntelliId table is the canonical record of "which IID is currently active for this manuscript / session / author."

Every action invocation:
1. Looks up the active IntelliId for the (author, manuscript, IID-provider) tuple
2. If no IntelliId exists, creates one (with sealed instance_hash)
3. Records the call against the IntelliId
4. Updates the disclosure block visible in the sidebar + outputs

This ties the registry to the live disclosure UI — they're the same data, presented at different levels of detail.

---

## Output requested from UXPilot

1. Module registry main view with one wired Mae card + OpenAI placeholder + Custom-provider invitation
2. Add-IID modal expanded
3. Per-module configuration panel (Configure button)
4. Disable confirmation dialog
5. Remove confirmation dialog (more emphatic)
6. Custom IID provider setup form (advanced)
