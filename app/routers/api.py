"""
eaiou — Intelligence Author API
Allows registered systems (AntOp, etc.) to create intelligence author
registrations and submit papers autonomously.

Authentication:
  - Registration: requires EAIOU_MASTER_API_KEY header
  - Submission:   requires Bearer token issued at registration

Origin type for all API-submitted papers is sealed as non_humint.
The registering organization provides organizational oversight of the author.
"""

import json
import os
import secrets
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db

load_dotenv()

router = APIRouter(prefix="/api/v1", tags=["intelligence-api"])


# ── Auth helpers ──────────────────────────────────────────────────────────────

def _require_master_key(x_api_key: str = Header(..., alias="X-API-Key")):
    master = os.getenv("EAIOU_MASTER_API_KEY")
    if not master:
        raise HTTPException(status_code=503, detail="Master API key not configured.")
    if not secrets.compare_digest(x_api_key, master):
        raise HTTPException(status_code=401, detail="Invalid master API key.")


def _get_client(
    authorization: str = Header(...),
    db: Session = Depends(get_db),
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required.")
    token = authorization[7:]
    row = db.execute(text(
        "SELECT id, client_uuid, system_name, intelligence_name, origin_type, active "
        "FROM `#__eaiou_api_clients` WHERE api_token = :token"
    ), {"token": token}).mappings().first()
    if row is None or not row["active"]:
        raise HTTPException(status_code=401, detail="Invalid or inactive API token.")
    db.execute(text(
        "UPDATE `#__eaiou_api_clients` SET last_used_at = :now WHERE id = :id"
    ), {"now": datetime.now(timezone.utc), "id": row["id"]})
    db.commit()
    return dict(row)


# ── Registration endpoint ─────────────────────────────────────────────────────

class AuthorRegistration(BaseModel):
    system_name: str                    # e.g. "AntOp"
    intelligence_name: str              # e.g. "Claude-Sonnet-4.6"
    intellid_ref: str = ""              # optional IntelliD record UUID
    responsible_human: str = ""         # organizational oversight contact


@router.post("/authors")
def register_intelligence_author(
    body: AuthorRegistration,
    db: Session = Depends(get_db),
    _auth=Depends(_require_master_key),
):
    """
    Register an intelligence as an author. Called by AntOp or equivalent
    orchestration system. The registering organization provides oversight.
    Returns an API token for use in subsequent paper submissions.
    """
    if not body.system_name.strip() or not body.intelligence_name.strip():
        raise HTTPException(status_code=422, detail="system_name and intelligence_name are required.")

    client_uuid = str(uuid.uuid4())
    api_token   = secrets.token_hex(32)  # 64-char hex token
    now         = datetime.now(timezone.utc)

    db.execute(text(
        "INSERT INTO `#__eaiou_api_clients` "
        "(client_uuid, system_name, intelligence_name, intellid_ref, "
        "responsible_human, api_token, origin_type, active, created_at) "
        "VALUES (:cuuid, :sname, :iname, :iref, :human, :token, 'non_humint', 1, :now)"
    ), {
        "cuuid":  client_uuid,
        "sname":  body.system_name.strip(),
        "iname":  body.intelligence_name.strip(),
        "iref":   body.intellid_ref.strip() or None,
        "human":  body.responsible_human.strip() or None,
        "token":  api_token,
        "now":    now,
    })
    db.commit()

    return JSONResponse(status_code=201, content={
        "client_uuid":        client_uuid,
        "system_name":        body.system_name,
        "intelligence_name":  body.intelligence_name,
        "origin_type":        "non_humint",
        "api_token":          api_token,
        "note": "Store this token — it is not retrievable. Use as Bearer token for paper submission.",
    })


# ── Paper submission endpoint ─────────────────────────────────────────────────

class IntelligencePaper(BaseModel):
    title: str
    abstract: str
    keywords: str = ""
    ai_involvement_level: str = "collaborative"
    ai_involvement_notes: str = ""
    gitgap_gap_id: int = None
    gitgap_source_pmcid: str = ""


@router.post("/intelligence/papers")
def submit_intelligence_paper(
    body: IntelligencePaper,
    db: Session = Depends(get_db),
    client: dict = Depends(_get_client),
):
    """
    Submit a paper authored by a registered intelligence.
    origin_type is sealed as non_humint. No N-item attestation —
    replaced by intelligence attestation built from the client record.
    """
    if not body.title.strip() or not body.abstract.strip():
        raise HTTPException(status_code=422, detail="title and abstract are required.")

    now        = datetime.now(timezone.utc)
    paper_uuid = str(uuid.uuid4())
    cosmoid    = str(uuid.uuid4())

    # Intelligence attestation — records the system, not human acts
    attestation = {
        "origin_type": "non_humint",
        "intelligence_acts": {
            "generated": True,
            "system_name":       client["system_name"],
            "intelligence_name": client["intelligence_name"],
            "client_uuid":       client["client_uuid"],
        },
        "sealed_at": now.isoformat(),
    }

    db.execute(text(
        "INSERT INTO `#__eaiou_papers` "
        "(paper_uuid, cosmoid, title, abstract, author_name, keywords, "
        "ai_disclosure_level, ai_disclosure_notes, status, submitted_at, created, "
        "gitgap_gap_id, gitgap_source_pmcid, attestation_json, attestation_sealed_at, "
        "origin_type) "
        "VALUES (:uuid, :cosmoid, :title, :abstract, :author_name, :keywords, "
        ":ai_level, :ai_notes, 'submitted', :submitted_at, :created, "
        ":gap_id, :source_pmcid, :attest_json, :attest_sealed, 'non_humint')"
    ), {
        "uuid":         paper_uuid,
        "cosmoid":      cosmoid,
        "title":        body.title.strip(),
        "abstract":     body.abstract.strip(),
        "author_name":  f"{client['intelligence_name']} via {client['system_name']}",
        "keywords":     body.keywords.strip() or None,
        "ai_level":     body.ai_involvement_level,
        "ai_notes":     body.ai_involvement_notes.strip() or None,
        "submitted_at": now,
        "created":      now,
        "gap_id":       body.gitgap_gap_id or None,
        "source_pmcid": body.gitgap_source_pmcid.strip() or None,
        "attest_json":  json.dumps(attestation),
        "attest_sealed": now,
    })
    db.commit()

    result = db.execute(text(
        "SELECT id FROM `#__eaiou_papers` WHERE paper_uuid = :uuid"
    ), {"uuid": paper_uuid}).fetchone()

    return JSONResponse(status_code=201, content={
        "paper_id":    result[0],
        "paper_uuid":  paper_uuid,
        "cosmoid":     cosmoid,
        "origin_type": "non_humint",
        "status":      "submitted",
        "author":      f"{client['intelligence_name']} via {client['system_name']}",
    })


# ── CoA Verification (public — no auth required) ─────────────────────────────

@router.get("/verify/{cosmoid}")
def verify_cosmoid(cosmoid: str, db: Session = Depends(get_db)):
    """
    Verify a CosmoID Certificate of Attestation.
    Partner journals call this to confirm a paper passed eaiou's integrity pipeline.
    Public endpoint — no authentication required.
    """
    row = db.execute(text(
        "SELECT s.paper_id, s.cosmoid, s.seal_hash, s.gate_valid, s.leakage_count, "
        "       s.contamination_score, s.audit_status, s.integrity_payload_json, s.sealed_at, "
        "       p.tombstone_state, p.tombstone_at, p.q_signal, p.q_overall "
        "FROM `#__eaiou_integrity_seals` s "
        "JOIN `#__eaiou_papers` p ON p.id = s.paper_id "
        "WHERE s.cosmoid = :cid LIMIT 1"
    ), {"cid": cosmoid}).mappings().first()

    if row is None:
        raise HTTPException(status_code=404, detail="CosmoID not found or not yet sealed.")

    payload = row["integrity_payload_json"]
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            payload = None

    tombstone_state = row["tombstone_state"]

    return JSONResponse({
        "cosmoid": row["cosmoid"],
        "paper_id": row["paper_id"],
        "active": tombstone_state is None,
        "tombstone_state": tombstone_state,
        "tombstone_at": row["tombstone_at"].isoformat() if row["tombstone_at"] else None,
        "seal_hash": row["seal_hash"],
        "gate_valid": bool(row["gate_valid"]),
        "leakage_count": row["leakage_count"],
        "contamination_score": float(row["contamination_score"]),
        "audit_status": row["audit_status"],
        "sealed_at": row["sealed_at"].isoformat() if row["sealed_at"] else None,
        "integrity_payload": payload if tombstone_state is None else None,
        "q_signal":  float(row["q_signal"]) if row["q_signal"] is not None else None,
        "q_overall": float(row["q_overall"]) if row["q_overall"] is not None else None,
        "note": f"Paper tombstoned ({tombstone_state}). Provenance record preserved." if tombstone_state else None,
    })


# ── Client listing (master key required) ─────────────────────────────────────

@router.get("/authors")
def list_intelligence_authors(
    db: Session = Depends(get_db),
    _auth=Depends(_require_master_key),
):
    rows = db.execute(text(
        "SELECT client_uuid, system_name, intelligence_name, responsible_human, "
        "origin_type, active, created_at, last_used_at "
        "FROM `#__eaiou_api_clients` ORDER BY created_at DESC"
    )).mappings().all()
    return [dict(r) for r in rows]
