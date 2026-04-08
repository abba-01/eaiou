# Plugin 03 — Un Scientific Flag (plg_content_unscientific)
**Status:** Draft (Planning)  
**Target Stack:** Joomla 5.3 (LAMP) — Core-first, strict MVC, no custom DB tables  
**Plugin Type:** `content` (with minimal `system` behaviors if needed)  
**Goal:** Provide a first‑class **“Un Scientific”** marker for Articles to transparently flag **contested, ambiguous, or accuracy‑pending** sections—especially in **human–AI collaboration**—without deleting content. Preserve discoverability and auditability using **Custom Fields, Tags, Workflows, and Action Logs** only.

---

## 1) Purpose
- Mark content that resides in **oMMP un space**: epistemically non‑null but unresolved/contested.  
- Support **human–AI collaboration** contention (accuracy/attribution/clarification).  
- Make flagged areas **visible to readers** (badge/panel), **actionable for editors** (required clarifications), and **searchable** (Smart Search + Tag).  
- Never remove content; instead, record contention, reasoning, and resolution path.

---

## 2) Core‑first Dependencies
- **com_content (Articles)** as the single store.  
- **Custom Fields** (Article) for flag state, reasons, scopes, resolution.  
- **Tags** (optional) to auto‑apply `un-scientific`.  
- **Workflows** to gate state transitions if unresolved.  
- **Action Logs** for provenance of add/remove/resolve actions.  
- **Email Templates** (optional) to notify authors/reviewers.

---

## 3) Events & Hooks (Joomla 5 typed)
- Render:
  - `onContentAfterTitle` → show **Un Scientific** badge when active.  
  - `onContentAfterDisplay` → render **Flag Panel** (reasons, scopes, requested clarifications, status).
- Validate / Enforce:
  - `onContentPrepareForm` → inject helper hints; restrict who may set/clear flag by ACL.  
  - `onContentBeforeSave` → normalize & validate fields; may set tag automatically.  
  - `onContentBeforeChangeState` → optionally block **Publish** until `resolved=Yes` or `editor_override=1`.  
- Normalize:
  - `onContentNormaliseRequestData` → canonicalize scopes, unique IDs for flagged sections (if using anchors).

---

## 4) Content Model (Custom Fields spec)
Create **Field Group: Un Scientific** (Article context).

### A. Flag Switch
- `unsci_active` (Radio: No/Yes) — controls rendering/enforcement.

### B. Scope & Reasons (Repeatable: each contention entry)
- `unsci_entries` (Repeatable Subform):
  - `unsci_scope` (List: Whole Article, Abstract, Methods, Results, Discussion, Figure, Table, Dataset, AI Contribution, Other) **required**
  - `unsci_anchor` (Text — optional fragment/ID to point to a specific section/element)
  - `unsci_reason` (Checkboxes: Accuracy Clarification, Missing Citation, Method Ambiguity, Data Quality, COI Concern, AI Attribution, Ethics, Other) **required**
  - `unsci_notes` (Textarea — brief explanation) **required**
  - `unsci_requested_action` (Checkboxes: Provide Citation, Add Method Detail, Supply Data Link, Run Replication, Reword Claim, Add AI Oversight Notes, Other)
  - `unsci_risk_level` (List: Low, Medium, High)
  - `unsci_createdby` (User — auto-set when created via plugin UI)
  - `unsci_createdat` (Calendar — auto-set)

### C. Resolution
- `unsci_resolved` (Radio: No/Yes)  
- `unsci_resolution_notes` (Textarea — what changed/why) **required if resolved**
- `unsci_resolvedby` (User — auto-set when resolved)  
- `unsci_resolvedat` (Calendar — auto-set)

### D. AI Collaboration Link (optional cross‑ref)
- `unsci_related_ai` (Checkbox — “Flag relates to AI Usage”)  
  - When checked, plugin renders quick link/context from **AI Usage** fields.

### E. Display Controls
- `unsci_display_level` (List: Full, Summary Only, Hidden to Public) — reviewers/editors always see full.

### F. Integrity (auto)
- `unsci_lastcheck` (Calendar — updated on each save)  
- `unsci_complete` (Checkbox — indicates minimally valid record)

---

## 5) Validation Rules
When `unsci_active=Yes`:
- At least **one** `unsci_entries` item with `scope` and `reason`.  
- If `unsci_resolved=Yes` → `unsci_resolution_notes` required; set resolver and timestamp.  
- On pass: set `unsci_complete=1` and update `unsci_lastcheck`.  
- On fail: block **Publish** transition (configurable).

Optional behaviors (params):
- **Auto‑tag** Article with `un-scientific` when active; remove when fully resolved.  
- **Auto‑notify** authors when flagged or when resolution requested.

---

## 6) Rendering (Front‑end)
- **Badge (after title)**: `Un Scientific` with color based on `risk_level` max; hover shows count of entries & status (Resolved/Unresolved).  
- **Panel (after content)**:  
  - Table/list of entries with: Scope, Reasons, Notes, Requested Action, CreatedBy/At.  
  - If `unsci_resolved=Yes`: show Resolution notes & resolver/time.  
  - If `unsci_related_ai=Yes`: add a “See AI Usage” quick link.  
  - Respect `unsci_display_level` (public vs reviewer/editor).

Use **WebAsset API** for minimal CSS/JS (accordion, status chips).

---

## 7) ACL & Workflows
- **Who can flag:** Reviewers, Editors, Admins (configurable); Authors may **view & respond** but cannot clear without Editor action (configurable).  
- **Workflow gating:** if active & unresolved, block `Under Review → Published` unless `editor_override=1`.  
- **Always visible** to Reviewer/Editorial roles regardless of display level.

---

## 8) Action Logs
- On flag set: `UNSCI_SET: entries={n}, maxrisk={level}`  
- On resolve: `UNSCI_RESOLVED: entries={n}, notes_present={bool}`  
- On publish attempt blocked: `UNSCI_BLOCKED: reason=unresolved`

No sensitive notes stored in logs; details remain in Custom Fields.

---

## 9) Search & Discoverability
- When active, **auto‑apply Tag** `un-scientific` (config) → Smart Search filterable.  
- Panel renders meta attributes for schema.org `CorrectionComment` (optional enhancement).

---

## 10) Internationalization (i18n)
Example keys:
```
PLG_CONTENT_UNSCIENTIFIC="Un Scientific Flag"
PLG_CONTENT_UNSCIENTIFIC_BADGE="Un Scientific"
PLG_CONTENT_UNSCIENTIFIC_PANEL="Contention & Clarifications"
PLG_CONTENT_UNSCIENTIFIC_SCOPE="Scope"
PLG_CONTENT_UNSCIENTIFIC_REASON="Reason"
PLG_CONTENT_UNSCIENTIFIC_REQUESTED="Requested Action"
PLG_CONTENT_UNSCIENTIFIC_RESOLUTION="Resolution"
PLG_CONTENT_UNSCIENTIFIC_BLOCK="Publishing blocked: outstanding Un Scientific flags."
```

---

## 11) File/Folder Scaffold
```
/plugins/content/unscientific/unscientific.php
/plugins/content/unscientific/unscientific.xml
/plugins/content/unscientific/services/provider.php
/plugins/content/unscientific/tmpl/panel.php
/plugins/content/unscientific/media/css/unscientific.css
/plugins/content/unscientific/media/js/unscientific.js
/plugins/content/unscientific/language/en-GB/en-GB.plg_content_unscientific.ini
/plugins/content/unscientific/language/en-GB/en-GB.plg_content_unscientific.sys.ini
```

---

## 12) Minimal Manifest (unscientific.xml)
```xml
<?xml version="1.0" encoding="utf-8"?>
<extension type="plugin" group="content" method="upgrade" version="5.0">
  <name>plg_content_unscientific</name>
  <author>AIEOU.org</author>
  <version>0.1.0</version>
  <description>Flags contested or accuracy-pending content with Un Scientific markers.</description>
  <files>
    <filename plugin="unscientific">unscientific.php</filename>
    <filename>services/provider.php</filename>
    <folder>tmpl</folder>
    <folder>media</folder>
  </files>
  <languages>
    <language tag="en-GB">language/en-GB/en-GB.plg_content_unscientific.ini</language>
    <language tag="en-GB">language/en-GB/en-GB.plg_content_unscientific.sys.ini</language>
  </languages>
  <config>
    <fields name="params">
      <fieldset name="basic">
        <field name="block_publish" type="radio" default="1" label="Block publish if unresolved" />
        <field name="editor_override" type="radio" default="0" label="Allow editorial override" />
        <field name="auto_tag" type="radio" default="1" label="Auto-apply 'un-scientific' tag" />
        <field name="default_display_level" type="list" default="summary" label="Default display level">
          <option value="full">Full</option>
          <option value="summary">Summary Only</option>
          <option value="hidden">Hidden to Public</option>
        </field>
      </fieldset>
    </fields>
  </config>
</extension>
```

---

## 13) Test Plan
**Unit/Integration**
- Saves with `unsci_active=Yes` and valid entry → OK; sets `unsci_complete` and timestamps.  
- Publish blocked when unresolved and `block_publish=1`.  
- Resolve flips state and clears tag if `auto_tag=1`.

**Functional**
- Reviewer sets a flag with scope+reason → badge/panel show; author sees requested actions.  
- Editor resolves with notes → publish allowed; Action Logs show events.  
- `Display Level` honored for public vs reviewer/editor.

**Regression**
- Rendering limited to Article views; no schema added; tag add/remove idempotent.

---

## 14) Rollout & Admin Checklist
1. Create Field Group “Un Scientific” & fields in §4.  
2. (Optional) Create Tag `un-scientific`.  
3. Enable plugin; set params (block publish, auto-tag).  
4. Update Workflows (Review → Publish) to rely on plugin check.  
5. Add short editorial SOP: when to flag, how to resolve, messaging templates.
