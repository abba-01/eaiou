"""
eaiou — Belarc Paper Profile Report
Standalone; no auth required to run an analysis.

Input:  raw paper text (paste of abstract + key sections)
          OR a file uploaded via POST /report/upload (stored in user's drawer)
Output: full structured HTML report covering 6 dimensions:
  1. Coverage Overview (covered / novel / needs-work stats + AI signal)
  2. Gap Fills Table   (covered claims → matched gap → score → age)
  3. Needs Reinforcement (partial-match claims → citation suggestions)
  4. Novel Contributions (novel claims → potential new gaps)
  5. Discipline Profile (inferred field + gap-class distribution)
  6. Recommendations (prioritized action items)

No account required for paste analysis.
Upload requires login; files are stored in the user's personal drawer.
"""

import re
from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Request, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..deps import get_current_user
from ..security import get_csrf_token, validate_csrf
from ..services.coverage import analyze_coverage, CURRENT_YEAR
from ..services.file_extract import (
    validate_file, extract_text, compute_sha256,
    stored_path, stored_rel, save_to_disk, MAX_USER_FILES,
)

router = APIRouter(tags=["report"])
templates = Jinja2Templates(directory="app/templates")


# ── AI signal ─────────────────────────────────────────────────────────────────

_AI_PHRASES = [
    r"\bdelve\b",
    r"\bcomprehensive\b.*\bframework\b",
    r"\bit('s| is) (important|worth|crucial) to note\b",
    r"\bin (this|the) (context|realm)\b",
    r"\bfacilitate\b",
    r"\bleverage\b",
    r"\bcertainly\b",
    r"\babsolutely\b",
    r"\bI('d| would) be happy\b",
]


def _ai_signal(text: str) -> tuple[str, int]:
    hits = sum(1 for p in _AI_PHRASES if re.search(p, text, re.IGNORECASE))
    if hits >= 3:
        return "high", hits
    if hits >= 1:
        return "moderate", hits
    return "low", hits


# ── Discipline inference ───────────────────────────────────────────────────────

_DISCIPLINE_KEYWORDS: dict[str, list[str]] = {
    "computer_science":  ["algorithm", "neural network", "machine learning", "deep learning",
                          "classifier", "embedding", "latency", "throughput", "dataset"],
    "physics":           ["quantum", "relativity", "photon", "cosmology", "hubble",
                          "dark matter", "dark energy", "tensor", "gravitational",
                          "redshift", "supernova", "supernovae", "cepheid", "parsec",
                          "magnitude", "luminosity", "galaxy", "mpc", "distance modulus"],
    "biology":           ["gene", "protein", "cell", "organism", "mutation", "genome",
                          "phenotype", "species", "dna", "rna"],
    "medicine":          ["patient", "clinical", "treatment", "diagnosis", "symptom",
                          "therapy", "drug", "trial", "dose", "hospital"],
    "psychology":        ["cognitive", "behavior", "mental", "emotion", "perception",
                          "memory", "disorder", "anxiety", "depression", "trauma"],
    "economics":         ["market", "price", "demand", "supply", "gdp", "inflation",
                          "trade", "fiscal", "monetary", "wage"],
    "criminal_justice":  ["recidivism", "criminal", "incarceration", "parole",
                          "sentencing", "reentry", "offender", "prison", "probation"],
    "sociology":         ["social", "community", "culture", "inequality", "race",
                          "ethnicity", "norms", "institutions", "class", "stratification"],
    "mathematics":       ["theorem", "proof", "topology", "algebra", "differential",
                          "manifold", "lattice", "eigenvalue", "convergence"],
    "neuroscience":      ["neuron", "cortex", "brain", "synaptic", "dopamine",
                          "fmri", "eeg", "hippocampus", "axon", "synapse"],
}


def _infer_disciplines(text: str) -> list[str]:
    """Return top 3 inferred disciplines by keyword frequency (min 2 hits)."""
    text_lower = text.lower()
    scores: dict[str, int] = {}
    for disc, terms in _DISCIPLINE_KEYWORDS.items():
        score = sum(1 for t in terms if t in text_lower)
        if score >= 2:
            scores[disc] = score
    return sorted(scores, key=lambda d: scores[d], reverse=True)[:3]


# ── Recommendations ───────────────────────────────────────────────────────────

def _generate_recommendations(
    coverage: dict,
    ai_hits: int,
    disciplines: list[str],
) -> list[dict]:
    recs: list[dict] = []
    summary = coverage["summary"]
    total = summary["total"]

    if total == 0:
        recs.append({
            "priority": "high",
            "icon": "fa-triangle-exclamation",
            "text": (
                "No verifiable claims detected. Add explicit result statements "
                "(\"we find\", \"our results show\", \"we demonstrate\") to "
                "improve coverage scoring and help reviewers verify your claims."
            ),
        })
        return recs

    needs_work  = summary["needs_work"]
    novel       = summary["novel"]
    covered     = summary["covered"]
    novel_ratio = novel / total

    if needs_work > 0:
        recs.append({
            "priority": "high",
            "icon": "fa-book-open",
            "text": (
                f"{needs_work} claim(s) have partial literature support "
                f"(appreciated confidence 0.25–0.54). Review the Needs Reinforcement "
                f"section and add direct citations to the suggested gaps to push "
                f"these into the Covered tier."
            ),
        })

    if covered == 0 and total > 0:
        recs.append({
            "priority": "high",
            "icon": "fa-magnifying-glass",
            "text": (
                "No claims strongly match existing literature. Verify that your "
                "argument is explicitly framed as a response to known gaps. "
                "A literature review section that directly names each gap before "
                "claiming to address it will significantly strengthen coverage scoring."
            ),
        })

    if novel > 0:
        recs.append({
            "priority": "medium",
            "icon": "fa-lightbulb",
            "text": (
                f"{novel} claim(s) have no prior literature match in the gap index. "
                f"These represent potential new structural gaps. Consider pinning "
                f"them in gitgap to establish priority before submission — "
                f"\"NAUGHT\" status protects your claim date."
            ),
        })

    if novel_ratio > 0.5 and novel > 2:
        recs.append({
            "priority": "medium",
            "icon": "fa-scale-balanced",
            "text": (
                f"More than half of your claims ({int(novel_ratio*100)}%) are novel "
                f"with no existing match. Reviewers may ask for stronger theoretical "
                f"grounding. Add a 'Gap Analysis' subsection that explicitly positions "
                f"each novel claim against the nearest existing literature."
            ),
        })

    if ai_hits >= 3:
        recs.append({
            "priority": "high",
            "icon": "fa-robot",
            "text": (
                f"AI phrasing density is high ({ai_hits} characteristic phrase(s) "
                f"detected). Disclose AI use in your submission's AI Disclosure "
                f"section. Consider revising affected passages for direct academic voice."
            ),
        })
    elif ai_hits >= 1:
        recs.append({
            "priority": "low",
            "icon": "fa-robot",
            "text": (
                f"Moderate AI phrasing detected ({ai_hits} phrase(s)). "
                f"Ensure AI use is disclosed in your AI Disclosure section if applicable."
            ),
        })

    if len(disciplines) >= 2:
        bridge = " and ".join(d.replace("_", " ") for d in disciplines[:2])
        recs.append({
            "priority": "low",
            "icon": "fa-arrows-left-right",
            "text": (
                f"This paper appears to bridge {bridge}. Explicitly framing the "
                f"methodological transfer in your introduction may strengthen positioning "
                f"and attract cross-disciplinary reviewers."
            ),
        })

    return recs


# ── Helper: fetch drawer files for current user ────────────────────────────────

def _drawer_files(user_id: int, db: Session) -> list:
    return db.execute(
        text("SELECT id, original_name, mime_type, file_size, uploaded_at "
             "FROM `#__eaiou_user_files` "
             "WHERE user_id = :u AND deleted_at IS NULL ORDER BY uploaded_at DESC"),
        {"u": user_id},
    ).mappings().all()


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/report/upload")
async def report_upload(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Upload a PDF, DOCX, or TXT. Extracts text server-side; stores file in user drawer."""
    if not current_user:
        raise HTTPException(status_code=403, detail="Login required to upload files.")

    content = await file.read()
    mime_type = validate_file(content, file.filename or "upload")

    count = db.execute(
        text("SELECT COUNT(*) FROM `#__eaiou_user_files` WHERE user_id = :u AND deleted_at IS NULL"),
        {"u": current_user["id"]},
    ).scalar()
    if count >= MAX_USER_FILES:
        raise HTTPException(
            status_code=429,
            detail=f"File drawer limit ({MAX_USER_FILES}) reached. Delete files to continue.",
        )

    sha256 = compute_sha256(content)

    # Dedup: same user + same content → return existing record without re-storing
    existing = db.execute(
        text("SELECT id, extracted_text, original_name FROM `#__eaiou_user_files` "
             "WHERE user_id = :u AND sha256 = :s AND deleted_at IS NULL"),
        {"u": current_user["id"], "s": sha256},
    ).mappings().first()
    if existing:
        return JSONResponse({
            "file_id": existing["id"],
            "extracted_text": existing["extracted_text"] or "",
            "title": existing["original_name"],
        })

    extracted = extract_text(content, mime_type)
    path = stored_path(current_user["id"], sha256, mime_type)
    save_to_disk(content, path)

    db.execute(
        text("""
            INSERT INTO `#__eaiou_user_files`
                (user_id, original_name, stored_path, mime_type, file_size, sha256, extracted_text, uploaded_at)
            VALUES (:u, :n, :p, :m, :sz, :h, :t, :now)
        """),
        {
            "u":   current_user["id"],
            "n":   file.filename or "upload",
            "p":   stored_rel(current_user["id"], sha256, mime_type),
            "m":   mime_type,
            "sz":  len(content),
            "h":   sha256,
            "t":   extracted,
            "now": datetime.now(timezone.utc).replace(tzinfo=None),
        },
    )
    db.commit()
    file_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
    return JSONResponse({
        "file_id": file_id,
        "extracted_text": extracted,
        "title": file.filename or "upload",
    })


@router.get("/report", response_class=HTMLResponse)
async def report_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Serve the blank report form."""
    # Pre-fill from drawer file if ?file_id= provided
    prefill_text = request.query_params.get("text", "")
    prefill_title = request.query_params.get("title", "")
    file_id_param = request.query_params.get("file_id", "")

    if file_id_param and current_user:
        try:
            fid = int(file_id_param)
            row = db.execute(
                text("SELECT extracted_text, original_name FROM `#__eaiou_user_files` "
                     "WHERE id = :id AND user_id = :u AND deleted_at IS NULL"),
                {"id": fid, "u": current_user["id"]},
            ).mappings().first()
            if row:
                prefill_text = row["extracted_text"] or ""
                prefill_title = prefill_title or row["original_name"]
        except (ValueError, TypeError):
            pass

    drawer = _drawer_files(current_user["id"], db) if current_user else []

    return templates.TemplateResponse(request, "report.html", {
        "report":        None,
        "error":         None,
        "prefill_text":  prefill_text,
        "prefill_title": prefill_title,
        "current_user":  current_user,
        "csrf_token":    get_csrf_token(request),
        "drawer_files":  drawer,
    })


@router.post("/report", response_class=HTMLResponse)
async def generate_report(
    request: Request,
    paper_text:  str = Form(...),
    paper_title: str = Form(""),
    file_id:     int | None = Form(default=None),
    csrf_token:  str = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Run full analysis and render the report document."""
    validate_csrf(request, csrf_token)

    text_input = paper_text.strip()

    # If file_id provided, resolve text from user's drawer (overrides pasted text)
    if file_id and current_user:
        row = db.execute(
            text("SELECT extracted_text FROM `#__eaiou_user_files` "
                 "WHERE id = :id AND user_id = :u AND deleted_at IS NULL"),
            {"id": file_id, "u": current_user["id"]},
        ).mappings().first()
        if row and row["extracted_text"]:
            text_input = row["extracted_text"]

    drawer = _drawer_files(current_user["id"], db) if current_user else []

    if len(text_input) < 100:
        return templates.TemplateResponse(request, "report.html", {
            "report":        None,
            "error":         "Text is too short. Paste at least the abstract and key sections.",
            "prefill_text":  paper_text,
            "prefill_title": paper_title,
            "current_user":  current_user,
            "csrf_token":    get_csrf_token(request),
            "drawer_files":  drawer,
        })

    # Core analyses
    coverage    = analyze_coverage(abstract=text_input, sections=[])
    ai_level, ai_hits = _ai_signal(text_input)
    disciplines = _infer_disciplines(text_input)
    recs        = _generate_recommendations(coverage, ai_hits, disciplines)

    gap_classes = Counter(
        c["best_match"]["gap_class"]
        for c in coverage["claims"]
        if c.get("best_match") and c["best_match"].get("gap_class")
    )

    word_count = len(text_input.split())
    summary    = coverage["summary"]
    total      = max(summary["total"], 1)

    report = {
        "title":         paper_title.strip() or "Untitled Paper",
        "word_count":    word_count,
        "generated_at":  datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "coverage":      coverage,
        "summary":       summary,
        "total":         summary["total"],
        "pct_covered":   round(summary["covered"]    / total * 100),
        "pct_novel":     round(summary["novel"]      / total * 100),
        "pct_needs":     round(summary["needs_work"] / total * 100),
        "ai_level":      ai_level,
        "ai_hits":       ai_hits,
        "disciplines":   disciplines,
        "gap_classes":   dict(gap_classes),
        "recs":          recs,
        "recs_high":     [r for r in recs if r["priority"] == "high"],
        "recs_medium":   [r for r in recs if r["priority"] == "medium"],
        "recs_low":      [r for r in recs if r["priority"] == "low"],
        "claims_covered":    [c for c in coverage["claims"] if c["status"] == "covered"],
        "claims_needs_work": [c for c in coverage["claims"] if c["status"] == "needs_work"],
        "claims_novel":      [c for c in coverage["claims"] if c["status"] == "novel"],
    }

    return templates.TemplateResponse(request, "report.html", {
        "report":        report,
        "error":         None,
        "prefill_text":  "",
        "prefill_title": "",
        "current_user":  current_user,
        "csrf_token":    get_csrf_token(request),
        "drawer_files":  drawer,
    })
