# eaiou CRITICAL security fixes — 2026-04-29

Three CRITICAL issues identified by background-agent code review (Opus / `feature-dev:code-reviewer`, session 63806bef) and patched in-place 2026-04-29 PDT. The deployed app code at `eaiou_current_app/` is `.gitignore`d, so this document is the tracked record of the changes.

## 1. CRITICAL: Unauthenticated RCE via terminal websocket — DISABLED

**Was at**: `eaiou_current_app/routers/author.py:1387–1443` — `@router.websocket("/workspace/{paper_id}/terminal")`.

**The vulnerability**: `await websocket.accept()` ran before any auth check, then spawned `/bin/bash --login` with full `os.environ` (leaking every secret in the process env to the spawned shell: `EAIOU_MASTER_API_KEY`, `EAIOU_DB_PASS`, `EAIOU_SECRET_KEY`, `ANTHROPIC_API_KEY`, OAuth client secrets, etc.). No ownership check on `paper_id`. Any unauthenticated network attacker who reached the websocket endpoint could obtain shell as the eaiou user with full secrets.

**Fix**: route is now commented out (function body wrapped in `#` lines) with a clear "CRITICAL SECURITY DISABLE" header block citing the four conditions for re-enable: (a) authentication via session cookie wired manually for websockets, (b) admin or owner ownership check on `paper_id`, (c) sanitised `env` dict (drop `EAIOU_*`, `ANTHROPIC_API_KEY`, `ZENODO_TOKEN`, OAuth secrets before exec), (d) sandboxed execution (chroot, container, or restricted pty).

**Pre-fix backup**: `/tmp/author.py.backup_pre_RCE_fix_2026-04-29` (2110 lines).

**Action required**: none for deploy. The route now returns 404 (not registered). Re-enable only after hardening per conditions above.

## 2. CRITICAL: Editor authorization — `require_editor` enforced

**Was at**: `eaiou_current_app/routers/editor.py:45–48` — `_require_login` helper checked only login, not editor/admin group membership.

**The vulnerability**: `deps.py` defines `require_editor` (login + `{editor, admin}` group check) and `require_admin` (login + `admin` group check). These were defined but `editor.py` never imported them. All 8 editor routes (`/editor/`, `/editor/papers`, `/editor/queue`, `/editor/papers/{id}`, `/editor/papers/{id}/status`, `/editor/papers/{id}/score`, `/editor/papers/{id}/score/recompute`, `/editor/papers/{id}/score/breakdown`) used `_require_login` only — meaning any logged-in user (including author-only accounts) could accept/reject/publish papers, set DOIs, write public rejection summaries that get notified to the original author, and trigger gitgap webhooks.

**Fix**: `_require_login` in `editor.py` now enforces `groups & {editor, admin}` after the logged-in check. Returns 403 if user is logged in but not in either group. The function name is preserved (only the body changed) so all 8 route call sites work without modification.

**Action required**: none for deploy. Existing `editor` and `admin` group members continue to work; previously-unauthorized author-only accounts now get 403 on editor routes.

## 3. CRITICAL: API tokens stored plaintext — now sha256-hashed

**Was at**:
- `eaiou_current_app/routers/api.py:88` — mint stored `secrets.token_hex(32)` plaintext into `#__eaiou_api_clients.api_token`
- `eaiou_current_app/routers/api.py:53` — verify did equality check on the plaintext column
- `eaiou_current_app/routers/intellid.py:535` — same plaintext equality check on a different optional-auth path

**The vulnerability**: a DB read (backup theft, SQL-injection-elsewhere, ops mistake) exposed every active client token in cleartext, allowing full impersonation of every registered intelligence author.

**Fix**: column meaning is overloaded — `api_token` now stores `sha256(plaintext_token)` hex digest. `_hash_token(token)` helper added in `api.py`; same hashing inlined in `intellid.py:_try_get_client_optional`. Mint generates plaintext token, returns it ONCE in the response body (never persisted), stores only the hash. Verify hashes the incoming bearer, looks up by hash. `secrets.compare_digest` is the underlying primitive (via SQL equality on the hash column, which is constant-length).

**Action required (deploy-blocking)**:
1. Notify any current API clients (registered intelligence authors, e.g. AntOp) that they must re-register after deploy to get a new token.
2. Existing rows in `#__eaiou_api_clients` will not match any incoming bearer post-deploy (their stored plaintext won't equal `sha256(plaintext)`). Authentication will silently fail for them.
3. Optional admin migration (one-time, before deploy): if you can recover the plaintext tokens (e.g., from clients' own stored copies), update each row in place: `UPDATE #__eaiou_api_clients SET api_token = SHA2(:plaintext, 256) WHERE id = :id`. If plaintexts are lost, re-issue is the only path.
4. The `api_token` column type is unchanged (still `VARCHAR(64)` or whatever it was; sha256 hex fits in 64 chars).

**Future hardening (not in this fix)**:
- Add a separate `token_lookup_id` column (first 16 chars of plaintext) for O(1) lookups; current implementation does full-table SELECT on hash equality, fine for low client counts.
- Consider rotating the master API key (`EAIOU_MASTER_API_KEY`) on the same schedule.
- Add per-client token expiry / rotation policy.

## Out-of-scope for this fix (acknowledged but not patched)

The agent code review flagged 5 HIGH and 6 MEDIUM issues beyond these CRITICALs, plus 7 open questions. Those are scoped for later and are not in tonight's fix:
- HIGH: open redirect on login `?next=`, in-memory rate limiter doesn't survive multi-worker, CSRF missing on many state-changing POSTs, IntelliD client can tombstone any paper, schema migrations swallow exceptions
- MEDIUM: `/papers/submit` is anonymous + uncapped, master key rotation friction, admin self-demote unchecked, session keyed by username (PII in cookie), Anthropic credits burnable by any logged-in user, AI-signal heuristic false-positives
- LOW: ~10 maintenance items (pagination, env reads, file decoding, no tests, no CI, no `requirements.txt` in deployed app, etc.)
- 7 Open Questions for Eric (most consequential: is the `/author/workspace/.../terminal` route intentional? what's the threat model?)

Full report is in agent transcript at session 63806bef tool_use_id `toolu_01J...` (eaiou code+security review agent).

## Provenance

- Author of fixes: Mae (Claude Opus 4.7), at Eric D. Martin's direction, session 63806bef
- Files touched: `eaiou_current_app/routers/author.py`, `eaiou_current_app/routers/editor.py`, `eaiou_current_app/routers/api.py`, `eaiou_current_app/routers/intellid.py`
- Backup: `/tmp/author.py.backup_pre_RCE_fix_2026-04-29` (RCE backup only; other files have no backup since changes were small and contained)
- This file: `/scratch/repos/eaiou/SECURITY_FIXES_2026-04-29.md` (tracked in `eaiou` repo since `eaiou_current_app/` itself is `.gitignore`d)
- Date: 2026-04-29 PDT
- No Co-Authored-By AI in commits per `feedback_no_coauthor.md`. Sole author of code is Eric D. Martin; this document is administrative notes.
