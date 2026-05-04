"""
marketplace.py — order lifecycle for the checksubmit MVP.

Phase 0 service. Wires:
  * eaiou_orders DB row creation + lookup
  * Subscription-credit deduction OR Stripe meter-event firing
  * Handler dispatch via app.services.review_handlers
  * Idempotency replay (Idempotency-Key header → existing order)

Compliance:
  * Each order gets exactly one IID call (no chaining; no background calls).
  * Disclosure block survives in result_json (handler returns include `iid` field).
  * Audit log row written to eaiou_marketplace_log on every state transition.
"""

import json
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.review_handlers import dispatch as dispatch_handler


class InsufficientCreditError(RuntimeError):
    """Raised when a subscription has no remaining credit for the requested SKU."""


class ProductNotFoundError(RuntimeError):
    """Raised when the requested SKU does not exist or is inactive."""


def get_product(db: Session, sku: str) -> dict:
    """Look up a product by SKU; raise ProductNotFoundError if missing/inactive."""
    row = db.execute(text("""
        SELECT sku, display_name, description,
               retail_price_cents, wholesale_price_cents,
               latency_target_seconds, handler_module, active
        FROM `#__eaiou_products` WHERE sku = :sku AND active = 1
    """), {"sku": sku}).mappings().first()
    if not row:
        raise ProductNotFoundError(f"product not found or inactive: {sku!r}")
    return dict(row)


def list_products(db: Session) -> list[dict]:
    """List all active products in catalog order (cheapest first)."""
    rows = db.execute(text("""
        SELECT sku, display_name, description,
               retail_price_cents, wholesale_price_cents,
               latency_target_seconds, handler_module
        FROM `#__eaiou_products` WHERE active = 1
        ORDER BY retail_price_cents
    """)).mappings().all()
    return [dict(r) for r in rows]


def find_existing_order_by_idempotency(
    db: Session,
    idempotency_key: str,
    user_id: Optional[str] = None,
    partner_key_id: Optional[str] = None,
) -> Optional[dict]:
    """
    Idempotency-replay safety. Returns the existing order if one was already
    created with this idempotency_key for this actor; None otherwise.
    """
    if not idempotency_key:
        return None
    if user_id:
        clause = "user_id = :actor_id"
    elif partner_key_id:
        clause = "partner_key_id = :actor_id"
    else:
        return None
    row = db.execute(text(f"""
        SELECT order_id, sku, status, result_json, amount_cents, via, created_at, completed_at
        FROM `#__eaiou_orders` WHERE {clause} AND idempotency_key = :idem_key
        LIMIT 1
    """), {"actor_id": user_id or partner_key_id, "idem_key": idempotency_key}).mappings().first()
    return dict(row) if row else None


def deduct_subscription_credit(db: Session, user_id: str, sku: str) -> bool:
    """
    Atomically decrement a subscription credit for (user, sku) if any remain.

    Returns:
      True if a credit was deducted; False if user has no active subscription
      or no remaining credits for this SKU.
    """
    # Find the active subscription for this user
    sub = db.execute(text("""
        SELECT subscription_id FROM `#__eaiou_subscriptions`
        WHERE user_id = :user_id AND status = 'active'
        ORDER BY current_period_end DESC LIMIT 1
    """), {"user_id": user_id}).mappings().first()
    if not sub:
        return False

    # Atomic-decrement only if remaining_count > 0 and within current period
    result = db.execute(text("""
        UPDATE `#__eaiou_subscription_credits`
        SET remaining_count = remaining_count - 1
        WHERE subscription_id = :sub_id
          AND sku = :sku
          AND remaining_count > 0
          AND :now BETWEEN period_start AND period_end
    """), {"sub_id": sub["subscription_id"], "sku": sku, "now": datetime.utcnow()})
    return result.rowcount > 0


def log_event(
    db: Session,
    event_type: str,
    actor_type: str,
    actor_id: Optional[str],
    entity_type: Optional[str],
    entity_id: Optional[str],
    payload: Optional[dict] = None,
):
    """Append an event to eaiou_marketplace_log (audit trail)."""
    db.execute(text("""
        INSERT INTO `#__eaiou_marketplace_log`
          (log_id, event_type, actor_type, actor_id, entity_type, entity_id, payload_json)
        VALUES (:log_id, :event_type, :actor_type, :actor_id, :entity_type, :entity_id, :payload_json)
    """), {
        "log_id": str(uuid.uuid4()),
        "event_type": event_type,
        "actor_type": actor_type,
        "actor_id": actor_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "payload_json": json.dumps(payload) if payload else None,
    })


def create_order(
    db: Session,
    sku: str,
    inputs: dict,
    *,
    user_id: Optional[str] = None,
    partner_key_id: Optional[str] = None,
    manuscript_id: Optional[str] = None,
    idempotency_key: Optional[str] = None,
    source: Optional[str] = None,
    session_id: Optional[str] = None,
) -> dict:
    """
    End-to-end order placement.

    Steps:
      1. Idempotency check — return existing order if Idempotency-Key replay
      2. Look up product (raises ProductNotFoundError on miss)
      3. Determine billing path (subscription credit vs Stripe meter vs partner wholesale)
      4. Insert pending order row
      5. Dispatch handler
      6. Update order with result + completed_at
      7. If Stripe-metered, fire meter event after success
      8. Append audit log

    Returns:
      The order row as a dict (status='completed' on happy path).
    """
    if (user_id is None) == (partner_key_id is None):
        raise ValueError("exactly one of user_id or partner_key_id must be set")

    # 1. Idempotency
    existing = find_existing_order_by_idempotency(
        db, idempotency_key, user_id=user_id, partner_key_id=partner_key_id
    )
    if existing:
        return existing

    # 2. Product lookup
    product = get_product(db, sku)

    # 3. Billing path
    is_partner = partner_key_id is not None
    via = "partner_wholesale" if is_partner else None
    amount_cents = product["wholesale_price_cents"] if is_partner else product["retail_price_cents"]

    if not is_partner:
        # Author-initiated: try subscription credit first, fall back to Stripe meter
        if deduct_subscription_credit(db, user_id, sku):
            via = "subscription_credit"
            amount_cents = 0  # credit covers it
        else:
            via = "stripe_meter"
            # actual charge fires after handler success (step 7)

    # 4. Insert pending order
    order_id = str(uuid.uuid4())
    db.execute(text("""
        INSERT INTO `#__eaiou_orders`
          (order_id, user_id, partner_key_id, sku, manuscript_id,
           inputs_json, status, amount_cents, via,
           idempotency_key, source, session_id)
        VALUES
          (:order_id, :user_id, :partner_key_id, :sku, :manuscript_id,
           :inputs_json, 'running', :amount_cents, :via,
           :idempotency_key, :source, :session_id)
    """), {
        "order_id": order_id,
        "user_id": user_id,
        "partner_key_id": partner_key_id,
        "sku": sku,
        "manuscript_id": manuscript_id,
        "inputs_json": json.dumps(inputs),
        "amount_cents": amount_cents,
        "via": via,
        "idempotency_key": idempotency_key,
        "source": source,
        "session_id": session_id,
    })
    log_event(
        db, "order.created",
        actor_type="user" if user_id else "partner",
        actor_id=user_id or partner_key_id,
        entity_type="order", entity_id=order_id,
        payload={"sku": sku, "via": via, "amount_cents": amount_cents},
    )

    # 5. Dispatch handler
    ctx = {
        "user_id": user_id,
        "partner_key_id": partner_key_id,
        "manuscript_id": manuscript_id,
        "order_id": order_id,
    }
    try:
        result = dispatch_handler(sku, inputs, ctx)
        status = "failed" if result.get("error") else "completed"
    except Exception as exc:
        # Defensive — dispatch_handler should already trap exceptions, but
        # we re-trap to keep the order row consistent.
        result = {"error": f"unhandled exception: {exc}", "iid": {}}
        status = "failed"

    # 6. Update order with result
    completed_at = datetime.utcnow()
    db.execute(text("""
        UPDATE `#__eaiou_orders`
        SET result_json = :result_json,
            status = :status,
            completed_at = :completed_at,
            iid_id = :iid_id
        WHERE order_id = :order_id
    """), {
        "order_id": order_id,
        "result_json": json.dumps(result),
        "status": status,
        "completed_at": completed_at,
        "iid_id": result.get("iid", {}).get("instance_hash"),
    })
    log_event(
        db, f"order.{status}",
        actor_type="user" if user_id else "partner",
        actor_id=user_id or partner_key_id,
        entity_type="order", entity_id=order_id,
        payload={"sku": sku, "iid": result.get("iid")},
    )

    # 7. Fire Stripe meter event AFTER handler success
    if status == "completed" and via == "stripe_meter":
        try:
            from app.services import stripe_client  # late import to avoid req at boot

            customer = _stripe_customer_for_user(db, user_id)
            if customer:
                event = stripe_client.record_meter_event(customer, sku, count=1)
                db.execute(text("""
                    UPDATE `#__eaiou_orders` SET stripe_meter_event_id = :ev WHERE order_id = :order_id
                """), {"ev": event.get("id"), "order_id": order_id})
                log_event(
                    db, "stripe.meter_event_recorded",
                    actor_type="system", actor_id=None,
                    entity_type="order", entity_id=order_id,
                    payload={"event_id": event.get("id"), "sku": sku},
                )
        except Exception as exc:
            log_event(
                db, "stripe.meter_event_failed",
                actor_type="system", actor_id=None,
                entity_type="order", entity_id=order_id,
                payload={"error": str(exc)},
            )
            # Don't fail the order — meter sync runs in reconciliation later.

    db.commit()

    return get_order(db, order_id)


def get_order(db: Session, order_id: str) -> Optional[dict]:
    """Fetch an order by id with parsed result_json."""
    row = db.execute(text("""
        SELECT order_id, user_id, partner_key_id, sku, manuscript_id,
               inputs_json, result_json, status, iid_id, amount_cents, via,
               stripe_meter_event_id, idempotency_key, source, session_id,
               created_at, completed_at, refunded_at
        FROM `#__eaiou_orders` WHERE order_id = :order_id
    """), {"order_id": order_id}).mappings().first()
    if not row:
        return None
    out = dict(row)
    if out["inputs_json"]:
        try:
            out["inputs"] = json.loads(out["inputs_json"])
        except json.JSONDecodeError:
            out["inputs"] = {}
    if out["result_json"]:
        try:
            out["result"] = json.loads(out["result_json"])
        except json.JSONDecodeError:
            out["result"] = {}
    return out


def cancel_order(
    db: Session,
    order_id: str,
    *,
    user_id: Optional[str] = None,
    partner_key_id: Optional[str] = None,
    refund: bool = False,
) -> dict:
    """
    Cancel an order. M-4 fix (audit-trail): caller passes user_id or partner_key_id
    so the audit log records the actual actor instead of None.

    If `refund` and the order was Stripe-charged, raise a refund request via the
    Stripe webhook flow (not implemented in Phase 0).
    """
    db.execute(text("""
        UPDATE `#__eaiou_orders`
        SET status = 'cancelled', refunded_at = :now
        WHERE order_id = :order_id AND status IN ('pending', 'running')
    """), {"order_id": order_id, "now": datetime.utcnow()})
    log_event(
        db, "order.cancelled",
        actor_type="user" if user_id else ("partner" if partner_key_id else "system"),
        actor_id=user_id or partner_key_id,
        entity_type="order", entity_id=order_id,
        payload={"refund_requested": refund},
    )
    db.commit()
    return get_order(db, order_id)


def _stripe_customer_for_user(db: Session, user_id: str):
    """Internal: look up the Stripe customer associated with a user."""
    row = db.execute(text("""
        SELECT stripe_customer_id FROM `#__eaiou_subscriptions`
        WHERE user_id = :user_id AND stripe_customer_id IS NOT NULL
        ORDER BY current_period_end DESC LIMIT 1
    """), {"user_id": user_id}).mappings().first()
    if not row or not row["stripe_customer_id"]:
        return None
    from app.services import stripe_client
    return stripe_client.stripe.Customer.retrieve(row["stripe_customer_id"])
