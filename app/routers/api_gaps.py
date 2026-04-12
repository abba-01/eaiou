"""
eaiou — Tier 6 JSON REST API: Gaps
7 endpoints: gap CRUD, linked papers, stalled items, external sync.

Router prefix: /api/v1
Tags:          api-gaps

Tables created in lifespan (main.py):
  #__eaiou_gaps       — id, domain, description, stall_type, status,
                         created_at, updated_at, created_by
  #__eaiou_gap_papers — gap_id, paper_id, linked_at

Live schema verified 2026-04-12:
  #__eaiou_papers — gitgap_gap_id INT UNSIGNED column EXISTS
"""

import hashlib
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..deps import (
    require_auth,
    require_editor,
    require_admin,
)
from ..services.api_log import log_api_call

router = APIRouter(prefix="/api/v1", tags=["api-gaps"])

# ── Whitelisted patch fields ──────────────────────────────────────────────────

_GAP_PATCH = frozenset({"domain", "description", "stall_type", "status"})


# ── Pydantic models ───────────────────────────────────────────────────────────

class GapCreate(BaseModel):
    domain: str
    description: str
    stall_type: Optional[str] = None
    linked_paper_ids: List[int] = []


class GapUpdate(BaseModel):
    domain: Optional[str] = None
    description: Optional[str] = None
    stall_type: Optional[str] = None
    status: Optional[str] = None


class GapSync(BaseModel):
    gaps: list  # [{domain, description, stall_type, external_id=None}]


# ── 1. GET /gaps/{id} — gap.get (PUBLIC) ─────────────────────────────────────

@router.get("/gaps/{id}")
async def gap_get(
    id: int,
    db: Session = Depends(get_db),
):
    row = db.execute(text(
        "SELECT id, domain, description, stall_type, status, "
        "created_at, updated_at, created_by "
        "FROM `#__eaiou_gaps` WHERE id = :id"
    ), {"id": id}).mappings().first()

    if row is None:
        raise HTTPException(status_code=404, detail="Gap not found.")

    linked_count = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_gap_papers` WHERE gap_id = :gid"
    ), {"gid": id}).scalar() or 0

    result = dict(row)
    result["linked_paper_count"] = linked_count
    return result


# ── 2. GET /gaps — gap.list (PUBLIC) ─────────────────────────────────────────

@router.get("/gaps")
async def gap_list(
    db: Session = Depends(get_db),
):
    rows = db.execute(text(
        "SELECT g.id, g.domain, g.description, g.stall_type, g.status, "
        "g.created_at, g.updated_at, "
        "COUNT(gp.paper_id) AS linked_paper_count "
        "FROM `#__eaiou_gaps` g "
        "LEFT JOIN `#__eaiou_gap_papers` gp ON gp.gap_id = g.id "
        "GROUP BY g.id "
        "ORDER BY linked_paper_count DESC"
    )).mappings().all()

    return [dict(r) for r in rows]


# ── 3. POST /gaps — gap.create ────────────────────────────────────────────────

@router.post("/gaps")
async def gap_create(
    body: GapCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    now = datetime.now(timezone.utc)

    db.execute(text(
        "INSERT INTO `#__eaiou_gaps` "
        "(domain, description, stall_type, status, created_at, created_by) "
        "VALUES (:domain, :desc, :stype, 'open', :now, :uid)"
    ), {
        "domain": body.domain,
        "desc":   body.description,
        "stype":  body.stall_type,
        "now":    now,
        "uid":    current_user["id"],
    })
    db.commit()

    gap_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()

    # Link papers if provided
    for paper_id in body.linked_paper_ids:
        db.execute(text(
            "INSERT IGNORE INTO `#__eaiou_gap_papers` (gap_id, paper_id, linked_at) "
            "VALUES (:gid, :pid, :now)"
        ), {"gid": gap_id, "pid": paper_id, "now": now})
    if body.linked_paper_ids:
        db.commit()

    log_api_call(
        db, "/api/v1/gaps", "POST",
        hashlib.sha256(str(gap_id).encode()).hexdigest(), 201,
    )

    return JSONResponse(
        status_code=201,
        content={"gap_id": gap_id, "domain": body.domain},
    )


# ── 4. PATCH /gaps/{id} — gap.update ─────────────────────────────────────────

@router.patch("/gaps/{id}")
async def gap_update(
    id: int,
    body: GapUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    body_data = body.model_dump(exclude_none=True)
    sets = {k: v for k, v in body_data.items() if k in _GAP_PATCH}

    if not sets:
        raise HTTPException(status_code=422, detail="No valid fields to update.")

    now = datetime.now(timezone.utc)
    set_clause = ", ".join(f"`{k}` = :{k}" for k in sets)
    sets["_id"] = id
    sets["_now"] = now

    result = db.execute(text(
        f"UPDATE `#__eaiou_gaps` SET {set_clause}, updated_at = :_now WHERE id = :_id"
    ), sets)
    db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Gap not found.")

    log_api_call(
        db, f"/api/v1/gaps/{id}", "PATCH",
        hashlib.sha256(str(id).encode()).hexdigest(), 200,
    )

    return {"id": id, "updated": True}


# ── 5. GET /gaps/{id}/papers — gap.get_linked_papers (PUBLIC) ────────────────

@router.get("/gaps/{id}/papers")
async def gap_get_linked_papers(
    id: int,
    db: Session = Depends(get_db),
):
    # Verify gap exists
    gap = db.execute(text(
        "SELECT id FROM `#__eaiou_gaps` WHERE id = :id"
    ), {"id": id}).fetchone()

    if gap is None:
        raise HTTPException(status_code=404, detail="Gap not found.")

    rows = db.execute(text(
        "SELECT p.id, p.title, p.status, p.q_signal "
        "FROM `#__eaiou_gap_papers` gp "
        "JOIN `#__eaiou_papers` p ON p.id = gp.paper_id AND p.tombstone_state IS NULL "
        "WHERE gp.gap_id = :gid "
        "ORDER BY p.q_signal IS NULL ASC, p.q_signal DESC"
    ), {"gid": id}).mappings().all()

    return [dict(r) for r in rows]


# ── 6. GET /gaps/{id}/stalled — gap.get_stalled_items (PUBLIC) ───────────────

@router.get("/gaps/{id}/stalled")
async def gap_get_stalled_items(
    id: int,
    db: Session = Depends(get_db),
):
    # Verify gap exists
    gap = db.execute(text(
        "SELECT id FROM `#__eaiou_gaps` WHERE id = :id"
    ), {"id": id}).fetchone()

    if gap is None:
        raise HTTPException(status_code=404, detail="Gap not found.")

    # gitgap_gap_id exists on #__eaiou_papers (confirmed in schema check)
    rows = db.execute(text(
        "SELECT id AS paper_id, title, status "
        "FROM `#__eaiou_papers` "
        "WHERE gitgap_gap_id = :gid AND tombstone_state IS NULL "
        "ORDER BY id"
    ), {"gid": id}).mappings().all()

    # Fall back to gap_papers join if gitgap direct query returns nothing
    stalled = [dict(r) for r in rows]

    if not stalled:
        fallback = db.execute(text(
            "SELECT p.id AS paper_id, p.title, p.status "
            "FROM `#__eaiou_papers` p "
            "JOIN `#__eaiou_gap_papers` gp ON gp.paper_id = p.id "
            "WHERE gp.gap_id = :gid AND p.tombstone_state IS NULL "
            "ORDER BY p.id"
        ), {"gid": id}).mappings().all()
        stalled = [dict(r) for r in fallback]

    return {"gap_id": id, "stalled_items": stalled}


# ── 7. POST /gaps/sync — gap.sync_external ────────────────────────────────────

@router.post("/gaps/sync")
async def gap_sync_external(
    body: GapSync,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    now = datetime.now(timezone.utc)
    synced_count = 0

    for entry in body.gaps:
        if isinstance(entry, dict):
            domain = entry.get("domain", "")
            description = entry.get("description", "")
            stall_type = entry.get("stall_type")
        else:
            domain = getattr(entry, "domain", "")
            description = getattr(entry, "description", "")
            stall_type = getattr(entry, "stall_type", None)

        if not domain:
            continue

        result = db.execute(text(
            "INSERT IGNORE INTO `#__eaiou_gaps` "
            "(domain, description, stall_type, status, created_at, created_by) "
            "VALUES (:domain, :desc, :stype, 'open', :now, :uid)"
        ), {
            "domain": domain,
            "desc":   description,
            "stype":  stall_type,
            "now":    now,
            "uid":    current_user["id"],
        })
        synced_count += result.rowcount

    db.commit()

    log_api_call(
        db, "/api/v1/gaps/sync", "POST",
        hashlib.sha256(f"sync|{now.isoformat()}".encode()).hexdigest(), 200,
    )

    return {"synced_count": synced_count}
