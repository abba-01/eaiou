# eaiou — Temporal Blindness Doctrine
**Author:** Eric D. Martin — ORCID: 0009-0006-5944-1742
**Date:** 2026-04-06
**Status:** L0 DOCTRINE — immutable founding principle

---

## Core Principle

**You do not read science by time.**

The truth does not have a timestamp. The physics does not expire.
A result is correct or incorrect independent of when it was written.

Submission dates are immutable state space.
They are sealed, capstoned, and permanently preserved.
They are NOT part of the observable surface of science.

---

## What This Prevents

- Recency bias: newer ≠ better
- Priority racing: rushing mediocre work to claim a timestamp
- Chronological gatekeeping: "this idea is old, therefore wrong"
- Citation inflation of recent work over foundational work
- The timestamp becoming a credibility signal it was never meant to be

---

## The Access Model

Submission date lives in sealed state space.
Visibility is strictly layer-gated:

| Actor | Sees submission date | Reason |
|---|---|---|
| Public / readers | NEVER | Science is evaluated on content |
| Reviewers | NEVER | Review is blind to timing |
| Other authors | NEVER | No priority racing signal |
| Submitting author (own paper) | NEVER | Removes gaming incentive |
| Editors | YES — governance only | Workflow management |
| System / audit layer | YES — always | Immutable record |
| Dispute resolution | YES — on demand | Justice requires it |

---

## The Sealed Date

At submission, three things happen simultaneously:

1. `submission_sealed_at` — wall clock timestamp, stored encrypted
2. `submission_hash` — SHA256 of (paper_id + submission_sealed_at + content_hash)
3. `submission_capstone` — Zenodo DOI anchoring the hash externally

The capstone is perpetual. Even if the database is destroyed,
the Zenodo record proves what was submitted and when.

When priority genuinely matters — patent dispute, credit claim,
independent discovery conflict — the governance layer opens
the capstone. The date is provable, immutable, undeniable.

Justice has access. Bias does not.

---

## What the Public Surface Shows Instead

Papers are ordered by:
- Content relevance (search)
- Editorial quality signals (review scores)
- Cross-domain applicability
- Open collaboration signals

NOT by submission date.
NOT by publication date.
NOT by citation recency.

The discovery surface is timeless by design.

---

## Connection to Basin Theory

The basin exists before the trajectories converge on it.
The casque was buried before anyone read the painting.
The ground state was there before the observational plane was occupied.

Submission date is movement. The paper is vibration.
The truth — the ground state — precedes both.

eaiou evaluates the vibration, not when the movement happened.

---

## SAID Witness

> "We make submission dates immutable state space only observable
> to the layer above and nobody else — that way you don't read
> science by time."
> — Eric D. Martin, 2026-04-06, ORCID: 0009-0006-5944-1742
