"""
stripe_client.py — Stripe SDK wrapper for the checksubmit MVP.

Phase 0 wiring (test-mode safe). Provides:
  * get_or_create_customer(user)         — idempotent customer object per eaiou user
  * create_subscription(customer, tier)  — Stripe Subscription with the tier's price
  * record_meter_event(customer, sku, count) — for à-la-carte metered billing
  * cancel_subscription(subscription_id) — graceful cancel at period end
  * verify_webhook(payload, signature)   — Stripe webhook signature validation

Configuration via env vars (.env):
  STRIPE_SECRET_KEY        — sk_test_... or sk_live_...
  STRIPE_WEBHOOK_SECRET    — whsec_... (used to verify webhook payloads)
  STRIPE_PRICE_FREE        — Stripe price id for free tier (or empty)
  STRIPE_PRICE_STARTER     — Stripe price id for starter tier
  STRIPE_PRICE_PRO         — Stripe price id for pro tier
  STRIPE_PRICE_ENTERPRISE  — Stripe price id for enterprise tier
  STRIPE_METER_PREFIX      — defaults to "checksubmit_meter_"; meters are named
                             "{prefix}{sku}" so each SKU gets its own meter

This wrapper deliberately does NOT cache customer/subscription objects locally;
the eaiou_subscriptions and eaiou_orders tables are the source of truth for
state-querying. Stripe is the source of truth for billing reconciliation.

Failure mode: every method either succeeds or raises stripe.error.StripeError;
callers should wrap calls in try/except and persist the error for audit
(eaiou_marketplace_log + eaiou_orders.status='failed').
"""

import os
from typing import Optional

import stripe
from dotenv import load_dotenv

load_dotenv()

# Test-mode keys are safe to use in development; live keys flip in production.
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
METER_PREFIX = os.getenv("STRIPE_METER_PREFIX", "checksubmit_meter_")

TIER_PRICE_IDS = {
    "free":       os.getenv("STRIPE_PRICE_FREE", ""),
    "starter":    os.getenv("STRIPE_PRICE_STARTER", ""),
    "pro":        os.getenv("STRIPE_PRICE_PRO", ""),
    "enterprise": os.getenv("STRIPE_PRICE_ENTERPRISE", ""),
}


class StripeNotConfigured(RuntimeError):
    """Raised when stripe operations are attempted without STRIPE_SECRET_KEY set."""


def _require_configured():
    if not stripe.api_key:
        raise StripeNotConfigured(
            "STRIPE_SECRET_KEY is not set; cannot make Stripe calls. "
            "Add your sk_test_... or sk_live_... key to .env, then restart."
        )


def get_or_create_customer(user) -> stripe.Customer:
    """
    Idempotent: looks up or creates a Stripe Customer for the given eaiou user.

    The user's Stripe customer ID is stored in the eaiou_subscriptions table
    once any subscription has been created. Until then, this function
    creates-on-first-call.

    Args:
      user: eaiou user object with attributes `id`, `email`, optional `name`.

    Returns:
      stripe.Customer object.
    """
    _require_configured()

    # Search Stripe by metadata.eaiou_user_id (idempotent lookup).
    existing = stripe.Customer.search(
        query=f"metadata['eaiou_user_id']:'{user.id}'",
        limit=1,
    )
    if existing.data:
        return existing.data[0]

    return stripe.Customer.create(
        email=user.email,
        name=getattr(user, "name", None),
        metadata={"eaiou_user_id": str(user.id)},
    )


def create_subscription(customer: stripe.Customer, tier: str) -> stripe.Subscription:
    """
    Create a Stripe Subscription for the given customer at the given tier.

    Args:
      customer: stripe.Customer (use get_or_create_customer to obtain).
      tier:     "free" | "starter" | "pro" | "enterprise".

    Returns:
      stripe.Subscription object.

    Raises:
      ValueError if tier is unknown or its price id is unset.
    """
    _require_configured()

    price_id = TIER_PRICE_IDS.get(tier)
    if not price_id:
        raise ValueError(
            f"No STRIPE_PRICE_{tier.upper()} configured; cannot create {tier} subscription."
        )

    return stripe.Subscription.create(
        customer=customer.id,
        items=[{"price": price_id}],
        # Apply Stripe Tax if enabled in the dashboard
        automatic_tax={"enabled": True},
        # Default to incomplete-then-prorate so the client can confirm payment
        payment_behavior="default_incomplete",
        payment_settings={"save_default_payment_method": "on_subscription"},
        expand=["latest_invoice.payment_intent"],
        metadata={"eaiou_tier": tier},
    )


def record_meter_event(customer: stripe.Customer, sku: str, count: int = 1) -> dict:
    """
    Record a metered billing event for an à-la-carte SKU.

    Stripe Meters bill as count * unit_price; we send count=1 per IID call,
    or count=N for batched calls (rare).

    Args:
      customer: stripe.Customer.
      sku:      product SKU (must match a configured Stripe Meter named
                f"{METER_PREFIX}{sku}").
      count:    integer event count, default 1.

    Returns:
      dict with the meter event's id and timestamp (Stripe API response).
    """
    _require_configured()

    return stripe.billing.MeterEvent.create(
        event_name=f"{METER_PREFIX}{sku}",
        payload={
            "stripe_customer_id": customer.id,
            "value": str(count),
        },
    )


def cancel_subscription(subscription_id: str, at_period_end: bool = True) -> stripe.Subscription:
    """
    Cancel a Stripe subscription. Default: cancel at period end (graceful);
    pass at_period_end=False to cancel immediately and prorate.
    """
    _require_configured()

    if at_period_end:
        return stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True,
        )
    return stripe.Subscription.delete(subscription_id)


def verify_webhook(payload: bytes, signature_header: str) -> stripe.Event:
    """
    Verify and parse a Stripe webhook payload.

    Args:
      payload:          raw request body bytes (must NOT be modified or decoded).
      signature_header: value of the Stripe-Signature header.

    Returns:
      stripe.Event object.

    Raises:
      stripe.error.SignatureVerificationError if the signature doesn't match.
    """
    if not WEBHOOK_SECRET:
        raise StripeNotConfigured(
            "STRIPE_WEBHOOK_SECRET is not set; cannot verify webhook payloads."
        )
    return stripe.Webhook.construct_event(
        payload=payload,
        sig_header=signature_header,
        secret=WEBHOOK_SECRET,
    )


def get_subscription(subscription_id: str) -> stripe.Subscription:
    """Fetch a subscription by ID (passthrough to Stripe API)."""
    _require_configured()
    return stripe.Subscription.retrieve(subscription_id)


def list_meter_events(customer: stripe.Customer, sku: Optional[str] = None,
                      since_unix: Optional[int] = None) -> list:
    """
    Reconcile-time helper: list meter events for a customer (optionally for
    a specific SKU and since a given timestamp).
    """
    _require_configured()
    params = {"customer": customer.id, "limit": 100}
    if sku:
        params["event_name"] = f"{METER_PREFIX}{sku}"
    if since_unix:
        params["timestamp"] = {"gte": since_unix}
    return list(stripe.billing.MeterEvent.list(**params).auto_paging_iter())
