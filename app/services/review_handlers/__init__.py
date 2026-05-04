"""
Review-handler registry.

Phase 0 of the checksubmit MVP. Each handler module under this package registers
itself for one SKU via the @register decorator. The dispatcher resolves SKU -> handler
at call time. If no handler is registered for a SKU, dispatch returns an honest
{"stub": True, ...} response rather than failing — handlers are pluggable post-deploy.

Compliance:
* No IID chaining: handlers receive raw inputs only; one handler MUST NOT call another
  handler with the first's output. Composed services (full_review) declare composition
  inline in their handler body, calling each component IID independently with the same
  source inputs.
* No background invocation: handlers run synchronously inside the FastAPI request that
  invoked them. No celery, no daemons.
* Disclosure: every handler returns a result that includes provider attribution
  (provider name, model_family, instance_hash). The dispatcher persists these into
  the order row so the disclosure block survives every export.

See: docs/TOS_COMPLIANCE_DOCTRINE.md, manusights_competitor_mvp_plan.md §0.1.
"""

from typing import Callable, Dict, Any

# {sku: handler_callable}
HANDLERS: Dict[str, Callable[[dict, dict], dict]] = {}


def register(sku: str):
    """
    Decorator: register a handler for a SKU.

    Usage:
        @register("scope_check")
        def handle(inputs: dict, ctx: dict) -> dict:
            return {"reasoning": "...", "iid": {...}}
    """
    def deco(fn: Callable[[dict, dict], dict]) -> Callable[[dict, dict], dict]:
        if sku in HANDLERS:
            raise RuntimeError(f"duplicate handler registration for SKU {sku!r}")
        HANDLERS[sku] = fn
        return fn
    return deco


def dispatch(sku: str, inputs: dict, ctx: dict | None = None) -> dict:
    """
    Look up and invoke the handler for `sku`. Falls back to stub response if missing.

    Args:
      sku:    Product SKU (must match eaiou_products.sku).
      inputs: User-provided inputs for the action (e.g. {"manuscript_text": "..."})
      ctx:    Request context — current_user, manuscript_id, partner_key, etc.

    Returns:
      dict with keys:
        - reasoning      (str)  — the human-readable result body
        - iid            (dict) — provider/model/instance_hash for disclosure
        - structured     (dict) — optional structured fields per-SKU
        - stub           (bool) — True if no real handler is wired yet
        - error          (str)  — set if the handler failed
    """
    ctx = ctx or {}
    handler = HANDLERS.get(sku)
    if handler is None:
        return {
            "stub": True,
            "sku": sku,
            "reasoning": (
                f"Stub handler for {sku}. Real review logic ships in Phase 1 of the "
                "checksubmit MVP build. The order has been recorded; once the real "
                "handler is wired, this output card will be replaced with the actual "
                "review."
            ),
            "iid": {
                "provider": "checksubmit",
                "model_family": "stub",
                "instance_hash": "00000000",
            },
        }
    try:
        return handler(inputs, ctx)
    except Exception as exc:
        return {
            "error": str(exc),
            "sku": sku,
            "reasoning": (
                f"Handler {handler.__module__}.{handler.__name__} raised {type(exc).__name__}. "
                "The order has been recorded as failed; no charge applies."
            ),
            "iid": {
                "provider": "checksubmit",
                "model_family": "error",
                "instance_hash": "00000000",
            },
        }


# Import all handler modules so they self-register via @register.
# Adding a new SKU = drop a new file in this package + import it here.
from . import scope_check          # noqa: E402, F401
from . import journal_select       # noqa: E402, F401
from . import outline_check        # noqa: E402, F401
from . import clarity_check        # noqa: E402, F401
from . import methods_check        # noqa: E402, F401
from . import reference_audit      # noqa: E402, F401
from . import full_review          # noqa: E402, F401
from . import premium_review       # noqa: E402, F401
