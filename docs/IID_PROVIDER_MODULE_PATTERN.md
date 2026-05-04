# eaiou IID Provider Module Pattern — How to Add a New Provider

**Date:** 2026-05-01
**Author:** Eric D. Martin
**Purpose:** Step-by-step guide for adding a new IID provider (e.g., OpenAI, Gemini, custom self-hosted) as a module to eaiou alongside the existing Mae (Anthropic) module.

---

## 1. The pattern in one sentence

Every IID provider is a Python module under `app/services/iid_providers/` that exports a `PROVIDER_NAME` string, a `SUPPORTED_MODELS` list, a `default_model()` function, and a `call(action_sku, inputs, manuscript_context, api_key, model)` function returning a `ProviderResponse` dataclass — and self-registers via `register_provider(sys.modules[__name__])` at module load time.

---

## 2. Files to create per new provider

For a hypothetical "OpenAI" provider:

```
app/services/iid_providers/
├── __init__.py             (existing — registry; do not modify)
├── anthropic.py            (existing — Mae)
├── openai.py               ← NEW
└── ...

tests/test_iid_providers/
├── test_anthropic.py       (existing)
└── test_openai.py          ← NEW

requirements.txt            ← add: openai>=1.0.0
```

That's it. Three files, plus one line in `requirements.txt`.

---

## 3. Provider module template

Save as `app/services/iid_providers/openai.py`:

```python
"""
OpenAI IID provider adapter.

Calls api.openai.com via the openai Python SDK.
NEVER receives outputs from other providers (no chaining).
Self-registers on import.
"""
import hashlib
import os
import sys
from datetime import datetime, timezone
from openai import OpenAI

from . import register_provider, ProviderResponse
from ..iid_handlers import dispatch as handler_dispatch

# === Required exports ===

PROVIDER_NAME = "openai"
SUPPORTED_MODELS = [
    "gpt-4o",
    "gpt-4-turbo",
    "gpt-4o-mini",
    "o1-preview",
    "o1-mini",
]

def default_model() -> str:
    return "gpt-4o"

def call(
    action_sku: str,
    inputs: dict,
    manuscript_context: dict | None,
    api_key: str,
    model: str | None = None,
) -> ProviderResponse:
    """Invoke OpenAI for the given action SKU.
    
    Args:
        action_sku: e.g., 'scope_check', 'journal_select'
        inputs: dict from the API request (manuscript abstract, etc.)
        manuscript_context: optional metadata about the manuscript
        api_key: OpenAI API key (decrypted by the dispatcher just before call)
        model: optional model override; falls back to default_model()
    
    Returns:
        ProviderResponse with result, latency_ms, raw_provider_response,
        instance_hash (sealed session fingerprint), model_used.
    
    Raises:
        Various openai SDK exceptions on API failure.
        ValueError if action_sku has no registered handler.
    """
    model = model or default_model()
    client = OpenAI(api_key=api_key)
    
    # Get the prompt-spec for this action SKU
    prompt_spec = handler_dispatch(action_sku, inputs, manuscript_context)
    
    # Translate from Anthropic-style messages to OpenAI-style messages
    # (handlers are Anthropic-shaped because Mae was the first provider; OpenAI
    # adapter normalizes here)
    openai_messages = []
    if prompt_spec.get("system"):
        openai_messages.append({"role": "system", "content": prompt_spec["system"]})
    openai_messages.extend(prompt_spec["messages"])
    
    start = datetime.now(timezone.utc)
    response = client.chat.completions.create(
        model=model,
        max_tokens=prompt_spec["max_tokens"],
        messages=openai_messages,
    )
    elapsed_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
    
    # Parse via the handler's parse_response function
    parsed_result = prompt_spec["parse_response"](response)
    
    return ProviderResponse(
        result=parsed_result,
        latency_ms=elapsed_ms,
        raw_provider_response={
            "id": response.id,
            "model": response.model,
            "finish_reason": response.choices[0].finish_reason if response.choices else None,
            "usage": response.usage.model_dump() if response.usage else None,
        },
        instance_hash=_instance_hash(api_key, model),
        model_used=response.model,
    )

# === Internal helpers ===

def _instance_hash(api_key: str, model: str) -> str:
    """Sealed session fingerprint per SAID framework — never reveals raw API key."""
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    raw = f"{api_key}|{model}|{day}".encode()
    return hashlib.sha256(raw).hexdigest()[:16]

# === Self-registration ===
register_provider(sys.modules[__name__])
```

---

## 4. Why each piece exists

### `PROVIDER_NAME`

A string identifier used in:
- `tbleaiou_iid_providers.provider_name` column
- Authentication: per-provider API keys are stored under this name
- Dispatcher: `iid_providers.get_provider("openai")` returns this module
- UI: the provider chip shown to authors

**Convention:** lowercase, alphanumeric + underscores, ≤ 32 chars.

### `SUPPORTED_MODELS`

A list of model identifiers this provider supports. Used to:
- Validate `model` parameter in `call()`
- Populate the model-selection dropdown in the registry UI
- Determine pricing tables (each model has its own per-token cost)

**Convention:** the actual model identifiers the provider's API accepts. Don't lowercase or reformat — pass through verbatim.

### `default_model() -> str`

Returns the model used when the author hasn't specified one. Should return:
- A reasonable balance of quality, cost, and latency
- A model that supports all the actions this provider exposes

For Mae: `claude-sonnet-4-6` is a good default (faster than Opus, more capable than Haiku).
For OpenAI: `gpt-4o` is the standard balance.

### `call(action_sku, inputs, manuscript_context, api_key, model)`

The main entry point. The dispatcher calls this exactly once per IID action:

- `action_sku` — the SKU the author invoked (e.g., `scope_check`)
- `inputs` — the JSON payload from the API request body
- `manuscript_context` — optional manuscript-level metadata (cosmoid, title, authors, target venue)
- `api_key` — already decrypted; never logged; passed through to the provider's SDK only
- `model` — optional override; if `None`, use `default_model()`

The function:
1. Calls `iid_handlers.dispatch(action_sku, ...)` to get the prompt-spec
2. Translates the spec into the provider's native API call format (system prompt, messages, max_tokens)
3. Makes the API call
4. Parses the response via `prompt_spec["parse_response"]`
5. Returns a `ProviderResponse` dataclass

### `ProviderResponse`

A simple dataclass defined in `app/services/iid_providers/__init__.py`:

```python
@dataclass
class ProviderResponse:
    result: dict[str, Any]              # parsed structured result for the user
    latency_ms: int                      # how long the API call took
    raw_provider_response: dict | None   # for audit log; never shown to user
    instance_hash: str                   # sealed session fingerprint
    model_used: str                      # actual model the provider used
```

The dispatcher persists all of these in the action record; the UI shows `result`, `instance_hash`, `model_used`, and `latency_ms`. The `raw_provider_response` is admin-only audit material.

### `_instance_hash(api_key, model)`

The sealed session fingerprint per SAID framework. Required pattern:

1. Compute SHA-256 of `(api_key + model + day_bucket)`
2. Take the first 16 hex chars as the fingerprint
3. The fingerprint **changes every day** by design — so old outputs don't suggest recent activity, and so the fingerprint can't be used to track an author's API key longitudinally

Other valid sealing strategies (any one of):
- Include user_id in the hash (per-user-per-day-per-model fingerprint)
- Use HMAC instead of plain SHA (with a server-side secret)
- Truncate to 12 or 24 chars

The minimum requirement: never reveal the raw API key, and never make the fingerprint a stable long-term identifier of the API key alone.

### `register_provider(sys.modules[__name__])`

Self-registration on import. The dispatcher's `iid_providers.get_provider()` resolves the provider by `PROVIDER_NAME` from the registry populated at app startup.

This pattern means: dropping a new file in `app/services/iid_providers/` is sufficient — no manual list updates anywhere else.

---

## 5. Test module template

Save as `tests/test_iid_providers/test_openai.py`:

```python
"""Tests for OpenAI IID provider adapter."""
import pytest
from unittest.mock import patch, MagicMock
from app.services.iid_providers import openai as openai_provider
from app.services.iid_providers import get_provider, list_providers

class TestProviderRegistration:
    def test_registered_on_import(self):
        assert "openai" in list_providers()
    
    def test_supports_models(self):
        assert "gpt-4o" in openai_provider.SUPPORTED_MODELS
        assert openai_provider.default_model() == "gpt-4o"

class TestCall:
    @patch("app.services.iid_providers.openai.OpenAI")
    def test_call_returns_provider_response(self, mock_openai_class):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.id = "chatcmpl-test"
        mock_response.model = "gpt-4o"
        mock_response.choices = [MagicMock(finish_reason="stop")]
        mock_response.choices[0].message.content = '{"in_scope": true, "confidence": 0.85, "reasoning": "test", "similar_papers": []}'
        mock_response.usage = MagicMock()
        mock_response.usage.model_dump.return_value = {"prompt_tokens": 100, "completion_tokens": 50}
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        response = openai_provider.call(
            action_sku="scope_check",
            inputs={"abstract": "test abstract", "claimed_venue": "Journal of Test"},
            manuscript_context=None,
            api_key="sk-test-key",
            model=None,
        )
        
        assert response.model_used == "gpt-4o"
        assert response.instance_hash  # non-empty
        assert response.result.get("in_scope") is True
        assert response.latency_ms > 0
    
    def test_instance_hash_does_not_leak_key(self):
        h = openai_provider._instance_hash("sk-very-secret-key-do-not-leak", "gpt-4o")
        assert "sk-" not in h
        assert "secret" not in h
        assert "do-not-leak" not in h
        assert len(h) == 16
    
    def test_instance_hash_changes_per_day(self):
        # Two calls on the same day should match; ideally change next day
        # (Not directly testable without mocking the date, but verify length and format.)
        h1 = openai_provider._instance_hash("sk-test", "gpt-4o")
        h2 = openai_provider._instance_hash("sk-test", "gpt-4o")
        assert h1 == h2  # within same UTC day
```

---

## 6. Provider-specific gotchas to anticipate

| Provider | Gotcha |
|---|---|
| **Anthropic / Mae** | Messages API requires alternating user/assistant roles; system prompt is separate parameter, not a message |
| **OpenAI** | `response.choices[0].message.content` is the text; `response.id` for tracking; tokens-by-model pricing varies |
| **Gemini (Google)** | Uses google-generativeai SDK; messages style is "parts"; safety filters may auto-block; needs explicit safety_settings to allow scientific content |
| **Llama (self-hosted via Ollama / vLLM)** | OpenAI-compatible API mode is easiest path; use the `openai` Python SDK pointed at `http://localhost:11434/v1` (Ollama) or `http://localhost:8000/v1` (vLLM); use the `custom` provider adapter |
| **Custom HTTP IID** | Must return disclosure block with provider_name + model_family + instance_hash; eaiou rejects responses lacking it |

---

## 7. Adding a new action SKU (orthogonal to provider work)

If you want to add a new action SKU (e.g., `bibliography_check`), the pattern is symmetric:

1. Add a new file `app/services/iid_handlers/bibliography_check.py` with `@register("bibliography_check") def handle(inputs, manuscript_context): ...`
2. Add a row to `tbleaiou_products` (or its equivalent) with the SKU, retail price, wholesale price
3. Update the UI to show the new action button on each provider's card
4. Optional: update each provider's `enabled_skus` JSON to include or exclude the new SKU per provider's preference

The provider modules don't need to know about new SKUs — the handler dispatch happens inside `call()` via `iid_handlers.dispatch()`.

---

## 8. Removing a provider

To remove a provider:

1. Mark all `tbleaiou_iid_providers` rows for that `provider_name` as `disabled_at = NOW()` — preserves audit history
2. Optionally `DELETE FROM tbleaiou_iid_providers WHERE provider_name = X` — destroys configuration but preserves action history (which references provider_id)
3. Remove the file from `app/services/iid_providers/<provider>.py`
4. Remove the row from `requirements.txt` if the provider's SDK is no longer needed
5. Existing `tbleaiou_iid_actions` rows with this provider continue to render (audit-immutable); the UI shows the provider chip with a "(removed)" indicator

---

## 9. Provider isolation invariants (DO NOT VIOLATE)

- **A provider module's `call()` MUST NOT call another provider's `call()`.** Provider-isolation is enforced by code review.
- **A provider's response MUST NOT be passed as input to another provider's `call()`.** The dispatcher takes `inputs` once and uses them. Comparing IID outputs is the user's job, not the system's.
- **Per-provider API keys MUST be encrypted at rest** (`api_key_encrypted` is `VARBINARY(512)` for AES-GCM-encrypted bytes; the encryption key is in eaiou's secrets store, not in the database).
- **Provider modules MUST NOT log raw API keys.** Logging `instance_hash` is fine; logging `api_key` is a security violation.
- **Provider modules MUST NOT perform action SKU dispatch themselves.** Handlers belong in `app/services/iid_handlers/`. Provider modules call `iid_handlers.dispatch()`.

These are doctrine. Code review enforces them.

---

## 10. Roadmap of providers (Mae 2026-05-01 view)

| Provider | Status | Files needed | Estimated build time |
|---|---|---|---|
| **Mae (Anthropic)** | ✅ Wired | `anthropic.py`, tests | DONE |
| **OpenAI** | ⚪ Placeholder | `openai.py`, tests, requirements.txt entry | 1 day |
| **Gemini (Google)** | ⚪ Placeholder | `gemini.py`, tests, requirements.txt entry | 1 day |
| **Llama (self-hosted)** | ⚪ Placeholder | use `custom.py` with OpenAI-compatible mode | half day |
| **Mistral** | ⚪ Future | `mistral.py`, tests | 1 day |
| **Cohere** | ⚪ Future | `cohere.py`, tests | 1 day |
| **Custom (advanced)** | ✅ Wired | `custom.py` | DONE |

The goal is provider-agnostic by architecture. Today only Mae is active; tomorrow OpenAI; next week Gemini. No major rewrites required.
