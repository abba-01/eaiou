"""
journal_select — Top-3 venue recommendations with reasoning.

Phase 1: Anthropic-backed structured output. Phase 2 will ground recommendations
in Crossref-corpus signals (scope-fit score, recent acceptance density).
"""
from . import register
from ._anthropic_client import call_anthropic, truncate_text


_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "recommendations": {
            "type": "array",
            "minItems": 1,
            "maxItems": 5,
            "items": {
                "type": "object",
                "properties": {
                    "venue": {"type": "string", "description": "Journal or conference name"},
                    "rank": {"type": "integer", "minimum": 1, "maximum": 5},
                    "fit_reasoning": {"type": "string"},
                    "scope_match_score": {"type": "number", "minimum": 0, "maximum": 1},
                    "caveats": {"type": "string"},
                },
                "required": ["venue", "rank", "fit_reasoning"],
            },
        },
        "summary": {"type": "string", "description": "One-paragraph executive summary"},
    },
    "required": ["recommendations", "summary"],
}


_SYSTEM_PROMPT = """You are a venue-selection advisor for academic manuscripts.

Identify the top 3 (up to 5) journals or conferences best aligned with the \
manuscript's actual contribution and methodology. Bias toward venues whose \
typical scope MATCHES this manuscript, not toward high-impact venues regardless \
of fit.

For each recommendation:
  - Name the venue (full name, not just an acronym).
  - Rank (1 = strongest fit).
  - Briefly state why this venue fits this manuscript.
  - Score the scope match 0–1 (0 = wrong scope; 1 = textbook fit).
  - Note any caveats (page limits, fee structure, scope-edge issues).

Avoid: predatory venues, vanity venues, venues with active scope-creep concerns.

Return via the journal_select_result tool.
"""


@register("journal_select")
def handle(inputs: dict, ctx: dict) -> dict:
    text = truncate_text(inputs.get("manuscript_text", ""))
    field_hint = inputs.get("field_hint") or "(unspecified)"
    excludes = inputs.get("exclude_venues") or []

    user_prompt = (
        f"## Field hint\n{field_hint}\n\n"
        f"## Excluded venues\n{', '.join(excludes) if excludes else '(none)'}\n\n"
        f"## Manuscript\n{text or '(no manuscript text)'}"
    )

    response = call_anthropic(
        sku="journal_select",
        system_prompt=_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        tool_schema=_TOOL_SCHEMA,
        tool_name="journal_select_result",
        max_tokens=2048,
    )

    return {
        "sku": "journal_select",
        "reasoning": response.get("reasoning", ""),
        "structured": response.get("structured", {}),
        "iid": response.get("iid", {}),
        **({"error": response["error"]} if response.get("error") else {}),
    }
