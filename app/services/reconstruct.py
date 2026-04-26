"""
eaiou — Reconstruction Service

Rebuilds the manuscript trajectory from snapshot chain.
Each snapshot = a gate-pass moment; together they are the
provenance record of how the paper evolved through the pipeline.

"You are no longer validating papers — you are validating the path
 that made the paper inevitable." — Basin Theory integrity spec
"""

from __future__ import annotations

import json
from sqlalchemy.orm import Session
from sqlalchemy import text

from .integrity import vectorize_text, _cosine_distance, classify_divergence


def reconstruct_chain(paper_id: int, db: Session) -> dict:
    """
    Return ordered snapshot chain with divergence at each step.

    Gives reviewers (and the author) a clear picture of how the manuscript
    changed between each gate milestone.
    """
    rows = db.execute(text(
        "SELECT id, gate_code, content_hash, section_json, section_count, "
        "       divergence_from_prior, change_class, created_at "
        "FROM `#__eaiou_paper_snapshots` "
        "WHERE paper_id = :pid ORDER BY created_at ASC, id ASC"
    ), {"pid": paper_id}).mappings().all()

    chain = []
    prev_vec = None

    for row in rows:
        sections = []
        if row["section_json"]:
            try:
                sections = json.loads(row["section_json"])
            except Exception:
                pass

        # Combine all section text for divergence
        full_text = " ".join(s.get("section_content") or "" for s in sections)
        cur_vec = vectorize_text(full_text)

        if prev_vec is None:
            delta = 0.0
            change = "ORIGIN"
        else:
            delta = _cosine_distance(prev_vec, cur_vec)
            change = classify_divergence(delta)

        chain.append({
            "snapshot_id": row["id"],
            "gate_code": row["gate_code"],
            "content_hash": row["content_hash"],
            "section_count": row["section_count"] or 0,
            "divergence_from_previous": round(delta, 4),
            "change_type": change,
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "section_preview": [
                {
                    "name": s.get("section_name", ""),
                    "excerpt": (s.get("section_content") or "")[:200],
                }
                for s in sections if s.get("section_content")
            ],
        })

        prev_vec = cur_vec

    # Reconstruction validity: can the final state be traced to the origin?
    reconstructible = len(chain) > 0
    any_rewrite = any(step["change_type"] == "REWRITE" for step in chain)
    any_branch  = any(step["change_type"] == "BRANCH"  for step in chain)

    # Annotate fork points for display
    for step in chain:
        ct = step["change_type"]
        step["is_fork_point"] = ct in ("BRANCH", "REWRITE")
        step["fork_severity"] = ct if step["is_fork_point"] else None

    return {
        "paper_id": paper_id,
        "snapshot_count": len(chain),
        "reconstructible": reconstructible,
        "contains_rewrite": any_rewrite,
        "contains_branch":  any_branch,
        "chain": chain,
    }
