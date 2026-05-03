# EAIOU Authoring System — Design v3 Lock

**Date:** 2026-05-02 20:07 PDT
**Status:** v3 — journal-rail-lock decision committed
**Authors:** Eric D. Martin (architecture), Mae (synthesis)
**Supersedes:** v2 design pass (gate logic + Question Discovery + validity routing + commitment ledger)
**Locked principle (top-of-document):**

```
1. The manuscript is not the starting point. The research question is.
2. The system asks; the author chooses what to do with drift.
3. The journal is the rail. The desktop locks to the journal.
4. The author writes INTO the journal — not toward it. No formatting step.
5. Two intake paths only: FRESH or RESTRUCTURED. No "upload-and-submit-as-is" path exists.
```

## Two intake paths, no third

| Path | What the author has | What EAIOU does |
|---|---|---|
| **FRESH** | Idea, no draft | Q1–Q5 → validity route → journal → rails → write INTO the journal from word one |
| **RESTRUCTURED** | Existing manuscript (any state) | Q1–Q5 → validity route → journal → rails → manuscript dismantled into evidence + claims, rebuilt INTO the journal's locked form |

The discarded path — "street-wise paper" / "upload my polished manuscript and just submit it" — is structurally rejected. The UI does not expose this affordance. MCP rejects any API call shaped like this path. Accepting it would force EAIOU to accept the author's scope, journal choice, and validity standard at face value — losing the three controls that make the architecture defensible.

## Commercial moat: four-way intersection

| Capability | Without it | With it |
|---|---|---|
| Pre-population + write-into-the-journal | Author writes generic prose, then formats for journal | Manuscript IS journal-formatted from line one; submission is one-click |
| FRESH or RESTRUCTURED only | Anyone uploads anything; EAIOU = submission portal | EAIOU controls intake shape; EAIOU = authoring system |
| MCP enforcement layer | App-layer rules bypassable via direct API | Gates enforced at protocol layer; bypass requires rebuilding the app |
| App surface (locked workspace) | Generic editor with sidebars | Workspace IS the journal layout; affordances match rails exactly |

These four are only deliverable jointly. A competitor copying any one is still inferior. The four-way intersection is the moat.

## Architectural decision (this pass)

Journal selection is a hard gate between Scope Axis Builder and Authoring Workspace. Author picks **either** a single target journal **or** a journal array (≥1, ≤N candidate journals). Selection imports the journal's authoring + material rails and pins them to the manuscript. The desktop is then locked to those rails for the lifetime of that manuscript (mutable only via explicit Scope Evolution Decision).

## Carrier mapping

EAIOU's authoring layer is an applied EB carrier:

| Carrier algebra | EAIOU |
|---|---|
| `e` (Expressed Center) | Confirmed research question |
| Rail (structural form) | Journal's authoring + material requirements |
| `b` (Bound) | Manuscript draft, shaped against the rail |
| `|b - e|` | Drift from question (semantic) |
| `|b - rail|` | Drift from journal requirements (structural) |
| Carrier-set theorem | EAIOU carries the work; the author is the (e, b) generator |
| Author-owned text | Author chooses every disposition of drift |
| A6 in/out symmetry | Author-supplied falsifiability matched against analyzer's score |

## Flow

```
Q1–Q5 Intent (5-question funnel: question / claim type / audience / provenance / falsifiability)
    ↓
Validity Route (paper type taxonomy: empirical / math / theoretical / review / case / framework / position)
    ↓
Journal Family Suggestion (filtered by validity route)
    ↓
Journal Selection — single OR array — HARD GATE
    ↓
Rails Imported, Desktop Locked
    ↓
Scope Axis Built within rails
    ↓
Authoring Workspace within rails
    ↓
Submission Readiness = rails-completeness check
```

## Rails payload

When journal(s) are selected, EAIOU imports a structured `journal_rails` object pinned to the manuscript record. Example:

```json
{
  "manuscript_id": "...",
  "primary_journal_id": "nature_comms",
  "candidate_journals": ["nature_comms", "plos_one", "scientific_reports"],
  "rails": {
    "section_template": ["Abstract", "Introduction", "Results", "Discussion",
                         "Methods", "Data Availability", "Code Availability",
                         "Author Contributions", "Competing Interests",
                         "References"],
    "word_count_targets": {"abstract": 200, "main": 5000, "methods": 2000},
    "required_statements": ["data_availability", "code_availability",
                            "competing_interests", "author_contributions",
                            "ai_use_disclosure"],
    "citation_style": "nature",
    "figure_limit": 6,
    "table_limit": 4,
    "supplementary_allowed": true,
    "preregistration_recognized": true,
    "open_access_required": false,
    "registered_report_track": false,
    "ethics_required_for": ["human_subjects", "animal_subjects",
                            "clinical_trial"]
  }
}
```

## Journal-array semantics

When author selects 3 journals, the desktop loads the **superset** of rails:

| Rail dimension | Aggregation across array |
|---|---|
| section_template | UNION (every section any journal demands) |
| word_count_targets | MINIMUM (most restrictive wins for safety) |
| required_statements | UNION |
| citation_style | Primary's; reflowable on primary-switch |
| figure_limit | MINIMUM |
| table_limit | MINIMUM |
| ethics_required_for | UNION |

Author can switch primary at any time → desktop reflows to the new primary's rails. The shape is "build to satisfy all candidates; submit to the chosen one."

## Validity-route reconciliation

Selection of a journal that does not publish the chosen validity route is blocked at selection time. Examples:

- Author picks `framework` validity route → only journals with `validity_routes_accepted` containing `framework` appear in the journal-family suggestions.
- Author picks `position` (opinion paper) → only journals with editorial / commentary tracks appear.
- Author later changes validity route → existing journal selection is revalidated; journals no longer compatible are flagged for removal from the candidate array.

## Schema additions

```sql
CREATE TABLE eaiou_journals (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    publisher VARCHAR(255) NOT NULL,
    issn VARCHAR(32) NOT NULL DEFAULT '',
    scope_keywords TEXT NOT NULL,
    validity_routes_accepted TEXT NOT NULL,           -- JSON array
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
    created DATETIME NULL DEFAULT NULL,
    modified DATETIME NULL DEFAULT NULL,
    state TINYINT NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    KEY idx_publisher (publisher),
    KEY idx_issn (issn),
    KEY idx_state (state)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE eaiou_manuscript_journals (
    id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    manuscript_id INT UNSIGNED NOT NULL,
    journal_id INT UNSIGNED NOT NULL,
    position VARCHAR(16) NOT NULL DEFAULT 'candidate',  -- primary | candidate
    selected_at DATETIME NULL DEFAULT NULL,
    switched_at_history_json TEXT NOT NULL,
    state TINYINT NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    KEY idx_manuscript (manuscript_id),
    KEY idx_journal (journal_id),
    KEY idx_position (position)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

The `eaiou_manuscripts` table also gains:

```sql
ALTER TABLE eaiou_manuscripts
  ADD COLUMN journal_rails_json TEXT NOT NULL,
  ADD COLUMN journal_rails_locked_at DATETIME NULL DEFAULT NULL;
```

## New MCP service calls

| Service | Input | Output | Cost tier | Blocking |
|---|---|---|---|---|
| `journal.family_suggest` | confirmed_question + validity_route + audience | ranked list of journal families | BYOK | advisory |
| `journal.candidates_filter` | journal_family + validity_route + scope_keywords | list of specific journal candidates | BYOK | advisory |
| `journal.rails_import` | journal_id (or array) | journal_rails payload | free | blocking |
| `journal.array_aggregate` | journal_id[] | superset rails | free | blocking |
| `journal.primary_switch` | manuscript_id, new_primary_journal_id | reflowed rails | free | non-blocking |
| `rails.compliance_check` | manuscript_id | per-rail compliance report | free | advisory |
| `rails.completeness_check` | manuscript_id | submission-readiness summary | free | blocking (gate) |

## Gate checklist v3 (final)

```
[ ] Author question exists
[ ] Author confirmed extracted question
[ ] Paper validity route selected
[ ] Author commitment ledger sealed
[ ] Validity route compatible with at least one journal in catalog
[ ] Journal or journal-array selected — HARD GATE
[ ] Rails imported and visible in desktop
[ ] Section template populated from rails
[ ] Word count targets locked per section
[ ] Required statements identified and queued
[ ] Scope axis generated (within rails)
[ ] Gap / novelty scan completed or intentionally skipped
[ ] Evidence burden created
[ ] Manuscript structure generated (matching rails)
[ ] Early upload, if present, compared against confirmed question
[ ] Scope drift resolved (per author's Scope Evolution Decision)
[ ] AI / human contribution log complete
[ ] Transparency ledger complete
[ ] Rails-compliance check passed (all required statements present, word counts within limits, etc.)
[ ] Version milestone sealed
[ ] Submission readiness passed
```

## Why the journal-rail lock matters

Without it, the workspace is unconstrained and the author has no shape to write toward. Every editorial decision (length, structure, required disclosures, citation format) becomes a personal interpretation made too late. With it, every action in the editor is pre-validated against where the work is going. Scope drift becomes measurable against two known anchors (question + rail) instead of one.

The journal-rail-lock is what differentiates EAIOU from "another markdown editor with sidebars." It is the thing that justifies the architecture.

## Implementation queue

1. Build `eaiou_journals` seed catalog (start with ~50 high-volume journals across the validity route taxonomy)
2. Build View 03A (Question Discovery Assistant) per v2 design
3. Build Validity Route view (paper type taxonomy)
4. Build Journal Family Suggestion view
5. Build Journal Selection (single OR array) view — the hard gate
6. Build rails-import + desktop-lock mechanism
7. Build `rails.compliance_check` + `rails.completeness_check` services
8. Wire Submission Readiness gate to `rails.completeness_check`
9. Build Scope Evolution Decision view (revise / update / split) per v2

## Provenance

This document is itself an artifact under `feedback_artifact_hash_naming.md`.

- v3 lock decision: 2026-05-02 20:07 PDT, in chat between Eric D. Martin and Mae.
- Spec basis: EAIOU intake v1 (2026-04-26), v2 design pass (2026-05-02 19:55 PDT, design agent), v3 journal-rail-lock (this document, 2026-05-02 20:07 PDT).
