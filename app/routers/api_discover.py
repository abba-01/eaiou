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
    """Cross-domain discovery: unused refs + papers tagged rs:CrossDomain,
    rs:OpenQuestion, rs:NotTopic (the three discovery-signal tags)."""

    # Source 1: unused references (existing)
    ref_rows = db.execute(text(
        "SELECT r.id, r.paper_id, r.citation_title, r.citation_source, "
        "r.fulltext_notes, p.title AS source_paper_title "
        "FROM `#__eaiou_remsearch` r "
        "LEFT JOIN `#__eaiou_papers` p ON p.id = r.paper_id AND p.tombstone_state IS NULL "
        "WHERE r.used = 0 "
        "ORDER BY r.id "
        "LIMIT :limit OFFSET :offset"
    ), {"limit": limit, "offset": offset}).mappings().all()

    ideas = []
    for r in ref_rows:
        ideas.append({
            "source_paper_id":    r["paper_id"],
            "source_paper_title": r["source_paper_title"],
            "idea_title":         r["citation_title"],
            "idea_notes":         r["fulltext_notes"],
            "origin_type":        "remsearch",
        })

    # Source 2: RS-tagged discovery signals
    tag_rows = db.execute(text(
        "SELECT t.id, t.paper_id, t.tag, t.subtype, t.notes, "
        "p.title AS paper_title "
        "FROM `#__eaiou_paper_tags` t "
        "JOIN `#__eaiou_papers` p ON p.id = t.paper_id "
        "WHERE t.tag IN ('rs:CrossDomain', 'rs:OpenQuestion', 'rs:NotTopic') "
        "AND t.tag_resolved = 0 AND t.visibility = 'public' "
        "AND p.tombstone_state IS NULL "
        "ORDER BY t.created_at DESC "
        "LIMIT :limit OFFSET :offset"
    ), {"limit": limit, "offset": offset}).mappings().all()

    for r in tag_rows:
        ideas.append({
            "source_paper_id":    r["paper_id"],
            "source_paper_title": r["paper_title"],
            "idea_title":         f"{r['tag']}" + (f":{r['subtype']}" if r["subtype"] else ""),
            "idea_notes":         r["notes"],
            "origin_type":        r["tag"],
        })

    total_refs = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_remsearch` WHERE used = 0"
    )).scalar() or 0
    total_tags = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_paper_tags` t "
        "JOIN `#__eaiou_papers` p ON p.id = t.paper_id "
        "WHERE t.tag IN ('rs:CrossDomain', 'rs:OpenQuestion', 'rs:NotTopic') "
        "AND t.tag_resolved = 0 AND t.visibility = 'public' "
        "AND p.tombstone_state IS NULL"
    )).scalar() or 0

    return {"ideas": ideas, "total": total_refs + total_tags}


# ── 5. GET /discover/gaps — discover.gaps (PUBLIC) ────────────────────────────

@router.get("/discover/gaps")
async def discover_gaps(
    tag: Optional[str] = Query(None, description="Filter by RS tag (e.g. rs:Stalled)"),
    db: Session = Depends(get_db),
):
    """Gap map: active RS tags grouped by tag + subtype, with stall counts."""
    where = [
        "t.tag_resolved = 0",
        "t.visibility = 'public'",
        "p.tombstone_state IS NULL",
    ]
    params: dict = {}

    if tag:
        where.append("t.tag = :tag")
        params["tag"] = tag

    where_sql = " AND ".join(where)

    rows = db.execute(text(
        f"SELECT t.tag, t.subtype, COUNT(*) AS count "
        f"FROM `#__eaiou_paper_tags` t "
        f"JOIN `#__eaiou_papers` p ON p.id = t.paper_id "
        f"WHERE {where_sql} "
        f"GROUP BY t.tag, t.subtype "
        f"ORDER BY count DESC"
    ), params).mappings().all()

    return {"gaps": [dict(r) for r in rows]}


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
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Papers whose authors are seeking collaboration (rs:LookCollab tag)."""
    rows = db.execute(text(
        "SELECT t.id AS tag_id, t.paper_id, t.notes, t.created_at, "
        "p.title AS paper_title, p.author_name, p.orcid "
        "FROM `#__eaiou_paper_tags` t "
        "JOIN `#__eaiou_papers` p ON p.id = t.paper_id "
        "WHERE t.tag = 'rs:LookCollab' AND t.tag_resolved = 0 "
        "AND t.visibility = 'public' AND p.tombstone_state IS NULL "
        "ORDER BY t.created_at DESC "
        "LIMIT :limit OFFSET :offset"
    ), {"limit": limit, "offset": offset}).mappings().all()

    total = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_paper_tags` t "
        "JOIN `#__eaiou_papers` p ON p.id = t.paper_id "
        "WHERE t.tag = 'rs:LookCollab' AND t.tag_resolved = 0 "
        "AND t.visibility = 'public' AND p.tombstone_state IS NULL"
    )).scalar() or 0

    return {"papers": [dict(r) for r in rows], "total": total}
