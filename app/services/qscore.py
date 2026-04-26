"""
eaiou — Q Score Service

Q score = quality signal derived from hard provenance evidence.
It is NOT an imprimatur — it does not certify the paper's claims.
It measures the quality of the trajectory that produced the paper.

Two columns on #__eaiou_papers:
  q_signal  — computed automatically at seal; reflects evidence
  q_overall — editor decision; defaults to q_signal; can be overridden

Scale: 0.0–10.0

Dimensions and weights (tunable):
  0.40  basin_integrity    — MBS from integrity seal
  0.25  investigation      — interrogation depth + volley rigor
  0.20  completeness       — sections written at seal time
  0.15  gap_coverage       — gap anchor present + gap age signal

Classification:
  ≥ 8.0  STRONG  — well-documented, rigorous, gap-anchored
  ≥ 6.0  GOOD    — solid provenance, minor gaps
  ≥ 4.0  FAIR    — some gaps in process or completeness
  < 4.0  WEAK    — insufficient process record
"""

from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import text


# ── Weights ───────────────────────────────────────────────────────────────────

W_INTEGRITY    = 0.40
W_INVESTIGATION = 0.25
W_COMPLETENESS  = 0.20
W_GAP_COVERAGE  = 0.15


# ── Sub-score computations ────────────────────────────────────────────────────

def _integrity_score(paper_id: int, db: Session) -> float:
    """
    0–10 from Manuscript Basin Score.
    Uses the latest integrity seal for this paper.
    """
    row = db.execute(text(
        "SELECT mbs FROM `#__eaiou_integrity_seals` "
        "WHERE paper_id = :pid ORDER BY sealed_at DESC LIMIT 1"
    ), {"pid": paper_id}).fetchone()

    if row is None or row[0] is None:
        return 0.0

    mbs = float(row[0])
    if mbs >= 0.90:
        return 10.0
    elif mbs >= 0.75:
        return 7.5 + (mbs - 0.75) / (0.90 - 0.75) * 2.5   # linear interpolation 7.5→10
    elif mbs >= 0.60:
        return 5.0 + (mbs - 0.60) / (0.75 - 0.60) * 2.5
    else:
        return max(0.0, mbs / 0.60 * 5.0)


def _investigation_score(paper_id: int, db: Session) -> float:
    """
    0–10 from interrogation exchanges + volley rounds.
    Measures how rigorously the author engaged with the investigation process.
    """
    interrogation_count = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_interrogation_log` WHERE paper_id = :pid"
    ), {"pid": paper_id}).scalar() or 0

    volley_rounds = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_volley_log` WHERE paper_id = :pid"
    ), {"pid": paper_id}).scalar() or 0

    # Interrogation: 0=0, 1=3, 2=5, 3=7, 5+=10
    if interrogation_count >= 5:
        i_score = 10.0
    elif interrogation_count >= 3:
        i_score = 7.0
    elif interrogation_count >= 2:
        i_score = 5.0
    elif interrogation_count >= 1:
        i_score = 3.0
    else:
        i_score = 0.0

    # Volley: 0=0, 1=5, 2=8, 3+=10
    if volley_rounds >= 3:
        v_score = 10.0
    elif volley_rounds >= 2:
        v_score = 8.0
    elif volley_rounds >= 1:
        v_score = 5.0
    else:
        v_score = 0.0

    return round((i_score + v_score) / 2.0, 4)


def _completeness_score(paper_id: int, db: Session) -> float:
    """
    0–10 from ratio of sections with written content at seal time.
    Uses current section state (sections may have been filled after sealing).
    """
    rows = db.execute(text(
        "SELECT section_content, section_notes "
        "FROM `#__eaiou_paper_sections` WHERE paper_id = :pid"
    ), {"pid": paper_id}).fetchall()

    if not rows:
        return 0.0

    written = sum(
        1 for r in rows
        if (r[0] or "").strip() or (r[1] or "").strip()
    )
    ratio = written / len(rows)

    if ratio >= 1.0:
        return 10.0
    elif ratio >= 0.80:
        return 7.5
    elif ratio >= 0.60:
        return 5.0
    elif ratio >= 0.40:
        return 3.0
    else:
        return max(0.0, ratio * 7.5)


def _gap_coverage_score(paper_id: int, db: Session) -> float:
    """
    0–10 from gap anchor presence.
    A gap-anchored paper responds to a documented unresolved research question.
    Papers without a gap anchor are still valid but score at the baseline (5.0).
    """
    row = db.execute(text(
        "SELECT gitgap_gap_id FROM `#__eaiou_papers` WHERE id = :pid"
    ), {"pid": paper_id}).fetchone()

    if row is None:
        return 0.0

    if row[0] is not None:
        return 10.0

    # No gap anchor — baseline: the work may be valid but is not explicitly
    # gap-anchored in the gitgap record. Half credit.
    return 5.0


# ── Composite ─────────────────────────────────────────────────────────────────

def compute_q_signal(paper_id: int, db: Session) -> dict:
    """
    Compute the Q signal for a paper from all available evidence.

    Returns a dict suitable for storing and displaying:
      q_signal: float 0–10
      q_label:  STRONG / GOOD / FAIR / WEAK
      breakdown: sub-scores by dimension
    """
    integrity    = _integrity_score(paper_id, db)
    investigation = _investigation_score(paper_id, db)
    completeness = _completeness_score(paper_id, db)
    gap_coverage = _gap_coverage_score(paper_id, db)

    q = round(
        W_INTEGRITY    * integrity
        + W_INVESTIGATION * investigation
        + W_COMPLETENESS  * completeness
        + W_GAP_COVERAGE  * gap_coverage,
        4,
    )

    return {
        "q_signal": q,
        "q_label":  q_label(q),
        "breakdown": {
            "integrity":     round(integrity, 4),
            "investigation": round(investigation, 4),
            "completeness":  round(completeness, 4),
            "gap_coverage":  round(gap_coverage, 4),
        },
        "weights": {
            "integrity":     W_INTEGRITY,
            "investigation": W_INVESTIGATION,
            "completeness":  W_COMPLETENESS,
            "gap_coverage":  W_GAP_COVERAGE,
        },
    }


def q_label(q: float) -> str:
    if q >= 8.0:
        return "STRONG"
    elif q >= 6.0:
        return "GOOD"
    elif q >= 4.0:
        return "FAIR"
    return "WEAK"


def persist_q_signal(paper_id: int, db: Session) -> dict:
    """
    Compute and persist q_signal to the papers table.
    Sets q_overall = q_signal only if q_overall is currently NULL
    (preserves manual editor overrides).
    Returns the computed result dict.
    """
    result = compute_q_signal(paper_id, db)
    q = result["q_signal"]

    db.execute(text(
        "UPDATE `#__eaiou_papers` "
        "SET q_signal = :q, "
        "    q_overall = COALESCE(q_overall, :q) "
        "WHERE id = :pid"
    ), {"q": q, "pid": paper_id})
    db.commit()

    return result
