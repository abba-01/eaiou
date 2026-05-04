"""
eaiou / checksubmit marketplace API
Phase 0 router for the review-as-a-service storefront.

Endpoints:
  GET  /api/v1/products                 — public catalog (wholesale stripped)
  POST /api/v1/orders                   — place an order (author OR partner)
  GET  /api/v1/orders/{order_id}        — fetch an order
  POST /api/v1/orders/{order_id}/cancel — cancel a pending/running order

Auth modes (via _resolve_actor dep):
  * Bearer / session (eaiou user) — via Depends(optional_auth)
  * Partner key (eaiou_pk_*) — X-Partner-Key header, SHA-256 lookup

Security hardening (audit 2026-05-02):
  * H-3 fix: _resolve_actor is a real FastAPI dep using Depends(optional_auth) —
    no more reading request.state.current_user (nothing populated it).
  * M-1 fix: OrderCreate.inputs has 8KB cap + key-type sanity check.
  * M-2 fix: source field allowlist {manuscript_editor, api_v1, partner_api, mcp}.
  * M-3 fix: ProductPublicOut (no wholesale) for unauthenticated callers;
    ProductPartnerOut (with wholesale) for partner-key callers.
  * M-4 fix: cancel_order passes actor_id through to audit log.

Tags: marketplace
Prefix: /api/v1
"""

import hashlib
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import optional_auth
from ..services import marketplace

router = APIRouter(prefix="/api/v1", tags=["marketplace"])


# ── Constants ─────────────────────────────────────────────────────────────────

_VALID_SOURCES = frozenset({"manuscript_editor", "api_v1", "partner_api", "mcp", "gpt_app"})
_MAX_INPUTS_BYTES = 8 * 1024  # 8 KB


# ── Pydantic models ───────────────────────────────────────────────────────────

class ProductPublicOut(BaseModel):
    """Public catalog view — no wholesale price (M-3 fix)."""
    sku: str
    display_name: str
    description: Optional[str] = None
    retail_price_cents: int
    latency_target_seconds: int


class ProductPartnerOut(ProductPublicOut):
    """Partner catalog view — includes wholesale price for billing transparency."""
    wholesale_price_cents: int


class OrderCreate(BaseModel):
    sku: str
    inputs: dict = Field(default_factory=dict)
    manuscript_id: Optional[str] = None
    source: Optional[str] = Field(default=None, description=f"One of: {sorted(_VALID_SOURCES)}")
    session_id: Optional[str] = None

    @field_validator("inputs")
    @classmethod
    def validate_inputs_size(cls, v: dict) -> dict:
        """M-1 fix: cap inputs at 8KB; reject non-string keys."""
        if not isinstance(v, dict):
            raise ValueError("inputs must be a JSON object")
        if any(not isinstance(k, str) for k in v.keys()):
            raise ValueError("inputs keys must all be strings")
        size = len(json.dumps(v).encode("utf-8"))
        if size > _MAX_INPUTS_BYTES:
            raise ValueError(f"inputs exceeds 8KB cap (got {size} bytes)")
        return v

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: Optional[str]) -> Optional[str]:
        """M-2 fix: source must be in allowlist when set."""
        if v is None:
            return None
        if v not in _VALID_SOURCES:
            raise ValueError(f"source must be one of {sorted(_VALID_SOURCES)}")
        return v


class OrderOut(BaseModel):
    order_id: str
    sku: str
    status: str
    via: Optional[str] = None
    amount_cents: int
    iid_id: Optional[str] = None
    manuscript_id: Optional[str] = None
    source: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    inputs: Optional[dict] = None
    result: Optional[dict] = None


# ── Auth resolver (H-3 fix — proper FastAPI dep, no state inspection) ────────

def _resolve_partner_key(db: Session, raw_key: str) -> Optional[str]:
    """Validate a partner key by SHA-256 hash; return partner_key_id or None."""
    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    row = db.execute(text("""
        SELECT partner_key_id, active, revoked_at
        FROM `#__eaiou_partner_keys`
        WHERE key_hash = :key_hash LIMIT 1
    """), {"key_hash": key_hash}).mappings().first()
    if not row or not row["active"] or row["revoked_at"]:
        return None
    db.execute(text("""
        UPDATE `#__eaiou_partner_keys`
        SET last_used_at = :now
        WHERE partner_key_id = :pk
    """), {"now": datetime.utcnow(), "pk": row["partner_key_id"]})
    db.commit()
    return row["partner_key_id"]


def resolve_actor(
    request: Request,
    current_user: Optional[dict] = Depends(optional_auth),
    db: Session = Depends(get_db),
) -> tuple[Optional[str], Optional[str]]:
    """
    H-3 fix: real dep, real auth resolution.

    Auth precedence:
      1. X-Partner-Key header → partner-initiated order
      2. Session-authenticated eaiou user (via optional_auth dep) → user order
      3. Otherwise 401

    Returns (user_id, partner_key_id) where exactly one is set.
    """
    partner_key = request.headers.get("X-Partner-Key")
    if partner_key:
        partner_key_id = _resolve_partner_key(db, partner_key)
        if not partner_key_id:
            raise HTTPException(status_code=401, detail="invalid partner key")
        return None, partner_key_id

    if current_user and current_user.get("id"):
        return str(current_user["id"]), None

    raise HTTPException(status_code=401, detail="authentication required")


def resolve_actor_optional(
    request: Request,
    current_user: Optional[dict] = Depends(optional_auth),
    db: Session = Depends(get_db),
) -> tuple[Optional[str], Optional[str], bool]:
    """
    Like resolve_actor but doesn't raise on missing auth.

    Returns (user_id, partner_key_id, is_authenticated).
    Used by GET /products which serves both anon and partner views.
    """
    partner_key = request.headers.get("X-Partner-Key")
    if partner_key:
        partner_key_id = _resolve_partner_key(db, partner_key)
        if partner_key_id:
            return None, partner_key_id, True
        # Bad partner key falls through to anonymous (don't leak validity timing)

    if current_user and current_user.get("id"):
        return str(current_user["id"]), None, True

    return None, None, False


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/products")
def list_products(
    actor: tuple = Depends(resolve_actor_optional),
    db: Session = Depends(get_db),
):
    """
    Public catalog. Returns ProductPublicOut for anon callers,
    ProductPartnerOut (with wholesale) for partner-key callers (M-3 fix).
    """
    _, partner_key_id, _ = actor
    products = marketplace.list_products(db)

    if partner_key_id:
        return [ProductPartnerOut(
            sku=p["sku"],
            display_name=p["display_name"],
            description=p.get("description"),
            retail_price_cents=p["retail_price_cents"],
            wholesale_price_cents=p["wholesale_price_cents"],
            latency_target_seconds=p["latency_target_seconds"],
        ) for p in products]

    return [ProductPublicOut(
        sku=p["sku"],
        display_name=p["display_name"],
        description=p.get("description"),
        retail_price_cents=p["retail_price_cents"],
        latency_target_seconds=p["latency_target_seconds"],
    ) for p in products]


@router.post("/orders", response_model=OrderOut, status_code=201)
def create_order(
    body: OrderCreate,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    actor: tuple = Depends(resolve_actor),
    db: Session = Depends(get_db),
):
    """
    Place an order. Auth via resolve_actor dep (Bearer/session OR X-Partner-Key).
    """
    user_id, partner_key_id = actor

    try:
        order = marketplace.create_order(
            db,
            sku=body.sku,
            inputs=body.inputs,
            user_id=user_id,
            partner_key_id=partner_key_id,
            manuscript_id=body.manuscript_id,
            idempotency_key=idempotency_key,
            source=body.source or ("partner_api" if partner_key_id else "api_v1"),
            session_id=body.session_id,
        )
    except marketplace.ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return _to_order_out(order)


@router.get("/orders/{order_id}", response_model=OrderOut)
def get_order(
    order_id: str,
    actor: tuple = Depends(resolve_actor),
    db: Session = Depends(get_db),
):
    """Fetch an order. Author orders visible only to author; partner orders only to partner."""
    user_id, partner_key_id = actor
    order = marketplace.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="order not found")

    if user_id and order.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="not your order")
    if partner_key_id and order.get("partner_key_id") != partner_key_id:
        raise HTTPException(status_code=403, detail="not your order")

    return _to_order_out(order)


@router.post("/orders/{order_id}/cancel", response_model=OrderOut)
def cancel_order(
    order_id: str,
    actor: tuple = Depends(resolve_actor),
    db: Session = Depends(get_db),
):
    """Cancel a pending or running order. Audit log records actor (M-4 fix)."""
    user_id, partner_key_id = actor
    order = marketplace.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="order not found")
    if user_id and order.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="not your order")
    if partner_key_id and order.get("partner_key_id") != partner_key_id:
        raise HTTPException(status_code=403, detail="not your order")
    if order["status"] not in ("pending", "running"):
        raise HTTPException(status_code=409, detail=f"cannot cancel order in status {order['status']}")

    # M-4 fix: pass user_id / partner_key_id so audit log captures actor
    cancelled = marketplace.cancel_order(
        db, order_id,
        user_id=user_id,
        partner_key_id=partner_key_id,
        refund=False,
    )
    return _to_order_out(cancelled)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_order_out(order: dict) -> OrderOut:
    """Convert raw marketplace dict to OrderOut response model."""
    return OrderOut(
        order_id=order["order_id"],
        sku=order["sku"],
        status=order["status"],
        via=order.get("via"),
        amount_cents=order["amount_cents"],
        iid_id=order.get("iid_id"),
        manuscript_id=order.get("manuscript_id"),
        source=order.get("source"),
        created_at=order["created_at"],
        completed_at=order.get("completed_at"),
        refunded_at=order.get("refunded_at"),
        inputs=order.get("inputs"),
        result=order.get("result"),
    )
