# EAIOU — MCP Orchestration Build Plan (Claude Code Lockfile)

**Version:** 1.0.0 — 2026-04-12
**Author:** Eric D. Martin — ORCID: 0009-0006-5944-1742
**Purpose:** This document defines the MCP (Model Context Protocol) orchestration layer for eaiou. MCP sits BETWEEN the frontend views and the backend. Every frontend action calls an MCP tool. MCP enforces rules, ACL, and doctrine BEFORE the backend executes. Claude Code MUST implement MCP tools in the order specified.
**Companions:** `EAIOU_FRONTEND_BUILD_PLAN.md` · `EAIOU_BACKEND_BUILD_PLAN.md` · `EAIOU_API_BUILD_PLAN.md`
**Status:** CANONICAL

---

## 0. RULES FOR CLAUDE CODE

1. **MCP is the enforcement layer.** The frontend NEVER talks directly to the database. Frontend → MCP → Backend.
2. **Every MCP tool checks ACL before execution.** If the caller lacks permission, return `{error: "forbidden", code: 403}` immediately.
3. **Every MCP tool that touches papers checks Temporal Blindness.** Strip sealed fields before returning data to any non-governance caller.
4. **Every mutating MCP tool writes an Action Log entry.** No silent mutations.
5. **MCP tools are grouped into 18 namespaces.** Each namespace maps to a backend domain. Do not cross namespace boundaries — a `paper.*` tool never directly queries `review_logs` without going through `review.*`.
6. **Build MCP tool groups in tier order.** Tier 1 must be complete before Tier 2 begins.
7. **Every MCP tool has a defined input schema, output schema, and error set.** No untyped tools.
8. **MCP tools that combine multiple backend calls are composites.** Document which sub-calls they make.

---

## 1. WHERE MCP SITS

```
┌─────────────────────────────┐
│     FRONTEND (37 views)     │
│  React/HTML/laravel php and fast api pythion for everythign else tmpl     │
└─────────────┬───────────────┘
              │ calls MCP tools
              ▼
┌─────────────────────────────┐
│         MCP LAYER           │
│  • ACL enforcement          │
│  • Temporal Blindness       │
│  • Input validation         │
│  • Rule orchestration       │
│  • Action Log writes        │
│  • Composite operations     │
└─────────────┬───────────────┘
              │ calls backend
              ▼
┌─────────────────────────────┐
│   BACKEND (laravel php and fast api pythion for everythign else + REST)   │
│  • com_eaiou (11 tables)    │
│  • 11 plugins               │
│  • 5 modules                │
│  • laravel php and fast api pythion for everythign else core (articles,   │
│    workflows, custom fields,│
│    tags, action logs)        │
└─────────────────────────────┘
```

**MCP enforces BEFORE backend executes:**
- ACL: Does this user have permission?
- Temporal Blindness: Are sealed fields being requested by a non-governance user?
- Validation: Is the input well-formed?
- Business rules: Can this workflow transition happen? Are plugin guards satisfied?
- Logging: Record the action before returning

---

## 2. MCP TOOL NAMESPACES (18 groups)

| # | Namespace | Tool Count | Backend Domain |
|---|-----------|-----------|----------------|
| 1 | `paper.*` | 14 | eaiou_papers + #__content |
| 2 | `review.*` | 9 | eaiou_review_logs + Custom Fields (Deadlines) |
| 3 | `user.*` | 10 | #__users + User Custom Fields |
| 4 | `intellid.*` | 6 | eaiou_ai_sessions |
| 5 | `contribution.*` | 7 | eaiou_attribution_log |
| 6 | `gap.*` | 8 | Aggregated from rs:Stalled tags + external GitGap |
| 7 | `workflow.*` | 8 | laravel php and fast api pythion for everythign else Workflows + eaiou_papers.status |
| 8 | `qscore.*` | 5 | eaiou_quality_signals + eaiou_papers.q_signal |
| 9 | `transparency.*` | 5 | Custom Fields (Transparency) + eaiou_remsearch |
| 10 | `ai.*` | 5 | eaiou_ai_sessions + Custom Fields (AI Usage) + eaiou_didntmakeit |
| 11 | `search.*` | 2 | Smart Search + eaiou_remsearch + Tags |
| 12 | `discover.*` | 7 | Aggregations across papers, tags, remsearch |
| 13 | `notification.*` | 4 | laravel php and fast api pythion for everythign else Mail Templates + Action Logs |
| 14 | `admin.*` | 13 | All tables + system config |
| 15 | `system.*` | 6 | Infrastructure + hash chain |
| 16 | `auth.*` | 8 | #__users + eaiou_api_keys |
| 17 | `log.*` | 7 | eaiou_api_logs + Action Logs |
| 18 | `api.*` | 7 | eaiou_api_keys + eaiou_api_logs + webhooks |
| | **TOTAL** | **136** | |

---

## 3. COMPLETE MCP TOOL SPECIFICATIONS

### 3.1 `paper.*` — Core Paper Object (14 tools)

#### `paper.get`
| Field | Value |
|-------|-------|
| Input | `{id: int}` |
| ACL | PUBLIC (published), AUTHOR (own drafts), EDITOR+ (any state) |
| Output | Full paper object: title, abstract, authors_json, authorship_mode, status, q_signal, badges, article content. **NO sealed dates unless governance caller.** |
| Backend | GET `/api/v1/eaiou/papers/{id}` + GET `#__content` article |
| Temporal Blindness | Strip submission_sealed_at, acceptance_sealed_at, publication_sealed_at |
| View mapping | VIEW 03 (Paper Detail), VIEW 19 (Reviewer Paper), VIEW 21 (Editorial Paper) |

#### `paper.list`
| Field | Value |
|-------|-------|
| Input | `{filters: {category?, authorship_mode?, status?, include_nottopic?}, limit: 20, offset: 0}` |
| ACL | PUBLIC |
| Output | Paginated array of paper summaries sorted by `q_signal DESC` |
| **SORT RULE** | **q_signal DESC ONLY. If caller passes sort=date, return error 400: "Temporal Blindness violation: date sorting not permitted."** |
| Backend | GET `/api/v1/eaiou/papers` |
| View mapping | VIEW 01 (Home), VIEW 02 (Papers List) |

#### `paper.search`
| Field | Value |
|-------|-------|
| Input | `{query: string, filters: {...}, include_unspace: bool}` |
| ACL | PUBLIC |
| Output | Search results sorted by q_signal DESC, with un-space results if toggled |
| Backend | GET `/api/v1/eaiou/search` + Smart Search |
| View mapping | VIEW 04 (Search) |

#### `paper.create`
| Field | Value |
|-------|-------|
| Input | `{title, abstract, authorship_mode, authors_json, keywords, catid}` |
| ACL | AUTHOR |
| Output | Created paper with id, paper_uuid |
| Side effects | Generate paper_uuid. Create #__content article. Write Action Log. |
| View mapping | VIEW 09 (Submit Step 1) |

#### `paper.update`
| Field | Value |
|-------|-------|
| Input | `{id: int, data: {partial fields}}` |
| ACL | OWNER or EDITOR |
| Validation | Cannot update sealed fields. Cannot update q_signal directly. |
| Action Log | `PAPER_UPDATED: paper_id={id}` |

#### `paper.delete`
| Field | Value |
|-------|-------|
| Input | `{id: int}` |
| ACL | ADMIN only |
| **RULE** | **TOMBSTONE ONLY. Sets state = -2 (trashed). NEVER hard-deletes.** |
| Action Log | `PAPER_TOMBSTONED: paper_id={id}` |

#### `paper.get_versions`
| Field | Value |
|-------|-------|
| Input | `{paper_id: int}` |
| ACL | PUBLIC |
| Output | Array of versions: label, ai_flag, content_hash. **generated_at stripped for non-governance callers.** |
| View mapping | VIEW 03 sidebar (Version History) |

#### `paper.create_version`
| Field | Value |
|-------|-------|
| Input | `{paper_id: int, label: string, file?, ai_flag: bool, ai_model_name?, notes?}` |
| ACL | AUTHOR (own) or EDITOR |
| Side effects | Compute content_hash. Store file under /media/com_eaiou/{uuid}/versions/{label}/. Increment submission_version. |
| View mapping | VIEW 16 (Paper Revise) |

#### `paper.get_workflow`
| Field | Value |
|-------|-------|
| Input | `{paper_id: int}` |
| ACL | PUBLIC (current state name), EDITOR+ (transitions + history) |
| Output | `{current_state, available_transitions?, history?}` |
| Composite | Calls `workflow.get_state` + `workflow.get_history` |

#### `paper.get_integrity_chain`
| Field | Value |
|-------|-------|
| Input | `{paper_id: int}` |
| ACL | PUBLIC |
| Output | `{sealed_hash, capstone_doi, version_hashes: [...]}` — **NO sealed dates** |
| View mapping | VIEW 03 sidebar (Integrity Chain) |

#### `paper.link_gap`
| Field | Value |
|-------|-------|
| Input | `{paper_id: int, gap_id: int}` |
| ACL | AUTHOR or EDITOR |
| Action Log | `GAP_LINKED: paper_id={id}, gap_id={id}` |

#### `paper.unlink_gap`
| Field | Value |
|-------|-------|
| Input | `{paper_id: int, gap_id: int}` |
| ACL | AUTHOR or EDITOR |

#### `paper.get_transparency`
| Field | Value |
|-------|-------|
| Input | `{paper_id: int}` |
| ACL | PUBLIC |
| Composite | Calls `transparency.get` |
| View mapping | VIEW 03 (Transparency Block) |

#### `paper.get_ai_usage`
| Field | Value |
|-------|-------|
| Input | `{paper_id: int}` |
| ACL | PUBLIC (display_level controlled), REVIEWER+ (always full) |
| Composite | Calls `ai.get_disclosure` |
| View mapping | VIEW 03 (AI Usage Block) |

---

### 3.2 `review.*` — Peer Review (9 tools)

#### `review.assign`
| Field | Value |
|-------|-------|
| Input | `{paper_id, reviewer_id, due_date, notes?}` |
| ACL | EDITOR |
| Side effects | Update Deadlines custom field. Send invite email. Set invite_status=Pending. |
| Action Log | `REVIEWER_ASSIGNED` |

#### `review.unassign`
| Field | Value |
|-------|-------|
| Input | `{paper_id, reviewer_id}` |
| ACL | EDITOR |
| Side effects | Set invite_status=Replaced in Deadlines field. |
| Action Log | `REVIEWER_UNASSIGNED` |

#### `review.submit`
| Field | Value |
|-------|-------|
| Input | `{paper_id, reviewer_id, rubric_overall, rubric_originality, rubric_methodology, rubric_transparency, rubric_ai_disclosure, rubric_crossdomain, recommendation, review_notes, labels_json?, unsci_flagged, open_consent}` |
| ACL | ASSIGNED REVIEWER |
| Validation | All rubric scores 0–10. Recommendation must be valid. Reviewer must be assigned. |
| Side effects | INSERT eaiou_review_logs. INSERT eaiou_quality_signals. **Trigger `qscore.compute`.** If all reviewers done → transition to decision_pending. |
| Action Log | `REVIEW_SUBMITTED` |
| View mapping | VIEW 18 (Review Console) |

#### `review.save_draft`
| Field | Value |
|-------|-------|
| Input | `{paper_id, reviewer_id, partial_data}` |
| ACL | ASSIGNED REVIEWER |
| Notes | Saves partial review in session/temp storage. Does NOT create eaiou_review_logs record. Does NOT trigger qscore. |

#### `review.get`
| Field | Value |
|-------|-------|
| Input | `{paper_id, reviewer_id}` |
| ACL | REVIEWER (own), EDITOR+ (any) |
| Output | Review record with scores, notes, recommendation |

#### `review.list_by_paper`
| Field | Value |
|-------|-------|
| Input | `{paper_id}` |
| ACL | EDITOR+ (full), PUBLIC (filtered by openreports mode) |
| Output | Array of reviews. Public response filtered by or_mode (strip identity if anonymous, strip body if summary-only). |
| View mapping | VIEW 03 (Open Reports Block), VIEW 23 (Editorial Decision) |

#### `review.list_by_reviewer`
| Field | Value |
|-------|-------|
| Input | `{reviewer_id}` |
| ACL | REVIEWER (own), ADMIN |
| Output | All reviews by this reviewer across papers |
| View mapping | VIEW 17 (Reviewer Queue — completed tab) |

#### `review.flag_unsci`
| Field | Value |
|-------|-------|
| Input | `{paper_id, reviewer_id, scope, reason, notes, risk_level}` |
| ACL | REVIEWER or EDITOR |
| Side effects | Set unsci_active=true in Un Scientific custom field. Add entry to unsci_entries. Auto-tag article with `un-scientific`. |
| Action Log | `UNSCI_FLAGGED` |

#### `review.get_rubric`
| Field | Value |
|-------|-------|
| Input | none |
| ACL | PUBLIC |
| Output | `{dimensions: [{name, weight, min, max}], transparency_multiplier: 1.5}` |
| View mapping | VIEW 17 sidebar (Rubric Guide), VIEW 18 (rubric form) |

---

### 3.3 `user.*` — User/Role Management (10 tools)

#### `user.get`
| Input | `{id}` | ACL | AUTH (own), EDITOR+ (any) |
#### `user.list`
| Input | `{filters: {group?, has_orcid?}}` | ACL | EDITOR+ |
#### `user.create`
| Input | `{name, email, password, groups?}` | ACL | ADMIN |
#### `user.update`
| Input | `{id, data}` | ACL | AUTH (own profile), ADMIN (any) |
#### `user.delete`
| Input | `{id}` | ACL | ADMIN | **RULE: Tombstone only. Block/disable, never hard-delete.** |
#### `user.assign_role`
| Input | `{user_id, role}` | ACL | ADMIN | Side effects: Add to laravel php and fast api pythion for everythign else user group |
#### `user.remove_role`
| Input | `{user_id, role}` | ACL | ADMIN |
#### `user.link_orcid`
| Input | `{user_id, orcid_id}` | ACL | AUTH (own) | Side effects: OAuth flow via plg_system_orcid_link |
#### `user.unlink_orcid`
| Input | `{user_id}` | ACL | AUTH (own) |
#### `user.get_activity`
| Input | `{user_id}` | ACL | AUTH (own), EDITOR+ | Output: papers submitted, reviews completed, q_signal avg |

---

### 3.4 `intellid.*` — AI + Human Entity System (6 tools)

#### `intellid.get`
| Input | `{id}` | ACL | REVIEWER+ |
#### `intellid.list`
| Input | `{filters: {paper_id?, model?}}` | ACL | REVIEWER+ |
#### `intellid.create`
| Input | `{paper_id, session_label, ai_model_name, tokens_in?, tokens_out?, session_notes?, answer_box_session_id?}` | ACL | AUTHOR or API_CLIENT |
#### `intellid.update`
| Input | `{id, data}` | ACL | AUTHOR (own session) or EDITOR |
#### `intellid.get_contributions`
| Input | `{session_id}` | ACL | EIC+ (full content), REVIEWER (metadata + exclusion_reason only, prompt/response NULL if redacted) |
| Tables | eaiou_didntmakeit WHERE session_id |
#### `intellid.get_activity`
| Input | `{intellid_id}` | ACL | REVIEWER+ | Output: all sessions, token totals, papers involved |

---

### 3.5 `contribution.*` — Authorship Core (7 tools)

#### `contribution.create`
| Input | `{paper_id, contributor_name, orcid?, role_description, contribution_type, is_human, is_ai, ai_tool_used?, version_id?}` | ACL | AUTHOR (own) or EDITOR |
#### `contribution.update`
| Input | `{id, data}` | ACL | OWNER or EDITOR |
#### `contribution.delete`
| Input | `{id}` | ACL | EDITOR | **TOMBSTONE ONLY (state = -2)** |
#### `contribution.list_by_paper`
| Input | `{paper_id}` | ACL | PUBLIC |
#### `contribution.list_by_intellid`
| Input | `{intellid_id}` | ACL | REVIEWER+ | Output: all attribution entries for this AI model/entity |
#### `contribution.compute_weights`
| Input | `{paper_id}` | ACL | EDITOR | Notes: Compute relative contribution weights from attribution entries. Advisory only — does not override author declarations. |

---

### 3.6 `gap.*` — Gap / GitGap System (8 tools)

#### `gap.get`
| Input | `{id}` | ACL | PUBLIC |
#### `gap.list`
| Input | `{filters: {domain?}}` | ACL | PUBLIC | Sort: stall_density DESC |
#### `gap.create`
| Input | `{domain, description, stall_type?, linked_paper_ids?}` | ACL | EDITOR |
#### `gap.update`
| Input | `{id, data}` | ACL | EDITOR |
#### `gap.get_linked_papers`
| Input | `{gap_id}` | ACL | PUBLIC |
#### `gap.get_stalled_items`
| Input | `{gap_id}` | ACL | PUBLIC | Output: breakdown by rs:Stalled subtype |
#### `gap.analyze`
| Input | `{domain}` | ACL | EDITOR | Notes: Auto-detect gaps from unresolved rs:Stalled tags in the domain. Returns proposed gaps. Does NOT auto-create — editor confirms. |
#### `gap.sync_external`
| Input | none | ACL | ADMIN | Side effects: Trigger GitGap webhook sync. Log result. |

---

### 3.7 `workflow.*` — State Machine (8 tools)

#### `workflow.get_state`
| Input | `{paper_id}` | ACL | PUBLIC (state name), EDITOR+ (transitions) |
#### `workflow.transition`
| Input | `{paper_id, target_state, notes?}` | ACL | Role-dependent (see state machine) |
| **CRITICAL** | If target=submitted → **TEMPORAL SEALING EVENT.** If target=accepted → **CAPSTONE TRIGGER.** |
#### `workflow.assign_reviewers`
| Input | `{paper_id, reviewers: [{user_id, due_date}]}` | ACL | EDITOR |
| Composite | Calls `review.assign` per reviewer. Transitions paper to under_review. |
#### `workflow.request_revision`
| Input | `{paper_id, notes, due_date}` | ACL | EDITOR |
#### `workflow.accept`
| Input | `{paper_id, editor_notes?}` | ACL | EDITOR |
| Side effects | Set acceptance_sealed_at. Queue Zenodo deposition. |
#### `workflow.reject`
| Input | `{paper_id, reason, editor_notes?}` | ACL | EDITOR |
| **RULE** | Tombstone to archived. NEVER hard-delete. Paper remains searchable. |
#### `workflow.publish`
| Input | `{paper_id}` | ACL | EDITOR |
| Side effects | Set publication_sealed_at. Transition to published. Trigger mod_latest_papers refresh. |
| **Plugin guards fire:** | transparency complete? AI log complete? unsci resolved? |
#### `workflow.get_history`
| Input | `{paper_id}` | ACL | EDITOR+ | Output: Full transition log with timestamps (governance-only timestamps) |

---

### 3.8 `qscore.*` — Quality Signal (5 tools)

#### `qscore.compute`
| Input | `{paper_id}` | ACL | EDITOR or SYSTEM |
| Logic | Average all quality_signals → apply weights (transparency ×1.5) → composite → denormalize to eaiou_papers.q_signal |
#### `qscore.get`
| Input | `{paper_id}` | ACL | PUBLIC |
| Output | `{q_signal, breakdown: {overall, originality, methodology, transparency, ai_disclosure, crossdomain}, review_count}` |
#### `qscore.breakdown`
| Input | `{paper_id}` | ACL | PUBLIC | Notes: Alias for qscore.get with full dimension detail |
#### `qscore.update_weights`
| Input | `{weights: {overall, originality, methodology, transparency, ai_disclosure, crossdomain}}` | ACL | ADMIN |
| Side effects | **Triggers batch recomputation of ALL q_signals.** |
#### `qscore.validate`
| Input | `{paper_id}` | ACL | EDITOR | Output: Whether q_signal is consistent with current review data |

---

### 3.9 `transparency.*` — Transparency + Remsearch (5 tools)

#### `transparency.get`
| Input | `{paper_id}` | ACL | PUBLIC |
#### `transparency.update`
| Input | `{paper_id, data}` | ACL | AUTHOR (own) or EDITOR |
#### `transparency.add_source`
| Input | `{paper_id, citation_title, citation_source?, citation_link?, source_type, used, reason_unused?}` | ACL | AUTHOR |
#### `transparency.mark_unused`
| Input | `{source_id, reason}` | ACL | AUTHOR or EDITOR |
#### `transparency.get_completeness`
| Input | `{paper_id}` | ACL | AUTHOR or EDITOR | Output: `{complete, missing_fields, sources_count, excluded_without_reason}` |

---

### 3.10 `ai.*` — AI / MCP-Aware Operations (5 tools)

#### `ai.log_session`
| Input | `{paper_id, model, usage_type, summary, tokens_in?, tokens_out?}` | ACL | AUTHOR or API_CLIENT |
#### `ai.get_sessions`
| Input | `{paper_id}` | ACL | REVIEWER+ |
#### `ai.generate_review`
| Input | `{paper_id}` | ACL | EDITOR |
| Notes | **Controlled AI reviewer.** Generates a draft review using the paper content. Returns draft — does NOT auto-submit. Editor must review and approve before it becomes a real review. Logged as AI session. |
| Action Log | `AI_REVIEW_GENERATED: paper_id={id}` |
#### `ai.assist_submission`
| Input | `{paper_id, step: "metadata"|"triage"|"ai_usage"|"declarations"}` | ACL | AUTHOR |
| Notes | AI assistant that helps author fill submission wizard fields. Returns suggestions — author accepts/rejects. Logged as AI session. |
#### `ai.get_disclosure`
| Input | `{paper_id}` | ACL | PUBLIC (display_level filtered), REVIEWER+ (always full) |

---

### 3.11 `search.*` — Search (2 tools)

#### `search.query`
| Input | `{query, filters, limit, offset}` | ACL | PUBLIC | Sort: q_signal DESC |
#### `search.unspace`
| Input | `{query, tag_type?}` | ACL | PUBLIC | Notes: Search un-space (excluded sources, NotTopic artifacts, didntmakeit metadata) |

---

### 3.12 `discover.*` — Discovery (7 tools)

#### `discover.papers`
| Input | `{filters}` | ACL | PUBLIC | Notes: Curated paper list (alias for paper.list with published + badge enrichment) |
#### `discover.ideas`
| Input | `{domain?, min_entropy?}` | ACL | PUBLIC | Output: Entropy-novelty ranked ideas from un-space |
#### `discover.gaps`
| Input | `{domain?}` | ACL | PUBLIC | Output: Gap map data (stall density by domain + type) |
#### `discover.trends`
| Input | none | ACL | PUBLIC |
#### `discover.collaboration`
| Input | `{collab_type?, interest_level?}` | ACL | PUBLIC |
#### `discover.get_entropy_score`
| Input | `{item_id}` | ACL | PUBLIC | Output: Entropy-novelty score for a specific un-space artifact |

---

### 3.13 `notification.*` (4 tools)

#### `notification.send`
| Notes | INTERNAL — triggered by workflow transitions and deadline_nudger |
#### `notification.list`
| Input | `{user_id?}` | ACL | AUTH (own) |
#### `notification.mark_read`
| Input | `{id}` | ACL | AUTH (own) |
#### `notification.preview_email`
| Input | `{template_id, paper_id?, user_id?}` | ACL | ADMIN |

---

### 3.14 `admin.*` — Full Control Surface (13 tools)

#### `admin.dashboard`
| ACL | EDITOR+ | Output: KPIs, system health, activity summary |
#### `admin.users.list`
| ACL | ADMIN |
#### `admin.users.update`
| ACL | ADMIN |
#### `admin.papers.override_status`
| Input | `{paper_id, status, reason, bypass_guards: true}` | ACL | EIC or ADMIN |
| **WARNING** | Bypasses plugin guards. Must provide reason. Logged. |
#### `admin.papers.export`
| Input | `{filters, format: "csv"|"json"}` | ACL | ADMIN |
#### `admin.reviewers.performance`
| ACL | EDITOR+ | Output: Per-reviewer metrics (assigned, completed, on-time %, avg turnaround) |
#### `admin.reviewers.list`
| ACL | EDITOR+ | Output: All users in eaiou_Reviewer group with activity stats |
#### `admin.gaps.sync`
| ACL | ADMIN | Composite: Calls `gap.sync_external` |
#### `admin.gaps.manage`
| ACL | EDITOR | Notes: CRUD interface for manually created gaps |
#### `admin.settings.get`
| ACL | ADMIN |
#### `admin.settings.update`
| ACL | ADMIN |
#### `admin.qscore.config`
| ACL | ADMIN | Notes: Get/update q_signal weights. Triggers batch recomputation. |
#### `admin.workflow.config`
| ACL | ADMIN | Output: Current state machine, transitions, guard rules |
#### `admin.scheduler.status`
| ACL | ADMIN | Output: Last nudger run, next scheduled, emails sent, dry-run status |

---

### 3.15 `system.*` — Infrastructure (6 tools)

#### `system.health`
| ACL | PUBLIC (basic), ADMIN (detailed) |
#### `system.hash.verify`
| ACL | ADMIN | Notes: Walk API log hash chain, verify integrity |
#### `system.hash.rebuild`
| ACL | ADMIN | Notes: Recompute all log_hash values from scratch. **DESTRUCTIVE — only for recovery.** Logged as critical event. |
#### `system.maintenance.enable`
| ACL | ADMIN |
#### `system.maintenance.disable`
| ACL | ADMIN |
#### `system.metrics`
| ACL | ADMIN |

---

### 3.16 `auth.*` — Authentication + Access (8 tools)

#### `auth.login`
| Input | `{username, password}` or `{orcid_token}` | ACL | PUBLIC |
#### `auth.logout`
| ACL | AUTH |
#### `auth.register`
| Input | `{name, email, password}` | ACL | PUBLIC | Notes: Creates Registered user. Author role must be requested/assigned separately. |
#### `auth.check_permission`
| Input | `{user_id, action, paper_id?}` | ACL | AUTH |
#### `auth.get_roles`
| Input | `{user_id}` | ACL | AUTH (own), ADMIN (any) |
#### `auth.api_key.create`
| ACL | ADMIN | Output: Raw key (returned ONCE), hash stored |
#### `auth.api_key.revoke`
| ACL | ADMIN |
#### `auth.api_key.list`
| ACL | ADMIN | Notes: Keys masked (last 4 chars only) |

---

### 3.17 `log.*` — Logging + Audit (7 tools)

#### `log.api_call`
| Notes | INTERNAL — auto-called on every API request. Computes log_hash + prior_hash. APPEND ONLY. |
#### `log.notification`
| Notes | INTERNAL — called by nudger and workflow events |
#### `log.webhook`
| Notes | INTERNAL — called by GitGap webhook handler |
#### `log.get_api_logs`
| Input | `{filters: {endpoint?, response_code?, from?, to?}, limit}` | ACL | ADMIN |
#### `log.get_webhook_logs`
| ACL | ADMIN |
#### `log.get_notification_logs`
| ACL | ADMIN |
#### `log.hash_chain`
| ACL | ADMIN | Notes: Alias for system.hash.verify |

---

### 3.18 `api.*` — External Access (7 tools)

#### `api.keys.create`
| ACL | ADMIN | Side effects: Generate key → SHA256 hash → store hash. Return raw key ONCE. |
#### `api.keys.list`
| ACL | ADMIN | Notes: Masked keys |
#### `api.keys.revoke`
| ACL | ADMIN |
#### `api.logs.list`
| ACL | ADMIN | Alias for log.get_api_logs |
#### `api.rate_limit.check`
| ACL | AUTH | Output: `{limit, remaining, reset_at, window}` |
#### `api.webhook.gitgap`
| ACL | Webhook secret auth | Notes: Receive GitGap payload, process gap updates |
#### `api.webhook.retry`
| Input | `{webhook_id}` | ACL | ADMIN |

---

## 4. VIEW → MCP TOOL MAPPING

This maps every frontend view to the MCP tools it calls. Claude Code: when building a view, these are the ONLY data sources.

| View | MCP Tools Called |
|------|----------------|
| VIEW 01 — Home | `paper.list`, `discover.gaps`, `discover.collaboration`, `discover.trends` |
| VIEW 02 — Papers List | `paper.list`, `discover.gaps`, `discover.collaboration` |
| VIEW 03 — Paper Detail | `paper.get`, `qscore.breakdown`, `transparency.get`, `ai.get_disclosure`, `contribution.list_by_paper`, `paper.get_versions`, `paper.get_integrity_chain`, `review.list_by_paper` |
| VIEW 04 — Search | `search.query`, `search.unspace`, `discover.ideas`, `discover.gaps` |
| VIEW 05 — Discover Ideas | `discover.ideas`, `discover.gaps`, `search.unspace` |
| VIEW 06 — Discover Gaps | `discover.gaps`, `gap.list`, `gap.get_stalled_items`, `discover.collaboration` |
| VIEW 07 — Discover Trends | `discover.trends`, `discover.gaps` |
| VIEW 08 — Discover Open | `discover.collaboration`, `discover.gaps` |
| VIEW 09 — Submit Step 1 | `paper.create` |
| VIEW 10 — Submit Step 2 | `paper.create_version` |
| VIEW 11 — Submit Step 3 | `ai.log_session`, `ai.assist_submission` |
| VIEW 12 — Submit Step 4 | `transparency.add_source`, `transparency.get_completeness` |
| VIEW 13 — Submit Step 5 | `contribution.create` |
| VIEW 14 — Submit Step 6 | `transparency.get_completeness`, `ai.get_disclosure`, `workflow.transition` (submit) |
| VIEW 15 — My Papers | `paper.list` (filtered by OWNER), `notification.list`, `qscore.get` |
| VIEW 16 — Paper Revise | `paper.get`, `paper.create_version`, `review.list_by_paper` |
| VIEW 17 — Reviewer Queue | `review.list_by_reviewer`, `review.get_rubric`, `user.get_activity` |
| VIEW 18 — Review Console | `paper.get`, `review.submit`, `review.save_draft`, `review.flag_unsci`, `ai.get_sessions`, `transparency.get` |
| VIEW 19 — Reviewer Paper | `paper.get`, `qscore.breakdown`, `ai.get_sessions`, `paper.get_integrity_chain` |
| VIEW 20 — Editorial Papers | `admin.dashboard`, `paper.list` (all states), `admin.reviewers.performance` |
| VIEW 21 — Editorial Paper | `paper.get`, `workflow.get_state`, `review.list_by_paper`, `paper.get_integrity_chain` |
| VIEW 22 — Reviewer Assignment | `workflow.assign_reviewers`, `user.list` (reviewers), `review.assign` |
| VIEW 23 — Editorial Decision | `review.list_by_paper`, `workflow.accept`, `workflow.reject`, `workflow.request_revision`, `workflow.publish`, `paper.get_integrity_chain` |
| VIEW 24 — Admin Dashboard | `admin.dashboard`, `system.health`, `system.metrics`, `log.get_api_logs`, `admin.scheduler.status` |
| VIEW 25 — API Keys | `api.keys.list`, `api.keys.create`, `api.keys.revoke` |
| VIEW 26 — API Logs | `log.get_api_logs`, `system.hash.verify` |
| VIEW 27 — Users | `admin.users.list`, `user.assign_role`, `user.remove_role` |
| VIEW 28 — Settings | `admin.settings.get`, `admin.settings.update`, `admin.qscore.config`, `admin.workflow.config` |
| VIEW 29 — Login | `auth.login` |
| VIEW 30 — Register | `auth.register` |
| VIEW 31 — ORCID Profile | `user.get`, `user.link_orcid`, `user.unlink_orcid`, `user.get_activity` |

---

## 5. BUILD ORDER

Build MCP tool groups in this order. Each group must be tested before proceeding.

| Phase | Tool Groups | Depends On |
|-------|------------|-----------|
| 1 | `paper.*` (14), `auth.*` (8), `user.*` (10) | Backend Tier 1 |
| 2 | `workflow.*` (8), `qscore.*` (5) | Phase 1 |
| 3 | `review.*` (9), `contribution.*` (7) | Phase 1 + 2 |
| 4 | `transparency.*` (5), `ai.*` (5), `intellid.*` (6) | Phase 1 |
| 5 | `search.*` (2), `discover.*` (7) | Phase 1 + 4 |
| 6 | `gap.*` (8) | Phase 5 |
| 7 | `notification.*` (4), `log.*` (7) | Phase 2 + 3 |
| 8 | `admin.*` (13), `system.*` (6), `api.*` (7) | All above |

---

## 6. ENFORCEMENT RULES (MCP LAYER)

Every MCP tool MUST enforce these before passing to backend:

### 6.1 Temporal Blindness
```
IF caller is NOT (EIC or ADMIN with governance_unlock=true):
    STRIP from response:
        - submission_sealed_at
        - acceptance_sealed_at
        - publication_sealed_at
        - generated_at (on versions)
        - review_sealed_at (on reviews)
    REJECT any sort parameter containing "date", "time", "sealed", "created"
    REJECT any filter on sealed fields
```

### 6.2 ACL Gate
```
IF caller lacks required permission for this tool:
    RETURN {error: "forbidden", code: 403, required: "{permission}"}
    DO NOT execute backend call
```

### 6.3 Tombstone Enforcement
```
ON any delete operation:
    SET state = -2 (trashed)
    NEVER execute DELETE FROM
    WRITE Action Log: "{ENTITY}_TOMBSTONED: id={id}"
```

### 6.4 Action Log
```
ON every mutating operation:
    WRITE to laravel php and fast api pythion for everythign else Action Logs:
        - action type
        - entity type + id
        - user_id
        - timestamp
        - summary (no PII, no raw content)
```

### 6.5 q_signal Sort
```
ON every paper list/search/discover operation:
    ENFORCE ORDER BY q_signal DESC
    IF caller requests date sort:
        RETURN {error: "Temporal Blindness violation", code: 400}
```

---

*End of EAIOU MCP Build Plan v1.0.0*
*136 tools · 18 namespaces · strict build order*
*ORCID: 0009-0006-5944-1742 — Eric D. Martin*
*MCP enforces. Backend executes. The river flows by quality.*
