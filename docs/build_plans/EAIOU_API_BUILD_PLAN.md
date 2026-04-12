# EAIOU — API Build Plan (Claude Code Lockfile)

**Version:** 1.0.0 — 2026-04-12
**Author:** Eric D. Martin — ORCID: 0009-0006-5944-1742
**Purpose:** This document specifies EVERY API endpoint in the eaiou platform — 87 endpoints across 12 tiers. Claude Code MUST implement them in tier order. Each endpoint has its HTTP method, route, ACL, request/response shape, DB tables touched, and validation rules.
**Companions:** `EAIOU_BACKEND_BUILD_PLAN.md` (component + plugins) · `EAIOU_FRONTEND_BUILD_PLAN.md` (views)
**Status:** CANONICAL

---

## 0. RULES FOR CLAUDE CODE

1. **Build tiers in order.** Tier 1 must be complete and tested before Tier 2 begins.
2. **Every endpoint goes through `plg_webservices_eaiou`.** Register the route there first.
3. **Every endpoint respects ACL.** Check `$user->authorise()` before any data access.
4. **Every mutating endpoint writes an Action Log entry.** No silent writes.
5. **Every public GET endpoint runs through `plg_system_temporal_blindness`.** Sealed fields MUST be stripped before response.
6. **All list endpoints default to `ORDER BY q_signal DESC`** unless the endpoint is explicitly marked as using a different sort (e.g., reviewer queue by due date).
7. **No endpoint returns `submission_sealed_at`, `acceptance_sealed_at`, or `publication_sealed_at`** unless the caller has governance unlock permission AND the `governance_unlock` flag is set.
8. **API log hash chain:** Every API call that passes through `api.keys` auth MUST be logged in `eaiou_api_logs` with `log_hash` and `prior_hash` computed.
9. **Use JSON for all request/response bodies.** Content-Type: `application/json`.
10. **Error responses use standard HTTP codes** with `{"error": "message", "code": HTTP_CODE}` body.

---

## 1. BASE URL AND AUTH

**REST base:** `/api/index.php/v1/eaiou`

All routes below are relative to this base. Full example:
```
GET https://eaiou.org/api/index.php/v1/eaiou/papers
```

**Authentication methods:**
- **Session auth:** PHP Laravel for backend and Py9thonk Fast API for evertthin g else session cookie (for logged-in frontend users)
- **API key auth:** `X-Eaiou-Key: {api_key}` header → validated against `eaiou_api_keys`
- **PHP Laravel for backend and Py9thonk Fast API for evertthin g else API token:** Standard PHP Laravel for backend and Py9thonk Fast API for evertthin g else Web Services bearer token

**ACL shorthand used below:**
- `PUBLIC` = no auth required
- `AUTH` = any authenticated user
- `AUTHOR` = eaiou_Author group
- `REVIEWER` = eaiou_Reviewer group
- `EDITOR` = eaiou_Editor group
- `EIC` = eaiou_EIC group
- `ADMIN` = eaiou_Admin group
- `OWNER` = authenticated user who created the record
- `ASSIGNED` = reviewer assigned to this paper

---

## TIER 1 — CORE SYSTEM (16 endpoints)

> Must exist first. Everything else depends on these.

---

### `paper.get`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/papers/{id}` |
| **ACL** | PUBLIC |
| **Tables** | `eaiou_papers` JOIN `#__content` (article) |
| **Response** | Paper object with article data, authorship_mode, status, q_signal, badges, authors_json. **NO sealed dates.** |
| **Temporal Blindness** | Strip `submission_sealed_at`, `acceptance_sealed_at`, `publication_sealed_at` from response |
| **Notes** | Include computed badge flags: has_transparency, has_ai_usage, has_unsci, collab_open |

### `paper.list`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/papers` |
| **ACL** | PUBLIC |
| **Tables** | `eaiou_papers` JOIN `#__content` |
| **Query params** | `?limit=20&offset=0&category={catid}&authorship_mode={mode}&status=published&include_nottopic=false` |
| **Sort** | `q_signal DESC` — **ONLY.** No date sort parameter accepted. If `sort=date` is passed, return 400. |
| **Response** | Paginated array of paper summaries with q_signal, badges, ORCID, discipline tags |
| **Temporal Blindness** | No sealed dates in response. No date-based filtering on sealed fields. |

### `paper.create`
| | |
|---|---|
| **Method** | POST |
| **Route** | `/papers` |
| **ACL** | AUTHOR |
| **Tables** | `eaiou_papers` INSERT, `#__content` INSERT |
| **Request body** | `{article_id?, paper_uuid, authorship_mode, title, abstract, authors_json, keywords, catid}` |
| **Validation** | paper_uuid must be unique. authorship_mode must be human/ai/hybrid. |
| **Side effects** | Generate paper_uuid if not provided. Create `#__content` article if article_id not provided. |
| **Action Log** | `PAPER_CREATED: paper_uuid={uuid}` |
| **Response** | Created paper object with id and paper_uuid |

### `paper.update`
| | |
|---|---|
| **Method** | PATCH |
| **Route** | `/papers/{id}` |
| **ACL** | OWNER or EDITOR |
| **Tables** | `eaiou_papers` UPDATE, `#__content` UPDATE |
| **Request body** | Partial update: any paper field except sealed fields |
| **Validation** | Cannot update sealed fields (submission_sealed_at, etc.). Cannot update q_signal directly (computed only). |
| **Action Log** | `PAPER_UPDATED: paper_id={id}, fields=[list]` |

### `workflow.get_state`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/papers/{id}/workflow` |
| **ACL** | PUBLIC (state name only), EDITOR+ (full transition history) |
| **Tables** | `eaiou_papers`.status, PHP Laravel for backend and Py9thonk Fast API for evertthin g else Workflow transitions |
| **Response** | `{current_state: "under_review", available_transitions: [...]}` (transitions only shown to EDITOR+) |

### `workflow.transition`
| | |
|---|---|
| **Method** | POST |
| **Route** | `/papers/{id}/workflow/transition` |
| **ACL** | Depends on transition (see Section 7.2 of Backend Plan): AUTHOR for submit, EDITOR for assign/decide/publish |
| **Request body** | `{target_state: "submitted", notes: "..."}` |
| **Validation** | Transition must be valid from current state. Plugin guards fire (transparency complete, AI log complete, unsci resolved). |
| **Side effects** | If target_state=submitted → **TEMPORAL SEALING EVENT** (see Backend Plan Section 13). If target_state=accepted → **CAPSTONE TRIGGER**. |
| **Action Log** | `WORKFLOW_TRANSITION: paper_id={id}, from={old}, to={new}` |

### `contribution.create`
| | |
|---|---|
| **Method** | POST |
| **Route** | `/papers/{paper_id}/attribution` |
| **ACL** | AUTHOR (own paper) or EDITOR |
| **Tables** | `eaiou_attribution_log` INSERT |
| **Request body** | `{contributor_name, orcid?, role_description, contribution_type, is_human, is_ai, ai_tool_used?, version_id?}` |
| **Action Log** | `ATTRIBUTION_ADDED: paper_id={id}, contributor={name}, type={human|ai}` |

### `contribution.list_by_paper`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/papers/{paper_id}/attribution` |
| **ACL** | PUBLIC |
| **Tables** | `eaiou_attribution_log` WHERE paper_id |
| **Response** | Array of attribution entries |

### `intellid.create`
| | |
|---|---|
| **Method** | POST |
| **Route** | `/ai/sessions` |
| **ACL** | AUTHOR or API_CLIENT |
| **Tables** | `eaiou_ai_sessions` INSERT |
| **Request body** | `{paper_id, session_label, ai_model_name, start_time?, end_time?, tokens_in?, tokens_out?, redaction_status, session_notes?, session_hash?, answer_box_session_id?, answer_box_ledger_capstone?}` |
| **Action Log** | `AI_SESSION_LOGGED: paper_id={id}, model={name}` |

### `intellid.list`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/ai/sessions` |
| **ACL** | REVIEWER+ |
| **Tables** | `eaiou_ai_sessions` |
| **Query params** | `?paper_id={id}&model={name}` |
| **Response** | Array of AI session records |

### `user.get`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/users/{id}` |
| **ACL** | AUTH (own profile), EDITOR+ (any user) |
| **Tables** | `#__users` + User Custom Fields (orcid_id, orcid_url) |
| **Response** | User object with name, email (if authorized), ORCID, groups |

### `user.list`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/users` |
| **ACL** | EDITOR+ |
| **Tables** | `#__users` + `#__user_usergroup_map` |
| **Query params** | `?group={group_name}&has_orcid=true` |

### `qscore.compute`
| | |
|---|---|
| **Method** | POST |
| **Route** | `/papers/{paper_id}/qsignal/compute` |
| **ACL** | EDITOR or SYSTEM (triggered automatically after review) |
| **Tables** | `eaiou_quality_signals` INSERT, `eaiou_papers` UPDATE (q_signal denormalized) |
| **Logic** | Read all quality_signals for paper_id → average each dimension → apply weights (transparency ×1.5) → compute composite → write new quality_signals row → update eaiou_papers.q_signal |
| **Action Log** | `QSIGNAL_COMPUTED: paper_id={id}, q_signal={value}` |

### `qscore.get`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/papers/{paper_id}/qsignal` |
| **ACL** | PUBLIC |
| **Tables** | `eaiou_quality_signals` WHERE paper_id |
| **Response** | `{q_signal: 9.24, breakdown: {overall: 9.0, originality: 9.4, methodology: 8.8, transparency: 9.6, ai_disclosure: 9.1, crossdomain: 9.0}, review_count: 2}` |

### `auth.login`
| | |
|---|---|
| **Method** | POST |
| **Route** | `/auth/login` |
| **ACL** | PUBLIC |
| **Request body** | `{username, password}` or `{orcid_token}` (for ORCID OAuth) |
| **Response** | `{token, user_id, groups: [...], orcid_id?}` |
| **Notes** | Wraps PHP Laravel for backend and Py9thonk Fast API for evertthin g else authentication. For ORCID OAuth, delegates to plg_system_orcid_link. |

### `auth.check_permission`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/auth/permissions` |
| **ACL** | AUTH |
| **Query params** | `?action={action}&paper_id={id}` |
| **Response** | `{allowed: true/false, reason: "..."}` |
| **Notes** | Wraps `$user->authorise()` for the requested action on the given asset. |

---

## TIER 2 — REVIEW + WORKFLOW ENGINE (9 endpoints)

> Depends on: Tier 1 (papers, users, workflow, qscore)

---

### `review.assign`
| | |
|---|---|
| **Method** | POST |
| **Route** | `/papers/{paper_id}/reviewers` |
| **ACL** | EDITOR |
| **Tables** | Article Custom Fields (Deadlines group: rev_invite_assignments) UPDATE |
| **Request body** | `{reviewer_user_id, invite_due_date, notes?}` |
| **Side effects** | Set rev_invite_status=Pending, rev_invite_sent=NOW(). Send invite email via Mail Template. |
| **Action Log** | `REVIEWER_ASSIGNED: paper_id={id}, reviewer={user_id}` |

### `review.submit`
| | |
|---|---|
| **Method** | POST |
| **Route** | `/papers/{paper_id}/reviews` |
| **ACL** | ASSIGNED REVIEWER |
| **Tables** | `eaiou_review_logs` INSERT, `eaiou_quality_signals` INSERT |
| **Request body** | `{version_reviewed, rubric_overall, rubric_originality, rubric_methodology, rubric_transparency, rubric_ai_disclosure, rubric_crossdomain, recommendation, review_notes, labels_json?, unsci_flagged, open_consent}` |
| **Validation** | All rubric scores must be 0–10. Recommendation must be valid enum. Reviewer must be assigned to this paper. |
| **Side effects** | Create quality_signals record from rubric. **Trigger `qscore.compute`** for this paper. If all assigned reviewers have submitted → transition to decision_pending. |
| **Action Log** | `REVIEW_SUBMITTED: paper_id={id}, reviewer={user_id}, recommendation={rec}` |

### `review.get`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/reviews/{review_id}` |
| **ACL** | REVIEWER (own review), EDITOR+ (any review) |
| **Tables** | `eaiou_review_logs` |
| **Notes** | Public access controlled by plg_content_openreports mode (open/anonymous/summary) |

### `review.list_by_paper`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/papers/{paper_id}/reviews` |
| **ACL** | EDITOR+ (full), PUBLIC (if or_mode allows) |
| **Tables** | `eaiou_review_logs` WHERE paper_id |
| **Response** | Array of reviews. Public response filtered by openreports mode (strip reviewer identity if anonymous, strip body if summary-only). |

### `workflow.assign_reviewers`
| | |
|---|---|
| **Method** | POST |
| **Route** | `/papers/{paper_id}/workflow/assign` |
| **ACL** | EDITOR |
| **Side effects** | Calls `review.assign` for each reviewer. Transitions paper to `under_review` if currently `submitted`. |
| **Request body** | `{reviewers: [{user_id, due_date}], notes?}` |
| **Action Log** | `REVIEWERS_ASSIGNED: paper_id={id}, count={n}` |

### `workflow.request_revision`
| | |
|---|---|
| **Method** | POST |
| **Route** | `/papers/{paper_id}/workflow/revise` |
| **ACL** | EDITOR |
| **Request body** | `{revision_notes, due_date}` |
| **Side effects** | Transition to `revisions_requested`. Set auth_rev_due in Deadlines field group. Send revision request email. |
| **Action Log** | `REVISION_REQUESTED: paper_id={id}` |

### `workflow.accept`
| | |
|---|---|
| **Method** | POST |
| **Route** | `/papers/{paper_id}/workflow/accept` |
| **ACL** | EDITOR |
| **Request body** | `{editor_notes?}` |
| **Side effects** | Transition to `accepted`. Set `acceptance_sealed_at`. **CAPSTONE TRIGGER:** queue Zenodo deposition. Send acceptance email. |
| **Action Log** | `PAPER_ACCEPTED: paper_id={id}` |

### `workflow.reject`
| | |
|---|---|
| **Method** | POST |
| **Route** | `/papers/{paper_id}/workflow/reject` |
| **ACL** | EDITOR |
| **Request body** | `{rejection_reason, editor_notes?}` |
| **Side effects** | Transition to `rejected` → archived (tombstone). Send rejection email. Paper remains searchable. **Never hard-deleted.** |
| **Action Log** | `PAPER_REJECTED: paper_id={id}` |

### `review.get_rubric`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/review/rubric` |
| **ACL** | PUBLIC |
| **Response** | `{dimensions: [{name: "overall", weight: 1.0}, {name: "originality", weight: 1.0}, {name: "methodology", weight: 1.0}, {name: "transparency", weight: 1.5}, {name: "ai_disclosure", weight: 1.0}, {name: "crossdomain", weight: 1.0}], scale: {min: 0, max: 10}}` |
| **Notes** | Returns current rubric configuration. Weights configurable in admin settings. |

---

## TIER 3 — AUTHORSHIP + AI / INTELLID LAYER (7 endpoints)

> Depends on: Tier 1 (papers, contribution, intellid)

---

### `contribution.update`
| | |
|---|---|
| **Method** | PATCH |
| **Route** | `/attribution/{id}` |
| **ACL** | OWNER or EDITOR |
| **Tables** | `eaiou_attribution_log` UPDATE |
| **Validation** | Cannot change paper_id. All other fields updatable. |
| **Action Log** | `ATTRIBUTION_UPDATED: id={id}` |

### `contribution.delete`
| | |
|---|---|
| **Method** | DELETE |
| **Route** | `/attribution/{id}` |
| **ACL** | EDITOR |
| **Tables** | `eaiou_attribution_log` UPDATE `state = -2` |
| **Notes** | **TOMBSTONE ONLY.** Sets state to trashed. Never hard-deletes. Record preserved in archive. |
| **Action Log** | `ATTRIBUTION_TOMBSTONED: id={id}` |

### `intellid.get`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/ai/sessions/{id}` |
| **ACL** | REVIEWER+ |
| **Tables** | `eaiou_ai_sessions` |

### `intellid.get_contributions`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/ai/sessions/{session_id}/didntmakeit` |
| **ACL** | EIC+ (full content), REVIEWER (metadata only: exclusion_reason, redacted flag) |
| **Tables** | `eaiou_didntmakeit` WHERE session_id |
| **Notes** | If redacted=1, prompt_text and response_text are NULL in response. redaction_hash is always returned for integrity verification. |

### `ai.log_session`
| | |
|---|---|
| **Method** | POST |
| **Route** | `/papers/{paper_id}/ai/sessions` |
| **ACL** | AUTHOR or API_CLIENT |
| **Tables** | `eaiou_ai_sessions` INSERT |
| **Notes** | Alias for `intellid.create` scoped to a specific paper. |

### `ai.get_sessions`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/papers/{paper_id}/ai/sessions` |
| **ACL** | REVIEWER+ |
| **Tables** | `eaiou_ai_sessions` WHERE paper_id |

### `ai.get_disclosure`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/papers/{paper_id}/ai/disclosure` |
| **ACL** | PUBLIC |
| **Tables** | Article Custom Fields (AI Usage group) |
| **Response** | `{ai_used: true, tools: [...], interaction_count: 12, didntmakeit_count: 4, display_level: "full", relationship_statement: "...", ai_log_complete: true}` |
| **Notes** | Reads from Custom Fields. Detail level controlled by `ai_display_level` field. Reviewers/editors always see full. |

---

## TIER 4 — TRANSPARENCY + REMSEARCH (5 endpoints)

> Depends on: Tier 1 (papers)

---

### `transparency.get`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/papers/{paper_id}/transparency` |
| **ACL** | PUBLIC |
| **Tables** | Article Custom Fields (Transparency group) + `eaiou_remsearch` WHERE paper_id |
| **Response** | `{sources: [{title, type, used, reason_unused}], datasets: [...], methods: "...", limitations: "...", complete: true, lastcheck: "ISO8601"}` |

### `transparency.update`
| | |
|---|---|
| **Method** | PATCH |
| **Route** | `/papers/{paper_id}/transparency` |
| **ACL** | AUTHOR (own) or EDITOR |
| **Tables** | Article Custom Fields UPDATE |
| **Side effects** | Revalidate completeness. Update `transp_complete` and `transp_lastcheck`. |
| **Action Log** | `TRANSPARENCY_UPDATED: paper_id={id}` |

### `transparency.add_source`
| | |
|---|---|
| **Method** | POST |
| **Route** | `/papers/{paper_id}/remsearch` |
| **ACL** | AUTHOR |
| **Tables** | `eaiou_remsearch` INSERT |
| **Request body** | `{citation_title, citation_source?, citation_link?, source_type, used, reason_unused?, fulltext_notes?}` |
| **Validation** | If used=0 (excluded), reason_unused should be provided (required before publish). |
| **Action Log** | `REMSEARCH_ADDED: paper_id={id}, title={title}, used={0|1}` |

### `transparency.mark_unused`
| | |
|---|---|
| **Method** | PATCH |
| **Route** | `/remsearch/{id}` |
| **ACL** | AUTHOR or EDITOR |
| **Tables** | `eaiou_remsearch` UPDATE |
| **Request body** | `{used: 0, reason_unused: "scope"}` |
| **Action Log** | `REMSEARCH_MARKED_UNUSED: id={id}` |

### `transparency.get_completeness`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/papers/{paper_id}/transparency/completeness` |
| **ACL** | AUTHOR or EDITOR |
| **Response** | `{complete: false, missing: ["transp_methods", "transp_limitations"], sources_count: 4, excluded_without_reason: 1}` |
| **Notes** | Used by submission wizard step 6 (confirm) to show pre-submission checklist. |

---

## TIER 5 — DISCOVERY + SEARCH (7 endpoints)

> Depends on: Tier 1 (papers, qscore), Tier 4 (remsearch)

---

### `search.query`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/search` |
| **ACL** | PUBLIC |
| **Query params** | `?q={text}&category={catid}&authorship_mode={mode}&has_ai=true&has_collab=true&limit=20&offset=0` |
| **Sort** | `q_signal DESC` always. No date sort. |
| **Tables** | `#__content` + `eaiou_papers` + Smart Search index |
| **Response** | Paginated paper results with q_signal, badges, highlights |

### `search.unspace`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/search/unspace` |
| **ACL** | PUBLIC |
| **Query params** | `?q={text}&tag_type={rs:NotTopic|rs:NullResult|...}&limit=20&offset=0` |
| **Tables** | `eaiou_remsearch` (unused sources) + Article Tags (rs:NotTopic artifacts) + `eaiou_didntmakeit` (metadata only) |
| **Sort** | Entropy-novelty score DESC |
| **Response** | Array of un-space artifacts: excluded sources, NotTopic items, null results |
| **Notes** | This is the "search the river's unused tributaries" endpoint. |

### `discover.papers`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/discover/papers` |
| **ACL** | PUBLIC |
| **Notes** | Alias for `paper.list` with curated defaults (published only, q_signal DESC, includes badge data) |

### `discover.ideas`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/discover/ideas` |
| **ACL** | PUBLIC |
| **Query params** | `?domain={category}&min_entropy=0.5&limit=20` |
| **Tables** | `eaiou_remsearch` (unused, cross_domain_flag=1) + Article Tags (rs:NotTopic, rs:NullResult, rs:OpenQuestion) |
| **Sort** | Entropy-novelty score DESC |
| **Response** | Array of idea objects: `{source_paper_id, source_paper_title, idea_title, idea_description, entropy_score, tags: [...], origin_type: "nottopic|nullresult|didntmakeit"}` |

### `discover.gaps`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/discover/gaps` |
| **ACL** | PUBLIC |
| **Tables** | Article Tags (rs:Stalled:*) with tag_resolved=false, aggregated by category |
| **Response** | `{domains: [{name: "Cosmology", stall_count: 12, stall_types: {Data: 5, Methodology: 4, Funding: 3}}, ...]}` |
| **Notes** | Feeds the Gap Map visualization. Stall density by domain and stall type. |

### `discover.trends`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/discover/trends` |
| **ACL** | PUBLIC |
| **Tables** | Aggregation of search query patterns + rs:OpenQuestion tags + rs:Stalled density changes over time |
| **Response** | Array of trending topics with momentum scores |

### `discover.collaboration`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/discover/collaboration` |
| **ACL** | PUBLIC |
| **Tables** | Article Custom Fields (Open Collaboration group) WHERE collab_open=true |
| **Query params** | `?collab_type={co-author|data-sharing|peer-review|funding}&interest_level={high|medium|low}` |
| **Response** | Array of papers open for collaboration with collab_type, interest_level, collab_seek |

---

## TIER 6 — GAP / GITGAP SYSTEM (7 endpoints)

> Depends on: Tier 5 (discover.gaps)

---

### `gap.get`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/gaps/{id}` |
| **ACL** | PUBLIC |
| **Tables** | Aggregated from rs:Stalled tags per domain |
| **Response** | Gap detail: domain, stall types, linked papers, total stall count |

### `gap.list`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/gaps` |
| **ACL** | PUBLIC |
| **Response** | All gaps by domain, sorted by stall density DESC |

### `gap.create`
| | |
|---|---|
| **Method** | POST |
| **Route** | `/gaps` |
| **ACL** | EDITOR |
| **Request body** | `{domain, description, stall_type?, linked_paper_ids?: [...]}` |
| **Notes** | Manually declare a gap (supplement to auto-detection from rs:Stalled tags) |
| **Action Log** | `GAP_CREATED: domain={domain}` |

### `gap.update`
| | |
|---|---|
| **Method** | PATCH |
| **Route** | `/gaps/{id}` |
| **ACL** | EDITOR |

### `gap.get_linked_papers`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/gaps/{id}/papers` |
| **ACL** | PUBLIC |
| **Response** | Papers with rs:Stalled tags contributing to this gap |

### `gap.get_stalled_items`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/gaps/{id}/stalled` |
| **ACL** | PUBLIC |
| **Response** | Breakdown of stalled items by stall subtype |

### `gap.sync_external`
| | |
|---|---|
| **Method** | POST |
| **Route** | `/gaps/sync` |
| **ACL** | ADMIN |
| **Notes** | Trigger sync with GitGap external service. Webhook handler for incoming gap data. |
| **Action Log** | `GAP_SYNC: source=gitgap, gaps_updated={n}` |

---

## TIER 7 — VERSIONING + INTEGRITY (4 endpoints)

> Depends on: Tier 1 (papers)

---

### `paper.get_versions`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/papers/{paper_id}/versions` |
| **ACL** | PUBLIC |
| **Tables** | `eaiou_versions` WHERE paper_id |
| **Response** | Array of versions: label, ai_flag, ai_model_name, content_hash, notes |
| **Temporal Blindness** | `generated_at` is governance-only. Public response omits it. |

### `paper.create_version`
| | |
|---|---|
| **Method** | POST |
| **Route** | `/papers/{paper_id}/versions` |
| **ACL** | AUTHOR (own) or EDITOR |
| **Tables** | `eaiou_versions` INSERT |
| **Request body** | `{label, file_path?, ai_flag, ai_model_name?, notes?}` |
| **Side effects** | Compute `content_hash` = SHA256 of uploaded file. Store file under `/media/com_eaiou/{paper_uuid}/versions/{label}/`. Increment `submission_version` in eaiou_papers. |
| **Action Log** | `VERSION_CREATED: paper_id={id}, label={label}, ai_flag={0|1}` |

### `paper.get_integrity_chain`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/papers/{paper_id}/integrity` |
| **ACL** | PUBLIC |
| **Tables** | `eaiou_papers` (submission_hash, submission_capstone), `eaiou_versions` (content_hash per version) |
| **Response** | `{sealed: {hash: "a3f8...", capstone: "10.5281/zenodo.789..."}, versions: [{label: "v1", content_hash: "..."}, {label: "v2", content_hash: "..."}]}` |
| **Notes** | Does NOT reveal sealed dates. Only hashes and capstone DOI. |

### `system.hash.verify`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/audit/chain_status` |
| **ACL** | ADMIN |
| **Tables** | `eaiou_api_logs` |
| **Logic** | Walk the hash chain from entry 1 to last. For each entry, verify `prior_hash` matches previous entry's `log_hash`. |
| **Response** | `{status: "intact", entries: 4521, last_verified: "2026-04-12T..."}` or `{status: "broken", break_at: 3847, expected_hash: "...", found_hash: "..."}` |

---

## TIER 8 — ADMIN CONTROL (8 endpoints)

> Depends on: Tier 1, Tier 2

---

### `admin.dashboard`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/admin/dashboard` |
| **ACL** | EDITOR+ |
| **Response** | `{papers: {total, by_state: {...}}, reviews: {pending, overdue, completed_30d}, ttfd_median_days, acceptance_rate_90d, rejection_rate_90d, active_reviewers, api_calls_30d}` |

### `admin.users.list`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/admin/users` |
| **ACL** | ADMIN |
| **Tables** | `#__users` + groups + User Custom Fields |
| **Query params** | `?group={name}&has_orcid=true&status=active` |

### `admin.users.update`
| | |
|---|---|
| **Method** | PATCH |
| **Route** | `/admin/users/{id}` |
| **ACL** | ADMIN |
| **Notes** | Update user groups, status, block/unblock |
| **Action Log** | `USER_UPDATED: user_id={id}, changes=[...]` |

### `admin.papers.override_status`
| | |
|---|---|
| **Method** | POST |
| **Route** | `/admin/papers/{id}/override` |
| **ACL** | EIC or ADMIN |
| **Request body** | `{target_state, reason, bypass_guards: true}` |
| **Notes** | Emergency override: bypasses plugin guards (transparency, AI, unsci). Must provide reason. |
| **Action Log** | `STATUS_OVERRIDE: paper_id={id}, to={state}, reason={text}, guards_bypassed=true` |

### `admin.settings.get`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/admin/settings` |
| **ACL** | ADMIN |
| **Response** | Component configuration: q_signal weights, storage paths, enabled plugins, API throttle settings |

### `admin.settings.update`
| | |
|---|---|
| **Method** | PATCH |
| **Route** | `/admin/settings` |
| **ACL** | ADMIN |
| **Action Log** | `SETTINGS_UPDATED: keys=[...]` |

### `admin.qscore.config`
| | |
|---|---|
| **Method** | GET/PATCH |
| **Route** | `/admin/qsignal/config` |
| **ACL** | ADMIN |
| **Response/Request** | `{weights: {overall: 1.0, originality: 1.0, methodology: 1.0, transparency: 1.5, ai_disclosure: 1.0, crossdomain: 1.0}}` |
| **Notes** | Changing weights triggers recomputation of ALL q_signals (batch job). |
| **Action Log** | `QSIGNAL_WEIGHTS_UPDATED: old={...}, new={...}` |

### `admin.workflow.config`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/admin/workflow/config` |
| **ACL** | ADMIN |
| **Response** | Current workflow states, transitions, guard rules |

---

## TIER 9 — LOGGING + AUDIT (7 endpoints)

> Depends on: Tier 1 (runs from the start, formalized here)

---

### `log.api_call`
| | |
|---|---|
| **Method** | (INTERNAL — called automatically on every API request) |
| **Tables** | `eaiou_api_logs` INSERT |
| **Logic** | On every API call: record endpoint, method, request_hash (SHA256 of payload), response_code, log_timestamp. Compute log_hash. Read prior entry's log_hash → store as prior_hash. **APPEND ONLY.** |

### `log.notification`
| | |
|---|---|
| **Method** | (INTERNAL — called by deadline_nudger and workflow events) |
| **Tables** | PHP Laravel for backend and Py9thonk Fast API for evertthin g else Action Logs |
| **Notes** | All notification sends are recorded in Action Logs, not a separate table. |

### `log.webhook`
| | |
|---|---|
| **Method** | (INTERNAL — called by gap.sync_external) |
| **Tables** | PHP Laravel for backend and Py9thonk Fast API for evertthin g else Action Logs |

### `log.get_api_logs`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/admin/api/logs` |
| **ACL** | ADMIN |
| **Tables** | `eaiou_api_logs` |
| **Query params** | `?endpoint={path}&response_code={code}&from={date}&to={date}&limit=50` |
| **Response** | Paginated log entries with hash chain data |

### `log.get_webhook_logs`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/admin/webhooks/logs` |
| **ACL** | ADMIN |
| **Tables** | PHP Laravel for backend and Py9thonk Fast API for evertthin g else Action Logs filtered by webhook events |

### `log.get_notification_logs`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/admin/notifications/logs` |
| **ACL** | ADMIN |
| **Tables** | PHP Laravel for backend and Py9thonk Fast API for evertthin g else Action Logs filtered by nudger/notification events |

### `log.hash_chain`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/audit/chain_status` |
| **ACL** | ADMIN |
| **Notes** | Alias for `system.hash.verify` (Tier 7). Same endpoint, listed here for completeness. |

---

## TIER 10 — NOTIFICATIONS (4 endpoints)

> Depends on: Tier 2 (workflow events), Tier 9 (logging)

---

### `notification.send`
| | |
|---|---|
| **Method** | (INTERNAL — triggered by workflow transitions and deadline_nudger) |
| **Logic** | Uses PHP Laravel for backend and Py9thonk Fast API for evertthin g else Mail Templates. Sends email to relevant user. Records in Action Log. |
| **Templates** | mail_reviewer_invite_reminder, mail_reviewer_due_reminder, mail_author_revision_reminder, mail_editor_escalation, mail_paper_accepted, mail_paper_rejected, mail_paper_published |

### `notification.list`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/notifications` |
| **ACL** | AUTH (own notifications only) |
| **Tables** | PHP Laravel for backend and Py9thonk Fast API for evertthin g else Action Logs filtered by current user's events |
| **Response** | Array of notification objects: `{type, message, paper_id?, read: false, timestamp}` |

### `notification.mark_read`
| | |
|---|---|
| **Method** | PATCH |
| **Route** | `/notifications/{id}/read` |
| **ACL** | AUTH (own only) |

### `notification.preview_email`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/admin/notifications/preview` |
| **ACL** | ADMIN |
| **Query params** | `?template={template_key}&paper_id={id}&user_id={id}` |
| **Response** | Rendered email HTML with tokens replaced |

---

## TIER 11 — SYSTEM + INFRASTRUCTURE (4 endpoints)

---

### `system.health`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/system/health` |
| **ACL** | PUBLIC (basic), ADMIN (detailed) |
| **Response (basic)** | `{status: "ok", version: "1.0.0"}` |
| **Response (admin)** | `{status: "ok", version: "1.0.0", db: "connected", php: "8.4.10", PHP Laravel for backend and Py9thonk Fast API for evertthin g else: "6.x", cache: "redis_ok", disk_usage: "12GB/50GB", last_nudger_run: "ISO8601"}` |

### `system.metrics`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/system/metrics` |
| **ACL** | ADMIN |
| **Response** | `{papers: {total, published, under_review}, reviews: {total, avg_turnaround_days}, api: {calls_24h, error_rate}, storage: {total_bytes, papers_count}}` |

### `system.maintenance.enable`
| | |
|---|---|
| **Method** | POST |
| **Route** | `/system/maintenance` |
| **ACL** | ADMIN |
| **Request body** | `{enabled: true, message: "Maintenance in progress"}` |
| **Action Log** | `MAINTENANCE_ENABLED` |

### `system.maintenance.disable`
| | |
|---|---|
| **Method** | POST |
| **Route** | `/system/maintenance` |
| **ACL** | ADMIN |
| **Request body** | `{enabled: false}` |
| **Action Log** | `MAINTENANCE_DISABLED` |

---

## TIER 12 — API + EXTERNAL ACCESS (7 endpoints)

> Depends on: Tier 9 (logging)

---

### `api.keys.create`
| | |
|---|---|
| **Method** | POST |
| **Route** | `/api/keys` |
| **ACL** | ADMIN |
| **Tables** | `eaiou_api_keys` INSERT |
| **Request body** | `{user_id, description, access_level}` |
| **Logic** | Generate random API key → hash with SHA256 → store hash only. Return raw key ONCE in response (never stored). |
| **Response** | `{id, api_key: "eaiou_live_abc123...", access_level, status: "active"}` |
| **Action Log** | `API_KEY_CREATED: user_id={id}, access_level={level}` |

### `api.keys.list`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/api/keys` |
| **ACL** | ADMIN |
| **Tables** | `eaiou_api_keys` |
| **Response** | Array of keys (masked: show last 4 chars only), description, access_level, status, last_used |

### `api.keys.revoke`
| | |
|---|---|
| **Method** | PATCH |
| **Route** | `/api/keys/{id}/revoke` |
| **ACL** | ADMIN |
| **Tables** | `eaiou_api_keys` UPDATE status='revoked' |
| **Action Log** | `API_KEY_REVOKED: key_id={id}` |

### `api.logs.list`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/api/logs` |
| **ACL** | ADMIN |
| **Notes** | Alias for `log.get_api_logs` |

### `api.webhook.gitgap`
| | |
|---|---|
| **Method** | POST |
| **Route** | `/webhooks/gitgap` |
| **ACL** | Validated by webhook secret (not user auth) |
| **Request body** | GitGap payload (gap updates, stall notifications) |
| **Side effects** | Update gap data. Log webhook receipt. |
| **Action Log** | `WEBHOOK_RECEIVED: source=gitgap` |

### `api.webhook.retry`
| | |
|---|---|
| **Method** | POST |
| **Route** | `/admin/webhooks/{id}/retry` |
| **ACL** | ADMIN |
| **Notes** | Re-fire a failed webhook. Log retry attempt. |

### `api.rate_limit.check`
| | |
|---|---|
| **Method** | GET |
| **Route** | `/api/rate_limit` |
| **ACL** | AUTH |
| **Response** | `{limit: 1000, remaining: 847, reset_at: "ISO8601", window: "1h"}` |

---

## ENDPOINT COUNT SUMMARY

| Tier | Name | Endpoints |
|------|------|-----------|
| 1 | Core System | 16 |
| 2 | Review + Workflow | 9 |
| 3 | Authorship + AI | 7 |
| 4 | Transparency + Remsearch | 5 |
| 5 | Discovery + Search | 7 |
| 6 | Gap / GitGap | 7 |
| 7 | Versioning + Integrity | 4 |
| 8 | Admin Control | 8 |
| 9 | Logging + Audit | 7 |
| 10 | Notifications | 4 |
| 11 | System + Infrastructure | 4 |
| 12 | API + External Access | 7 |
| **TOTAL** | | **85** |

(2 endpoints are aliases: `log.hash_chain` → `system.hash.verify`, `api.logs.list` → `log.get_api_logs`. Unique implementations: 83.)

---

## BUILD CHECKLIST

Claude Code: implement and test each tier before proceeding to the next.

### Tier 1 — Core System
- [ ] paper.get
- [ ] paper.list (verify q_signal sort, verify NO date sort accepted)
- [ ] paper.create
- [ ] paper.update
- [ ] workflow.get_state
- [ ] workflow.transition (verify temporal sealing on submit)
- [ ] contribution.create
- [ ] contribution.list_by_paper
- [ ] intellid.create
- [ ] intellid.list
- [ ] user.get
- [ ] user.list
- [ ] qscore.compute (verify weight formula, verify denormalization)
- [ ] qscore.get
- [ ] auth.login
- [ ] auth.check_permission

### Tier 2 — Review + Workflow
- [ ] review.assign
- [ ] review.submit (verify q_signal recomputation trigger)
- [ ] review.get
- [ ] review.list_by_paper (verify openreports mode filtering)
- [ ] workflow.assign_reviewers
- [ ] workflow.request_revision
- [ ] workflow.accept (verify capstone trigger)
- [ ] workflow.reject (verify tombstone, never hard-delete)
- [ ] review.get_rubric

### Tier 3 — Authorship + AI
- [ ] contribution.update
- [ ] contribution.delete (verify tombstone)
- [ ] intellid.get
- [ ] intellid.get_contributions (verify redaction filtering)
- [ ] ai.log_session
- [ ] ai.get_sessions
- [ ] ai.get_disclosure

### Tier 4 — Transparency + Remsearch
- [ ] transparency.get
- [ ] transparency.update
- [ ] transparency.add_source
- [ ] transparency.mark_unused
- [ ] transparency.get_completeness

### Tier 5 — Discovery + Search
- [ ] search.query (verify q_signal sort only)
- [ ] search.unspace
- [ ] discover.papers
- [ ] discover.ideas
- [ ] discover.gaps
- [ ] discover.trends
- [ ] discover.collaboration

### Tier 6 — Gap / GitGap
- [ ] gap.get
- [ ] gap.list
- [ ] gap.create
- [ ] gap.update
- [ ] gap.get_linked_papers
- [ ] gap.get_stalled_items
- [ ] gap.sync_external

### Tier 7 — Versioning + Integrity
- [ ] paper.get_versions (verify sealed dates stripped)
- [ ] paper.create_version (verify content_hash computed)
- [ ] paper.get_integrity_chain
- [ ] system.hash.verify

### Tier 8 — Admin Control
- [ ] admin.dashboard
- [ ] admin.users.list
- [ ] admin.users.update
- [ ] admin.papers.override_status (verify Action Log)
- [ ] admin.settings.get
- [ ] admin.settings.update
- [ ] admin.qscore.config
- [ ] admin.workflow.config

### Tier 9 — Logging + Audit
- [ ] log.api_call (verify hash chain: log_hash + prior_hash)
- [ ] log.notification
- [ ] log.webhook
- [ ] log.get_api_logs
- [ ] log.get_webhook_logs
- [ ] log.get_notification_logs
- [ ] log.hash_chain

### Tier 10 — Notifications
- [ ] notification.send
- [ ] notification.list
- [ ] notification.mark_read
- [ ] notification.preview_email

### Tier 11 — System + Infrastructure
- [ ] system.health
- [ ] system.metrics
- [ ] system.maintenance.enable
- [ ] system.maintenance.disable

### Tier 12 — API + External Access
- [ ] api.keys.create (verify raw key returned once, hash stored)
- [ ] api.keys.list (verify key masking)
- [ ] api.keys.revoke
- [ ] api.logs.list
- [ ] api.webhook.gitgap
- [ ] api.webhook.retry
- [ ] api.rate_limit.check

---

*End of EAIOU API Build Plan v1.0.0*
*87 endpoints · 12 tiers · strict build order*
*ORCID: 0009-0006-5944-1742 — Eric D. Martin*
*Temporal Blindness enforced. q_signal is the river.*
