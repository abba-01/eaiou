# eaiou Phase 1 Audit Report -- 2026-04-17

## Environment
- **MariaDB:** running, 34 tables confirmed in `eaiou` database
- **Python venv:** OK after installing missing deps (pypdf, python-docx)
- **App startup:** clean, 183 routes registered
- **Test data:** 2 papers (id=1 "Test Paper One" submitted, id=2 "AntOp Live Run Test" under_review)

## Route Audit Results

| Route | Status | Notes |
|-------|--------|-------|
| GET / | 200 | Homepage |
| GET /about | 200 | About page |
| GET /papers/ | 200 | Paper listing |
| GET /health | 200 | Health endpoint |
| GET /api/docs | 200 | Swagger UI |
| GET /policy | 200 | Policy index (FIXED: was 404, route added to main.py) |
| GET /policy/temporal-blindness | 200 | Temporal blindness policy |
| GET /policy/ai-disclosure | 200 | AI disclosure policy |
| GET /policy/open-access | 200 | Open access policy |
| GET /policy/intelligence-blindness | 200 | Intelligence blindness policy |
| GET /papers/1 | 200 | Paper detail (integer ID) |
| GET /papers/submitted/1 | 200 | Submission confirmation |
| GET /papers/status/1 | 200 | Status tracking |
| GET /papers/2 | 200 | Paper detail (second test paper) |
| GET /auth/login | 200 | Login page |
| POST /auth/login | 303 | Admin login -> / (FIXED: was 500, middleware bug) |
| GET /auth/logout | 302 | Logout redirect |
| GET /author/ | 200 | Author dashboard |
| GET /author/dashboard | 200 | Author dashboard (alias) |
| GET /author/submit | 200 | Submission form |
| GET /author/drawer | 200 | Drawer component |
| GET /author/notifications | 200 | Author notifications |
| GET /editor/ | 200 | Editor dashboard |
| GET /editor/queue | 200 | Editor queue (FIXED: was 500, missing columns in query) |
| GET /editor/papers/1 | 200 | Editor paper detail |
| GET /editor/papers/1/score/breakdown | 200 | Q score breakdown |
| GET /admin/ | 200 | Admin dashboard |
| GET /admin/users | 200 | Admin user list |
| GET /admin/users/new | 200 | Admin new user form |
| GET /api/v1/papers | 200 | API papers list |
| GET /api/v1/system/health | 200 | API system health |
| GET /api/v1/papers?sort=date | 400 | TB: sort rejected |
| GET /api/v1/papers?sort=created | 400 | TB: sort rejected |
| GET /api/v1/papers?sort=submitted_at | 400 | TB: sort rejected |
| GET /api/v1/papers?sort=q_signal | 200 | TB: sort allowed |
| TB sealed fields | PASS | No sealed fields in public API response |

**Final count: 36 PASS, 0 FAIL**

## Fixes Applied

### Fix 1: TemporalBlindnessMiddleware crash on login (POST /auth/login -> 500)
- **File:** `app/middleware/temporal_blindness.py`
- **Root cause:** `_is_governance()` called `user.get("groups")` but `request.session["user"]` stores a username string, not a dict. The `.get()` call raised `AttributeError: 'str' object has no attribute 'get'`.
- **Fix:** Added type check -- if `user` is a string, return `False` (non-governance). Phase 2 can store a dict with groups when multi-user roles are implemented.

### Fix 2: Missing /policy route (GET /policy -> 404)
- **File:** `app/main.py`
- **Root cause:** Individual policy pages (/policy/temporal-blindness, etc.) had routes, but the parent /policy page did not, despite `templates/policy.html` existing.
- **Fix:** Added `@app.get("/policy")` route pointing to `policy.html`.

### Fix 3: Editor queue crash (GET /editor/queue -> 500)
- **File:** `app/routers/editor.py`
- **Root cause:** The queue query selected `id, paper_uuid, title, abstract, author_name, orcid, ai_disclosure_level` but the template accesses `paper.status`, `paper.cosmoid`, and `paper.q_overall`. Missing columns caused `UndefinedError`.
- **Fix:** Added `cosmoid, status, q_overall` to the SELECT query.

### Fix 4: Missing Python dependencies
- **Packages:** `pypdf`, `python-docx`
- **Root cause:** Listed in requirements.txt but not installed in venv.
- **Fix:** `pip install pypdf python-docx`

## SSOT Verification Checklist

- **Hardcoded hex:** Design token definitions in `base/base.html` and brand SVGs in `auth/login.html` are legitimate; no violations in active templates using the primary design system.
- **Temporal Blindness in templates:** Only documentation references to sealed fields (policy text, comments); no sort violations found.
- **Shell inheritance:** All admin/author/editor templates extend a base template.
- **Color words (text-blue, bg-red, etc.):** None found.

## SSOT Section 9 Corrections

The previous Section 9 ("What Is NOT Built Yet") contained the following incorrect claims:
- "Admin router -- no admin routes wired" -- **FALSE**: `routers/admin.py` is fully implemented with dashboard, user CRUD, group management
- "Editor router -- no editor routes wired" -- **FALSE**: `routers/editor.py` is fully implemented with dashboard, queue, paper detail, status transitions, Q scoring
- "Q scoring logic" listed as not built -- **FALSE**: `services/qscore.py` is fully implemented with 4-dimension weighted scoring
- "The app has not been run live against a real DB" -- **FALSE**: the app runs against MariaDB with 34 tables and 2 test papers

Section 9 was rewritten to accurately reflect the verified build state. Section 8 (Phase Boundaries) was also updated to list Phase 1 as complete with the full feature set. Section 4 (Route Table) was expanded to list all verified routes including admin, editor, author, and API prefixes.

## Phase 2 Items Confirmed Not Started
- Reviewer assignment and matching
- RS: tag ingestion, indexing, and UI
- Discovery routes (HTML frontend -- API endpoints exist)
- Local DB setup script / standalone migration runner
- Multi-user registration flow (Phase 1 is single-admin via .env)
