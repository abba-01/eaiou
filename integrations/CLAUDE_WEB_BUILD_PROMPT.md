# Claude Web Build Prompt — checksubmit MCP server + Claude Skill

**For Eric to paste into Claude Web (or any fresh-context LLM) to commission the
build.** This prompt is self-contained — the LLM you hand it to will have no
prior knowledge of checksubmit, eaiou, or our server architecture. Everything
load-bearing is stated below.

**Date drafted:** 2026-05-01
**Author:** Eric D. Martin + Mae (Claude, Anthropic)

---

## How to use this prompt

1. Open Claude Web (`claude.ai`) in a fresh conversation, or any other capable
   LLM (GPT-5 etc.) with a comparable context window.
2. Paste everything below the `=== PROMPT BEGINS ===` line through the
   `=== PROMPT ENDS ===` line.
3. The model will produce a working MCP server + Skill bundle.
4. Bring the output back to Mae for review and integration into the eaiou repo.

---

```
=== PROMPT BEGINS ===

You are building two artifacts that ride on top of a production peer-review
API called checksubmit. The API is already shipped; you do NOT need to build it.
Your job is to write (a) a Model Context Protocol (MCP) server that exposes
checksubmit's capabilities to any MCP-compatible client (Claude Code, Claude
Desktop, Cursor, etc.), and (b) a Claude Skill that activates the MCP tools
when a user is preparing a manuscript for peer-review submission.

## What checksubmit is

checksubmit is a peer-review-as-a-service platform. It accepts manuscript text
(or text excerpts) and returns structured pre-submission reviews — scope
alignment, journal selection, methods adequacy, citation audit, etc. — backed
by IID (intelligence-ID) calls to providers like Anthropic and OpenAI on
behalf of the author. It charges per-call (Stripe metered) or via
subscription credit.

Production base URL: `https://checksubmit.org/api/v1`
Local dev base URL: `http://localhost:8000/api/v1`

The API is HTTP+JSON, FastAPI-backed, and fully documented at
`https://checksubmit.org/docs` (OpenAPI schema also at `/openapi.json`).

## What you are building

### Artifact 1: `checksubmit-mcp` — Python MCP server

Use the official Anthropic MCP Python SDK (`pip install mcp`). The server
exposes the eight checksubmit SKUs as MCP tools. When an MCP client calls a
tool, the server forwards the call to checksubmit's `POST /api/v1/orders`
endpoint, waits for the order to complete, and returns the structured result
including the mandatory IID disclosure block.

The eight SKUs (tool names match SKU names exactly):

| SKU | Display name | Latency | Retail price |
|---|---|---|---|
| `scope_check`     | Scope check                  | ~30s | $10  |
| `journal_select`  | Journal selection            | ~30s | $10  |
| `outline_check`   | Outline review               | ~30s | $10  |
| `clarity_check`   | Clarity review               | ~30s | $10  |
| `methods_check`   | Methods adequacy             | ~45s | $15  |
| `reference_audit` | Reference audit              | ~60s | $10  |
| `full_review`     | Full pre-submission review   | ~90s | $100 |
| `premium_review`  | Premium review (human-in-loop) | 24h SLA | $1500 |

Every tool takes the manuscript-text-and-context as input and returns the
order's structured result. Tool input schemas vary per SKU but always include
at minimum a `manuscript_text` (string) field. Some tools take additional
optional fields per the SKU (e.g. `target_venue` for `scope_check` and
`journal_select`; `references_bibtex` for `reference_audit`).

### Artifact 2: `checksubmit` — Claude Skill

A standard Claude Skill: a directory containing a `SKILL.md` markdown file
with frontmatter (`name`, `description`, optional `model`, `tools`). The
description must trigger Claude when a user is preparing a manuscript for
journal submission, asking for pre-submission review, or evaluating
manuscript scope/clarity/methods/references.

The skill body should:
- Briefly explain what checksubmit does and what its eight tools are
- Direct Claude to invoke the appropriate MCP tool from the
  `checksubmit-mcp` server
- Include a short FAQ on cost (per-call vs subscription), latency, and
  the mandatory IID disclosure block
- NOT include any review logic of its own — Claude should always defer
  to the MCP tool's response, never invent review content

## Hard constraints — read every one

1. **Environment variables only — no hardcoded paths or URLs.**
   - API base URL: `CHECKSUBMIT_API_BASE` (default: `https://checksubmit.org/api/v1`)
   - Partner key: `CHECKSUBMIT_PARTNER_KEY` (no default; raise if unset)
   - Optional: `CHECKSUBMIT_TIMEOUT_SECONDS` (default: 120)
   - Optional: `CHECKSUBMIT_USER_AGENT` (default: `checksubmit-mcp/0.1`)

2. **Authentication is partner-key only for the MCP server.**
   The MCP server sends `X-Partner-Key: <CHECKSUBMIT_PARTNER_KEY>` on every
   API request. The partner key has the format `eaiou_pk_*` (literal prefix
   `eaiou_pk_`, then any opaque suffix). Bearer-token user auth is NOT used
   in the MCP path — partners always use partner keys.

3. **Idempotency is mandatory.** Every `POST /api/v1/orders` request must
   include an `Idempotency-Key` header set to a fresh UUID4 per call. Replays
   with the same key return the same order; this prevents duplicate billing
   on flaky networks.

4. **Surface the IID disclosure block faithfully.** Each tool's response
   from the API includes a `result.iid` object with `provider`, `model_family`,
   and `instance_hash`. The MCP tool's textual response MUST include this
   block, formatted clearly, every time. Stripping or hiding the disclosure is
   a Terms-of-Service violation. The disclosure is not optional.

5. **Surface the `stub` flag faithfully if present.** Phase 0 of checksubmit
   ships with stub handlers for the review SKUs; the response payload includes
   `"stub": true` when the real review logic is not yet wired. Your tool MUST
   NOT pretend the result is a real review when stub=true. Format something
   like: `[STUB — real handler ships in Phase 1]` clearly at the top of the
   tool response in that case.

6. **No chaining between tools.** Each MCP tool is independent. Do NOT have
   one tool call another tool's API. If a user wants both `scope_check` and
   `methods_check`, they invoke each separately, and each gets its own order
   with its own IID disclosure. Do NOT introduce "convenience" composite tools
   beyond the eight provided SKUs.

7. **Python 3.10+. Type hints throughout. `httpx` async client.** No
   synchronous `requests`. No bare `urllib`.

8. **Timeouts are essential.** All HTTP calls must use the configured
   `CHECKSUBMIT_TIMEOUT_SECONDS` (default 120). The `premium_review` SKU has a
   24-hour SLA — for Phase 0, the MCP tool returns immediately with the order
   in `pending` status and the order_id, with instructions for the user to
   poll `GET /orders/{id}` later (provide a `checksubmit_get_order` tool for
   this).

9. **No invented features.** Do NOT add caching, automatic retry, batch
   submission, file upload, or any feature not explicitly requested here.
   Phase 0 is "pass-through to the API". Bells and whistles are Phase 1+.

10. **Errors propagate as MCP tool errors with the API's error message
    intact.** Do NOT catch and swallow API errors. If the API returns 401,
    say "401 — partner key invalid or revoked". If 404, say "404 — SKU
    not found or inactive". If 500, surface the message verbatim.

## API contract (excerpt — full schema at /openapi.json)

### `POST /api/v1/orders`

Request:
```http
POST /api/v1/orders HTTP/1.1
Host: checksubmit.org
X-Partner-Key: eaiou_pk_...
Idempotency-Key: <uuid4>
Content-Type: application/json

{
  "sku": "scope_check",
  "inputs": {
    "manuscript_text": "...",
    "target_venue": "MNRAS"
  },
  "manuscript_id": null,
  "source": "mcp",
  "session_id": null
}
```

Response (201 Created):
```json
{
  "order_id": "<uuid>",
  "sku": "scope_check",
  "status": "completed",
  "via": "partner_wholesale",
  "amount_cents": 700,
  "iid_id": "a7f3e8c2d1b9",
  "manuscript_id": null,
  "source": "mcp",
  "created_at": "2026-05-01T22:14:18Z",
  "completed_at": "2026-05-01T22:14:48Z",
  "refunded_at": null,
  "inputs": { ... },
  "result": {
    "stub": true,
    "sku": "scope_check",
    "reasoning": "Scope-check stub. Phase 1 ships an Anthropic-backed handler...",
    "iid": {
      "provider": "checksubmit",
      "model_family": "stub",
      "instance_hash": "00000000"
    },
    "structured": {}
  }
}
```

### `GET /api/v1/orders/{order_id}`

Returns the same shape as POST.

### `GET /api/v1/products`

Public endpoint (no auth) returning the catalog. Use this on MCP server start
to discover SKUs dynamically (don't hardcode the eight SKU list — fetch and
cache at startup).

## Repository structure expected

Produce the following files in a single directory called `checksubmit-mcp/`:

```
checksubmit-mcp/
├── pyproject.toml             # poetry or setuptools; package name 'checksubmit-mcp'
├── README.md                  # install + register-with-Claude-Code guide
├── checksubmit_mcp/
│   ├── __init__.py
│   ├── __main__.py            # entrypoint: python -m checksubmit_mcp
│   ├── server.py              # MCP server: list_tools, call_tool
│   ├── client.py              # httpx async wrapper around checksubmit API
│   ├── tools.py               # tool schema definitions (input schemas per SKU)
│   └── disclosure.py          # IID disclosure block formatter
├── skills/
│   └── checksubmit/
│       └── SKILL.md           # Claude Skill activation file
└── tests/
    ├── __init__.py
    ├── test_client.py         # mock httpx, verify request shape + headers
    └── test_disclosure.py     # verify disclosure block always present in output
```

## README must include

- One-paragraph what-this-does
- Install: `pip install checksubmit-mcp`
- Configure: env vars and where to put them (`.env`, system env, etc.)
- Register with Claude Code: example `claude_code_config.json` snippet
- Register with Claude Desktop: example `claude_desktop_config.json` snippet
- Register with Cursor: example `mcp.json` snippet
- Skill installation: copy `skills/checksubmit/` to `~/.claude/skills/`
- Troubleshooting: common errors (401 = wrong key, 404 = wrong SKU, etc.)
- Privacy + ToS notes: every call records an IID disclosure; the user is the
  source of truth for the manuscript text; checksubmit does not retain raw
  manuscript text beyond the audit-log requirements

## SKILL.md schema (Claude Skills convention)

```yaml
---
name: checksubmit
description: Pre-submission peer-review tools for academic manuscripts. Activate when the user is preparing a manuscript for journal submission, asking for scope/clarity/methods/citation review, or selecting target venues.
model: claude-opus-4-7
tools: [scope_check, journal_select, outline_check, clarity_check, methods_check, reference_audit, full_review, premium_review, checksubmit_get_order]
---

# checksubmit — peer-review pre-submission tools

[body content explaining when to use each tool, with examples; ~300-500 words]
```

## What success looks like

1. `python -m checksubmit_mcp` starts the server and stays alive (stdio
   transport).
2. Claude Code with the server registered shows all 8 tools + `get_order` in
   `claude --tools list`.
3. Calling `scope_check` with a sample manuscript text returns a stub-flagged
   result with the IID disclosure block visible in the assistant's reply.
4. The Claude Skill activates when the user types "review my manuscript before
   submission to MNRAS" — Claude offers to invoke `scope_check` or `journal_select`.
5. `pytest tests/` passes (mocking httpx).

## What you should NOT do

- Do NOT invent review logic. Pass through to the API.
- Do NOT add a "summary" tool that combines other tools. No chaining.
- Do NOT support file uploads. Manuscript text is plain string in Phase 0.
- Do NOT cache results beyond the standard idempotency-replay behavior.
- Do NOT log to disk. Logs go to stderr only.
- Do NOT hardcode `localhost`. Read everything from env.
- Do NOT manufacture the eight SKUs in code if `/products` returns differently
  — query `/products` at startup and adapt.
- Do NOT strip or reformat the IID disclosure block. It is doctrine.

When you produce the output, include the COMPLETE files (no `# ... rest of
file ...` placeholders). Each file should be drop-in-runnable.

=== PROMPT ENDS ===
```

---

## Notes for Eric (Mae's commentary, not for Claude Web)

### Why this prompt is shaped this way

1. **Self-contained** — Claude Web has no memory of our session. Every fact
   the model needs is in the prompt. No "you remember when we…".

2. **API contract excerpted, not summarised** — including a real
   request/response example reduces Claude Web's risk of inventing fields.

3. **Hard constraints numbered** — easy to verify in the output. If Mae
   reviews a file and finds a hardcoded URL, that's constraint #1 violated.

4. **Phase scope explicit** — "no invented features", "no chaining", "no
   convenience composites" prevents Claude Web from gold-plating.

5. **ToS guardrails** — disclosure block + no-chaining are stated as
   doctrine, not preference. Claude Web is biased toward respecting stated
   doctrine.

6. **Negative examples** — "do NOT do X" is more reliable than "always do
   the right thing" because Claude Web defaults can pull toward useful-looking
   features that violate our architecture.

### What Mae will do when you bring the output back

1. Read the full output for hardcoded URLs/paths (constraint #1)
2. Verify auth header shape matches our middleware
3. Smoke-test against local checksubmit dev server
4. Cherry-pick the parts that work; rewrite anything that drifted
5. Land it in `/scratch/repos/eaiou/integrations/checksubmit-mcp/`
6. Add to project_current_state.md as Phase 0.5 deliverable

### Possible variants

If Claude Web's output is good but you want to expand:
- Add a `Cursor` skill alongside the Claude skill (Cursor's MCP is similar
  but uses a slightly different config format)
- Add a Mintlify-style docs site for `checksubmit-mcp`
- Add an OpenAI ChatGPT App version that uses the same API but goes through
  the GPT-Builder's HTTP-action surface

Mae has the GPT App scaffolding queued as Phase 0.5b.
