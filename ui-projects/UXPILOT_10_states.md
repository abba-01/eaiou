# UXPILOT_10 — state catalog & copy library

**Tokens:** see `UXPILOT_00_design_system.md §3` (light) and `§4` (dark).
**Components:** see `UXPILOT_08_components.md` for skeletons (§15), banners (§17), toasts (§8).
**Charts:** see `UXPILOT_09_dataviz.md` for chart-specific empty/loading.

This file consolidates every UI state pattern referenced across `UXPILOT_01..05`. Per-page prompts cite this file rather than restating loading/empty/error/success/sealed treatment.

---

## 1. State taxonomy

Eight states cover everything. UXPilot mockups must specify which state(s) they render.

| State | When | Acceptance |
|---|---|---|
| `loading` | Initial fetch, post-action wait | Skeleton placeholder, no spinner image, no shimmer animation |
| `empty` | Query returns 0 rows or filter excludes everything | Mono+Spectral copy from §3 library, no fake-empty chart frames |
| `error` | API call failed, network out, server 5xx | Coral 1px stripe + mono 12pt error message + retry link |
| `success` | Action completed (submit, save, accept, decide) | Toast `toast-success` (see `UXPILOT_08 §8`); no banner takeover |
| `sealed` | Content exists but is governance-locked from this projection | Lock chip + mono 11pt "sealed · governance unlock required" |
| `not_permitted` | User authenticated but lacks ACL | Mono 14pt "your role does not reach this surface" + role chip + link to doctrine |
| `not_found` | Resource doesn't exist (404) | "this surface is not in the river" copy from §4 + link to /papers |
| `maintenance` | Admin-set window | Banner per `UXPILOT_07 §10` with relative-window indicator |

---

## 2. Loading state — visual specs per surface

| Surface | Loading render |
|---|---|
| Card list (papers, queue, open requests) | Skeleton card stack from `UXPILOT_08 §15`. Count matches expected results (5, 8, 20 etc.) |
| Table (admin manager) | 8 skeleton rows. Headers render normal. Footer pagination renders disabled |
| Module body | 3 skeleton bars 36px each, 8px gap |
| Chart | Bg `--paper2` block matching chart bounds. No animation |
| Modal body | Centered mono 11pt `--ink3` "loading…" — no skeleton inside modal |
| Form (submit / decide) | Form fields render disabled (50% opacity); footer button shows loading state per `UXPILOT_08 §1` |
| Inline action (chip click, sort change) | 200ms opacity dim from 1.0 → 0.6, no skeleton swap |
| Page transition | No global loading. Each surface manages its own |

**Acceptance:**
- No spinner GIFs. No animated shimmer. No "Loading… please wait" prose.
- Skeletons are honest about absence — no performative animation.
- Per `UXPILOT_08 §15`, skeleton render only on initial fetch. Filter/tab changes use opacity dim instead.

---

## 3. Empty state — copy library

These strings carry the eaiou voice: poetic-honest, never apologetic, never marketing. Spectral italic for the leading line; mono 11pt for the action link below.

### 3.1 Public / discovery surfaces

| Surface | Empty copy | Action link |
|---|---|---|
| `/` (home) | *the river is rising* (placeholder — should not normally show) | `→ explore /papers` |
| `/papers` (filter excludes all) | *no papers match — your filter is too narrow* | `→ reset filters` |
| `/papers` (truly no published yet) | *the river is dry — no published papers yet* | `→ doctrine` |
| `/discover/ideas` | *no ideas in this slice — try a different cycle* | `→ all cycles` |
| `/discover/open` | *no open collaboration requests in this slice* | `→ all open` |
| `/discover/gaps` | *no gaps in this slice — the river is flowing freely* | `→ doctrine` |
| `/discover/trends` | *no trends — the field is asleep* | `→ all cycles` |
| `/search?q=X` | *no surface answers `<q>`* | `→ try tag: rs:` |
| `/tag/{name}` | *no papers carry this tag yet* | `→ /papers` |

### 3.2 Author surfaces

| Surface | Empty copy | Action link |
|---|---|---|
| `/mypapers` (no papers yet) | *your river hasn't started yet* | `→ submit your first paper` |
| `/mypapers` (filtered to 0) | *no papers in this slice of yours* | `→ reset filters` |
| `/paper/{id}/workspace` (no comments) | *no review activity yet — your paper is in queue* | `→ /reviewer/queue` |

### 3.3 Reviewer surfaces

| Surface | Empty copy | Action link |
|---|---|---|
| `/reviewer/queue` (no assignments) | *no active assignments* | `→ /reviewer/profile to set discipline` |
| `/reviewer/queue` (all complete) | *queue clear — the river thanks you* | `→ /papers` |
| `/reviewer/paper/{id}/review` (rubric blank) | *score each criterion to submit your review* | (no link — instruction only) |

### 3.4 Editor surfaces

| Surface | Empty copy | Action link |
|---|---|---|
| `/editorial/papers` (no manuscripts) | *no manuscripts in motion this cycle* | `→ /editorial/settings` |
| `/editorial/papers` (filtered to 0) | *no manuscripts in this slice* | `→ reset filters` |
| `/editorial/decide/{id}` (no reviews yet) | *cannot decide — no completed reviews* | `→ /editorial/assign/{id}` |

### 3.5 Admin surfaces

| Surface | Empty copy | Action link |
|---|---|---|
| Admin manager (no rows) | *no records match this filter* | `→ reset filters` |
| Admin manager (table empty entirely) | *no records yet — table is fresh* | (no link) |
| AI Sessions detail (no events) | *no events logged for this session* | `→ /administrator/.../com_eaiou&view=ai_sessions` |
| Sealed audit (no entries) | *the audit trail is empty in this scope* | (no link) |

### 3.6 Module empty states

Already specified in `UXPILOT_06`. Recap:

| Module | Copy |
|---|---|
| `mod_reviewer_queue` | *no active assignments* |
| `mod_editor_dashboard` | *no editorial activity this cycle* |
| `mod_latest_papers` | *the river is dry — no published papers* |
| `mod_open_collaborate` | *no open requests in this slice* |
| `mod_ai_usage_heatmap` | *no AI usage logged in this slice* |
| `mod_gap_map` | *no gaps in this slice — the river is flowing freely* |
| `mod_trending_ideas` | *no trends — the field is asleep* |
| `mod_intellid_graph` | *no attribution data* |
| `mod_appreciated_scale` | *no appreciated-scale matches yet* |

### 3.7 Empty state layout

- Render inside the surface frame (card, module body, table body, modal body).
- Spectral italic 14pt centered, `--ink2`.
- Mono 11pt action link below if applicable, `--river`, with `→ ` prefix.
- Min height: 120px (modules), 160px (table body), 200px (page main column when entirely empty).
- No icons. No illustrations. No mascots. (Honest absence.)

---

## 4. Error state — copy library

Errors stay terse and useful. Coral accent only. Never apologize. Always offer a next action.

| Surface / cause | Error copy | Recovery |
|---|---|---|
| API 5xx | *the surface is unreachable — try again* | `→ retry` link mono 11pt `--coral` |
| API 401 | *your session has expired* | `→ sign in again` |
| API 403 | *your role does not reach this surface* | `→ /doctrine` |
| API 404 (resource) | *this surface is not in the river* | `→ /papers` |
| API 422 (validation) | Inline field errors only; no top-level banner | (per-field in form) |
| API 429 (rate limit) | *too many requests — slow down* | `→ /doctrine` |
| Network offline | *the river is unreachable from here — check your connection* | `→ retry` |
| Filter combination invalid | *that combination is not allowed* + reason mono 11pt | `→ reset filters` |
| Form save failed (transient) | Toast `toast-error` mono 12pt "save failed — your draft is preserved" + retry button | (in toast) |
| Submit blocked (governance) | Modal `modal-confirm` Spectral 16pt "submission blocked — see doctrine" + close | `→ /doctrine` |

**Error layout:**
- Inline error: 1px coral top stripe across the surface; mono 12pt copy below in `--coral`; mono 11pt retry link `--coral`.
- Modal error: `modal-confirm` body shows Spectral 14pt error + mono 11pt cause; footer single "close" button.
- Toast error: persistent (no auto-dismiss) per `UXPILOT_08 §8`.
- Form field error: see `UXPILOT_08 §2` (mono 11pt below input).

**Acceptance:**
- Never the word "Sorry".
- Never the word "Oops".
- Never an exclamation point in error copy.
- Error code shown in mono 10pt UPPERCASE `--ink3` after copy: `ERR · 5XX · TRACE INT-9F2A`. Trace IDs help support; not user-facing recovery.

---

## 5. Success state — patterns

Success is quiet — eaiou avoids celebratory UI. No confetti, no checkmark bursts, no "great job!" copy.

| Action | Success treatment |
|---|---|
| Save draft | Toast `toast-info` mono 11pt "draft saved · cycle q4" — 5s dwell |
| Submit paper | Modal `modal-confirm` Spectral 16pt "your paper enters the river. capstone DOI minted: 10.5281/zenodo.NNNNN" + close button |
| Accept review assignment | Toast `toast-success` mono 11pt "assignment accepted · review window open" |
| Submit review | Modal `modal-confirm` Spectral 16pt "review submitted. session sealed." + close |
| Editor decide | Modal `modal-confirm` Spectral 16pt "decision rendered. authors notified via IntelliD relay." + close |
| Governance unlock granted | Banner per `UXPILOT_07 §10` row 1 (`--coral-l` bg, countdown chip) |
| UNKINT projection enable | Header chip flips `HUMINT → UNKINT` + countdown; toast `toast-info` "UNKINT projection active · Nm window" |
| UNKINT expire | Toast `toast-info` "UNKINT projection expired · HUMINT view restored" |
| Form submit (any inline) | Inline confirmation Spectral 14pt italic above form `--sage` "saved" — fades after 3s opacity 1 → 0 |

**Acceptance:**
- No success animations beyond opacity fades.
- Capstone DOI surface is the one place "publishing celebration" gets a slightly bigger Spectral display — and even then it's italic, not bold.
- No language like "yay", "awesome", "perfect", "great". Success states report fact only.

---

## 6. Sealed state — when content is governance-locked

eaiou supports sealed metadata that is visible only with explicit governance unlock. Sealed content is not absent — it is hidden behind a lock.

| Surface | Sealed render |
|---|---|
| Paper detail with sealed timestamps (HUMINT view) | Sealed badge per `UXPILOT_00 §8` in masthead. Sources tab "submitted at" row reads mono 11pt `--ink3` "sealed — request governance unlock". |
| Admin manager rows with sealed fields | Sealed cells render mono `····` placeholder, hover tooltip "sealed in HUMINT projection". |
| Sealed audit page | Page-level lock screen Spectral 36pt "sealed audit". Mono 11pt below: "this surface requires governance unlock + second-key approval. open request →". |
| USO record viewer | Page-level Spectral 18pt "USO record sealed at TRACK". Sealed metadata block visible only with admin governance unlock. |
| `view=didntmakeit&id={id}` | Lock chip + mono 11pt "didntmakeit detail · governance unlock required" |

**Sealed badge behavior:**
- Click → modal `modal-confirm` "this content is sealed. request governance unlock?" → opens UNKINT activation flow per `UXPILOT_07 §7`.

**Acceptance:**
- Sealed copy never says "private" or "hidden". It says "sealed".
- The placeholder mono `····` is visually equivalent to redaction. Never replace with `XXXX` or `[REDACTED]`.
- Sealed surfaces always tell the user *what type* of unlock is required (UNKINT projection vs sealed-audit unlock vs admin role).

---

## 7. Not-permitted state — ACL gate

User is authenticated but their role does not reach the surface.

**Render:**
- Page-level: full main column with mono 11pt UPPERCASE `--ink3` breadcrumb at top, Spectral 36pt centered "your role does not reach this surface".
- Below: mono 11pt UPPERCASE role chip showing user's current role + arrow + role chip showing required role.
- Below: Spectral 14pt italic "request a role change in /reviewer/profile" or "see the doctrine for role definitions".

**Action links:**
- `→ /doctrine` (always)
- `→ /reviewer/profile` (if upgrade is reviewer-side)
- `→ contact@eaiou` mono link (for editor / admin role asks)

**Acceptance:**
- Never use the word "denied" or "forbidden".
- Never use HTTP status code in the body copy ("403" is fine in URL or trace ID, not in user copy).
- The user's current role is always visible — they should know where they stand.

---

## 8. Not-found state (404)

**Render:**
- Page-level Spectral 36pt centered "this surface is not in the river".
- Mono 11pt below: `404 · ERR · NO MAP TO ENDPOINT`.
- Spectral 14pt italic "the most likely cause: the URL has a sealed-time component that has expired".
- Action chips: `→ /papers` · `→ /search` · `→ /` (mono 11pt outline buttons).
- Optional: list of 3 recently-visited papers if browser history allows.

**Acceptance:**
- Never blame the user.
- No mascot. No 404 illustration. No "Page not found" headline.
- Branded chrome (header, footer) renders normally.

---

## 9. Maintenance state

**Render:**
- Banner per `UXPILOT_07 §10` row 5 (`--paper2` bg, 4px `--ink3` left, mono 11pt + relative-window).
- Copy: `system maintenance · cycle q4 · relative window 4 of 7 · expected end ▢▢▢▣▣▣▣`.
- During hard-down maintenance: full-page surface with Spectral 24pt "the river is paused for maintenance" + relative-window glyph + mono 11pt "doctrine v2.0 · cycle q4".

**Acceptance:**
- No absolute clock times even in maintenance copy.
- Relative-window glyph (see `UXPILOT_09 §13`) is the only progress indicator.

---

## 10. Skeleton-to-content transition

When loading completes:
- Skeleton elements are replaced by real content with no animation (instant swap).
- Page reflow allowed (skeleton heights match content heights, so reflow should be near-zero).
- No fade-in. No translate. No spinner-to-content "reveal" effect.

**Acceptance:**
- The user should not perceive a "loading completed" moment as a UI event. It is a data event, not an experience.

---

## 11. Multi-surface coordination

When a single page contains multiple async surfaces (e.g., paper detail with manuscript tab + sources tab + AI usage tab + open reports tab), each tab loads independently.

- Tab strip renders immediately (chrome ready).
- Default tab body shows skeleton.
- Switching tabs before data arrives shows skeleton in the new tab.
- Once a tab's data loads, it's cached for the session — switching back is instant.
- Right-rail modules load independently of main column.

**Acceptance:**
- Never block the page on a single fetch.
- Independent failures: if AI usage tab errors but manuscript loads, only the AI usage tab shows error state.

---

## 12. Per-page state checklist

Every UXPilot page mockup should specify, for each surface zone, what these states look like. The per-page prompts in `UXPILOT_01..05` already include "States:" lines — this file standardizes the language they should use.

**Recommended pattern in page prompts:**
```
States:
  loading → [skeleton spec from UXPILOT_10 §2]
  empty → [copy from UXPILOT_10 §3]
  error → [copy from UXPILOT_10 §4]
  sealed (if applicable) → [render from UXPILOT_10 §6]
```

---

## 13. Voice rules for state copy

Eric's interaction rules (`feedback_interaction_rules.md`) require plain language, short sentences, active voice. State copy applies these even more strictly:

- ≤ 12 words per sentence (target).
- No transitions ("furthermore", "in conclusion", etc.).
- No second-person commands ("Please try again"). Use mono action links instead.
- Lowercase Spectral italic for emotive copy ("the river is dry"). Never sentence-case marketing.
- Mono UPPERCASE for system/technical labels ("ERR · 5XX", "SESSION LOCK", "GOVERNANCE UNLOCK").

---

## 14. Acceptance criteria for any UXPilot mockup that includes states

1. Every surface specifies all four base states: loading · empty · error · success.
2. Sealed and not-permitted states specified for ACL-gated surfaces.
3. Empty copy uses the library in §3 verbatim where listed.
4. Error copy follows §4 patterns; never apologetic; always offers an action.
5. Success uses toast or modal-confirm (no celebratory UI).
6. Sealed renders with `····` placeholder + sealed badge — never `[REDACTED]` or absence.
7. No spinners. No shimmer. No "please wait".
8. Skeleton heights match real-content heights to minimize reflow.
9. Cards rendered in empty state have no fake content placeholders.
10. State copy follows §13 voice rules (Spectral italic for affect, mono UPPERCASE for system).

---

## 15. Citation rules

- Per-page prompts cite empty copy by surface: "Empty state copy per `UXPILOT_10 §3.2` /mypapers row."
- Modules cite empty copy by module name: "Empty per `UXPILOT_10 §3.6` mod_open_collaborate."
- Error patterns cite by cause: "Render API 5xx error per `UXPILOT_10 §4`."

---

## 16. Open state questions (for Eric)

1. Sealed audit empty copy — should it tell the user the audit *exists but is unreachable*, or just say "empty in this scope"? Current spec leans toward the latter (don't leak existence).
2. Capstone DOI surface size — current spec says "Spectral italic, slightly larger". Confirm exact size.
3. Maintenance hard-down full-page — does eaiou ever go full hard-down, or always banner-level degraded?
4. 404 history list (3 recent papers) — privacy implications? May need to scope to public papers only.
5. Form save-draft auto-trigger — should every form auto-save on blur, or only the submit wizard? Current spec: only submit wizard.

---

## End of `UXPILOT_10_states.md`

Next file: `UXPILOT_11_motion.md` — animation timings, focus rings, hover transitions, modal/drawer/toast lifecycles.
