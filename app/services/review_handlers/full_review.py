"""
full_review — Composed pre-submission review.

Composes scope_check + clarity_check + methods_check IN PARALLEL, each
receiving the same source inputs. NO chaining — outputs are NOT fed into
each other. Each component handler returns its own result with its own
disclosure block; full_review aggregates the three into a single report.

Per ToS Compliance Doctrine §1 Rule 1: composition transparency is
load-bearing. The structured response includes each component's result
so a reader can see exactly which component said what, with that
component's own provider attribution.
"""
from concurrent.futures import ThreadPoolExecutor

from . import register, dispatch


_COMPONENT_SKUS = ("scope_check", "clarity_check", "methods_check")


@register("full_review")
def handle(inputs: dict, ctx: dict) -> dict:
    """
    Inputs (same as the three components — fanned out unchanged):
      manuscript_text  (str, required)
      target_venue     (str, optional)  — used by scope_check
      audience_level   (str, optional)  — used by clarity_check
      discipline       (str, optional)  — used by methods_check
    """
    # Parallel dispatch — each component runs independently with its own
    # provider call. Threads are safe here because each handler creates its
    # own httpx/Anthropic client + DB writes happen at the api_iid layer.
    with ThreadPoolExecutor(max_workers=len(_COMPONENT_SKUS)) as executor:
        future_map = {sku: executor.submit(dispatch, sku, inputs, ctx) for sku in _COMPONENT_SKUS}
        components = {sku: f.result() for sku, f in future_map.items()}

    # Aggregate — narrative reasoning concatenated; structured stays hierarchical
    component_summaries = []
    component_iids = {}
    any_failure = False
    for sku in _COMPONENT_SKUS:
        comp = components.get(sku, {})
        if comp.get("error"):
            any_failure = True
        component_iids[sku] = comp.get("iid", {})
        comp_summary = comp.get("structured", {}).get("summary") or comp.get("reasoning", "")
        component_summaries.append(f"### {sku}\n\n{comp_summary}")

    aggregated_reasoning = (
        "## Full Pre-Submission Review\n\n"
        "Three components dispatched in parallel — no chaining; each received "
        "the same source inputs. Each component's own disclosure block is "
        "available via the structured.components field below.\n\n"
        + "\n\n".join(component_summaries)
    )

    # full_review's instance_hash composes the three component hashes for
    # forensic traceability. NOT a chain — just an aggregation marker.
    component_hashes = [(component_iids.get(sku, {}) or {}).get("instance_hash", "") for sku in _COMPONENT_SKUS]
    composite_hash = "-".join(h[:5] for h in component_hashes if h)

    return {
        "sku": "full_review",
        "reasoning": aggregated_reasoning,
        "structured": {
            "components": components,
            "component_skus": list(_COMPONENT_SKUS),
            "any_failure": any_failure,
        },
        "iid": {
            "provider": "checksubmit-composite",
            "model_family": "scope_check+clarity_check+methods_check",
            "instance_hash": composite_hash[:16] or "0" * 16,
            "input_tokens": sum(
                (component_iids.get(sku, {}) or {}).get("input_tokens", 0) or 0
                for sku in _COMPONENT_SKUS
            ),
            "output_tokens": sum(
                (component_iids.get(sku, {}) or {}).get("output_tokens", 0) or 0
                for sku in _COMPONENT_SKUS
            ),
        },
        **({"error": "one or more component handlers failed"} if any_failure else {}),
    }
