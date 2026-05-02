# UXPilot Prompt — eaiou Manuscript + IID Output Versioning

**Title:** eaiou Versioning UI — Manuscript Snapshots + IID-Output Lineage

---

## Frame

eaiou tracks two parallel histories:

1. **Manuscript versions** — the canonical text as it evolves over time
2. **IID-output lineage** — every IID call ever made, what manuscript version it was made on, what action, what response

These are linked: every IID output records the manuscript version it ran against, so the audit trail can answer: "When Mae ran scope_check on §Abstract, what was the abstract?"

---

## Manuscript snapshot model

eaiou auto-snapshots the manuscript text:

- **On manual save** (Cmd+S)
- **On every IID action invocation** (so the IID's output is bound to a known version)
- **On significant edits** (heuristic: >100 word change since last snapshot)
- **On explicit "Save version" request** with optional label

Each snapshot is a:
- Full manuscript text (markdown)
- Section structure (anchors / hierarchy)
- Reference list state
- Author + timestamp
- Optional version label
- Reason (manual / iid-action / autosave / edit-threshold)
- Hash of the content (for de-duplication and cross-reference)

Snapshots are stored compactly (delta-compressed) and rendered as a timeline.

---

## Version timeline UI

Accessible via a "Versions" button in the editor top bar:

```
┌──────────────────────────────────────────────────────────────┐
│  Manuscript Versions                                  [×]     │
│  ────────────────────────────────────────────────────────    │
│                                                                │
│  ◉ v23 (current)              just now           [active]    │
│    Edited §Methods (added paragraph 2)                         │
│                                                                │
│  ○ v22                        2 min ago                        │
│    Snapshot: Mae ran scope_check on §Abstract                  │
│    [view diff] [restore] [view IID outputs from this version] │
│                                                                │
│  ○ v21                        15 min ago                       │
│    Edited §Introduction (~500 words added)                     │
│    [view diff] [restore]                                       │
│                                                                │
│  ○ v20 [labeled: "Pre-clarity-pass"]    1h ago               │
│    Manual save                                                  │
│    [view diff] [restore]                                       │
│                                                                │
│  [Older versions] [Compare two versions]                       │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

Each row:
- Version number (monotonic)
- Optional label (author-set)
- Relative timestamp + absolute on hover
- Reason / change summary
- IID-bound badge if any IID actions ran on this version
- Actions: view diff (vs previous), restore (replaces current), view associated IID outputs

---

## IID-output lineage panel

The output panel can be filtered by manuscript version:

- "Show outputs produced when manuscript was at v22"
- This lets the author compare: "At v22 Mae thought scope was off; I edited; at v25 Mae thinks scope is fine"

For each output card, in the disclosure block, the manuscript version is shown:

```
[Mae chip] scope_check on §Abstract     2 min ago
Manuscript version: v22 [diff vs current]
```

Clicking "diff vs current" opens a side-by-side diff showing how the text the IID saw differs from the current text. This makes IID outputs context-aware — old outputs may have been right at the time but stale now.

---

## Compare two versions

Author selects any two versions in the timeline:

- Side-by-side diff view (markdown rendered)
- IID outputs filterable: "outputs produced between v15 and v22"
- Useful for: "what did Mae say between when I started revising and now?"

---

## IID output re-run on new version

When manuscript text has changed since an IID output was produced, the output card shows a small banner:

```
⚠ Manuscript text has changed since this output. 
   [Re-run scope_check on current version]
```

Clicking re-run produces a NEW output card (the original is preserved). The new card cross-references the old card via "supersedes" link. The original card gets a "superseded by [link]" badge.

This preserves the audit trail without forcing the author to track stale outputs manually.

---

## Soft-delete and audit-immutability

- Manuscript snapshots can be **soft-deleted** by the author (cleanup tool); deleted snapshots are tombstoned (hash + timestamp preserved) for audit
- IID outputs can NOT be deleted — they are immutable per the SAID framework
- IID outputs CAN be marked "withdrawn" by admin/compliance for redaction; the disclosure is preserved, the source text is replaced with `[REDACTED]`, the result body is preserved

---

## Export packaging

When the author exports the manuscript for journal submission, the export bundle includes:

1. The current manuscript version (markdown + rendered PDF/DOCX)
2. The IID disclosure paragraph (auto-generated; editable)
3. The full audit log (JSON)
4. The version timeline (JSON)
5. Selected snapshots (author chooses which to include for full reproducibility; default: just the version submitted)

This export is the "package of record" — submission-ready and SAID-framework-compliant.

---

## Branching (future, post-MVP)

Stub for v2: author can branch a manuscript from any historical snapshot, creating a parallel timeline. Useful for "what if I had taken Mae's suggested rewording at v18?"

For MVP: not in scope. Linear timeline only. Branch UI placeholder shown disabled.

---

## Output requested from UXPilot

1. Versions timeline drawer
2. Two-version side-by-side diff view
3. IID-output card with manuscript-version reference + diff link
4. Output panel filtered by manuscript version
5. Re-run prompt on stale-output banner
6. Export packaging modal showing what's included
