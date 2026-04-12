"""
eaiou — Tier 2 JSON REST API: Review & Workflow Engine
9 endpoints: rubric, reviewer assignment, review submit/get/list,
workflow assign/revise/accept/reject.

Router prefix: /api/v1
Tags:          api-review

Live schema notes (verified 2026-04-12):
  #__eaiou_review_logs  — reviewer_id (not reviewer_user_id), no status col
                          state: 1=invited, 2=completed
                          recommendation enum: accept|minor|major|reject|abstain
  #__eaiou_quality_signals — q_overall/q_originality/… (full row per review)
  #__eaiou_papers       — acceptance_sealed_at, tombstone_state, rejection_*
"""

import hashlib
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..deps import (
    get_current_user,
    require_editor,
    require_auth,
    require_reviewer,
    optional_auth,
)
from ..services.api_log import log_api_call

router = APIRouter(prefix="/api/v1", tags=["api-review"])

# ── Rubric constants ──────────────────────────────────────────────────────────

_RUBRIC = {
    "dimensions": [
        {"name": "overall",        "weight": 1.0},
        {"name": "originality",    "weight": 1.0},
        {"name": "methodology",    "weight": 1.0},
        {"name": "transparency",   "weight": 1.5},
        {"name": "ai_disclosure",  "weight": 1.0},
        {"name": "crossdomain",    "weight": 1.0},
    ],
    "scale": {"min": 0, "max": 10},
}

# Mapping from API recommendation values → DB enum values
# DB enum: accept|minor|major|reject|abstain
_REC_TO_DB = {
    "accept":           "accept",
    "minor_revision":   "minor",
    "major_revision":   "major",
    "reject":           "reject",
}
_REC_FROM_DB = {v: k for k, v in _REC_TO_DB.items()}
# abstain has no API equivalent; round-trip as-is
_REC_FROM_DB["abstain"] = "abstain"


# ── Pydantic models ───────────────────────────────────────────────────────────

class ReviewerAssign(BaseModel):
    reviewer_user_id: int
    invite_due_date: str   # ISO date string — stored in labels_json for provenance
    notes: Optional[str] = None


class ReviewSubmit(BaseModel):
    version_reviewed: str = "v1"
    rubric_overall: float
    rubric_originality: float
    rubric_methodology: float
    rubric_transparency: float
    rubric_ai_disclosure: float
    rubric_crossdomain: float
    recommendation: str  # accept|minor_revision|major_revision|reject
    review_notes: str
    unsci_flagged: bool = False
    open_consent: bool = False

    @validator(
        "rubric_overall", "rubric_originality", "rubric_methodology",
        "rubric_transparency", "rubric_ai_disclosure", "rubric_crossdomain",
    )
    def check_score_range(cls, v):
        if not (0 <= v <= 10):
            raise ValueError("Rubric scores must be between 0 and 10")
        return v

    @validator("recommendation")
    def check_recommendation(cls, v):
        allowed = {"accept", "minor_revision", "major_revision", "reject"}
        if v not in allowed:
            raise ValueError(f"Recommendation must be one of: {allowed}")
        return v


class AssignReviewers(BaseModel):
    reviewers: list   # [{user_id: int, due_date: str}, …]
    notes: Optional[str] = None


class RevisionRequest(BaseModel):
    revision_notes: str
    due_date: str   # ISO date


class AcceptPaper(BaseModel):
    editor_notes: Optional[str] = None


class RejectPaper(BaseModel):
    rejection_reason: str
    editor_notes: Optional[str] = None


# ── Helper: insert a single reviewer-invite row ───────────────────────────────

def _insert_invite(db: Session, paper_id: int, reviewer_user_id: int,
                   notes: Optional[str], due_date: str, editor_user_id: int) -> int:
    """
    Insert one invited row into review_logs.
    state=1 means invited/active.
    Returns the new row id.
    """
    import json
    now = datetime.now(timezone.utc)
    labels = json.dumps({"invite_due_date": due_date, "notes": notes})
    db.execute(text(
        "INSERT INTO `#__eaiou_review_logs` "
        "(paper_id, reviewer_id, version_reviewed, state, labels_json, "
        "unsci_flagged, open_consent, created, created_by) "
        "VALUES (:paper_id, :reviewer_id, 'v1', 1, :labels, 0, 0, :now, :editor)"
    ), {
        "paper_id":    paper_id,
        "reviewer_id": reviewer_user_id,
        "labels":      labels,
        "now":         now,
        "editor":      editor_user_id,
    })
    db.commit()
    result = db.execute(text("SELECT LAST_INSERT_ID()")).fetchone()
    return result[0]


# ── 1. GET /review/rubric — review.get_rubric (PUBLIC) ───────────────────────

@router.get("/review/rubric")
async def review_get_rubric():
    return _RUBRIC


# ── 2. POST /papers/{paper_id}/reviewers — review.assign ─────────────────────

@router.post("/papers/{paper_id}/reviewers")
async def review_assign(
    paper_id: int,
    body: ReviewerAssign,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    # Verify reviewer exists
    reviewer = db.execute(text(
        "SELECT id FROM `#__eaiou_users` WHERE id = :id AND active = 1"
    ), {"id": body.reviewer_user_id}).fetchone()

    if reviewer is None:
        return JSONResponse(
            {"error": "not_found", "detail": "Reviewer user not found."},
            status_code=404,
        )

    _insert_invite(
        db, paper_id, body.reviewer_user_id,
        body.notes, body.invite_due_date, current_user["id"],
    )

    log_api_call(
        db, f"/api/v1/papers/{paper_id}/reviewers", "POST",
        hashlib.sha256(str(paper_id).encode()).hexdigest(), 201,
    )

    return JSONResponse(
        status_code=201,
        content={
            "paper_id":          paper_id,
            "reviewer_user_id":  body.reviewer_user_id,
            "status":            "invited",
        },
    )


# ── 3. POST /papers/{paper_id}/reviews — review.submit ───────────────────────

@router.post("/papers/{paper_id}/reviews")
async def review_submit(
    paper_id: int,
    body: ReviewSubmit,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    # ACL: must be an assigned reviewer for this paper (state=1 → invited)
    invite_row = db.execute(text(
        "SELECT id FROM `#__eaiou_review_logs` "
        "WHERE paper_id = :pid AND reviewer_id = :uid AND state = 1 "
        "ORDER BY id DESC LIMIT 1"
    ), {"pid": paper_id, "uid": current_user["id"]}).fetchone()

    if invite_row is None:
        return JSONResponse(
            {"error": "forbidden",
             "detail": "You are not an assigned reviewer for this paper."},
            status_code=403,
        )

    review_log_id = invite_row[0]
    now = datetime.now(timezone.utc)
    db_rec = _REC_TO_DB[body.recommendation]

    # UPDATE the invited row: add scores + recommendation + state=2 (completed)
    db.execute(text(
        "UPDATE `#__eaiou_review_logs` SET "
        "  version_reviewed   = :ver, "
        "  review_date        = :now, "
        "  rubric_overall     = :overall, "
        "  rubric_originality = :orig, "
        "  rubric_methodology = :meth, "
        "  rubric_transparency = :trans, "
        "  rubric_ai_disclosure = :ai, "
        "  rubric_crossdomain = :cross, "
        "  recommendation     = :rec, "
        "  review_notes       = :notes, "
        "  unsci_flagged      = :unsci, "
        "  open_consent       = :consent, "
        "  state              = 2, "
        "  modified           = :now "
        "WHERE id = :rid"
    ), {
        "ver":     body.version_reviewed,
        "now":     now,
        "overall": round(body.rubric_overall),
        "orig":    round(body.rubric_originality),
        "meth":    round(body.rubric_methodology),
        "trans":   round(body.rubric_transparency),
        "ai":      round(body.rubric_ai_disclosure),
        "cross":   round(body.rubric_crossdomain),
        "rec":     db_rec,
        "notes":   body.review_notes,
        "unsci":   int(body.unsci_flagged),
        "consent": int(body.open_consent),
        "rid":     review_log_id,
    })

    # INSERT into quality_signals — one row per completed review
    # quality_signals uses q_overall / q_originality / … (full row, not per-dimension)
    # Store raw 0-10 scores; q_signal = weighted average
    weights = [1.0, 1.0, 1.0, 1.5, 1.0, 1.0]
    scores  = [
        body.rubric_overall, body.rubric_originality, body.rubric_methodology,
        body.rubric_transparency, body.rubric_ai_disclosure, body.rubric_crossdomain,
    ]
    weighted_sum = sum(s * w for s, w in zip(scores, weights))
    weight_total = sum(weights)
    q_signal = round(weighted_sum / weight_total, 4)

    db.execute(text(
        "INSERT INTO `#__eaiou_quality_signals` "
        "(paper_id, review_log_id, "
        " q_overall, q_originality, q_methodology, q_transparency, "
        " q_ai_disclosure, q_crossdomain, q_signal, "
        " computed_at, state, created, created_by) "
        "VALUES (:pid, :rlid, "
        "        :overall, :orig, :meth, :trans, :ai, :cross, :qs, "
        "        :now, 1, :now, :uid)"
    ), {
        "pid":     paper_id,
        "rlid":    review_log_id,
        "overall": body.rubric_overall,
        "orig":    body.rubric_originality,
        "meth":    body.rubric_methodology,
        "trans":   body.rubric_transparency,
        "ai":      body.rubric_ai_disclosure,
        "cross":   body.rubric_crossdomain,
        "qs":      q_signal,
        "now":     now,
        "uid":     current_user["id"],
    })

    # Check if ALL invited reviewers for this paper have now submitted
    pending = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_review_logs` "
        "WHERE paper_id = :pid AND state = 1"
    ), {"pid": paper_id}).scalar()

    if pending == 0:
        db.execute(text(
            "UPDATE `#__eaiou_papers` SET status = 'decision_pending' "
            "WHERE id = :pid AND status = 'under_review'"
        ), {"pid": paper_id})

    db.commit()

    log_api_call(
        db, f"/api/v1/papers/{paper_id}/reviews", "POST",
        hashlib.sha256(str(paper_id).encode()).hexdigest(), 201,
    )

    return JSONResponse(
        status_code=201,
        content={
            "review_id":      review_log_id,
            "paper_id":       paper_id,
            "recommendation": body.recommendation,
        },
    )


# ── 4. GET /reviews/{review_id} — review.get ─────────────────────────────────

@router.get("/reviews/{review_id}")
async def review_get(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    row = db.execute(text(
        "SELECT id, paper_id, reviewer_id, version_reviewed, review_date, "
        "rubric_overall, rubric_originality, rubric_methodology, "
        "rubric_transparency, rubric_ai_disclosure, rubric_crossdomain, "
        "recommendation, review_notes, unsci_flagged, open_consent, state, created "
        "FROM `#__eaiou_review_logs` WHERE id = :id"
    ), {"id": review_id}).mappings().first()

    if row is None:
        return JSONResponse(
            {"error": "not_found", "detail": "Review not found."},
            status_code=404,
        )

    groups = set(current_user.get("groups", []))
    is_editor_plus = bool({"editor", "admin", "eic"} & groups)
    is_own_review  = (row["reviewer_id"] == current_user["id"])

    if not is_own_review and not is_editor_plus:
        return JSONResponse(
            {"error": "forbidden", "detail": "Access denied."},
            status_code=403,
        )

    result = dict(row)
    # Translate DB enum back to API enum
    if result.get("recommendation"):
        result["recommendation"] = _REC_FROM_DB.get(result["recommendation"], result["recommendation"])

    return result


# ── 5. GET /papers/{paper_id}/reviews — review.list_by_paper ─────────────────

@router.get("/papers/{paper_id}/reviews")
async def review_list_by_paper(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(optional_auth),
):
    groups = set(current_user.get("groups", [])) if current_user else set()
    is_editor_plus = bool({"editor", "admin", "eic"} & groups)

    if is_editor_plus:
        # Editors get all reviews
        rows = db.execute(text(
            "SELECT id, paper_id, reviewer_id, version_reviewed, review_date, "
            "rubric_overall, rubric_originality, rubric_methodology, "
            "rubric_transparency, rubric_ai_disclosure, rubric_crossdomain, "
            "recommendation, review_notes, unsci_flagged, open_consent, state, created "
            "FROM `#__eaiou_review_logs` WHERE paper_id = :pid ORDER BY id"
        ), {"pid": paper_id}).mappings().all()

        result = []
        for r in rows:
            d = dict(r)
            if d.get("recommendation"):
                d["recommendation"] = _REC_FROM_DB.get(d["recommendation"], d["recommendation"])
            result.append(d)
    else:
        # Public: only open_consent=1 reviews, reviewer_user_id stripped
        rows = db.execute(text(
            "SELECT id, paper_id, version_reviewed, review_date, "
            "rubric_overall, rubric_originality, rubric_methodology, "
            "rubric_transparency, rubric_ai_disclosure, rubric_crossdomain, "
            "recommendation, review_notes, unsci_flagged, open_consent, state, created "
            "FROM `#__eaiou_review_logs` "
            "WHERE paper_id = :pid AND open_consent = 1 AND state = 2 "
            "ORDER BY id"
        ), {"pid": paper_id}).mappings().all()

        result = []
        for r in rows:
            d = dict(r)
            if d.get("recommendation"):
                d["recommendation"] = _REC_FROM_DB.get(d["recommendation"], d["recommendation"])
            result.append(d)

    return {"reviews": result, "paper_id": paper_id}


# ── 6. POST /papers/{paper_id}/workflow/assign — workflow.assign_reviewers ────

@router.post("/papers/{paper_id}/workflow/assign")
async def workflow_assign_reviewers(
    paper_id: int,
    body: AssignReviewers,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    assigned_count = 0

    for entry in body.reviewers:
        user_id  = entry.get("user_id") if isinstance(entry, dict) else getattr(entry, "user_id", None)
        due_date = entry.get("due_date") if isinstance(entry, dict) else getattr(entry, "due_date", "")

        if user_id is None:
            continue

        # Verify user exists
        reviewer = db.execute(text(
            "SELECT id FROM `#__eaiou_users` WHERE id = :id AND active = 1"
        ), {"id": user_id}).fetchone()

        if reviewer is None:
            continue  # Skip invalid users; caller can check assigned_count

        _insert_invite(
            db, paper_id, user_id,
            body.notes, due_date or "", current_user["id"],
        )
        assigned_count += 1

    # Only advance paper status if at least one reviewer was successfully assigned
    if assigned_count > 0:
        db.execute(text(
            "UPDATE `#__eaiou_papers` SET status = 'under_review' "
            "WHERE id = :pid AND status = 'submitted' AND tombstone_state IS NULL"
        ), {"pid": paper_id})
        db.commit()

    # Get actual current paper status for the response
    paper_row = db.execute(text(
        "SELECT status FROM `#__eaiou_papers` WHERE id = :pid"
    ), {"pid": paper_id}).fetchone()
    actual_status = paper_row[0] if paper_row else "unknown"

    log_api_call(
        db, f"/api/v1/papers/{paper_id}/workflow/assign", "POST",
        hashlib.sha256(str(paper_id).encode()).hexdigest(), 200,
    )

    return JSONResponse({
        "paper_id":       paper_id,
        "assigned_count": assigned_count,
        "new_state":      actual_status,
    })


# ── 7. POST /papers/{paper_id}/workflow/revise — workflow.request_revision ────

@router.post("/papers/{paper_id}/workflow/revise")
async def workflow_request_revision(
    paper_id: int,
    body: RevisionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    now = datetime.now(timezone.utc)

    # Check paper exists and is not tombstoned BEFORE inserting revision row
    paper_row = db.execute(text(
        "SELECT id FROM `#__eaiou_papers` WHERE id = :pid AND tombstone_state IS NULL"
    ), {"pid": paper_id}).fetchone()
    if not paper_row:
        raise HTTPException(status_code=404, detail="Paper not found or tombstoned.")

    # Record revision request in revisions table for provenance
    db.execute(text(
        "INSERT INTO `#__eaiou_revisions` "
        "(paper_id, round, instructions, due_at, requested_at) "
        "VALUES (:pid, "
        "  COALESCE((SELECT MAX(round) FROM `#__eaiou_revisions` r2 WHERE r2.paper_id = :pid), 0) + 1, "
        "  :notes, :due, :now)"
    ), {
        "pid":   paper_id,
        "notes": body.revision_notes,
        "due":   body.due_date,
        "now":   now,
    })

    db.execute(text(
        "UPDATE `#__eaiou_papers` SET status = 'revisions_requested' "
        "WHERE id = :pid AND tombstone_state IS NULL"
    ), {"pid": paper_id})
    db.commit()

    log_api_call(
        db, f"/api/v1/papers/{paper_id}/workflow/revise", "POST",
        hashlib.sha256(str(paper_id).encode()).hexdigest(), 200,
    )

    return {"paper_id": paper_id, "new_state": "revisions_requested"}


# ── 8. POST /papers/{paper_id}/workflow/accept — workflow.accept ──────────────

@router.post("/papers/{paper_id}/workflow/accept")
async def workflow_accept(
    paper_id: int,
    body: AcceptPaper,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    now = datetime.now(timezone.utc)

    # Atomic COALESCE: sets acceptance_sealed_at only if currently NULL (no race condition)
    result = db.execute(text(
        "UPDATE `#__eaiou_papers` "
        "SET status = 'accepted', "
        "    acceptance_sealed_at = COALESCE(acceptance_sealed_at, :now) "
        "WHERE id = :pid AND tombstone_state IS NULL"
    ), {"pid": paper_id, "now": now})
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Paper not found or tombstoned.")

    log_api_call(
        db, f"/api/v1/papers/{paper_id}/workflow/accept", "POST",
        hashlib.sha256(str(paper_id).encode()).hexdigest(), 200,
    )

    return {"paper_id": paper_id, "new_state": "accepted"}


# ── 9. POST /papers/{paper_id}/workflow/reject — workflow.reject ──────────────

@router.post("/papers/{paper_id}/workflow/reject")
async def workflow_reject(
    paper_id: int,
    body: RejectPaper,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    now = datetime.now(timezone.utc)

    # Set status=rejected + tombstone_state=public_unspace — never hard-delete
    result = db.execute(text(
        "UPDATE `#__eaiou_papers` "
        "SET status = 'rejected', "
        "    tombstone_state = 'public_unspace', "
        "    rejection_notes = :notes, "
        "    tombstone_at = :now, "
        "    tombstone_by = :uid "
        "WHERE id = :pid AND tombstone_state IS NULL"
    ), {
        "notes": body.rejection_reason,
        "now":   now,
        "uid":   current_user["id"],
        "pid":   paper_id,
    })
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Paper not found, already tombstoned, or already rejected.")

    log_api_call(
        db, f"/api/v1/papers/{paper_id}/workflow/reject", "POST",
        hashlib.sha256(str(paper_id).encode()).hexdigest(), 200,
    )

    return {"paper_id": paper_id, "new_state": "rejected"}
