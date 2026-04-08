# Plugin 02 — AI Usage Log (plg_content_aiusage)
**Status:** Draft (Planning)  
**Target Stack:** Joomla 5.3 (LAMP) — Core-first, strict MVC, no custom DB tables  
**Plugin Type:** `content`  
**Goal:** Capture, validate, and render a first‑class **AI Usage Log** for Articles using native Custom Fields, providing auditability and clear disclosure. No external storage: all data lives in Article Custom Fields + Action Logs.

---

## 1) Purpose
- Provide a structured, auditable record when **AI assisted** the research or drafting process.  
- Enforce minimal disclosure before publish; render an **AI Relationship Statement** on the article.  
- Support privacy by design (hash prompts, redact sensitive text, configurable display).

---

## 2) Core‑first Dependencies
- **com_content (Articles)** as the single content store.  
- **Custom Fields** (Article context) for AI metadata.  
- **Workflows** for state transitions (enforcement).  
- **Action Logs** for provenance.  
- **Email Templates** (optional) for missing‑info nudges.

---

## 3) Events & Hooks (Joomla 5 typed)
- Render:
  - `onContentAfterTitle` → compact “AI‑Logged” badge + summary chips.  
  - `onContentAfterDisplay` → full AI Usage panel.
- Validate / Enforce:
  - `onContentPrepareForm` → inject field hints / help text.  
  - `onContentBeforeSave` → validate user input; derive hashes.  
  - `onContentAfterSave` → write Action Log summary.  
  - `onContentBeforeChangeState` → block publish if required AI fields missing when `ai_used=1`.
- Normalization:
  - `onContentNormaliseRequestData` → normalize URLs, map model names, trim lists.

> Use typed event classes (`\Joomla\CMS\Event\Model\BeforeSaveEvent`, etc.) where applicable in J5.

---

## 4) Content Model (Custom Fields spec)
Create **Field Group: AI Usage** (Article context).

### A. Usage Switch
- `ai_used` (Radio: No/Yes) — **drives validation**.

### B. Tooling (Repeatable: each AI tool/model used)
- `ai_tools` (Repeatable Subform):
  - `ai_vendor` (Text/List — e.g., OpenAI, Anthropic, Google, Local) **required**
  - `ai_model` (Text — e.g., GPT‑4.1, Claude‑3.5) **required**
  - `ai_version` (Text, optional)
  - `ai_mode` (List: Chat, API, Batch, Image, Audio, Code, Other)
  - `ai_endpoint` (URL/Text — optional, for API endpoint or app URL)
  - `ai_params` (Textarea — temperature, top_p, system prompt notes)

### C. Prompts & Outputs (Repeatable, privacy‑aware)
- `ai_interactions` (Repeatable Subform):
  - `ai_prompt_summary` (Textarea — high‑level description, **no raw prompt**) **required**
  - `ai_prompt_hash` (Text — **SHA‑256** of prompt text kept locally by author, not stored in raw form) **required if author used raw**  
  - `ai_output_type` (List: Text, Outline, Code, Table, Figure, Data, Other) **required**
  - `ai_contribution_scope` (List: Ideation, Drafting, Editing, Translation, Data Processing, Analysis, Visualization, Coding, Other) **required**
  - `ai_human_oversight` (Textarea — how the author verified/edited the output) **required**
  - `ai_external_data_used` (Radio: No/Yes) — if Yes, requires `ai_data_sources`.
  - `ai_data_sources` (Textarea — brief description/links to non‑article data passed to AI) *conditional*
  - `ai_risk_flags` (Checkboxes: Hallucination Risk, Sensitive Data Risk, Copyright Risk, Bias Risk, Other)
  - `ai_redactions` (Textarea — what was redacted and why)

### D. Statement & Controls
- `ai_relationship_statement` (Textarea — one‑paragraph disclosure) **required if ai_used=Yes**
- `ai_display_level` (List: Full, Summary Only, Hidden to Public) — **render controls** (admins/reviewers always see full).

### E. Integrity Fields (auto‑managed)
- `ai_log_complete` (Checkbox — set by plugin if all required fields are valid)
- `ai_log_lastcheck` (Calendar — auto‑updated on validation)

---

## 5) Validation Rules
When `ai_used=Yes`:
- At least one **Tool** and one **Interaction** entry.  
- `ai_prompt_summary`, `ai_output_type`, `ai_contribution_scope`, `ai_human_oversight` **required** per interaction.  
- If `ai_external_data_used=Yes` → `ai_data_sources` required.  
- `ai_relationship_statement` required.  
- Compute **SHA‑256** for `ai_prompt_hash` if author provides raw prompt (hash locally in plugin; do **not** store raw).  
- On pass: set `ai_log_complete=1` and update `ai_log_lastcheck`.  
- On fail: raise message and block **publish** transition.

When `ai_used=No`: no enforcement; rendering suppressed.

---

## 6) Rendering (Front‑end)
- **Badge (after title):** `AI‑Logged` chip with hover popover: model(s), interactions count, last checked date.  
- **Full Panel (after content):**
  - Tooling summary table (Vendor, Model, Mode).  
  - Interactions list (Prompt Summary, Output Type, Contribution Scope, Oversight, Data Sources, Risk Flags).  
  - AI Relationship Statement (blockquote).  
  - Respect `ai_display_level`:  
    - **Full:** render all.  
    - **Summary Only:** render tools + interaction counts + statement (no details).  
    - **Hidden to Public:** show badge to public; full panel only for Reviewer/Editorial ACL.

Use **WebAsset API** for minimal CSS/JS (accordion/popover).

---

## 7) ACL & Workflows
- Authors can set/edit fields; **Editors** can enforce and override (configurable).  
- Workflows check on transitions: `Draft → Under Review`, `Under Review → Published`.  
- Admins/Reviewers always see full details regardless of `ai_display_level`.

---

## 8) Action Logs
- On publish or validation pass, log:  
  `AI_LOG_OK: tools={n}, interactions={m}, lastcheck=ISO8601, display={level}`  
- On failure: `AI_LOG_FAIL` with reasons (no raw content).

---

## 9) Privacy & Security
- **No raw prompts** stored by default; only a **hash** and **summary**.  
- Redaction support via `ai_redactions`.  
- Option in plugin params: “Allow raw prompt capture (admin‑only)” (default **off**).  
- Clearly label any field that becomes public; all else defaults to internal if `Hidden to Public`.

---

## 10) Internationalization (i18n)
Example keys:
```
PLG_CONTENT_AIUSAGE="AI Usage Log"
PLG_CONTENT_AIUSAGE_BADGE="AI-Logged"
PLG_CONTENT_AIUSAGE_PANEL="AI Relationship & Usage"
PLG_CONTENT_AIUSAGE_TOOLS="AI Tools"
PLG_CONTENT_AIUSAGE_INTERACTIONS="AI Interactions"
PLG_CONTENT_AIUSAGE_OVERSIGHT="Human Oversight"
PLG_CONTENT_AIUSAGE_PROMPT_SUMMARY="Prompt Summary"
PLG_CONTENT_AIUSAGE_RISK_FLAGS="Risk Flags"
PLG_CONTENT_AIUSAGE_MISSING="AI usage details are incomplete."
```

---

## 11) File/Folder Scaffold
```
/plugins/content/aiusage/aiusage.php
/plugins/content/aiusage/aiusage.xml
/plugins/content/aiusage/services/provider.php
/plugins/content/aiusage/tmpl/panel.php
/plugins/content/aiusage/media/css/aiusage.css
/plugins/content/aiusage/media/js/aiusage.js
/plugins/content/aiusage/language/en-GB/en-GB.plg_content_aiusage.ini
/plugins/content/aiusage/language/en-GB/en-GB.plg_content_aiusage.sys.ini
```
- `provider.php` registers services & listeners (J5).  
- `tmpl/panel.php` renders the full panel from Custom Fields.

---

## 12) Minimal Manifest (aiusage.xml)
```xml
<?xml version="1.0" encoding="utf-8"?>
<extension type="plugin" group="content" method="upgrade" version="5.0">
  <name>plg_content_aiusage</name>
  <author>AIEOU.org</author>
  <version>0.1.0</version>
  <description>Captures, validates, and renders AI usage disclosure for Articles.</description>
  <files>
    <filename plugin="aiusage">aiusage.php</filename>
    <filename>services/provider.php</filename>
    <folder>tmpl</folder>
    <folder>media</folder>
  </files>
  <languages>
    <language tag="en-GB">language/en-GB/en-GB.plg_content_aiusage.ini</language>
    <language tag="en-GB">language/en-GB/en-GB.plg_content_aiusage.sys.ini</language>
  </languages>
  <config>
    <fields name="params">
      <fieldset name="basic">
        <field name="show_badge" type="radio" default="1" label="Show Badge" />
        <field name="enforce_publish" type="radio" default="1" label="Enforce before publish" />
        <field name="editor_override" type="radio" default="0" label="Allow editorial override" />
        <field name="allow_raw_prompts" type="radio" default="0" label="Allow raw prompt capture (admin-only)" />
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
- `onContentBeforeSave` rejects when `ai_used=Yes` and required fields missing.  
- Accepts when complete; sets `ai_log_complete` and `ai_log_lastcheck`.  
- Ensures hash is computed when author provided a raw prompt string (if allowed).

**Functional**  
- Author toggles `ai_used=Yes`, fills minimal fields → publish passes.  
- `Display Level` honored for public vs Reviewer/Editorial views.  
- Action Log entries appear with correct summary.

**Regression**  
- Panel appears only on Article views; badge toggles with param; no DB schema created.

---

## 14) Rollout & Admin Checklist
1. Create Field Group “AI Usage” & fields in §4.  
2. Enable plugin; set params (display level, enforcement).  
3. Add workflow guard on transitions (Draft → Review, Review → Published).  
4. Add a short **Author Guideline** block on disclosure practices.  
5. (Optional) Create an Email Template for missing info reminders.
