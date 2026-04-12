"""
eaiou — Tier 1 JSON REST API Core
16 human-facing endpoints for papers, workflow, users, auth, qscore,
contributions, and AI sessions.

Router prefix: /api/v1
Tags:          api-core
"""

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..deps import (
    get_current_user,
    require_author,
    require_reviewer,
    require_editor,
    require_auth,
    optional_auth,
)
from ..services.api_log import log_api_call

router = APIRouter(prefix="/api/v1", tags=["api-core"])

# ── Sealed-field constants ────────────────────────────────────────────────────

_SEALED = frozenset({
    "submission_sealed_at", "acceptance_sealed_at", "publication_sealed_at",
    "attestation_sealed_at", "attestation_json", "sealed_by", "submission_hash",
})
_FORBIDDEN_SORT = frozenset({
    "date", "created", "submitted_at", "created_at", "modified", "modified_at",
    "submission_sealed_at", "acceptance_sealed_at", "publication_sealed_at",
})

def _strip_sealed(d: dict) -> dict:
    return {k: v for k, v in d.items() if k not in _SEALED}

# Valid workflow transitions: {from_state: [allowed_to_states]}
_TRANSITIONS = {
    "draft":               ["submitted"],
    "submitted":           ["under_review"],
    "under_review":        ["decision_pending"],
    "decision_pending":    ["accepted", "rejected", "revisions_requested"],
    "revisions_requested": ["submitted"],
    "accepted":            ["published"],
}

# ── Pydantic models ───────────────────────────────────────────────────────────

class PaperCreate(BaseModel):
    title: str
    abstract: str
    authorship_mode: str = "human"
    authors_json: Optional[str] = None
    keywords: Optional[str] = None


class PaperUpdate(BaseModel):
    title: Optional[str] = None
    abstract: Optional[str] = None
    authorship_mode: Optional[str] = None
    authors_json: Optional[str] = None
    keywords: Optional[str] = None
    status: Optional[str] = None


class WorkflowTransition(BaseModel):
    target_state: str
    notes: Optional[str] = None


class ContributionCreate(BaseModel):
    contributor_name: str
    orcid: Optional[str] = None
    role_description: str
    contribution_type: str
    is_human: bool = True
    is_ai: bool = False
    ai_tool_used: Optional[str] = None


class AISessionCreate(BaseModel):
    paper_id: int
    session_label: str
    ai_model_name: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    redaction_status: str = "none"
    session_notes: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# ── 1. GET /papers — paper.list ───────────────────────────────────────────────

@router.get("/papers")
async def paper_list(
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None,
    authorship_mode: Optional[str] = None,
    sort: Optional[str] = None,
    db: Session = Depends(get_db),
):
    # TB: reject date-based sort
    if sort and sort.lower().lstrip("-") in _FORBIDDEN_SORT:
        return JSONResponse(
            {"error": "sort_forbidden", "detail": "Date-based sort not permitted."},
            status_code=400,
        )

    where = ["tombstone_state IS NULL"]
    params: dict = {"limit": limit, "offset": offset}
    if status:
        where.append("status = :status")
        params["status"] = status
    if authorship_mode:
        where.append("authorship_mode = :am")
        params["am"] = authorship_mode

    where_clause = "WHERE " + " AND ".join(where)

    rows = db.execute(text(
        f"SELECT id, paper_uuid, cosmoid, title, abstract, author_name, orcid, "
        f"authorship_mode, status, q_signal, q_overall, keywords, ai_disclosure_level "
        f"FROM `#__eaiou_papers` {where_clause} "
        f"ORDER BY q_signal IS NULL ASC, q_signal DESC "
        f"LIMIT :limit OFFSET :offset"
    ), params).mappings().all()

    count_params = {k: v for k, v in params.items() if k not in ("limit", "offset")}
    total = db.execute(text(
        f"SELECT COUNT(*) FROM `#__eaiou_papers` {where_clause}"
    ), count_params).scalar()

    return {
        "papers": [_strip_sealed(dict(r)) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ── 2. GET /papers/{id} — paper.get ──────────────────────────────────────────

@router.get("/papers/{paper_id}")
async def paper_get(paper_id: int, db: Session = Depends(get_db)):
    row = db.execute(text(
        "SELECT id, paper_uuid, cosmoid, title, abstract, author_name, orcid, "
        "authorship_mode, status, q_signal, q_overall, keywords, ai_disclosure_level, "
        "ai_disclosure_notes, origin_type, pipeline_stage "
        "FROM `#__eaiou_papers` "
        "WHERE id = :id AND tombstone_state IS NULL"
    ), {"id": paper_id}).mappings().first()

    if row is None:
        return JSONResponse({"error": "not_found", "detail": "Paper not found."}, status_code=404)

    return _strip_sealed(dict(row))


# ── 3. POST /papers — paper.create ───────────────────────────────────────────

@router.post("/papers")
async def paper_create(
    body: PaperCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_author),
):
    paper_uuid = str(uuid.uuid4())
    cosmoid    = str(uuid.uuid4())
    now        = datetime.now(timezone.utc)

    db.execute(text(
        "INSERT INTO `#__eaiou_papers` "
        "(paper_uuid, cosmoid, title, abstract, authorship_mode, authors_json, keywords, "
        "status, origin_type, submitted_at, created) "
        "VALUES (:uuid, :cosmoid, :title, :abstract, :am, :authors, :keywords, "
        "'draft', 'humint', NULL, :created)"
    ), {
        "uuid":     paper_uuid,
        "cosmoid":  cosmoid,
        "title":    body.title,
        "abstract": body.abstract,
        "am":       body.authorship_mode,
        "authors":  body.authors_json,
        "keywords": body.keywords,
        "created":  now,
    })
    db.commit()

    result = db.execute(text(
        "SELECT id FROM `#__eaiou_papers` WHERE paper_uuid = :uuid"
    ), {"uuid": paper_uuid}).fetchone()

    paper_id = result[0]
    log_api_call(
        db, "/api/v1/papers", "POST",
        hashlib.sha256(body.title.encode()).hexdigest(), 201,
    )

    return JSONResponse(
        status_code=201,
        content={"paper_id": paper_id, "paper_uuid": paper_uuid, "cosmoid": cosmoid},
    )


# ── 4. PATCH /papers/{id} — paper.update ─────────────────────────────────────

@router.patch("/papers/{paper_id}")
async def paper_update(
    paper_id: int,
    body: PaperUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    # Reject if any submitted key is in _SEALED
    body_fields = {k for k, v in body.model_dump().items() if v is not None}
    sealed_attempt = body_fields & _SEALED
    if sealed_attempt:
        return JSONResponse(
            {"error": "sealed_field", "detail": f"Cannot modify sealed fields: {sealed_attempt}"},
            status_code=400,
        )

    # ACL: must be editor/admin or the paper's author
    groups = set(current_user.get("groups", []))
    if not ({"editor", "admin"} & groups):
        row_author = db.execute(text(
            "SELECT author_name FROM `#__eaiou_papers` WHERE id = :id"
        ), {"id": paper_id}).fetchone()
        if row_author is None:
            return JSONResponse({"error": "not_found", "detail": "Paper not found."}, status_code=404)
        if row_author[0] != current_user.get("name"):
            return JSONResponse({"error": "forbidden", "detail": "You do not own this paper."}, status_code=403)

    # Build dynamic SET clause for non-None fields only
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        return JSONResponse({"error": "no_fields", "detail": "No fields to update."}, status_code=400)

    set_parts = [f"`{k}` = :{k}" for k in updates]
    set_clause = ", ".join(set_parts)
    updates["paper_id"] = paper_id

    db.execute(text(
        f"UPDATE `#__eaiou_papers` SET {set_clause} WHERE id = :paper_id"
    ), updates)
    db.commit()

    log_api_call(db, f"/api/v1/papers/{paper_id}", "PATCH",
                 hashlib.sha256(str(updates).encode()).hexdigest(), 200)

    # Return updated paper
    updated = db.execute(text(
        "SELECT id, paper_uuid, cosmoid, title, abstract, author_name, orcid, "
        "authorship_mode, status, q_signal, q_overall, keywords, ai_disclosure_level "
        "FROM `#__eaiou_papers` WHERE id = :id"
    ), {"id": paper_id}).mappings().first()

    if updated is None:
        return JSONResponse({"error": "not_found", "detail": "Paper not found."}, status_code=404)

    return _strip_sealed(dict(updated))


# ── 5. GET /papers/{id}/workflow — workflow.get_state ────────────────────────

@router.get("/papers/{paper_id}/workflow")
async def workflow_get_state(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(optional_auth),
):
    row = db.execute(text(
        "SELECT status FROM `#__eaiou_papers` WHERE id = :id"
    ), {"id": paper_id}).fetchone()

    if row is None:
        return JSONResponse({"error": "not_found", "detail": "Paper not found."}, status_code=404)

    current_state = row[0]
    groups = set(current_user.get("groups", [])) if current_user else set()
    is_editor_plus = bool({"editor", "eic", "admin"} & groups)

    available_transitions = None
    if is_editor_plus:
        available_transitions = _TRANSITIONS.get(current_state, [])

    return {
        "paper_id": paper_id,
        "current_state": current_state,
        "available_transitions": available_transitions,
    }


# ── 6. POST /papers/{id}/workflow/transition — workflow.transition ────────────

@router.post("/papers/{paper_id}/workflow/transition")
async def workflow_transition(
    paper_id: int,
    body: WorkflowTransition,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    groups = set(current_user.get("groups", []))

    # Get current state
    row = db.execute(text(
        "SELECT status, author_name FROM `#__eaiou_papers` WHERE id = :id"
    ), {"id": paper_id}).fetchone()

    if row is None:
        return JSONResponse({"error": "not_found", "detail": "Paper not found."}, status_code=404)

    current_state = row[0]
    paper_author  = row[1]

    # ACL: submitting → require_author + ownership; all others → require_editor
    if body.target_state == "submitted":
        if not ({"author", "admin", "editor"} & groups):
            return JSONResponse({"error": "forbidden", "detail": "Author access required."}, status_code=403)
        if not ({"admin", "editor"} & groups) and paper_author != current_user.get("name"):
            return JSONResponse({"error": "forbidden", "detail": "You do not own this paper."}, status_code=403)
    else:
        if not ({"editor", "eic", "admin"} & groups):
            return JSONResponse({"error": "forbidden", "detail": "Editor access required."}, status_code=403)

    # Validate transition
    allowed = _TRANSITIONS.get(current_state, [])
    if body.target_state not in allowed:
        return JSONResponse(
            {"error": "invalid_transition",
             "detail": f"Cannot transition from '{current_state}' to '{body.target_state}'. Allowed: {allowed}"},
            status_code=422,
        )

    # Build SET clause with optional seal timestamps
    now = datetime.now(timezone.utc)
    set_parts = ["status = :target_state"]
    params: dict = {"target_state": body.target_state, "paper_id": paper_id}

    if body.target_state == "submitted":
        set_parts.append("submission_sealed_at = :now")
        params["now"] = now
    elif body.target_state == "accepted":
        set_parts.append("acceptance_sealed_at = :now")
        params["now"] = now

    set_clause = ", ".join(set_parts)
    db.execute(text(
        f"UPDATE `#__eaiou_papers` SET {set_clause} WHERE id = :paper_id"
    ), params)
    db.commit()

    log_api_call(db, f"/api/v1/papers/{paper_id}/workflow/transition", "POST",
                 hashlib.sha256(body.target_state.encode()).hexdigest(), 200)

    return {"paper_id": paper_id, "old_state": current_state, "new_state": body.target_state}


# ── 7. POST /papers/{paper_id}/attribution — contribution.create ──────────────

@router.post("/papers/{paper_id}/attribution")
async def contribution_create(
    paper_id: int,
    body: ContributionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_author),
):
    now = datetime.now(timezone.utc)
    db.execute(text(
        "INSERT INTO `#__eaiou_attribution_log` "
        "(paper_id, contributor_name, orcid, role_description, contribution_type, "
        "is_human, is_ai, ai_tool_used, created) "
        "VALUES (:paper_id, :name, :orcid, :role, :ctype, :is_human, :is_ai, :ai_tool, :now)"
    ), {
        "paper_id": paper_id,
        "name":     body.contributor_name,
        "orcid":    body.orcid,
        "role":     body.role_description,
        "ctype":    body.contribution_type,
        "is_human": int(body.is_human),
        "is_ai":    int(body.is_ai),
        "ai_tool":  body.ai_tool_used,
        "now":      now,
    })
    db.commit()

    result = db.execute(text(
        "SELECT LAST_INSERT_ID() AS id"
    )).fetchone()

    log_api_call(db, f"/api/v1/papers/{paper_id}/attribution", "POST",
                 hashlib.sha256(body.contributor_name.encode()).hexdigest(), 201)

    return JSONResponse(status_code=201, content={"attribution_id": result[0], "paper_id": paper_id})


# ── 8. GET /papers/{paper_id}/attribution — contribution.list_by_paper ────────

@router.get("/papers/{paper_id}/attribution")
async def contribution_list(paper_id: int, db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT id, paper_id, contributor_name, orcid, role_description, "
        "contribution_type, is_human, is_ai, ai_tool_used, created "
        "FROM `#__eaiou_attribution_log` "
        "WHERE paper_id = :pid AND (state IS NULL OR state != -2)"
    ), {"pid": paper_id}).mappings().all()

    return {"attributions": [dict(r) for r in rows], "paper_id": paper_id}


# ── 9. POST /ai/sessions — intellid.create ────────────────────────────────────

@router.post("/ai/sessions")
async def ai_session_create(
    body: AISessionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    now = datetime.now(timezone.utc)

    # Parse optional datetime strings
    start_time = None
    end_time   = None
    if body.start_time:
        try:
            start_time = datetime.fromisoformat(body.start_time)
        except ValueError:
            pass
    if body.end_time:
        try:
            end_time = datetime.fromisoformat(body.end_time)
        except ValueError:
            pass

    db.execute(text(
        "INSERT INTO `#__eaiou_ai_sessions` "
        "(paper_id, session_label, ai_model_name, start_time, end_time, "
        "tokens_in, tokens_out, redaction_status, session_notes, created) "
        "VALUES (:paper_id, :label, :model, :start, :end, "
        ":tin, :tout, :redact, :notes, :now)"
    ), {
        "paper_id": body.paper_id,
        "label":    body.session_label,
        "model":    body.ai_model_name,
        "start":    start_time,
        "end":      end_time,
        "tin":      body.tokens_in,
        "tout":     body.tokens_out,
        "redact":   body.redaction_status,
        "notes":    body.session_notes,
        "now":      now,
    })
    db.commit()

    result = db.execute(text("SELECT LAST_INSERT_ID() AS id")).fetchone()

    log_api_call(db, "/api/v1/ai/sessions", "POST",
                 hashlib.sha256(body.session_label.encode()).hexdigest(), 201)

    return JSONResponse(status_code=201, content={"session_id": result[0], "paper_id": body.paper_id})


# ── 10. GET /ai/sessions — intellid.list ─────────────────────────────────────

@router.get("/ai/sessions")
async def ai_session_list(
    paper_id: Optional[int] = None,
    model: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_reviewer),
):
    where = []
    params: dict = {}
    if paper_id is not None:
        where.append("paper_id = :paper_id")
        params["paper_id"] = paper_id
    if model:
        where.append("ai_model_name = :model")
        params["model"] = model

    where_clause = ("WHERE " + " AND ".join(where)) if where else ""

    rows = db.execute(text(
        f"SELECT id, paper_id, session_label, ai_model_name, start_time, end_time, "
        f"tokens_in, tokens_out, redaction_status, session_notes, created "
        f"FROM `#__eaiou_ai_sessions` {where_clause} ORDER BY id DESC"
    ), params).mappings().all()

    return {"sessions": [dict(r) for r in rows]}


# ── 11. GET /users/{id} — user.get ───────────────────────────────────────────

@router.get("/users/{user_id}")
async def user_get(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    # Self or editor/admin only
    groups = set(current_user.get("groups", []))
    if current_user["id"] != user_id and not ({"editor", "admin"} & groups):
        return JSONResponse({"error": "forbidden", "detail": "Access denied."}, status_code=403)

    row = db.execute(text(
        "SELECT id, username, display_name, orcid, active "
        "FROM `#__eaiou_users` WHERE id = :id"
    ), {"id": user_id}).mappings().first()

    if row is None:
        return JSONResponse({"error": "not_found", "detail": "User not found."}, status_code=404)

    user_groups = [
        r["name"] for r in db.execute(text(
            "SELECT g.name FROM `#__eaiou_groups` g "
            "JOIN `#__eaiou_user_groups` ug ON ug.group_id = g.id "
            "WHERE ug.user_id = :uid"
        ), {"uid": user_id}).mappings().all()
    ]

    result = dict(row)
    result["groups"] = user_groups
    return result


# ── 12. GET /users — user.list ────────────────────────────────────────────────

@router.get("/users")
async def user_list(
    group: Optional[str] = None,
    has_orcid: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    where = []
    params: dict = {}

    if group:
        where.append(
            "u.id IN (SELECT ug.user_id FROM `#__eaiou_user_groups` ug "
            "JOIN `#__eaiou_groups` g ON g.id = ug.group_id WHERE g.name = :group)"
        )
        params["group"] = group
    if has_orcid:
        where.append("u.orcid IS NOT NULL AND u.orcid != ''")

    where_clause = ("WHERE " + " AND ".join(where)) if where else ""

    rows = db.execute(text(
        f"SELECT u.id, u.username, u.display_name, u.orcid, u.active "
        f"FROM `#__eaiou_users` u {where_clause} ORDER BY u.id"
    ), params).mappings().all()

    # Attach groups for each user
    result = []
    for r in rows:
        user_dict = dict(r)
        user_groups = [
            g["name"] for g in db.execute(text(
                "SELECT g.name FROM `#__eaiou_groups` g "
                "JOIN `#__eaiou_user_groups` ug ON ug.group_id = g.id "
                "WHERE ug.user_id = :uid"
            ), {"uid": r["id"]}).mappings().all()
        ]
        user_dict["groups"] = user_groups
        result.append(user_dict)

    return {"users": result}


# ── 13. POST /papers/{paper_id}/qsignal/compute — qscore.compute ─────────────

@router.post("/papers/{paper_id}/qsignal/compute")
async def qscore_compute(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_editor),
):
    # Try quality_signals first, then fall back to review_logs rubric scores
    qs_rows = db.execute(text(
        "SELECT q_overall, q_originality, q_methodology, q_transparency, "
        "q_ai_disclosure, q_crossdomain "
        "FROM `#__eaiou_quality_signals` WHERE paper_id = :pid AND state IS NULL "
        "ORDER BY id DESC LIMIT 10"
    ), {"pid": paper_id}).mappings().all()

    if qs_rows:
        # Average across existing signal rows
        def avg_col(col):
            vals = [float(r[col]) for r in qs_rows if r[col] is not None]
            return sum(vals) / len(vals) if vals else None

        overall      = avg_col("q_overall")
        originality  = avg_col("q_originality")
        methodology  = avg_col("q_methodology")
        transparency = avg_col("q_transparency")
        ai_disclosure = avg_col("q_ai_disclosure")
        crossdomain  = avg_col("q_crossdomain")
    else:
        # Fall back to review_logs rubric scores (scale 1-5 → 0-1)
        rl_rows = db.execute(text(
            "SELECT rubric_overall, rubric_originality, rubric_methodology, "
            "rubric_transparency, rubric_ai_disclosure, rubric_crossdomain "
            "FROM `#__eaiou_review_logs` WHERE paper_id = :pid "
            "AND state IS NULL ORDER BY id DESC LIMIT 10"
        ), {"pid": paper_id}).mappings().all()

        if not rl_rows:
            return JSONResponse(
                {"error": "no_data", "detail": "No review data found for this paper."},
                status_code=404,
            )

        def avg_rubric(col):
            vals = [r[col] for r in rl_rows if r[col] is not None]
            if not vals:
                return None
            return sum(vals) / len(vals) / 5.0  # Normalize 1-5 → 0-1 scale

        overall      = avg_rubric("rubric_overall")
        originality  = avg_rubric("rubric_originality")
        methodology  = avg_rubric("rubric_methodology")
        transparency = avg_rubric("rubric_transparency")
        ai_disclosure = avg_rubric("rubric_ai_disclosure")
        crossdomain  = avg_rubric("rubric_crossdomain")

    # Compute weighted q_signal: transparency × 1.5, others × 1.0
    dims = [
        (overall,       1.0),
        (originality,   1.0),
        (methodology,   1.0),
        (transparency,  1.5),
        (ai_disclosure, 1.0),
        (crossdomain,   1.0),
    ]
    weighted_sum = sum(v * w for v, w in dims if v is not None)
    weight_total = sum(w for v, w in dims if v is not None)
    q_signal = round(weighted_sum / weight_total, 4) if weight_total > 0 else None

    now = datetime.now(timezone.utc)

    # Insert new quality_signals row
    db.execute(text(
        "INSERT INTO `#__eaiou_quality_signals` "
        "(paper_id, q_overall, q_originality, q_methodology, q_transparency, "
        "q_ai_disclosure, q_crossdomain, q_signal, computed_at) "
        "VALUES (:pid, :overall, :orig, :meth, :trans, :ai, :cross, :qs, :now)"
    ), {
        "pid":    paper_id,
        "overall": overall,
        "orig":   originality,
        "meth":   methodology,
        "trans":  transparency,
        "ai":     ai_disclosure,
        "cross":  crossdomain,
        "qs":     q_signal,
        "now":    now,
    })

    # Update paper q_signal and q_overall
    db.execute(text(
        "UPDATE `#__eaiou_papers` SET q_signal = :qs, q_overall = :qo WHERE id = :pid"
    ), {"qs": q_signal, "qo": overall, "pid": paper_id})
    db.commit()

    log_api_call(db, f"/api/v1/papers/{paper_id}/qsignal/compute", "POST",
                 hashlib.sha256(str(paper_id).encode()).hexdigest(), 200)

    return {
        "paper_id": paper_id,
        "q_signal": q_signal,
        "breakdown": {
            "overall":       overall,
            "originality":   originality,
            "methodology":   methodology,
            "transparency":  transparency,
            "ai_disclosure": ai_disclosure,
            "crossdomain":   crossdomain,
        },
    }


# ── 14. GET /papers/{paper_id}/qsignal — qscore.get ─────────────────────────

@router.get("/papers/{paper_id}/qsignal")
async def qscore_get(paper_id: int, db: Session = Depends(get_db)):
    row = db.execute(text(
        "SELECT q_signal, q_overall, q_originality, q_methodology, q_transparency, "
        "q_ai_disclosure, q_crossdomain "
        "FROM `#__eaiou_quality_signals` WHERE paper_id = :pid "
        "ORDER BY id DESC LIMIT 1"
    ), {"pid": paper_id}).mappings().first()

    review_count = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_review_logs` WHERE paper_id = :pid"
    ), {"pid": paper_id}).scalar()

    if row is None:
        return {
            "paper_id": paper_id,
            "q_signal": None,
            "breakdown": {
                "overall": None, "originality": None, "methodology": None,
                "transparency": None, "ai_disclosure": None, "crossdomain": None,
            },
            "review_count": review_count,
        }

    return {
        "paper_id": paper_id,
        "q_signal": float(row["q_signal"]) if row["q_signal"] is not None else None,
        "breakdown": {
            "overall":       float(row["q_overall"])       if row["q_overall"]       is not None else None,
            "originality":   float(row["q_originality"])   if row["q_originality"]   is not None else None,
            "methodology":   float(row["q_methodology"])   if row["q_methodology"]   is not None else None,
            "transparency":  float(row["q_transparency"])  if row["q_transparency"]  is not None else None,
            "ai_disclosure": float(row["q_ai_disclosure"]) if row["q_ai_disclosure"] is not None else None,
            "crossdomain":   float(row["q_crossdomain"])   if row["q_crossdomain"]   is not None else None,
        },
        "review_count": review_count,
    }


# ── 15. POST /auth/login — auth.login JSON ────────────────────────────────────

@router.post("/auth/login")
async def auth_login(
    request: Request,
    body: LoginRequest,
    db: Session = Depends(get_db),
):
    from ..security import verify_password, check_login_rate_limit, record_login_attempt

    ip = request.client.host if request.client else "unknown"
    check_login_rate_limit(ip)

    row = db.execute(text(
        "SELECT id, username, display_name, password_hash, active, orcid "
        "FROM `#__eaiou_users` WHERE username = :u"
    ), {"u": body.username}).mappings().first()

    if row is None or not row["active"] or not row["password_hash"] \
            or not verify_password(body.password, row["password_hash"]):
        record_login_attempt(ip)
        return JSONResponse({"error": "invalid_credentials"}, status_code=401)

    # Load groups
    groups = [
        r["name"] for r in db.execute(text(
            "SELECT g.name FROM `#__eaiou_groups` g "
            "JOIN `#__eaiou_user_groups` ug ON ug.group_id = g.id "
            "WHERE ug.user_id = :uid"
        ), {"uid": row["id"]}).mappings().all()
    ]

    request.session["user"] = row["username"]

    return {
        "user_id":  row["id"],
        "username": row["username"],
        "groups":   groups,
        "orcid":    row["orcid"],
    }


# ── 16. GET /auth/permissions — auth.check_permission ────────────────────────

@router.get("/auth/permissions")
async def auth_check_permission(
    action: str,
    paper_id: Optional[int] = None,
    current_user: dict = Depends(require_auth),
):
    groups = set(current_user.get("groups", []))

    _perm_map = {
        "submit_paper":  lambda g: bool({"author", "admin"} & g),
        "review_paper":  lambda g: bool({"reviewer", "editor", "admin"} & g),
        "edit_paper":    lambda g: bool({"editor", "admin"} & g),
        "admin_panel":   lambda g: bool({"admin"} & g),
    }

    if action not in _perm_map:
        return JSONResponse(
            {"error": "unknown_action", "detail": f"Unknown action '{action}'."},
            status_code=400,
        )

    allowed = _perm_map[action](groups)
    reason  = f"User groups: {sorted(groups)}"

    return {"allowed": allowed, "reason": reason}
