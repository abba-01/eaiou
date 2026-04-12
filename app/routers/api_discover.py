"""
eaiou — Tier 5 JSON REST API: Discovery + Search
7 endpoints: search, unspace, discover/papers, ideas, gaps, trends,
collaboration.

Router prefix: /api/v1
Tags:          api-discover

TB RULE: All list endpoints ORDER BY q_signal IS NULL ASC, q_signal DESC.
         If sort param contains date/time keywords → 400 Temporal Blindness.

Live schema verified 2026-04-12:
  #__eaiou_papers   — id, title, abstract, keywords, authorship_mode, status,
      q_signal, q_overall, ai_disclosure_level, tombstone_state, created,
      gitgap_gap_id  (exists), category does NOT exist
  #__eaiou_remsearch — id, paper_id, citation_title, citation_source,
      citation_link, source_type, used, fulltext_notes
"""

import hashlib
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..deps import optional_auth

router = APIRouter(prefix="/api/v1", tags=["api-discover"])

# ── Sealed fields — strip from all public responses ──────────────────────────

_SEALED = frozenset({
    "submission_sealed_at", "acceptance_sealed_at", "publication_sealed_at",
    "attestation_sealed_at", "attestation_json", "sealed_by", "submission_hash",
})

_TB_KEYWORDS = frozenset({
    "date", "created", "submitted_at", "created_at", "modified", "modified_at",
    "submission_sealed_at", "acceptance_sealed_at", "publication_sealed_at",
    "timestamp", "time",
})


def _strip_sealed(d: dict) -> dict:
    return {k: v for k, v in d.items() if k not in _SEALED}


def _like_escape(s: str) -> str:
    """Escape LIKE special characters to prevent wildcard injection."""
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _check_sort(sort: Optional[str]):
    if sort:
        sort_lower = sort.lower()
        for kw in _TB_KEYWORDS:
            if kw in sort_lower:
                raise HTTPException(
                    status_code=400,
                    detail=f"Temporal Blindness: sort by '{sort}' is not allowed. Sort by q_signal only.",
                )


# ── 1. GET /search — search.query (PUBLIC) ────────────────────────────────────

@router.get("/search")
async def search_query(
    q: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None),
    authorship_mode: Optional[str] = Query(None),
    has_ai: Optional[bool] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    _check_sort(sort)

    q_pattern = f"%{_like_escape(q)}%"
    where_clauses = [
        "tombstone_state IS NULL",
        "(title LIKE :q ESCAPE '\\\\' OR abstract LIKE :q ESCAPE '\\\\' OR keywords LIKE :q ESCAPE '\\\\')",
    ]
    params: dict = {"q": q_pattern, "limit": limit, "offset": offset}

    if authorship_mode:
        where_clauses.append("authorship_mode = :authorship_mode")
        params["authorship_mode"] = authorship_mode

    if has_ai is not None:
        if has_ai:
            where_clauses.append(
                "ai_disclosure_level IS NOT NULL AND ai_disclosure_level != 'none'"
            )
        else:
            where_clauses.append(
                "(ai_disclosure_level IS NULL OR ai_disclosure_level = 'none')"
            )

    where_sql = " AND ".join(where_clauses)

    total = db.execute(text(
        f"SELECT COUNT(*) FROM `#__eaiou_papers` WHERE {where_sql}"
    ), params).scalar() or 0

    rows = db.execute(text(
        f"SELECT id, title, abstract, keywords, authorship_mode, status, "
        f"q_signal, q_overall, ai_disclosure_level, author_name, orcid, doi "
        f"FROM `#__eaiou_papers` WHERE {where_sql} "
        f"ORDER BY q_signal IS NULL ASC, q_signal DESC "
        f"LIMIT :limit OFFSET :offset"
    ), params).mappings().all()

    results = [_strip_sealed(dict(r)) for r in rows]

    return {
        "results": results,
        "total":   total,
        "limit":   limit,
        "offset":  offset,
    }


# ── 2. GET /search/unspace — search.unspace (PUBLIC) ─────────────────────────

@router.get("/search/unspace")
async def search_unspace(
    q: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    where_clauses = ["used = 0"]
    params: dict = {"limit": limit, "offset": offset}

    if q:
        where_clauses.append("(citation_title LIKE :q ESCAPE '\\\\' OR fulltext_notes LIKE :q ESCAPE '\\\\')")
        params["q"] = f"%{_like_escape(q)}%"

    where_sql = " AND ".join(where_clauses)

    total = db.execute(text(
        f"SELECT COUNT(*) FROM `#__eaiou_remsearch` WHERE {where_sql}"
    ), params).scalar() or 0

    rows = db.execute(text(
        f"SELECT id, paper_id, citation_title, citation_source, citation_link, "
        f"source_type, reason_unused, fulltext_notes, created "
        f"FROM `#__eaiou_remsearch` WHERE {where_sql} "
        f"ORDER BY id LIMIT :limit OFFSET :offset"
    ), params).mappings().all()

    return {
        "items": [dict(r) for r in rows],
        "total": total,
    }


# ── 3. GET /discover/papers — discover.papers (PUBLIC) ───────────────────────

@router.get("/discover/papers")
async def discover_papers(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    total = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_papers` "
        "WHERE status = 'published' AND tombstone_state IS NULL"
    )).scalar() or 0

    rows = db.execute(text(
        "SELECT id, title, abstract, keywords, authorship_mode, status, "
        "q_signal, q_overall, ai_disclosure_level, author_name, orcid, doi "
        "FROM `#__eaiou_papers` "
        "WHERE status = 'published' AND tombstone_state IS NULL "
        "ORDER BY q_signal IS NULL ASC, q_signal DESC "
        "LIMIT :limit OFFSET :offset"
    ), {"limit": limit, "offset": offset}).mappings().all()

    return {
        "papers": [_strip_sealed(dict(r)) for r in rows],
        "total":  total,
        "limit":  limit,
        "offset": offset,
    }


# ── 4. GET /discover/ideas — discover.ideas (PUBLIC) ─────────────────────────

@router.get("/discover/ideas")
async def discover_ideas(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    total = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_remsearch` WHERE used = 0"
    )).scalar() or 0

    rows = db.execute(text(
        "SELECT r.id, r.paper_id, r.citation_title, r.citation_source, "
        "r.fulltext_notes, p.title AS source_paper_title "
        "FROM `#__eaiou_remsearch` r "
        "LEFT JOIN `#__eaiou_papers` p ON p.id = r.paper_id AND p.tombstone_state IS NULL "
        "WHERE r.used = 0 "
        "ORDER BY r.id "
        "LIMIT :limit OFFSET :offset"
    ), {"limit": limit, "offset": offset}).mappings().all()

    ideas = []
    for r in rows:
        ideas.append({
            "source_paper_id":    r["paper_id"],
            "source_paper_title": r["source_paper_title"],
            "idea_title":         r["citation_title"],
            "idea_notes":         r["fulltext_notes"],
            "entropy_score":      1.0,
            "origin_type":        "nottopic",
        })

    return {"ideas": ideas, "total": total}


# ── 5. GET /discover/gaps — discover.gaps (PUBLIC) ────────────────────────────

@router.get("/discover/gaps")
async def discover_gaps(
    db: Session = Depends(get_db),
):
    # Group stalled papers by ai_disclosure_level as domain proxy
    # (no category column on papers in live schema)
    rows = db.execute(text(
        "SELECT "
        "  COALESCE(ai_disclosure_level, 'none') AS domain, "
        "  COUNT(*) AS stall_count "
        "FROM `#__eaiou_papers` "
        "WHERE status IN ('rejected', 'under_review') "
        "GROUP BY domain "
        "ORDER BY stall_count DESC"
    )).mappings().all()

    return {"domains": [dict(r) for r in rows]}


# ── 6. GET /discover/trends — discover.trends (PUBLIC) ───────────────────────

@router.get("/discover/trends")
async def discover_trends(
    db: Session = Depends(get_db),
):
    rows = db.execute(text(
        "SELECT keywords FROM `#__eaiou_papers` "
        "WHERE status != 'draft' "
        "AND keywords IS NOT NULL AND keywords != '' "
        "AND created > NOW() - INTERVAL 90 DAY"
    )).fetchall()

    freq: dict = {}
    for (kw_str,) in rows:
        if kw_str:
            for kw in kw_str.split(","):
                kw = kw.strip().lower()
                if kw:
                    freq[kw] = freq.get(kw, 0) + 1

    sorted_trends = sorted(freq.items(), key=lambda x: -x[1])[:20]

    return {
        "trends": [{"keyword": kw, "count": cnt} for kw, cnt in sorted_trends]
    }


# ── 7. GET /discover/collaboration — discover.collaboration (PUBLIC) ──────────

@router.get("/discover/collaboration")
async def discover_collaboration(
    collab_type: Optional[str] = Query(None),
    interest_level: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    # collab_open column does not exist in live schema — return empty gracefully
    # with a note for future migration
    return {
        "papers": [],
        "note": "Collaboration matching not yet configured. collab_open column pending schema migration.",
    }
