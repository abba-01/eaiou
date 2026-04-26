"""
eaiou — Editor router
Editorial workspace: paper management, status transitions, Q scoring.
Phase 1: admin-only. Requires login.
"""

import os
from datetime import datetime, timezone

import httpx

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..deps import get_current_user
from ..services.qscore import compute_q_signal, persist_q_signal, q_label
from ..services.trajectory import get_trajectory_tree

GITGAP_API = os.getenv("GITGAP_API_URL", "http://127.0.0.1:8001")

router = APIRouter(prefix="/editor", tags=["editor"])
templates = Jinja2Templates(directory="app/templates")

_VALID_STATUSES = {
    "submitted", "under_review", "revision_requested",
    "accepted", "rejected", "published", "archived",
}

# F2-C: Permitted forward transitions (terminal states block all moves)
_TRANSITIONS = {
    "submitted":          {"under_review", "rejected", "archived"},
    "under_review":       {"revision_requested", "accepted", "rejected", "archived"},
    "revision_requested": {"submitted", "under_review", "accepted", "rejected", "archived"},
    "accepted":           {"published", "archived"},
    "rejected":           {"archived"},
    "published":          {"archived"},
    "archived":           set(),
}


def _require_login(request: Request, current_user):
    if not current_user:
        return RedirectResponse(url=f"/auth/login?next={request.url.path}", status_code=302)
    return None


def _get_stats(db: Session) -> dict:
    row = db.execute(text(
        "SELECT "
        "  COUNT(*) AS total, "
        "  SUM(status = 'submitted') AS submitted, "
        "  SUM(status = 'under_review') AS under_review, "
        "  SUM(status = 'revision_requested') AS revision_requested, "
        "  SUM(status = 'accepted') AS accepted, "
        "  SUM(status = 'rejected') AS rejected, "
        "  SUM(status = 'published') AS published "
        "FROM `#__eaiou_papers`"
    )).mappings().first()
    return {k: (v or 0) for k, v in row.items()}


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
@router.get("/papers", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    status: str = "",
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect

    where = "WHERE status = :status" if status else "WHERE 1=1"
    params = {"status": status} if status else {}

    papers = db.execute(text(
        f"SELECT id, paper_uuid, title, author_name, ai_disclosure_level, status, q_overall "
        f"FROM `#__eaiou_papers` "
        f"{where} "
        f"ORDER BY q_overall IS NULL, q_overall DESC, paper_uuid ASC"
    ), params).mappings().all()

    stats = _get_stats(db)
    queue_count = stats.get("submitted", 0)

    return templates.TemplateResponse(request, "editor/dashboard.html", {
        "current_user": current_user,
        "papers": papers,
        "stats": stats,
        "queue_count": queue_count,
    })


# ── Queue (submitted only) ───────────────────────────────────────────────────

@router.get("/queue", response_class=HTMLResponse)
async def queue(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect

    papers = db.execute(text(
        "SELECT id, paper_uuid, cosmoid, title, abstract, author_name, orcid, "
        "ai_disclosure_level, status, q_overall "
        "FROM `#__eaiou_papers` WHERE status = 'submitted' "
        "ORDER BY q_overall IS NULL, q_overall DESC, paper_uuid ASC"
    )).mappings().all()

    stats = _get_stats(db)

    return templates.TemplateResponse(request, "editor/queue.html", {
        "current_user": current_user,
        "papers": papers,
        "stats": stats,
        "queue_count": len(papers),
    })


# ── Paper detail (editorial view) ────────────────────────────────────────────

@router.get("/papers/{paper_id}", response_class=HTMLResponse)
async def paper_detail(
    request: Request,
    paper_id: int,
    flash: str = "",
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect

    paper = db.execute(text(
        "SELECT id, paper_uuid, cosmoid, title, abstract, author_name, orcid, keywords, "
        "ai_disclosure_level, ai_disclosure_notes, status, q_overall, q_signal, "
        "rejection_reason_code, rejection_notes, rejection_public_summary, "
        "doi, submission_capstone "
        "FROM `#__eaiou_papers` WHERE id = :id"
    ), {"id": paper_id}).mappings().first()

    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    stats = _get_stats(db)

    # Q score breakdown (computed live, not persisted)
    try:
        q_breakdown = compute_q_signal(paper_id, db)
    except Exception:
        q_breakdown = None

    # Trajectory tree
    try:
        trajectory = get_trajectory_tree(paper_id, db)
        has_rewrite = any(n.get("method_class") == "rewrite" for n in trajectory)
        has_branch  = any(n.get("method_class") == "branch" for n in trajectory)
    except Exception:
        trajectory, has_rewrite, has_branch = [], False, False

    # RS tags (editors see all visibility levels)
    rs_tags = db.execute(text(
        "SELECT id, tag, subtype, visibility, tag_resolved, notes, created_at, resolved_at "
        "FROM `#__eaiou_paper_tags` WHERE paper_id = :pid "
        "ORDER BY tag_resolved ASC, created_at DESC"
    ), {"pid": paper_id}).mappings().all()

    return templates.TemplateResponse(request, "editor/paper_detail.html", {
        "current_user":  current_user,
        "paper":         paper,
        "stats":         stats,
        "queue_count":   stats.get("submitted", 0),
        "flash":         flash,
        "q_breakdown":   q_breakdown,
        "q_signal_label": q_label(paper["q_signal"]) if paper["q_signal"] else None,
        "trajectory":    trajectory,
        "has_rewrite":   has_rewrite,
        "has_branch":    has_branch,
        "rs_tags":       [dict(t) for t in rs_tags],
    })


# ── Status transition ─────────────────────────────────────────────────────────

@router.post("/papers/{paper_id}/status")
async def update_status(
    request: Request,
    paper_id: int,
    status: str = Form(...),
    rejection_reason_code: str = Form(""),
    rejection_notes: str = Form(""),
    rejection_public_summary: str = Form(""),
    revision_summary: str = Form(""),
    revision_deadline: str = Form(""),
    doi: str = Form(""),
    submission_capstone: str = Form(""),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect

    if status not in _VALID_STATUSES:
        raise HTTPException(status_code=422, detail=f"Invalid status: {status}")

    # F2-C: Enforce valid state transitions
    current_status = db.execute(text(
        "SELECT status FROM `#__eaiou_papers` WHERE id = :id"
    ), {"id": paper_id}).scalar()
    if current_status and status not in _TRANSITIONS.get(current_status, set()):
        allowed = sorted(_TRANSITIONS.get(current_status, set()))
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid transition: {current_status} → {status}. "
                f"Allowed from '{current_status}': "
                + (", ".join(allowed) if allowed else "none (terminal state)")
            ),
        )

    # Fetch gap linkage before committing status change
    paper = db.execute(text(
        "SELECT gitgap_gap_id, cosmoid FROM `#__eaiou_papers` WHERE id = :id"
    ), {"id": paper_id}).mappings().first()

    db.execute(text(
        "UPDATE `#__eaiou_papers` SET status = :status WHERE id = :id"
    ), {"status": status, "id": paper_id})
    if status == "rejected":
        db.execute(text(
            "UPDATE `#__eaiou_papers` SET "
            "rejection_reason_code = :code, "
            "rejection_notes = :notes, "
            "rejection_public_summary = :summary "
            "WHERE id = :id"
        ), {
            "code":    rejection_reason_code or None,
            "notes":   rejection_notes or None,
            "summary": rejection_public_summary or None,
            "id":      paper_id,
        })
    # F4-A: Capture DOI and Zenodo receipt on publication
    if status == "published":
        db.execute(text(
            "UPDATE `#__eaiou_papers` SET "
            "doi = :doi, submission_capstone = :capstone "
            "WHERE id = :id"
        ), {
            "doi":      doi.strip() or None,
            "capstone": submission_capstone.strip() or None,
            "id":       paper_id,
        })
    # F2-A: Store revision instructions when requesting revision
    if status == "revision_requested" and revision_summary.strip():
        current_round = db.execute(text(
            "SELECT COALESCE(MAX(round), 0) FROM `#__eaiou_revisions` WHERE paper_id = :id"
        ), {"id": paper_id}).scalar() or 0
        db.execute(text(
            "INSERT INTO `#__eaiou_revisions` "
            "(paper_id, round, instructions, due_at, requested_at) "
            "VALUES (:pid, :round, :instr, :due, :now)"
        ), {
            "pid":   paper_id,
            "round": current_round + 1,
            "instr": revision_summary.strip(),
            "due":   revision_deadline or None,
            "now":   datetime.now(timezone.utc),
        })
    db.commit()

    # F2-D: Author notification on status change
    _STATUS_MESSAGES = {
        "under_review":       "Your paper is now under editorial review.",
        "revision_requested": "The editor has requested revisions to your paper.",
        "accepted":           "Congratulations — your paper has been accepted.",
        "rejected":           "Your paper was not accepted at this time.",
        "published":          "Your paper has been published.",
        "archived":           "Your paper has been archived.",
        "submitted":          "Your paper has been re-entered into the submission queue.",
    }
    _msg = _STATUS_MESSAGES.get(status)
    if _msg:
        try:
            paper_title = db.execute(text(
                "SELECT title FROM `#__eaiou_papers` WHERE id = :id"
            ), {"id": paper_id}).scalar() or f"Paper #{paper_id}"
            db.execute(text(
                "INSERT INTO `#__eaiou_notifications` (paper_id, type, message, created_at) "
                "VALUES (:pid, :type, :msg, :now)"
            ), {
                "pid":  paper_id,
                "type": f"status_{status}",
                "msg":  f"\u201c{paper_title}\u201d \u2014 {_msg}",
                "now":  datetime.now(timezone.utc),
            })
            db.commit()
        except Exception:
            pass  # Non-fatal

    # BF-2: Lifecycle webhooks to gitgap
    if paper and paper["gitgap_gap_id"]:
        gap_id  = paper["gitgap_gap_id"]
        cosmoid = paper["cosmoid"] or ""
        try:
            with httpx.Client(timeout=4) as client:
                if status in ("accepted", "published"):
                    client.post(
                        f"{GITGAP_API}/gaps/{gap_id}/found",
                        json={
                            "found_paper_cosmoid": cosmoid,
                            "found_paper_doi": doi.strip() or "",
                        },
                    )
                elif status == "rejected":
                    client.post(
                        f"{GITGAP_API}/gaps/{gap_id}/reject",
                        json={
                            "rejection_mode":     rejection_reason_code or "other",
                            "rejection_notes":     rejection_notes,
                            "pickup_instructions": rejection_public_summary,
                        },
                    )
        except Exception:
            pass  # Non-fatal — lifecycle webhook is best-effort

    return RedirectResponse(
        url=f"/editor/papers/{paper_id}?flash=Status+updated+to+{status.replace('_','+')}",
        status_code=303,
    )


# ── Q score ───────────────────────────────────────────────────────────────────

@router.post("/papers/{paper_id}/score")
async def update_score(
    request: Request,
    paper_id: int,
    q_overall: str = Form(""),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Editor override of Q score. Sets q_overall; preserves q_signal (computed)."""
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect

    score = None
    if q_overall.strip():
        try:
            score = float(q_overall)
            if not (0.0 <= score <= 10.0):
                raise ValueError
        except ValueError:
            raise HTTPException(status_code=422, detail="Q score must be between 0 and 10")

    db.execute(text(
        "UPDATE `#__eaiou_papers` SET q_overall = :score WHERE id = :id"
    ), {"score": score, "id": paper_id})
    db.commit()

    return RedirectResponse(
        url=f"/editor/papers/{paper_id}?flash=Q+score+saved",
        status_code=303,
    )


@router.post("/papers/{paper_id}/score/recompute")
async def recompute_score(
    request: Request,
    paper_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Recompute q_signal from current evidence.
    Resets q_overall to the new signal value (clears manual override).
    Returns the breakdown so the editor can see what drove the score.
    """
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect

    if not db.execute(text("SELECT id FROM `#__eaiou_papers` WHERE id = :id"),
                      {"id": paper_id}).scalar():
        raise HTTPException(status_code=404, detail="Paper not found")

    # Force recompute — clear q_overall so persist_q_signal sets it fresh
    db.execute(text(
        "UPDATE `#__eaiou_papers` SET q_overall = NULL WHERE id = :id"
    ), {"id": paper_id})
    db.commit()

    result = persist_q_signal(paper_id, db)

    return JSONResponse({
        "paper_id":  paper_id,
        "q_signal":  result["q_signal"],
        "q_label":   result["q_label"],
        "breakdown": result["breakdown"],
        "weights":   result["weights"],
    })


@router.get("/papers/{paper_id}/score/breakdown")
async def score_breakdown(
    request: Request,
    paper_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Show current Q signal computation without persisting.
    Useful for previewing what the score would be before committing.
    """
    redirect = _require_login(request, current_user)
    if redirect:
        return redirect

    if not db.execute(text("SELECT id FROM `#__eaiou_papers` WHERE id = :id"),
                      {"id": paper_id}).scalar():
        raise HTTPException(status_code=404, detail="Paper not found")

    # Fetch stored scores alongside computed
    stored = db.execute(text(
        "SELECT q_signal, q_overall FROM `#__eaiou_papers` WHERE id = :id"
    ), {"id": paper_id}).mappings().first()

    result = compute_q_signal(paper_id, db)

    return JSONResponse({
        "paper_id":       paper_id,
        "stored_signal":  float(stored["q_signal"]) if stored["q_signal"] else None,
        "stored_overall": float(stored["q_overall"]) if stored["q_overall"] else None,
        "computed":       result,
    })
