"""
eaiou — IntelliD Service

IntelliD is eaiou's identity layer for contributing intelligences.
One IntelliId per session instance — two sessions of the same model are
distinct IntelliIds. The instance_hash seals the session fingerprint
without exposing provider-specific data.

Doctrine:
  - type is always disclosed (human / ai / hybrid / institutional / system)
  - model_family is disclosed (claude, gpt-4, gemini, etc.)
  - session mapping is sealed (instance_hash only — no raw session IDs)
  - CosmoID context: the CosmoID of the paper/artifact active when the
    IntelliId was issued — binds the intelligence to a specific context

Temporal Blindness note:
  Do NOT use id DESC to sort or prioritize IntelliIds.
  Ordering by id is a hidden time proxy — use created DESC explicitly,
  or use the graph (contributions table) for relevance.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text


# ── Instance hash ─────────────────────────────────────────────────────────────

def generate_instance_hash(session_context: dict) -> str:
    """
    SHA-256 of session-specific context dict.
    Seals the session identity without exposing raw provider data.

    Recommended keys in session_context:
      model_family, connector, scope_paper_id, cosmoid_context,
      session_start_iso (ISO timestamp of session start)

    The hash is deterministic for the same inputs — if you re-call with
    the same dict, you get the same hash. This is intentional: it lets
    the same session be recognized without storing raw session IDs.
    """
    canonical = json.dumps(session_context, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ── Minting ───────────────────────────────────────────────────────────────────

def mint_intellid(
    type_: str,
    origin: str,
    db: Session,
    *,
    model_family: str = None,
    instance_hash: str = None,
    connector: str = None,
    cosmoid_context: str = None,
    scope_paper_id: int = None,
    public_type: bool = True,
) -> str:
    """
    Mint a new IntelliId UUID and persist it to the registry.
    Returns the new intellid string (UUID4).

    type_:  'human' | 'ai' | 'hybrid' | 'institutional' | 'system'
    origin: 'orcid' | 'model' | 'mcp' | 'api' | 'manual' | 'unknown'
    """
    intellid = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    db.execute(text(
        "INSERT INTO `#__eaiou_intellid_registry` "
        "(intellid, type, origin, model_family, instance_hash, connector, "
        " cosmoid_context, scope_paper_id, public_type, state, created) "
        "VALUES (:intellid, :type, :origin, :model_family, :instance_hash, "
        "        :connector, :cosmoid_context, :scope_paper_id, :public_type, 1, :now)"
    ), {
        "intellid":        intellid,
        "type":            type_,
        "origin":          origin,
        "model_family":    model_family,
        "instance_hash":   instance_hash,
        "connector":       connector,
        "cosmoid_context": cosmoid_context,
        "scope_paper_id":  scope_paper_id,
        "public_type":     1 if public_type else 0,
        "now":             now,
    })
    db.commit()
    return intellid


# ── Lookup ────────────────────────────────────────────────────────────────────

def get_intellid(intellid: str, db: Session) -> dict | None:
    """Fetch IntelliId registry row. Returns None if not found."""
    row = db.execute(text(
        "SELECT id, intellid, type, origin, model_family, instance_hash, "
        "       connector, cosmoid_context, scope_paper_id, public_type, state, created "
        "FROM `#__eaiou_intellid_registry` WHERE intellid = :intellid"
    ), {"intellid": intellid}).mappings().first()
    if row is None:
        return None
    return dict(row)


def get_contributions(intellid: str, db: Session) -> list[dict]:
    """Fetch all contribution edges for an IntelliId."""
    rows = db.execute(text(
        "SELECT id, intellid, artifact_type, artifact_id, artifact_uuid, "
        "       cosmoid, relation, weight, confidence, notes, state, created "
        "FROM `#__eaiou_intellid_contributions` "
        "WHERE intellid = :intellid ORDER BY created ASC"
    ), {"intellid": intellid}).mappings().all()
    return [dict(r) for r in rows]


# ── Contribution graph ────────────────────────────────────────────────────────

class ContributionError(ValueError):
    """Raised when a contribution references an invalid or tombstoned artifact."""


def validate_cosmoid_for_contribution(cosmoid: str, db: Session) -> None:
    """
    Verify a cosmoid exists and is not in a terminal tombstone state.
    Raises ContributionError if the artifact cannot receive contributions.

    'merged' and 'public_unspace' are terminal — contributions against them
    are rejected. 'private' and 'revivable' are soft-tombstones where
    contributions are still structurally permitted (owner can reactivate).
    """
    if not cosmoid:
        return  # No cosmoid provided — skip validation

    row = db.execute(text(
        "SELECT tombstone_state FROM `#__eaiou_papers` WHERE cosmoid = :cid"
    ), {"cid": cosmoid}).mappings().first()

    if row is None:
        raise ContributionError(f"Artifact cosmoid '{cosmoid}' not found.")

    terminal_states = {"merged", "public_unspace"}
    state = row["tombstone_state"]
    if state in terminal_states:
        raise ContributionError(
            f"Artifact cosmoid '{cosmoid}' is in terminal tombstone state '{state}'. "
            "Contributions are not accepted against tombstoned artifacts."
        )


def record_contribution(
    intellid: str,
    artifact_type: str,
    relation: str,
    db: Session,
    *,
    artifact_id: int = None,
    artifact_uuid: str = None,
    cosmoid: str = None,
    weight: float = None,
    confidence: float = None,
    notes: str = None,
    validate_cosmoid: bool = True,
) -> int:
    """
    Add a contribution edge to the graph.
    Returns the new contribution row id.

    artifact_type: 'paper' | 'version' | 'ai_session' | 'remsearch' |
                   'review' | 'dataset' | 'claim'
    relation:      'generated' | 'edited' | 'validated' | 'rejected' |
                   'reviewed' | 'cited' | 'derived' | 'proposed' | 'refuted'

    validate_cosmoid=True (default): reject contributions against tombstoned artifacts.
    Pass validate_cosmoid=False only for internal system calls (e.g. sealing pipeline).
    """
    if validate_cosmoid and cosmoid:
        validate_cosmoid_for_contribution(cosmoid, db)
    now = datetime.now(timezone.utc)
    db.execute(text(
        "INSERT INTO `#__eaiou_intellid_contributions` "
        "(intellid, artifact_type, artifact_id, artifact_uuid, cosmoid, "
        " relation, weight, confidence, notes, state, created) "
        "VALUES (:intellid, :atype, :aid, :auuid, :cosmoid, "
        "        :relation, :weight, :confidence, :notes, 1, :now)"
    ), {
        "intellid":   intellid,
        "atype":      artifact_type,
        "aid":        artifact_id,
        "auuid":      artifact_uuid,
        "cosmoid":    cosmoid,
        "relation":   relation,
        "weight":     weight,
        "confidence": confidence,
        "notes":      notes,
        "now":        now,
    })
    db.commit()
    return db.execute(text("SELECT LAST_INSERT_ID()")).scalar()


# ── Observation log ───────────────────────────────────────────────────────────

def record_observation(
    observed_cosmoid: str,
    observation_type: str,
    db: Session,
    *,
    observer_intellid: str = None,
    observer_hash: str = None,
    verification_level: str = "anonymous",
    uha_address: str = None,
    uha_cosmoid: str = None,
) -> int:
    """
    Log a UHA observation event.
    observation_type: 'read' | 'cite' | 'fork' | 'contact' | 'validate' | 'replicate'

    verification_level:
      'anonymous' — no bearer token; observer_hash is IP-derived (ephemeral)
      'verified'  — bearer token resolved to a valid api_client
      'system'    — internal system call

    observer_hash: SHA-256 of (IP + user-agent + hourly bucket) for anonymous callers,
                   or SHA-256 of client_uuid for verified callers. Never stores raw PII.
    """
    now = datetime.now(timezone.utc)
    db.execute(text(
        "INSERT INTO `#__eaiou_observation_log` "
        "(observed_cosmoid, observer_intellid, observation_type, "
        " uha_address, uha_cosmoid, observer_hash, verification_level, observation_at) "
        "VALUES (:oc, :oi, :otype, :uha, :uha_cid, :ohash, :vlevel, :now)"
    ), {
        "oc":      observed_cosmoid,
        "oi":      observer_intellid,
        "otype":   observation_type,
        "uha":     uha_address,
        "uha_cid": uha_cosmoid,
        "ohash":   observer_hash,
        "vlevel":  verification_level,
        "now":     now,
    })
    db.commit()
    return db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
