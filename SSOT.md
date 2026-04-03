EAIOU / eaiou — SSOT Knowledge Dump
Canonical name: eaiou

This file consolidates the knowledge available in the workspace about the eaiou journal platform and related Joomla extension plans.

============================================================
1. Canonical naming and scope
============================================================

Canonical SSOT name: eaiou

Observed naming variants in source material:
- EAIOU.org
- eaiou
- aieou / aieou.org
- com_aieou
- com_eaiou

Best normalized SSOT interpretation:
- Brand/site: eaiou
- Canonical component direction in later specs: com_eaiou
- Namespace: Eaiou
- DB prefix: #__eaiou_
- Media root: /media/com_eaiou/{paper_id}/...
- REST base: /api/index.php/v1/eaiou/...

Important note:
The source notes contain naming drift. Some older/planning notes say “com_aieou”, while later, more canonical notes settle on “com_eaiou”. Since the user requested “eaiou is ssot for the name,” this dump normalizes to eaiou.

============================================================
2. High-level mission
============================================================

eaiou is conceived as an observer-preserving peer review journal and archival platform built on Joomla 5.3 under a core-first philosophy.

Its central idea is:
- preserve the full research context, not just the polished final paper
- archive used and unused research materials
- record AI assistance and excluded AI outputs
- preserve peer review lineage
- support transparency, reproducibility, and discoverability
- annotate rather than delete
- use tombstones instead of hard deletes where possible

The platform is framed as a full-context publication system where authors submit:
- paper metadata
- manuscript versions
- unused artifacts
- AI logs
- literature triage
- reviewer lineage
- attribution data
- plugin/tool usage
- API activity

============================================================
3. Architectural split
============================================================

There are two major architectural layers in the material.

A) Custom journal component layer
This is the journal-specific archival and operational layer built as a Joomla component:
- component name direction: com_eaiou
- holds paper-centric records and linked research artifacts
- supports admin + site MVC
- intended to expose Joomla Web Services / REST endpoints

B) Core-first plugin/module layer
A suite of Joomla plugins/modules that intentionally reuses:
- com_content (Articles)
- Custom Fields
- Workflows
- Tags
- Action Logs
- Scheduler
- Mail Templates
- User Custom Fields
- ACL

The goal of this second layer is to add journal features without replacing Joomla core article systems.

============================================================
4. Core design principles
============================================================

1. Core-first
Use Joomla Articles, ACL, Workflows, Fields, Tags, Scheduler, and Action Logs wherever possible.

2. Annotate, don’t delete
Reviewer/editor actions should label, flag, contextualize, or tombstone artifacts instead of removing them.

3. Full-context preservation
Preserve failed trials, excluded sources, AI outputs, unused datasets, exploratory notes, and review history.

4. REST-first
Every major entity is intended to be CRUD-capable via Joomla Web Services.

5. ACL-clean
Explicit role gates: Authors, Reviewers, Editors, Admins, API Clients.

6. Deterministic storage
Media and bundle storage should follow a predictable per-paper layout.

============================================================
5. Main data model entities
============================================================

The custom component planning repeatedly identifies the following main entities.

5.1 eaiou_papers
The central hub table.

Common fields:
- id
- state
- access
- ordering
- created / created_by
- modified / modified_by
- checked_out / checked_out_time
- title
- slug
- abstract
- doi
- keywords
- authors_json
- authorship_mode (human / ai / hybrid)
- status
- submission_version
- submission_date
- acceptance_date
- publication_date
- bundle_path
- thumbnail

Purpose:
- canonical record for a paper submission and publication lifecycle
- parent of versions, AI sessions, triage, reviews, attribution, plugin audit, etc.

5.2 eaiou_versions
Versioned artifacts per paper.

Common fields:
- id
- paper_id
- label
- file_path
- ai_flag
- ai_model_name
- generated_at
- notes

Purpose:
- represent version lineage of a paper or artifact bundle
- identify AI-generated/assisted versions

5.3 eaiou_ai_sessions
Per-paper AI usage logs.

Common fields:
- id
- paper_id
- session_label
- ai_model_name
- start_time
- end_time
- tokens_in
- tokens_out
- redaction_status
- session_notes
- session_hash

Purpose:
- immutable or semi-immutable audit of AI involvement
- session-level traceability for model usage

5.4 eaiou_didntmakeit
Excluded prompt/response archival linked to AI sessions.

Common fields:
- id
- session_id
- prompt_text
- response_text
- redacted
- redaction_hash

Purpose:
- preserve excluded AI interactions or non-final outputs
- keep “what didn’t make it” available for archival context

5.5 eaiou_remsearch
Literature triage / reference triage.

Common fields:
- id
- paper_id
- citation_title
- citation_source
- citation_link
- source_type
- used
- reason_unused

Purpose:
- capture sources considered
- distinguish included vs excluded literature
- record exclusion reasons

5.6 eaiou_review_logs
Structured peer review lineage.

Common fields:
- id
- paper_id
- reviewer_user_id
- review_date
- version_reviewed
- rubric_overall
- rubric_originality
- rubric_methodology
- rubric_transparency
- rubric_ai_disclosure
- labels_json
- review_notes

Purpose:
- preserve review history
- store rubric scores and labels
- support public or semi-public peer-review rendering

5.7 eaiou_attribution_log
Contribution history.

Common fields:
- id
- paper_id
- contributor_name
- role_description
- contribution_type
- ai_tool_used
- timestamp

Purpose:
- capture who did what
- distinguish human and AI contribution roles

5.8 eaiou_plugins_used
Tool/plugin audit.

Common fields:
- id
- paper_id
- plugin_name
- plugin_type
- execution_context
- exec_log_path

Purpose:
- record tool or plugin execution in relation to a paper

5.9 eaiou_api_keys
API access registry.

Common fields:
- id
- user_id
- api_key_hash or api_key
- description
- access_level
- status

Purpose:
- manage web-services/API client access

5.10 eaiou_api_logs
Immutable API call audit.

Common fields:
- id
- api_key_id
- endpoint
- request_data
- response_code
- timestamp

Purpose:
- preserve API interaction history and accountability

5.11 Optional discovery/collab entities
Seen in planning notes:
- eaiou_research_open
- eaiou_ideas
- eaiou_collab_matches

Purpose:
- open collaboration signals
- entropy/novelty-ranked ideas
- collaboration matching

============================================================
6. Relationships
============================================================

Primary relationships described:

- Paper 1—N Versions
- Paper 1—N AI Sessions
- Paper 1—N Review Logs
- Paper 1—N RemSearch entries
- Paper 1—N Attribution entries
- Paper 1—N Plugins Used entries

- AI Session 1—N Didn’t-Make-It entries

- User 1—N Review Logs
- User 1—N API Keys

Potential later additions:
- Paper 1—N Research Open entries
- Paper 1—N Ideas
- Collaboration matches linked across papers/users

============================================================
7. Workflow and states
============================================================

Planned state machine:
- draft
- submitted
- under_review or review
- revisions
- accepted
- published
- retired

Workflow principles:
- publish-time enforcement can be performed by plugins
- unresolved issues can block publishing
- deletion should become archival tombstoning rather than hard deletion
- reviewer labels annotate artifacts rather than remove them

============================================================
8. Roles / ACL model
============================================================

Roles repeatedly described:
- Author
- Reviewer
- Editor
- Admin
- API Client

Intended permissions:

Author:
- create/edit own paper
- upload bundles
- manage own related artifacts where permitted
- view own logs

Reviewer:
- access review console
- submit review logs
- label content or flag issues within ACL

Editor:
- edit any paper
- manage versions, triage, attribution
- resolve flags
- publish/unpublish
- manage reviewer/editorial workflows

Admin:
- global configuration
- API key/log management
- maintenance
- full oversight

API Client:
- web services access according to key access_level

============================================================
9. Storage layout
============================================================

Common planned storage pattern:

/media/com_eaiou/{paper_id}/
  /versions/{label}/
  /unused/
  /ai_sessions/{session_id}/
  /triage/

Design intent:
- deterministic media placement
- store originals and derived artifacts
- keep content hashes in DB where appropriate

============================================================
10. Site/frontend concepts
============================================================

Planned site features include:

1. Submit wizard
Typical steps:
- paper metadata
- upload bundle
- AI usage
- literature triage
- declarations
- reviewer suggest/avoid
- submit

2. Paper detail page
Tabs or sections such as:
- Article
- Versions
- Unused Data
- AI Logs
- Reviews
- Attribution

3. Review console
Reviewer-facing structured interface with:
- rubric sliders/scores
- labels/chips
- notes/comments
- possible attachments
- decision suggestions

4. Discovery views
Planned discovery-oriented pages:
- ideas discover
- open to collaborate board
- gap map
- trend/insight or entropy-derived exploration

5. API key self-service
For permitted users

============================================================
11. Admin/backend concepts
============================================================

Planned backend areas include:
- Dashboard
- Papers
- Versions
- Reviews
- AI Sessions
- Didn’t-Make-It
- Literature Triage
- Attribution
- Plugins Used
- API Keys
- API Logs
- Settings

Settings ideas mentioned:
- labels/rubrics
- file storage roots
- AI model allow-list
- API throttles
- mail templates or policy controls

============================================================
12. REST / endpoint direction
============================================================

The source material describes two endpoint styles:
- standard CRUD endpoints for entities
- functional Layer-5 style endpoints

Entity CRUD examples:
- /api/index.php/v1/eaiou/papers
- /api/index.php/v1/eaiou/versions
- /api/index.php/v1/eaiou/ai_sessions
- /api/index.php/v1/eaiou/didntmakeit
- /api/index.php/v1/eaiou/review_logs
- /api/index.php/v1/eaiou/remsearch
- /api/index.php/v1/eaiou/attribution
- /api/index.php/v1/eaiou/plugins_used
- /api/index.php/v1/eaiou/api_keys
- /api/index.php/v1/eaiou/api_logs

Functional / Layer-5 style directions:
- /eaiou/submit
- /eaiou/review
- /eaiou/search
- /eaiou/trace/entropy
- /eaiou/dataset/link
- /eaiou/ai/log
- /eaiou/export/context
- /eaiou/register/observer

Discovery/collaboration directions mentioned:
- /eaiou/research/open
- /eaiou/research/seek
- /eaiou/ideas/discover
- /eaiou/ideas/subscribe
- /eaiou/collaboration/match
- /eaiou/trend/insight
- /eaiou/gap/map

============================================================
13. Conceptual framing from the notes
============================================================

One recurring conceptual framing is that eaiou is not a normal journal website. It is positioned as:
- a full-context publication layer
- a place where used and unused research remain discoverable
- a searchable archive of “un research” or not-final material
- an observer-preserving publishing environment
- a mechanism to reduce silent loss of epistemically valuable context

Core conceptual features described in prose include:
- mandatory full-context submission
- searchable index of used and unused research
- reviewer ability to mark relevant / not relevant / critique without deletion
- AI usage logging in controlled environments
- possibility that irrelevant material in one field could be useful in another

============================================================
14. Core-first plugin and module suite
============================================================

The most detailed materials describe a core-first extension suite on top of Joomla Articles + Fields.

------------------------------------------------------------
14.1 Plugin 01 — Transparency Block
------------------------------------------------------------

Type:
- content plugin
- plg_content_transparency

Purpose:
- render and validate structured transparency metadata on articles

Data model direction:
Field Group: Transparency (Article context)

Main planned fields:
- transp_sources (repeatable)
  - src_title
  - src_type
  - src_pid
  - src_used
  - src_reason
  - src_notes

- transp_datasets (repeatable)
  - data_title
  - data_link
  - data_type
  - data_license
  - data_availability
  - data_anonymization

- transp_methods
- transp_limitations
- transp_complete
- transp_lastcheck

Behavior:
- render a badge/summary after title
- render full transparency block after content
- validate before publish
- optionally block state change if incomplete
- log validation summaries in Action Logs

Conceptual value:
- sources consulted, including excluded sources
- datasets/code details
- methods and limitations as required transparency

------------------------------------------------------------
14.2 Plugin 02 — AI Usage Log
------------------------------------------------------------

Type:
- content plugin
- plg_content_aiusage

Purpose:
- provide structured AI usage disclosure and auditability for articles

Field Group: AI Usage (Article context)

Main planned fields:
- ai_used
- ai_tools (repeatable)
  - ai_vendor
  - ai_model
  - ai_version
  - ai_mode
  - ai_endpoint
  - ai_params

- ai_interactions (repeatable)
  - ai_prompt_summary
  - ai_prompt_hash
  - ai_output_type
  - ai_contribution_scope
  - ai_human_oversight
  - ai_external_data_used
  - ai_data_sources
  - ai_risk_flags
  - ai_redactions

- ai_relationship_statement
- ai_display_level
- ai_log_complete
- ai_log_lastcheck

Behavior:
- show AI-Logged badge
- render AI Relationship & Usage panel
- require disclosure when ai_used=Yes
- hash prompts rather than storing raw prompts by default
- support display levels: full / summary / hidden
- block publish if incomplete when AI was used

Conceptual value:
- first-class AI collaboration record
- privacy-aware disclosure
- reproducibility and editorial enforcement

------------------------------------------------------------
14.3 Plugin 03 — Un Scientific Flag
------------------------------------------------------------

Type:
- content plugin
- plg_content_unscientific

Purpose:
- mark contested, ambiguous, unresolved, or accuracy-pending content
- especially useful in human-AI collaboration settings
- preserve contested material rather than removing it

Field Group: Un Scientific (Article context)

Main planned fields:
- unsci_active
- unsci_entries (repeatable)
  - unsci_scope
  - unsci_anchor
  - unsci_reason
  - unsci_notes
  - unsci_requested_action
  - unsci_risk_level
  - unsci_createdby
  - unsci_createdat

- unsci_resolved
- unsci_resolution_notes
- unsci_resolvedby
- unsci_resolvedat
- unsci_related_ai
- unsci_display_level
- unsci_lastcheck
- unsci_complete

Behavior:
- render Un Scientific badge after title
- render contention/clarification panel after content
- optionally auto-tag article as un-scientific
- can block publishing while unresolved
- allows editorial override if configured

Conceptual value:
- support unresolved or contested knowledge without deletion
- preserve audit trail and resolution path
- expose “epistemically non-null but unresolved” material

------------------------------------------------------------
14.4 Plugin 04 — Deadline Nudger
------------------------------------------------------------

Type:
- system plugin
- plg_system_deadline_nudger

Purpose:
- send reminders and escalations for reviewer invites, reviews, revisions, and editorial follow-ups
- use Joomla Scheduler + Mail Templates + Custom Fields
- no custom DB tables

Field Group direction: Deadlines (Article context)

Main planned fields:
- rev_invite_assignments (repeatable)
  - rev_user
  - rev_invite_sent
  - rev_invite_due
  - rev_invite_status
  - rev_invite_escalated

- rev_due_date (overall or per reviewer)
- auth_rev_due
- auth_rev_escalated
- ed_followup_due
- ed_followup_escalated

Behavior:
- scheduler task checks deadlines
- sends reviewer reminders
- sends author revision reminders
- escalates overdue items to editors
- supports dry-run mode
- writes Action Logs rather than storing separate notification state where possible

Conceptual value:
- operational workflow support without abandoning core-first design

------------------------------------------------------------
14.5 Plugin 06 — Open Reports
------------------------------------------------------------

Type:
- content plugin
- plg_content_openreports

Purpose:
- render reviewer reports and author responses alongside published article
- support transparent peer review modes with privacy safeguards

Field Group: Peer Review (Open Reports)

Main planned fields:
- or_enabled
- or_mode
  - Open Identities
  - Open Reports (anonymized)
  - Summary Only
- or_publish_on
- or_redact_emails

- or_reviews (repeatable)
  - or_rev_id
  - or_rev_user
  - or_rev_displayname
  - or_rev_consent_display
  - or_rev_recommendation
  - or_rev_scores
  - or_rev_text
  - or_rev_attachments
  - or_rev_date
  - or_rev_redactions
  - or_rev_publish

- or_author_responses (repeatable)
  - or_ar_to_review
  - or_ar_text
  - or_ar_date

- or_lastcheck
- or_complete

Behavior:
- render peer-review panel below article body
- enforce reviewer consent rules for open identity display
- support anonymized or summary-only modes
- redact email/PII patterns where configured
- coordinate with workflow timing: on accept, on publish, or manual

Conceptual value:
- transparent peer review as part of publication record
- privacy-aware public review rendering

------------------------------------------------------------
14.6 Plugin 07 — ORCID Link
------------------------------------------------------------

Type:
- system plugin
- plg_system_orcid_link

Purpose:
- allow users to link verified ORCID iD to Joomla profiles via OAuth
- privacy-first
- store only ORCID iD and URL by default

User Field Group direction: External IDs

Main planned user fields:
- orcid_id
- orcid_url
- orcid_verified_at

Behavior:
- Connect ORCID / Disconnect on user profile
- callback route validates state
- stores verified ORCID iD in user custom fields
- does not persist tokens by default
- optional read-limited fetch only if enabled

Conceptual value:
- verified researcher identity linkage
- support authors, reviewers, editors

------------------------------------------------------------
14.7 Module 05 — Reviewer Queue
------------------------------------------------------------

Type:
- site module
- mod_reviewer_queue

Purpose:
- show logged-in reviewer their assigned manuscripts
- due dates, status, badges, and quick actions
- read from articles + fields only

Data assumptions:
- reviewer assignments stored in repeatable article fields
- queue entries determined by user assignment + invite status + workflow state

UI direction:
- list or card mode
- title, category, state, invite status, due date
- days remaining / overdue colors
- optional badges:
  - AI-Logged
  - Un Scientific
  - Un Research
- optional quick actions:
  - Accept
  - Decline
  - Open Review
  - Contact Editor

Conceptual value:
- reviewer-facing workflow panel without custom review queue tables

------------------------------------------------------------
14.8 Module 06 — Editor Dashboard KPIs
------------------------------------------------------------

Type:
- admin module
- mod_editor_dashboard

Purpose:
- KPI dashboard for editors/EIC using articles + fields + logs + scheduler history
- no custom DB tables

Planned KPIs:
- submissions by state
- time to first decision (median / P90)
- overdue reviews / revisions / decisions
- reviewer throughput
- acceptance / rejection rates
- aging buckets by state
- queue by editor/section
- flags summary:
  - AI-Logged
  - Un Scientific
  - Un Research

UI direction:
- KPI cards
- tabs: Overview, Overdue, Reviewers, Trends, Flags
- filters for dates/categories/states/reviewer/editor
- optional CSV export

Conceptual value:
- editorial situational awareness using core data sources

============================================================
15. SQL/install direction
============================================================

The install SQL excerpts broadly align with the entity list above and define tables such as:
- #__eaiou_papers
- #__eaiou_versions
- #__eaiou_ai_sessions
- #__eaiou_didntmakeit
- #__eaiou_remsearch
- #__eaiou_review_logs
- #__eaiou_attribution_log
- #__eaiou_plugins_used
- #__eaiou_api_keys
- #__eaiou_api_logs

Observed implementation direction:
- Joomla-standard audit/state/access columns on each table
- indexes on status, publication date, paper foreign keys, model names, user/status combinations, etc.
- some notes mention FK constraints and ON DELETE CASCADE, though exact SQL excerpt shown was partial

============================================================
16. Menus, routes, and UX cues
============================================================

Proposed routes/menus found in the notes:
- /papers
- /paper/:id/:slug
- /submit
- /review/:paper_id
- /discover/ideas
- /discover/open
- /map/gaps
- API Keys

Modules mentioned:
- Latest Submissions
- Open to Collaborate
- Recently Reviewed
- AI Usage Heatmap
- Reviewer Queue
- Editor Dashboard

============================================================
17. Notable conceptual differentiators
============================================================

What makes eaiou distinct from an ordinary journal CMS in these notes:

1. Preservation of unused material
Unused or excluded research is considered valuable and should remain searchable.

2. AI as first-class provenance
AI assistance is not hidden; it is logged, structured, and optionally displayed.

3. Review as archival lineage
Peer review becomes part of the preserved research trail, not just editorial housekeeping.

4. Contested knowledge support
The “Un Scientific” concept preserves unresolved, ambiguous, or contested content rather than erasing it.

5. Cross-domain serendipity
Material considered irrelevant in one context may later matter in another.

6. Strong accountability
Action Logs, API logs, hashes, and structured fields reinforce provenance and auditability.

============================================================
18. Internal inconsistencies / cautions
============================================================

Important cautions from the available material:

1. Naming drift exists
The files contain both aieou and eaiou naming. For SSOT use, normalize to eaiou.

2. Two-stack tension exists
Some notes push a custom component with dedicated tables, while other specs push “core-first” article-based plugins/modules.
Best interpretation:
- use custom component for archive-specific records
- use core-first article plugins/modules for publication workflow UI and presentation

3. Some notes are explicitly brainstorm/draft status
Several plugin/module files are planning drafts, not finished code.

4. Not all SQL/manifests are final
The SQL and manifests shown are enough to infer design direction, but not guaranteed production-ready.

============================================================
19. Best current synthesis
============================================================

Best synthesis of the workspace material:

eaiou is a Joomla-based journal and peer-review platform designed to preserve the entire research process rather than only the final publication. It combines a custom paper-centric archival component with a suite of core-first Joomla plugins and modules. Its defining features are full-context submission, preservation of unused artifacts, structured AI disclosure, reviewer lineage, transparency enforcement, contested-content flagging, deadline nudging, ORCID linkage, reviewer/editor dashboards, and REST-accessible records. The governing philosophy is to annotate rather than delete, retain provenance, and make discarded or unresolved research context discoverable.

============================================================
20. SSOT recommendation
============================================================

If this material is to be turned into a real single source of truth, the cleanest normalization would be:

Canonical project name:
- eaiou

Canonical Joomla component:
- com_eaiou

Canonical namespace:
- Eaiou

Canonical DB prefix:
- #__eaiou_

Canonical site path family:
- /eaiou/...

Canonical API family:
- /api/index.php/v1/eaiou/...

Canonical conceptual statement:
- eaiou is an observer-preserving, full-context peer-review journal platform that archives papers, versions, unused research, AI involvement, review lineage, and attribution, using Joomla 5.3 with a core-first extension strategy.

End of file.
