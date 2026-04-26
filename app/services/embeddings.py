"""
eaiou — Embedding Service  (Phase 2: TF-IDF / character n-gram + HashingVectorizer)

Replaces the word-frequency bag-of-words used in Phase 1.

Backend: sklearn HashingVectorizer with character n-grams (3–5 chars).
  • Fixed dimension (512) — no corpus fitting required.
  • Deterministic — same text always produces the same vector.
  • Morphology-aware — captures word stems, prefixes, and compound forms.
  • No stopword lists needed — character level naturally down-weights function words.

Storage format: JSON array of 512 floats (L2-normalised).
Legacy detection: if stored JSON is an object (dict), it's the old word-count format.

Phase 3 upgrade path: replace _hashing_vectorizer() + embed_text() with a
sentence-transformer or API call. The divergence_score() interface is unchanged.
"""

import json
import math
from typing import Union

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.preprocessing import normalize

# ── Vectorizer configuration ──────────────────────────────────────────────────

_N_FEATURES = 512
_NGRAM_RANGE = (3, 5)  # character 3-grams through 5-grams

_vectorizer = HashingVectorizer(
    analyzer="char_wb",          # character n-grams with word boundaries
    ngram_range=_NGRAM_RANGE,
    n_features=_N_FEATURES,
    norm="l2",                   # L2-normalise; cosine sim = dot product
    alternate_sign=False,        # all non-negative (cleaner for visual inspection)
    dtype=np.float32,
)


# ── Encoding ──────────────────────────────────────────────────────────────────

def embed_text(text: str) -> list[float]:
    """
    Encode a plain text string to a dense 512-dim L2-normalised vector.
    Returns a Python list of floats (JSON-serialisable).
    """
    if not text or not text.strip():
        return [0.0] * _N_FEATURES
    sparse = _vectorizer.transform([text])          # (1, 512) sparse
    dense  = sparse.toarray()[0]                    # (512,) dense float32
    # Already L2-normalised by HashingVectorizer (norm='l2')
    return dense.tolist()


def embed_sections(sections: list) -> list[float]:
    """
    Concatenate all section content and embed as a single vector.
    Mirrors the behaviour of the old vectorize(sections) → embed_text interface.
    """
    text = " ".join((s.get("section_content") or "") for s in sections)
    return embed_text(text)


# ── Similarity / distance ─────────────────────────────────────────────────────

def cosine_distance_dense(v1: list[float], v2: list[float]) -> float:
    """
    Cosine distance between two L2-normalised dense vectors.
    Because both are L2-normalised, cosine_sim = dot product.
    Returns a value in [0.0, 1.0].

    Zero vectors (empty content) are treated as identical — distance 0.0.
    """
    if len(v1) != len(v2):
        raise ValueError(f"Vector dimension mismatch: {len(v1)} vs {len(v2)}")
    mag1 = math.sqrt(sum(x * x for x in v1))
    mag2 = math.sqrt(sum(x * x for x in v2))
    # Both empty — identical content
    if mag1 == 0.0 and mag2 == 0.0:
        return 0.0
    # One empty, one not — maximally different
    if mag1 == 0.0 or mag2 == 0.0:
        return 1.0
    dot = sum(a * b for a, b in zip(v1, v2))
    # Clamp to [0,1] to handle float precision edge cases
    return round(max(0.0, min(1.0, 1.0 - dot / (mag1 * mag2))), 4)


# ── Legacy compat ─────────────────────────────────────────────────────────────

def _cosine_distance_sparse(v1: dict, v2: dict) -> float:
    """
    Word-frequency cosine distance (Phase 1 fallback).
    Used when comparing against snapshots stored in the old dict format.
    """
    all_keys = set(v1) | set(v2)
    if not all_keys:
        return 0.0
    dot  = sum(v1.get(k, 0) * v2.get(k, 0) for k in all_keys)
    mag1 = math.sqrt(sum(v * v for v in v1.values())) or 1.0
    mag2 = math.sqrt(sum(v * v for v in v2.values())) or 1.0
    return round(1.0 - dot / (mag1 * mag2), 4)


# ── Unified divergence entry point ────────────────────────────────────────────

def divergence_from_stored(
    stored_vector_json: str,
    current_text: str,
) -> float:
    """
    Compute divergence between a stored snapshot vector and current content.

    Handles both vector formats transparently:
      • JSON object  → Phase 1 word-count dict  → legacy cosine distance
      • JSON array   → Phase 2 dense embedding  → dense cosine distance

    Returns 0.0–1.0.  Higher = more diverged.
    """
    if not stored_vector_json:
        return 0.0
    stored = json.loads(stored_vector_json)

    if isinstance(stored, dict):
        # Legacy path: word-count vector from Phase 1 snapshots
        from .integrity import vectorize_text  # avoid circular at module level
        current_vec = vectorize_text(current_text)
        return _cosine_distance_sparse(stored, current_vec)

    # Phase 2+: dense float list
    current_vec = embed_text(current_text)
    return cosine_distance_dense(stored, current_vec)
