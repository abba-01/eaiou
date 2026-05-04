"""
Stripe webhook receiver for the checksubmit MVP.

Endpoint:
  POST /api/v1/stripe/webhook
    Headers: Stripe-Signature (verified)
    Body:    raw Stripe event payload (must NOT be modified by middleware)

Events handled:
  customer.subscription.created           — insert eaiou_subscriptions row
  customer.subscription.updated           — refresh status + period dates
  customer.subscription.deleted           — mark canceled
  invoice.payment_succeeded               — refresh subscription period
  invoice.payment_failed                  — flag past_due
  billing.meter_event_summary.created     — reconcile metered usage (informational)

Compliance:
  * Webhook signature is verified before any DB write — no event accepted on bad sig.
  * Every event is logged to eaiou_marketplace_log with the raw Stripe event id.
  * Event idempotency: each Stripe event_id is logged once; replay is detected via
    UNIQUE constraint on (event_type, entity_id) where entity_id = stripe_event_id.

Tags: stripe-webhook
Prefix: /api/v1
"""

import json
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..services import stripe_client
from ..services.marketplace import log_event

router = APIRouter(prefix="/api/v1/stripe", tags=["stripe-webhook"])


@router.post("/webhook", status_code=200)
async def stripe_webhook(request: Request,
                         stripe_signature: str = Header(default="", alias="Stripe-Signature")):
    """
    Stripe webhook receiver.

    Handles signature verification, event-type routing, and idempotency.
    Returns 200 on success, 400 on signature failure, 200 (with logged 'unhandled')
    on unrecognized events so Stripe doesn't retry indefinitely.
    """
    payload = await request.body()

    try:
        event = stripe_client.verify_webhook(payload, stripe_signature)
    except stripe_client.StripeNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        # Signature verification failed — log to system log (not DB, since we
        # might be under attack) and return 400.
        raise HTTPException(status_code=400, detail=f"signature verification failed: {exc}")

    event_id = event.get("id")
    event_type = event.get("type")

    db = SessionLocal()
    try:
        # Idempotency: skip if we've already processed this event.
        seen = db.execute(text("""
            SELECT log_id FROM `#__eaiou_marketplace_log`
            WHERE event_type = :event_type AND entity_id = :event_id LIMIT 1
        """), {"event_type": f"stripe.{event_type}", "event_id": event_id}).first()
        if seen:
            return {"received": True, "duplicate": True, "event_id": event_id}

        # Dispatch by event type
        handler = WEBHOOK_HANDLERS.get(event_type)
        if handler:
            try:
                handler(db, event)
            except Exception as exc:
                log_event(
                    db, f"stripe.{event_type}.handler_error",
                    actor_type="stripe_webhook", actor_id=event_id,
                    entity_type="stripe_event", entity_id=event_id,
                    payload={"error": str(exc), "event": _safe_event_summary(event)},
                )
                db.commit()
                # We still return 200 — Stripe should not retry on handler errors;
                # the audit log captures the failure for manual reconciliation.
                return {"received": True, "handler_error": str(exc), "event_id": event_id}

        # Always log the receipt (handler may have logged additional events)
        log_event(
            db, f"stripe.{event_type}",
            actor_type="stripe_webhook", actor_id=event_id,
            entity_type="stripe_event", entity_id=event_id,
            payload={"event": _safe_event_summary(event)},
        )
        db.commit()
    finally:
        db.close()

    return {"received": True, "event_id": event_id, "type": event_type}


# ── Event handlers ────────────────────────────────────────────────────────────

def _on_subscription_created(db: Session, event: dict):
    """customer.subscription.created — insert eaiou_subscriptions row."""
    sub = event["data"]["object"]
    user_id = sub.get("metadata", {}).get("eaiou_user_id")
    if not user_id:
        return  # Subscription not associated with an eaiou user (e.g. test event)
    tier = sub.get("metadata", {}).get("eaiou_tier", "starter")

    db.execute(text("""
        INSERT INTO `#__eaiou_subscriptions`
          (subscription_id, user_id, tier, stripe_subscription_id, stripe_customer_id,
           status, current_period_start, current_period_end)
        VALUES
          (:subscription_id, :user_id, :tier, :stripe_sub_id, :stripe_cust_id,
           :status, :period_start, :period_end)
        ON DUPLICATE KEY UPDATE
          status = VALUES(status),
          current_period_start = VALUES(current_period_start),
          current_period_end = VALUES(current_period_end)
    """), {
        "subscription_id": str(uuid.uuid4()),
        "user_id": user_id,
        "tier": tier,
        "stripe_sub_id": sub["id"],
        "stripe_cust_id": sub["customer"],
        "status": sub["status"],
        "period_start": datetime.fromtimestamp(sub["current_period_start"]),
        "period_end": datetime.fromtimestamp(sub["current_period_end"]),
    })


def _on_subscription_updated(db: Session, event: dict):
    """customer.subscription.updated — refresh status + period dates."""
    sub = event["data"]["object"]
    db.execute(text("""
        UPDATE `#__eaiou_subscriptions`
        SET status = :status,
            current_period_start = :period_start,
            current_period_end = :period_end,
            updated_at = CURRENT_TIMESTAMP
        WHERE stripe_subscription_id = :stripe_sub_id
    """), {
        "stripe_sub_id": sub["id"],
        "status": sub["status"],
        "period_start": datetime.fromtimestamp(sub["current_period_start"]),
        "period_end": datetime.fromtimestamp(sub["current_period_end"]),
    })


def _on_subscription_deleted(db: Session, event: dict):
    """customer.subscription.deleted — mark canceled."""
    sub = event["data"]["object"]
    db.execute(text("""
        UPDATE `#__eaiou_subscriptions`
        SET status = 'canceled', updated_at = CURRENT_TIMESTAMP
        WHERE stripe_subscription_id = :stripe_sub_id
    """), {"stripe_sub_id": sub["id"]})


def _on_invoice_payment_succeeded(db: Session, event: dict):
    """invoice.payment_succeeded — re-confirm subscription is active."""
    invoice = event["data"]["object"]
    stripe_sub_id = invoice.get("subscription")
    if not stripe_sub_id:
        return
    db.execute(text("""
        UPDATE `#__eaiou_subscriptions`
        SET status = 'active', updated_at = CURRENT_TIMESTAMP
        WHERE stripe_subscription_id = :stripe_sub_id
    """), {"stripe_sub_id": stripe_sub_id})


def _on_invoice_payment_failed(db: Session, event: dict):
    """invoice.payment_failed — flag past_due so the UI can prompt for new card."""
    invoice = event["data"]["object"]
    stripe_sub_id = invoice.get("subscription")
    if not stripe_sub_id:
        return
    db.execute(text("""
        UPDATE `#__eaiou_subscriptions`
        SET status = 'past_due', updated_at = CURRENT_TIMESTAMP
        WHERE stripe_subscription_id = :stripe_sub_id
    """), {"stripe_sub_id": stripe_sub_id})


def _on_meter_event_summary_created(db: Session, event: dict):
    """billing.meter_event_summary.created — informational; reconcile if needed."""
    # Phase 0: just log. Phase 1+ might reconcile against eaiou_orders.
    pass


WEBHOOK_HANDLERS = {
    "customer.subscription.created":         _on_subscription_created,
    "customer.subscription.updated":         _on_subscription_updated,
    "customer.subscription.deleted":         _on_subscription_deleted,
    "invoice.payment_succeeded":             _on_invoice_payment_succeeded,
    "invoice.payment_failed":                _on_invoice_payment_failed,
    "billing.meter_event_summary.created":   _on_meter_event_summary_created,
}


def _safe_event_summary(event: dict) -> dict:
    """Strip large payloads before logging — keep id, type, object id."""
    obj = event.get("data", {}).get("object", {})
    return {
        "id": event.get("id"),
        "type": event.get("type"),
        "object_id": obj.get("id"),
        "object_type": obj.get("object"),
    }
