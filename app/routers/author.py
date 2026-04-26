"""
eaiou — Author router
Authenticated authoring workspace: dashboard, submission form.
Phase 1: single-admin model. All papers visible to the logged-in user.
"""

import asyncio
import fcntl
import json
import os
import pty
import re
import struct
import termios
import uuid
from datetime import datetime, timezone

from ..services.integrity import (
    build_snapshot_record, divergence_score,
    gate_validity_label, classify_divergence,
    vectorize_text, similarity_score,
    compute_mbs, mbs_label,
)
from ..services.leakage import detect_leakage, persist_leakage
from ..services.contamination import contamination_score as compute_contamination
from ..services.reconstruct import reconstruct_chain
from ..services.qscore import persist_q_signal
from ..services.trajectory import detect_and_record_forks, get_trajectory_tree
from ..services.embeddings import embed_text, cosine_distance_dense

import httpx
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..deps import get_current_user
from ..security import get_csrf_token, validate_csrf

GITGAP_API = os.getenv("GITGAP_API_URL", "http://127.0.0.1:8001")
EAIOU_MASTER_API_KEY = os.getenv("EAIOU_MASTER_API_KEY", "")

router = APIRouter(prefix="/author", tags=["author"])
templates = Jinja2Templates(directory="app/templates")


def _gateway_term_from_claim(claim: str) -> str:
    """Derive a short, topic-focused gateway term from an assertion sentence."""
    clean = re.sub(
        r'^\s*((we|our|this\s+\w+)\s+\w+(?:\s+\w+)?\s+(that\s+)?)',
        '', claim, flags=re.IGNORECASE,
    ).strip()
    _STOP = frozenset({
        'the', 'a', 'an', 'of', 'in', 'is', 'are', 'was', 'were',
        'that', 'this', 'with', 'for', 'and', 'or', 'but', 'by', 'to',
    })
    words = [w for w in re.findall(r'\b[a-zA-Z][a-zA-Z]{2,}\b', clean)
             if w.lower() not in _STOP]
    return ' '.join(words[:5]) or clean[:50]


def _require_login(request: Request, current_user):
    """Redirect to login if not authenticated."""
    if not current_user:
        return RedirectResponse(url=f"/auth/login?next={request.url.path}", status_code=302)
    return None


# ── Submission Gateway ────────────────────────────────────────────────────────
# Every condition must pass before seal is allowed.
# Pattern: named checks, explicit pass/fail, blocked until all green.

import re as _re

def _check_gateway(paper_id: int, paper: dict, sections: list,
                   db: Session) -> list:
    """
    Returns a list of gate condition dicts:
      { "code", "label", "passed": bool, "detail": str }
    Seal is blocked if any passed == False.
    """
    checks = []

    # 1. Interrogation — investigation must have happened
    interrogation_count = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_interrogation_log` WHERE paper_id = :pid"
    ), {"pid": paper_id}).scalar() or 0
    checks.append({
        "code":   "INTERROGATION",
        "label":  "Investigation interrogation",
        "passed": interrogation_count >= 1,
        "detail": f"{interrogation_count} exchange{'s' if interrogation_count != 1 else ''} — minimum 1 required",
    })

    # 2. Volley — cross-intelligence audit must have run
    volley_count = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_volley_log` WHERE paper_id = :pid"
    ), {"pid": paper_id}).scalar() or 0
    checks.append({
        "code":   "VOLLEY_RAN",
        "label":  "Cross-intelligence audit",
        "passed": volley_count >= 1,
        "detail": f"{volley_count} audit round{'s' if volley_count != 1 else ''} — minimum 1 required",
    })

    # 3. Volley resolution — no unresponded findings
    unresponded = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_volley_log` "
        "WHERE paper_id = :pid AND is_clean = 0 AND author_response IS NULL"
    ), {"pid": paper_id}).scalar() or 0
    checks.append({
        "code":   "VOLLEY_RESOLVED",
        "label":  "Audit findings addressed",
        "passed": unresponded == 0,
        "detail": f"{unresponded} unresponded finding round{'s' if unresponded != 1 else ''}" if unresponded else "All rounds responded to or clean",
    })

    # 4. Sections populated — paper must have written content beyond abstract
    written_sections = sum(
        1 for s in sections
        if (s.get("section_content") or "").strip() or (s.get("section_notes") or "").strip()
    )
    undefined_sections = [s["section_name"] for s in sections
                          if not (s.get("section_content") or "").strip()
                          and not (s.get("section_notes") or "").strip()]
    checks.append({
        "code":   "SECTIONS_POPULATED",
        "label":  "Sections with content",
        "passed": written_sections >= 1,
        "detail": (f"{written_sections} written — undefined: {', '.join(undefined_sections[:3])}"
                   if undefined_sections else f"{written_sections} section{'s' if written_sections != 1 else ''} written"),
    })

    # 5. Citations present — abstract or sections must contain citation markers
    all_text = (paper.get("abstract") or "") + " ".join(
        (s.get("section_content") or "") + (s.get("section_notes") or "")
        for s in sections
    )
    citation_pattern = _re.compile(
        r'\[\d+\]'                      # [1], [23]
        r'|\([A-Z][a-z]+[\s,]+\d{4}\)' # (Smith, 2020) / (Smith 2020)
        r'|\bet al\b'                   # et al.
        r'|\bdoi:\s*10\.'               # doi:10.xxxx
    )
    has_citations = bool(citation_pattern.search(all_text))
    checks.append({
        "code":   "CITATIONS_PRESENT",
        "label":  "Sources cited",
        "passed": has_citations,
        "detail": "Citation markers found" if has_citations else "No citation markers detected — sources must be cited",
    })

    # 6. Bibliography section present
    section_names_lower = [s["section_name"].lower() for s in sections]
    has_bib = any(
        kw in name for name in section_names_lower
        for kw in ("reference", "bibliograph", "works cited", "literature")
    )
    checks.append({
        "code":   "BIBLIOGRAPHY",
        "label":  "Bibliography / References section",
        "passed": has_bib,
        "detail": "References section found" if has_bib else "No References or Bibliography section — required",
    })

    # 7. Abstract non-trivial — at least 80 words
    abstract_words = len((paper.get("abstract") or "").split())
    checks.append({
        "code":   "ABSTRACT_DEPTH",
        "label":  "Abstract depth",
        "passed": abstract_words >= 80,
        "detail": f"{abstract_words} words — minimum 80 required",
    })

    # 8. Red Team — adversarial challenge must have run at least once
    red_team_count = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_module_events` "
        "WHERE paper_id = :pid AND event_type = 'red_team'"
    ), {"pid": paper_id}).scalar() or 0
    checks.append({
        "code":   "RED_TEAM_RAN",
        "label":  "Red Team challenge",
        "passed": red_team_count >= 1,
        "detail": f"{red_team_count} red team event{'s' if red_team_count != 1 else ''} — minimum 1 required",
    })

    return checks


# ── Author Profile — derived from sealed provenance, never asked ──────────────

def _compute_author_profile(paper_id: int, paper: dict, sections: list,
                              db: Session) -> dict:
    """
    Derives behavioral profile from the provenance record at seal time.
    Signals are observed passively — the author never fills out a profile.
    The bin is the shape of how they worked.
    """
    bins = []
    ev   = {}

    interrog = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_interrogation_log` WHERE paper_id = :pid"
    ), {"pid": paper_id}).scalar() or 0

    module_count = db.execute(text(
        "SELECT COUNT(DISTINCT id) FROM `#__eaiou_intelligence_modules` WHERE paper_id = :pid"
    ), {"pid": paper_id}).scalar() or 0

    red_team = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_module_events` "
        "WHERE paper_id = :pid AND event_type = 'red_team'"
    ), {"pid": paper_id}).scalar() or 0

    volley_rounds = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_volley_log` WHERE paper_id = :pid"
    ), {"pid": paper_id}).scalar() or 0

    undefined_at_seal = sum(
        1 for s in sections
        if not (s.get("section_content") or "").strip()
        and not (s.get("section_notes") or "").strip()
    )

    origin   = paper.get("origin_type", "")
    ai_level = paper.get("ai_disclosure_level", "")

    ev.update({
        "origin_type":                origin,
        "ai_disclosure_level":        ai_level,
        "interrogation_exchanges":    interrog,
        "modules_used":               module_count,
        "red_team_runs":              red_team,
        "volley_rounds":              volley_rounds,
        "undefined_sections_at_seal": undefined_at_seal,
        "total_sections":             len(sections),
    })

    # Origin
    if origin == "humint":
        if ai_level in ("none", "minimal") and module_count <= 1:
            bins.append({"dim": "origin", "bin": "Originator",
                "reason": f"HUMINT-conceived · {ai_level} AI involvement"})
        elif interrog >= 5 and module_count >= 2:
            bins.append({"dim": "origin", "bin": "Collaborator",
                "reason": f"HUMINT-conceived · {interrog} interrogation exchanges · {module_count} intelligence modules"})
        else:
            bins.append({"dim": "origin", "bin": "Director",
                "reason": f"HUMINT-conceived · {ai_level} AI involvement · directed {module_count} module{'s' if module_count != 1 else ''}"})
    else:
        bins.append({"dim": "origin", "bin": "Synthesizer",
            "reason": "Non-HUMINT origin — intelligence-generated work"})

    # Investigation depth
    if interrog >= 5:
        bins.append({"dim": "investigation", "bin": "Explorer",
            "reason": f"{interrog} interrogation exchanges before theory"})
    elif interrog >= 2:
        bins.append({"dim": "investigation", "bin": "Efficient",
            "reason": f"{interrog} interrogation exchanges"})
    else:
        bins.append({"dim": "investigation", "bin": "Skimmer",
            "reason": f"{interrog} interrogation exchange{'s' if interrog != 1 else ''}"})

    # Self-challenge
    if red_team >= 3:
        bins.append({"dim": "challenge", "bin": "Stress-Tester",
            "reason": f"Red Team ran {red_team} times"})
    else:
        bins.append({"dim": "challenge", "bin": "Challenger",
            "reason": f"Red Team ran {red_team} time{'s' if red_team != 1 else ''}"})

    # Thoroughness
    if undefined_at_seal == 0:
        bins.append({"dim": "thoroughness", "bin": "Complete",
            "reason": "All sections written at seal"})
    elif undefined_at_seal <= 2:
        bins.append({"dim": "thoroughness", "bin": "Provisional",
            "reason": f"{undefined_at_seal} undefined section{'s' if undefined_at_seal != 1 else ''} at seal"})
    else:
        bins.append({"dim": "thoroughness", "bin": "Minimal",
            "reason": f"{undefined_at_seal} of {len(sections)} sections undefined at seal"})

    # Volley posture
    if volley_rounds >= 3:
        bins.append({"dim": "volley", "bin": "Rigorous",
            "reason": f"{volley_rounds} audit rounds before clean"})
    elif volley_rounds == 1:
        bins.append({"dim": "volley", "bin": "Clean-Direct",
            "reason": "Clean on first audit"})
    else:
        bins.append({"dim": "volley", "bin": "Solid",
            "reason": f"{volley_rounds} audit rounds"})

    # Ambition — gap age
    if paper.get("gitgap_gap_id"):
        try:
            with httpx.Client(timeout=3) as client:
                r = client.get(f"{GITGAP_API}/gaps/{paper['gitgap_gap_id']}")
                if r.status_code == 200:
                    gap_year = r.json().get("pub_year")
                    if gap_year:
                        gap_age = datetime.now(timezone.utc).year - gap_year
                        ev["gap_age_years"] = gap_age
                        bins.append({
                            "dim": "ambition",
                            "bin": "Ambitious" if gap_age >= 10 else "Current",
                            "reason": f"Responded to a {gap_age}-year-old unresolved gap",
                        })
        except Exception:
            pass

    return {"bins": bins, "evidence": ev}


# ── Wheelhouse: Vocabulary + Gap Matching ─────────────────────────────────────

_STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "up", "as", "is", "was", "are", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "shall", "can",
    "this", "that", "these", "those", "it", "its", "we", "our", "they",
    "their", "not", "no", "nor", "so", "yet", "both", "either", "neither",
    "such", "more", "most", "also", "into", "than", "then", "there",
    "when", "where", "which", "who", "what", "how", "why", "all", "each",
    "few", "some", "any", "while", "after", "before", "between", "through",
    "about", "during", "study", "studies", "research", "paper", "work",
    "method", "methods", "result", "results", "data", "analysis", "based",
    "using", "used", "among", "between", "within", "without", "across",
    "whether", "however", "therefore", "thus", "although", "despite",
    "provide", "provides", "provided", "present", "presents", "show",
    "shows", "showed", "find", "finds", "found", "remain", "remains",
    "lack", "lacking", "known", "unknown", "well", "different", "current",
    "new", "novel", "important", "significant", "effect", "effects",
    "level", "levels", "high", "low", "increased", "decreased", "change",
    "changes", "function", "functions", "role", "roles", "associated",
    "related", "given", "evidence", "understanding", "further", "review",
    "available", "limited", "large", "small", "specific", "other",
    "two", "three", "one", "including", "compared", "control",
    "human", "patients", "sample", "samples", "case", "cases",
}

import re as _re_vocab


def _extract_vocab(texts: list) -> list:
    """
    Extract significant single-word and two-word terms from a list of text strings.
    Filters stop words and short tokens. Returns top 200 by frequency.
    """
    combined = " ".join(t for t in texts if t)
    tokens = _re_vocab.findall(r"[a-z][a-z'\-]{2,}", combined.lower())
    singles = [t for t in tokens if t not in _STOP_WORDS and len(t) >= 4]
    bigrams = []
    for i in range(len(tokens) - 1):
        a, b = tokens[i], tokens[i + 1]
        if a not in _STOP_WORDS and b not in _STOP_WORDS and len(a) >= 4 and len(b) >= 4:
            bigrams.append(f"{a} {b}")
    freq = {}
    for t in singles + bigrams:
        freq[t] = freq.get(t, 0) + 1
    return [t for t, _ in sorted(freq.items(), key=lambda x: -x[1])[:200]]


def _profile_to_query_text(profile_vocab_json: str) -> str:
    """
    Build a query string from profile_vocab_json for context search.
    Handles both formats:
      - JSON list  (from ORCID enrichment): ["hubble tension", "dark energy", ...]
      - JSON dict  (from intake / vectorize_text): {"hubble": 3, "tension": 2, ...}
    Returns top 40 terms joined as a space-separated string.
    """
    data = json.loads(profile_vocab_json) if profile_vocab_json else []
    if isinstance(data, list):
        terms = data[:40]
    else:
        # Dict: sort by count descending, take top 40 keys
        terms = [k for k, _ in sorted(data.items(), key=lambda x: -x[1])][:40]
    return " ".join(str(t) for t in terms)


async def _enrich_orcid(orcid: str) -> list:
    """Fetch publication titles from ORCID public API."""
    url = f"https://pub.orcid.org/v3.0/{orcid}/works"
    async with httpx.AsyncClient(timeout=12) as client:
        r = await client.get(url, headers={"Accept": "application/vnd.orcid+json"})
        if r.status_code != 200:
            return []
    data = r.json()
    titles = []
    for group in data.get("group", []):
        for summary in group.get("work-summary", []):
            title_obj = (summary.get("title") or {}).get("title") or {}
            val = title_obj.get("value", "")
            if val:
                titles.append(val)
    return titles


@router.post("/profile/enrich")
async def profile_enrich(
    request: Request,
    orcid: str = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Enrich author vocabulary profile from ORCID publication record."""
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect

    from fastapi.responses import JSONResponse
    orcid = orcid.strip()
    if not orcid:
        raise HTTPException(status_code=422, detail="ORCID required")

    titles = await _enrich_orcid(orcid)
    if not titles:
        return JSONResponse({"enriched": False, "reason": "No publications found at this ORCID"})

    vocab = _extract_vocab(titles)
    now = datetime.now(timezone.utc)

    existing = db.execute(text(
        "SELECT id FROM `#__eaiou_author_profiles` WHERE orcid = :orcid"
    ), {"orcid": orcid}).fetchone()

    if existing:
        db.execute(text(
            "UPDATE `#__eaiou_author_profiles` "
            "SET profile_vocab_json = :vocab, vocab_updated_at = :ts WHERE orcid = :orcid"
        ), {"vocab": json.dumps(vocab), "ts": now, "orcid": orcid})
    else:
        db.execute(text(
            "INSERT INTO `#__eaiou_author_profiles` "
            "(orcid, profile_vocab_json, vocab_updated_at) VALUES (:orcid, :vocab, :ts)"
        ), {"orcid": orcid, "vocab": json.dumps(vocab), "ts": now})
    db.commit()

    profile_row = db.execute(text(
        "SELECT id FROM `#__eaiou_author_profiles` WHERE orcid = :orcid"
    ), {"orcid": orcid}).fetchone()

    return JSONResponse({
        "enriched": True,
        "vocab_size": len(vocab),
        "profile_id": profile_row[0],
        "sample_terms": vocab[:12],
    })


@router.post("/wheelhouse/rescore")
async def wheelhouse_rescore(
    request: Request,
    orcid: str = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Re-score all keeper-passed gaps from gitgap against author vocabulary."""
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect

    from fastapi.responses import JSONResponse
    profile = db.execute(text(
        "SELECT id, profile_vocab_json FROM `#__eaiou_author_profiles` WHERE orcid = :orcid"
    ), {"orcid": orcid.strip()}).mappings().first()

    if not profile or not profile["profile_vocab_json"]:
        raise HTTPException(status_code=404, detail="Profile not found — run /author/profile/enrich first")

    profile_id  = profile["id"]
    query_text  = _profile_to_query_text(profile["profile_vocab_json"])

    if not query_text.strip():
        return JSONResponse({"rescored": False, "reason": "Profile vocabulary is empty"})

    try:
        with httpx.Client(timeout=10) as client:
            r = client.get(f"{GITGAP_API}/gaps/search", params={
                "q":         query_text,
                "limit":     200,
                "min_score": 0.05,   # filter out truly unrelated gaps
            })
            if r.status_code != 200:
                return JSONResponse({"rescored": False, "reason": "gitgap context search unavailable"})
            gaps = r.json().get("gaps", [])
    except Exception:
        return JSONResponse({"rescored": False, "reason": "gitgap unreachable"})

    now = datetime.now(timezone.utc)
    scored = 0
    for gap in gaps:
        score = gap.get("similarity", 0.0)
        if score <= 0:
            continue
        db.execute(text(
            "INSERT INTO `#__eaiou_gap_matches` "
            "(author_profile_id, gap_id, gap_declaration, gap_title, gap_journal, gap_term, "
            "match_score, matched_at) "
            "VALUES (:pid, :gid, :decl, :title, :journal, :term, :score, :ts) "
            "ON DUPLICATE KEY UPDATE match_score = :score, matched_at = :ts"
        ), {
            "pid":    profile_id,
            "gid":    gap["id"],
            "decl":   (gap.get("declaration_text") or "")[:1000],
            "title":  (gap.get("title") or "")[:500],
            "journal":(gap.get("journal") or "")[:200],
            "term":   (gap.get("gateway_term") or "")[:100],
            "score":  score,
            "ts":     now,
        })
        scored += 1

    db.commit()
    return JSONResponse({"rescored": True, "gaps_scored": len(gaps), "matches_found": scored,
                         "query_preview": query_text[:120]})


@router.post("/wheelhouse/rescore-all")
async def wheelhouse_rescore_all(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    F1-D: Bulk wheelhouse rescore for all ORCID-linked author profiles.
    Protected by EAIOU_MASTER_API_KEY — called by gitgap after new gaps are pinned.
    Returns 202 so gitgap doesn't wait for the full run to complete.
    """
    from fastapi.responses import JSONResponse

    key = request.headers.get("X-API-Key", "")
    if not EAIOU_MASTER_API_KEY or not key or key != EAIOU_MASTER_API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    profiles = db.execute(text(
        "SELECT id, orcid, profile_vocab_json FROM `#__eaiou_author_profiles` "
        "WHERE profile_vocab_json IS NOT NULL AND profile_vocab_json != '' "
        "LIMIT 100"
    )).mappings().all()

    results = []
    for profile in profiles:
        try:
            query_text = _profile_to_query_text(profile["profile_vocab_json"])
            if not query_text.strip():
                continue
            with httpx.Client(timeout=10) as client:
                r = client.get(f"{GITGAP_API}/gaps/search", params={
                    "q": query_text, "limit": 200, "min_score": 0.05,
                })
                if r.status_code != 200:
                    continue
                gaps = r.json().get("gaps", [])
            now = datetime.now(timezone.utc)
            scored = 0
            for gap in gaps:
                score = gap.get("similarity", 0.0)
                if score <= 0:
                    continue
                db.execute(text(
                    "INSERT INTO `#__eaiou_gap_matches` "
                    "(author_profile_id, gap_id, gap_declaration, gap_title, gap_journal, gap_term, "
                    "match_score, matched_at) "
                    "VALUES (:pid, :gid, :decl, :title, :journal, :term, :score, :ts) "
                    "ON DUPLICATE KEY UPDATE match_score = :score, matched_at = :ts"
                ), {
                    "pid":     profile["id"],
                    "gid":     gap["id"],
                    "decl":    (gap.get("declaration_text") or "")[:1000],
                    "title":   (gap.get("title") or "")[:500],
                    "journal": (gap.get("journal") or "")[:200],
                    "term":    (gap.get("gateway_term") or "")[:100],
                    "score":   score,
                    "ts":      now,
                })
                scored += 1
            db.commit()
            results.append({"orcid": profile["orcid"], "scored": scored})
        except Exception:
            pass  # Non-fatal per profile

    return JSONResponse({"rescored_profiles": len(results), "results": results}, status_code=202)


@router.get("/wheelhouse")
async def get_wheelhouse(
    request: Request,
    orcid: str = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return top gap matches for the wheelhouse card (JSON)."""
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect

    from fastapi.responses import JSONResponse
    if not orcid:
        return JSONResponse({"matches": [], "profile_exists": False})

    profile = db.execute(text(
        "SELECT id FROM `#__eaiou_author_profiles` WHERE orcid = :orcid"
    ), {"orcid": orcid.strip()}).mappings().first()

    if not profile:
        return JSONResponse({"matches": [], "profile_exists": False})

    matches = db.execute(text(
        "SELECT id, gap_id, gap_declaration, gap_title, gap_journal, gap_term, match_score "
        "FROM `#__eaiou_gap_matches` "
        "WHERE author_profile_id = :pid AND dismissed = 0 AND accepted = 0 "
        "ORDER BY match_score DESC LIMIT 8"
    ), {"pid": profile["id"]}).mappings().all()

    return JSONResponse({"matches": [dict(m) for m in matches], "profile_exists": True})


@router.post("/wheelhouse/{match_id}/dismiss")
async def wheelhouse_dismiss(
    match_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect

    from fastapi.responses import JSONResponse
    db.execute(text(
        "UPDATE `#__eaiou_gap_matches` SET dismissed = 1 WHERE id = :id"
    ), {"id": match_id})
    db.commit()
    return JSONResponse({"dismissed": True})


@router.post("/wheelhouse/{match_id}/accept")
async def wheelhouse_accept(
    match_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect

    from fastapi.responses import JSONResponse
    row = db.execute(text(
        "SELECT gap_id FROM `#__eaiou_gap_matches` WHERE id = :id"
    ), {"id": match_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Match not found")

    db.execute(text(
        "UPDATE `#__eaiou_gap_matches` SET accepted = 1 WHERE id = :id"
    ), {"id": match_id})
    db.commit()
    return JSONResponse({
        "accepted": True,
        "gap_id": row["gap_id"],
        "redirect": f"/author/submit?gap_id={row['gap_id']}",
    })


@router.get("/workspace/{paper_id}/profile")
async def workspace_profile(
    paper_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect
    from fastapi.responses import JSONResponse
    row = db.execute(text(
        "SELECT author_profile_json, status FROM `#__eaiou_papers` WHERE id = :id"
    ), {"id": paper_id}).mappings().first()
    if not row or not row["author_profile_json"]:
        raise HTTPException(status_code=404, detail="Profile not yet computed.")
    return JSONResponse(json.loads(row["author_profile_json"]))


@router.get("/", response_class=HTMLResponse)
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect

    papers = db.execute(text(
        "SELECT id, paper_uuid, cosmoid, title, status, ai_disclosure_level, orcid "
        "FROM `#__eaiou_papers` "
        "ORDER BY q_overall IS NULL, q_overall DESC, paper_uuid ASC LIMIT 100"
    )).mappings().all()

    # Status counts
    counts = {"total": 0, "submitted": 0, "under_review": 0, "accepted": 0}
    author_orcid = None
    for p in papers:
        counts["total"] += 1
        s = p["status"]
        if s in counts:
            counts[s] += 1
        if p.get("orcid") and not author_orcid:
            author_orcid = p["orcid"]

    # Wheelhouse: top gap matches for this author
    wheelhouse = []
    profile_exists = False
    if author_orcid:
        profile_row = db.execute(text(
            "SELECT id FROM `#__eaiou_author_profiles` WHERE orcid = :orcid"
        ), {"orcid": author_orcid}).mappings().first()
        if profile_row:
            profile_exists = True
            wheelhouse = db.execute(text(
                "SELECT id, gap_id, gap_declaration, gap_title, gap_journal, "
                "gap_term, match_score "
                "FROM `#__eaiou_gap_matches` "
                "WHERE author_profile_id = :pid AND dismissed = 0 AND accepted = 0 "
                "ORDER BY match_score DESC LIMIT 5"
            ), {"pid": profile_row["id"]}).mappings().all()
            wheelhouse = [dict(w) for w in wheelhouse]

    # Intake completion check
    intake_complete = False
    if author_orcid:
        intake_row = db.execute(text(
            "SELECT intake_json FROM `#__eaiou_author_profiles` WHERE orcid = :orcid"
        ), {"orcid": author_orcid}).mappings().first()
        if intake_row and intake_row["intake_json"]:
            data = json.loads(intake_row["intake_json"])
            intake_complete = data.get("completed_at") is not None

    # F2-D: Unread notification count for badge
    unread_count = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_notifications` WHERE read_at IS NULL"
    )).scalar() or 0

    # F2-D: Recent unread notifications for dashboard feed (latest 10)
    notifications = db.execute(text(
        "SELECT n.id, n.paper_id, n.type, n.message, n.created_at, n.read_at "
        "FROM `#__eaiou_notifications` n "
        "ORDER BY n.created_at DESC LIMIT 10"
    )).mappings().all()

    return templates.TemplateResponse(request, "views/30_submission_dashboard.html", {
        "current_user": current_user,
        "papers": papers,
        "stats": counts,
        "author_orcid": author_orcid,
        "wheelhouse": wheelhouse,
        "profile_exists": profile_exists,
        "intake_complete": intake_complete,
        "unread_count": unread_count,
        "notifications": [dict(n) for n in notifications],
        "notification_count": unread_count,
    })


# ── Author intake conversation ────────────────────────────────────────────────

_INTAKE_STEPS = [
    {
        "step": 1,
        "field": "domain",
        "question": "What is your primary research domain?",
        "hint": "e.g. Theoretical Physics, Molecular Biology, Clinical Psychology, Mathematics",
        "placeholder": "Describe your field in a few words…",
        "type": "text",
    },
    {
        "step": 2,
        "field": "methods",
        "question": "What methods do you typically use in your work?",
        "hint": "e.g. analytical derivations, observational data, clinical trials, meta-analysis",
        "placeholder": "Describe your methodology…",
        "type": "textarea",
    },
    {
        "step": 3,
        "field": "ai_tools",
        "question": "How do you use AI tools in your research process?",
        "hint": "Be honest — this helps us calibrate the AI disclosure analysis. 'Not at all' is a valid answer.",
        "placeholder": "e.g. drafting, literature review, mathematical checks, not at all…",
        "type": "textarea",
    },
    {
        "step": 4,
        "field": "journals",
        "question": "What journals or sources do you regularly read or cite?",
        "hint": "This seeds gap recommendations from the literature you already follow.",
        "placeholder": "e.g. Physical Review D, Nature, JAMA, arXiv astro-ph…",
        "type": "text",
    },
]


def _get_or_create_profile_id(orcid: str, db: Session) -> int:
    row = db.execute(text(
        "SELECT id FROM `#__eaiou_author_profiles` WHERE orcid = :orcid"
    ), {"orcid": orcid}).mappings().first()
    if row:
        return row["id"]
    db.execute(text(
        "INSERT INTO `#__eaiou_author_profiles` (orcid) VALUES (:orcid)"
    ), {"orcid": orcid})
    db.commit()
    return db.execute(text("SELECT LAST_INSERT_ID()")).scalar()


@router.get("/new", response_class=HTMLResponse)
async def submission_hub(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Submission intake hub — four pathways to creating a new paper."""
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect

    orcid = (current_user or {}).get("orcid") or (current_user or {}).get("username")

    # Prefetch wheelhouse matches if profile exists
    wheelhouse = []
    profile_exists = False
    if orcid:
        profile = db.execute(text(
            "SELECT id FROM `#__eaiou_author_profiles` WHERE orcid = :orcid"
        ), {"orcid": orcid}).mappings().first()
        if profile:
            profile_exists = True
            matches = db.execute(text(
                "SELECT id, gap_id, gap_declaration, gap_title, gap_journal, "
                "       gap_term, match_score "
                "FROM `#__eaiou_gap_matches` "
                "WHERE author_profile_id = :pid AND dismissed = 0 AND accepted = 0 "
                "ORDER BY match_score DESC LIMIT 5"
            ), {"pid": profile["id"]}).mappings().all()
            wheelhouse = [dict(m) for m in matches]

    return templates.TemplateResponse(request, "author/submission_hub.html", {
        "current_user":   current_user,
        "wheelhouse":     wheelhouse,
        "profile_exists": profile_exists,
        "gitgap_url":     "http://127.0.0.1:8001",
    })


class TextBody(BaseModel):
    text: str


@router.post("/quick-coverage")
async def quick_coverage(body: TextBody, current_user=Depends(get_current_user)):
    """Stateless coverage analysis — no paper record created. Used by submission hub card 3."""
    from fastapi.responses import JSONResponse
    from ..services.coverage import analyze_coverage
    result = analyze_coverage(abstract=body.text, sections=[])
    return JSONResponse(result)


@router.post("/preprint-check")
async def preprint_check(body: TextBody, current_user=Depends(get_current_user)):
    """
    Blind integrity check on raw preprint text.
    Runs: claim coverage, basic AI-signal heuristics, declaration scan.
    No record created. Returns structured report.
    """
    from fastapi.responses import JSONResponse
    from ..services.coverage import analyze_coverage, extract_claims

    text = body.text or ""

    # Coverage analysis
    coverage = analyze_coverage(abstract=text, sections=[])

    # Basic AI-signal heuristic: look for characteristic AI phrasing
    import re
    ai_phrases = [
        r"\bdelve\b", r"\bcomprehensive\b.*\bframework\b",
        r"\bit('s| is) (important|worth|crucial) to note\b",
        r"\bin (this|the) (context|realm)\b",
        r"\bfacilitate\b", r"\bleverage\b",
        r"\bcertainly\b", r"\babsolutely\b",
        r"\bI('d| would) be happy\b",
    ]
    ai_hits = sum(1 for p in ai_phrases if re.search(p, text, re.IGNORECASE))
    if ai_hits >= 3:
        ai_signal = "high — characteristic AI phrasing detected"
    elif ai_hits >= 1:
        ai_signal = "moderate"
    else:
        ai_signal = "low"

    # Gate-style checks (stateless versions)
    claims = extract_claims(text)
    has_abstract = len(text) > 200
    has_claims = len(claims) > 0
    novel_ratio = (coverage["summary"]["novel"] / max(coverage["summary"]["total"], 1))

    checks = [
        {
            "code":   "min_length",
            "label":  "Sufficient content",
            "passed": has_abstract,
            "detail": None if has_abstract else "Text is very short — paste abstract and key sections for a useful check.",
        },
        {
            "code":   "claims_detected",
            "label":  "Assertions detected",
            "passed": has_claims,
            "detail": None if has_claims else "No verifiable claims found. Paper may need more explicit result statements.",
        },
        {
            "code":   "coverage_not_zero",
            "label":  "Literature coverage",
            "passed": coverage["summary"]["covered"] > 0,
            "detail": "At least one claim matches existing literature." if coverage["summary"]["covered"] > 0 else "No claims matched known literature — verify citations are present.",
        },
        {
            "code":   "novel_contributions",
            "label":  "Novel contributions identified",
            "passed": coverage["summary"]["novel"] > 0,
            "detail": f"{coverage['summary']['novel']} claim(s) identified as novel gap fills." if coverage["summary"]["novel"] > 0 else "No novel claims detected — the contribution may need clearer framing.",
        },
        {
            "code":   "ai_disclosure",
            "label":  "AI signal within acceptable range",
            "passed": ai_hits < 3,
            "detail": f"AI phrase density: {ai_hits} hit(s). Disclose AI use in submission." if ai_hits >= 3 else None,
        },
    ]

    return JSONResponse({
        "checks":                checks,
        "coverage_summary":      coverage["summary"],
        "ai_disclosure_detected": ai_signal,
        "error":                 None,
    })


@router.get("/intake", response_class=HTMLResponse)
async def intake_get(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect

    orcid = current_user.get("orcid") or current_user.get("username")
    if not orcid:
        return RedirectResponse("/author/dashboard", status_code=302)

    row = db.execute(text(
        "SELECT intake_json FROM `#__eaiou_author_profiles` WHERE orcid = :orcid"
    ), {"orcid": orcid}).mappings().first()

    intake = json.loads(row["intake_json"]) if row and row["intake_json"] else {}
    if intake.get("completed_at"):
        return RedirectResponse("/author/dashboard", status_code=302)

    current_step = intake.get("step", 1)
    if current_step > len(_INTAKE_STEPS):
        return RedirectResponse("/author/dashboard", status_code=302)

    step_def = _INTAKE_STEPS[current_step - 1]
    return templates.TemplateResponse(request, "views/28_submission_form.html", {
        "current_user": current_user,
        "step_def": step_def,
        "total_steps": len(_INTAKE_STEPS),
        "intake": intake,
        "notification_count": 0,
    })


@router.get("/intake/back/{step}", response_class=HTMLResponse)
async def intake_back(
    request: Request,
    step: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Go back one step — decrement the step counter and redirect to /intake."""
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect
    orcid = current_user.get("orcid") or current_user.get("username")
    if not orcid:
        return RedirectResponse("/author/dashboard", status_code=302)
    row = db.execute(text(
        "SELECT intake_json FROM `#__eaiou_author_profiles` WHERE orcid = :orcid"
    ), {"orcid": orcid}).mappings().first()
    intake = json.loads(row["intake_json"]) if row and row["intake_json"] else {}
    intake["step"] = max(1, step - 1)
    db.execute(text(
        "UPDATE `#__eaiou_author_profiles` SET intake_json = :intake WHERE orcid = :orcid"
    ), {"intake": json.dumps(intake), "orcid": orcid})
    db.commit()
    return RedirectResponse("/author/intake", status_code=302)


@router.post("/intake", response_class=HTMLResponse)
async def intake_post(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect

    orcid = current_user.get("orcid") or current_user.get("username")
    if not orcid:
        return RedirectResponse("/author/dashboard", status_code=302)

    form = await request.form()
    step  = int(form.get("step", 1))
    field = form.get("field", "")
    value = (form.get("value") or "").strip()

    profile_id = _get_or_create_profile_id(orcid, db)

    row = db.execute(text(
        "SELECT intake_json FROM `#__eaiou_author_profiles` WHERE orcid = :orcid"
    ), {"orcid": orcid}).mappings().first()

    intake = json.loads(row["intake_json"]) if row and row["intake_json"] else {}
    if field:
        intake[field] = value
    intake["step"] = step + 1

    now = datetime.now(timezone.utc)

    if step >= len(_INTAKE_STEPS):
        # Final step — mark complete
        intake["completed_at"] = now.isoformat()
        # Seed profile_vocab_json from intake answers
        combined = " ".join(str(intake.get(k, "")) for k in ("domain", "methods", "journals"))
        from ..services.integrity import vectorize_text
        vocab = vectorize_text(combined)
        db.execute(text(
            "UPDATE `#__eaiou_author_profiles` "
            "SET intake_json = :intake, profile_vocab_json = :vocab, "
            "vocab_updated_at = :ts, updated_at = :ts "
            "WHERE orcid = :orcid"
        ), {
            "intake": json.dumps(intake),
            "vocab":  json.dumps(vocab),
            "ts":     now,
            "orcid":  orcid,
        })
        db.commit()
        return RedirectResponse("/author/dashboard?intake=done", status_code=302)

    db.execute(text(
        "UPDATE `#__eaiou_author_profiles` "
        "SET intake_json = :intake, updated_at = :ts "
        "WHERE orcid = :orcid"
    ), {"intake": json.dumps(intake), "ts": now, "orcid": orcid})
    db.commit()

    return RedirectResponse("/author/intake", status_code=302)


@router.get("/papers", response_class=HTMLResponse)
async def author_papers(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Alias for dashboard — same view, My Papers nav active."""
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect
    return RedirectResponse(url="/author/", status_code=302)


@router.get("/submit", response_class=HTMLResponse)
async def submit_form(
    request: Request,
    gap_id: str = Query(None, description="gitgap gap ID — pre-fills from gap leaf"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect

    gap = None
    related_gaps = []
    if gap_id and gap_id.isdigit():
        try:
            with httpx.Client(timeout=5) as client:
                resp = client.get(f"{GITGAP_API}/gaps/{gap_id}")
                if resp.status_code == 200:
                    gap = resp.json()
                    # Pull related gaps using the declaration as the query
                    # Gives the investigator a landscape view before writing
                    if gap.get("declaration_text"):
                        sr = client.get(f"{GITGAP_API}/gaps/search", params={
                            "q": gap["declaration_text"],
                            "limit": 5,
                            "min_score": 0.20,
                        })
                        if sr.status_code == 200:
                            related_gaps = [
                                g for g in sr.json().get("gaps", [])
                                if str(g.get("id")) != str(gap_id)
                            ]
        except Exception:
            pass  # gitgap unavailable — form renders without pre-fill

    # Drawer files — quick-pick for doc-populate card
    drawer = []
    if current_user:
        drawer = db.execute(
            text("SELECT id, original_name, mime_type, file_size "
                 "FROM `#__eaiou_user_files` "
                 "WHERE user_id = :u AND deleted_at IS NULL ORDER BY uploaded_at DESC LIMIT 20"),
            {"u": current_user["id"]},
        ).mappings().all()

    return templates.TemplateResponse(request, "author/submit.html", {
        "current_user": current_user,
        "error": None,
        "form": {},
        "gap": gap,
        "related_gaps": related_gaps,
        "csrf_token": get_csrf_token(request),
        "drawer_files": drawer,
    })


@router.post("/submit")
async def submit_paper(
    request: Request,
    title: str = Form(...),
    abstract: str = Form(...),
    author_name: str = Form(...),
    orcid: str = Form(""),
    keywords: str = Form(""),
    ai_disclosure_level: str = Form(...),
    ai_disclosure_notes: str = Form(""),
    # N items — required author acts
    attest_conceived: str = Form(None),
    attest_methodology: str = Form(None),
    attest_interpreted: str = Form(None),
    attest_responsibility: str = Form(None),
    attest_gap_anchor: str = Form(None),
    # CAN items — optional production assistance
    can_spellcheck: str = Form(None),
    can_lit_search: str = Form(None),
    can_data_format: str = Form(None),
    can_statistical: str = Form(None),
    can_translation: str = Form(None),
    can_figure_gen: str = Form(None),
    # AI detection consent — required when ai_disclosure_level == 'none'
    attest_ai_detection_consent: str = Form(None),
    # Gap linkage
    gitgap_gap_id: int = Form(None),
    gitgap_source_pmcid: str = Form(""),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect
    validate_csrf(request, csrf_token)

    form_data = {
        "title": title, "abstract": abstract, "author_name": author_name,
        "orcid": orcid, "keywords": keywords,
        "ai_disclosure_level": ai_disclosure_level,
        "ai_disclosure_notes": ai_disclosure_notes,
    }

    # Re-fetch gap for error re-render if needed
    gap = None
    if gitgap_gap_id:
        try:
            with httpx.Client(timeout=5) as client:
                resp = client.get(f"{GITGAP_API}/gaps/{gitgap_gap_id}")
                if resp.status_code == 200:
                    gap = resp.json()
        except Exception:
            pass

    def _err(msg):
        return templates.TemplateResponse(request, "author/submit.html", {
            "current_user": current_user,
            "error": msg,
            "form": form_data,
            "gap": gap,
        }, status_code=422)

    if not title.strip() or not abstract.strip() or not author_name.strip():
        return _err("Title, abstract, and author name are required.")

    # All N items must be checked — these are the acts that constitute authorship
    n_checked = [attest_conceived, attest_methodology, attest_interpreted, attest_responsibility]
    if not all(n_checked):
        return _err("All author attestation items are required.")

    if gitgap_gap_id and not attest_gap_anchor:
        return _err("You must acknowledge the CAUGHT gap anchor to submit in response to a gap.")

    if ai_disclosure_level == "none" and not attest_ai_detection_consent:
        return _err("Declaring no AI involvement requires consent to AI detection. Please acknowledge the detection terms.")

    now = datetime.now(timezone.utc)
    paper_uuid = str(uuid.uuid4())
    cosmoid = str(uuid.uuid4())

    attestation = {
        "n_items": {
            "conceived": True,
            "methodology": True,
            "interpreted": True,
            "responsibility": True,
        },
        "can_items": {
            "spellcheck": bool(can_spellcheck),
            "lit_search": bool(can_lit_search),
            "data_format": bool(can_data_format),
            "statistical": bool(can_statistical),
            "translation": bool(can_translation),
            "figure_gen": bool(can_figure_gen),
        },
        "sealed_at": now.isoformat(),
    }
    if gitgap_gap_id:
        attestation["n_items"]["gap_anchor"] = True
    if ai_disclosure_level == "none" and attest_ai_detection_consent:
        attestation["ai_detection_consent"] = True

    # origin_type: derived from attestation at submission, sealed permanently.
    # humint     = work started by human interest; all four authorial acts attested by a human
    # non_humint = authorial acts not attested as human-origin; generated by intelligences
    n_items = attestation["n_items"]
    humint_acts = [n_items.get("conceived"), n_items.get("methodology"),
                   n_items.get("interpreted"), n_items.get("responsibility")]
    origin_type = "humint" if all(humint_acts) else "non_humint"
    attestation["origin_type"] = origin_type

    db.execute(text(
        "INSERT INTO `#__eaiou_papers` "
        "(paper_uuid, cosmoid, title, abstract, author_name, orcid, keywords, "
        "ai_disclosure_level, ai_disclosure_notes, status, submitted_at, created, "
        "gitgap_gap_id, gitgap_source_pmcid, attestation_json, attestation_sealed_at, "
        "origin_type) "
        "VALUES (:uuid, :cosmoid, :title, :abstract, :author_name, :orcid, :keywords, "
        ":ai_level, :ai_notes, 'submitted', :submitted_at, :created, "
        ":gap_id, :source_pmcid, :attest_json, :attest_sealed, "
        ":origin_type)"
    ), {
        "uuid": paper_uuid,
        "cosmoid": cosmoid,
        "title": title.strip(),
        "abstract": abstract.strip(),
        "author_name": author_name.strip(),
        "orcid": orcid.strip() or None,
        "keywords": keywords.strip() or None,
        "ai_level": ai_disclosure_level,
        "ai_notes": ai_disclosure_notes.strip() or None,
        "submitted_at": now,
        "created": now,
        "gap_id": gitgap_gap_id or None,
        "source_pmcid": gitgap_source_pmcid.strip() or None,
        "attest_json": json.dumps(attestation),
        "attest_sealed": now,
        "origin_type": origin_type,
    })
    db.commit()

    result = db.execute(text(
        "SELECT id FROM `#__eaiou_papers` WHERE paper_uuid = :uuid"
    ), {"uuid": paper_uuid}).fetchone()

    # Reflect back to gitgap — mark this gap as CAUGHT with computed confidence
    if gitgap_gap_id:
        try:
            with httpx.Client(timeout=5) as client:
                # Compute catch_confidence: how well does this abstract address the gap?
                catch_conf = None
                gap_resp = client.get(f"{GITGAP_API}/gaps/{gitgap_gap_id}")
                if gap_resp.status_code == 200:
                    gap_decl = gap_resp.json().get("declaration_text", "")
                    if gap_decl and abstract.strip():
                        abstract_vec = embed_text(abstract.strip())
                        decl_vec = embed_text(gap_decl)
                        catch_conf = round(1.0 - cosine_distance_dense(abstract_vec, decl_vec), 4)
                client.post(
                    f"{GITGAP_API}/gaps/{gitgap_gap_id}/catch",
                    json={"paper_cosmoid": cosmoid, "catch_confidence": catch_conf},
                )
        except Exception:
            pass  # non-fatal — provenance is already in eaiou

    # F1-C: Auto-register novel claims as new gaps in gitgap
    # Only for papers not anchored to an existing gap (they create, not fill)
    if not gitgap_gap_id:
        try:
            from ..services.coverage import analyze_coverage as _analyze_cov
            coverage = _analyze_cov(abstract=abstract.strip(), sections=[], timeout=3.0)
            novel_claims = [
                c for c in coverage.get("claims", []) if c["status"] == "novel"
            ][:5]  # cap at 5 to avoid spamming gitgap
            first_gap_id = None
            if novel_claims:
                with httpx.Client(timeout=5) as client:
                    for claim in novel_claims:
                        term = _gateway_term_from_claim(claim["text"])
                        pin_r = client.post(
                            f"{GITGAP_API}/gaps/pin",
                            json={
                                "declaration_text": claim["text"],
                                "gateway_term":     term,
                                "confidence":       0.75,
                            },
                        )
                        if pin_r.status_code == 200:
                            new_gap_id = pin_r.json().get("id")
                            if new_gap_id:
                                if first_gap_id is None:
                                    first_gap_id = new_gap_id
                                # Immediately CATCH: paper identifies AND addresses this gap
                                client.post(
                                    f"{GITGAP_API}/gaps/{new_gap_id}/catch",
                                    json={"paper_cosmoid": cosmoid, "catch_confidence": 0.75},
                                )
            if first_gap_id:
                db.execute(text(
                    "UPDATE `#__eaiou_papers` SET gitgap_gap_id = :gid WHERE id = :id"
                ), {"gid": first_gap_id, "id": result[0]})
                db.commit()
        except Exception:
            pass  # Non-fatal — gap registration is best-effort

    return RedirectResponse(url=f"/author/workspace/{result[0]}", status_code=303)


@router.get("/workspace/{paper_id}/gate")
async def workspace_gate_status(
    paper_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Returns live gate condition status as JSON."""
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect

    from fastapi.responses import JSONResponse
    paper = db.execute(text(
        "SELECT id, title, abstract, gitgap_gap_id "
        "FROM `#__eaiou_papers` WHERE id = :id"
    ), {"id": paper_id}).mappings().first()
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    sections = db.execute(text(
        "SELECT section_name, section_content, section_notes "
        "FROM `#__eaiou_paper_sections` WHERE paper_id = :pid ORDER BY section_order ASC"
    ), {"pid": paper_id}).mappings().all()

    checks = _check_gateway(paper_id, dict(paper), [dict(s) for s in sections], db)
    return JSONResponse({"all_passed": all(c["passed"] for c in checks), "checks": checks})


@router.websocket("/workspace/{paper_id}/terminal")
async def workspace_terminal(websocket: WebSocket, paper_id: int):
    """Spawn an interactive bash session in a per-paper temp directory."""
    await websocket.accept()

    work_dir = f"/tmp/eaiou_workspace_{paper_id}"
    os.makedirs(work_dir, exist_ok=True)

    master_fd, slave_fd = pty.openpty()

    proc = await asyncio.create_subprocess_exec(
        "/bin/bash", "--login",
        stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
        cwd=work_dir,
        env={**os.environ, "TERM": "xterm-256color", "COLORTERM": "truecolor"},
    )
    os.close(slave_fd)
    loop = asyncio.get_event_loop()

    async def pty_to_ws():
        while True:
            try:
                data = await loop.run_in_executor(None, os.read, master_fd, 4096)
                await websocket.send_bytes(data)
            except OSError:
                break

    async def ws_to_pty():
        try:
            async for msg in websocket.iter_text():
                if msg.startswith("{"):
                    try:
                        obj = json.loads(msg)
                        if obj.get("type") == "resize":
                            cols, rows = int(obj["cols"]), int(obj["rows"])
                            fcntl.ioctl(master_fd, termios.TIOCSWINSZ,
                                        struct.pack("HHHH", rows, cols, 0, 0))
                    except (json.JSONDecodeError, KeyError, OSError):
                        pass
                else:
                    os.write(master_fd, msg.encode("utf-8"))
        except (WebSocketDisconnect, Exception):
            pass

    try:
        await asyncio.gather(pty_to_ws(), ws_to_pty())
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        try:
            proc.kill()
        except ProcessLookupError:
            pass
        try:
            os.close(master_fd)
        except OSError:
            pass


@router.post("/workspace/{paper_id}/seal")
async def workspace_seal(
    paper_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Seal a paper for review — re-checks all gateway conditions server-side."""
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect

    from fastapi.responses import JSONResponse

    paper = db.execute(text(
        "SELECT id, title, abstract, gitgap_gap_id, status, origin_type, ai_disclosure_level "
        "FROM `#__eaiou_papers` WHERE id = :id"
    ), {"id": paper_id}).mappings().first()
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    if paper["status"] in ("under_review", "accepted"):
        return JSONResponse({"error": "Paper is already in the review queue."}, status_code=400)

    sections = db.execute(text(
        "SELECT section_name, section_content, section_notes "
        "FROM `#__eaiou_paper_sections` WHERE paper_id = :pid ORDER BY section_order ASC"
    ), {"pid": paper_id}).mappings().all()
    sections_list = [dict(s) for s in sections]

    checks = _check_gateway(paper_id, dict(paper), sections_list, db)
    failed = [c for c in checks if not c["passed"]]

    if failed:
        return JSONResponse(
            {"blocked": True, "failed_checks": failed, "checks": checks},
            status_code=422,
        )

    now = datetime.now(timezone.utc)

    # ── Trajectory integrity: snapshot + gate validity ────────────────────────
    # For each passed gate: capture snapshot (first time wins — UNIQUE KEY).
    # Compare current state to any existing snapshot to compute gate validity.
    integrity_warns = []

    # Fetch the prior snapshot (last one written) to measure drift chain.
    prior_snapshot = db.execute(text(
        "SELECT word_vector_json, gate_code FROM `#__eaiou_paper_snapshots` "
        "WHERE paper_id = :pid ORDER BY created_at DESC LIMIT 1"
    ), {"pid": paper_id}).mappings().first()
    prior_vec_json = prior_snapshot["word_vector_json"] if prior_snapshot else None

    # Fetch all existing snapshots for this paper
    existing_snaps = {
        row["gate_code"]: row
        for row in db.execute(text(
            "SELECT gate_code, content_hash, word_vector_json "
            "FROM `#__eaiou_paper_snapshots` WHERE paper_id = :pid"
        ), {"pid": paper_id}).mappings().all()
    }

    # Get sections with section_order for integrity service
    sections_full = db.execute(text(
        "SELECT section_name, section_content, section_order "
        "FROM `#__eaiou_paper_sections` WHERE paper_id = :pid ORDER BY section_order ASC"
    ), {"pid": paper_id}).mappings().all()
    sections_full_list = [dict(s) for s in sections_full]

    for check in checks:
        if not check["passed"]:
            continue
        code = check["code"]

        if code not in existing_snaps:
            # First time this gate passed — create snapshot
            snap = build_snapshot_record(
                paper_id, code, sections_full_list, prior_vec_json
            )
            db.execute(text(
                "INSERT IGNORE INTO `#__eaiou_paper_snapshots` "
                "(paper_id, gate_code, content_hash, word_vector_json, section_json, "
                " section_count, divergence_from_prior, change_class) "
                "VALUES (:paper_id, :gate_code, :content_hash, :word_vector_json, :section_json, "
                "        :section_count, :divergence_from_prior, :change_class)"
            ), snap)
            check["validity"] = "intact"
            check["divergence"] = 0.0
            prior_vec_json = snap["word_vector_json"]
        else:
            # Gate previously passed — compute current divergence from that snapshot
            snap = existing_snaps[code]
            delta = divergence_score(snap["word_vector_json"], sections_full_list)
            validity = gate_validity_label(delta)
            check["validity"] = validity
            check["divergence"] = delta
            check["change_class"] = classify_divergence(delta)
            if validity == "invalidated":
                integrity_warns.append({
                    "gate": code,
                    "validity": validity,
                    "divergence": delta,
                    "message": f"Gate {code} evidence no longer corresponds to current manuscript "
                               f"(divergence {delta:.2%}). Re-running this check is recommended.",
                })
            elif validity == "drifted":
                integrity_warns.append({
                    "gate": code,
                    "validity": validity,
                    "divergence": delta,
                    "message": f"Gate {code} shows significant drift ({delta:.2%}). "
                               "Review changes since this gate passed.",
                })

    db.commit()

    # ── Leakage detection ─────────────────────────────────────────────────────
    leakage_hits = detect_leakage(paper_id, db)
    leakage_count = persist_leakage(paper_id, leakage_hits, db)
    db.commit()

    # ── Contamination scoring ─────────────────────────────────────────────────
    contamination = compute_contamination(paper_id, db)

    # ── Compute and seal the author profile ───────────────────────────────────
    profile = _compute_author_profile(paper_id, dict(paper), sections_list, db)
    profile["sealed_at"] = now.isoformat()
    profile["integrity_warns"] = integrity_warns

    # ── Trajectory fork detection ─────────────────────────────────────────────
    # Ensure root exists, then scan snapshot chain for BRANCH/REWRITE events.
    # Creates child trajectory records where divergence exceeded threshold.
    forks = detect_and_record_forks(paper_id, db)
    if forks:
        for fork in forks:
            if fork["change_class"] == "REWRITE":
                integrity_warns.append({
                    "gate":         fork["gate_code"],
                    "validity":     "rewrite_fork",
                    "divergence":   fork["divergence"],
                    "message":      fork["fork_reason"],
                })

    db.execute(text(
        "UPDATE `#__eaiou_papers` "
        "SET status = 'under_review', pipeline_stage = 'sealed', submitted_at = :ts, "
        "    author_profile_json = :profile, author_profile_computed_at = :ts "
        "WHERE id = :id"
    ), {"ts": now, "id": paper_id, "profile": json.dumps(profile)})

    # ── Persist integrity seal (CoA record) ───────────────────────────────────
    cosmoid = db.execute(text(
        "SELECT cosmoid FROM `#__eaiou_papers` WHERE id = :id"
    ), {"id": paper_id}).scalar()

    gate_valid = not integrity_warns or all(
        w.get("validity") != "invalidated" for w in integrity_warns
    )

    # ── MBS — Manuscript Basin Score ─────────────────────────────────────────
    snap_rows = db.execute(text(
        "SELECT divergence_from_prior FROM `#__eaiou_paper_snapshots` "
        "WHERE paper_id = :pid AND divergence_from_prior IS NOT NULL"
    ), {"pid": paper_id}).fetchall()
    max_divergence = max((r[0] for r in snap_rows), default=0.0)
    snap_count = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_paper_snapshots` WHERE paper_id = :pid"
    ), {"pid": paper_id}).scalar() or 0

    mbs = compute_mbs(
        checks=checks,
        leakage_count=leakage_count,
        contamination_score=contamination["contamination_score"],
        snapshot_count=snap_count,
        max_divergence=max_divergence,
    )
    mbs_class = mbs_label(mbs)

    audit_status = "PASS" if gate_valid and leakage_count == 0 and mbs >= 0.75 else "WARN"

    integrity_payload = {
        "paper_id": paper_id,
        "cosmoid": cosmoid,
        "gate_validity": {c["code"]: c.get("validity", "intact") for c in checks},
        "integrity_warns": integrity_warns,
        "leakage": {
            "count": leakage_count,
            "top_hits": [h.to_dict() for h in leakage_hits[:10]],
        },
        "contamination": contamination,
        "mbs": mbs,
        "mbs_label": mbs_class,
        "sealed_at": now.isoformat(),
    }

    import hashlib
    seal_hash = hashlib.sha256(
        json.dumps(integrity_payload, sort_keys=True, default=str).encode()
    ).hexdigest()

    db.execute(text(
        "INSERT INTO `#__eaiou_integrity_seals` "
        "(paper_id, cosmoid, seal_hash, gate_valid, leakage_count, "
        "contamination_score, mbs, audit_status, integrity_payload_json) "
        "VALUES (:pid, :cid, :hash, :gv, :lc, :cs, :mbs, :status, :payload) "
        "ON DUPLICATE KEY UPDATE "
        "seal_hash=:hash, gate_valid=:gv, leakage_count=:lc, "
        "contamination_score=:cs, mbs=:mbs, audit_status=:status, "
        "integrity_payload_json=:payload, sealed_at=CURRENT_TIMESTAMP"
    ), {
        "pid": paper_id, "cid": cosmoid, "hash": seal_hash,
        "gv": 1 if gate_valid else 0, "lc": leakage_count,
        "cs": contamination["contamination_score"],
        "mbs": mbs, "status": audit_status,
        "payload": json.dumps(integrity_payload),
    })
    db.commit()

    # ── Q signal — computed from all available evidence at seal time ──────────
    q_result = persist_q_signal(paper_id, db)

    response = {
        "sealed": True,
        "redirect": f"/papers/{paper['id']}",
        "audit_status": audit_status,
        "leakage_count": leakage_count,
        "q_signal": q_result["q_signal"],
        "q_label": q_result["q_label"],
    }
    if integrity_warns:
        response["integrity_warns"] = integrity_warns
    return JSONResponse(response)


@router.get("/workspace/{paper_id}/trajectory")
async def workspace_trajectory(
    paper_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Return the trajectory tree for this paper.
    Shows where BRANCH and REWRITE forks occurred relative to the snapshot chain.
    """
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect
    from fastapi.responses import JSONResponse

    tree = get_trajectory_tree(paper_id, db)
    has_rewrite = any(t["method_class"] == "rewrite" for t in tree)
    has_branch  = any(t["method_class"] == "branch"  for t in tree)

    return JSONResponse({
        "paper_id":       paper_id,
        "trajectory_count": len(tree),
        "has_rewrite":    has_rewrite,
        "has_branch":     has_branch,
        "trajectories":   tree,
    })


@router.get("/workspace/{paper_id}/reconstruct")
async def workspace_reconstruct(
    paper_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return full snapshot chain with divergence at each gate milestone."""
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect
    from fastapi.responses import JSONResponse
    result = reconstruct_chain(paper_id, db)
    if result["snapshot_count"] == 0:
        raise HTTPException(status_code=404, detail="No snapshots found for this paper.")
    return JSONResponse(result)


@router.get("/workspace/{paper_id}/integrity-summary")
async def workspace_integrity_summary(
    paper_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Single payload: gate status + divergence + leakage + contamination + latest seal."""
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect
    from fastapi.responses import JSONResponse

    # Gate status
    paper = db.execute(text(
        "SELECT id, title, abstract, gitgap_gap_id "
        "FROM `#__eaiou_papers` WHERE id = :id"
    ), {"id": paper_id}).mappings().first()
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    sections = db.execute(text(
        "SELECT section_name, section_content, section_notes "
        "FROM `#__eaiou_paper_sections` WHERE paper_id = :pid ORDER BY section_order ASC"
    ), {"pid": paper_id}).mappings().all()
    checks = _check_gateway(paper_id, dict(paper), [dict(s) for s in sections], db)

    # Latest snapshot divergence
    latest_snap = db.execute(text(
        "SELECT gate_code, divergence_from_prior, change_class, created_at "
        "FROM `#__eaiou_paper_snapshots` "
        "WHERE paper_id = :pid ORDER BY created_at DESC LIMIT 1"
    ), {"pid": paper_id}).mappings().first()

    # Leakage count
    leakage_count = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_leakage_flags` WHERE paper_id = :pid"
    ), {"pid": paper_id}).scalar() or 0

    # Contamination
    contamination = compute_contamination(paper_id, db)

    # Latest seal record
    seal = db.execute(text(
        "SELECT seal_hash, gate_valid, audit_status, sealed_at "
        "FROM `#__eaiou_integrity_seals` WHERE paper_id = :pid ORDER BY sealed_at DESC LIMIT 1"
    ), {"pid": paper_id}).mappings().first()

    return JSONResponse({
        "paper_id": paper_id,
        "gate": {"all_passed": all(c["passed"] for c in checks), "checks": checks},
        "latest_snapshot": dict(latest_snap) if latest_snap else None,
        "leakage_count": leakage_count,
        "contamination_score": contamination["contamination_score"],
        "seal": dict(seal) if seal else None,
    })


@router.get("/workspace/{paper_id}/coverage")
async def workspace_coverage(
    paper_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Research Coverage Analysis — runs claim extraction + appreciated gap scoring.
    Returns per-claim coverage status (covered / novel / needs_work) and summary.
    """
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect
    from fastapi.responses import JSONResponse
    from ..services.coverage import analyze_coverage

    paper = db.execute(text(
        "SELECT id, abstract FROM `#__eaiou_papers` WHERE id = :id"
    ), {"id": paper_id}).mappings().first()
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    sections = db.execute(text(
        "SELECT section_name, section_content "
        "FROM `#__eaiou_paper_sections` WHERE paper_id = :pid ORDER BY section_order ASC"
    ), {"pid": paper_id}).mappings().all()

    result = analyze_coverage(
        abstract=paper["abstract"] or "",
        sections=[dict(s) for s in sections],
    )
    return JSONResponse(result)


@router.get("/workspace/{paper_id}", response_class=HTMLResponse)
async def workspace(
    paper_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect

    paper = db.execute(text(
        "SELECT id, cosmoid, paper_uuid, title, abstract, keywords, "
        "       status, pipeline_stage, gitgap_gap_id, origin_type "
        "FROM `#__eaiou_papers` WHERE id = :id"
    ), {"id": paper_id}).mappings().first()

    if paper is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Paper not found")

    paper = dict(paper)

    # Fetch gap declaration text if gap is anchored
    if paper.get("gitgap_gap_id"):
        try:
            with httpx.Client(timeout=5) as client:
                resp = client.get(f"{GITGAP_API}/gaps/{paper['gitgap_gap_id']}")
                if resp.status_code == 200:
                    paper["gap_declaration"] = resp.json().get("declaration_text", "")
        except Exception:
            paper["gap_declaration"] = None

    sections = db.execute(text(
        "SELECT id, section_order, section_name, section_notes, "
        "       section_content, seeded_from "
        "FROM `#__eaiou_paper_sections` "
        "WHERE paper_id = :pid ORDER BY section_order ASC"
    ), {"pid": paper_id}).mappings().all()

    volley_history = db.execute(text(
        "SELECT round_number, finding_count, is_clean, findings_json, "
        "       author_response, audited_at, responded_at "
        "FROM `#__eaiou_volley_log` "
        "WHERE paper_id = :pid ORDER BY round_number ASC"
    ), {"pid": paper_id}).mappings().all()

    volley_history = [dict(v) for v in volley_history]
    last_volley = volley_history[-1] if volley_history else None
    volley_round = (last_volley["round_number"] + 1) if last_volley and last_volley.get("author_response") else (last_volley["round_number"] if last_volley else 1)

    # F2-A: Latest pending revision (drives the revision banner)
    latest_rev = db.execute(text(
        "SELECT round, instructions, due_at, requested_at "
        "FROM `#__eaiou_revisions` WHERE paper_id = :pid "
        "AND resubmitted_at IS NULL ORDER BY round DESC LIMIT 1"
    ), {"pid": paper_id}).mappings().first()

    # F2-D: Unread count for notification bell in base template
    unread_count = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_notifications` WHERE read_at IS NULL"
    )).scalar() or 0

    return templates.TemplateResponse(request, "author/workspace.html", {
        "current_user":    current_user,
        "paper":           paper,
        "sections":        [dict(s) for s in sections],
        "volley_history":  volley_history,
        "last_volley":     last_volley,
        "volley_round":    volley_round,
        "latest_revision": dict(latest_rev) if latest_rev else None,
        "unread_count":    unread_count,
        "csrf_token":      get_csrf_token(request),
    })


@router.post("/workspace/{paper_id}/resubmit")
async def workspace_resubmit(
    paper_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """F2-A: Author marks revision as complete — resets status to submitted."""
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect

    paper = db.execute(text(
        "SELECT id, status FROM `#__eaiou_papers` WHERE id = :id"
    ), {"id": paper_id}).mappings().first()

    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    if paper["status"] != "revision_requested":
        raise HTTPException(status_code=422, detail="Paper is not awaiting revision")

    now = datetime.now(timezone.utc)

    # Mark the pending revision record as resubmitted
    db.execute(text(
        "UPDATE `#__eaiou_revisions` SET resubmitted_at = :now "
        "WHERE paper_id = :pid AND resubmitted_at IS NULL "
        "ORDER BY round DESC LIMIT 1"
    ), {"now": now, "pid": paper_id})

    # Reset paper status to submitted for re-entry into the review queue
    db.execute(text(
        "UPDATE `#__eaiou_papers` SET status = 'submitted' WHERE id = :id"
    ), {"id": paper_id})

    db.commit()

    return RedirectResponse(
        url=f"/author/workspace/{paper_id}",
        status_code=303,
    )


# ── F2-D: Notifications ───────────────────────────────────────────────────────

@router.post("/notifications/read-all")
async def notifications_read_all(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Mark all unread notifications as read."""
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect

    db.execute(text(
        "UPDATE `#__eaiou_notifications` SET read_at = :now WHERE read_at IS NULL"
    ), {"now": datetime.now(timezone.utc)})
    db.commit()
    return RedirectResponse(url="/author/", status_code=303)


# ── Wireframe stub routes ─────────────────────────────────────────────────────

@router.get("/notifications", response_class=HTMLResponse)
async def notifications_page(request: Request, current_user=Depends(get_current_user)):
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect
    return templates.TemplateResponse(request, "views/14_notifications.html", {
        "current_user": current_user, "notification_count": 0,
    })


@router.get("/messages", response_class=HTMLResponse)
async def messages_page(request: Request, current_user=Depends(get_current_user)):
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect
    return templates.TemplateResponse(request, "views/01_communication_center.html", {
        "current_user": current_user, "notification_count": 0,
    })


@router.get("/messages-v2", response_class=HTMLResponse)
async def messages_v2_page(request: Request, current_user=Depends(get_current_user)):
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect
    return templates.TemplateResponse(request, "views/17_communication_center.html", {
        "current_user": current_user, "notification_count": 0,
    })


@router.get("/papers/{paper_id}/versions", response_class=HTMLResponse)
async def paper_versions_page(
    request: Request, paper_id: int, current_user=Depends(get_current_user),
):
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect
    return templates.TemplateResponse(request, "views/29_version_control.html", {
        "current_user": current_user, "paper_id": paper_id, "notification_count": 0,
    })


@router.get("/papers/{paper_id}/transparency", response_class=HTMLResponse)
async def paper_transparency_page(
    request: Request, paper_id: int, current_user=Depends(get_current_user),
):
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect
    return templates.TemplateResponse(request, "views/24_transparency.html", {
        "current_user": current_user, "paper_id": paper_id, "notification_count": 0,
    })


# ── F4-B: Author Withdrawal ────────────────────────────────────────────────────

@router.post("/papers/{paper_id}/withdraw")
async def withdraw_paper(
    paper_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    F4-B: Author withdrawal — tombstones the paper with tombstone_state='private'.
    Only permitted when status is 'submitted' or 'under_review'.
    """
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect

    paper = db.execute(text(
        "SELECT id, status, title FROM `#__eaiou_papers` WHERE id = :id"
    ), {"id": paper_id}).mappings().first()

    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    if paper["status"] not in ("submitted", "under_review"):
        raise HTTPException(
            status_code=422,
            detail=(
                f"Withdrawal not permitted at this stage. "
                f"Papers may only be withdrawn while 'submitted' or 'under_review'. "
                f"Current status: '{paper['status']}'."
            ),
        )

    now = datetime.now(timezone.utc)
    db.execute(text(
        "UPDATE `#__eaiou_papers` SET "
        "tombstone_state = 'private', "
        "tombstone_reason_code = 'author_deleted', "
        "tombstone_reason = 'Withdrawn by author via workspace UI.', "
        "tombstone_at = :now "
        "WHERE id = :id"
    ), {"now": now, "id": paper_id})
    db.commit()

    return RedirectResponse(url="/author/", status_code=303)


# ── File drawer ───────────────────────────────────────────────────────────────

@router.get("/drawer", response_class=HTMLResponse)
async def author_drawer(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not current_user:
        return RedirectResponse(url=f"/auth/login?next=/author/drawer", status_code=302)
    files = db.execute(
        text("""
            SELECT id, original_name, mime_type, file_size, uploaded_at
            FROM `#__eaiou_user_files`
            WHERE user_id = :u AND deleted_at IS NULL
            ORDER BY uploaded_at DESC
        """),
        {"u": current_user["id"]},
    ).mappings().all()
    return templates.TemplateResponse(
        request, "author/drawer.html",
        {
            "current_user": current_user,
            "files": files,
            "csrf_token": get_csrf_token(request),
        },
    )


@router.post("/drawer/{file_id}/delete")
async def author_drawer_delete(
    request: Request,
    file_id: int,
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=403, detail="Login required.")
    validate_csrf(request, csrf_token)
    # Soft-delete — only the owning user can delete their own files
    db.execute(
        text("UPDATE `#__eaiou_user_files` SET deleted_at = :now "
             "WHERE id = :id AND user_id = :u AND deleted_at IS NULL"),
        {"now": datetime.now(timezone.utc).replace(tzinfo=None), "id": file_id, "u": current_user["id"]},
    )
    db.commit()
    return RedirectResponse(url="/author/drawer", status_code=303)

