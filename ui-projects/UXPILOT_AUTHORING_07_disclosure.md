# UXPilot Prompt — eaiou IID Disclosure UI (SAID Framework Compliance)

**Title:** eaiou Disclosure UI — SAID-Framework Renderings

---

## Frame

Every IID interaction in eaiou produces and displays a **disclosure block** — a structured record of which IID participated, what model family, what session instance, when, on what content, with what cost. This is doctrine per the SAID framework (Stripped/Audited/Identified/Disclosed) and per `app/services/intellid.py`.

The disclosure block is **always visible**, **never collapsible**, and **always carries the IID's full attribution**. Authors should never wonder which IID produced what.

---

## Disclosure block schema

Every disclosure block contains:

| Field | Example | Purpose |
|---|---|---|
| `provider` | `"Mae"` | Human-readable provider name |
| `provider_org` | `"Anthropic"` | The organization behind the IID |
| `model_family` | `"claude-sonnet-4-6"` | Specific model identity |
| `model_version` | `"2026-04-15"` | Model snapshot if known |
| `instance_hash` | `"abc12345"` | Sealed session fingerprint (8-char prefix; full on click) |
| `intellid_id` | `"iid_xxxxxxxxxxxxxxxx"` | eaiou's IntelliId record |
| `cosmoid` | `"cosmoid_xxxxxxxxx"` | eaiou's CosmoID for the manuscript context |
| `action_sku` | `"scope_check"` | Which SKU was invoked |
| `latency_ms` | `8420` | How long the call took |
| `cost_cents` | `7` | What was billed |
| `billing_path` | `"subscription_credit"` or `"stripe_meter"` or `"partner_key"` | How it was paid |
| `produced_at` | `"2026-05-01T19:32:14Z"` | RFC 3339 timestamp |
| `served_by_host` | `"edm-prod-01"` | Which eaiou instance proxied the call |
| `stub` | `false` | True if running in stub mode (Phase 0) |
| `partner_key_id` | `null` | If the call came through a partner-key (B2B), that key's id |
| `redacted` | `false` | True if compliance withdrawn the source post-hoc |

---

## Disclosure block visual rendering

### Compact (on every output card header)

```
[Mae chip] Mae · claude-sonnet-4-6 · inst abc12345 · 2 min ago · $0.07
```

Single line, color-coded by provider chip, expands on click.

### Expanded (when author clicks the chip or "View full disclosure")

```
┌────────────────────────────────────────────────────────┐
│  Disclosure                                    [×]      │
│  ──────────────────────────────────────────────────    │
│                                                          │
│  Provider:        Mae (Anthropic)                       │
│  Model:           claude-sonnet-4-6 (2026-04-15)        │
│  Instance hash:   abc12345-7a9b-4f2e-c8d1-1d34ef5a (full)│
│  IntelliD:        iid_72jHLpW9K...                      │
│  CosmoID:         cosmoid_x...   [the manuscript record]│
│  ──────────────────────────────────────────────────    │
│  Action:          scope_check                            │
│  Latency:         8.42s                                  │
│  Cost:            $0.07 (Pro subscription credit)        │
│  Path:            subscription_credit                    │
│  ──────────────────────────────────────────────────    │
│  Produced:        2026-05-01 19:32:14 PDT                │
│  Served by:       edm-prod-01                            │
│  Stub mode:       no                                     │
│  Partner key:     none (direct user call)                │
│  Redacted:        no                                     │
│  ──────────────────────────────────────────────────    │
│  [View raw IntelliId record (admin)] [Copy disclosure JSON] │
└────────────────────────────────────────────────────────┘
```

### Disclosure-on-comment (when an IID output is inserted as a margin comment)

The comment header shows the compact disclosure, and the full disclosure is reachable via a "View provenance" link in the comment footer:

```
┌──────────────────────────────────────────────────┐
│ [Mae chip] Mae · scope_check · 2 min ago         │
│ ──────────────────────────────────────────────   │
│ in_scope: true (confidence 0.84)                 │
│ The abstract aligns with the venue's...          │
│ ──────────────────────────────────────────────   │
│ [Reply] [Resolve] [View provenance]              │
└──────────────────────────────────────────────────┘
```

---

## Where disclosure appears

1. **Every output card** in the Output Panel — header strip + expanded on click
2. **Every margin comment** that was inserted from an IID output
3. **Every export** (audit-log JSON / CSV) — full disclosure record per output
4. **Every API response** for partner-key callers — full disclosure in the response JSON
5. **Manuscript-level summary** (top bar IID Activity drawer) — list of all IIDs that contributed to this manuscript with counts
6. **Author's session view** (settings → "This session's IID activity") — chronological log

---

## Manuscript-level disclosure roster

Top of the manuscript editor, accessed via the IID Activity chip in the title bar:

```
┌──────────────────────────────────────────────────────┐
│  IIDs Active on This Manuscript                       │
│  ────────────────────────────────────────────────    │
│                                                        │
│  [Mae chip] Mae (Anthropic)            12 outputs     │
│   claude-sonnet-4-6, instance abc12345                │
│   $0.84 spent, scope_check x4, clarity_check x6,     │
│   methods_check x2                                    │
│                                                        │
│  [OpenAI chip] OpenAI                  0 outputs     │
│   not yet wired (placeholder)                         │
│                                                        │
│  ────────────────────────────────────────────────    │
│  Total: 12 outputs from 1 IID, $0.84                  │
│  [Export full audit log]                              │
└──────────────────────────────────────────────────────┘
```

---

## Author-visible privacy controls

Per the SAID framework, sealed instance_hash means the raw session/API key isn't exposed in the disclosure. But authors can:

- See the full instance_hash if they expand
- See which CosmoID their IID activity is tied to
- See exactly what source text the IID received (in each output card's source-text block)
- Export a complete audit log for their own records or for journal-submission disclosure
- Mark specific outputs as "do not include in audit-log export" (compliance carve-out for confidential manuscripts; output is preserved internally but excluded from exports)

---

## Disclosure on author-publication output

When the author submits the manuscript to a journal, eaiou auto-generates an **AI-use disclosure paragraph** for inclusion in cover letter or supplementary material:

```
AI participation disclosure (per SAID framework):
This manuscript was prepared with assistance from the following 
Intelligence-IDs (IIDs):

• Mae (Anthropic, claude-sonnet-4-6, instance abc12345-7a9b-...)
  — performed: scope_check (4 invocations), clarity_check (6),
    methods_check (2). All outputs are advisory; the author
    retained final discretion over manuscript content.

A complete audit log of IID interactions is available at:
https://eaiou.org/manuscripts/[id]/audit-log

This disclosure was auto-generated by eaiou per SAID framework
discipline. No IID-produced text was inserted into the manuscript
without author review and explicit acceptance.
```

The author can edit this paragraph before exporting. The full audit log is available via stable URL for reviewers / editors who want to verify.

---

## What disclosure is NOT

- Not a checkbox the author can untick
- Not a banner that can be dismissed
- Not collapsed or hidden by default
- Not summarized into a generic "AI was used" — every IID is named with its full disclosure
- Not chained or blended — each IID's disclosure stands alone, never merged with another IID's

---

## Output requested from UXPilot

1. Compact disclosure as it appears in an output card header
2. Expanded disclosure modal with all 14 fields
3. Margin-comment with disclosure header
4. Manuscript-level IID Activity drawer
5. Auto-generated AI-use-disclosure paragraph preview
6. Author-controls for privacy (export, mark-as-do-not-export)
