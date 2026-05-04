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
6. Switching journals outside the original candidate array forces RESTRUCTURED intake.
   No simple format-flip exists. Different journal = different rails = different work.
7. Refusal of RESTRUCTURED intake is decline-of-service. 100% absolute, no exceptions,
   no premium tier that bypasses, no negotiation. The policy IS the product.
8. Custom-by-chat is the differentiator. Author choices happen through conversation,
   not static forms. Without chat-driven customization, we are everyone else.
9. Override of evidence-backed recommendations (journal, scope, validity route,
   falsifiability) moves the manuscript OUT OF SLA. Author can still use the tool;
   author forfeits service-level guarantees until returning to a recommended envelope.
10. The method is the system. Conform, or use a different tool. Authors stay in the
    system and answer the system's questions in the form the system asks them. No
    rephrasing, no skipping, no outside-tool bypass, no street-wise-paper path. EAIOU
    is correctly unsuitable for authors who want a different method.
```

## Principle #10 — the consolidating frame

The method is the system. The method is not negotiable. This is the user-facing
terms-of-service version of every prior principle. Each prior principle defends
against one failure mode; this one defends against the
**erosion-by-individual-exception** mode that would dissolve all of them.

The "use a different tool" exit is not abandonment — it is integrity. The right
authors stay because the method serves them. The wrong authors leave because
they want something EAIOU does not sell. Both outcomes are correct.

Self-selection as a feature:

- Authors who want a method, trust rigidity, prefer guided structure → stay
- Authors who want freedom-as-blank-canvas → leave, find a different tool
- Authors who want to game the system → bounce off the gates and leave
- Authors who are partway-formed and can be guided → the chat-driven layer (#8)
  helps them across the threshold

By being unsuitable for some authors, EAIOU becomes maximally valuable to the
rest. Niche-by-design, not by accident. Same shape as journal partnerships:
the value is in the constraint, not in spite of it.

#10 is the floor. The other nine principles stand on it. Without #10, the
principle stack is opinion. With #10, it is policy.

## Principle #8 — custom-by-chat is the differentiator

Every author choice that customizes the workspace flows through chat, not
through a static dropdown form. The chat is the meta-layer over every
structural rail. The rigidity is the floor; the chat is the texture that
makes the rigidity feel humane.

Without chat-driven customization, the system becomes a compliance gauntlet
indistinguishable from existing submission portals. With it, the same gates
feel like a guided audition — personalized, evidence-backed, conversational.

## Principle #9 — out-of-SLA when author overrides analyzer

When the author makes a choice (journal, scope, validity route, falsifiability
disposition) that contradicts EAIOU's evidence-backed recommendation, the
manuscript moves OUT OF SLA. Service continues; service-level guarantees
forfeit until the author returns to a recommended envelope.

SLA status is persistent and visible at all times. Override events are logged
with timestamp, dimension, the recommendation that was overridden, the
evidence cited, and the author's rationale. The audit trail is append-only
— returns to in-SLA add new entries; existing entries never get edited.

This is the carrier theorem at the commercial layer: the carrier carries any
value, but only specific values are guaranteed by the structure. Author owns
the outcome of every commit. SLA forfeit is the financial expression of the
author-owned text doctrine.

```
┌─────────────────────────────────────┐
│ Status: ⚠ OUT OF SLA                │
│ Reason: You chose [J] over our top  │
│   recommendation [K] on 2026-05-02. │
│ Evidence we cited: [12 articles]    │
│ Your override reason: "..."          │
│ Effects:                            │
│   Fit Guarantee:        ✗ inactive  │
│   Restructure Guarantee: ✗ inactive │
│   Time Guarantee:       ✓ active    │
│   Match Guarantee:      ✗ inactive  │
│ [Return to recommendation envelope] │
└─────────────────────────────────────┘
```


## Principle #7 — refusal is the architecture's signature

If the author refuses RESTRUCTURED intake (manuscript exists, but they want
polish-not-restructure), EAIOU declines service. Not blocks-with-warning. Not
soft-redirects. Declines.

There is no third path. Ever. No exception tier. The 100% policy IS the
product. A 95% policy with 5% exceptions becomes 50% in practice via slippage,
and slippage destroys the SLA guarantees, the journal partnerships, and the
brand position. All three are downstream of intake-shape control.

The decline moment in UX:

> EAIOU does not offer manuscript submission without restructure.
>
> You have two options:
>
>   [Begin RESTRUCTURED intake]   [Begin FRESH intake (discard upload)]
>
> If neither path works for you, EAIOU is not the right tool for this
> manuscript. We are not a submission service. We are an authoring system,
> and our service-level guarantees and journal partnerships require that
> we control the intake shape.
>
>   [Close — return manuscript to me]

The exit is the integrity move. EAIOU lets the author walk away clean. Doesn't
accept the work in any compromised form. Doesn't retain them with a downgraded
service.

Brand position:

> EAIOU is not for everyone. EAIOU is for authors willing to do the discipline
> that lets us guarantee outcomes and partner with journals on their behalf.
> If that's not what you want, you are correctly excluded.

The exclusion is the signal. Orchestras hold auditions. You don't get into the
orchestra by refusing the audition. That's not gatekeeping — it's the condition
under which the orchestra can promise the audience a concert. EAIOU's intake
discipline is the audition.

## Two intake paths, no third

| Path | What the author has | What EAIOU does |
|---|---|---|
| **FRESH** | Idea, no draft | Q1–Q5 → validity route → journal → rails → write INTO the journal from word one |
| **RESTRUCTURED** | Existing manuscript (any state) | Q1–Q5 → validity route → journal → rails → manuscript dismantled into evidence + claims, rebuilt INTO the journal's locked form |

The discarded path — "street-wise paper" / "upload my polished manuscript and just submit it" — is structurally rejected. The UI does not expose this affordance. MCP rejects any API call shaped like this path. Accepting it would force EAIOU to accept the author's scope, journal choice, and validity standard at face value — losing the three controls that make the architecture defensible.

## Layout architecture — dual-sidebar on wide, inline on narrow

The visual surface that makes everything above feel like a single tool, not a
gauntlet of gates.

**Wide screens (≥1280px) — every tier, no upcharge:**

```
┌──────────────────┬───────────────────────────────────┬──────────────────┐
│ LEFT TOOLBAR     │ MAIN CANVAS (write into journal)  │ RIGHT TOOLBAR    │
│                  │                                   │                  │
│ Sections req.    │ [Article in journal layout]       │ IID assistants   │
│ - Methods   1/1  │                                   │ Drift indicator  │
│ - Results   2/3  │                                   │ Rails compliance │
│ Figures   2 / 3  │                                   │ Submission ready │
│ Tables    1 / 4  │                                   │ Drawer (uploads) │
│ Required stmts   │                                   │ Version history  │
│ Refs    34 / 80  │                                   │                  │
│ [drag to insert] │                                   │                  │
└──────────────────┴───────────────────────────────────┴──────────────────┘
```

The **left toolbar is the journal's required-element inventory.** Each row
shows a scarcity counter (`Figures 2/3` = need 3, have 2). Author drags items
from toolbar to canvas:

- Figure shells with journal-formatted caption template pre-applied
- Table shells with header-row + averages-row pre-built per journal convention
- Required statement cards (data availability, COI, AI disclosure, author
  contributions) drop into their conventionally-correct positions
- Section headers from the locked template
- Citation entries from the locked citation manager (with margin numbers
  for Nature, inline `[N]` for IEEE, `(Author Year)` for PLOS, etc.)

The **right toolbar is the work surface.** IID assistants (Claude, OpenAI,
others — BYOK), drift indicator (semantic + structural), rails-compliance
light, submission-readiness gauge, drawer for uploaded reference manuscripts,
version timeline.

The scarcity counters turn the toolbar into a diagnostic-and-affordance
dashboard. Author sees what's needed, what's done, grabs the next thing — all
without leaving the canvas.

**Drag-from-toolbar = the primary mechanic.** Author needs another figure →
drag from `Figures 2/3` slot → caption shell appears at cursor with the
journal's exact format (e.g. `**Fig. 3.** *Title sentence.* Caption body.` for
Nature; auto-assigned margin reference). The author doesn't construct from
scratch; they fill known slots dragged from a known palette. This is the
"write INTO the journal" principle made mechanical.

**Inner rails (right toolbar) are author-customizable and persistent.** The
left toolbar contents are defined by the journal rails and locked. The right
toolbar contents are defined by the author and follow them across every
section of the manuscript:

- Pin a Claude IID assistant with a personal prompt that travels with them
- Pin the drift indicator at the top, bottom, or middle of the right rail
- Pin a personal scratchpad for notes that don't enter the manuscript
- Pin reference-search shortcuts scoped to a specific corpus
- Pin a comment thread with a co-author

Whatever the author pins persists across every page within that manuscript.
This expresses the doctrine cleanly: rigidity where it must be (left, journal)
and flexibility where it should be (right, author). Carrier vs. agent.

**Narrow screens — rails go inline.** On tablet/phone the dual sidebar
collapses; the rails become inline elements within the editing flow:

| Width | Layout |
|---|---|
| ≥ 1280px | Dual sidebar (default for wide, every tier) |
| 768–1279px | Single right sidebar; left toolbar as collapsible drawer |
| 480–767px | Both sidebars become bottom drawer + inline checkpoint cards between sections |
| < 480px | Inline-only with floating IID action button |

Functionality identical at every viewport. Rail integrity preserved. The
"write into the journal" mechanic survives — drag becomes tap on touch
devices, but the slots and conventions are the same.

## Interactive journal and scope finder

The intake flow is **live-reactive**, not a static fill-out-and-submit form.
Every author answer reshapes the next set of options visibly:

- After Q1 (question): the analyzer extracts a normalized form; author confirms
  or revises; the candidate journal pool starts as ~1500 journals
- After Q2 (claim type): validity route options narrow; pool shrinks visibly
  ("from 1500 to 380 candidates")
- After Q3 (audience): tier filter applies; pool shrinks again
- After Q4 (provenance): related-work weighting applied
- After Q5 (falsifiability): validity-rigor filter; pool reaches a workable size
  (typically 15–50 candidates)

The shrinking pool is a **live progress signal** the author sees. They can
trace cause and effect — "my Q3 answer just dropped my favorite journal off
the list, let me reconsider Q3 or accept that the journal isn't a good fit."

Pool shrink is visualized as a count + a delta animation + a "what just got
filtered out, and why" expandable trace. This catches misalignment early and
turns intake into guided exploration rather than survey-completion.

## Live evidence with every journal judgment

Every judgment EAIOU emits about journals (suggester ranking, fit score,
drift assessment, restructure recommendation, falsifiability score against
journal norms) is accompanied by the **live evidence set used to make the
judgment** — actual recent articles, clickable to inspect.

If the author wants to disagree, they must engage with the cited articles.
Abstract complaints fail because the evidence is on the table. Informed
disagreements are honored — authors who read the cited articles and produce a
counter-argument can override the recommendation, with the override and its
rationale logged via `intellid.log` for editorial review later.

This holds EAIOU to its own standard: show your work, cite your sources,
reason from evidence. Same discipline the system asks of authors elsewhere.

Every judgment-emitting service (`journal.family_suggest`,
`journal.candidates_filter`, `falsifiability.score`, `scope.reconciliation`,
`manuscript.intent_compare`) returns an `evidence[]` array with source
pointers, retrieval-time metadata, and per-source contribution weights:

```json
{
  "score": "low",
  "evidence": [
    {
      "source": "doi:10.1371/example.1",
      "title": "...",
      "weight": 0.34,
      "retrieved": "2026-05-02T20:15:00Z",
      "citation_used_in_reasoning": "Methods section, paragraph 2"
    }
  ],
  "reasoning_trace": "..."
}
```

## Service-level guarantees enabled by the rigidity

Because intake is forced through one of two paths (FRESH | RESTRUCTURED), and
rails are locked at journal selection, EAIOU can sell **outcomes, not effort**:

| Tier | Guarantee |
|---|---|
| Fit Guarantee | If a manuscript exits EAIOU's submission-readiness check and the chosen journal desk-rejects on *format* grounds, EAIOU refunds and restructures into a sibling journal at no cost |
| Restructure Guarantee | RESTRUCTURED intake completes within N business days or refund |
| Time-to-Submission | FRESH path → first-draft in N weeks for a given paper type |
| Match Guarantee | If the journal-family suggester's top-1 has measurably below-cohort acceptance rate, suggester re-runs for free |

These guarantees are only possible because the architecture is rigid. Loose
tools can't sell outcomes; only EAIOU can, because intake shape is controlled.

## Journal partnership — the upstream-filter pivot

EAIOU is not a competitor to journals. EAIOU is an **upstream filter** that
benefits journals by reducing their format-burden, desk-reject rate, and
scope-mismatch rate. This makes journal partnerships a natural B2B revenue
layer in addition to author-side authoring fees:

| For the journal | For EAIOU |
|---|---|
| Manuscripts arrive structurally pre-conformant → lower copy-edit burden | Authoring fees + subscription |
| Lower desk-reject rate → better author experience metric | Higher fit-rate → SLA guarantees deliverable |
| Better scope-fit (validity-route filter) → higher relevance per submission | Lower restructure refunds |
| Editorial priorities surfaced *before* submission → opportunity to shape pipeline | Premium signal source for the suggester |

Once journals see this, partnership opportunities open private signal channels
to EAIOU:

- Current editorial priorities (what topics the journal is actively seeking)
- Section-format preferences not in public guidelines
- Topic priority weights and real-time hotness signals
- Reviewer-pool preferences ("this kind of work goes to pool A in form B")
- Pre-screening lanes ("we'd like to see manuscripts on topic X before public submission")
- Beyond-public acceptance trend data

The rigidity that looks like friction to the author is the *exact same*
property that earns SLAs and partnerships. A loose tool can sell neither.

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
