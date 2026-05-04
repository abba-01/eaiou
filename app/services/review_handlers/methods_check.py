"""
methods_check — Methods-section adequacy / reproducibility audit.
"""
from . import register
from ._anthropic_client import call_anthropic, truncate_text


_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "reproducibility_score": {"type": "number", "minimum": 0, "maximum": 1},
        "verdict": {
            "type": "string",
            "enum": ["adequate", "needs_revision", "insufficient"],
        },
        "missing_elements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["controls", "procedure", "parameters", "data_sources",
                                 "version_pinning", "statistical_treatment", "preregistration",
                                 "ablation", "compute_resources"],
                    },
                    "description": {"type": "string"},
                    "severity": {"type": "string", "enum": ["high", "medium", "low"]},
                },
                "required": ["category", "description"],
            },
        },
        "undocumented_assumptions": {
            "type": "array",
            "items": {"type": "string"},
        },
        "summary": {"type": "string"},
    },
    "required": ["verdict", "summary"],
}


_SYSTEM_PROMPT = """You are a reproducibility-focused methods reviewer.

Audit the methods section for: missing controls, unclear procedures, \
unspecified parameters, missing version pinning of tools/datasets, \
undocumented statistical assumptions, missing ablations, missing compute \
resource details (for computational papers).

Output: reproducibility_score (0-1), verdict (adequate / needs_revision / \
insufficient), missing_elements (categorized + severity), undocumented_assumptions.

Discipline-aware: if discipline=computational, emphasize seed-pinning, hardware \
specs, software versions; if discipline=experimental, emphasize controls, \
sample sizes, blinding; if discipline=theoretical, emphasize derivation \
completeness, axiom dependencies.

Return via methods_check_result.
"""


@register("methods_check")
def handle(inputs: dict, ctx: dict) -> dict:
    methods_text = inputs.get("methods_section_text") or inputs.get("manuscript_text", "")
    methods_text = truncate_text(methods_text)
    discipline = inputs.get("discipline") or "general"

    user_prompt = (
        f"## Discipline\n{discipline}\n\n"
        f"## Methods text\n{methods_text or '(no methods text provided)'}"
    )

    response = call_anthropic(
        sku="methods_check",
        system_prompt=_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        tool_schema=_TOOL_SCHEMA,
        tool_name="methods_check_result",
        max_tokens=2560,
    )

    return {
        "sku": "methods_check",
        "reasoning": response.get("reasoning", ""),
        "structured": response.get("structured", {}),
        "iid": response.get("iid", {}),
        **({"error": response["error"]} if response.get("error") else {}),
    }
