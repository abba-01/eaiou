"""
eaiou — Intelligence router
Structure Intelligence: paper scaffold from hypothesis + gap.
Audit Intelligence: adversarial whole-document audit (fresh context, no construction involvement).

Requires: ANTHROPIC_API_KEY in environment.
"""

import json
import os
from datetime import datetime, timezone

import httpx

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/author/api", tags=["intelligence"])

STRUCTURE_SYSTEM = """You are an academic paper structure specialist embedded in eaiou, a research integrity platform.

Your ONLY job is to generate the section structure for a research paper — not to write content, not to argue points, not to generate prose.

Given a research hypothesis and optionally a gap declaration (an unresolved research question the paper responds to), output a JSON object representing the paper's full structural skeleton.

Rules:
- Identify the paper type from the hypothesis: empirical (IMRaD), theoretical, review, or mixed
- Generate sections appropriate for that type
- Each section's "focus" must be 1-2 sentences describing what THIS specific paper's version of that section must address — derived from the provided hypothesis and gap, not generic boilerplate
- Subsections are optional; include only when the structure genuinely requires subdivision
- Do not write any argument, claim, or content — only structural annotations
- If gap_declaration is provided, anchor the Introduction and Discussion to the gap explicitly

Output ONLY valid JSON. No markdown. No explanation. Exactly this format:
{
  "format": "IMRaD" | "Theoretical" | "Review" | "Mixed",
  "sections": [
    {
      "name": "Section name",
      "focus": "What this section must address for this specific paper.",
      "subsections": []
    }
  ]
}"""


class StructureRequest(BaseModel):
    title: str = ""
    hypothesis: str = ""
    gap_declaration: str = ""
    keywords: str = ""


@router.post("/structure")
async def generate_structure(
    body: StructureRequest,
    current_user=Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="ANTHROPIC_API_KEY not configured. Add it to .env to enable Structure Intelligence."
        )

    if not body.hypothesis.strip() and not body.title.strip():
        raise HTTPException(status_code=422, detail="Provide at least a title or hypothesis.")

    user_prompt = f"""Title: {body.title or '(not yet set)'}
Hypothesis / abstract so far: {body.hypothesis or '(not yet written)'}
Gap declaration: {body.gap_declaration or '(no gap anchor)'}
Keywords: {body.keywords or '(none)'}"""

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=STRUCTURE_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = message.content[0].text.strip()

    try:
        structure = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Structure Intelligence returned malformed output.")

    return JSONResponse(content=structure)


# ── Audit Intelligence ────────────────────────────────────────────────────────

AUDIT_SYSTEM = """You are an adversarial scientific auditor. You have NO prior involvement in this paper's construction. You did not help write it. You have no investment in the argument.

Your job is to find what does not hold. Read the complete document and produce a structured audit report.

You audit for:
- Logical gaps: claims that do not follow from what precedes them
- Unsupported assertions: claims made without stated evidence or reasoning
- Internal inconsistency: sections that contradict each other
- Gap coverage: does the paper actually address the gap it claims to address?
- Methodology gaps: approach stated but not sufficient to support conclusions
- Unstated assumptions: reasoning that only works if something unstated is true
- Scope violations: conclusions that exceed what the methodology can support

CRITICAL RULE — UNDEFINED VALUES:
If the document contains placeholders, blanks, or sections marked as undefined or not yet written, DO NOT invent what those sections might say. DO NOT project a trajectory. Flag them as UNDEFINED and note that the audit cannot proceed on those sections until they are populated. Never fill gaps with assumptions about what the author intends.

Report findings only. No suggestions. No praise. No improvements. Only what does not hold and why.

Output ONLY valid JSON. No markdown. No explanation:
{
  "findings": [
    {
      "code": "FINDING_CODE",
      "section": "section name or 'whole document'",
      "severity": "critical|major|minor",
      "observation": "what does not hold and specifically why"
    }
  ],
  "undefined_sections": ["list of section names that are empty or undefined"],
  "is_clean": false,
  "audit_note": "one sentence overall characterization"
}"""


class AuditRequest(BaseModel):
    paper_id: int


def _build_document(paper, sections) -> str:
    """Assemble the full document text for audit. Marks undefined sections explicitly."""
    parts = []
    parts.append(f"TITLE: {paper['title'] or '[UNDEFINED]'}")
    parts.append(f"\nABSTRACT:\n{paper['abstract'] or '[UNDEFINED — section not yet written]'}")

    if paper.get('keywords'):
        parts.append(f"\nKEYWORDS: {paper['keywords']}")

    if paper.get('gitgap_gap_id'):
        decl = paper.get('gap_declaration_text') or '[gap declaration not loaded]'
        parts.append(f"\nGAP ANCHOR (this paper responds to):\n{decl}")

    if sections:
        parts.append("\n--- SECTIONS ---")
        for s in sections:
            name = s['section_name']
            content = s['section_content'] or s['section_notes']
            if content and content.strip():
                parts.append(f"\n[{name}]\n{content.strip()}")
            else:
                parts.append(f"\n[{name}]\n[UNDEFINED — section not yet written]")
    else:
        parts.append("\n--- SECTIONS ---\n[No sections written yet — paper is abstract only]")

    return "\n".join(parts)


@router.post("/audit/{paper_id}")
async def audit_document(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503,
            detail="ANTHROPIC_API_KEY not configured.")

    paper = db.execute(text(
        "SELECT p.id, p.title, p.abstract, p.keywords, p.gitgap_gap_id, "
        "       g.declaration_text AS gap_declaration_text "
        "FROM `#__eaiou_papers` p "
        "LEFT JOIN gap_anchor_cache g ON g.gap_id = p.gitgap_gap_id "
        "WHERE p.id = :id"
    ), {"id": paper_id}).mappings().first()

    # gap_anchor_cache may not exist yet — fall back gracefully
    if paper is None:
        paper = db.execute(text(
            "SELECT id, title, abstract, keywords, gitgap_gap_id "
            "FROM `#__eaiou_papers` WHERE id = :id"
        ), {"id": paper_id}).mappings().first()
        if paper is None:
            raise HTTPException(status_code=404, detail="Paper not found")
        paper = dict(paper)
        paper['gap_declaration_text'] = None

    sections = db.execute(text(
        "SELECT section_name, section_notes, section_content "
        "FROM `#__eaiou_paper_sections` "
        "WHERE paper_id = :pid ORDER BY section_order ASC"
    ), {"pid": paper_id}).mappings().all()

    # Determine next round number
    last_round = db.execute(text(
        "SELECT MAX(round_number) FROM `#__eaiou_volley_log` WHERE paper_id = :pid"
    ), {"pid": paper_id}).scalar() or 0
    round_number = last_round + 1

    document = _build_document(dict(paper), [dict(s) for s in sections])
    model = "claude-sonnet-4-6"

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=2048,
        system=AUDIT_SYSTEM,
        messages=[{"role": "user", "content": f"Audit this document:\n\n{document}"}],
    )

    raw = message.content[0].text.strip()
    try:
        audit = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Audit Intelligence returned malformed output.")

    now = datetime.now(timezone.utc)
    finding_count = len(audit.get("findings", []))
    is_clean = audit.get("is_clean", False) and finding_count == 0

    db.execute(text(
        "INSERT INTO `#__eaiou_volley_log` "
        "(paper_id, round_number, auditor_model, document_snapshot, "
        "findings_json, finding_count, is_clean, audited_at) "
        "VALUES (:pid, :rnd, :model, :doc, :findings, :count, :clean, :now)"
    ), {
        "pid":      paper_id,
        "rnd":      round_number,
        "model":    model,
        "doc":      document,
        "findings": json.dumps(audit),
        "count":    finding_count,
        "clean":    1 if is_clean else 0,
        "now":      now,
    })

    # Advance pipeline stage
    db.execute(text(
        "UPDATE `#__eaiou_papers` SET pipeline_stage = 'volley' WHERE id = :id"
    ), {"id": paper_id})
    db.commit()

    return JSONResponse(content={
        "round":              round_number,
        "finding_count":      finding_count,
        "is_clean":           is_clean,
        "findings":           audit.get("findings", []),
        "undefined_sections": audit.get("undefined_sections", []),
        "audit_note":         audit.get("audit_note", ""),
        "auditor_model":      model,
    })


# ── Interrogation — expert-routed dialogue ───────────────────────────────────

EXPERT_ROUTER_SYSTEM = """You are an expert domain classifier. Given a research question, identify the single most relevant expert domain that should answer it.

Return ONLY a JSON object:
{
  "domain": "short domain name",
  "expert_title": "full expert title for system prompt",
  "rationale": "one sentence why this domain"
}

Examples:
- Question about sample size → {"domain": "statistics", "expert_title": "Research statistician specializing in inferential methods and study design", "rationale": "..."}
- Question about falsifiability → {"domain": "philosophy_of_science", "expert_title": "Philosopher of science specializing in scientific methodology and epistemology", "rationale": "..."}
- Question about historical precedent → {"domain": "history_of_science", "expert_title": "Historian of science specializing in the development of the relevant field", "rationale": "..."}

Be specific. "Scientist" is not a domain. Identify the precise expertise the question requires."""

INTERROGATION_SYSTEM_TEMPLATE = """You are a {expert_title}.

You are embedded in an active research investigation. You have been given the full context of the work so far. Your job is to engage with the author's question from your domain expertise — not to answer generically, but to bring your specific analytical lens to this specific investigation.

Rules:
- Respond from your domain's perspective and methodology
- Challenge assumptions that your domain would challenge
- Surface what your domain knows that the author may not have considered
- Do not invent data or findings — reason from stated material and your domain knowledge
- If the question touches undefined territory (sections not yet written, data not yet collected), say so explicitly — do not project or invent
- You are a member of the author's investigation team. The author leads. You advise.

Investigation context:
{context}"""


class InterrogationRequest(BaseModel):
    paper_id: int
    question: str
    expert_domain: str = ""   # optional — if blank, auto-route


def _build_investigation_context(paper: dict, sections: list, volley_history: list,
                                  interrogation_history: list) -> str:
    parts = [f"GAP: {paper.get('gitgap_gap_id') or 'none'}"]
    if paper.get('gap_declaration_text'):
        parts.append(f"Gap declaration: {paper['gap_declaration_text']}")
    parts.append(f"\nTitle: {paper.get('title') or '[untitled]'}")
    parts.append(f"Abstract/Hypothesis: {paper.get('abstract') or '[not yet written]'}")

    if sections:
        parts.append("\nSections established:")
        for s in sections:
            status = "written" if (s.get('section_content') or s.get('section_notes')) else "UNDEFINED"
            parts.append(f"  [{status}] {s['section_name']}")

    if interrogation_history:
        parts.append("\nPrior interrogation (most recent 3 exchanges):")
        for entry in interrogation_history[-3:]:
            parts.append(f"  Q [{entry.get('expert_domain','?')}]: {entry['question'][:200]}")
            parts.append(f"  A: {entry['response'][:300]}")

    if volley_history:
        last = volley_history[-1]
        parts.append(f"\nLast audit round {last.get('round_number')}: "
                     f"{last.get('finding_count')} findings, "
                     f"{'clean' if last.get('is_clean') else 'unresolved'}")

    return "\n".join(parts)


@router.post("/interrogate")
async def interrogate(
    body: InterrogationRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured.")

    if not body.question.strip():
        raise HTTPException(status_code=422, detail="Question cannot be empty.")

    client = anthropic.Anthropic(api_key=api_key)

    # Load investigation context
    paper = db.execute(text(
        "SELECT id, title, abstract, keywords, gitgap_gap_id "
        "FROM `#__eaiou_papers` WHERE id = :id"
    ), {"id": body.paper_id}).mappings().first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    paper = dict(paper)
    paper['gap_declaration_text'] = None

    if paper.get('gitgap_gap_id'):
        try:
            with httpx.Client(timeout=5) as hx:
                r = hx.get(f"{os.getenv('GITGAP_API_URL','http://127.0.0.1:8001')}/gaps/{paper['gitgap_gap_id']}")
                if r.status_code == 200:
                    paper['gap_declaration_text'] = r.json().get('declaration_text', '')
        except Exception:
            pass

    sections = db.execute(text(
        "SELECT section_name, section_notes, section_content "
        "FROM `#__eaiou_paper_sections` WHERE paper_id = :pid ORDER BY section_order"
    ), {"pid": body.paper_id}).mappings().all()

    volley_history = db.execute(text(
        "SELECT round_number, finding_count, is_clean "
        "FROM `#__eaiou_volley_log` WHERE paper_id = :pid ORDER BY round_number"
    ), {"pid": body.paper_id}).mappings().all()

    interrogation_history = db.execute(text(
        "SELECT question, response, expert_domain, asked_at "
        "FROM `#__eaiou_interrogation_log` WHERE paper_id = :pid ORDER BY asked_at DESC LIMIT 10"
    ), {"pid": body.paper_id}).mappings().all() if _interrogation_table_exists(db) else []

    context = _build_investigation_context(
        paper,
        [dict(s) for s in sections],
        [dict(v) for v in volley_history],
        [dict(i) for i in interrogation_history],
    )

    # Step 1: Route to expert domain
    if body.expert_domain.strip():
        expert_domain = body.expert_domain.strip()
        expert_title = expert_domain.replace("_", " ").title() + " specialist"
    else:
        router_msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            system=EXPERT_ROUTER_SYSTEM,
            messages=[{"role": "user", "content": f"Question: {body.question}"}],
        )
        try:
            routing = json.loads(router_msg.content[0].text.strip())
            expert_domain = routing.get("domain", "generalist")
            expert_title  = routing.get("expert_title", "Research specialist")
        except Exception:
            expert_domain = "generalist"
            expert_title  = "Research specialist"

    # Step 2: Expert response with full investigation context
    system_prompt = INTERROGATION_SYSTEM_TEMPLATE.format(
        expert_title=expert_title,
        context=context,
    )
    response_msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": body.question}],
    )
    response_text = response_msg.content[0].text.strip()

    # Log the exchange
    _log_interrogation(db, body.paper_id, body.question, response_text, expert_domain, expert_title)

    return JSONResponse(content={
        "expert_domain": expert_domain,
        "expert_title":  expert_title,
        "question":      body.question,
        "response":      response_text,
    })


def _interrogation_table_exists(db: Session) -> bool:
    try:
        db.execute(text("SELECT 1 FROM `#__eaiou_interrogation_log` LIMIT 1"))
        return True
    except Exception:
        return False


def _log_interrogation(db: Session, paper_id: int, question: str,
                        response: str, domain: str, expert_title: str):
    try:
        db.execute(text(
            "INSERT INTO `#__eaiou_interrogation_log` "
            "(paper_id, question, response, expert_domain, expert_title, asked_at) "
            "VALUES (:pid, :q, :r, :d, :et, :now)"
        ), {
            "pid": paper_id, "q": question, "r": response,
            "d": domain, "et": expert_title,
            "now": datetime.now(timezone.utc),
        })
        db.commit()
    except Exception:
        db.rollback()


# ── Intelligence Modules: Read · Red Team · Defend ───────────────────────────
# eaiou owns the system prompts. Providers choose the model. Standard is fixed.

MODULE_READ_SYSTEM = """You are an intelligence reading a research paper in progress.

Read the full document carefully. Return a structured first-read report covering:
- What is structurally present and coherent
- Which sections are UNDEFINED or not yet written
- Internal tensions between any stated claims
- Your first-read impression of where this work stands

Observe only. Do not suggest edits. Do not rewrite anything. Report what you see."""


MODULE_RED_TEAM_SYSTEM = """You are the red team for this research paper.

Your job: find what does not hold. Attack from your strongest position.

Rules:
- Challenge specific claims — not generic criticism
- Use internal contradictions where they exist
- Distinguish what is asserted from what is demonstrated
- Flag UNDEFINED sections — do not invent around them
- Every challenge must be grounded in the document's own text or identifiable gaps

{focus_instruction}

Be the strongest possible adversarial challenge to this work as it currently stands."""


MODULE_DEFEND_SYSTEM = """You are the defender of this research paper.

Argue for the positions taken in this document. Draw only from what the document contains — its stated reasoning, methodology, and evidence.

Rules:
- Do not manufacture defenses the document doesn't support
- Acknowledge real weaknesses precisely, then defend what can be defended
- Do not yield ground the document itself earns
- Make the strongest possible case for this work as it stands

{challenge_instruction}"""


class AddModuleRequest(BaseModel):
    role: str                          # 'defender' or 'red_team'
    display_label: str = ""
    provider: str = "anthropic"
    model_id: str = "claude-sonnet-4-6"


class ConfigureModuleRequest(BaseModel):
    display_label: str = ""
    role: str = ""


class ModuleFocusRequest(BaseModel):
    focus: str = ""


def _require_module_apikey():
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured.")
    return key


def _fetch_paper_minimal(paper_id: int, db: Session) -> dict:
    paper = db.execute(text(
        "SELECT id, title, abstract, keywords, gitgap_gap_id "
        "FROM `#__eaiou_papers` WHERE id = :id"
    ), {"id": paper_id}).mappings().first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return {**dict(paper), "gap_declaration_text": None}


def _fetch_sections_minimal(paper_id: int, db: Session) -> list:
    return [dict(s) for s in db.execute(text(
        "SELECT section_name, section_notes, section_content "
        "FROM `#__eaiou_paper_sections` WHERE paper_id = :pid ORDER BY section_order"
    ), {"pid": paper_id}).mappings().all()]


def _run_module_action(module_id: int, paper_id: int, event_type: str,
                        system_prompt: str, user_content: str,
                        model_id: str, focus: str, db: Session) -> str:
    api_key = _require_module_apikey()
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model_id,
        max_tokens=1500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}],
    )
    response_text = message.content[0].text.strip()
    now = datetime.now(timezone.utc)
    db.execute(text(
        "INSERT INTO `#__eaiou_module_events` "
        "(module_id, paper_id, event_type, focus_text, response_text, "
        " tokens_in, tokens_out, occurred_at) "
        "VALUES (:mid, :pid, :etype, :focus, :resp, :tin, :tout, :now)"
    ), {
        "mid": module_id, "pid": paper_id, "etype": event_type,
        "focus": focus or None, "resp": response_text,
        "tin": message.usage.input_tokens,
        "tout": message.usage.output_tokens,
        "now": now,
    })
    db.execute(text(
        "UPDATE `#__eaiou_intelligence_modules` "
        "SET status = 'active', last_event_at = :now WHERE id = :mid"
    ), {"now": now, "mid": module_id})
    db.commit()
    return response_text


@router.get("/modules/{paper_id}")
async def list_modules(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    rows = db.execute(text(
        "SELECT m.id, m.display_label, m.role, m.provider, m.model_id, "
        "       m.status, m.last_event_at, "
        "       e.event_type AS last_event_type, "
        "       e.response_text AS last_response "
        "FROM `#__eaiou_intelligence_modules` m "
        "LEFT JOIN `#__eaiou_module_events` e ON e.id = ("
        "    SELECT id FROM `#__eaiou_module_events` "
        "    WHERE module_id = m.id ORDER BY occurred_at DESC LIMIT 1"
        ") "
        "WHERE m.paper_id = :pid ORDER BY m.created ASC"
    ), {"pid": paper_id}).mappings().all()

    return JSONResponse(content={"modules": [
        {k: (str(v) if hasattr(v, 'isoformat') else v) for k, v in dict(r).items()}
        for r in rows
    ]})


@router.post("/modules/{paper_id}")
async def add_module(
    paper_id: int,
    body: AddModuleRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")
    if body.role not in ("defender", "red_team"):
        raise HTTPException(status_code=422, detail="Role must be 'defender' or 'red_team'.")
    if not db.execute(text("SELECT id FROM `#__eaiou_papers` WHERE id = :id"),
                      {"id": paper_id}).scalar():
        raise HTTPException(status_code=404, detail="Paper not found")

    now = datetime.now(timezone.utc)
    db.execute(text(
        "INSERT INTO `#__eaiou_intelligence_modules` "
        "(paper_id, display_label, role, provider, model_id, status, created) "
        "VALUES (:pid, :label, :role, :provider, :model, 'not_loaded', :now)"
    ), {
        "pid": paper_id,
        "label": body.display_label.strip() or None,
        "role": body.role,
        "provider": body.provider,
        "model": body.model_id,
        "now": now,
    })
    db.commit()
    module_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
    return JSONResponse(content={"module_id": module_id, "role": body.role})


@router.patch("/modules/{paper_id}/{module_id}")
async def configure_module(
    paper_id: int,
    module_id: int,
    body: ConfigureModuleRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")
    updates, params = [], {"mid": module_id, "pid": paper_id}
    if body.display_label is not None:
        updates.append("display_label = :label")
        params["label"] = body.display_label.strip() or None
    if body.role in ("defender", "red_team"):
        updates.append("role = :role")
        params["role"] = body.role
    if not updates:
        return JSONResponse(content={"status": "no_change"})
    db.execute(text(
        f"UPDATE `#__eaiou_intelligence_modules` SET {', '.join(updates)} "
        "WHERE id = :mid AND paper_id = :pid"
    ), params)
    db.commit()
    return JSONResponse(content={"status": "updated"})


@router.post("/modules/{paper_id}/{module_id}/read")
async def module_read(
    paper_id: int,
    module_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")
    module = db.execute(text(
        "SELECT id, model_id FROM `#__eaiou_intelligence_modules` "
        "WHERE id = :mid AND paper_id = :pid"
    ), {"mid": module_id, "pid": paper_id}).mappings().first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    paper = _fetch_paper_minimal(paper_id, db)
    sections = _fetch_sections_minimal(paper_id, db)
    document = _build_document(paper, sections)

    response = _run_module_action(
        module_id, paper_id, "read",
        MODULE_READ_SYSTEM,
        f"Read this document:\n\n{document}",
        module["model_id"], "", db
    )
    return JSONResponse(content={"event_type": "read", "response": response})


@router.post("/modules/{paper_id}/{module_id}/redteam")
async def module_redteam(
    paper_id: int,
    module_id: int,
    body: ModuleFocusRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")
    module = db.execute(text(
        "SELECT id, model_id, status FROM `#__eaiou_intelligence_modules` "
        "WHERE id = :mid AND paper_id = :pid"
    ), {"mid": module_id, "pid": paper_id}).mappings().first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    if module["status"] == "not_loaded":
        raise HTTPException(status_code=422, detail="Module must Read the document first.")

    focus = body.focus.strip()
    system = MODULE_RED_TEAM_SYSTEM.format(
        focus_instruction=f"Focus your challenge on: {focus}" if focus
                          else "Challenge the full document — no section is exempt."
    )
    paper = _fetch_paper_minimal(paper_id, db)
    sections = _fetch_sections_minimal(paper_id, db)
    document = _build_document(paper, sections)

    response = _run_module_action(
        module_id, paper_id, "red_team", system,
        f"Red team this document:\n\n{document}",
        module["model_id"], focus, db
    )
    return JSONResponse(content={"event_type": "red_team", "response": response})


@router.post("/modules/{paper_id}/{module_id}/defend")
async def module_defend(
    paper_id: int,
    module_id: int,
    body: ModuleFocusRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")
    module = db.execute(text(
        "SELECT id, model_id, status FROM `#__eaiou_intelligence_modules` "
        "WHERE id = :mid AND paper_id = :pid"
    ), {"mid": module_id, "pid": paper_id}).mappings().first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    if module["status"] == "not_loaded":
        raise HTTPException(status_code=422, detail="Module must Read the document first.")

    focus = body.focus.strip()
    system = MODULE_DEFEND_SYSTEM.format(
        challenge_instruction=f"Defend against this specific challenge: {focus}" if focus
                               else "Defend the document against its most likely criticisms."
    )
    paper = _fetch_paper_minimal(paper_id, db)
    sections = _fetch_sections_minimal(paper_id, db)
    document = _build_document(paper, sections)

    response = _run_module_action(
        module_id, paper_id, "defend", system,
        f"Defend this document:\n\n{document}",
        module["model_id"], focus, db
    )
    return JSONResponse(content={"event_type": "defend", "response": response})


@router.get("/interrogation/{paper_id}")
async def get_interrogation_history(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Returns recent interrogation exchanges for the investigation panel."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    if not _interrogation_table_exists(db):
        return JSONResponse(content={"exchanges": [], "total": 0})

    rows = db.execute(text(
        "SELECT id, question, response, expert_domain, expert_title, asked_at "
        "FROM `#__eaiou_interrogation_log` "
        "WHERE paper_id = :pid ORDER BY asked_at DESC LIMIT 20"
    ), {"pid": paper_id}).mappings().all()

    exchanges = []
    for r in rows:
        d = dict(r)
        d["asked_at"] = str(d["asked_at"]) if d.get("asked_at") else None
        exchanges.append(d)

    total = db.execute(text(
        "SELECT COUNT(*) FROM `#__eaiou_interrogation_log` WHERE paper_id = :pid"
    ), {"pid": paper_id}).scalar() or 0

    return JSONResponse(content={"exchanges": exchanges, "total": total})


class CreateSectionRequest(BaseModel):
    section_name: str
    section_order: int = 0
    section_content: str = ""
    section_notes: str = ""


@router.post("/sections/{paper_id}")
async def create_section(
    paper_id: int,
    body: CreateSectionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new paper section (used by agent team after structure generation)."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required.")
    if not body.section_name.strip():
        raise HTTPException(status_code=422, detail="section_name required.")
    paper = db.execute(
        text("SELECT id FROM `#__eaiou_papers` WHERE id = :id"), {"id": paper_id}
    ).scalar()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")
    db.execute(
        text(
            "INSERT INTO `#__eaiou_paper_sections` "
            "(paper_id, section_name, section_content, section_notes, section_order, seeded_from) "
            "VALUES (:pid, :name, :content, :notes, :ord, 'template')"
        ),
        {
            "pid":     paper_id,
            "name":    body.section_name.strip(),
            "content": body.section_content.strip() or None,
            "notes":   body.section_notes.strip() or None,
            "ord":     body.section_order,
        },
    )
    db.commit()
    section_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
    return JSONResponse(content={"section_id": section_id, "section_name": body.section_name})


class SeedSectionRequest(BaseModel):
    content: str
    seeded_from: str = "interrogation"


@router.post("/sections/{paper_id}/{section_id}/seed")
async def seed_section(
    paper_id: int,
    section_id: int,
    body: SeedSectionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Seeds a section with content from an interrogation response."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    if not body.content.strip():
        raise HTTPException(status_code=422, detail="Content cannot be empty.")

    result = db.execute(text(
        "UPDATE `#__eaiou_paper_sections` "
        "SET section_notes = :content, seeded_from = :source "
        "WHERE id = :sid AND paper_id = :pid AND "
        "(section_notes IS NULL OR section_notes = '')"
    ), {
        "content": body.content.strip(),
        "source":  body.seeded_from,
        "sid":     section_id,
        "pid":     paper_id,
    })

    if result.rowcount == 0:
        # Section already has notes — append rather than overwrite
        db.execute(text(
            "UPDATE `#__eaiou_paper_sections` "
            "SET section_notes = CONCAT(COALESCE(section_notes,''), '\n\n---\n', :content), "
            "    seeded_from = :source "
            "WHERE id = :sid AND paper_id = :pid"
        ), {
            "content": body.content.strip(),
            "source":  body.seeded_from,
            "sid":     section_id,
            "pid":     paper_id,
        })

    db.commit()
    return JSONResponse(content={"seeded": True, "section_id": section_id})


class UpdateSectionContentRequest(BaseModel):
    section_content: str


@router.put("/sections/{paper_id}/{section_id}")
async def update_section_content(
    paper_id: int,
    section_id: int,
    body: UpdateSectionContentRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Direct author edit of section_content from the focus editor modal."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required.")
    row = db.execute(
        text("SELECT id FROM `#__eaiou_paper_sections` WHERE id = :sid AND paper_id = :pid"),
        {"sid": section_id, "pid": paper_id},
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Section not found.")
    db.execute(
        text("UPDATE `#__eaiou_paper_sections` SET section_content = :content WHERE id = :sid"),
        {"content": body.section_content.strip() or None, "sid": section_id},
    )
    db.commit()
    return JSONResponse(content={"saved": True, "section_id": section_id})


class VolleyResponse(BaseModel):
    round_number: int
    author_response: str


@router.post("/audit/{paper_id}/respond")
async def respond_to_audit(
    paper_id: int,
    body: VolleyResponse,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Author records their response to an audit round. Unlocks next round."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Login required")

    if not body.author_response.strip():
        raise HTTPException(status_code=422, detail="Response cannot be empty.")

    now = datetime.now(timezone.utc)
    result = db.execute(text(
        "UPDATE `#__eaiou_volley_log` "
        "SET author_response = :resp, responded_at = :now "
        "WHERE paper_id = :pid AND round_number = :rnd AND author_response IS NULL"
    ), {
        "resp": body.author_response.strip(),
        "now":  now,
        "pid":  paper_id,
        "rnd":  body.round_number,
    })
    db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404,
            detail="Round not found or already responded to.")

    return JSONResponse(content={"status": "recorded", "round": body.round_number})
