# Claude Web Build Prompt — checksubmit GPT (OpenAI ChatGPT App)

**For Eric to paste into Claude Web (or GPT-5) to commission the OpenAI App
build.** Companion to `CLAUDE_WEB_BUILD_PROMPT.md` (which builds the MCP +
Claude Skill). Both can be run in parallel against fresh Claude Web sessions.

**Date drafted:** 2026-05-01
**Author:** Eric D. Martin + Mae (Claude, Anthropic)

---

## How to use this prompt

1. Open Claude Web in a fresh conversation.
2. Paste everything below the `=== PROMPT BEGINS ===` line through the
   `=== PROMPT ENDS ===` line.
3. The model will produce: the OpenAPI 3.1.0 schema, GPT system prompt, GPT
   instructions, privacy policy template, and the GPT-Builder configuration
   walkthrough.
4. Eric uses these as the inputs to the GPT-Builder UI at `chat.openai.com/gpts/new`.
5. Bring the output back to Mae for review.

---

```
=== PROMPT BEGINS ===

You are creating a custom GPT for ChatGPT's GPT Store that exposes a
peer-review-as-a-service API called checksubmit. The GPT itself does not
contain review logic; it is a thin shell that calls checksubmit's HTTP API
via the GPT-Builder's "Actions" mechanism (which uses an OpenAPI 3.1.0
schema to define HTTP tools).

Your output is a complete bundle of artifacts ready to paste into the
GPT-Builder UI at https://chat.openai.com/gpts/new.

## What checksubmit is

checksubmit is a peer-review pre-submission service. Authors submit manuscript
text and receive structured reviews — scope alignment, journal selection,
methods adequacy, citation audit. The reviews are produced by IID
(intelligence-ID) calls to providers like Anthropic and OpenAI, with
mandatory disclosure of provider/model on every output.

Production base URL: `https://checksubmit.org/api/v1`

The OpenAPI schema is available at `https://checksubmit.org/openapi.json`.

## What you are building

### 1. OpenAPI 3.1.0 schema for GPT Actions

A self-contained `openapi.yaml` that defines:
- `POST /api/v1/orders` — place a peer-review order
- `GET /api/v1/orders/{order_id}` — fetch an order's result
- `GET /api/v1/products` — list available SKUs

The schema must include:
- `servers` block with `https://checksubmit.org` as the production URL
- `components.securitySchemes.PartnerKeyAuth` defining `apiKey` in `header`
  named `X-Partner-Key`
- Operation IDs that are valid identifiers and human-readable
- Request/response schemas for each endpoint
- The `Idempotency-Key` request header (string, UUID format) on POST /orders

The eight SKUs (these are the supported `sku` enum values):

| SKU | Display name | Latency | Retail | Wholesale |
|---|---|---|---|---|
| `scope_check`     | Scope check                   | ~30s | $10  | $7  |
| `journal_select`  | Journal selection             | ~30s | $10  | $7  |
| `outline_check`   | Outline review                | ~30s | $10  | $7  |
| `clarity_check`   | Clarity review                | ~30s | $10  | $7  |
| `methods_check`   | Methods adequacy              | ~45s | $15  | $10 |
| `reference_audit` | Reference audit               | ~60s | $10  | $7  |
| `full_review`     | Full pre-submission review    | ~90s | $100 | $70 |
| `premium_review`  | Premium review (human-in-loop) | 24h SLA | $1500 | $1000 |

### 2. GPT system prompt (the GPT's "Instructions" field)

A 600–1000 word system prompt that:
- Names the GPT ("checksubmit Peer Review")
- Tells the GPT to invoke the OpenAPI actions when the user requests
  review of any manuscript text
- Forces the GPT to ALWAYS surface the IID disclosure block in its
  reply (`result.iid` field from the API response)
- Forces the GPT to surface the `result.stub` flag faithfully when present
- Forbids the GPT from inventing review content
- Forbids the GPT from chaining tools (one call per user request)
- Tells the GPT to ask for the manuscript text, optional target venue, and
  any other tool-specific inputs before invoking
- Describes pricing transparently — the GPT shows the SKU price before
  invoking, asks for confirmation
- Includes a short FAQ on what each SKU does and when to use which

### 3. GPT description + greeting message + conversation starters

For the GPT-Builder's basic config:
- **Name**: "checksubmit Peer Review" (or similar, suggest 2 alternatives)
- **Description** (≤300 chars): Crisp pitch for the GPT Store listing
- **Conversation starters** (4 examples): Common author requests
  - e.g. "Review my abstract for scope alignment with MNRAS"
  - e.g. "Suggest journals for this draft"
  - e.g. "Audit my methods section for reproducibility"
  - e.g. "Run a full pre-submission review"

### 4. Privacy policy template

A short, honest privacy policy in markdown:
- What checksubmit collects (manuscript text the user submits;
  authentication via partner key)
- What checksubmit does with it (review-tool processing only; no model
  training; audit log retains hash + metadata, not raw text after 90 days)
- IID disclosure: every output records the provider used
- User rights: data export, deletion request via `support@checksubmit.org`
- Subject to checksubmit.org's master Terms of Service

The privacy policy will live at `https://checksubmit.org/privacy` —
the GPT-Builder requires a privacy policy URL.

### 5. Authentication setup walkthrough

Markdown documentation for Eric on how to configure the GPT's API auth in
GPT-Builder UI:
- In Actions → Authentication → API Key (Custom Header)
- Header name: `X-Partner-Key`
- Auth type: Custom
- The user (Eric) supplies a partner key; checksubmit issues these
- Format: `eaiou_pk_<opaque-string>`

## Hard constraints

1. **OpenAPI 3.1.0 only** (not 3.0; GPT Actions accepts 3.1.0).

2. **Server URL**: exactly `https://checksubmit.org`. No trailing slash.
   No environment variable substitution (GPT-Builder doesn't support that).

3. **OperationIds must be unique and ≤64 chars.** Suggest:
   `placeReviewOrder`, `getReviewOrder`, `listProducts`.

4. **Schema completeness.** Every parameter, request body field, and
   response field must have a `description`. The GPT relies on these to
   pick the right tool and fill the right inputs.

5. **No invented endpoints.** Use only `POST /orders`, `GET /orders/{id}`,
   `GET /products`. Do not add cancel, refund, list-orders, or any
   convenience endpoints.

6. **No batch operations.** Each tool call is a single order. The user can
   issue multiple in sequence; the GPT must NOT propose a batch.

7. **The GPT's system prompt forbids chaining.** If the user asks for
   "scope + clarity + methods", the GPT issues three separate API calls
   sequentially; it must NOT call `full_review` as a substitute (that
   composition is a different priced product).

8. **The GPT's system prompt enforces disclosure.** Every assistant reply
   that includes review content must also include a labeled disclosure
   block at the bottom. Format:

   ```
   ──── IID DISCLOSURE ────
   Provider: <result.iid.provider>
   Model: <result.iid.model_family>
   Instance: <result.iid.instance_hash>
   Action: <sku>
   Order: <order_id>
   Timestamp: <completed_at>
   ────────────────────────
   ```

9. **Stub handling.** When `result.stub === true`, prefix the GPT's reply
   with a clearly marked `⚠ STUB RESULT — real handler ships in Phase 1`.
   Do NOT pretend the stub is a real review.

10. **Pricing transparency.** Before invoking any paid SKU, the GPT must
    confirm with the user: "This will charge $X via your subscription tier
    or partner key. Proceed?" — then wait for explicit confirmation.

11. **No CORS or browser concerns** — GPT Actions execute server-side from
    OpenAI's infrastructure; you don't need to think about browser
    constraints. Just produce the OpenAPI schema correctly.

## Output format

Produce the following artifacts in order, each as a complete, paste-ready
block:

### A. `openapi.yaml`

The full OpenAPI 3.1.0 schema. Begin with the `openapi: 3.1.0` line.

### B. `gpt_instructions.md`

The full GPT system prompt. This goes in the GPT-Builder's "Instructions"
field. Plain markdown, ≤8000 chars (GPT-Builder limit).

### C. `gpt_metadata.md`

The GPT's name, description, conversation starters, and category
recommendation (suggest a category from GPT Store's allowed list:
Productivity / Research & Analysis / Writing).

### D. `privacy_policy.md`

The privacy policy in markdown. Will be hosted at
`https://checksubmit.org/privacy`.

### E. `setup_walkthrough.md`

Step-by-step instructions for Eric to:
1. Visit https://chat.openai.com/gpts/new
2. Configure the basic info (name, description, etc. from gpt_metadata.md)
3. Paste the system prompt from gpt_instructions.md into Instructions
4. Add an Action via "Create new action"
5. Paste openapi.yaml into the schema field
6. Configure auth (Custom Header: X-Partner-Key)
7. Set the privacy policy URL
8. Test conversation
9. Publish (private link first, then public when ready)

## What you should NOT do

- Do NOT add features beyond what's listed.
- Do NOT invent SKUs.
- Do NOT add OAuth (partner key is sufficient for B2B; OAuth user-flow is
  for Phase 2+).
- Do NOT swallow the disclosure block.
- Do NOT invent historical/legal language in the privacy policy. Stay
  honest and minimal.
- Do NOT recommend a "trial mode" or "free tier inside the GPT" — pricing
  is upstream of the GPT.
- Do NOT use anything other than markdown for the human-readable artifacts.

When you produce the output, include the COMPLETE artifacts. Eric will
paste each into the appropriate GPT-Builder field directly.

=== PROMPT ENDS ===
```

---

## Notes for Eric (Mae's commentary)

### Two prompts, two surfaces

You now have:
- `CLAUDE_WEB_BUILD_PROMPT.md` — produces MCP server + Claude Skill (Anthropic ecosystem)
- `CLAUDE_WEB_BUILD_PROMPT_GPT_APP.md` — produces OpenAPI + GPT system prompt + GPT-Builder walkthrough (OpenAI ecosystem)

Run them in parallel against two fresh Claude Web sessions. Both are
~10 minutes of model time; both produce drop-in artifacts.

### Why two prompts instead of one combined prompt

- Each ecosystem has different file formats, different auth patterns,
  different SDK choices. Combined prompts produce mush.
- You can iterate on each surface independently — if the MCP version
  needs a tweak, you don't re-run the GPT version.
- Each is small enough to fit comfortably in a single Claude Web context.

### What's NOT in either prompt (by design)

- **Cursor / Continue / Cline** — they all read MCP servers, so the
  Anthropic prompt's MCP server works for them too. No additional work.
- **Slack / Discord / Telegram bots** — possible Phase 0.5c, not now.
- **Mobile app** — no.
- **Chrome extension** — possible Phase 0.5d, not now.

### The cash-flow gate (re. "we could blow up so fast")

Both prompts produce production-shaped artifacts. The constraint that
matters is NOT engineering — it's that distribution doesn't outrun the
Anthropic-spend-vs-Stripe-receipt float. Solution paths:

1. **Pre-paid-only mode for Phase 0.5 launch** — partner key has a
   pre-loaded credit balance; calls deduct from balance; if balance hits
   zero, calls 402-Payment-Required. No float exposure.
2. **Stripe Treasury** — same-day payouts to a checking account so the
   lag is hours not days.
3. **Conservative rate limiting per partner key** — `rate_limit_per_minute`
   on `eaiou_partner_keys` (we already have the column) — set to 60/minute
   per partner during the first 30 days, then loosen as float metrics
   stabilize.

When you bring back the Claude Web outputs, Mae will integrate them and
also wire option 1 (pre-paid-only mode) into the marketplace router as
a feature flag.
