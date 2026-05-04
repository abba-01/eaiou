"""
api_iid_providers.py — CRUD on eaiou_iid_providers (per-user IID configurations).

Endpoints:
  GET    /api/iid/providers              — list current user's providers
  GET    /api/iid/providers/{id}         — fetch one
  POST   /api/iid/providers              — create new
  PATCH  /api/iid/providers/{id}         — update (display_name, default_model, enabled_actions, cost_cap_cents)
  POST   /api/iid/providers/{id}/key     — set / rotate API key (separate endpoint; key is never returned)
  DELETE /api/iid/providers/{id}         — soft-delete (active=0, disabled_at=now)
  POST   /api/iid/providers/{id}/test    — minimal ping to verify auth (Phase 1 wire-up)

Auth: Depends(require_auth). Per-user isolation enforced at every query
(provider must belong to current_user.id). Per ToS Compliance Doctrine §1
Rule 3 (per-provider credential isolation):
  * API keys encrypted at rest via Fernet (cryptography lib)
  * Encryption key sourced from EAIOU_IID_KEY_FERNET in .env (NOT in DB)
  * Raw key NEVER returned in any response — only the prefix (first 8 chars)
  * Rotation issues a new ciphertext, no plaintext stored intermediately

Tags: iid-providers
Prefix: /api/iid/providers
"""

import json
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_auth

router = APIRouter(prefix="/api/iid/providers", tags=["iid-providers"])


# ── Encryption helpers ────────────────────────────────────────────────────────

def _fernet() -> Fernet:
    """
    Load Fernet from EAIOU_IID_KEY_FERNET env var. Raises 503 if not configured
    so the operator sees the gap clearly.
    """
    key = os.getenv("EAIOU_IID_KEY_FERNET")
    if not key:
        raise HTTPException(
            status_code=503,
            detail=(
                "EAIOU_IID_KEY_FERNET not configured. Generate via "
                "`python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'` "
                "and add to .env."
            ),
        )
    try:
        return Fernet(key.encode("utf-8") if isinstance(key, str) else key)
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=503,
            detail=f"EAIOU_IID_KEY_FERNET malformed: {exc}",
        )


def _encrypt(raw: str) -> bytes:
    return _fernet().encrypt(raw.encode("utf-8"))


def _decrypt(ciphertext: bytes) -> str:
    try:
        return _fernet().decrypt(ciphertext).decode("utf-8")
    except InvalidToken as exc:
        raise HTTPException(status_code=500, detail="stored API key cannot be decrypted (key rotation needed)")


# ── Provider name → legal-entity defaults ─────────────────────────────────────

_PROVIDER_DEFAULTS = {
    "mae":     {"provider_legal": "Anthropic", "default_model_hint": "claude-opus-4-7"},
    "openai":  {"provider_legal": "OpenAI",    "default_model_hint": "gpt-5"},
    "gemini":  {"provider_legal": "Google",    "default_model_hint": "gemini-2.5"},
    "llama":   {"provider_legal": "Meta",      "default_model_hint": "llama-3.1-405b"},
    "custom":  {"provider_legal": "Custom",    "default_model_hint": ""},
}


# ── Pydantic models ───────────────────────────────────────────────────────────

class ProviderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    display_name: str = Field(..., min_length=1, max_length=128)
    default_model: str = Field(..., min_length=1, max_length=128)
    api_key: str = Field(..., min_length=8, max_length=512, description="Raw API key — encrypted at rest, never returned")
    api_endpoint_url: Optional[str] = Field(default=None, max_length=512, description="Override for custom providers only")
    enabled_actions: Optional[list[str]] = Field(default=None)
    cost_cap_cents: Optional[int] = Field(default=None, ge=0)

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        # Allow standard provider names; custom prefix permitted via 'custom_*'
        if v in _PROVIDER_DEFAULTS:
            return v
        if v.startswith("custom_") and len(v) > 7:
            return v
        raise ValueError(
            f"name must be one of {list(_PROVIDER_DEFAULTS.keys())} or start with 'custom_'"
        )


class ProviderUpdate(BaseModel):
    display_name: Optional[str] = Field(default=None, max_length=128)
    default_model: Optional[str] = Field(default=None, max_length=128)
    enabled_actions: Optional[list[str]] = Field(default=None)
    cost_cap_cents: Optional[int] = Field(default=None, ge=0)
    active: Optional[bool] = None


class ProviderKeyUpdate(BaseModel):
    api_key: str = Field(..., min_length=8, max_length=512)


class ProviderOut(BaseModel):
    id: int
    name: str
    display_name: str
    provider_legal: str
    default_model: str
    api_key_prefix: Optional[str] = None
    api_endpoint_url: Optional[str] = None
    enabled_actions: Optional[list[str]] = None
    cost_cap_cents: Optional[int] = None
    active: bool
    created_at: str
    updated_at: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=list[ProviderOut])
def list_providers(
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """List all providers configured by the current user (active + inactive)."""
    rows = db.execute(text("""
        SELECT id, name, display_name, provider_legal, default_model,
               api_key_encrypted, api_endpoint_url, enabled_actions,
               cost_cap_cents, active, created_at, updated_at
        FROM `#__eaiou_iid_providers`
        WHERE user_id = :uid
        ORDER BY active DESC, name
    """), {"uid": current_user["id"]}).mappings().all()
    return [_to_out(r) for r in rows]


@router.get("/{provider_id}", response_model=ProviderOut)
def get_provider(
    provider_id: int,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    row = _load(db, current_user["id"], provider_id)
    if not row:
        raise HTTPException(status_code=404, detail="provider not found")
    return _to_out(row)


@router.post("", response_model=ProviderOut, status_code=201)
def create_provider(
    body: ProviderCreate,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    defaults = _PROVIDER_DEFAULTS.get(body.name, _PROVIDER_DEFAULTS["custom"])
    encrypted = _encrypt(body.api_key)

    try:
        result = db.execute(text("""
            INSERT INTO `#__eaiou_iid_providers`
              (user_id, name, display_name, provider_legal, default_model,
               api_key_encrypted, api_endpoint_url, enabled_actions,
               cost_cap_cents, active)
            VALUES
              (:uid, :name, :display, :legal, :model,
               :keyenc, :endpoint, :actions,
               :cap, 1)
        """), {
            "uid": current_user["id"],
            "name": body.name,
            "display": body.display_name,
            "legal": defaults["provider_legal"],
            "model": body.default_model,
            "keyenc": encrypted,
            "endpoint": body.api_endpoint_url,
            "actions": json.dumps(body.enabled_actions) if body.enabled_actions else None,
            "cap": body.cost_cap_cents,
        })
    except Exception as exc:
        if "Duplicate entry" in str(exc):
            raise HTTPException(status_code=409, detail=f"provider {body.name!r} already configured for this user")
        raise

    db.commit()
    return get_provider(result.lastrowid, current_user=current_user, db=db)


@router.patch("/{provider_id}", response_model=ProviderOut)
def update_provider(
    provider_id: int,
    body: ProviderUpdate,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    if not _load(db, current_user["id"], provider_id):
        raise HTTPException(status_code=404, detail="provider not found")

    fields = []
    params = {"pid": provider_id, "uid": current_user["id"]}
    if body.display_name is not None:
        fields.append("display_name = :display"); params["display"] = body.display_name
    if body.default_model is not None:
        fields.append("default_model = :model");  params["model"] = body.default_model
    if body.enabled_actions is not None:
        fields.append("enabled_actions = :actions"); params["actions"] = json.dumps(body.enabled_actions)
    if body.cost_cap_cents is not None:
        fields.append("cost_cap_cents = :cap");   params["cap"] = body.cost_cap_cents
    if body.active is not None:
        fields.append("active = :active");        params["active"] = 1 if body.active else 0
        if not body.active:
            fields.append("disabled_at = NOW()")

    if not fields:
        return get_provider(provider_id, current_user=current_user, db=db)

    db.execute(
        text(f"UPDATE `#__eaiou_iid_providers` SET {', '.join(fields)} WHERE id = :pid AND user_id = :uid"),
        params,
    )
    db.commit()
    return get_provider(provider_id, current_user=current_user, db=db)


@router.post("/{provider_id}/key", response_model=ProviderOut)
def rotate_key(
    provider_id: int,
    body: ProviderKeyUpdate,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Replace the stored encrypted API key. Raw key NEVER returned."""
    if not _load(db, current_user["id"], provider_id):
        raise HTTPException(status_code=404, detail="provider not found")

    encrypted = _encrypt(body.api_key)
    db.execute(text("""
        UPDATE `#__eaiou_iid_providers`
        SET api_key_encrypted = :keyenc, disabled_at = NULL, active = 1
        WHERE id = :pid AND user_id = :uid
    """), {"keyenc": encrypted, "pid": provider_id, "uid": current_user["id"]})
    db.commit()
    return get_provider(provider_id, current_user=current_user, db=db)


@router.delete("/{provider_id}", status_code=204)
def delete_provider(
    provider_id: int,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Soft delete: active=0, disabled_at=now. Audit row preserved."""
    if not _load(db, current_user["id"], provider_id):
        raise HTTPException(status_code=404, detail="provider not found")
    db.execute(text("""
        UPDATE `#__eaiou_iid_providers`
        SET active = 0, disabled_at = NOW()
        WHERE id = :pid AND user_id = :uid
    """), {"pid": provider_id, "uid": current_user["id"]})
    db.commit()
    return None


@router.post("/{provider_id}/test")
def test_provider(
    provider_id: int,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    Phase 0: returns the prefix + provider info; doesn't actually call the
    provider API yet. Phase 1 will wire a minimal ping per provider adapter
    (anthropic 'haiku ping', openai 'gpt-4o-mini ping', etc.) to verify the
    key actually authenticates.
    """
    row = _load(db, current_user["id"], provider_id)
    if not row:
        raise HTTPException(status_code=404, detail="provider not found")
    return {
        "provider_id": provider_id,
        "name": row["name"],
        "active": bool(row["active"]),
        "phase": "stub",
        "note": "Phase 1: real ping to provider API will replace this stub.",
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load(db: Session, user_id: int, provider_id: int) -> Optional[dict]:
    row = db.execute(text("""
        SELECT id, user_id, name, display_name, provider_legal, default_model,
               api_key_encrypted, api_endpoint_url, enabled_actions,
               cost_cap_cents, active, created_at, updated_at
        FROM `#__eaiou_iid_providers`
        WHERE id = :pid AND user_id = :uid
    """), {"pid": provider_id, "uid": user_id}).mappings().first()
    return dict(row) if row else None


def _to_out(row: dict) -> ProviderOut:
    """Map DB row to ProviderOut, exposing only the api_key_prefix (never raw)."""
    api_key_prefix = None
    if row.get("api_key_encrypted"):
        # Decrypt just to compute prefix; the raw key never leaves this function.
        try:
            raw = _decrypt(row["api_key_encrypted"])
            api_key_prefix = raw[:8] + "…" if len(raw) > 8 else raw[:4] + "…"
        except HTTPException:
            api_key_prefix = "<encrypted>"
        except Exception:
            api_key_prefix = "<error>"

    enabled = None
    if row.get("enabled_actions"):
        try:
            enabled = json.loads(row["enabled_actions"])
        except json.JSONDecodeError:
            enabled = None

    return ProviderOut(
        id=row["id"],
        name=row["name"],
        display_name=row["display_name"],
        provider_legal=row["provider_legal"],
        default_model=row["default_model"],
        api_key_prefix=api_key_prefix,
        api_endpoint_url=row.get("api_endpoint_url"),
        enabled_actions=enabled,
        cost_cap_cents=row.get("cost_cap_cents"),
        active=bool(row["active"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )
