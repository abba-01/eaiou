"""
_anthropic_client.py — shared Anthropic-backed handler primitive.

Each Phase 1 review handler in this package uses `call_anthropic()` to invoke
the Claude API with a per-handler prompt + structured-output tool. This shared
primitive is NOT an orchestrator (no chaining); it's a thin wrapper that:

  1. Constructs the messages payload
  2. Forces structured output via a tool-call schema
  3. Captures provider/model/instance_hash for the IID disclosure block
  4. Reports usage (input/output tokens) for cost reconciliation
  5. Falls back to a DRY-RUN fake response when CHECKSUBMIT_DRY_RUN=1 is set
     (lets handlers be tested + smoke-checked without burning API credits)

Compliance:
  * Per ToS Doctrine §1 Rule 1 — handlers MUST NOT call this primitive with
    another handler's output as input. Inputs come from the user/dispatcher.
  * Per Rule 4 — the response always carries the disclosure fields
    (provider, model_family, instance_hash). Stripping these is forbidden.
"""

import hashlib
import json
import os
from typing import Any, Optional

# Lazy-import anthropic so this module loads even when SDK isn't installed
# (tests + dry-run paths don't need it).
_anthropic_client = None


class AnthropicNotConfigured(RuntimeError):
    """Raised when ANTHROPIC_API_KEY is missing and dry-run is off."""


def _get_client():
    global _anthropic_client
    if _anthropic_client is not None:
        return _anthropic_client
    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CHECKSUBMIT_ANTHROPIC_API_KEY")
    if not api_key:
        raise AnthropicNotConfigured(
            "Neither ANTHROPIC_API_KEY nor CHECKSUBMIT_ANTHROPIC_API_KEY set in env. "
            "Set CHECKSUBMIT_DRY_RUN=1 to bypass for testing."
        )
    import anthropic
    _anthropic_client = anthropic.Anthropic(api_key=api_key)
    return _anthropic_client


def call_anthropic(
    *,
    sku: str,
    system_prompt: str,
    user_prompt: str,
    tool_schema: dict,
    tool_name: str,
    model: str = "claude-opus-4-7",
    max_tokens: int = 2048,
) -> dict:
    """
    Make one structured-output Anthropic API call. Returns a dict with:
      - reasoning   (str)  — human-readable narrative the model produced
      - structured  (dict) — fields extracted from the tool-call (per-SKU schema)
      - iid         (dict) — provider, model_family, instance_hash, input_tokens, output_tokens
      - error       (str)  — set on failure; not raised so handler can decide

    Dry-run path: if CHECKSUBMIT_DRY_RUN=1, returns a deterministic fake
    response that exercises the same return shape without calling the API.

    Args:
      sku:           SKU label (used in disclosure block + dry-run instance_hash)
      system_prompt: System message — describes role, constraints, output policy
      user_prompt:   The user-turn content (already-composed input text)
      tool_schema:   JSON-Schema dict for the structured output (the tool's
                     input_schema). The model is forced to call this single tool.
      tool_name:     Name for the tool; appears in audit logs.
      model:         Anthropic model id. Defaults to claude-opus-4-7.
      max_tokens:    Cap on output. Default 2048; raise for full_review.
    """
    if os.getenv("CHECKSUBMIT_DRY_RUN") == "1":
        return _dry_run_response(sku=sku, tool_name=tool_name, tool_schema=tool_schema, model=model)

    try:
        client = _get_client()
    except AnthropicNotConfigured as exc:
        return {
            "reasoning": f"Anthropic API not configured: {exc}",
            "structured": {},
            "iid": {
                "provider": "checksubmit",
                "model_family": "not_configured",
                "instance_hash": "0" * 16,
                "input_tokens": 0,
                "output_tokens": 0,
            },
            "error": str(exc),
        }

    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            tools=[{
                "name": tool_name,
                "description": f"Return the structured {sku} result.",
                "input_schema": tool_schema,
            }],
            tool_choice={"type": "tool", "name": tool_name},
        )
    except Exception as exc:
        return {
            "reasoning": f"Anthropic API call failed: {exc}",
            "structured": {},
            "iid": {
                "provider": "Anthropic",
                "model_family": model,
                "instance_hash": "0" * 16,
                "input_tokens": 0,
                "output_tokens": 0,
            },
            "error": str(exc),
        }

    # Extract structured output from the tool-call block
    structured = {}
    reasoning_parts = []
    for block in response.content:
        if getattr(block, "type", None) == "tool_use":
            structured = block.input or {}
        elif getattr(block, "type", None) == "text":
            reasoning_parts.append(block.text)

    reasoning = "\n\n".join(reasoning_parts).strip()
    if not reasoning:
        # Some structured-only responses don't include free-form text.
        # Synthesize a minimal narrative from the structured output's
        # "summary" field if present.
        reasoning = structured.get("summary", "") or json.dumps(structured, indent=2)

    instance_hash = _short_hash(response.id) if hasattr(response, "id") else _short_hash(str(structured))

    usage = getattr(response, "usage", None)
    input_tokens = getattr(usage, "input_tokens", None) if usage else None
    output_tokens = getattr(usage, "output_tokens", None) if usage else None

    return {
        "reasoning": reasoning,
        "structured": structured,
        "iid": {
            "provider": "Anthropic",
            "model_family": getattr(response, "model", model),
            "instance_hash": instance_hash,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        },
    }


def _dry_run_response(*, sku: str, tool_name: str, tool_schema: dict, model: str) -> dict:
    """Deterministic fake response for testing without the API."""
    fake_id = f"dry-run-{sku}"
    return {
        "reasoning": (
            f"[DRY RUN] {sku} would be invoked via {tool_name} on model {model}. "
            f"Real response will replace this when CHECKSUBMIT_DRY_RUN is unset and "
            f"ANTHROPIC_API_KEY is configured."
        ),
        "structured": {"_dry_run": True, "_tool": tool_name, "_sku": sku},
        "iid": {
            "provider": "Anthropic",
            "model_family": f"{model} (dry-run)",
            "instance_hash": _short_hash(fake_id),
            "input_tokens": 0,
            "output_tokens": 0,
        },
    }


def _short_hash(s: str) -> str:
    """Truncated SHA-256 hex (16 chars) — matches our disclosure-block convention."""
    return hashlib.sha256(str(s).encode("utf-8")).hexdigest()[:16]


# ── Per-handler prompt / schema helpers ────────────────────────────────────────

def truncate_text(text: str, max_chars: int = 30000) -> str:
    """Cap a manuscript blob before sending. 30K chars ≈ 7.5K tokens — cheap pass."""
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    head = text[: max_chars // 2]
    tail = text[-max_chars // 2:]
    return f"{head}\n\n[... {len(text) - max_chars} chars elided ...]\n\n{tail}"
