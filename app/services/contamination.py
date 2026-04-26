"""
eaiou — Contamination Scoring Service

Measures content overlap between human-authored sections and
intelligence module responses.

Basin Theory framing: contamination = shared steps between trajectories.
In eaiou terms: intelligence module output appearing directly in manuscript
sections = the module's trajectory crossed into the human's trajectory early.

This is NOT a fraud signal on its own — authors legitimately improve their
writing based on module feedback (covered by CAN items). The contamination
score is a provenance data point: high score means the intelligence had a
heavy hand in the text itself, not just in the ideas.

Score range: 0.0 (no overlap) → 1.0 (near-identical text).
"""

from __future__ import annotations

import json
from sqlalchemy.orm import Session
from sqlalchemy import text

from .integrity import vectorize_text, similarity_score


def contamination_score(paper_id: int, db: Session) -> dict:
    """
    Compare all human-authored section content against all module response text.

    Returns max similarity + per-comparison breakdown.
    """
    # Current sections (human trajectory)
    sections = db.execute(text(
        "SELECT section_name, section_content FROM `#__eaiou_paper_sections` "
        "WHERE paper_id = :pid AND section_content IS NOT NULL "
        "ORDER BY section_order ASC"
    ), {"pid": paper_id}).mappings().all()

    # All module responses (intelligence trajectories)
    module_events = db.execute(text(
        "SELECT id, event_type, response_text FROM `#__eaiou_module_events` "
        "WHERE paper_id = :pid AND response_text IS NOT NULL"
    ), {"pid": paper_id}).mappings().all()

    if not sections or not module_events:
        return {
            "paper_id": paper_id,
            "contamination_score": 0.0,
            "comparisons": [],
            "note": "Insufficient data — no sections or no module responses.",
        }

    comparisons = []

    for sec in sections:
        s_text = sec["section_content"] or ""
        if len(s_text.strip()) < 50:
            continue
        sv = vectorize_text(s_text)

        for evt in module_events:
            r_text = evt["response_text"] or ""
            if len(r_text.strip()) < 50:
                continue
            rv = vectorize_text(r_text)
            sim = similarity_score(sv, rv)

            if sim > 0.2:  # only record meaningful overlaps
                comparisons.append({
                    "section_name": sec["section_name"],
                    "module_event_id": evt["id"],
                    "event_type": evt["event_type"],
                    "similarity": sim,
                })

    overall = max((c["similarity"] for c in comparisons), default=0.0)
    # Sort by similarity desc for reporting
    comparisons.sort(key=lambda x: -x["similarity"])

    return {
        "paper_id": paper_id,
        "contamination_score": round(overall, 4),
        "comparisons": comparisons[:20],  # top 20
    }
