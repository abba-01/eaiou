"""
outline_check — Structure-of-argument review.

Identifies weak transitions, missing premises, unsupported claims, and
breaks in the argument flow.
"""
from . import register
from ._anthropic_client import call_anthropic, truncate_text


_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "argument_flow": {
            "type": "string",
            "enum": ["coherent", "uneven", "broken"],
        },
        "structural_issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "issue_type": {
                        "type": "string",
                        "enum": ["missing_premise", "weak_transition", "unsupported_claim",
                                 "redundancy", "out_of_order", "logical_gap"],
                    },
                    "where": {"type": "string"},
                    "description": {"type": "string"},
                    "severity": {"type": "string", "enum": ["high", "medium", "low"]},
                },
                "required": ["issue_type", "where", "description"],
            },
        },
        "missing_supports": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string"},
                    "needs": {"type": "string", "description": "What evidence/argument would support this claim"},
                },
                "required": ["claim", "needs"],
            },
        },
        "summary": {"type": "string"},
    },
    "required": ["argument_flow", "summary"],
}


_SYSTEM_PROMPT = """You are a structural-logic reviewer. Read the manuscript and \
assess only its argumentative skeleton: do the premises support the conclusion? \
Are transitions clean? Are any load-bearing claims unsupported?

Do NOT critique writing style or word choice — clarity_check covers that.
Do NOT critique methodology — methods_check covers that.

You are looking at: argument flow, missing premises, weak transitions, \
unsupported claims, redundancy, out-of-order presentation, logical gaps.

Return via outline_check_result.
"""


@register("outline_check")
def handle(inputs: dict, ctx: dict) -> dict:
    text = truncate_text(inputs.get("manuscript_text", ""))
    section_outline = inputs.get("section_outline")

    user_prompt = (
        (f"## Section outline (author-provided)\n{section_outline}\n\n" if section_outline else "")
        + f"## Manuscript\n{text or '(no manuscript text)'}"
    )

    response = call_anthropic(
        sku="outline_check",
        system_prompt=_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        tool_schema=_TOOL_SCHEMA,
        tool_name="outline_check_result",
        max_tokens=2048,
    )

    return {
        "sku": "outline_check",
        "reasoning": response.get("reasoning", ""),
        "structured": response.get("structured", {}),
        "iid": response.get("iid", {}),
        **({"error": response["error"]} if response.get("error") else {}),
    }
