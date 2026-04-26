"""
eaiou — Research Coverage Analysis

For a given paper, extracts key claims and scores each against the gitgap
gap index. Surfaces three tiers:

  COVERED    — claim matches existing literature (similarity ≥ 0.45)
  NOVEL      — claim has no known prior literature (this paper fills the gap)
  NEEDS WORK — claim exists in literature but at low confidence

Appreciated scale: base similarity is amplified by gap age.
  age_amp = 1.0 + min(gap_age_years / 15.0, 0.8)   # caps at 1.8×
  appreciated = base_similarity × age_amp

A 5-year-old unresolved gap matched at 0.60 similarity → appreciated = 0.80.
This means filling an old gap is scored more firmly than filling a new one.
"""

import re
import os
from datetime import datetime
from typing import Optional
import httpx

GITGAP_API = os.getenv("GITGAP_API_URL", "http://127.0.0.1:8001")
CURRENT_YEAR = datetime.now().year

# Discount applied to internal cosine so gitgap always wins when available
_INTERNAL_DISCOUNT = 0.75


def _internal_cosine(claim: str, body: str) -> float:
    """
    TF-IDF cosine similarity between a claim sentence and the paper body.
    Returns 0.0 if body is empty or sklearn unavailable.
    """
    if not body or not claim:
        return 0.0
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        vec = TfidfVectorizer(stop_words="english", min_df=1)
        tfidf = vec.fit_transform([claim, body])
        return float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])
    except Exception:
        return 0.0

# ── Claim extraction patterns ─────────────────────────────────────────────────
# These match assertion-type sentences — statements the paper is making that
# require evidentiary backing. Distinct from gap patterns (absence language).

_ASSERTION_PATTERNS = [
    # Direct result statements
    r"\bwe (show|demonstrate|find|establish|confirm|prove|report|observe|identify|propose)\b",
    r"\bout results (show|suggest|indicate|confirm|demonstrate)\b",
    r"\bthis (paper|study|work|analysis) (shows?|demonstrates?|finds?|establishes?|presents?)\b",
    r"\bour (analysis|method|approach|framework|model) (shows?|confirms?|demonstrates?|reveals?)\b",
    r"\bwe (conclude|argue|claim|hypothesize|posit)\b",
    # Quantitative claims
    r"\b\d+(\.\d+)?\s*%\b",
    r"\bsignificant(ly)?\b",
    r"\bstatistically\b",
    r"\bp\s*[<>=]\s*0\.\d+\b",
    r"\bconfidence interval\b",
    # Comparative claims
    r"\b(better|worse|higher|lower|larger|smaller|greater|fewer) than\b",
    r"\bout(perform|score|pace)\b",
    r"\bsuperior\b",
    r"\bunlike (previous|prior|existing|earlier)\b",
    # Novelty assertions
    r"\bfirst (to|time|study|paper|report|demonstrate)\b",
    r"\bnovel\b",
    r"\bpreviously (unknown|unreported|unrecognized|uncharacterized)\b",
    r"\bno (prior|previous|existing) (work|study|research|literature)\b",
    # Mechanism claims
    r"\bis (caused|driven|explained|mediated|modulated) by\b",
    r"\bdepends on\b",
    r"\bcorrelates? with\b",
    r"\bpredicts?\b",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _ASSERTION_PATTERNS]


def extract_claims(text: str, max_claims: int = 20) -> list[str]:
    """
    Extract assertion-type sentences from paper text.
    Returns up to max_claims distinct claim sentences.
    """
    if not text:
        return []

    # Split into sentences (naive but robust)
    sentences = re.split(r'(?<=[.!?])\s+', text)

    # Score each sentence by how many assertion patterns it matches
    scored = []
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 40 or len(sent) > 400:
            continue
        hits = sum(1 for pat in _COMPILED if pat.search(sent))
        if hits > 0:
            scored.append((hits, sent))

    # Sort by hit count descending, deduplicate similar sentences
    scored.sort(key=lambda x: x[0], reverse=True)

    seen: list[str] = []
    for _, sent in scored:
        # Simple dedup: skip if first 60 chars are similar to an existing claim
        fingerprint = sent[:60].lower()
        if not any(fingerprint == s[:60].lower() for s in seen):
            seen.append(sent)
        if len(seen) >= max_claims:
            break

    return seen


def _appreciated_score(base_similarity: float, pub_year: Optional[int]) -> float:
    """
    Apply the appreciated scale: older unresolved gaps amplify the score.
    age_amp = 1.0 + min(age_years / 15.0, 0.8)  → max 1.8× at 15+ years
    """
    if pub_year and pub_year > 0:
        age_years = max(0, CURRENT_YEAR - pub_year)
        age_amp = 1.0 + min(age_years / 15.0, 0.8)
    else:
        age_amp = 1.0
    return round(min(base_similarity * age_amp, 1.0), 4)


def _classify_coverage(appreciated: float) -> str:
    """
    Three-tier classification from appreciated confidence score.
      COVERED    ≥ 0.55  — strong match in literature, claim well-supported
      NOVEL      < 0.25  — no match found, this paper is filling the gap
      NEEDS WORK 0.25–0.54 — weak support, needs stronger citation framing
    """
    if appreciated >= 0.55:
        return "covered"
    if appreciated < 0.25:
        return "novel"
    return "needs_work"


def analyze_coverage(
    abstract: str,
    sections: list[dict],
    timeout: float = 6.0,
) -> dict:
    """
    Run full coverage analysis for a paper.

    sections: list of {section_name, section_content}
    Returns:
      {
        "claims": [
          {
            "text":             str,
            "status":          "covered" | "novel" | "needs_work",
            "best_match":      gap dict | None,
            "base_similarity": float,
            "appreciated":     float,
            "gap_age_years":   int | None,
          }
        ],
        "summary": {
            "total":      int,
            "covered":    int,
            "novel":      int,
            "needs_work": int,
        },
        "error": str | None,
      }
    """
    # Build full text corpus
    full_text = (abstract or "") + "\n\n"
    for s in sections:
        full_text += (s.get("section_content") or "") + "\n\n"

    claims = extract_claims(full_text)

    if not claims:
        return {
            "claims": [],
            "summary": {"total": 0, "covered": 0, "novel": 0, "needs_work": 0},
            "error": None,
        }

    # Build body corpus once for internal cosine fallback
    body_text = full_text  # already built above

    results = []
    try:
        with httpx.Client(timeout=timeout) as client:
            for claim in claims:
                try:
                    resp = client.get(
                        f"{GITGAP_API}/gaps/search",
                        params={"q": claim, "limit": 3, "min_score": 0.15},
                    )
                    if resp.status_code != 200:
                        best = None
                        base_sim = 0.0
                    else:
                        data = resp.json()
                        gaps = data.get("gaps", [])
                        best = gaps[0] if gaps else None
                        base_sim = best["similarity"] if best else 0.0
                except Exception:
                    best = None
                    base_sim = 0.0

                pub_year = best.get("pub_year") if best else None
                appreciated = _appreciated_score(base_sim, pub_year)
                gap_age = (CURRENT_YEAR - pub_year) if pub_year else None

                # Internal cosine fallback: when gitgap has no match, score
                # against the paper's own body text (discounted so gitgap wins)
                internal = 0.0
                coverage_source = "gitgap"
                if base_sim == 0.0:
                    internal = _internal_cosine(claim, body_text)
                    internal_boosted = round(internal * _INTERNAL_DISCOUNT, 4)
                    if internal_boosted > appreciated:
                        appreciated = internal_boosted
                        coverage_source = "internal"

                results.append({
                    "text":             claim,
                    "status":           _classify_coverage(appreciated),
                    "best_match":       {
                        "id":            best["id"],
                        "gateway_term":  best["gateway_term"],
                        "declaration":   (best["declaration_text"] or "")[:160],
                        "pub_year":      best["pub_year"],
                        "pmcid":         best["pmcid"],
                    } if best else None,
                    "base_similarity":  base_sim,
                    "appreciated":      appreciated,
                    "gap_age_years":    gap_age,
                    "internal_cosine":  round(internal, 4),
                    "coverage_source":  coverage_source,
                })

    except Exception as e:
        return {
            "claims": [],
            "summary": {"total": 0, "covered": 0, "novel": 0, "needs_work": 0},
            "error": str(e),
        }

    summary = {"total": len(results), "covered": 0, "novel": 0, "needs_work": 0}
    for r in results:
        summary[r["status"]] += 1

    return {
        "claims":  results,
        "summary": summary,
        "error":   None,
    }
