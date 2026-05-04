"""
Temporal Blindness Middleware — L0 doctrine enforcement
- Sort gate: rejects ?sort= on any date/time/sealed field → HTTP 400
- Sealed field strip: removes sealed temporal fields from all JSON responses
  for callers who are not in the 'governance' group
"""

import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

# Fields stripped from all non-governance JSON responses
_SEALED_FIELDS = frozenset({
    "submission_sealed_at",
    "acceptance_sealed_at",
    "publication_sealed_at",
    "attestation_sealed_at",
    "sealed_by",
    "submission_hash",
})

# Sort values that violate Temporal Blindness
_FORBIDDEN_SORT_KEYS = frozenset({
    "date", "created", "submitted_at", "created_at",
    "modified", "modified_at",
    "submission_sealed_at", "acceptance_sealed_at",
    "publication_sealed_at", "attestation_sealed_at",
})


def _is_governance(request: Request) -> bool:
    """
    Return True if the session user belongs to the 'governance' group.

    H-1 fix (CWO audit 2026-05-02): session stores username as a STRING, not
    a dict. The previous code returned False for every logged-in user — the
    governance unlock was effectively dead. This version does a DB lookup
    when the session has just the username, so governance members actually
    get the unlock.
    """
    user = request.session.get("user")
    if not user:
        return False

    # If session somehow stores a dict (future Phase 2), use it directly.
    if isinstance(user, dict):
        return "governance" in (user.get("groups") or [])

    # Session stores a username string — look up groups in DB.
    if isinstance(user, str):
        try:
            from sqlalchemy import text
            from ..database import SessionLocal
            with SessionLocal() as db:
                rows = db.execute(text("""
                    SELECT g.name FROM `#__eaiou_groups` g
                    JOIN `#__eaiou_user_groups` ug ON ug.group_id = g.id
                    JOIN `#__eaiou_users` u ON u.id = ug.user_id
                    WHERE u.username = :u AND u.active = 1
                """), {"u": user}).mappings().all()
                groups = [r["name"] for r in rows]
                return "governance" in groups
        except Exception:
            # Fail closed: any error in lookup → no governance privilege.
            # This is intentional — an exception here MUST NOT leak sealed
            # fields by accident.
            return False

    return False


def _strip_sealed(obj):
    """Recursively remove sealed fields from dicts/lists."""
    if isinstance(obj, dict):
        return {k: _strip_sealed(v) for k, v in obj.items()
                if k not in _SEALED_FIELDS}
    if isinstance(obj, list):
        return [_strip_sealed(i) for i in obj]
    return obj


class TemporalBlindnessMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Sort gate — runs BEFORE the route handler
        sort_val = request.query_params.get("sort", "").lower().lstrip("-")
        if sort_val and sort_val in _FORBIDDEN_SORT_KEYS:
            return JSONResponse(
                {
                    "error": "sort_forbidden",
                    "detail": (
                        f"Sorting by '{sort_val}' violates the Temporal "
                        "Blindness doctrine. Use q_signal for discovery ordering."
                    ),
                },
                status_code=400,
            )

        response = await call_next(request)

        # 2. Sealed field strip — only for JSON responses, only for non-governance
        if _is_governance(request):
            return response

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            data = json.loads(body)
            cleaned = _strip_sealed(data)
            cleaned_body = json.dumps(cleaned).encode()
        except (json.JSONDecodeError, ValueError):
            cleaned_body = body

        # Drop Content-Length so Response recomputes it from cleaned_body
        clean_headers = {
            k: v for k, v in response.headers.items()
            if k.lower() != "content-length"
        }
        return Response(
            content=cleaned_body,
            status_code=response.status_code,
            headers=clean_headers,
            media_type="application/json",
        )
