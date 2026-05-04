"""
premium_review — Full IID review + human expert pass on flagged items.

Phase 1 implementation:
  1. Dispatch full_review (parallel scope+clarity+methods) — same inputs
  2. Identify high-severity flagged items from each component
  3. Insert a row in eaiou_premium_review_queue (table TBD) for human follow-up
  4. Return the IID review immediately + a queue receipt; human pass attaches
     within 24h SLA via a separate completion path

For Phase 1 scaffolding, the human queue write is logged but the table
write is deferred to Phase 1.1 (need migration_009 for the queue table).
For now, the response carries `human_pass_pending: true` and the order's
status is set to `premium_review_pending_human` by the dispatcher's
post-processing.
"""
from . import register, dispatch


@register("premium_review")
def handle(inputs: dict, ctx: dict) -> dict:
    """
    Inputs (forwarded to full_review unchanged):
      manuscript_text                  (str, required)
      target_venue                     (str, optional)
      audience_level                   (str, optional)
      discipline                       (str, optional)
      preferred_human_reviewer_id      (str, optional)
    """
    iid_review = dispatch("full_review", inputs, ctx)

    # Identify high-severity flagged items from the IID review for human triage
    components = iid_review.get("structured", {}).get("components", {}) or {}
    high_severity = []

    # scope_check overreach (severity not always set; treat all flagged as high)
    scope_struct = (components.get("scope_check", {}).get("structured") or {})
    for issue in scope_struct.get("flagged_overreach") or []:
        high_severity.append({"source": "scope_check", "issue": issue})

    # clarity_check high-severity issues
    clarity_struct = (components.get("clarity_check", {}).get("structured") or {})
    for issue in clarity_struct.get("issues") or []:
        if isinstance(issue, dict) and issue.get("severity") == "high":
            high_severity.append({"source": "clarity_check", "issue": issue})

    # methods_check high-severity missing elements
    methods_struct = (components.get("methods_check", {}).get("structured") or {})
    for elem in methods_struct.get("missing_elements") or []:
        if isinstance(elem, dict) and elem.get("severity") == "high":
            high_severity.append({"source": "methods_check", "issue": elem})

    preferred_human = inputs.get("preferred_human_reviewer_id")

    # Phase 1 scaffolding: log the queue intent. Phase 1.1 writes to
    # eaiou_premium_review_queue table; for now, surface in response only.
    queue_receipt = {
        "queue_status": "pending_human",
        "high_severity_items": len(high_severity),
        "preferred_reviewer": preferred_human,
        "sla_hours": 24,
        "note": (
            "Phase 1 scaffolding: high-severity items would be queued to "
            "eaiou_premium_review_queue here; human reviewer assignment + "
            "sla tracking ships in migration_009."
        ),
    }

    return {
        "sku": "premium_review",
        "reasoning": (
            iid_review.get("reasoning", "")
            + f"\n\n## Human Expert Pass\n\n"
            + f"{len(high_severity)} high-severity item(s) flagged for human review. "
            + f"24-hour SLA. Order status will transition to "
            + f"`premium_review_pending_human` until the human pass completes."
        ),
        "structured": {
            "iid_review": iid_review.get("structured"),
            "high_severity_items": high_severity,
            "queue_receipt": queue_receipt,
            "human_pass_pending": True,
        },
        "iid": iid_review.get("iid", {}),
    }
