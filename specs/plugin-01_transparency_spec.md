# Plugin 01 — Transparency Block (plg_content_transparency)
**Status:** Draft (Planning)  
**Target Stack:** Joomla 5.3 (LAMP) — Core-first, strict MVC, no custom DB tables  
**Plugin Type:** `content`  
**Goal:** Render and validate structured Source/Data/Method transparency on Articles using native Custom Fields + Workflows.

---

## 1) Purpose
- Enforce and render a **Transparency Block** on Article pages:
  - **Sources consulted** (used and excluded) with reasons.
  - **Datasets & code** (location, license, accessibility).
  - **Method & limitations** notes.
- Provide **pre-publish validation** to prevent workflow transition unless required transparency fields are complete.
- Zero new schema: use **Custom Fields** assigned to Articles + native Action Logs.

---

## 2) Core-first Dependencies
- **com_content (Articles)** for submissions.
- **Custom Fields** (repeatable groups).
- **Workflows** for state transitions.
- **Action Logs** for provenance.
- **Email Templates** (optional) to notify authors of missing fields.

---

## 3) Events & Hooks (Joomla 5 typed events)
- View/render injection:
  - `onContentAfterTitle` → add compact transparency badge/summary.
  - `onContentAfterDisplay` → render full Transparency Block.
- Validation/Enforcement:
  - `onContentPrepareForm` → inject field hints + client-side help.
  - `onContentBeforeSave` → server-side validation on save.
  - `onContentBeforeChangeState` → block state change if required fields missing.
- Data normalization:
  - `onContentNormaliseRequestData` → trim lists, normalize URLs/DOIs.

> **Note:** Use the new event classes (e.g., `\Joomla\CMS\Event\Model\BeforeSaveEvent`) where applicable.

---

## 4) Content Model (Custom Fields spec)
Create a **Field Group: Transparency** (Article context).

### A. Sources (Repeatable)
- `transp_sources` (Repeatable Subform):
  - `src_title` (Text, required)
  - `src_type` (List: Primary, Secondary, Tertiary)
  - `src_pid` (Text, DOI/Handle/URL)
  - `src_used` (Radio: Used / Excluded)
  - `src_reason` (Textarea — required if Excluded)
  - `src_notes` (Textarea, optional)

### B. Datasets (Repeatable)
- `transp_datasets` (Repeatable Subform):
  - `data_title` (Text, required)
  - `data_link` (URL)
  - `data_type` (List: Raw, Processed, Code, Images, Other)
  - `data_license` (Text/List — SPDX optional)
  - `data_availability` (List: Open, Restricted, Upon Request)
  - `data_anonymization` (Checkbox + Textarea notes)

### C. Methods & Limitations
- `transp_methods` (Textarea, required)
- `transp_limitations` (Textarea, required)

### D. Integrity Flags
- `transp_complete` (Checkbox — auto-set by plugin when valid)
- `transp_lastcheck` (Calendar — auto-updated on validation)

---

## 5) Validation Rules
- At least **one Source** entry.
- All **Excluded** sources must include `src_reason`.
- If **Datasets** present and `data_availability=Restricted/Upon Request` → require a short justification in notes.
- `transp_methods` and `transp_limitations` **required** before publishing (state change to Published).
- On pass: set `transp_complete=1`, update `transp_lastcheck`.
- On fail: raise message; block save or state transition (depending on context).

---

## 6) Rendering (Front-end)
- **Badge line (after title):** small icons + counts: Sources Used/Excluded, Datasets, Last Checked date, completeness.
- **Full block (after content):**
  - Collapsible panels: **Sources**, **Datasets**, **Methods & Limitations**.
  - Each source shows title → link (DOI/URL), type, status (Used/Excluded) + reason if excluded.
  - Respect article view access and ACL.

Use **WebAsset API** to enqueue minimal JS (accordion) and CSS.

---

## 7) ACL & Workflows
- Only **Editors+** can override validation failures (via a toggle in plugin params: “Allow editorial override”).  
- Authors can save drafts with missing transparency; **publish** requires completeness.
- Integrates with **Workflows**: check on transitions `Draft → Under Review`, `Under Review → Published`.

---

## 8) Action Logs
- On successful validation/publish, log a summary line:
  - `TRANSPARENCY_OK: sources={used:X, excluded:Y}, datasets=Z, lastcheck=ISO8601`
- On block, log `TRANSPARENCY_FAIL` with reasons (not field contents).

---

## 9) Email Templates (optional)
- `tpl_transparency_missing`: sent to Author when editor attempts to move forward but fields missing.

---

## 10) Internationalization (i18n)
Language keys (example):
```
PLG_CONTENT_TRANSPARENCY="Transparency Block"
PLG_CONTENT_TRANSPARENCY_BADGE="Transparency"
PLG_CONTENT_TRANSPARENCY_SOURCES="Sources"
PLG_CONTENT_TRANSPARENCY_EXCLUDED="Excluded"
PLG_CONTENT_TRANSPARENCY_USED="Used"
PLG_CONTENT_TRANSPARENCY_DATASETS="Datasets & Code"
PLG_CONTENT_TRANSPARENCY_METHODS="Methods"
PLG_CONTENT_TRANSPARENCY_LIMITATIONS="Limitations"
PLG_CONTENT_TRANSPARENCY_INCOMPLETE="Transparency requirements are incomplete."
```
Provide `en-GB.plg_content_transparency.ini` and `.sys.ini`.

---

## 11) File/Folder Scaffold
```
/plugins/content/transparency/transparency.php
/plugins/content/transparency/transparency.xml
/plugins/content/transparency/services/provider.php
/plugins/content/transparency/language/en-GB/en-GB.plg_content_transparency.ini
/plugins/content/transparency/language/en-GB/en-GB.plg_content_transparency.sys.ini
/plugins/content/transparency/tmpl/block.php
/plugins/content/transparency/media/css/transparency.css
/plugins/content/transparency/media/js/transparency.js
```
- `provider.php` registers services & event listeners (J5 style).
- `tmpl/block.php` renders the full block using Article’s Custom Fields.

---

## 12) Minimal Manifest (transparency.xml)
```xml
<?xml version="1.0" encoding="utf-8"?>
<extension type="plugin" group="content" method="upgrade" version="5.0">
  <name>plg_content_transparency</name>
  <author>AIEOU.org</author>
  <version>0.1.0</version>
  <description>Renders and validates transparency metadata for Articles.</description>
  <files>
    <filename plugin="transparency">transparency.php</filename>
    <filename>services/provider.php</filename>
    <folder>tmpl</folder>
    <folder>media</folder>
  </files>
  <languages>
    <language tag="en-GB">language/en-GB/en-GB.plg_content_transparency.ini</language>
    <language tag="en-GB">language/en-GB/en-GB.plg_content_transparency.sys.ini</language>
  </languages>
  <config>
    <fields name="params">
      <fieldset name="basic">
        <field name="show_badge" type="radio" default="1" label="Show Badge" description="Show compact badge after title."/>
        <field name="editor_override" type="radio" default="0" label="Allow Editorial Override" description="Permit Editors to publish even if incomplete."/>
      </fieldset>
    </fields>
  </config>
</extension>
```

---

## 13) Test Plan
**Unit/Integration**
- Mock events: `onContentBeforeSave` rejects when required fields missing.
- Accepts when required fields filled; sets `transp_complete` and `transp_lastcheck`.

**Functional**
- Author saves draft missing fields (allowed).
- Editor attempts to publish → blocked; email sent (optional).
- After completing fields, publish succeeds; Action Log populated.
- Frontend renders badge + block; toggles behave.

**Regression**
- Ensure rendering only on Article views (not categories/feeds unless enabled).
- Confirm compatibility with template overrides.

---

## 14) Rollout & Admin Checklist
1. Create Field Group “Transparency” and fields from §4.
2. Enable plugin; set params.
3. Update Workflows to include validation on transitions.
4. Add language overrides for front-end labels if needed.
5. Add menu item note: authors must complete Transparency before publish.
