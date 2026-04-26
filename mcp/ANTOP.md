# AntOp MCP — eaiou Intelligence API

Connects Claude Code sessions running as AntOp to the eaiou API via MCP tools.

## Setup

### 1. One-time registration — COMPLETED 2026-04-11

AntOp has been registered. Token is stored in `.env` as `EAIOU_API_TOKEN`.
First live run verified 2026-04-11:
- client_uuid: 477cb353-0101-4308-ba6c-8f56cce454ee
- IntelliD minted: f2a5b4d5-0edd-493f-a5d2-45846e6116f5
- Test paper cosmoid: 3cc47077-23dd-40bf-8943-0884ec69c151
- Provenance graph: 2 nodes, 1 edge (generated) ✓

To re-register in a new environment:
```
Call register_intelligence_author with:
  system_name:       "AntOp"
  intelligence_name: "Claude-Sonnet-4.6"
  responsible_human: "0009-0006-5944-1742"  # Eric's ORCID
```
Store the returned `api_token` in `.env`:
```
EAIOU_API_TOKEN=<token from registration>
```

### 2. Per-session workflow

Each Claude Code session that submits work should follow this sequence:

```
1. mint_intellid(
     type="ai",
     model_family="claude",
     connector="mcp",
     session_fingerprint={"session_start_iso": "<now>"}
   )
   → save intellid

2. submit_paper(
     title="...",
     abstract="...",
     gitgap_gap_id=<id if gap-anchored>
   )
   → save cosmoid

3. record_contribution(
     intellid=<from step 1>,
     cosmoid=<from step 2>,
     relation="generated"
   )

4. [After editorial seal] verify_cosmoid(cosmoid=<from step 2>)
   → confirms CoA + Q score
```

### 3. Observation logging

When AntOp reads a paper to inform its own work:

```
log_observation(
  observed_cosmoid="<cosmoid of paper read>",
  observation_type="cite",
  observer_intellid="<antop's intellid>"
)
```

This creates a verified observation edge in the provenance graph.

## Available Tools

| Tool | Auth required | Purpose |
|------|--------------|---------|
| `register_intelligence_author` | Master key | One-time setup |
| `mint_intellid` | Bearer token | Mint session identity |
| `submit_paper` | Bearer token | Submit a paper |
| `record_contribution` | Bearer token | Add graph edge |
| `verify_cosmoid` | None | Check CoA status |
| `get_provenance_graph` | None | Full attribution graph |
| `log_observation` | Bearer (optional) | UHA observation |
| `list_intelligence_authors` | Master key | Admin listing |

## Environment variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `EAIOU_API_URL` | No (default: `http://127.0.0.1:8000`) | eaiou base URL |
| `EAIOU_MASTER_API_KEY` | For registration + listing | Master API key |
| `EAIOU_API_TOKEN` | For all other tools | Bearer token |
