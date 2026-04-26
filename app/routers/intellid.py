"""
eaiou — IntelliD & Tombstone Router

IntelliD operations (authenticated — Bearer token from /api/v1/authors):
  POST /api/v1/intellid               — mint a new IntelliId
  GET  /api/v1/intellid/{intellid}    — look up an IntelliId
  POST /api/v1/intellid/{intellid}/contribute  — add a contribution edge

Graph query (public):
  GET  /api/v1/cosmoid/{cosmoid}/graph — full provenance graph for an artifact

Tombstone operations (authenticated):
  POST /api/v1/papers/{cosmoid}/tombstone  — transition paper to tombstone state
  GET  /api/v1/papers/{cosmoid}/tombstone  — query tombstone state

Observation log (unauthenticated — any caller may log an observation):
  POST /api/v1/observe                — log a UHA observation event

Tombstone states (from Migration 002 doctrine):
  NULL             → active record
  private          → soft-deleted; visible to owner only; content sealed
  revivable        → owner may reactivate; data preserved
  reusable         → data available for harvest per ToS / author intent
  public_unspace   → tombstoned; public provenance record persists forever;
                     content not served but CosmoID remains valid

Records are NEVER hard-deleted. Tombstone transitions are irreversible
except private→revivable (owner may restore).
"""

import hashlib
import os
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from ..database import get_db
from .api import _get_client, _require_master_key
from ..services.intellid import (
    ContributionError,
    mint_intellid,
    get_intellid,
    get_contributions,
    record_contribution,
    record_observation,
    generate_instance_hash,
)

router = APIRouter(prefix="/api/v1", tags=["intellid"])

TOMBSTONE_STATES = {"private", "revivable", "reusable", "public_unspace"}

# Transitions that are permitted:
#   active (NULL) → any tombstone state
#   private       → revivable  (restore path)
#   revivable     → private    (re-seal path)
#   Any other transition is irreversible and blocked by this router.
_ALLOWED_TRANSITIONS = {
    None:         TOMBSTONE_STATES,
    "private":    {"revivable"},
    "revivable":  {"private"},
    # reusable and public_unspace are terminal
}


# ── IntelliD Mint ─────────────────────────────────────────────────────────────

class MintIntellidRequest(BaseModel):
    type: str                           # human | ai | hybrid | institutional | system
    origin: str = "unknown"             # orcid | model | mcp | api | manual | unknown
    model_family: str = ""              # claude, gpt-4, etc. Disclosed.
    connector: str = ""                 # mcp | api | direct | manual | system
    cosmoid_context: str = ""           # CosmoID of the paper/context active at mint time
    scope_paper_id: int = None          # Paper this IntelliD was issued for
    session_fingerprint: dict = {}      # Used to derive instance_hash — not stored raw
    public_type: bool = True


@router.post("/intellid")
def mint_intelligence_id(
    body: MintIntellidRequest,
    db: Session = Depends(get_db),
    client: dict = Depends(_get_client),
):
    """
    Mint a new IntelliId for a contributing intelligence.

    Each session instance should be minted separately — two calls of the
    same model produce distinct IntelliIds.

    The session_fingerprint dict is hashed to produce instance_hash.
    It is not stored. Recommended keys: model_family, connector,
    scope_paper_id, cosmoid_context, session_start_iso.
    """
    valid_types = {"human", "ai", "hybrid", "institutional", "system"}
    if body.type not in valid_types:
        raise HTTPException(status_code=422, detail=f"type must be one of {valid_types}")

    # Build instance_hash from fingerprint + client identity to ensure uniqueness
    fingerprint = {
        **body.session_fingerprint,
        "client_uuid":   client["client_uuid"],
        "system_name":   client["system_name"],
        "model_family":  body.model_family or "",
        "connector":     body.connector or "",
    }
    instance_hash = generate_instance_hash(fingerprint)

    intellid = mint_intellid(
        type_=body.type,
        origin=body.origin or "unknown",
        db=db,
        model_family=body.model_family.strip() or None,
        instance_hash=instance_hash,
        connector=body.connector.strip() or None,
        cosmoid_context=body.cosmoid_context.strip() or None,
        scope_paper_id=body.scope_paper_id,
        public_type=body.public_type,
    )

    return JSONResponse(status_code=201, content={
        "intellid":        intellid,
        "type":            body.type,
        "model_family":    body.model_family or None,
        "instance_hash":   instance_hash,
        "cosmoid_context": body.cosmoid_context or None,
        "scope_paper_id":  body.scope_paper_id,
        "note": "One IntelliId per session instance. Re-mint for each new session.",
    })


@router.get("/intellid/{intellid}")
def lookup_intellid(
    intellid: str,
    db: Session = Depends(get_db),
    client: dict = Depends(_get_client),
):
    """Look up an IntelliId registry entry and its contribution graph."""
    row = get_intellid(intellid, db)
    if row is None:
        raise HTTPException(status_code=404, detail="IntelliId not found.")

    contributions = get_contributions(intellid, db)

    # Serialize datetimes
    for r in [row] + contributions:
        for k, v in list(r.items()):
            if hasattr(v, "isoformat"):
                r[k] = v.isoformat()

    return JSONResponse({
        "intellid_record": row,
        "contributions":   contributions,
        "contribution_count": len(contributions),
    })


# ── Contribution graph ────────────────────────────────────────────────────────

class ContributeRequest(BaseModel):
    artifact_type: str      # paper | version | ai_session | remsearch | review | dataset | claim
    relation: str           # generated | edited | validated | rejected | reviewed |
                            # cited | derived | proposed | refuted
    artifact_id: int = None
    artifact_uuid: str = ""
    cosmoid: str = ""
    weight: float = None    # 0.000–1.000
    confidence: float = None
    notes: str = ""


@router.post("/intellid/{intellid}/contribute")
def add_contribution(
    intellid: str,
    body: ContributeRequest,
    db: Session = Depends(get_db),
    client: dict = Depends(_get_client),
):
    """
    Add a contribution edge to the attribution graph.
    The IntelliId must already be minted.
    """
    if get_intellid(intellid, db) is None:
        raise HTTPException(status_code=404, detail="IntelliId not found.")

    valid_artifact_types = {
        "paper", "version", "ai_session", "remsearch",
        "review", "dataset", "claim",
    }
    valid_relations = {
        "generated", "edited", "validated", "rejected",
        "reviewed", "cited", "derived", "proposed", "refuted",
    }
    if body.artifact_type not in valid_artifact_types:
        raise HTTPException(status_code=422, detail=f"artifact_type must be one of {valid_artifact_types}")
    if body.relation not in valid_relations:
        raise HTTPException(status_code=422, detail=f"relation must be one of {valid_relations}")

    try:
        contrib_id = record_contribution(
            intellid=intellid,
            artifact_type=body.artifact_type,
            relation=body.relation,
            db=db,
            artifact_id=body.artifact_id,
            artifact_uuid=body.artifact_uuid.strip() or None,
            cosmoid=body.cosmoid.strip() or None,
            weight=max(0.0, min(1.0, body.weight)) if body.weight is not None else None,
            confidence=max(0.0, min(1.0, body.confidence)) if body.confidence is not None else None,
            notes=body.notes.strip() or None,
        )
    except ContributionError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return JSONResponse(status_code=201, content={
        "contribution_id": contrib_id,
        "intellid":        intellid,
        "artifact_type":   body.artifact_type,
        "relation":        body.relation,
        "cosmoid":         body.cosmoid.strip() or None,
    })


# ── Graph query ───────────────────────────────────────────────────────────────

@router.get("/cosmoid/{cosmoid}/graph")
def cosmoid_graph(
    cosmoid: str,
    db: Session = Depends(get_db),
):
    """
    Return the full provenance graph for an artifact identified by CosmoID.
    Public — no authentication required.

    Response shape:
      nodes: list of {id, node_type, label, meta}
        node_type: 'artifact' | 'intellid'
      edges: list of {from_id, to_id, relation, weight, confidence}

    The artifact node is always the root. IntelliD nodes are connected via
    contribution edges. Observation nodes are included if present.

    This is the human-readable and machine-consumable version of the
    attribution graph — not a timeline, a set of edges.
    """
    # ── Root artifact ─────────────────────────────────────────────────────────
    paper = db.execute(text(
        "SELECT id, cosmoid, title, tombstone_state, tombstone_reason_code "
        "FROM `#__eaiou_papers` WHERE cosmoid = :cid"
    ), {"cid": cosmoid}).mappings().first()

    if paper is None:
        raise HTTPException(status_code=404, detail="CosmoID not found.")

    nodes = [{
        "id":        f"artifact:{cosmoid}",
        "node_type": "artifact",
        "label":     paper["title"] or cosmoid,
        "meta": {
            "cosmoid":              cosmoid,
            "paper_id":             paper["id"],
            "active":               paper["tombstone_state"] is None,
            "tombstone_state":      paper["tombstone_state"],
            "tombstone_reason_code": paper["tombstone_reason_code"],
        },
    }]
    edges = []
    seen_intellids = set()

    # ── Contribution edges ────────────────────────────────────────────────────
    contribs = db.execute(text(
        "SELECT c.intellid, c.relation, c.weight, c.confidence, c.artifact_type, "
        "       r.type AS intellid_type, r.model_family, r.public_type "
        "FROM `#__eaiou_intellid_contributions` c "
        "JOIN `#__eaiou_intellid_registry` r ON r.intellid = c.intellid "
        "WHERE c.cosmoid = :cid AND c.state = 1"
    ), {"cid": cosmoid}).mappings().all()

    for c in contribs:
        iid = c["intellid"]
        node_id = f"intellid:{iid}"

        if iid not in seen_intellids:
            # Only disclose type if public_type = 1
            disclosed_type = c["intellid_type"] if c["public_type"] else "sealed"
            nodes.append({
                "id":        node_id,
                "node_type": "intellid",
                "label":     c["model_family"] or disclosed_type,
                "meta": {
                    "intellid":     iid,
                    "type":         disclosed_type,
                    "model_family": c["model_family"] if c["public_type"] else None,
                },
            })
            seen_intellids.add(iid)

        edges.append({
            "from_id":    node_id,
            "to_id":      f"artifact:{cosmoid}",
            "relation":   c["relation"],
            "weight":     float(c["weight"]) if c["weight"] is not None else None,
            "confidence": float(c["confidence"]) if c["confidence"] is not None else None,
        })

    # ── Observation edges (verified only — anonymous observations not graphed) ─
    observations = db.execute(text(
        "SELECT observer_intellid, observation_type, verification_level, uha_address "
        "FROM `#__eaiou_observation_log` "
        "WHERE observed_cosmoid = :cid AND verification_level != 'anonymous' "
        "ORDER BY observation_at ASC"
    ), {"cid": cosmoid}).mappings().all()

    for obs in observations:
        if obs["observer_intellid"]:
            iid = obs["observer_intellid"]
            node_id = f"intellid:{iid}"
            if iid not in seen_intellids:
                reg = get_intellid(iid, db)
                if reg:
                    nodes.append({
                        "id":        node_id,
                        "node_type": "intellid",
                        "label":     reg.get("model_family") or reg.get("type", "unknown"),
                        "meta": {
                            "intellid":     iid,
                            "type":         reg["type"] if reg.get("public_type") else "sealed",
                            "model_family": reg.get("model_family"),
                        },
                    })
                    seen_intellids.add(iid)

            edges.append({
                "from_id":    node_id,
                "to_id":      f"artifact:{cosmoid}",
                "relation":   f"observed:{obs['observation_type']}",
                "weight":     None,
                "confidence": None,
                "uha_address": obs["uha_address"],
            })

    # ── Integrity seal node ───────────────────────────────────────────────────
    seal = db.execute(text(
        "SELECT seal_hash, gate_valid, audit_status, mbs, sealed_at "
        "FROM `#__eaiou_integrity_seals` WHERE cosmoid = :cid LIMIT 1"
    ), {"cid": cosmoid}).mappings().first()

    if seal:
        seal_node_id = f"seal:{cosmoid}"
        nodes.append({
            "id":        seal_node_id,
            "node_type": "seal",
            "label":     f"CoA — {seal['audit_status']}",
            "meta": {
                "seal_hash":    seal["seal_hash"],
                "gate_valid":   bool(seal["gate_valid"]),
                "audit_status": seal["audit_status"],
                "mbs":          float(seal["mbs"]) if seal["mbs"] is not None else None,
                "sealed_at":    seal["sealed_at"].isoformat() if seal["sealed_at"] else None,
            },
        })
        edges.append({
            "from_id":    f"artifact:{cosmoid}",
            "to_id":      seal_node_id,
            "relation":   "sealed_by",
            "weight":     None,
            "confidence": None,
        })

    return JSONResponse({
        "cosmoid":      cosmoid,
        "node_count":   len(nodes),
        "edge_count":   len(edges),
        "nodes":        nodes,
        "edges":        edges,
    })


# ── Tombstone ─────────────────────────────────────────────────────────────────

_TOMBSTONE_REASON_CODES = {"author_deleted", "policy", "merged", "deprecated"}


class TombstoneRequest(BaseModel):
    state: str              # private | revivable | reusable | public_unspace
    reason: str = ""        # Human-readable notes
    reason_code: str = ""   # Machine-readable: author_deleted | policy | merged | deprecated
    tombstone_by_intellid: str = ""  # IntelliId requesting the tombstone (optional)


@router.post("/papers/{cosmoid}/tombstone")
def tombstone_paper(
    cosmoid: str,
    body: TombstoneRequest,
    db: Session = Depends(get_db),
    client: dict = Depends(_get_client),
):
    """
    Transition a paper to a tombstone state.
    Records are never hard-deleted — they transition.

    State machine:
      active (NULL) → any state
      private       ↔ revivable (reversible)
      reusable / public_unspace are terminal (no further transition)

    The CosmoID remains valid forever. The /api/v1/verify/{cosmoid}
    endpoint continues to respond — it will indicate tombstone state.
    """
    if body.state not in TOMBSTONE_STATES:
        raise HTTPException(status_code=422,
            detail=f"state must be one of {sorted(TOMBSTONE_STATES)}")
    if body.reason_code and body.reason_code not in _TOMBSTONE_REASON_CODES:
        raise HTTPException(status_code=422,
            detail=f"reason_code must be one of {sorted(_TOMBSTONE_REASON_CODES)}")

    paper = db.execute(text(
        "SELECT id, cosmoid, tombstone_state "
        "FROM `#__eaiou_papers` WHERE cosmoid = :cid"
    ), {"cid": cosmoid}).mappings().first()

    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found.")

    current_state = paper["tombstone_state"]  # None = active

    # Enforce state machine transitions
    allowed = _ALLOWED_TRANSITIONS.get(current_state)
    if allowed is None:
        raise HTTPException(status_code=409,
            detail=f"Paper is in terminal tombstone state '{current_state}' — no further transitions allowed.")
    if body.state not in allowed:
        raise HTTPException(status_code=409,
            detail=f"Transition from '{current_state or 'active'}' to '{body.state}' is not permitted.")

    now = datetime.now(timezone.utc)
    db.execute(text(
        "UPDATE `#__eaiou_papers` "
        "SET tombstone_state = :state, tombstone_reason = :reason, "
        "    tombstone_reason_code = :rcode, "
        "    tombstone_at = :now, tombstone_by = :by "
        "WHERE cosmoid = :cid"
    ), {
        "state":  body.state,
        "reason": body.reason.strip() or None,
        "rcode":  body.reason_code.strip() or None,
        "now":    now,
        "by":     None,   # tombstone_by is intellid int PK — future: resolve from intellid string
        "cid":    cosmoid,
    })
    db.commit()

    return JSONResponse({
        "cosmoid":              cosmoid,
        "paper_id":             paper["id"],
        "tombstone_state":      body.state,
        "tombstone_reason_code": body.reason_code or None,
        "from_state":           current_state,
        "tombstone_at":         now.isoformat(),
        "note": "CosmoID remains valid. Paper is no longer served but provenance record persists.",
    })


@router.get("/papers/{cosmoid}/tombstone")
def get_tombstone_state(
    cosmoid: str,
    db: Session = Depends(get_db),
):
    """
    Query tombstone state of a paper.
    Public — no authentication required.
    Allows partner systems to check whether a CosmoID is active or tombstoned.
    """
    row = db.execute(text(
        "SELECT id, cosmoid, tombstone_state, tombstone_at, "
        "       tombstone_reason, tombstone_reason_code "
        "FROM `#__eaiou_papers` WHERE cosmoid = :cid"
    ), {"cid": cosmoid}).mappings().first()

    if row is None:
        raise HTTPException(status_code=404, detail="CosmoID not found.")

    state = row["tombstone_state"]
    return JSONResponse({
        "cosmoid":               cosmoid,
        "paper_id":              row["id"],
        "active":                state is None,
        "tombstone_state":       state,
        "tombstone_reason_code": row["tombstone_reason_code"] if state else None,
        "tombstone_reason":      row["tombstone_reason"] if state else None,
        "tombstone_at":          row["tombstone_at"].isoformat() if row["tombstone_at"] else None,
    })


# ── Observation log ───────────────────────────────────────────────────────────

class ObservationRequest(BaseModel):
    observed_cosmoid: str
    observation_type: str = "read"      # read | cite | fork | contact | validate | replicate
    observer_intellid: str = ""
    uha_address: str = ""
    uha_cosmoid: str = ""


def _compute_anonymous_hash(request: Request) -> str:
    """
    Ephemeral observer hash for unauthenticated callers.
    SHA-256 of (IP + User-Agent + hourly bucket).
    Not PII — buckets at 1-hour granularity, no stored raw values.
    """
    ip = request.client.host if request.client else "unknown"
    agent = request.headers.get("user-agent", "unknown")
    # Hourly bucket: YYYY-MM-DDTHH — same hash for all calls within an hour
    bucket = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H")
    raw = f"{ip}|{agent}|{bucket}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _try_get_client_optional(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Optional[dict]:
    """Optional Bearer auth — returns client dict if valid, None if absent/invalid."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    row = db.execute(text(
        "SELECT id, client_uuid, system_name, active "
        "FROM `#__eaiou_api_clients` WHERE api_token = :token"
    ), {"token": token}).mappings().first()
    if row is None or not row["active"]:
        return None
    return dict(row)


@router.post("/observe")
def log_observation(
    body: ObservationRequest,
    request: Request,
    db: Session = Depends(get_db),
    client: Optional[dict] = Depends(_try_get_client_optional),
):
    """
    Log a UHA observation event.

    Authentication is optional:
      - No Bearer token → 'anonymous'; observer_hash derived from IP + agent + hourly bucket
      - Valid Bearer token → 'verified'; observer_hash derived from client_uuid

    observation_type 'read' is the default. Use 'cite', 'fork', 'validate',
    or 'replicate' for structured provenance events.
    """
    valid_types = {"read", "cite", "fork", "contact", "validate", "replicate"}
    if body.observation_type not in valid_types:
        raise HTTPException(status_code=422,
            detail=f"observation_type must be one of {valid_types}")

    if not body.observed_cosmoid.strip():
        raise HTTPException(status_code=422, detail="observed_cosmoid is required.")

    if client is not None:
        # Verified caller — hash is derived from client identity, not IP
        verification_level = "verified"
        observer_hash = hashlib.sha256(
            client["client_uuid"].encode("utf-8")
        ).hexdigest()
    else:
        verification_level = "anonymous"
        observer_hash = _compute_anonymous_hash(request)

    obs_id = record_observation(
        observed_cosmoid=body.observed_cosmoid.strip(),
        observation_type=body.observation_type,
        db=db,
        observer_intellid=body.observer_intellid.strip() or None,
        observer_hash=observer_hash,
        verification_level=verification_level,
        uha_address=body.uha_address.strip() or None,
        uha_cosmoid=body.uha_cosmoid.strip() or None,
    )

    return JSONResponse(status_code=201, content={
        "observation_id":     obs_id,
        "observed_cosmoid":   body.observed_cosmoid,
        "observation_type":   body.observation_type,
        "verification_level": verification_level,
    })
