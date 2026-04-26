# G5 Review — IntelliD / CosmoID / UHA Stack Alignment
**Date:** 2026-04-10
**Source:** External GPT (G5) — provided in response to eaiou_governance_2026-04-10.pdf
**Filed by:** Eric D. Martin | ORCID 0009-0006-5944-1742
**Retrieve:** "bring up the G5 IntellID/CosmoID review"

---

## Summary

G5 independently reviewed the eaiou governance PDF and aligned the IntellID concept with UHA and CosmoID. This record captures what was confirmed, what was corrected, and what was implemented.

---

## What G5 Confirmed

- IntelliD architecture is conceptually sound ("not just identity — addressable cognition")
- Temporal Blindness implementation is correctly done, including `NO INDEX` on sealed fields ("elite-level thinking")
- Intelligence Blindness pairing with Temporal Blindness is correct
- Authoring layer vs publishing gateway separation is correct
- AntOp right of first refusal ("AntOp connects via their own MCP, we provide the API")

---

## What G5 Flagged (and Corrective Actions Taken)

### 1. `id DESC` is a Temporal Blindness leak

**G5 finding:** `ORDER BY q_overall IS NULL, q_overall DESC, id DESC` — the `id DESC` fallback is a proxy for submission order. Higher `id` = later submission. This reintroduces time as a hidden ordering axis.

**Fix applied (2026-04-10):** Replaced `id DESC` with `paper_uuid ASC` in both `main.py` and `routers/papers.py`. UUIDv4 is randomly generated at creation — carries no temporal signal.

---

### 2. IntelliD not in schema

**G5 finding:** IntelliD is defined in governance but absent from the database.

**Fix applied (2026-04-10):** Created `python_cms_migration_002.sql`:
- `#__eaiou_intellid_registry` — one row per contributing intelligence instance
- `#__eaiou_intellid_contributions` — contribution graph (intellid → artifact → relation)
- `#__eaiou_observation_log` — optional UHA observation layer

---

### 3. Instance vs Type separation

**G5 finding:** Multiple Claude sessions within a paper must be distinct IntelliDs, not collapsed into one. Schema must support `instance_hash` to distinguish session-specific instances.

**Resolution:** `intellid_registry` has `model_family` (disclosed, e.g. "claude") and `instance_hash` (sealed SHA256 of session-specific context). These are separate fields — type is public, instance mapping is sealed.

---

### 4. CosmoID belongs at creation, not publication

**G5 finding:** CosmoID should be minted when a record is created, not when it's published. It represents the existence of a state, not its visibility.

**Fix applied (2026-04-10):**
- Added `cosmoid CHAR(36) UNIQUE` to `#__eaiou_papers`
- `cosmoid = str(uuid.uuid4())` minted in `POST /papers/submit` alongside `paper_uuid`
- CosmoID is permanent — persists through tombstone

---

### 5. Tombstone model needs explicit states

**G5 finding:** Deletion should be `tombstone`, never actual deletion. CosmoID persists. States should be explicit.

**Fix applied (2026-04-10):** Added to `#__eaiou_papers`:
- `tombstone_state ENUM('private','revivable','reusable','public_unspace')`
- `tombstone_reason TEXT`
- `tombstone_at DATETIME`
- `tombstone_by INT`

NULL = active record. Tombstone is a state transition, not a deletion.

---

## The Clean Stack (as defined by G5 review)

```
Work            → sealed into immutable publication record
Contributors    → represented by IntelliDs
Contributor ctx → fingerprinted by CosmoID (attached to IntelliD instance)
Observation     → optionally encoded into UHA (only when observed/read)
```

### Stack Axes

| Axis | System | What it solves |
|---|---|---|
| Where | UHA | Frame-agnostic position |
| When | Temporal Blindness | Hidden from evaluation |
| Who/What | IntelliD | Instance-specific identity |
| Context | CosmoID | Operating parameter fingerprint |

---

## Stack Invariants

- CosmoID is minted at record creation — never null after first write
- CosmoID persists through tombstone — it fingerprints a state that existed
- IntelliD and CosmoID are not the same: IntelliD = which intelligence; CosmoID = under what context
- `id DESC` is NEVER a valid tiebreaker — use `paper_uuid ASC` (random UUID4)
- UHA is optional, only on observed/read events — not on every paper record

---

## G5 Instruction to Claude (exact)

> "Implement:
> 1. `intellid_registry` — UUID, type, instance_hash, connector, scope
> 2. `intellid_contributions` — intellid → artifact → relation
> 3. Remove string-based attribution dependency
> 4. Replace `id DESC` fallback sorting"

Items 1, 2, 4 implemented in this session. Item 3 (string-based attribution dependency) is Phase 2 — the `attribution_log` table remains as a legacy bridge; the graph is authoritative going forward.

---

## Open Items (not yet implemented)

- Authentication handshake for AntOp MCP connector
- Permission model per IntelliD
- Session lifecycle for AI IntelliDs
- UHA observation encoding (observation_log table exists; encoding logic is Phase 2)
- Legal/ToS language for tombstoned artifact reuse

---

*Filed for team review.*
*Retrieve: "bring up the G5 IntellID/CosmoID review"*
