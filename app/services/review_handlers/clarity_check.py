"""
clarity_check — Plain-English readability + jargon flag.

Per-sentence audit: jargon, unclear referents, sentences that obscure
the contribution.
"""
from . import register
from ._anthropic_client import call_anthropic, truncate_text


_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "overall_clarity": {
            "type": "string",
            "enum": ["clear", "uneven", "obscure"],
        },
        "audience_fit": {
            "type": "string",
            "description": "How well the language matches the stated audience level",
        },
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "original": {"type": "string", "description": "Verbatim problematic sentence"},
                    "issue": {
                        "type": "string",
                        "enum": ["jargon", "unclear_referent", "buried_lede",
                                 "passive_voice_obscuring_actor", "ambiguous_pronoun",
                                 "unnecessary_complexity"],
                    },
                    "severity": {"type": "string", "enum": ["high", "medium", "low"]},
                    "suggested_rewrite": {"type": "string"},
                },
                "required": ["original", "issue", "suggested_rewrite"],
            },
        },
        "summary": {"type": "string"},
    },
    "required": ["overall_clarity", "summary"],
}


_SYSTEM_PROMPT = """You are a plain-English clarity reviewer for academic prose.

Per sentence: flag jargon that won't reach the stated audience, unclear referents, \
buried ledes, passive voice that hides the actor, ambiguous pronouns, and \
unnecessary complexity. Provide a suggested rewrite for each.

Don't audit logic (outline_check) or methods (methods_check). Audit voice + \
readability only. Preserve the author's terminology where it's load-bearing — \
"carrier", "intellid", "expressed sum" stay; "leverage", "robust", "novel" go.

Return via clarity_check_result.
"""


@register("clarity_check")
def handle(inputs: dict, ctx: dict) -> dict:
    text = truncate_text(inputs.get("manuscript_text", ""))
    audience = inputs.get("audience_level") or "general_scientific"

    user_prompt = (
        f"## Audience level\n{audience}\n\n"
        f"## Manuscript\n{text or '(no manuscript text)'}"
    )

    response = call_anthropic(
        sku="clarity_check",
        system_prompt=_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        tool_schema=_TOOL_SCHEMA,
        tool_name="clarity_check_result",
        max_tokens=3072,
    )

    return {
        "sku": "clarity_check",
        "reasoning": response.get("reasoning", ""),
        "structured": response.get("structured", {}),
        "iid": response.get("iid", {}),
        **({"error": response["error"]} if response.get("error") else {}),
    }
