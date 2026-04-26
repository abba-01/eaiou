"""
eaiou — Leakage Detection Service

Detects answer leakage: intelligence module response text appearing in
manuscript sections at or before the snapshot where that module ran.

This is a WARN signal, not a hard block. High similarity may mean:
- Author legitimately incorporated feedback (allowed — that's what CAN items cover)
- Author copied verbatim without responding (provenance concern)
- Module accurately described existing content (coincidence)

Reviewers see the leakage flags. Human sign-off required to resolve.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session
from sqlalchemy import text

from .integrity import vectorize_text, similarity_score

LEAKAGE_THRESHOLD = 0.72   # ≥ 72% similarity = flag


@dataclass
class LeakageHit:
    section_name: str
    snapshot_id: int | None
    module_event_id: int | None
    similarity_score: float
    reason: str

    def to_dict(self):
        return asdict(self)


def detect_leakage(paper_id: int, db: Session) -> list[LeakageHit]:
    """
    Compare each snapshot's sections against module responses that existed
    at or before that snapshot.

    Returns list of LeakageHit where similarity >= LEAKAGE_THRESHOLD.
    """
    snapshots = db.execute(text(
        "SELECT id, gate_code, section_json, created_at "
        "FROM `#__eaiou_paper_snapshots` "
        "WHERE paper_id = :pid ORDER BY created_at ASC"
    ), {"pid": paper_id}).mappings().all()

    module_events = db.execute(text(
        "SELECT id, event_type, response_text, occurred_at "
        "FROM `#__eaiou_module_events` "
        "WHERE paper_id = :pid AND response_text IS NOT NULL "
        "ORDER BY occurred_at ASC"
    ), {"pid": paper_id}).mappings().all()

    hits: list[LeakageHit] = []

    for snap in snapshots:
        if not snap["section_json"]:
            continue
        try:
            sections = json.loads(snap["section_json"])
        except Exception:
            continue

        snap_time = snap["created_at"]
        # Module events at or before this snapshot
        prior_events = [e for e in module_events if e["occurred_at"] <= snap_time]

        for section in sections:
            s_name = section.get("section_name", "")
            s_content = section.get("section_content") or ""
            if len(s_content.strip()) < 50:
                continue  # too short to be meaningful
            sv = vectorize_text(s_content)

            for evt in prior_events:
                r_text = evt["response_text"] or ""
                if len(r_text.strip()) < 50:
                    continue
                rv = vectorize_text(r_text)
                sim = similarity_score(sv, rv)

                if sim >= LEAKAGE_THRESHOLD:
                    hits.append(LeakageHit(
                        section_name=s_name,
                        snapshot_id=snap["id"],
                        module_event_id=evt["id"],
                        similarity_score=sim,
                        reason=(
                            f"Section '{s_name}' is {sim:.0%} similar to "
                            f"{evt['event_type']} module response recorded "
                            f"before this snapshot. Review for unsupported "
                            f"claim injection."
                        ),
                    ))

    return hits


def persist_leakage(paper_id: int, hits: list[LeakageHit], db: Session) -> int:
    """Write leakage flags to DB. Returns count written."""
    count = 0
    for hit in hits:
        db.execute(text(
            "INSERT INTO `#__eaiou_leakage_flags` "
            "(paper_id, snapshot_id, section_name, module_event_id, "
            "similarity_score, status, reason) "
            "VALUES (:pid, :snap_id, :sec, :evt_id, :score, 'WARN', :reason)"
        ), {
            "pid": paper_id,
            "snap_id": hit.snapshot_id,
            "sec": hit.section_name,
            "evt_id": hit.module_event_id,
            "score": hit.similarity_score,
            "reason": hit.reason,
        })
        count += 1
    return count
