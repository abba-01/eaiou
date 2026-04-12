"""
eaiou — Tier 4 JSON REST API: Transparency
5 endpoints: transparency metadata, remsearch sources, completeness.

Router prefix: /api/v1
Tags:          api-transparency

Live schema verified 2026-04-12:
  #__eaiou_papers    — NO transp_* columns in live schema; treat as null
  #__eaiou_remsearch — id, paper_id, citation_title, citation_source,
      citation_link, source_type, used, reason_unused, fulltext_notes,
      state, created, created_by, modified, modified_by
"""

import hashlib
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..deps import (
    get_current_user,
    require_auth,
    require_editor,
    optional_auth,
)
from ..services.api_log import log_api_call

router = APIRouter(prefix="/api/v1", tags=["api-transparency"])

# ── Whitelisted patch fields ──────────────────────────────────────────────────

# No transp_* columns exist in live schema; patch endpoint accepts nothing for now
# but is structured to add columns when migration adds them.
_PAPER_TRANSP_PATCH = frozenset()  # empty — no live transparency cols on papers


# ── Pydantic models ───────────────────────────────────────────────────────────

class TransparencyUpdate(BaseModel):
    # Placeholders — will be meaningful once transp_* columns land in schema
    transp_methods: Optional[str] = None
    transp_limitations: Optional[str] = None


class RemSearchCreate(BaseModel):
    citation_title: str
    citation_source: Optional[str] = None
    citation_link: Optional[str] = None
    source_type: str
    used: int = 1
    reason_unused: Optional[str] = None
    fulltext_notes: Optional[str] = None


class RemSearchUpdate(BaseModel):
    used: int = 0
    reason_unused: str


# ── 1. GET /papers/{paper_id}/transparency — transparency.get (PUBLIC) ────────

@router.get("/papers/{paper_id}/transparency")
async def transparency_get(
    paper_id: int,
    db: Session = Depends(get_db),
):
    paper = db.execute(text(
        "SELECT id FROM `#__eaiou_papers` "
        "WHERE id = :pid AND tombstone_state IS NULL"
    ), {"pid": paper_id}).fetchone()

    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found.")

    sources = db.execute(text(
        "SELECT id, citation_title, citation_source, citation_link, "
        "source_type, used, reason_unused, fulltext_notes, state, created "
        "FROM `#__eaiou_remsearch` WHERE paper_id = :pid ORDER BY id"
    ), {"pid": paper_id}).mappings().all()

    source_list = [dict(s) for s in sources]
    total = len(source_list)
    unused_count = sum(1 for s in source_list if s.get("used") == 0)

    return {
        "paper_id":          paper_id,
        "sources":           source_list,
        "sources_count":     total,
        "unused_count":      unused_count,
        # transp_* columns not yet in live schema — return nulls
        "complete":          None,
        "lastcheck":         None,
        "methods":           None,
        "limitations":       None,
    }


# ── 2. PATCH /papers/{paper_id}/transparency — transparency.update ────────────

@router.patch("/papers/{paper_id}/transparency")
async def transparency_update(
    paper_id: int,
    body: TransparencyUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    # Verify paper exists
    paper = db.execute(text(
        "SELECT id, author_name FROM `#__eaiou_papers` "
        "WHERE id = :pid AND tombstone_state IS NULL"
    ), {"pid": paper_id}).mappings().first()

    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found.")

    # ACL: AUTHOR (own paper) or EDITOR
    groups = set(current_user.get("groups", []))
    is_editor_plus = bool({"editor", "admin"} & groups)

    if not is_editor_plus:
        if paper["author_name"] != current_user["name"]:
            raise HTTPException(status_code=403, detail="You do not own this paper.")

    # No live transp_* columns exist yet — return graceful no-op
    body_data = body.model_dump(exclude_none=True)
    sets = {k: v for k, v in body_data.items() if k in _PAPER_TRANSP_PATCH}

    if sets:
        now = datetime.now(timezone.utc)
        set_clause = ", ".join(f"`{k}` = :{k}" for k in sets)
        sets["_pid"] = paper_id
        sets["_now"] = now
        db.execute(text(
            f"UPDATE `#__eaiou_papers` SET {set_clause}, modified = :_now WHERE id = :_pid"
        ), sets)
        db.commit()

    log_api_call(
        db, f"/api/v1/papers/{paper_id}/transparency", "PATCH",
        hashlib.sha256(str(paper_id).encode()).hexdigest(), 200,
    )

    return {"paper_id": paper_id, "updated": True}


# ── 3. POST /papers/{paper_id}/remsearch — transparency.add_source ────────────

@router.post("/papers/{paper_id}/remsearch")
async def transparency_add_source(
    paper_id: int,
    body: RemSearchCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    # Verify paper exists
    paper = db.execute(text(
        "SELECT id FROM `#__eaiou_papers` "
        "WHERE id = :pid AND tombstone_state IS NULL"
    ), {"pid": paper_id}).fetchone()

    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found.")

    now = datetime.now(timezone.utc)

    db.execute(text(
        "INSERT INTO `#__eaiou_remsearch` "
        "(paper_id, citation_title, citation_source, citation_link, "
        " source_type, used, reason_unused, fulltext_notes, "
        " state, created, created_by) "
        "VALUES (:pid, :title, :source, :link, "
        "        :stype, :used, :reason, :notes, "
        "        1, :now, :uid)"
    ), {
        "pid":    paper_id,
        "title":  body.citation_title,
        "source": body.citation_source,
        "link":   body.citation_link,
        "stype":  body.source_type,
        "used":   body.used,
        "reason": body.reason_unused,
        "notes":  body.fulltext_notes,
        "now":    now,
        "uid":    current_user["id"],
    })
    db.commit()

    new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()

    log_api_call(
        db, f"/api/v1/papers/{paper_id}/remsearch", "POST",
        hashlib.sha256(str(paper_id).encode()).hexdigest(), 201,
    )

    return JSONResponse(
        status_code=201,
        content={"remsearch_id": new_id, "paper_id": paper_id},
    )


# ── 4. PATCH /remsearch/{id} — transparency.mark_unused ──────────────────────

@router.patch("/remsearch/{id}")
async def transparency_mark_unused(
    id: int,
    body: RemSearchUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    now = datetime.now(timezone.utc)

    result = db.execute(text(
        "UPDATE `#__eaiou_remsearch` "
        "SET used = :used, reason_unused = :reason, modified = :now, modified_by = :uid "
        "WHERE id = :id"
    ), {
        "used":   body.used,
        "reason": body.reason_unused,
        "now":    now,
        "uid":    current_user["id"],
        "id":     id,
    })
    db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="RemSearch record not found.")

    log_api_call(
        db, f"/api/v1/remsearch/{id}", "PATCH",
        hashlib.sha256(str(id).encode()).hexdigest(), 200,
    )

    return {"id": id, "used": body.used}


# ── 5. GET /papers/{paper_id}/transparency/completeness ───────────────────────

@router.get("/papers/{paper_id}/transparency/completeness")
async def transparency_completeness(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    # Verify paper exists
    paper = db.execute(text(
        "SELECT id, author_name, title, abstract, keywords, ai_disclosure_level "
        "FROM `#__eaiou_papers` WHERE id = :pid AND tombstone_state IS NULL"
    ), {"pid": paper_id}).mappings().first()

    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found.")

    # ACL: AUTHOR or EDITOR
    groups = set(current_user.get("groups", []))
    is_editor_plus = bool({"editor", "admin"} & groups)

    if not is_editor_plus:
        if paper["author_name"] != current_user["name"]:
            raise HTTPException(status_code=403, detail="Access denied.")

    # Count all sources
    sources_count = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_remsearch` WHERE paper_id = :pid"
    ), {"pid": paper_id}).scalar() or 0

    # Count excluded sources without reason
    excluded_without_reason = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_remsearch` "
        "WHERE paper_id = :pid AND used = 0 "
        "AND (reason_unused IS NULL OR reason_unused = '')"
    ), {"pid": paper_id}).scalar() or 0

    # Check which paper fields are missing
    missing = []
    if not paper["abstract"]:
        missing.append("abstract")
    if not paper["keywords"]:
        missing.append("keywords")
    if not paper["ai_disclosure_level"]:
        missing.append("ai_disclosure_level")
    if excluded_without_reason > 0:
        missing.append("remsearch_exclusion_reasons")

    complete = (len(missing) == 0)

    return {
        "paper_id":               paper_id,
        "complete":               complete,
        "missing":                missing,
        "sources_count":          sources_count,
        "excluded_without_reason": excluded_without_reason,
    }
