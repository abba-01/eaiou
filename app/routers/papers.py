"""
eaiou — Papers router
Submission, listing, retrieval.
"""

import uuid

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone

from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/papers", tags=["papers"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def list_papers(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    rows = db.execute(text(
        "SELECT id, title, abstract, author_name, orcid, status, "
        "ai_disclosure_level, q_overall FROM `#__eaiou_papers` "
        "WHERE status != 'draft' AND tombstone_state IS NULL "
        "ORDER BY q_overall IS NULL, q_overall DESC, paper_uuid ASC LIMIT 50"
    )).mappings().all()
    return templates.TemplateResponse(request, "papers/list.html", {
        "papers": rows,
        "current_user": current_user,
    })


@router.get("/submit", response_class=HTMLResponse)
async def submit_form(request: Request, current_user=Depends(get_current_user)):
    return templates.TemplateResponse(request, "papers/submit.html", {
        "current_user": current_user,
        "error": None,
    })


@router.get("/submitted/{paper_id}", response_class=HTMLResponse)
async def submission_confirmed(
    request: Request,
    paper_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = db.execute(text(
        "SELECT id, cosmoid, paper_uuid, title, abstract, author_name, orcid, ai_disclosure_level "
        "FROM `#__eaiou_papers` WHERE id = :id"
    ), {"id": paper_id}).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    return templates.TemplateResponse(request, "papers/submitted.html", {
        "paper": row,
        "current_user": current_user,
    })


@router.get("/status/{paper_id}", response_class=HTMLResponse)
async def paper_status(
    request: Request,
    paper_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = db.execute(text(
        "SELECT id, title, abstract, author_name, orcid, keywords, "
        "ai_disclosure_level, status, q_overall "
        "FROM `#__eaiou_papers` WHERE id = :id"
    ), {"id": paper_id}).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    return templates.TemplateResponse(request, "views/13_status_tracking.html", {
        "paper": row,
        "current_user": current_user,
        "notification_count": 0,
    })


@router.get("/{paper_id}", response_class=HTMLResponse)
async def view_paper(
    request: Request,
    paper_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = db.execute(text(
        "SELECT id, cosmoid, title, abstract, author_name, orcid, keywords, "
        "ai_disclosure_level, ai_disclosure_notes, status, submitted_at, q_overall, q_signal, "
        "gitgap_gap_id, rejection_public_summary, doi, submission_capstone "
        "FROM `#__eaiou_papers` WHERE id = :id"
    ), {"id": paper_id}).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    # CoA seal — most recent integrity seal for this paper
    seal = db.execute(text(
        "SELECT cosmoid, gate_valid, audit_status, mbs AS mbs_score, seal_hash, sealed_at "
        "FROM `#__eaiou_integrity_seals` "
        "WHERE paper_id = :id ORDER BY sealed_at DESC LIMIT 1"
    ), {"id": paper_id}).mappings().first()

    # Contribution graph — intellid nodes (strip hashes for public display)
    contributions = db.execute(text(
        "SELECT ic.relation, ic.weight, ic.confidence, "
        "       ir.type, ir.model_family, ir.connector "
        "FROM `#__eaiou_intellid_contributions` ic "
        "JOIN `#__eaiou_intellid_registry` ir ON ir.intellid = ic.intellid "
        "WHERE ic.artifact_type = 'paper' "
        "AND ic.artifact_id = (SELECT cosmoid FROM `#__eaiou_papers` WHERE id = :id) "
        "ORDER BY ic.weight DESC"
    ), {"id": paper_id}).mappings().all()

    # CAUGHT anchor — fetch gap declaration from gitgap if paper was submitted in response to a gap
    caught_gap = None
    if row["gitgap_gap_id"]:
        try:
            import httpx, os
            gitgap_api = os.getenv("GITGAP_API_URL", "http://127.0.0.1:8001")
            with httpx.Client(timeout=4) as client:
                resp = client.get(f"{gitgap_api}/gaps/{row['gitgap_gap_id']}")
                if resp.status_code == 200:
                    caught_gap = resp.json()
        except Exception:
            pass

    # RS tags (public visibility only for public view)
    rs_tags = db.execute(text(
        "SELECT tag, subtype, notes, created_at "
        "FROM `#__eaiou_paper_tags` "
        "WHERE paper_id = :pid AND tag_resolved = 0 AND visibility = 'public' "
        "ORDER BY created_at DESC"
    ), {"pid": paper_id}).mappings().all()

    return templates.TemplateResponse(request, "views/22_the_article.html", {
        "paper":         row,
        "current_user":  current_user,
        "seal":          seal,
        "contributions": [dict(c) for c in contributions],
        "caught_gap":    caught_gap,
        "rs_tags":       [dict(t) for t in rs_tags],
        "notification_count": 0,
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
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    paper_uuid = str(uuid.uuid4())
    cosmoid = str(uuid.uuid4())  # minted at creation, permanent, never removed
    db.execute(text(
        "INSERT INTO `#__eaiou_papers` "
        "(paper_uuid, cosmoid, title, abstract, author_name, orcid, keywords, "
        "ai_disclosure_level, ai_disclosure_notes, status, submitted_at, created) "
        "VALUES (:uuid, :cosmoid, :title, :abstract, :author_name, :orcid, :keywords, "
        ":ai_level, :ai_notes, 'submitted', :submitted_at, :created)"
    ), {
        "uuid": paper_uuid,
        "cosmoid": cosmoid,
        "title": title,
        "abstract": abstract,
        "author_name": author_name,
        "orcid": orcid,
        "keywords": keywords,
        "ai_level": ai_disclosure_level,
        "ai_notes": ai_disclosure_notes,
        "submitted_at": now,
        "created": now,
    })
    db.commit()
    result = db.execute(text("SELECT LAST_INSERT_ID() as id")).mappings().first()
    new_id = result["id"] if result else None
    return RedirectResponse(url=f"/papers/submitted/{new_id}", status_code=303)
