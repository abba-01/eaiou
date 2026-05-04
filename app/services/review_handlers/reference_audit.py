"""
reference_audit — Cite-check via Crossref REST API.

Phase 1 (current): per-DOI lookup against Crossref public REST API. Free,
rate-limited to ~50 req/s with the polite mailto-header pool. Reports for
each cited DOI: exists / not_found / retracted / superseded.

Phase 2 (post corpus indexing): adds stronger-citation candidates from the
Qdrant-indexed Crossref corpus.

This handler does NOT call Anthropic — it's a deterministic API-based audit.
The disclosure block reflects checksubmit + Crossref REST as the providers.
"""

import os
import re
from typing import Optional

import httpx

from . import register


_CROSSREF_BASE = "https://api.crossref.org/works"
_DOI_REGEX = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)


def _polite_mailto() -> Optional[str]:
    """Crossref's polite-pool requires a mailto in User-Agent for higher rate limits."""
    return os.getenv("CROSSREF_MAILTO") or os.getenv("EAIOU_CONTACT_EMAIL")


def _user_agent() -> str:
    mailto = _polite_mailto()
    base = "checksubmit/1.0"
    if mailto:
        return f"{base} (mailto:{mailto})"
    return base


def _extract_dois(text: str) -> list[str]:
    """Pull all DOI patterns from text. De-dupes preserving first-seen order."""
    seen = []
    for m in _DOI_REGEX.finditer(text):
        doi = m.group(0).rstrip(".,;)")  # trailing punctuation
        if doi not in seen:
            seen.append(doi)
    return seen


def _check_doi(client: httpx.Client, doi: str) -> dict:
    """Fetch one DOI from Crossref. Returns {status, title, year, retracted, ...}."""
    try:
        resp = client.get(f"{_CROSSREF_BASE}/{doi}", timeout=15.0)
    except httpx.HTTPError as exc:
        return {"doi": doi, "status": "error", "error": str(exc)}

    if resp.status_code == 404:
        return {"doi": doi, "status": "not_found"}
    if resp.status_code != 200:
        return {"doi": doi, "status": "error", "error": f"HTTP {resp.status_code}"}

    try:
        msg = resp.json().get("message", {})
    except ValueError:
        return {"doi": doi, "status": "error", "error": "non-json response"}

    title = (msg.get("title") or [None])[0]
    container = (msg.get("container-title") or [None])[0]
    year = None
    if msg.get("issued", {}).get("date-parts"):
        year = msg["issued"]["date-parts"][0][0]

    # Crossref flags retractions in update-to / subtype
    retracted = False
    for upd in msg.get("update-to", []):
        if upd.get("type") in ("retraction", "withdrawal"):
            retracted = True
            break
    if msg.get("subtype") == "retraction":
        retracted = True

    return {
        "doi": doi,
        "status": "retracted" if retracted else "ok",
        "title": title,
        "container": container,
        "year": year,
    }


@register("reference_audit")
def handle(inputs: dict, ctx: dict) -> dict:
    """
    Inputs:
      manuscript_text   — extract DOIs from this if no bibtex supplied
      references_bibtex — optional pre-extracted bibtex (Phase 1.1: parse it)
      doi_list          — optional pre-extracted DOI list (skip parsing)
    """
    if inputs.get("doi_list"):
        dois = list(inputs["doi_list"])[:200]  # cap
    elif inputs.get("references_bibtex"):
        dois = _extract_dois(inputs["references_bibtex"])
    else:
        dois = _extract_dois(inputs.get("manuscript_text", ""))

    if not dois:
        return {
            "sku": "reference_audit",
            "reasoning": (
                "No DOIs found in the input. Provide either references_bibtex, "
                "doi_list, or a manuscript_text containing inline DOIs (10.xxxx/...)."
            ),
            "structured": {"doi_count": 0, "results": []},
            "iid": {
                "provider": "checksubmit",
                "model_family": "crossref-rest-v1",
                "instance_hash": "0" * 16,
                "input_tokens": 0,
                "output_tokens": 0,
            },
        }

    headers = {"User-Agent": _user_agent()}
    results = []
    flagged = []
    with httpx.Client(headers=headers, timeout=15.0) as client:
        for doi in dois[:100]:  # hard cap per call
            result = _check_doi(client, doi)
            results.append(result)
            if result["status"] in ("not_found", "retracted", "error"):
                flagged.append(result)

    summary_lines = [f"Audited {len(results)} DOIs:"]
    by_status = {}
    for r in results:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
    for status, count in sorted(by_status.items()):
        summary_lines.append(f"  {status}: {count}")
    if flagged:
        summary_lines.append("\nFlagged for review:")
        for f in flagged[:10]:
            summary_lines.append(f"  {f['doi']} — {f['status']}")

    # instance_hash: deterministic over the doi set so repeats are stable
    import hashlib
    instance_hash = hashlib.sha256(("|".join(sorted(dois))).encode()).hexdigest()[:16]

    return {
        "sku": "reference_audit",
        "reasoning": "\n".join(summary_lines),
        "structured": {
            "doi_count": len(results),
            "by_status": by_status,
            "results": results,
            "flagged": flagged,
        },
        "iid": {
            "provider": "Crossref",
            "model_family": "crossref-rest-v1",
            "instance_hash": instance_hash,
            "input_tokens": None,
            "output_tokens": None,
        },
    }
