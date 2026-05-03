---
title: EAIOU Authoring System — Architecture v3
subtitle: Locked design from 2026-05-02 working session
author: Eric D. Martin (architecture) · Mae (synthesis)
date: 2026-05-02
geometry: margin=0.75in
fontsize: 10pt
---

# Top-of-document principles

In order of load-bearing weight, descending. Lower numbers depend on higher numbers.

```
10. The method is the system. Conform, or use a different tool.
 9. Override of evidence-backed recommendations → OUT OF SLA.
 8. Custom-by-chat is the differentiator. Without it we are everyone else.
 7. Refusal of RESTRUCTURED intake is decline-of-service. 100% absolute.
 6. Switching journals outside the candidate array forces RESTRUCTURED intake.
 5. Two intake paths only: FRESH or RESTRUCTURED.
 4. Author writes INTO the journal — no formatting step.
 3. The journal is the rail. Desktop locks to the journal.
 2. The system asks; the author chooses what to do with drift.
 1. The manuscript is not the starting point. The research question is.
```

#10 is the floor. The other nine stand on it. Without #10 the stack is opinion. With #10 it is policy.

# Carrier mapping

EAIOU's authoring layer is an applied EB carrier. The same algebra that locks the math anchors the architecture.

| Carrier algebra | EAIOU |
|---|---|
| `e` (Expressed Center) | Confirmed research question |
| Rail (structural form `b` must satisfy) | Journal's authoring + material requirements |
| `b` (Bound) | Manuscript draft, shaped against the rail |
| `\|b - e\|` | Drift from the question (semantic) |
| `\|b - rail\|` | Drift from the journal (structural) |
| Carrier-set theorem | EAIOU carries the work; the author is the `(e, b)` generator |
| Author-owned text doctrine | Author chooses every disposition of drift |
| A6 in/out symmetry | Author-supplied falsifiability matched against analyzer score |

# Flow

```
Q1–Q5 Intake
    ↓
Validity Route (paper type)
    ↓
Journal Family Suggestion (filtered by validity route)
    ↓
Journal Selection (single OR array) — HARD GATE
    ↓
Rails imported, desktop locked
    ↓
Scope Axis built within rails
    ↓
Authoring Workspace within rails
    ↓
Submission Readiness (rails-completeness check)
```

# Two intake paths, no third

| Path | Author has | EAIOU does |
|---|---|---|
| FRESH | Idea, no draft | Q1–Q5 → validity → journal → rails → write INTO the journal from line one |
| RESTRUCTURED | Existing manuscript | Q1–Q5 → validity → journal → rails → manuscript dismantled into evidence + claims, rebuilt INTO journal's locked form |

The discarded path — "upload my polished manuscript and just submit it" — is structurally rejected. The UI does not expose this affordance; MCP rejects any API call shaped like this path.

# RESTRUCTURED algorithm — three buckets

When the RESTRUCTURED path is taken, EAIOU dismantles the uploaded
manuscript into three explicit buckets. The new workspace starts FRESH;
bucket contents flow in only where we are prepared to handle them.

| Bucket | Contents | Destination |
|---|---|---|
| 1. POPULATE | Title; Abstract minus first two and last sentences; Discussion heading only; Figures; Tables | Drops into the fresh workspace as starter material |
| 2. DROP | Conclusion (in full); Intro prose; Results prose; Discussion prose; any free-text body | Never populated. Archived to drawer for reference only. |
| 3. CALIBRATION | Methods (analytical reference); first two sentences of Abstract; last sentence of Abstract; paragraph-ending style sample | Not in workspace. Used by analyzers only. |

Why each bucket is shaped this way:

- **Title** preserved. Renaming is a Scope Evolution decision, not automatic.
- **Abstract middle** is summary content; usable as starter prose.
- **First two sentences of Abstract** anchor the original claim. After
  rebuild, the new conclusion is compared against them. *"Did the rebuilt
  manuscript actually do what the original claimed?"*
- **Last sentence of Abstract** anchors voice. After rebuild, the new prose
  is compared against it. *"Is this still you, or did the restructure
  flatten your voice?"*
- **Discussion heading only** preserves the structural marker; prose drops
  because discussion prose drifts most.
- **Conclusion** fully discarded. It was shaped to a journal that may not be
  the new target.
- **Methods** kept analytical-only. The work the author did stays valid even
  when prose changes; the methods section is a reference the author pulls
  from when filling the new methods slot.
- **Figures & Tables** preserved. They are data; data is journal-agnostic.

## Style hygiene rules

The dismantling encodes editorial discipline. Surfaced as named, inline
coaching rules — visible in the margin, not blocking:

| Rule | Detector |
|---|---|
| Don't end paragraphs with a citation | `style.paragraph_ending_check` |
| Don't trail off | Final paragraphs of major sections need declarative terminal claims |
| Conclusion must answer the opening claim | `claim.anchor_compare` against first-two-sentences anchor |
| Voice must remain the author's | `voice.calibration_compare` against last-sentence anchor |

# The five intake questions

| # | Question | Feeds |
|---|---|---|
| 1 | What question is this work asking? | Locked as `e` |
| 2 | What is it going to do? *(measure / test / build / synthesize / argue)* | Validity route + claim type |
| 3 | Who wants to read this? | Audience tier; journal filter |
| 4 | How did this question come to you? | Provenance / lineage |
| 5 | What would convince you that you are wrong? | Author-supplied falsifiability |

**Q3A — Question Discovery Assistant** runs *before* Q1 if the author cannot yet articulate a clean research question. Idea-dump prompts produce candidate questions; author selects or rewrites one before the gate opens.

Each answer is autofillable from an uploaded manuscript when in RESTRUCTURED path, but the author must confirm or revise — autofill is never silently committed.

# Validity routes

The paper-type taxonomy that filters journal selection:

| Route | Validity standard |
|---|---|
| empirical | falsifiability |
| mathematical | proof / counterexample vulnerability |
| theoretical | boundary conditions + explanatory constraint |
| review | reproducible search logic + inclusion/exclusion transparency |
| case study | evidentiary traceability |
| framework | classification utility + scope limits |
| position | argumentative coherence + steelman of opposing view |

Service: `validity.route` returns `{paper_type, validity_standard, required_next_gate}`.

# Author Commitment Ledger

Captures intent before writing starts. Sealed by `intent.commitment_seal`.

Stored fields:
- confirmed question
- claimed paper type
- target audience
- intended field
- excluded fields
- acceptable risk level
- evidence type expected
- whether manuscript existed before intake

Revisions are append-only. Public record shows evolution; no silent overwrite.

# Journal selection — hard gate

Author picks **one journal** OR **a journal array (≥1, ≤N)**. Validity route filters which journals appear. Cannot enter the workspace without a selection.

The intake finder is **live-reactive**. The candidate pool starts at ~1500 journals. Each answer shrinks the pool visibly with a delta animation and a "what just got filtered out, and why" expandable trace.

For arrays: the desktop loads the **superset** of rails — union of sections, minimum of limits, primary's citation style with reflowable on switch.

# Rails — what gets imported and locked

When journal(s) selected, EAIOU pulls a `journal_rails` payload pinned to the manuscript:

- Section template
- Word count targets per section
- Required statements (data availability, COI, AI disclosure, author contributions, ethics)
- Citation style
- Figure / table limits
- Supplementary policy
- Pre-registration recognition
- Open access requirement
- Registered Report track availability

The desktop is locked to these rails. Affordances that don't fit don't render.

# Pre-population — write INTO the journal

When the desktop locks, the workspace is pre-furnished with the journal's conventions in place from line one:

- Margin-style numbered references appear live as author cites (Nature)
- Table shells include averages-row / units-row pre-built per journal
- Figure caption shells appear in the journal's typographic format
- Required-statement cards drop into their conventionally-correct positions
- Citation manager pre-loaded with the journal's style
- Word counter live per section, locked to per-section limits

There is no "formatting step" downstream. Submission is structurally guaranteed because the work is already in the journal's shape.

# Layout

**Wide screens (≥1280px) — every tier, no upcharge:**

```
┌─────────────────┬─────────────────────────────┬─────────────────┐
│ LEFT TOOLBAR    │ MAIN CANVAS                 │ RIGHT TOOLBAR   │
│ (journal rails) │ (write into journal)        │ (inner rails)   │
│                 │                             │                 │
│ Sections req.   │                             │ IID assistants  │
│ Figures n / m   │                             │ Drift indicator │
│ Tables  n / m   │                             │ Rails compliance│
│ Required stmts  │                             │ Submission ready│
│ Refs    n / m   │                             │ Drawer (uploads)│
│ [drag → insert] │                             │ Version history │
│                 │                             │ SLA status      │
└─────────────────┴─────────────────────────────┴─────────────────┘
```

**Left toolbar = journal-required-element inventory** with scarcity counters. Locked by rails. Drag items into canvas; they drop in journal-formatted shape.

**Right toolbar = work surface, customizable inner rails.** Author pins what they want — Claude IID with personal prompt, scratchpad, drift indicator placement, co-author thread. Pins persist across every section. Carrier vs. agent: rigidity left, flexibility right.

**Drag-from-toolbar = primary mechanic.** Author needs another figure → drag from `Figures 2/3` → caption shell drops at cursor in journal format. Author fills slots; structural shape is given.

**Narrow screens — rails go inline:**

| Width | Layout |
|---|---|
| ≥ 1280px | Dual sidebar (default for wide) |
| 768–1279px | Single right sidebar; left as collapsible drawer |
| 480–767px | Both sidebars become bottom drawer + inline checkpoint cards |
| < 480px | Inline-only with floating IID action button |

Functionality identical at every viewport. Rails preserved.

# Switching journals

| Case | Behavior |
|---|---|
| Switch primary within original candidate array | Allowed. Rails reflow within the union. |
| Add a journal not in the array, or switch to one outside the array | BLOCKED at the simple-switch path. Author must initiate RESTRUCTURED intake. |
| Refuses RESTRUCTURED | Service declines. EAIOU is not a polish-and-submit tool. |

The friction isn't punitive — it's diagnostic. If the work shifted enough to need a different journal, restructure is what the work needs anyway. If it didn't shift, the friction prevents waste.

# Live evidence with every judgment

Every journal-related output (suggester ranking, fit score, drift assessment, restructure recommendation, falsifiability comparison) emits an `evidence[]` array — actual recent articles, clickable to inspect, with retrieval-time metadata and per-source contribution weights.

Authors who want to disagree must engage with the cited articles. Abstract complaints fail because the evidence is on the table. Informed disagreements are honored: override + rationale logged via `intellid.log`.

```json
{
  "score": "low",
  "evidence": [
    {"source": "doi:...", "title": "...", "weight": 0.34,
     "retrieved": "2026-05-02T20:15:00Z",
     "citation_used_in_reasoning": "Methods, p2"}
  ],
  "reasoning_trace": "..."
}
```

# Custom-by-chat — the differentiator

Every author choice that customizes the workspace flows through chat, not through static dropdown forms.

| Form-based tool | EAIOU chat-driven |
|---|---|
| Dropdown: "Select journal" | "Show me journals for empirical neuroscience targeting clinicians, ranked by acceptance trend" |
| Static drift indicator | "Your discussion is drifting toward Y. Three options: revise back, update question, split. Which?" |
| Form: "Override SLA recommendation" | "I want Nature even though your evidence says it's a poor fit — show me why you flagged it, then I'll decide" |

The rigidity (rails, gate sequence) is the floor. The chat is the texture that makes the rigidity feel humane.

# Out-of-SLA on override

Author choices that contradict EAIOU's evidence-backed recommendations move the manuscript OUT OF SLA. Service continues; service-level guarantees forfeit until return to a recommended envelope.

SLA status is persistent and visible:

```
Status: ⚠ OUT OF SLA
Reason: You chose [J] over our top recommendation [K] on 2026-05-02.
Evidence we cited: [12 articles]
Your override reason: "..."
Effects:
  Fit Guarantee:        ✗ inactive
  Restructure Guarantee: ✗ inactive
  Time Guarantee:       ✓ active
  Match Guarantee:      ✗ inactive
[Return to recommendation envelope]
```

Override events logged append-only with timestamp, dimension, the recommendation overridden, evidence cited, author rationale. The audit trail never gets edited; returns to in-SLA add new entries.

# Conform or leave

The method is the system. The method is not negotiable.

| Without #10 | With #10 |
|---|---|
| Author negotiates Q5 wording → falsifiability slips | Q5 is asked in the system's form; author answers or leaves |
| Author imports outside structure → rails compromised | The system's structure is the structure |
| Author asks to skip Q4 → intake erodes | "Skip" is not in the menu |
| Power user demands API bypass → MCP rules become advisory | API enforces same rules as UI |
| Sales says "for this enterprise client we can flex" → architecture corrupted | No flex tier exists; pricing buys volume, not method-bypass |

Self-selection as a feature:

- Authors who want a method → stay, get SLA-backed outcomes
- Authors who want freedom-as-blank-canvas → leave, find a different tool
- Authors who want to game the system → bounce off the gates and leave
- Authors who are partway-formed → the chat layer (#8) helps them across

By being unsuitable for some authors, EAIOU becomes maximally valuable to the rest.

# Service-level guarantees — only possible because rigidity holds

| Tier | Guarantee |
|---|---|
| Fit Guarantee | If a manuscript exits readiness check and the chosen journal desk-rejects on format grounds, EAIOU refunds and restructures into a sibling journal at no cost |
| Restructure Guarantee | RESTRUCTURED intake completes within N business days or refund |
| Time-to-Submission | FRESH path → first-draft in N weeks for a given paper type |
| Match Guarantee | If the suggester's top-1 has measurably below-cohort acceptance rate, the suggester re-runs free |

Loose tools cannot sell outcomes; only EAIOU can, because intake shape is controlled.

# Journal partnership — the upstream-filter pivot

EAIOU is not a competitor to journals. EAIOU is an upstream filter that benefits journals.

| For the journal | For EAIOU |
|---|---|
| Manuscripts arrive structurally pre-conformant → lower copy-edit burden | Authoring fees + subscription |
| Lower desk-reject rate → better author-experience metric | Higher fit-rate → SLAs deliverable |
| Better scope-fit → higher relevance per submission | Lower restructure refunds |
| Editorial priorities surfaced before submission → shape pipeline | Premium signal source for the suggester |

Once journals see this, partnership opens private signal channels:
- Current editorial priorities
- Section-format preferences not in public guidelines
- Topic priority weights and real-time hotness signals
- Reviewer-pool preferences
- Pre-screening lanes
- Beyond-public acceptance trend data

The rigidity that looks like friction to authors is the same property that earns SLAs and partnerships. A loose tool can sell neither.

# Market position

EAIOU is the **first and only AI-integrated full-service manuscript authoring
system for independent researchers operating under SAID protocols.**

| Component | What it asserts |
|---|---|
| First AI-integrated | Existing tools avoid AI or bolt it on; EAIOU is built around IID dispatch from line zero |
| Full-service manuscript | Intake to submission readiness, not editing-only or formatting-only |
| Independent researchers | Target market: researchers without institutional infrastructure (no university press office, no editorial assistant, no junior coauthors). EAIOU replaces what institutions provide. |
| SAID protocols | Strong AI Information Disclosure — every IID interaction logged, no chaining, per-provider credential isolation, author-owned text. ToS Compliance Doctrine §1 enforced. |

The independent-researcher target is non-obvious. Existing tools assume a user
with institutional support. EAIOU is built for the researcher who does not
have that, and SAID compliance is what gives them institutional-grade
trustworthiness markers without the institution.

# Workflow is a no-exception process

A clarifying frame for principle #10 (conform-or-leave): a *workflow* is, by
definition, a no-exception process. The moment an exception is granted, the
artifact is no longer a workflow but a suggestion. EAIOU's rigidity is
legitimate not because of authority but because of category. Calling EAIOU
a "workflow" commits to the no-exception property.

# Commercial moat — the five-way intersection

| Capability | Without it | With it |
|---|---|---|
| Pre-population + write-into-the-journal | Author writes generic prose, formats later | Manuscript IS journal-formatted from line one |
| Two-paths-only intake | Anyone uploads anything; EAIOU = portal | EAIOU controls intake shape; EAIOU = authoring system |
| MCP enforcement layer | App rules bypassable via direct API | Gates enforced at protocol layer |
| Locked app surface | Generic editor with sidebars | Workspace IS the journal layout |
| SAID protocol compliance | AI integration opaque; no provable authorship; institutional credibility required to be trusted | Every IID action logged; author-owned-text + audit trail = provable authorship; institutional-grade trust without an institution |

These five are only deliverable jointly. A competitor copying any one — or even any four — is still inferior. The five-way intersection is the moat. SAID compliance is the leg that converts "control of intake shape" into "institutional-grade authorship guarantee" — without it, the architecture works but doesn't earn the independent-researcher market.

# Schema additions

```sql
CREATE TABLE eaiou_intake_sessions (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id INT UNSIGNED NOT NULL,
  manuscript_id INT UNSIGNED NULL DEFAULT NULL,
  path VARCHAR(16) NOT NULL,                  -- fresh | restructured
  current_gate VARCHAR(64) NOT NULL,
  consent_status VARCHAR(32) NOT NULL DEFAULT 'pending',
  q1_question TEXT NOT NULL,
  q2_claim_type VARCHAR(64) NOT NULL DEFAULT '',
  q3_audience VARCHAR(64) NOT NULL DEFAULT '',
  q4_provenance TEXT NOT NULL,
  q5_falsifiability TEXT NOT NULL,
  validity_route VARCHAR(32) NOT NULL DEFAULT '',
  candidate_journals_json TEXT NOT NULL,
  selected_journal_id INT UNSIGNED NULL DEFAULT NULL,
  primary_journal_id INT UNSIGNED NULL DEFAULT NULL,
  created DATETIME NULL DEFAULT NULL,
  modified DATETIME NULL DEFAULT NULL,
  PRIMARY KEY (id),
  KEY idx_user (user_id),
  KEY idx_manuscript (manuscript_id),
  KEY idx_gate (current_gate)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE eaiou_journals (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  publisher VARCHAR(255) NOT NULL,
  issn VARCHAR(32) NOT NULL DEFAULT '',
  scope_keywords TEXT NOT NULL,
  validity_routes_accepted TEXT NOT NULL,
  word_limits_json TEXT NOT NULL,
  section_template_json TEXT NOT NULL,
  required_statements_json TEXT NOT NULL,
  citation_style VARCHAR(64) NOT NULL DEFAULT '',
  figure_limit INT NOT NULL DEFAULT 0,
  table_limit INT NOT NULL DEFAULT 0,
  supplementary_allowed TINYINT NOT NULL DEFAULT 0,
  preregistration_recognized TINYINT NOT NULL DEFAULT 0,
  open_access_required TINYINT NOT NULL DEFAULT 0,
  registered_report_track TINYINT NOT NULL DEFAULT 0,
  ethics_required_for_json TEXT NOT NULL,
  submission_url VARCHAR(512) NOT NULL DEFAULT '',
  fees_json TEXT NOT NULL,
  acceptance_rate_pct DECIMAL(5,2) NULL DEFAULT NULL,
  time_to_decision_days INT NULL DEFAULT NULL,
  scope_score_components_json TEXT NOT NULL,
  state TINYINT NOT NULL DEFAULT 1,
  PRIMARY KEY (id),
  KEY idx_publisher (publisher),
  KEY idx_issn (issn)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE eaiou_manuscript_journals (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  manuscript_id INT UNSIGNED NOT NULL,
  journal_id INT UNSIGNED NOT NULL,
  position VARCHAR(16) NOT NULL DEFAULT 'candidate',  -- primary | candidate
  selected_at DATETIME NULL DEFAULT NULL,
  switched_at_history_json TEXT NOT NULL,
  PRIMARY KEY (id),
  KEY idx_manuscript (manuscript_id),
  KEY idx_journal (journal_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE eaiou_manuscripts
  ADD COLUMN journal_rails_json TEXT NOT NULL,
  ADD COLUMN journal_rails_locked_at DATETIME NULL DEFAULT NULL,
  ADD COLUMN sla_status VARCHAR(32) NOT NULL DEFAULT 'in_sla',
  ADD COLUMN sla_overrides_json TEXT NOT NULL,
  ADD COLUMN sla_status_changed_at DATETIME NULL DEFAULT NULL;
```

# New MCP service calls

| Service | Cost tier | Blocking |
|---|---|---|
| `question.discover` | BYOK | advisory |
| `question.extract` | BYOK | blocking |
| `question.confirm` | free | blocking |
| `validity.route` | free | blocking |
| `intent.commitment_seal` | free | blocking |
| `journal.family_suggest` | BYOK | advisory |
| `journal.candidates_filter` | BYOK | advisory |
| `journal.rails_import` | free | blocking |
| `journal.array_aggregate` | free | blocking |
| `journal.primary_switch` | free | non-blocking |
| `journal.switch_request` | free | advisory |
| `manuscript.restructure_initiate` | $5 platform | blocking |
| `manuscript.intent_compare` | BYOK | advisory |
| `falsifiability.score` | BYOK | advisory |
| `falsifiability.rewrite` | $5 platform | non-blocking |
| `contribution.classify` | BYOK | blocking |
| `scope.axis.generate` | BYOK | blocking |
| `scope.reconciliation` | BYOK | advisory |
| `scope.evolution_decision` | free | blocking |
| `scope.prewrite.scan` | BYOK | advisory |
| `gap.idea.scan` | $5 platform | advisory |
| `audience.map` | BYOK | advisory |
| `evidence.burden` | free | advisory |
| `structure.generate` | BYOK | blocking |
| `draft.scope_drift_check` | BYOK | advisory |
| `citation.burden_check` | BYOK | advisory |
| `transparency.source_check` | free | blocking |
| `version.milestone_seal` | free | blocking |
| `submission.readiness_check` | $5 platform | blocking |
| `manuscript.split_recommendation` | BYOK | advisory |
| `rails.compliance_check` | free | advisory |
| `rails.completeness_check` | free | blocking |
| `intellid.log` | free | blocking |

# Gate checklist

```
[ ] Author question exists (Q1)
[ ] Author confirmed extracted question
[ ] Q2–Q5 answered in the system's form
[ ] Validity route selected and compatible with at least one journal
[ ] Author Commitment Ledger sealed
[ ] Journal or journal-array selected — HARD GATE
[ ] Rails imported and visible in desktop
[ ] Section template populated from rails
[ ] Word count targets locked per section
[ ] Required statements identified and queued
[ ] Scope axis generated within rails
[ ] Gap / novelty scan completed or intentionally skipped (with rationale)
[ ] Evidence burden created
[ ] Manuscript structure generated matching rails
[ ] Early upload, if present, compared via manuscript.intent_compare
[ ] Scope drift resolved per author's evolution decision
[ ] AI / human contribution log complete
[ ] Transparency ledger complete
[ ] Rails-compliance check passed
[ ] Version milestone sealed
[ ] Submission readiness passed
[ ] If override events occurred: SLA-status visible and acknowledged by author
```

# Implementation queue

Sequential. Each step depends on the prior.

1. `eaiou_journals` seed catalog (~50 high-volume journals across the validity-route taxonomy)
2. View 03A — Question Discovery Assistant
3. Validity Route view
4. Journal Family Suggester (live-reactive, with evidence)
5. Journal Selection (single OR array) — the hard gate
6. Rails-import + desktop-lock mechanism
7. `rails.compliance_check` + `rails.completeness_check`
8. Submission Readiness gate wired to readiness check
9. Scope Evolution Decision view
10. SLA-status indicator + override audit trail
11. Chat-driven customization layer over every choice

Multi-week build. Architecture is locked. The hard part is no longer the design.

# Provenance

This document is a v3 lock. It supersedes the v1 (intake stub, 2026-04-26) and v2 (gate-logic + Question Discovery + validity routing + commitment ledger, 2026-05-02 19:55 PDT). v3 was assembled in chat between Eric D. Martin and Mae on 2026-05-02 between 19:55 and 20:30 PDT.

Per `feedback_artifact_hash_naming.md`, the canonical version of this document carries its commit hash inside the filename when locked. Filename will be updated to include the commit hash after Eric's scrub pass.
