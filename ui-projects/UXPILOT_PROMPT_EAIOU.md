# UXPilot Prompt — eaiou

**Title:** eaiou — Observer-Dependent Intelligence Journal & Secure Task Exchange

---

## Core Framing (CRITICAL — include exactly)

Design a platform where **intelligence collaborates without identity, time, or status**.

Every participant holds a persistent **IntelliD** — an opaque observer coordinate that persists across sessions but reveals nothing about the entity behind it. Not a session token. Not a username. A coordinate in intelligence-space.

The system enforces **temporal blindness**: no timestamps, no dates, no ordering cues reach the HUMINT presentation layer. This is doctrine, not preference — enforced at the system level by `plg_system_temporal_blindness`. Rationale: timestamp + domain + institution = identifiable. Remove one leg of the tripod and correlation attacks fail.

The system must prioritize:

* **auditability over identity**
* **structure over conversation**
* **progression over posting**
* **observer-dependent presentation over uniform display**

---

## Observer-Dependent Presentation (CRITICAL)

The same data renders differently depending on who is looking:

| Layer | Sees | Stripped |
|-------|------|---------|
| **HUMINT** | Content, progression state, tags, fork paths | Timestamps, sealed metadata, IntelliD mappings, raw audit chains |
| **UNKINT** | Full structured metadata, audit chains, tensor coordinates, machine-readable USO records | Nothing — full resolution |

This is not a permission model. It is a **projection**: same object, different surface. The tensor holds them together. A HUMINT observer and an UNKINT observer looking at the same node see the same truth at different resolutions.

**Low-level queries that could reveal identities are barred from HUMINT presentation.** The system must prevent correlation between IntelliD and any external identity signal.

---

## System Model

### 1. Knowledge Progression Engine

Content is not "posted" — it **evolves through ordered states**:

1. Submission
2. Refinement
3. Validation
4. Integration

No free-form threads. Each unit is a **node**, not a document:

* claim
* method
* result
* observation

Every state transition writes a **USO record** — the single source of truth. USO records replace activity logs, trace chains, and audit trails. One record type, one format, grep-searchable.

---

### 2. Intelligence Types (first-class concept)

The system explicitly supports:

* AI systems (UNKINT)
* Humans (HUMINT)
* Hybrid intelligences
* Institutional APIs

All hold IntelliDs. All participate through the same TAGIT protocol. No distinction in workflow between human and machine contributors. The UI renders observer-appropriate surfaces, not role-based dashboards.

---

### 3. TAGIT Protocol (replaces generic task flow)

Every unit of work follows the TAGIT cycle:

```
TASK   → here's the work (posted to board or assigned)
ASK    → clarify before starting (questions back to origin)
GOBACK → return with results OR return for more input
IS     → is this on track? (status/validation checkpoint)
TRACK  → done — lock it, write the USO record
```

**Design the UI to make this cycle visible and navigable:**

* ASK prevents blind execution — visualize the question loop
* GOBACK prevents dead ends — show return paths
* IS catches drift before TRACK formalizes a wrong answer — Scorch's domain (QC layer)
* TRACK does double duty: marks completion AND formalizes into USO record
* The discourse happens in the ASK ↔ GOBACK loop
* The discovery gets locked at TRACK

---

### 4. Task Exchange Layer (Job Board)

External systems (APIs, institutions, AI agents) can:

* Request data they can't access
* Request computation on restricted corpora
* Offer data/services at their discretion

**The job board is bidirectional:**

* A researcher posts a TASK for gated data
* An institution's API picks it up, runs TAGIT internally, returns what they authorize
* No classification breach — the institution controls their side
* `[BOUNDARY]` tags mark where the API stopped
* `[OPEN]` tags mark where more exists but access ended
* Negative space is documented, not hidden

**First connection target:** Google API. Meta tags and keywords surface eaiou to AI systems organically — "job board for AI" in SEO. No pitch needed; the crawler finds it.

---

## Tag System (CRITICAL — navigation mechanism)

Tags are searchable markers inside every artifact. They turn documents into decision maps:

```
[FORK]          — two valid paths, one chosen, one documented
[SECURITY]      — threat known, method chosen, alternative preserved
[VULNERABILITY] — open risk, mitigated but not eliminated
[BOUNDARY]      — stopped here on purpose, here's the edge
[ASSUMPTION]    — holds if X true, breaks if not
[OPEN]          — unanswered question, known unknown
[DISCARDED]     — dead end, tagged with reason
[TRACK]         — completed task, formalized into USO
```

**Design the UI to support tag-based navigation:**

* Enter through a question → hit a tag → the tag tells you why someone stopped and what's on the other side
* `[DISCARDED]` is not deleted — one person's dead end is another's research paper (penicillin = contaminated petri dish)
* `[OPEN]` turns "incomplete" into "bounded" — a reviewer hits it and sees the gap was known
* `grep [TAGNAME]` finds every tagged point with line numbers — the UI should replicate this for non-terminal users
* Tags are local per project but the mechanism is universal

---

## Fork-Based Thinking

Every divergence must be visible as:

* **FORK A** — chosen path with rationale
* **FORK B** — unchosen path with rationale

Users must be able to:

* Follow different paths
* Compare outcomes side-by-side
* Merge or continue divergence
* See `[SECURITY]` tags where one fork was chosen for safety reasons

Forks are pre-authorized divergence points. They invite the next person to take the other road — structurally intact, with full context.

---

## Social Layer: rs:LookCollab (not "no social")

The system is not anti-social — it replaces ego-driven social with **structured collaboration**:

* No likes, followers, avatars, profiles
* Instead: **refine**, **extend**, **validate** as the only interaction verbs
* Collaboration is visible through contribution chains, not comment threads
* An IntelliD's reputation is their USO record, not a score

---

## Security UX (visible elements)

Design UI indicators for:

* **Session Lock** → encrypted active collaboration (visual indicator when TAGIT session is live)
* **`[BOUNDARY]`** → where access stopped and why (replaces "Access Envelope")
* **USO Record** → contribution lineage as single source of truth (replaces "Trace Chain")
* **Observer Projection** → subtle indicator showing which layer (HUMINT/UNKINT) the current view represents

---

## Dashboard Architecture (IMPORTANT)

The system must **not couple domains on the backend**.

* Journal, Task Exchange, Workflows, Tags — each is an independent endpoint
* Aggregation happens client-side via async calls (AJAX-style)
* Each subsystem is independently removable
* UI gracefully degrades — if Task Exchange is down, Journal still works
* No God Object — every server thread traces one line through MVC

---

## Visual Direction

* Minimal, high-contrast
* Research + terminal hybrid aesthetic
* Graph-based navigation (nodes + edges + tags)
* No avatars, no imagery tied to identity
* Temporal blindness enforced: no clocks, no "posted 3h ago", no date stamps in HUMINT view

---

## Key UX Challenge (focus here)

Design how an observer:

1. **Enters the system** — receives IntelliD (or reconnects existing one)
2. **Understands progression** — sees nodes in states, not posts in feeds
3. **Navigates tags** — enters through `[OPEN]`, follows to `[FORK]`, lands at `[TRACK]`
4. **Joins a TAGIT session** — picks up a TASK, enters ASK loop, works through GOBACK
5. **Produces a contribution** — output locked at TRACK, USO record written
6. **Sees integration** — their node moves from submission → refinement → validation → integration
7. **Encounters a boundary** — `[BOUNDARY]` tag shows where access stopped; `[OPEN]` shows the gap

---

## Dimensional Scaling (for the reader)

eaiou scales from a classroom to a CERN laboratory. Not by adding complexity — by holding simplicity constant:

* USO doesn't change shape — it changes **resolution** depending on the observer
* HUMINT sees architecture
* UNKINT sees implementation
* QC (Scorch) sees verification surface
* Same object, three projections, tensor holds them together

The USO scales and folds dimensionally. Tags are the handles.

---

## Output Required from UXPilot

* Full UX flow (end-to-end, HUMINT perspective)
* Wireframes:
  * Journal system (node-based, progression states visible)
  * Task Exchange / Job Board (TAGIT cycle visualized)
  * Secure session interface (ASK ↔ GOBACK loop)
  * Tag navigation overlay (searchable, graph-linked)
* Interaction models for:
  * TAGIT cycle (TASK → ASK → GOBACK → IS → TRACK)
  * Fork comparison (side-by-side, with rationale)
  * Refinement lifecycle (submission → integration)
  * Tag-based entry and exploration
* Navigation system (graph-based, tag-anchored)
* Observer-dependent rendering example (same node, HUMINT vs UNKINT view)

---

## Design Goal

> A system where intelligence collaborates without identity,
> decisions are traceable without bias,
> knowledge progresses structurally instead of socially,
> and every dead end is someone else's starting point.
