"""
seed_products.py — populate the eaiou_products table with the Phase 0 catalog.

Run with:
    python scripts/seed_products.py

Idempotent: uses INSERT ... ON DUPLICATE KEY UPDATE so re-running refreshes prices/handler refs
without creating duplicates. Safe to run after pricing changes.

The 8 SKUs are Phase 0 of the checksubmit MVP. Each maps to a handler module
under app.services.review_handlers.<handler_name> — handlers ship as stubs in
Phase 0 and get real review logic in Phase 1 per the build plan.

Source of truth for prices and handler names:
    /scratch/repos/eaiou/manusights_competitor_mvp_plan.md §0.1
"""

import sys
from pathlib import Path

# Ensure we can import from the eaiou app
EAIOU_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EAIOU_ROOT))

from sqlalchemy import text
from app.database import SessionLocal  # noqa: E402

PRODUCTS = [
    {
        "sku": "scope_check",
        "display_name": "Scope check",
        "description": (
            "Verify the manuscript's claim aligns with the target venue's scope; "
            "flag overreach or misalignment before submission."
        ),
        "retail_price_cents": 1000,
        "wholesale_price_cents": 700,
        "latency_target_seconds": 30,
        "handler_module": "app.services.review_handlers.scope_check",
    },
    {
        "sku": "journal_select",
        "display_name": "Journal selection",
        "description": (
            "Top-3 journal recommendations with reasoning, scope-fit notes, "
            "and current acceptance-rate snapshot."
        ),
        "retail_price_cents": 1000,
        "wholesale_price_cents": 700,
        "latency_target_seconds": 30,
        "handler_module": "app.services.review_handlers.journal_select",
    },
    {
        "sku": "outline_check",
        "display_name": "Outline review",
        "description": (
            "Structure-of-argument check: does the manuscript's organization "
            "support the conclusion? Identify weak transitions and missing premises."
        ),
        "retail_price_cents": 1000,
        "wholesale_price_cents": 700,
        "latency_target_seconds": 30,
        "handler_module": "app.services.review_handlers.outline_check",
    },
    {
        "sku": "clarity_check",
        "display_name": "Clarity review",
        "description": (
            "Plain-English readability pass; flag jargon, unclear referents, "
            "and sentences that obscure the contribution."
        ),
        "retail_price_cents": 1000,
        "wholesale_price_cents": 700,
        "latency_target_seconds": 30,
        "handler_module": "app.services.review_handlers.clarity_check",
    },
    {
        "sku": "methods_check",
        "display_name": "Methods adequacy",
        "description": (
            "Methods-section review: does the description support reproducibility? "
            "Flag missing controls, unclear procedures, undocumented assumptions."
        ),
        "retail_price_cents": 1500,
        "wholesale_price_cents": 1000,
        "latency_target_seconds": 45,
        "handler_module": "app.services.review_handlers.methods_check",
    },
    {
        "sku": "reference_audit",
        "display_name": "Reference audit",
        "description": (
            "Cite-check via Crossref + corpus retrieval: verify each reference "
            "exists, is current, and is the strongest available citation for the claim."
        ),
        "retail_price_cents": 1000,
        "wholesale_price_cents": 700,
        "latency_target_seconds": 60,
        "handler_module": "app.services.review_handlers.reference_audit",
    },
    {
        "sku": "full_review",
        "display_name": "Full pre-submission review",
        "description": (
            "Composed review: scope_check + clarity_check + methods_check "
            "delivered as one structured report. Recommended before any submission."
        ),
        "retail_price_cents": 10000,
        "wholesale_price_cents": 7000,
        "latency_target_seconds": 90,
        "handler_module": "app.services.review_handlers.full_review",
    },
    {
        "sku": "premium_review",
        "display_name": "Premium review (human-in-loop)",
        "description": (
            "Full IID review plus human expert pass on flagged items. "
            "Slower turnaround; intended for high-stakes submissions."
        ),
        "retail_price_cents": 150000,
        "wholesale_price_cents": 100000,
        "latency_target_seconds": 86400,  # 24h SLA placeholder
        "handler_module": "app.services.review_handlers.premium_review",
    },
]


UPSERT_SQL = text("""
    INSERT INTO `#__eaiou_products`
      (sku, display_name, description, retail_price_cents,
       wholesale_price_cents, latency_target_seconds, handler_module, active)
    VALUES (:sku, :display_name, :description, :retail_price_cents,
            :wholesale_price_cents, :latency_target_seconds, :handler_module, 1)
    ON DUPLICATE KEY UPDATE
      display_name=VALUES(display_name),
      description=VALUES(description),
      retail_price_cents=VALUES(retail_price_cents),
      wholesale_price_cents=VALUES(wholesale_price_cents),
      latency_target_seconds=VALUES(latency_target_seconds),
      handler_module=VALUES(handler_module),
      active=VALUES(active)
""")

VERIFY_SQL = text("""
    SELECT sku, display_name, retail_price_cents, handler_module, active
    FROM `#__eaiou_products` ORDER BY retail_price_cents
""")


def seed():
    with SessionLocal() as session:
        for p in PRODUCTS:
            session.execute(UPSERT_SQL, p)
        session.commit()
        print(f"Seeded {len(PRODUCTS)} products.")

        rows = session.execute(VERIFY_SQL).fetchall()
        print()
        print(f"{'sku':<20} {'price':>10}  {'handler_module':<55}  active")
        print("-" * 100)
        for sku, name, cents, handler, active in rows:
            price = f"${cents/100:.2f}"
            print(f"{sku:<20} {price:>10}  {handler:<55}  {bool(active)}")


if __name__ == "__main__":
    seed()
