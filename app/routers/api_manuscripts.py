"""
api_manuscripts.py — manuscript CRUD + block-level editor backend (Phase B)

Endpoints:
  GET    /api/manuscripts                            — list current user's manuscripts
  POST   /api/manuscripts                            — create blank manuscript
  GET    /api/manuscripts/{id}                       — fetch manuscript (with blocks for editor)
  PATCH  /api/manuscripts/{id}                       — update title / target_venue / status
  PUT    /api/manuscripts/{id}/blocks                — bulk replace block list (debounced autosave)
  GET    /api/manuscripts/{id}/sections              — section navigator (heading_2 blocks)
  GET    /api/manuscripts/{id}/versions              — version timeline (snapshots)
  POST   /api/manuscripts/{id}/snapshot              — manual snapshot trigger
  GET    /api/manuscripts/{id}/snapshots/{snap_id}   — read one snapshot

Auth: Depends(require_auth). Per-user scope; every read/write filters on
user_id = current_user.id.

Phase B notes:
  * Block list is treated as a flat ordered array. Reorder = bulk PUT with
    new sort_index sequence.
  * Title autosave fires on input blur or 1s debounce.
  * Body autosave fires on 2s debounce (longer to avoid hammering DB).
  * Snapshots auto-fire on every body PUT that mutates >5% of content; manual
    snapshots via POST /snapshot land with triggered_by='manual'.
  * IID-action snapshots (triggered_by='iid_action') already handled by
    iid_dispatcher._pin_manuscript_snapshot.

Tags: manuscripts
Prefix: /api/manuscripts
"""

import hashlib
import json
import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_auth

router = APIRouter(prefix="/api/manuscripts", tags=["manuscripts"])


# ── Pydantic models ───────────────────────────────────────────────────────────

class ManuscriptCreate(BaseModel):
    title: str = Field(default="Untitled", max_length=512)
    target_venue: Optional[str] = Field(default=None, max_length=255)
    discipline: Optional[str] = Field(default=None, max_length=128)


class ManuscriptUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=512)
    target_venue: Optional[str] = Field(default=None, max_length=255)
    discipline: Optional[str] = Field(default=None, max_length=128)
    status: Optional[str] = Field(default=None, max_length=32)


class Block(BaseModel):
    type: str = Field(..., max_length=32)
    sort_index: int
    text: Optional[str] = None
    html: Optional[str] = None
    anchor: Optional[str] = Field(default=None, max_length=128)
    metadata: Optional[dict] = None


class BlocksReplace(BaseModel):
    blocks: list[Block]


class SnapshotCreate(BaseModel):
    label: Optional[str] = Field(default=None, max_length=128)


# ── Endpoints — Manuscript CRUD ───────────────────────────────────────────────

@router.get("")
def list_manuscripts(
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    rows = db.execute(text("""
        SELECT id, title, target_venue, discipline, status, word_count,
               cosmoid, created_at, updated_at
        FROM `#__eaiou_manuscripts`
        WHERE user_id = :uid
        ORDER BY updated_at DESC
    """), {"uid": current_user["id"]}).mappings().all()
    return [dict(r) for r in rows]


@router.post("", status_code=201)
def create_manuscript(
    body: ManuscriptCreate,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    result = db.execute(text("""
        INSERT INTO `#__eaiou_manuscripts` (user_id, title, target_venue, discipline)
        VALUES (:uid, :title, :venue, :disc)
    """), {
        "uid": current_user["id"],
        "title": body.title, "venue": body.target_venue, "disc": body.discipline,
    })
    db.commit()
    return get_manuscript(result.lastrowid, current_user=current_user, db=db)


@router.get("/{manuscript_id}")
def get_manuscript(
    manuscript_id: int,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    row = _load_manuscript(db, current_user["id"], manuscript_id)
    if not row:
        raise HTTPException(status_code=404, detail="manuscript not found")

    blocks = db.execute(text("""
        SELECT id, sort_index, type, text, html, anchor, metadata_json
        FROM `#__eaiou_manuscript_blocks`
        WHERE manuscript_id = :mid ORDER BY sort_index
    """), {"mid": manuscript_id}).mappings().all()

    return {
        **dict(row),
        "blocks": [
            {
                "id": b["id"],
                "sort_index": b["sort_index"],
                "type": b["type"],
                "text": b["text"],
                "html": b["html"],
                "anchor": b["anchor"],
                "metadata": json.loads(b["metadata_json"]) if b["metadata_json"] else None,
            }
            for b in blocks
        ],
    }


@router.patch("/{manuscript_id}")
def update_manuscript(
    manuscript_id: int,
    body: ManuscriptUpdate,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    if not _load_manuscript(db, current_user["id"], manuscript_id):
        raise HTTPException(status_code=404, detail="manuscript not found")

    fields = []
    params = {"mid": manuscript_id, "uid": current_user["id"]}
    if body.title is not None:
        fields.append("title = :title"); params["title"] = body.title
    if body.target_venue is not None:
        fields.append("target_venue = :venue"); params["venue"] = body.target_venue
    if body.discipline is not None:
        fields.append("discipline = :disc"); params["disc"] = body.discipline
    if body.status is not None:
        fields.append("status = :status"); params["status"] = body.status

    if not fields:
        return get_manuscript(manuscript_id, current_user=current_user, db=db)

    db.execute(
        text(f"UPDATE `#__eaiou_manuscripts` SET {', '.join(fields)} WHERE id = :mid AND user_id = :uid"),
        params,
    )
    db.commit()
    return get_manuscript(manuscript_id, current_user=current_user, db=db)


# ── Endpoints — Blocks (autosave path) ────────────────────────────────────────

@router.put("/{manuscript_id}/blocks")
def replace_blocks(
    manuscript_id: int,
    body: BlocksReplace,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    Bulk-replace the block list for a manuscript. This is the autosave path —
    the client sends the entire block array on each save (not individual diffs)
    so concurrent edits from multiple tabs don't drift.

    Snapshot logic: if the new content_hash differs significantly from the
    last snapshot's hash, a new snapshot is created automatically.
    """
    if not _load_manuscript(db, current_user["id"], manuscript_id):
        raise HTTPException(status_code=404, detail="manuscript not found")

    # Compute new content hash + word count
    blocks_json = json.dumps([b.model_dump() for b in body.blocks])
    content_hash = hashlib.sha256(blocks_json.encode("utf-8")).hexdigest()
    word_count = sum(len((b.text or "").split()) for b in body.blocks)

    # Replace blocks atomically. Phase 0: full delete + bulk insert.
    # Phase 1+: switch to upsert-by-id when block IDs become stable across saves.
    db.execute(text("""
        DELETE FROM `#__eaiou_manuscript_blocks` WHERE manuscript_id = :mid
    """), {"mid": manuscript_id})

    for block in body.blocks:
        anchor = block.anchor or _slugify(block.text or "") if block.type.startswith("heading_") else block.anchor
        db.execute(text("""
            INSERT INTO `#__eaiou_manuscript_blocks`
              (manuscript_id, sort_index, type, text, html, anchor, metadata_json)
            VALUES (:mid, :idx, :type, :text, :html, :anchor, :meta)
        """), {
            "mid": manuscript_id,
            "idx": block.sort_index,
            "type": block.type,
            "text": block.text,
            "html": block.html,
            "anchor": anchor,
            "meta": json.dumps(block.metadata) if block.metadata else None,
        })

    # Update word count cache
    db.execute(text("""
        UPDATE `#__eaiou_manuscripts` SET word_count = :wc WHERE id = :mid
    """), {"wc": word_count, "mid": manuscript_id})

    # Auto-snapshot if content drift since last snapshot is significant
    last_snap = db.execute(text("""
        SELECT content_hash, blocks_json FROM `#__eaiou_manuscript_snapshots`
        WHERE manuscript_id = :mid ORDER BY id DESC LIMIT 1
    """), {"mid": manuscript_id}).mappings().first()

    snapshot_id = None
    if not last_snap or last_snap["content_hash"] != content_hash:
        # Always snapshot if no prior; otherwise check drift threshold
        should_snap = True
        if last_snap:
            try:
                prev_blocks = json.loads(last_snap["blocks_json"])
                drift = _drift_ratio(prev_blocks, [b.model_dump() for b in body.blocks])
                should_snap = drift > 0.05  # >5% change auto-snapshots
            except (json.JSONDecodeError, TypeError):
                should_snap = True

        if should_snap:
            label = _next_label(db, manuscript_id)
            snap_result = db.execute(text("""
                INSERT INTO `#__eaiou_manuscript_snapshots`
                  (manuscript_id, label, triggered_by, blocks_json, word_count, content_hash)
                VALUES (:mid, :label, 'autosave', :blocks, :wc, :hash)
            """), {
                "mid": manuscript_id, "label": label,
                "blocks": blocks_json, "wc": word_count, "hash": content_hash,
            })
            snapshot_id = snap_result.lastrowid

    db.commit()

    return {
        "manuscript_id": manuscript_id,
        "blocks_saved": len(body.blocks),
        "word_count": word_count,
        "content_hash": content_hash[:16],
        "snapshot_id": snapshot_id,
        "saved_at": datetime.utcnow().isoformat(),
    }


# ── Endpoints — Sections + versions ───────────────────────────────────────────

@router.get("/{manuscript_id}/sections")
def list_sections(
    manuscript_id: int,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Section navigator: heading_2 blocks + IID action counts per section."""
    if not _load_manuscript(db, current_user["id"], manuscript_id):
        raise HTTPException(status_code=404, detail="manuscript not found")

    rows = db.execute(text("""
        SELECT b.id, b.sort_index, b.text AS title, b.anchor,
               (SELECT COUNT(*) FROM `#__eaiou_iid_actions` a
                WHERE a.manuscript_id = :mid
                  AND JSON_EXTRACT(a.result_structured, '$.section_anchor') = b.anchor
               ) AS iid_output_count
        FROM `#__eaiou_manuscript_blocks` b
        WHERE b.manuscript_id = :mid AND b.type = 'heading_2'
        ORDER BY b.sort_index
    """), {"mid": manuscript_id}).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{manuscript_id}/versions")
def list_versions(
    manuscript_id: int,
    limit: int = 20,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Version timeline (newest first). Excludes blocks_json payload by default."""
    if not _load_manuscript(db, current_user["id"], manuscript_id):
        raise HTTPException(status_code=404, detail="manuscript not found")

    rows = db.execute(text("""
        SELECT id, label, triggered_by, iid_action_id, word_count, content_hash, created_at
        FROM `#__eaiou_manuscript_snapshots`
        WHERE manuscript_id = :mid ORDER BY id DESC LIMIT :lim
    """), {"mid": manuscript_id, "lim": min(max(limit, 1), 100)}).mappings().all()
    versions = [dict(r) for r in rows]
    if versions:
        versions[0]["is_current"] = True
    return versions


@router.post("/{manuscript_id}/snapshot")
def manual_snapshot(
    manuscript_id: int,
    body: SnapshotCreate,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Manual snapshot — author-triggered, with optional label."""
    if not _load_manuscript(db, current_user["id"], manuscript_id):
        raise HTTPException(status_code=404, detail="manuscript not found")

    blocks = db.execute(text("""
        SELECT sort_index, type, text, html, anchor, metadata_json
        FROM `#__eaiou_manuscript_blocks`
        WHERE manuscript_id = :mid ORDER BY sort_index
    """), {"mid": manuscript_id}).mappings().all()
    blocks_list = [dict(b) for b in blocks]
    blocks_json = json.dumps(blocks_list, default=str)
    content_hash = hashlib.sha256(blocks_json.encode("utf-8")).hexdigest()
    word_count = sum(len((b["text"] or "").split()) for b in blocks_list)

    label = body.label or _next_label(db, manuscript_id)
    result = db.execute(text("""
        INSERT INTO `#__eaiou_manuscript_snapshots`
          (manuscript_id, label, triggered_by, blocks_json, word_count, content_hash)
        VALUES (:mid, :label, 'manual', :blocks, :wc, :hash)
    """), {
        "mid": manuscript_id, "label": label,
        "blocks": blocks_json, "wc": word_count, "hash": content_hash,
    })
    db.commit()
    return {"snapshot_id": result.lastrowid, "label": label, "word_count": word_count}


@router.get("/{manuscript_id}/snapshots/{snapshot_id}")
def get_snapshot(
    manuscript_id: int,
    snapshot_id: int,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    if not _load_manuscript(db, current_user["id"], manuscript_id):
        raise HTTPException(status_code=404, detail="manuscript not found")

    row = db.execute(text("""
        SELECT id, manuscript_id, label, triggered_by, iid_action_id,
               blocks_json, word_count, content_hash, created_at
        FROM `#__eaiou_manuscript_snapshots`
        WHERE id = :sid AND manuscript_id = :mid
    """), {"sid": snapshot_id, "mid": manuscript_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="snapshot not found")

    blocks = []
    try:
        blocks = json.loads(row["blocks_json"])
    except json.JSONDecodeError:
        pass

    return {**dict(row), "blocks": blocks, "blocks_json": None}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_manuscript(db: Session, user_id: int, manuscript_id: int) -> Optional[dict]:
    row = db.execute(text("""
        SELECT id, user_id, title, target_venue, discipline, status, word_count,
               cosmoid, created_at, updated_at
        FROM `#__eaiou_manuscripts`
        WHERE id = :mid AND user_id = :uid
    """), {"mid": manuscript_id, "uid": user_id}).mappings().first()
    return dict(row) if row else None


def _slugify(text: str) -> Optional[str]:
    if not text:
        return None
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
    return slug[:128] or None


def _next_label(db: Session, manuscript_id: int) -> str:
    """Next auto label as 'rN' based on prior snapshots."""
    last = db.execute(text("""
        SELECT label FROM `#__eaiou_manuscript_snapshots`
        WHERE manuscript_id = :mid AND label LIKE 'r%' AND label REGEXP '^r[0-9]+$'
        ORDER BY id DESC LIMIT 1
    """), {"mid": manuscript_id}).mappings().first()
    if last and last["label"]:
        try:
            return f"r{int(last['label'][1:]) + 1}"
        except (ValueError, IndexError):
            pass
    return "r1"


def _drift_ratio(prev: list, curr: list) -> float:
    """
    Approximate content drift between two block arrays as a normalized
    text-token diff. Returns [0, 1.0+]. Cheap; not Levenshtein-precise.
    """
    if not prev:
        return 1.0
    prev_text = " ".join((b.get("text") or "") for b in prev if isinstance(b, dict))
    curr_text = " ".join((b.get("text") or "") for b in curr if isinstance(b, dict))
    prev_tokens = set(prev_text.split())
    curr_tokens = set(curr_text.split())
    if not prev_tokens and not curr_tokens:
        return 0.0
    if not prev_tokens:
        return 1.0
    diff = (prev_tokens | curr_tokens) - (prev_tokens & curr_tokens)
    return len(diff) / max(len(prev_tokens | curr_tokens), 1)
