"""
scope_check — Verify manuscript scope-fit for the target venue.

Phase 1 implementation: Anthropic-backed structured-output handler.

Inputs:
  manuscript_text   (str, required)   The manuscript body or excerpt.
  target_venue      (str, optional)   Journal/conference acronym; biases assessment.
  selected_section  (str, optional)   Section name if user invoked from the editor.

Output (structured):
  scope_alignment        : 'pass' | 'partial' | 'fail'
  venue_match_reasoning  : short paragraph
  flagged_overreach      : list of {claim, where, why}
  suggested_rephrasings  : list of {original, suggested, reason}
  summary                : one-paragraph executive summary
"""
from . import register
from ._anthropic_client import call_anthropic, truncate_text


_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "scope_alignment": {
            "type": "string",
            "enum": ["pass", "partial", "fail"],
            "description": "Overall scope fit: pass = aligned, partial = some overreach, fail = scope mismatch",
        },
        "venue_match_reasoning": {
            "type": "string",
            "description": "Short paragraph explaining the alignment level vs the target venue",
        },
        "flagged_overreach": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string", "description": "The over-reaching claim verbatim"},
                    "where": {"type": "string", "description": "Section / paragraph identifier"},
                    "why": {"type": "string", "description": "Why this claim outruns the data"},
                },
                "required": ["claim", "why"],
            },
        },
        "suggested_rephrasings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "original": {"type": "string"},
                    "suggested": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["original", "suggested"],
            },
        },
        "summary": {
            "type": "string",
            "description": "One-paragraph executive summary of the scope review",
        },
    },
    "required": ["scope_alignment", "venue_match_reasoning", "summary"],
}


_SYSTEM_PROMPT = """You are a methodical pre-submission scope reviewer for academic manuscripts.

Your job: assess whether the manuscript's claims fit the target venue's scope, \
and flag any claim that outruns the supporting data or methodology.

Be precise and skeptical. Headlines that overstate the contribution are the \
common failure mode. Identify them with section pointers.

Do NOT rewrite the manuscript. Do NOT write new content. You are reviewing only.

Return your review by calling the scope_check_result tool with the structured fields.
"""


@register("scope_check")
def handle(inputs: dict, ctx: dict) -> dict:
    manuscript_text = truncate_text(inputs.get("manuscript_text", ""))
    target_venue = inputs.get("target_venue") or "(none specified)"
    selected_section = inputs.get("selected_section")

    user_prompt_parts = [
        f"## Target venue\n{target_venue}\n",
        "## Manuscript",
    ]
    if selected_section:
        user_prompt_parts.append(f"(Author has highlighted section: {selected_section})")
    user_prompt_parts.append(manuscript_text or "(no manuscript text provided)")

    user_prompt = "\n\n".join(user_prompt_parts)

    response = call_anthropic(
        sku="scope_check",
        system_prompt=_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        tool_schema=_TOOL_SCHEMA,
        tool_name="scope_check_result",
        max_tokens=2048,
    )

    return {
        "sku": "scope_check",
        "reasoning": response.get("reasoning", ""),
        "structured": response.get("structured", {}),
        "iid": response.get("iid", {}),
        **({"error": response["error"]} if response.get("error") else {}),
    }
