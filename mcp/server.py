"""
eaiou AntOp MCP Server

Exposes eaiou's intelligence API as MCP tools so that Claude Code sessions
running as AntOp can submit papers, mint IntelliIds, record contributions,
and verify CoAs without leaving their conversation context.

All tools call the eaiou HTTP API — they go through the same authentication
and validation layer as any external caller.

Configuration (environment variables):
  EAIOU_API_URL          — base URL of the running eaiou instance
                           default: http://127.0.0.1:8000
  EAIOU_MASTER_API_KEY   — master key for author registration (one-time setup)
  EAIOU_API_TOKEN        — Bearer token for paper/intellid operations
                           obtained by calling register_intelligence_author once

Session pattern for AntOp:
  1. Call register_intelligence_author once → store the returned api_token
  2. Set EAIOU_API_TOKEN in environment
  3. For each paper session:
     a. mint_intellid          → get intellid for this session
     b. submit_paper           → get paper_id + cosmoid
     c. record_contribution    → link intellid to paper via cosmoid
     d. verify_cosmoid         → confirm CoA after seal
"""

import os
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("eaiou-antop")

EAIOU_API_URL = os.getenv("EAIOU_API_URL", "http://127.0.0.1:8000").rstrip("/")


def _api_token() -> str:
    token = os.getenv("EAIOU_API_TOKEN", "")
    if not token:
        raise ValueError(
            "EAIOU_API_TOKEN not set. "
            "Call register_intelligence_author first to obtain a token."
        )
    return token


def _master_key() -> str:
    key = os.getenv("EAIOU_MASTER_API_KEY", "")
    if not key:
        raise ValueError("EAIOU_MASTER_API_KEY not set.")
    return key


def _bearer_headers() -> dict:
    return {"Authorization": f"Bearer {_api_token()}"}


def _check(resp: httpx.Response) -> dict:
    """Raise with API error detail if response is not 2xx."""
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        raise ValueError(f"eaiou API error {resp.status_code}: {detail}")
    return resp.json()


# ── Author registration ───────────────────────────────────────────────────────

@mcp.tool()
def register_intelligence_author(
    system_name: str,
    intelligence_name: str,
    intellid_ref: str = "",
    responsible_human: str = "",
) -> dict:
    """
    Register an intelligence as an eaiou author. Requires EAIOU_MASTER_API_KEY.
    Returns an api_token — store it as EAIOU_API_TOKEN for subsequent calls.
    This is a one-time setup call per intelligence instance.

    Args:
        system_name:        Orchestration system name, e.g. "AntOp"
        intelligence_name:  Model identifier, e.g. "Claude-Sonnet-4.6"
        intellid_ref:       Optional IntelliD record UUID if already minted
        responsible_human:  Organizational oversight contact (ORCID or name)
    """
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{EAIOU_API_URL}/api/v1/authors",
            headers={"X-API-Key": _master_key()},
            json={
                "system_name":        system_name,
                "intelligence_name":  intelligence_name,
                "intellid_ref":       intellid_ref,
                "responsible_human":  responsible_human,
            },
        )
    result = _check(resp)
    return {
        "client_uuid":       result.get("client_uuid"),
        "api_token":         result.get("api_token"),
        "origin_type":       result.get("origin_type"),
        "note": (
            "Store api_token as EAIOU_API_TOKEN in environment. "
            "It is not retrievable after this response."
        ),
    }


# ── IntelliId minting ─────────────────────────────────────────────────────────

@mcp.tool()
def mint_intellid(
    type: str = "ai",
    model_family: str = "claude",
    connector: str = "mcp",
    cosmoid_context: str = "",
    scope_paper_id: int = None,
    session_fingerprint: dict = None,
) -> dict:
    """
    Mint a new IntelliId for this intelligence session.
    One IntelliId per session — call once per conversation, not per paper.

    Args:
        type:               Identity type: ai | human | hybrid | system
        model_family:       Disclosed model family: claude, gpt-4, gemini, etc.
        connector:          How connected: mcp | api | direct | manual | system
        cosmoid_context:    CosmoID of the paper being worked on, if known
        scope_paper_id:     Integer paper ID this IntelliId is scoped to
        session_fingerprint: Optional dict with session context for instance_hash
    """
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{EAIOU_API_URL}/api/v1/intellid",
            headers=_bearer_headers(),
            json={
                "type":               type,
                "model_family":       model_family,
                "connector":          connector,
                "cosmoid_context":    cosmoid_context,
                "scope_paper_id":     scope_paper_id,
                "session_fingerprint": session_fingerprint or {},
            },
        )
    return _check(resp)


# ── Paper submission ──────────────────────────────────────────────────────────

@mcp.tool()
def submit_paper(
    title: str,
    abstract: str,
    keywords: str = "",
    ai_involvement_level: str = "collaborative",
    ai_involvement_notes: str = "",
    gitgap_gap_id: int = None,
    gitgap_source_pmcid: str = "",
) -> dict:
    """
    Submit a paper authored by the registered intelligence.
    Returns paper_id, paper_uuid, cosmoid, and status.
    The CosmoID is the permanent identifier — use it for contribution recording
    and CoA verification.

    Args:
        title:                Paper title
        abstract:             Full abstract / hypothesis statement
        keywords:             Comma-separated keywords
        ai_involvement_level: none | editing | analysis | drafting | collaborative
        ai_involvement_notes: Free-text description of AI involvement
        gitgap_gap_id:        Integer gap ID from gitgap if addressing a known gap
        gitgap_source_pmcid:  PMC ID of the source paper if derived from one
    """
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{EAIOU_API_URL}/api/v1/papers",
            headers=_bearer_headers(),
            json={
                "title":                title,
                "abstract":             abstract,
                "keywords":             keywords,
                "ai_involvement_level": ai_involvement_level,
                "ai_involvement_notes": ai_involvement_notes,
                "gitgap_gap_id":        gitgap_gap_id,
                "gitgap_source_pmcid":  gitgap_source_pmcid,
            },
        )
    return _check(resp)


# ── Contribution recording ────────────────────────────────────────────────────

@mcp.tool()
def record_contribution(
    intellid: str,
    cosmoid: str,
    relation: str = "generated",
    artifact_type: str = "paper",
    weight: float = None,
    confidence: float = None,
    notes: str = "",
) -> dict:
    """
    Record this intelligence's contribution to an artifact in the attribution graph.
    The IntelliId must be minted before calling this.

    Args:
        intellid:      IntelliId UUID from mint_intellid
        cosmoid:       CosmoID of the artifact being contributed to
        relation:      generated | edited | validated | rejected | reviewed |
                       cited | derived | proposed | refuted
        artifact_type: paper | version | ai_session | remsearch | review | dataset | claim
        weight:        Contribution weight 0.0–1.0 (optional)
        confidence:    Attribution confidence 0.0–1.0 (optional)
        notes:         Free-text notes about the contribution
    """
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{EAIOU_API_URL}/api/v1/intellid/{intellid}/contribute",
            headers=_bearer_headers(),
            json={
                "artifact_type": artifact_type,
                "relation":      relation,
                "cosmoid":       cosmoid,
                "weight":        weight,
                "confidence":    confidence,
                "notes":         notes,
            },
        )
    return _check(resp)


# ── CoA verification ──────────────────────────────────────────────────────────

@mcp.tool()
def verify_cosmoid(cosmoid: str) -> dict:
    """
    Verify a CosmoID Certificate of Attestation.
    Public endpoint — no authentication required.
    Returns seal status, gate validity, MBS, Q score, and tombstone state.

    Args:
        cosmoid: CosmoID UUID of the paper to verify
    """
    with httpx.Client(timeout=30) as client:
        resp = client.get(f"{EAIOU_API_URL}/api/v1/verify/{cosmoid}")
    if resp.status_code == 404:
        return {"found": False, "cosmoid": cosmoid, "note": "Not sealed or not found."}
    return {**_check(resp), "found": True}


# ── Provenance graph ──────────────────────────────────────────────────────────

@mcp.tool()
def get_provenance_graph(cosmoid: str) -> dict:
    """
    Retrieve the full provenance graph for an artifact.
    Returns nodes (intellids, artifact, seal) and edges (contributions, observations).

    Args:
        cosmoid: CosmoID UUID of the artifact
    """
    with httpx.Client(timeout=30) as client:
        resp = client.get(f"{EAIOU_API_URL}/api/v1/cosmoid/{cosmoid}/graph")
    if resp.status_code == 404:
        return {"found": False, "cosmoid": cosmoid}
    return {**_check(resp), "found": True}


# ── Observation logging ───────────────────────────────────────────────────────

@mcp.tool()
def log_observation(
    observed_cosmoid: str,
    observation_type: str = "read",
    observer_intellid: str = "",
    uha_address: str = "",
) -> dict:
    """
    Log a UHA observation event against an artifact.
    Use this when AntOp reads, cites, or validates a paper by CosmoID.
    Calling with a valid Bearer token marks the observation as 'verified'.

    Args:
        observed_cosmoid:  CosmoID of the artifact being observed
        observation_type:  read | cite | fork | contact | validate | replicate
        observer_intellid: IntelliId of the observing intelligence (if minted)
        uha_address:       UHA-encoded observation address (if computed)
    """
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{EAIOU_API_URL}/api/v1/observe",
            headers=_bearer_headers(),
            json={
                "observed_cosmoid":  observed_cosmoid,
                "observation_type":  observation_type,
                "observer_intellid": observer_intellid,
                "uha_address":       uha_address,
            },
        )
    return _check(resp)


# ── Intelligence author listing ───────────────────────────────────────────────

@mcp.tool()
def list_intelligence_authors() -> list:
    """
    List all registered intelligence authors. Requires EAIOU_MASTER_API_KEY.
    Useful for AntOp to verify its own registration and see active clients.
    """
    with httpx.Client(timeout=30) as client:
        resp = client.get(
            f"{EAIOU_API_URL}/api/v1/authors",
            headers={"X-API-Key": _master_key()},
        )
    result = _check(resp)
    # Serialize datetimes
    return [
        {k: str(v) if hasattr(v, "isoformat") else v for k, v in row.items()}
        for row in result
    ]


# ── HTTP helpers (async — used by Phase 1+ tools) ────────────────────────────

import os as _os
import httpx as _httpx

_BASE = _os.environ.get("EAIOU_API_URL", "http://127.0.0.1:8000")
_TIMEOUT = 30.0


async def _request(method: str, path: str, **kwargs) -> dict:
    url = _BASE.rstrip("/") + path
    async with _httpx.AsyncClient(timeout=_TIMEOUT) as client:
        r = await client.request(method, url, **kwargs)
        try:
            return r.json()
        except Exception:
            return {"status_code": r.status_code, "text": r.text}


async def _get(path: str, params: dict = None) -> dict:
    return await _request("GET", path, params=params)


async def _post(path: str, json: dict = None) -> dict:
    return await _request("POST", path, json=json)


async def _patch(path: str, json: dict = None) -> dict:
    return await _request("PATCH", path, json=json)


async def _delete(path: str) -> dict:
    return await _request("DELETE", path)


async def _log_action(action: str, entity_id=None) -> None:
    try:
        await _post("/api/v1/log", json={"action": action, "entity_id": entity_id})
    except Exception:
        pass  # Best-effort — never fail the main operation


# Sealed fields stripped from all non-governance responses
_SEALED = frozenset({
    "submission_sealed_at",
    "acceptance_sealed_at",
    "publication_sealed_at",
    "attestation_sealed_at",
    "sealed_by",
    "submission_hash",
})


def _strip_sealed(obj):
    if isinstance(obj, dict):
        return {k: _strip_sealed(v) for k, v in obj.items() if k not in _SEALED}
    if isinstance(obj, list):
        return [_strip_sealed(i) for i in obj]
    return obj


# ============================================================
# PHASE 1 — paper.* (14 tools)
# ============================================================


@mcp.tool()
async def paper_get(id: int) -> dict:
    """Get a paper by ID. Strips sealed temporal fields for non-governance callers."""
    resp = await _get(f"/api/v1/papers/{id}")
    return _strip_sealed(resp)


@mcp.tool()
async def paper_list(filters: dict = {}, limit: int = 20, offset: int = 0, sort: str = "q_signal") -> dict:
    """List papers sorted by q_signal DESC. Returns error if date sort requested."""
    if any(k in sort.lower() for k in ("date", "time", "sealed", "created")):
        return {"error": "Temporal Blindness violation", "code": 400,
                "detail": "Date-based sorting is forbidden. Use q_signal."}
    resp = await _get("/api/v1/papers", params={"limit": limit, "offset": offset})
    return _strip_sealed(resp)


@mcp.tool()
async def paper_search(query: str, filters: dict = {}) -> dict:
    """Search papers. Results sorted by q_signal DESC."""
    resp = await _get("/api/v1/papers/search", params={"q": query})
    return _strip_sealed(resp)


@mcp.tool()
async def paper_create(title: str, abstract: str, authorship_mode: str,
                       authors_json: str, keywords: str) -> dict:
    """Create a new paper draft. Caller must have AUTHOR role."""
    resp = await _post("/api/v1/papers", json={
        "title": title, "abstract": abstract,
        "authorship_mode": authorship_mode,
        "authors_json": authors_json, "keywords": keywords,
    })
    await _log_action("PAPER_CREATED", resp.get("id"))
    return resp


@mcp.tool()
async def paper_update(id: int, data: dict) -> dict:
    """Update paper fields. Caller must be owner or EDITOR. Sealed fields rejected."""
    sealed = {
        "submission_sealed_at", "acceptance_sealed_at", "publication_sealed_at",
        "attestation_sealed_at", "sealed_by", "submission_hash",
    }
    forbidden = set(data.keys()) & sealed
    if forbidden:
        return {"error": "Cannot update sealed fields", "fields": list(forbidden), "code": 400}
    resp = await _patch(f"/api/v1/papers/{id}", json=data)
    await _log_action("PAPER_UPDATED", id)
    return resp


@mcp.tool()
async def paper_delete(id: int) -> dict:
    """Tombstone a paper (state=-2). ADMIN only. Never hard-deletes."""
    resp = await _patch(f"/api/v1/papers/{id}", json={"state": -2})
    await _log_action("PAPER_TOMBSTONED", id)
    return resp


@mcp.tool()
async def paper_get_versions(paper_id: int) -> dict:
    """Get all versions for a paper. Strips generated_at for public callers."""
    resp = await _get(f"/api/v1/papers/{paper_id}/versions")
    if isinstance(resp, list):
        return {"versions": [_strip_sealed({**v, "generated_at": None}) for v in resp]}
    return _strip_sealed(resp)


@mcp.tool()
async def paper_create_version(paper_id: int, label: str, ai_flag: bool = False,
                               notes: str = "") -> dict:
    """Add a new version to a paper. Caller must be AUTHOR or EDITOR."""
    resp = await _post(f"/api/v1/papers/{paper_id}/versions",
                       json={"label": label, "ai_flag": ai_flag, "notes": notes})
    await _log_action("VERSION_CREATED", paper_id)
    return resp


@mcp.tool()
async def paper_get_workflow(paper_id: int) -> dict:
    """Get workflow state and available transitions for a paper."""
    return await _get(f"/api/v1/papers/{paper_id}/workflow")


@mcp.tool()
async def paper_get_integrity_chain(paper_id: int) -> dict:
    """Get the integrity/provenance chain for a paper. No sealed dates returned."""
    resp = await _get(f"/api/v1/papers/{paper_id}/integrity")
    return _strip_sealed(resp)


@mcp.tool()
async def paper_link_gap(paper_id: int, gap_id: int) -> dict:
    """Link a paper to a research gap. Caller must be AUTHOR or EDITOR."""
    resp = await _post(f"/api/v1/papers/{paper_id}/gaps", json={"gap_id": gap_id})
    await _log_action("GAP_LINKED", paper_id)
    return resp


@mcp.tool()
async def paper_unlink_gap(paper_id: int, gap_id: int) -> dict:
    """Unlink a paper from a research gap. Caller must be AUTHOR or EDITOR."""
    resp = await _delete(f"/api/v1/papers/{paper_id}/gaps/{gap_id}")
    await _log_action("GAP_UNLINKED", paper_id)
    return resp


@mcp.tool()
async def paper_get_transparency(paper_id: int) -> dict:
    """Get the transparency block for a paper (remsearch + AI disclosure)."""
    return await _get(f"/api/v1/papers/{paper_id}/transparency")


@mcp.tool()
async def paper_get_badges(paper_id: int) -> dict:
    """Get quality and integrity badges for a paper."""
    return await _get(f"/api/v1/papers/{paper_id}/badges")


# ============================================================
# PHASE 1 — auth.* (8 tools)
# ============================================================


@mcp.tool()
async def auth_login(username: str, password: str) -> dict:
    """Authenticate with username/password. Returns session token."""
    return await _post("/auth/api/login", json={"username": username, "password": password})


@mcp.tool()
async def auth_logout() -> dict:
    """Invalidate the current session."""
    return await _post("/auth/api/logout", json={})


@mcp.tool()
async def auth_register(name: str, email: str, password: str) -> dict:
    """Register a new user (Registered role only; Author role assigned separately)."""
    return await _post("/auth/api/register", json={"name": name, "email": email, "password": password})


@mcp.tool()
async def auth_check_permission(user_id: int, action: str, paper_id: int = None) -> dict:
    """Check if a user has permission to perform an action."""
    params = {"user_id": user_id, "action": action}
    if paper_id:
        params["paper_id"] = paper_id
    return await _get("/auth/api/permissions/check", params=params)


@mcp.tool()
async def auth_get_roles(user_id: int) -> dict:
    """Get roles for a user. Own roles or ADMIN for any user."""
    return await _get(f"/auth/api/users/{user_id}/roles")


@mcp.tool()
async def auth_api_key_create(user_id: int, label: str) -> dict:
    """Create an API key. ADMIN only. Raw key returned once — hash stored."""
    resp = await _post("/auth/api/keys", json={"user_id": user_id, "label": label})
    await _log_action("API_KEY_CREATED", user_id)
    return resp


@mcp.tool()
async def auth_api_key_revoke(key_id: int) -> dict:
    """Revoke an API key. ADMIN only."""
    resp = await _patch(f"/auth/api/keys/{key_id}", json={"active": False})
    await _log_action("API_KEY_REVOKED", key_id)
    return resp


@mcp.tool()
async def auth_api_key_list(user_id: int) -> dict:
    """List API keys for a user. ADMIN only. Keys masked to last 4 chars."""
    return await _get("/auth/api/keys", params={"user_id": user_id})


# ============================================================
# PHASE 1 — user.* (10 tools)
# ============================================================


@mcp.tool()
async def user_get(id: int) -> dict:
    """Get a user profile. AUTH (own) or EDITOR+ (any)."""
    return await _get(f"/api/v1/users/{id}")


@mcp.tool()
async def user_list(filters: dict = {}) -> dict:
    """List users. EDITOR+ only. Filters: group, has_orcid."""
    return await _get("/api/v1/users", params=filters)


@mcp.tool()
async def user_create(name: str, email: str, password: str, groups: list = []) -> dict:
    """Create a user. ADMIN only."""
    resp = await _post("/api/v1/users", json={"name": name, "email": email,
                                              "password": password, "groups": groups})
    await _log_action("USER_CREATED", resp.get("id"))
    return resp


@mcp.tool()
async def user_update(id: int, data: dict) -> dict:
    """Update user profile. AUTH (own) or ADMIN (any)."""
    resp = await _patch(f"/api/v1/users/{id}", json=data)
    await _log_action("USER_UPDATED", id)
    return resp


@mcp.tool()
async def user_delete(id: int) -> dict:
    """Disable/tombstone a user. ADMIN only. Never hard-deletes."""
    resp = await _patch(f"/api/v1/users/{id}", json={"state": -2, "active": False})
    await _log_action("USER_TOMBSTONED", id)
    return resp


@mcp.tool()
async def user_assign_role(user_id: int, role: str) -> dict:
    """Assign a role to a user. ADMIN only."""
    resp = await _post(f"/api/v1/users/{user_id}/roles", json={"role": role})
    await _log_action("ROLE_ASSIGNED", user_id)
    return resp


@mcp.tool()
async def user_remove_role(user_id: int, role: str) -> dict:
    """Remove a role from a user. ADMIN only."""
    resp = await _delete(f"/api/v1/users/{user_id}/roles/{role}")
    await _log_action("ROLE_REMOVED", user_id)
    return resp


@mcp.tool()
async def user_link_orcid(user_id: int, orcid_id: str) -> dict:
    """Link an ORCID to a user profile. AUTH (own) only."""
    resp = await _patch(f"/api/v1/users/{user_id}", json={"orcid": orcid_id})
    await _log_action("ORCID_LINKED", user_id)
    return resp


@mcp.tool()
async def user_unlink_orcid(user_id: int) -> dict:
    """Unlink the ORCID from a user profile. AUTH (own) only."""
    resp = await _patch(f"/api/v1/users/{user_id}", json={"orcid": None})
    await _log_action("ORCID_UNLINKED", user_id)
    return resp


@mcp.tool()
async def user_get_activity(user_id: int) -> dict:
    """Get activity summary for a user. AUTH (own) or EDITOR+."""
    return await _get(f"/api/v1/users/{user_id}/activity")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
