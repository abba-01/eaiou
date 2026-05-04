# eaiou Multi-IID Authoring Workflow — Implementation Guide

**Date:** 2026-05-01
**Author:** Eric D. Martin
**Status:** Implementation reference for the inline IID-assistance feature on the author writing surface
**Scope:** Backend services + routers + database + auth + integration with existing eaiou IntelliD layer
**Related design files:** `/scratch/repos/eaiou/ui-projects/UXPILOT_AUTHORING_*.md` — wireframe specifications for the UI side

---

## 1. Goals and constraints

The multi-IID authoring workflow extends eaiou's existing FastAPI app with:

1. **Per-author IID provider registry** — each author can configure 1+ IID providers (Mae/Anthropic, OpenAI, Gemini, custom) with their own API keys, quotas, and enabled actions
2. **Action invocation API** — author-driven actions (`scope_check`, `journal_select`, `clarity_check`, `methods_check`, `reference_audit`, `outline_check`, `full_review`, `premium_review`) dispatched to the chosen IID provider
3. **Output persistence + lineage** — every IID call produces an immutable output record bound to the manuscript version it was made on
4. **SAID-framework disclosure** — every output carries full provider/model/instance disclosure, never blended with other providers
5. **ToS-compliance enforcement** — the system structurally prevents IID chaining and provides per-provider isolation
6. **Multi-IID parallel rendering** — UI can fire the same action against multiple IIDs concurrently, persist outputs side-by-side

### Critical constraints

- **No IID is the default.** Author opts into a provider; the system never auto-selects.
- **No IID output is auto-merged.** If author wants synthesis, they write it themselves.
- **No IID call happens without author action.** No background daemons; no scheduled IID invocations.
- **Stub mode is honest.** When a handler is in stub state, the response is explicitly labeled as stub.

---

## 2. Architecture overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser (author writing surface)                                │
│  - /author/manuscript/{id}/edit                                  │
│  - JS triggers POST /api/v1/iid/actions                          │
│  - Renders output cards, disclosure blocks, parallel comparison  │
└─────────────────────────────────────────────────────────────────┘
                              ↓ JSON over HTTPS, JWT bearer auth
┌─────────────────────────────────────────────────────────────────┐
│  FastAPI app (eaiou)                                             │
│  ┌───────────────────────────────────────────────────────┐      │
│  │  app/routers/api_iid.py  (NEW)                         │      │
│  │   POST /api/v1/iid/actions          (invoke)           │      │
│  │   GET  /api/v1/iid/actions/{job_id} (poll/fetch)       │      │
│  │   POST /api/v1/iid/actions/multi    (parallel run)     │      │
│  │   GET  /api/v1/iid/providers         (list active)     │      │
│  │   POST /api/v1/iid/providers         (add)             │      │
│  │   PATCH /api/v1/iid/providers/{id}   (configure)       │      │
│  │   DELETE /api/v1/iid/providers/{id}  (disable/remove)  │      │
│  │   GET  /api/v1/iid/outputs/{manuscript_id}  (history)  │      │
│  └───────────────────────────────────────────────────────┘      │
│  ┌───────────────────────────────────────────────────────┐      │
│  │  app/services/iid_dispatcher.py  (NEW)                 │      │
│  │   - Action dispatch entry point                        │      │
│  │   - Provider lookup, quota check, cost gate            │      │
│  │   - Idempotency-Key handling                           │      │
│  │   - Calls into provider-specific adapter               │      │
│  │   - Persists output record + IntelliId update          │      │
│  └───────────────────────────────────────────────────────┘      │
│  ┌───────────────────────────────────────────────────────┐      │
│  │  app/services/iid_providers/                           │      │
│  │   __init__.py     — provider registry pattern          │      │
│  │   anthropic.py    — Mae adapter (NEW)                  │      │
│  │   openai.py       — OpenAI adapter (placeholder; later)│      │
│  │   custom.py       — generic HTTP adapter (advanced)    │      │
│  └───────────────────────────────────────────────────────┘      │
│  ┌───────────────────────────────────────────────────────┐      │
│  │  app/services/iid_handlers/  (mirrors review_handlers) │      │
│  │   __init__.py            — handler registry            │      │
│  │   scope_check.py         — prompt + result schema      │      │
│  │   journal_select.py                                    │      │
│  │   clarity_check.py                                     │      │
│  │   methods_check.py                                     │      │
│  │   reference_audit.py                                   │      │
│  │   outline_check.py                                     │      │
│  │   full_review.py                                       │      │
│  │   premium_review.py                                    │      │
│  └───────────────────────────────────────────────────────┘      │
│  ┌───────────────────────────────────────────────────────┐      │
│  │  app/services/intellid.py  (EXISTING, extended)        │      │
│  │   - Per-provider IntelliId records                     │      │
│  │   - instance_hash sealing                              │      │
│  │   - CosmoID binding                                    │      │
│  └───────────────────────────────────────────────────────┘      │
│  ┌───────────────────────────────────────────────────────┐      │
│  │  app/models/iid_action.py + iid_provider.py  (NEW)     │      │
│  │   - SQLAlchemy models                                  │      │
│  │   - Pydantic request/response                          │      │
│  └───────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  MariaDB (eaiou DB) — new tables in migration_008               │
│   - tbleaiou_iid_providers                                       │
│   - tbleaiou_iid_actions                                         │
│   - tbleaiou_iid_action_inputs                                   │
│   - tbleaiou_manuscript_snapshots (extends existing)             │
└─────────────────────────────────────────────────────────────────┘
                              ↓ outbound
┌─────────────────────────────────────────────────────────────────┐
│  External IID provider APIs                                      │
│   - api.anthropic.com (Mae)                                      │
│   - api.openai.com (later)                                       │
│   - others via custom-adapter pattern                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Database schema (migration_008_iid_workflow.sql)

```sql
-- IID providers configured per author
CREATE TABLE tbleaiou_iid_providers (
    provider_id CHAR(36) PRIMARY KEY,
    user_id CHAR(36) NOT NULL,
    provider_name VARCHAR(64) NOT NULL,         -- 'mae' | 'openai' | 'gemini' | 'custom'
    display_name VARCHAR(128) NOT NULL,
    model_family VARCHAR(64) NOT NULL,           -- 'claude-sonnet-4-6' | 'gpt-4o' | etc.
    api_key_encrypted VARBINARY(512) NOT NULL,
    daily_quota INT NOT NULL DEFAULT 50,
    monthly_dollar_cap INT NOT NULL DEFAULT 5000,  -- cents
    enabled_skus JSON NOT NULL,                   -- ['scope_check','journal_select',...]
    custom_endpoint_url TEXT,                     -- only for 'custom' provider_name
    custom_auth_method VARCHAR(32),               -- 'bearer' | 'hmac' | 'mtls'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP NULL,
    disabled_at TIMESTAMP NULL,
    INDEX idx_user (user_id),
    INDEX idx_provider (provider_name)
);

-- IID action invocations
CREATE TABLE tbleaiou_iid_actions (
    action_id CHAR(36) PRIMARY KEY,
    user_id CHAR(36) NOT NULL,
    manuscript_id CHAR(36) NOT NULL,
    manuscript_version INT NOT NULL,             -- snapshot version at invocation time
    provider_id CHAR(36) NOT NULL,
    sku VARCHAR(64) NOT NULL,
    intellid_id CHAR(36),                         -- FK to tblintellids
    cosmoid VARCHAR(128),                         -- the manuscript's CosmoID
    status VARCHAR(32) NOT NULL,                  -- 'pending' | 'running' | 'completed' | 'error' | 'cancelled'
    inputs_json LONGTEXT NOT NULL,                -- {abstract, claimed_venue, etc.}
    result_json LONGTEXT,                         -- {in_scope, confidence, reasoning, ...}
    error_message TEXT,
    latency_ms INT,
    cost_cents INT NOT NULL,
    billing_path VARCHAR(32) NOT NULL,            -- 'subscription_credit' | 'stripe_meter' | 'partner_key'
    stripe_meter_event_id VARCHAR(128),
    idempotency_key VARCHAR(128),
    served_by_host VARCHAR(64),
    stub BOOLEAN NOT NULL DEFAULT FALSE,
    superseded_by CHAR(36) NULL,
    redacted_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    INDEX idx_user (user_id),
    INDEX idx_manuscript (manuscript_id),
    INDEX idx_provider (provider_id),
    INDEX idx_idempotency (idempotency_key),
    INDEX idx_intellid (intellid_id),
    FOREIGN KEY (provider_id) REFERENCES tbleaiou_iid_providers(provider_id)
);

-- Source-text inputs separated from action row to keep main row indexable
-- (large abstracts/sections can be 10KB+; LONGTEXT in inline row is fine but
-- separating allows batch operations on action metadata without pulling bodies)
CREATE TABLE tbleaiou_iid_action_inputs (
    action_id CHAR(36) PRIMARY KEY,
    source_text_hash CHAR(64) NOT NULL,           -- SHA-256 of source for de-dup
    source_text LONGTEXT NOT NULL,
    source_section VARCHAR(64),                   -- 'Abstract' | 'Methods' | etc.
    source_section_anchor VARCHAR(64),
    INDEX idx_source_hash (source_text_hash),
    FOREIGN KEY (action_id) REFERENCES tbleaiou_iid_actions(action_id) ON DELETE CASCADE
);

-- Manuscript snapshots for version-binding outputs
-- (extends existing snapshot pattern if any; or net-new)
CREATE TABLE tbleaiou_manuscript_snapshots (
    snapshot_id CHAR(36) PRIMARY KEY,
    manuscript_id CHAR(36) NOT NULL,
    version INT NOT NULL,
    content_hash CHAR(64) NOT NULL,
    content LONGTEXT NOT NULL,                    -- full markdown
    sections_json LONGTEXT,                       -- structure metadata
    reason VARCHAR(32) NOT NULL,                  -- 'manual' | 'iid_action' | 'autosave' | 'edit_threshold'
    user_label VARCHAR(255) NULL,
    created_by CHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_manuscript_version (manuscript_id, version),
    INDEX idx_manuscript_created (manuscript_id, created_at)
);
```

---

## 4. Provider registry pattern

The provider registry is the load-bearing extension point. New IID providers (Mae, OpenAI, Gemini, custom) plug in via this pattern.

### `app/services/iid_providers/__init__.py`

```python
"""
IID provider registry.

Each provider is a module exposing:
  - PROVIDER_NAME: str
  - SUPPORTED_MODELS: list[str]
  - default_model() -> str
  - call(action_sku, inputs, manuscript_context, intellid_record) -> ProviderResponse

Providers are NEVER chained. Each call is independent.
The dispatcher selects ONE provider per action.
"""
from typing import Protocol, Any
from dataclasses import dataclass

@dataclass
class ProviderResponse:
    result: dict[str, Any]
    latency_ms: int
    raw_provider_response: dict | None  # for audit logging only
    instance_hash: str                    # sealed session fingerprint
    model_used: str

class Provider(Protocol):
    PROVIDER_NAME: str
    SUPPORTED_MODELS: list[str]
    
    def default_model(self) -> str: ...
    def call(
        self,
        action_sku: str,
        inputs: dict,
        manuscript_context: dict | None,
        api_key: str,
        model: str | None = None,
    ) -> ProviderResponse: ...

PROVIDERS: dict[str, Provider] = {}

def register_provider(provider: Provider):
    PROVIDERS[provider.PROVIDER_NAME] = provider

def get_provider(name: str) -> Provider:
    if name not in PROVIDERS:
        raise ValueError(f"unknown IID provider: {name}")
    return PROVIDERS[name]

def list_providers() -> list[str]:
    return list(PROVIDERS.keys())
```

### `app/services/iid_providers/anthropic.py` (Mae)

```python
"""
Mae adapter — Anthropic Claude API.

Calls api.anthropic.com using the `anthropic` Python SDK.
Sealed instance_hash = SHA-256 of (api_key, model, day-bucket).
"""
import hashlib
from datetime import datetime, timezone
from anthropic import Anthropic
from . import register_provider, ProviderResponse
from ..iid_handlers import dispatch as handler_dispatch

PROVIDER_NAME = "mae"
SUPPORTED_MODELS = [
    "claude-sonnet-4-6",
    "claude-opus-4-7",
    "claude-haiku-4-5-20251001",
]

def default_model() -> str:
    return "claude-sonnet-4-6"

def _instance_hash(api_key: str, model: str) -> str:
    """Sealed session fingerprint — never reveals raw API key."""
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    raw = f"{api_key}|{model}|{day}".encode()
    return hashlib.sha256(raw).hexdigest()[:16]

def call(
    action_sku: str,
    inputs: dict,
    manuscript_context: dict | None,
    api_key: str,
    model: str | None = None,
) -> ProviderResponse:
    model = model or default_model()
    client = Anthropic(api_key=api_key)
    
    prompt_spec = handler_dispatch(action_sku, inputs, manuscript_context)
    
    start = datetime.now(timezone.utc)
    response = client.messages.create(
        model=model,
        max_tokens=prompt_spec["max_tokens"],
        system=prompt_spec["system"],
        messages=prompt_spec["messages"],
    )
    elapsed_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
    
    parsed_result = prompt_spec["parse_response"](response)
    
    return ProviderResponse(
        result=parsed_result,
        latency_ms=elapsed_ms,
        raw_provider_response={
            "id": response.id,
            "model": response.model,
            "stop_reason": response.stop_reason,
            "usage": response.usage.model_dump() if response.usage else None,
        },
        instance_hash=_instance_hash(api_key, model),
        model_used=response.model,
    )

# Self-register on import
import sys
register_provider(sys.modules[__name__])
```

### `app/services/iid_providers/openai.py` (placeholder)

```python
"""
OpenAI adapter — placeholder.

When wired, this will live alongside Mae adapter, NEVER chained.
The dispatcher selects between providers per the user's per-action choice.

For now this raises NotImplementedError on call() so any code path that
hits it without explicit author opt-in fails loudly rather than silently.
"""
from . import register_provider, ProviderResponse

PROVIDER_NAME = "openai"
SUPPORTED_MODELS = ["gpt-4o", "gpt-4-turbo", "o1-preview"]

def default_model() -> str:
    return "gpt-4o"

def call(action_sku, inputs, manuscript_context, api_key, model=None):
    raise NotImplementedError(
        "OpenAI provider not yet wired. "
        "Mae (Anthropic) is the only active IID provider as of 2026-05-01. "
        "OpenAI ships as a separate module — see UXPILOT_AUTHORING_02_iid_sidebar.md "
        "for the planned UI; this file is a placeholder so the registry knows "
        "the slot exists."
    )

import sys
register_provider(sys.modules[__name__])
```

### `app/services/iid_providers/custom.py` (advanced)

```python
"""
Custom IID provider adapter — generic HTTP for self-hosted or third-party IIDs.

Used by authors who point eaiou at their own LLM endpoint or a non-mainstream
provider. Requires the user to supply:
  - endpoint URL (HTTPS only)
  - auth method (bearer / hmac / mtls)
  - request shape mapping (eaiou wraps action SKUs to provider's native API)
  - response disclosure schema (provider must return provider_name + model_family + instance_hash)
"""
import hashlib
import httpx
from datetime import datetime, timezone
from . import register_provider, ProviderResponse

PROVIDER_NAME = "custom"
SUPPORTED_MODELS = []  # determined at registration time, per-instance

def default_model() -> str:
    return "custom"

def call(
    action_sku, inputs, manuscript_context, api_key, model=None,
    custom_endpoint_url: str = None,
    custom_auth_method: str = "bearer",
):
    if not custom_endpoint_url:
        raise ValueError("custom provider requires custom_endpoint_url")
    
    headers = {}
    if custom_auth_method == "bearer":
        headers["Authorization"] = f"Bearer {api_key}"
    # HMAC and mTLS handled in real impl
    
    payload = {
        "action_sku": action_sku,
        "inputs": inputs,
        "manuscript_context": manuscript_context,
    }
    
    start = datetime.now(timezone.utc)
    with httpx.Client(timeout=300.0) as client:
        resp = client.post(custom_endpoint_url, headers=headers, json=payload)
        resp.raise_for_status()
    elapsed_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
    
    body = resp.json()
    # Verify disclosure presence — per ToS doctrine, custom IIDs must self-disclose
    required_fields = ["provider_name", "model_family", "instance_hash"]
    for f in required_fields:
        if f not in body.get("disclosure", {}):
            raise ValueError(
                f"custom IID response missing disclosure.{f} — "
                "violates SAID-framework requirement"
            )
    
    return ProviderResponse(
        result=body["result"],
        latency_ms=elapsed_ms,
        raw_provider_response=body,
        instance_hash=body["disclosure"]["instance_hash"],
        model_used=body["disclosure"]["model_family"],
    )

import sys
register_provider(sys.modules[__name__])
```

---

## 5. Action handlers (the prompt + parse layer)

Each action SKU has a handler module that:
1. Receives the `inputs` dict from the API request
2. Composes a structured prompt for the IID provider
3. Specifies how to parse the provider's response into a structured result

### `app/services/iid_handlers/__init__.py`

```python
"""Handler registry — one module per action SKU."""
from typing import Callable, Any

HANDLERS: dict[str, Callable] = {}

def register(sku: str):
    def deco(handler_fn):
        HANDLERS[sku] = handler_fn
        return handler_fn
    return deco

def dispatch(sku: str, inputs: dict, manuscript_context: dict | None = None) -> dict:
    """
    Returns prompt_spec dict:
      {
        'system': str,
        'messages': list[dict],
        'max_tokens': int,
        'parse_response': callable(response) -> dict,
      }
    """
    if sku not in HANDLERS:
        return _stub_handler(sku, inputs, manuscript_context)
    return HANDLERS[sku](inputs, manuscript_context)

def _stub_handler(sku, inputs, manuscript_context):
    """Stub for SKUs not yet implemented — Phase 0 fallback."""
    return {
        "system": f"You are a stub for {sku}. Return a placeholder result.",
        "messages": [{"role": "user", "content": "stub"}],
        "max_tokens": 100,
        "parse_response": lambda response: {
            "stub": True,
            "sku": sku,
            "reasoning": f"stub for {sku} — real handler ships Phase 1",
        },
    }
```

### Example handler: `app/services/iid_handlers/scope_check.py`

```python
"""scope_check — is the manuscript in scope for the claimed venue?"""
from . import register
import json
import re

@register("scope_check")
def handle(inputs: dict, manuscript_context: dict | None) -> dict:
    abstract = inputs["abstract"]
    claimed_venue = inputs.get("claimed_venue", "(unspecified)")
    
    system = """You are a peer-review scope-check assistant. Given a manuscript abstract and a claimed target venue, assess whether the manuscript is in scope.

Return your answer as JSON with keys:
  - in_scope: boolean
  - confidence: float in [0, 1]
  - reasoning: 1-2 paragraph explanation
  - similar_papers: list of strings (DOI placeholders if you reference any)

Be honest. If you cannot determine scope without more information, say so in reasoning and set confidence low."""
    
    user_prompt = f"""Abstract:
\"\"\"
{abstract}
\"\"\"

Claimed target venue: {claimed_venue}

Is this in scope?"""
    
    def parse_response(response):
        text = response.content[0].text if response.content else ""
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if not m:
            return {
                "in_scope": None,
                "confidence": 0.0,
                "reasoning": "Provider returned non-JSON output. Raw text: " + text[:500],
                "similar_papers": [],
                "parse_warning": True,
            }
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError as e:
            return {
                "in_scope": None,
                "confidence": 0.0,
                "reasoning": f"JSON parse failed: {e}. Raw text: {text[:500]}",
                "similar_papers": [],
                "parse_warning": True,
            }
    
    return {
        "system": system,
        "messages": [{"role": "user", "content": user_prompt}],
        "max_tokens": 1024,
        "parse_response": parse_response,
    }
```

Each other handler (`journal_select`, `clarity_check`, `methods_check`, etc.) follows the same pattern: describe the task in `system`, format the input as `messages`, specify how to parse the structured response.

**For Phase 2** (when corpus indexing is available), handlers like `scope_check` and `journal_select` add a corpus-retrieval step — they query Qdrant for similar papers and include the retrieved DOIs/abstracts in the prompt as context. That changes the handler internals but not the API contract.

---

## 6. The dispatcher: tying it together

### `app/services/iid_dispatcher.py`

```python
"""IID action dispatcher — single entry point for all IID action invocations."""
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from . import iid_providers, iid_handlers
from .intellid import get_or_create_intellid
from ..models.iid_action import IIDAction, IIDProvider, IIDActionInput

class QuotaExceeded(Exception):
    pass

class CostCapExceeded(Exception):
    pass

class ProviderUnavailable(Exception):
    pass

def invoke_action(
    db: Session,
    user_id: str,
    manuscript_id: str,
    provider_id: str,
    sku: str,
    inputs: dict,
    idempotency_key: str | None = None,
    source_section: str | None = None,
) -> IIDAction:
    # 1. Idempotency check
    if idempotency_key:
        existing = (db.query(IIDAction)
                    .filter_by(user_id=user_id, idempotency_key=idempotency_key)
                    .first())
        if existing:
            return existing
    
    # 2. Provider lookup + quota check
    provider_row = db.query(IIDProvider).filter_by(provider_id=provider_id, user_id=user_id).first()
    if not provider_row:
        raise ValueError(f"provider {provider_id} not configured for user")
    if provider_row.disabled_at:
        raise ProviderUnavailable("provider disabled by user")
    _check_quota(db, provider_row)
    _check_cost_cap(db, provider_row)
    
    # 3. Manuscript snapshot lookup (or create)
    manuscript_version = _ensure_snapshot_for_action(db, manuscript_id, user_id)
    
    # 4. Action row inserted as 'pending'
    action_id = str(uuid.uuid4())
    cost_cents, billing_path = _resolve_billing(db, user_id, sku)
    
    action = IIDAction(
        action_id=action_id,
        user_id=user_id,
        manuscript_id=manuscript_id,
        manuscript_version=manuscript_version,
        provider_id=provider_id,
        sku=sku,
        status="running",
        inputs_json=inputs,
        cost_cents=cost_cents,
        billing_path=billing_path,
        idempotency_key=idempotency_key,
        served_by_host=_get_hostname(),
        stub=_is_stub_handler(sku),
    )
    db.add(action)
    db.add(IIDActionInput(
        action_id=action_id,
        source_text=inputs.get("abstract") or inputs.get("section_text") or str(inputs)[:65000],
        source_text_hash=_sha256(inputs.get("abstract") or str(inputs)),
        source_section=source_section,
    ))
    db.commit()
    
    # 5. Invoke provider
    try:
        provider = iid_providers.get_provider(provider_row.provider_name)
        api_key = _decrypt_api_key(provider_row.api_key_encrypted)
        manuscript_context = _build_manuscript_context(db, manuscript_id, manuscript_version)
        
        response = provider.call(
            action_sku=sku,
            inputs=inputs,
            manuscript_context=manuscript_context,
            api_key=api_key,
            model=provider_row.model_family,
        )
        
        # 6. IntelliId record (sealed instance_hash)
        intellid = get_or_create_intellid(
            db,
            provider_name=provider_row.provider_name,
            model_family=provider_row.model_family,
            instance_hash=response.instance_hash,
            cosmoid=manuscript_context.get("cosmoid"),
        )
        
        # 7. Persist result
        action.status = "completed"
        action.result_json = response.result
        action.latency_ms = response.latency_ms
        action.intellid_id = intellid.intellid_id
        action.completed_at = datetime.now(timezone.utc)
        
        # 8. Bill (subscription credit deduction or Stripe meter event)
        _record_billing(db, action, billing_path)
        
        db.commit()
        return action
    
    except Exception as exc:
        action.status = "error"
        action.error_message = str(exc)
        action.completed_at = datetime.now(timezone.utc)
        db.commit()
        raise

def invoke_parallel(
    db: Session,
    user_id: str,
    manuscript_id: str,
    provider_ids: list[str],
    sku: str,
    inputs: dict,
    idempotency_keys: list[str] | None = None,
) -> list[IIDAction]:
    """Run the same SKU against multiple providers in parallel.
    
    CRITICAL: each provider gets the IDENTICAL inputs. No chaining.
    Each runs in its own thread/coroutine; results are collected and returned.
    """
    import concurrent.futures
    
    if idempotency_keys is None:
        idempotency_keys = [str(uuid.uuid4()) for _ in provider_ids]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(provider_ids), 5)) as pool:
        futures = [
            pool.submit(
                invoke_action,
                db, user_id, manuscript_id, pid, sku, inputs,
                idempotency_key=ik,
            )
            for pid, ik in zip(provider_ids, idempotency_keys)
        ]
        results = []
        for f in concurrent.futures.as_completed(futures):
            try:
                results.append(f.result())
            except Exception as e:
                results.append(_make_error_action(e))
        return results

# helper functions: _check_quota, _check_cost_cap, _resolve_billing, _record_billing,
# _is_stub_handler, _ensure_snapshot_for_action, _build_manuscript_context,
# _decrypt_api_key, _sha256, _get_hostname, _make_error_action
# — implementations omitted here for brevity; standard patterns
```

---

## 7. Router endpoints

### `app/routers/api_iid.py` (new file)

```python
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from ..deps import get_db, get_current_user
from ..services.iid_dispatcher import invoke_action, invoke_parallel, QuotaExceeded, ProviderUnavailable
from ..models.iid_action import IIDActionRequest, IIDActionResponse, IIDProviderResponse

router = APIRouter(prefix="/api/v1/iid", tags=["iid"])

@router.post("/actions", response_model=IIDActionResponse)
async def create_action(
    request: IIDActionRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    try:
        action = invoke_action(
            db, user.user_id, request.manuscript_id,
            request.provider_id, request.sku, request.inputs,
            idempotency_key=idempotency_key,
            source_section=request.source_section,
        )
        return IIDActionResponse.from_orm(action)
    except QuotaExceeded as e:
        raise HTTPException(status_code=402, detail=f"quota exceeded: {e}")
    except ProviderUnavailable as e:
        raise HTTPException(status_code=503, detail=f"provider unavailable: {e}")

@router.post("/actions/multi", response_model=list[IIDActionResponse])
async def create_multi_action(
    request: dict,  # provider_ids list, single sku, single inputs
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    actions = invoke_parallel(
        db, user.user_id,
        request["manuscript_id"],
        request["provider_ids"],
        request["sku"],
        request["inputs"],
    )
    return [IIDActionResponse.from_orm(a) for a in actions]

@router.get("/actions/{action_id}", response_model=IIDActionResponse)
async def get_action(action_id: str, db: Session = Depends(get_db), user = Depends(get_current_user)):
    action = db.query(IIDAction).filter_by(action_id=action_id, user_id=user.user_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="action not found")
    return IIDActionResponse.from_orm(action)

# ... GET /providers, POST /providers, PATCH /providers/{id}, DELETE /providers/{id},
# GET /outputs/{manuscript_id} — straightforward CRUD on tbleaiou_iid_providers
```

---

## 8. Frontend integration points

The browser-side JS calls these endpoints. UI behavior per `UXPILOT_AUTHORING_*.md`:

### When author clicks "Run scope_check with Mae" in the sidebar

```javascript
// app/static/js/iid_actions.js (new)

async function runIIDAction(providerId, sku, inputs, sourceSection) {
    const idempotencyKey = generateUUID();
    showRunningState(providerId, sku);
    
    try {
        const response = await fetch('/api/v1/iid/actions', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${eaiouAuthToken}`,
                'Content-Type': 'application/json',
                'Idempotency-Key': idempotencyKey,
            },
            body: JSON.stringify({
                manuscript_id: currentManuscriptId,
                provider_id: providerId,
                sku: sku,
                inputs: inputs,
                source_section: sourceSection,
            }),
        });
        if (!response.ok) {
            const err = await response.json();
            showErrorState(providerId, err.detail);
            return;
        }
        const action = await response.json();
        renderOutputCard(action);  // appends to output panel
        updateProviderStatus(providerId, 'complete');
    } catch (err) {
        showErrorState(providerId, err.message);
    }
}

async function runIIDActionMulti(providerIds, sku, inputs, sourceSection) {
    showRunningStateMulti(providerIds, sku);
    const response = await fetch('/api/v1/iid/actions/multi', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${eaiouAuthToken}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            manuscript_id: currentManuscriptId,
            provider_ids: providerIds,
            sku: sku,
            inputs: inputs,
        }),
    });
    const actions = await response.json();
    renderOutputCardMulti(actions);  // side-by-side comparison card
}
```

### Output card rendering (per UXPILOT_AUTHORING_03)

```javascript
function renderOutputCard(action) {
    const card = document.createElement('div');
    card.classList.add('iid-output-card');
    card.classList.add(`iid-provider-${action.provider_name}`);  // colors via CSS class
    
    card.innerHTML = `
        <div class="header">
            <span class="provider-chip">${action.provider_display_name}</span>
            <span class="action-label">${action.sku} on ${action.source_section ?? 'full manuscript'}</span>
            <span class="time">${formatRelativeTime(action.completed_at)}</span>
        </div>
        <div class="source-text-block" data-collapsible>
            ${escapeHtml(truncate(action.inputs_json.abstract ?? action.inputs_json.section_text, 500))}
        </div>
        <div class="result-body">
            ${renderResultBody(action.result_json)}
        </div>
        <div class="disclosure-block">
            ${action.provider_name} · ${action.model_family} · inst ${action.instance_hash}
            <a href="#" data-action="expand-disclosure">View full disclosure</a>
        </div>
        <div class="cost-record">
            $${(action.cost_cents / 100).toFixed(2)} via ${action.billing_path}
        </div>
        <div class="actions">
            <button data-action="copy">Copy</button>
            <button data-action="insert-as-comment">Insert as comment</button>
            <button data-action="hide">Hide</button>
            <button data-action="rerun" data-action-id="${action.action_id}">Re-run</button>
            <button data-action="add-iid" data-sku="${action.sku}">+IID</button>
        </div>
    `;
    document.querySelector('#output-panel').prepend(card);
    animateSlideIn(card);
}
```

---

## 9. Migration path from existing eaiou code

The existing eaiou app already has `app/services/intellid.py` and `app/services/api_log.py`. The new authoring workflow:

1. **Reuses** `intellid.py` for the IntelliId records (sealed session fingerprints, CosmoID binding)
2. **Reuses** `api_log.py` for audit logging
3. **Reuses** `app/routers/api_review.py` patterns (already has the structure for review endpoints)
4. **Adds** new tables via `migration_008_iid_workflow.sql`
5. **Adds** new router `api_iid.py` registered in `app/main.py`
6. **Adds** new services dir `app/services/iid_providers/` and `app/services/iid_handlers/`
7. **Adds** new models in `app/models/iid_action.py` and `app/models/iid_provider.py`

Existing eaiou tests (`tests/`) get extended with:
- `tests/test_iid_dispatcher.py` — dispatcher logic, idempotency, quota
- `tests/test_iid_providers/test_anthropic.py` — Mae adapter against Anthropic test API
- `tests/test_iid_handlers/test_scope_check.py` — handler returns structured prompts
- `tests/test_api_iid.py` — router happy-path + auth

---

## 10. Deployment

The new code deploys via the existing eaiou deployment path:

1. `git push origin main` from local
2. SSH to droplet, `cd /home/mae/eaiou`, `git pull`
3. `source .venv/bin/activate && pip install -r requirements.txt` (adds anthropic SDK if not already)
4. Apply migration: `mariadb -u eaiou eaiou < schema/migration_008_iid_workflow.sql`
5. `systemctl restart eaiou`
6. Smoke test: `curl https://eaiou.org/api/v1/iid/providers` (returns empty list for fresh user)

No new daemons; no new ports; nginx config unchanged. The IID workflow lives within the existing eaiou FastAPI process.

---

## 11. ToS-compliance enforcement (structural)

The architecture makes IID-chaining structurally impossible at multiple layers:

1. **Dispatcher only takes ONE `provider_id` per `invoke_action` call.** Cannot pass an output's text as input to another provider via this endpoint.
2. **Output records are immutable.** Once written, no code path mutates the `result_json`. Re-runs produce new rows with `superseded_by` references — never edits the original.
3. **Multi-provider parallel runs receive identical inputs.** The `invoke_parallel` function takes `inputs` once and passes them to all providers; no provider sees another provider's output as input.
4. **Per-provider quotas + cost caps + API keys.** The `tbleaiou_iid_providers` table separates each provider's auth and limits; no shared pool means no cross-pollination.
5. **Disclosure validation.** The custom-provider adapter REJECTS responses missing `provider_name + model_family + instance_hash`. Standard adapters always emit these.
6. **Author-driven invocation only.** No background daemons, no scheduled actions, no agent loops. Every action is initiated by an authenticated user request.

The `tbleaiou_iid_actions` table's audit log makes any violation forensically discoverable: every action shows who initiated it, against which provider, with what input, returning what output. Cross-action chains would show up as anomalous patterns and could be flagged.

---

## 12. Cost accounting

Each action records `cost_cents` and `billing_path`:

- `subscription_credit` — author's tier provides this SKU as part of monthly allotment; deducts from `tbleaiou_subscription_credits.remaining_count`
- `stripe_meter` — overage billing; fires a Stripe meter event with the SKU as the meter name
- `partner_key` — B2B partner-key call; records the partner_key_id; billed via partner-rate invoice (separate from subscription)

The Stripe Tax integration handles VAT/sales tax automatically based on customer billing address.

Anthropic API cost (Claude Sonnet 4.6 example):
- Input: ~$3 per million tokens
- Output: ~$15 per million tokens
- Typical scope_check: ~5K input + 1K output ≈ $0.015 + $0.015 = $0.03
- $0.07 retail / $0.04 net margin per scope_check (after Stripe fees ~3%)

---

## 13. What's deferred

These are explicit out-of-scope for the MVP:

- Streaming responses from IIDs (current: complete-response polling)
- Partial / progressive output rendering
- Real-time collaboration (multiple authors on one manuscript simultaneously)
- WebSocket-based action notifications (current: poll via GET /actions/{id})
- A/B testing different prompts per handler (out of MVP)
- Fine-tuned models (uses base models only)
- Self-hosted Llama via Ollama / vLLM (use the `custom` adapter to point at it)

These are tracked in the broader `manusights_competitor_mvp_plan.md` Phase 4+.
