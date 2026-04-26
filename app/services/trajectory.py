"""
eaiou — Trajectory Service

A trajectory is the directional path of a manuscript through the pipeline.
Each paper starts with one trajectory. Forks occur when divergence between
consecutive snapshots crosses a threshold.

Fork rules (from integrity thresholds):
  DRIFT   (delta ≤ 0.10)  — same trajectory, no action
  BRANCH  (delta ≤ 0.30)  — document the new direction; both trajectories coexist
  REWRITE (delta >  0.30)  — hard fork; prior evidence does not correspond to
                             current manuscript; warn + new trajectory required

Trajectory tree:
  paper starts with one root trajectory (parent_id = NULL)
  each fork creates a child trajectory (parent_id = forked_from.id)
  REWRITE deactivates parent; BRANCH keeps parent active (coexistence)
  active = 1 → current trajectory for this paper (there can be multiple for BRANCH)

The trajectory record is provenance, not a gate. Creating one does not block
submission. It documents that the manuscript changed direction at a given point.
"""

from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text

from .integrity import BRANCH_THRESHOLD, DRIFT_THRESHOLD, classify_divergence


# ── Ensure root trajectory ────────────────────────────────────────────────────

def ensure_root_trajectory(paper_id: int, db: Session) -> int:
    """
    Ensure a root trajectory record exists for this paper.
    Idempotent — returns existing id if already present.
    """
    existing = db.execute(text(
        "SELECT id FROM `#__eaiou_trajectories` "
        "WHERE paper_id = :pid AND parent_id IS NULL "
        "ORDER BY created_at ASC LIMIT 1"
    ), {"pid": paper_id}).fetchone()

    if existing:
        return existing[0]

    db.execute(text(
        "INSERT INTO `#__eaiou_trajectories` "
        "(paper_id, parent_id, agent, method_class, active) "
        "VALUES (:pid, NULL, 'human', 'standard_authoring', 1)"
    ), {"pid": paper_id})
    db.commit()
    return db.execute(text("SELECT LAST_INSERT_ID()")).scalar()


# ── Fork detection from snapshot chain ───────────────────────────────────────

def detect_and_record_forks(paper_id: int, db: Session) -> list[dict]:
    """
    Scan the snapshot chain for this paper and create trajectory fork records
    wherever BRANCH or REWRITE divergence is detected.

    Called at seal time, after all snapshots have been captured.
    Idempotent — skips gates that already have a trajectory record.

    Returns list of fork dicts created this call.
    """
    # Load snapshot chain in creation order
    snapshots = db.execute(text(
        "SELECT id, gate_code, divergence_from_prior, change_class, created_at "
        "FROM `#__eaiou_paper_snapshots` "
        "WHERE paper_id = :pid AND divergence_from_prior IS NOT NULL "
        "ORDER BY created_at ASC, id ASC"
    ), {"pid": paper_id}).mappings().all()

    # Fetch existing fork records so we don't duplicate
    existing_forks = set(db.execute(text(
        "SELECT fork_reason FROM `#__eaiou_trajectories` "
        "WHERE paper_id = :pid AND parent_id IS NOT NULL"
    ), {"pid": paper_id}).scalars().all())

    # Ensure root exists
    root_id = ensure_root_trajectory(paper_id, db)

    # Get the currently active trajectory (most recent leaf)
    active = db.execute(text(
        "SELECT id FROM `#__eaiou_trajectories` "
        "WHERE paper_id = :pid AND active = 1 "
        "ORDER BY created_at DESC LIMIT 1"
    ), {"pid": paper_id}).fetchone()
    current_parent_id = active[0] if active else root_id

    forks_created = []
    now = datetime.now(timezone.utc)

    for snap in snapshots:
        gate_code   = snap["gate_code"]
        delta       = float(snap["divergence_from_prior"])
        change_class = snap["change_class"] or classify_divergence(delta)

        if change_class not in ("BRANCH", "REWRITE"):
            continue

        # Build a stable fork_reason key for deduplication
        fork_key = f"{gate_code}:{change_class}:{delta:.4f}"
        if fork_key in existing_forks:
            continue

        if change_class == "REWRITE":
            # Hard fork — deactivate current trajectory, new one takes over
            db.execute(text(
                "UPDATE `#__eaiou_trajectories` SET active = 0 "
                "WHERE paper_id = :pid AND active = 1"
            ), {"pid": paper_id})
            agent       = "rewrite_detected"
            method_class = "rewrite"
        else:
            # BRANCH — parallel trajectory, parent stays active
            agent       = "branch_detected"
            method_class = "branch"

        fork_reason = (
            f"{change_class} at gate {gate_code} — "
            f"divergence {delta:.2%} from prior snapshot"
        )

        db.execute(text(
            "INSERT INTO `#__eaiou_trajectories` "
            "(paper_id, parent_id, agent, method_class, active, fork_reason, created_at) "
            "VALUES (:pid, :parent, :agent, :method, 1, :reason, :now)"
        ), {
            "pid":    paper_id,
            "parent": current_parent_id,
            "agent":  agent,
            "method": method_class,
            "reason": fork_reason,
            "now":    now,
        })
        db.commit()

        new_id = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
        current_parent_id = new_id
        existing_forks.add(fork_key)

        forks_created.append({
            "trajectory_id": new_id,
            "gate_code":     gate_code,
            "change_class":  change_class,
            "divergence":    delta,
            "fork_reason":   fork_reason,
        })

    return forks_created


# ── Query helpers ─────────────────────────────────────────────────────────────

def get_trajectory_tree(paper_id: int, db: Session) -> list[dict]:
    """
    Return the full trajectory tree for a paper.
    Ordered by creation time — root first, then forks in discovery order.
    """
    rows = db.execute(text(
        "SELECT id, parent_id, agent, method_class, active, fork_reason, created_at "
        "FROM `#__eaiou_trajectories` "
        "WHERE paper_id = :pid ORDER BY created_at ASC"
    ), {"pid": paper_id}).mappings().all()

    return [
        {
            **dict(r),
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        }
        for r in rows
    ]
