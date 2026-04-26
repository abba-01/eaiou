"""
eaiou — Integrity Service
Trajectory-based manuscript validation engine.

Based on the Basin Theory integrity spec:
- Each gate pass = a trajectory step (snapshot of manuscript state)
- Divergence between snapshots = measure of how much the paper changed
- Gate validity decays if the manuscript diverges from the state it was in
  when that gate condition passed
- Drift / Branch / Rewrite classification from divergence score

Stack: MariaDB (no pgvector).
Phase 1: word-frequency bag-of-words vectors (legacy — read-only for old snapshots).
Phase 2: character n-gram + HashingVectorizer dense embeddings (current).
Phase 3 upgrade path: swap embed_sections() in embeddings.py with a neural model.
"""

import hashlib
import json
import re
from collections import Counter
from math import sqrt


# ── Canonicalization ──────────────────────────────────────────────────────────

def canonical_sections(sections: list) -> str:
    """Stable string from sections list — deterministic for hashing."""
    parts = []
    for s in sorted(sections, key=lambda x: x.get("section_order", 0)):
        content = (s.get("section_content") or "").strip()
        name = s.get("section_name", "")
        parts.append(f"{name}::{content}")
    return "\n---\n".join(parts)


def hash_content(sections: list) -> str:
    """SHA-256 of canonical section content."""
    return hashlib.sha256(
        canonical_sections(sections).encode("utf-8")
    ).hexdigest()


# ── Vectorization (Phase 1: word frequency) ───────────────────────────────────

_STOP = {
    "the", "and", "for", "with", "that", "this", "from", "have", "been",
    "which", "will", "more", "also", "than", "when", "were", "they", "their",
    "into", "where", "there", "about", "these", "other", "some", "such",
    "what", "used", "both", "each", "very", "then", "thus", "after",
}


def vectorize(sections: list) -> dict:
    """
    Word-frequency vector from all section content.
    Returns dict[word → count], top 100 significant words.
    Stored as JSON in MariaDB; used for divergence computation.
    """
    raw = " ".join(
        (s.get("section_content") or "") for s in sections
    ).lower()
    tokens = re.findall(r"[a-z]{4,}", raw)
    significant = [t for t in tokens if t not in _STOP]
    return dict(Counter(significant).most_common(100))


def vectorize_text(text: str) -> dict:
    """Same as vectorize() but takes a plain string — for leakage / contamination."""
    tokens = re.findall(r"[a-z]{4,}", (text or "").lower())
    significant = [t for t in tokens if t not in _STOP]
    return dict(Counter(significant).most_common(100))


def similarity_score(v1: dict, v2: dict) -> float:
    """Cosine similarity in [0,1]. Inverse of _cosine_distance."""
    return round(1.0 - _cosine_distance(v1, v2), 4)


# ── Divergence ────────────────────────────────────────────────────────────────

def _cosine_distance(v1: dict, v2: dict) -> float:
    """Cosine distance between two word-frequency dicts. Range: 0.0–1.0."""
    all_keys = set(v1) | set(v2)
    if not all_keys:
        return 0.0
    dot = sum(v1.get(k, 0) * v2.get(k, 0) for k in all_keys)
    mag1 = sqrt(sum(v * v for v in v1.values())) or 1.0
    mag2 = sqrt(sum(v * v for v in v2.values())) or 1.0
    return round(1.0 - dot / (mag1 * mag2), 4)


def divergence_score(snapshot_vector_json: str, current_sections: list) -> float:
    """
    Divergence between a stored snapshot (JSON string from DB) and current sections.
    0.0 = identical, 1.0 = completely different.

    Handles both Phase 1 (word-count dict) and Phase 2+ (dense float array) vectors.
    """
    from .embeddings import divergence_from_stored  # local import — avoids circular at load
    current_text = " ".join(
        (s.get("section_content") or "") for s in current_sections
    )
    return divergence_from_stored(snapshot_vector_json, current_text)


# ── Classification ────────────────────────────────────────────────────────────

# Thresholds — tunable. Start conservative for Phase 1.
DRIFT_THRESHOLD = 0.10      # ≤ 10% divergence: refinement along same trajectory
BRANCH_THRESHOLD = 0.30     # ≤ 30%: new trajectory introduced (document it, don't block)
# > 30%: rewrite — gate evidence no longer corresponds to this manuscript

GATE_WARN_THRESHOLD = 0.15   # gate evidence is drifting
GATE_INVALID_THRESHOLD = 0.35  # gate evidence does not correspond to current state


def classify_divergence(delta: float) -> str:
    """Drift / Branch / Rewrite from divergence score."""
    if delta <= DRIFT_THRESHOLD:
        return "DRIFT"
    elif delta <= BRANCH_THRESHOLD:
        return "BRANCH"
    return "REWRITE"


def gate_validity_label(delta: float) -> str:
    """intact / drifted / invalidated from divergence vs. gate snapshot."""
    if delta <= GATE_WARN_THRESHOLD:
        return "intact"
    elif delta <= GATE_INVALID_THRESHOLD:
        return "drifted"
    return "invalidated"


# ── Snapshot helpers ──────────────────────────────────────────────────────────

# ── Manuscript Basin Score (MBS) ─────────────────────────────────────────────

def compute_mbs(
    checks: list,
    leakage_count: int,
    contamination_score: float,
    snapshot_count: int,
    max_divergence: float,
) -> float:
    """
    Manuscript Basin Score — composite trajectory integrity metric.
    Range: 0.0–1.0. Higher = more trustworthy provenance chain.

    Weights (tunable):
      0.25  audit_completeness  — snapshots captured / gates passed
      0.25  gate_validity       — intact=1.0, drifted=0.5, invalidated=0.0
      0.20  leakage score       — penalized at 0.20 per hit, capped at 5
      0.15  contamination       — inverted: low overlap = high score
      0.15  trajectory stability — 1 - max divergence across snapshots

    Classification:
      ≥ 0.90  BASIN   — strong, well-documented trajectory
      ≥ 0.75  SOLID   — adequate; minor drift or flags
      ≥ 0.60  WARN    — significant drift or contamination
      < 0.60  FRAGILE — trajectory collapse or heavy leakage
    """
    passed = [c for c in checks if c.get("passed")]
    n_passed = len(passed) or 1

    # Audit completeness
    audit = min(1.0, snapshot_count / n_passed)

    # Gate validity
    vmap = {"intact": 1.0, "drifted": 0.5, "invalidated": 0.0}
    gscores = [vmap.get(c.get("validity", "intact"), 1.0) for c in passed]
    gate_val = sum(gscores) / len(gscores) if gscores else 1.0

    # Leakage (capped at 5 hits = full penalty)
    leak_penalty = min(1.0, leakage_count / 5.0)

    # Contamination (already [0,1])
    cont_penalty = min(1.0, max(0.0, contamination_score))

    # Trajectory stability
    stability = max(0.0, 1.0 - min(1.0, max_divergence))

    mbs = (
        0.25 * audit
        + 0.25 * gate_val
        + 0.20 * (1.0 - leak_penalty)
        + 0.15 * (1.0 - cont_penalty)
        + 0.15 * stability
    )
    return round(mbs, 4)


def mbs_label(mbs: float) -> str:
    """Human-readable MBS classification."""
    if mbs >= 0.90:
        return "BASIN"
    elif mbs >= 0.75:
        return "SOLID"
    elif mbs >= 0.60:
        return "WARN"
    return "FRAGILE"


# ── Snapshot helpers ──────────────────────────────────────────────────────────

def build_snapshot_record(paper_id: int, gate_code: str, sections: list,
                          prior_vector_json: str = None) -> dict:
    """
    Build a snapshot dict ready to INSERT into #__eaiou_paper_snapshots.
    If prior_vector_json is provided, computes divergence from it.

    Phase 2: content_vector is a dense 512-dim float array (JSON array).
    Legacy snapshots store a word-count dict (JSON object) — divergence_score handles both.
    """
    from .embeddings import embed_sections, divergence_from_stored
    vec = embed_sections(sections)
    h = hash_content(sections)

    delta = None
    change_class = None
    if prior_vector_json:
        current_text = " ".join((s.get("section_content") or "") for s in sections)
        delta = divergence_from_stored(prior_vector_json, current_text)
        change_class = classify_divergence(delta)

    return {
        "paper_id": paper_id,
        "gate_code": gate_code,
        "content_hash": h,
        "word_vector_json": json.dumps(vec),   # column kept; now stores dense float list
        "section_json": json.dumps([
            {"section_name": s.get("section_name", ""),
             "section_content": s.get("section_content") or "",
             "section_order": s.get("section_order", 0)}
            for s in sections
        ]),
        "section_count": len(sections),
        "divergence_from_prior": delta,
        "change_class": change_class,
    }
