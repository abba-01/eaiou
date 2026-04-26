"""
eaiou — RS (Research State) tag router
Author-applied, bottom-up signals indexed for discovery.
Vocabulary defined in SSOT Section 7.

Authors can add/resolve tags on their own papers.
Editors can add/resolve tags on any paper.
Public can view public-visibility tags.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..deps import get_current_user, require_auth
from ..security import get_csrf_token, validate_csrf

router = APIRouter(prefix="/tags", tags=["tags"])
templates = Jinja2Templates(directory="app/templates")

# ── Valid RS tags (from SSOT Section 7) ──────────────────────────────────────

RS_TAGS = {
    "rs:LookCollab":          {"label": "Seeking collaboration", "subtypes": []},
    "rs:NotTopic":            {"label": "Not on topic", "subtypes": [
        "AnotherField", "FutureWork", "Tangent",
        "AbandonedHypothesis", "Contradiction", "NullResult",
    ]},
    "rs:Stalled":             {"label": "Work blocked", "subtypes": [
        "Literature", "Data", "Analysis", "Writing", "Funding",
        "Equipment", "Methodology", "Collaboration", "Ethics",
        "Compute", "Reproducibility",
    ]},
    "rs:ForLater":            {"label": "Archived for future paper", "subtypes": []},
    "rs:OpenQuestion":        {"label": "Raised but not answered", "subtypes": []},
    "rs:NullResult":          {"label": "Null/negative result", "subtypes": []},
    "rs:Replication":         {"label": "Replication study", "subtypes": []},
    "rs:CrossDomain":         {"label": "Cross-domain value", "subtypes": []},
    "rs:Exploratory":         {"label": "Speculative, not yet formal", "subtypes": []},
    "rs:Contradiction":       {"label": "Contradicts existing literature", "subtypes": []},
    "rs:UnderReconsideration": {"label": "Author reconsidering", "subtypes": []},
}

VISIBILITY_LEVELS = ("public", "reviewers", "editorial", "private")


def _can_tag_paper(user: dict, paper_row, db: Session) -> bool:
    """Check if user can tag this paper (author of paper or editor/admin)."""
    groups = set(user.get("groups", []))
    if {"admin", "editor"} & groups:
        return True
    if paper_row and paper_row["created_by"] == user["id"]:
        return True
    return False


# ── GET /tags/paper/{paper_id} — list tags for a paper (JSON) ────────────────

@router.get("/paper/{paper_id}")
async def get_paper_tags(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return tags for a paper, filtered by visibility."""
    if current_user:
        groups = set(current_user.get("groups", []))
        if {"admin", "editor"} & groups:
            vis_filter = "1=1"
        elif "reviewer" in groups:
            vis_filter = "visibility IN ('public', 'reviewers')"
        else:
            vis_filter = "visibility IN ('public')"
    else:
        vis_filter = "visibility = 'public'"

    rows = db.execute(text(f"""
        SELECT id, tag, subtype, visibility, tag_resolved, notes,
               created_at, resolved_at
        FROM `#__eaiou_paper_tags`
        WHERE paper_id = :pid AND {vis_filter}
        ORDER BY tag_resolved ASC, created_at DESC
    """), {"pid": paper_id}).mappings().all()

    return {"paper_id": paper_id, "tags": [dict(r) for r in rows]}


# ── POST /tags/paper/{paper_id}/add — add a tag ─────────────────────────────

@router.post("/paper/{paper_id}/add")
async def add_tag(
    request: Request,
    paper_id: int,
    tag: str = Form(...),
    subtype: str = Form(""),
    visibility: str = Form("public"),
    notes: str = Form(""),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    validate_csrf(request, csrf_token)

    if tag not in RS_TAGS:
        raise HTTPException(status_code=422, detail=f"Unknown tag: {tag}")

    if visibility not in VISIBILITY_LEVELS:
        raise HTTPException(status_code=422, detail=f"Invalid visibility: {visibility}")

    valid_subtypes = RS_TAGS[tag]["subtypes"]
    subtype = subtype.strip() or None
    if subtype and valid_subtypes and subtype not in valid_subtypes:
        raise HTTPException(status_code=422, detail=f"Invalid subtype '{subtype}' for {tag}")

    paper = db.execute(
        text("SELECT id, created_by FROM `#__eaiou_papers` WHERE id = :id AND tombstone_state IS NULL"),
        {"id": paper_id},
    ).mappings().first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")

    if not _can_tag_paper(current_user, paper, db):
        raise HTTPException(status_code=403, detail="You can only tag your own papers.")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db.execute(text("""
        INSERT INTO `#__eaiou_paper_tags`
            (paper_id, tag, subtype, visibility, notes, created_at, created_by)
        VALUES (:pid, :tag, :sub, :vis, :notes, :now, :uid)
    """), {
        "pid": paper_id, "tag": tag, "sub": subtype,
        "vis": visibility, "notes": notes.strip() or None,
        "now": now, "uid": current_user["id"],
    })
    db.commit()

    referer = request.headers.get("referer", f"/author/workspace/{paper_id}")
    return RedirectResponse(url=referer, status_code=303)


# ── POST /tags/{tag_id}/resolve — mark a tag as resolved ────────────────────

@router.post("/{tag_id}/resolve")
async def resolve_tag(
    request: Request,
    tag_id: int,
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    validate_csrf(request, csrf_token)

    tag_row = db.execute(text("""
        SELECT t.id, t.paper_id, p.created_by
        FROM `#__eaiou_paper_tags` t
        JOIN `#__eaiou_papers` p ON p.id = t.paper_id
        WHERE t.id = :tid
    """), {"tid": tag_id}).mappings().first()

    if not tag_row:
        raise HTTPException(status_code=404, detail="Tag not found.")

    if not _can_tag_paper(current_user, tag_row, db):
        raise HTTPException(status_code=403, detail="Cannot resolve this tag.")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db.execute(text("""
        UPDATE `#__eaiou_paper_tags`
        SET tag_resolved = 1, resolved_at = :now
        WHERE id = :tid
    """), {"now": now, "tid": tag_id})
    db.commit()

    referer = request.headers.get("referer", f"/author/workspace/{tag_row['paper_id']}")
    return RedirectResponse(url=referer, status_code=303)


# ── POST /tags/{tag_id}/delete — remove a tag (author/editor only) ──────────

@router.post("/{tag_id}/delete")
async def delete_tag(
    request: Request,
    tag_id: int,
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    validate_csrf(request, csrf_token)

    tag_row = db.execute(text("""
        SELECT t.id, t.paper_id, p.created_by
        FROM `#__eaiou_paper_tags` t
        JOIN `#__eaiou_papers` p ON p.id = t.paper_id
        WHERE t.id = :tid
    """), {"tid": tag_id}).mappings().first()

    if not tag_row:
        raise HTTPException(status_code=404, detail="Tag not found.")

    if not _can_tag_paper(current_user, tag_row, db):
        raise HTTPException(status_code=403, detail="Cannot delete this tag.")

    db.execute(text("DELETE FROM `#__eaiou_paper_tags` WHERE id = :tid"), {"tid": tag_id})
    db.commit()

    referer = request.headers.get("referer", f"/author/workspace/{tag_row['paper_id']}")
    return RedirectResponse(url=referer, status_code=303)


# ── GET /tags/vocabulary — return the valid tag vocabulary (JSON) ────────────

@router.get("/vocabulary")
async def tag_vocabulary():
    """Return the full RS tag vocabulary for UI dropdowns."""
    return {"tags": RS_TAGS}


# ── API: GET /api/v1/tags/active — active tags across all papers ─────────────

@router.get("/api/active")
async def active_tags(
    tag: str | None = None,
    stall_type: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Return active (unresolved) public tags, optionally filtered."""
    where = ["t.tag_resolved = 0", "t.visibility = 'public'", "p.tombstone_state IS NULL"]
    params: dict = {"limit": limit}

    if tag:
        where.append("t.tag = :tag")
        params["tag"] = tag
    if stall_type:
        where.append("t.subtype = :sub")
        params["sub"] = stall_type

    where_sql = " AND ".join(where)

    rows = db.execute(text(f"""
        SELECT t.id, t.paper_id, t.tag, t.subtype, t.notes, t.created_at,
               p.title AS paper_title
        FROM `#__eaiou_paper_tags` t
        JOIN `#__eaiou_papers` p ON p.id = t.paper_id
        WHERE {where_sql}
        ORDER BY t.created_at DESC
        LIMIT :limit
    """), params).mappings().all()

    return {"active_tags": [dict(r) for r in rows], "count": len(rows)}


# ── API: GET /api/v1/tags/summary — tag counts for discovery ─────────────────

@router.get("/api/summary")
async def tag_summary(
    db: Session = Depends(get_db),
):
    """Return counts of active public tags by tag type, for gap map."""
    rows = db.execute(text("""
        SELECT t.tag, t.subtype, COUNT(*) AS count
        FROM `#__eaiou_paper_tags` t
        JOIN `#__eaiou_papers` p ON p.id = t.paper_id
        WHERE t.tag_resolved = 0 AND t.visibility = 'public'
          AND p.tombstone_state IS NULL
        GROUP BY t.tag, t.subtype
        ORDER BY count DESC
    """)).mappings().all()

    return {"tag_counts": [dict(r) for r in rows]}
