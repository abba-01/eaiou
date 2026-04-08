# Plugin 06 — Open Reports (Transparent Peer Review Renderer) — `plg_content_openreports`
**Status:** Draft (Planning)  
**Target Stack:** Joomla 5.3 (LAMP) — Core‑first, strict MVC, **no custom DB tables**  
**Plugin Type:** `content`  
**Goal:** Publish **peer‑review reports** and author responses alongside the article using only **Articles, Custom Fields, Workflows, Tags, Action Logs, and Mail Templates**. Supports open/transparent, single-/double‑blind, and “summary only” modes with privacy‑safe redaction.

---

## 1) Purpose
- Enable **transparent peer review** by rendering reviewer reports and author responses on the public article view (when configured).  
- Respect journal policies: **open identities**, **open reports**, or **summary only**.  
- Enforce reviewer/author consent flow and **privacy‑first redactions**.  
- All data lives in **Article Custom Fields**; no new schema.

---

## 2) Core‑first Dependencies
- **com_content (Articles)** as the canonical record.  
- **Custom Fields** (Article context) for review entries and author responses.  
- **Workflows** to guard publication of reports with consent checks.  
- **Tags** (optional) to indicate `open-reports` capability per journal/section.  
- **Action Logs** for provenance (publish, retract, redact).  
- **Mail Templates** (optional) for consent requests and notifications.

---

## 3) Events & Hooks (Joomla 5 typed)
- Render:
  - `onContentAfterDisplay` → render the **Open Reports Panel** below the article body.
- Validate / Enforce:
  - `onContentPrepareForm` → inject field hints and surface policy notes.  
  - `onContentBeforeSave` → validate reviewer consent flags and redaction settings.  
  - `onContentBeforeChangeState` → block publish of reports if required consents are missing (configurable).  
- Normalization:
  - `onContentNormaliseRequestData` → sanitize/strip email addresses/PII from display fields (configurable).

---

## 4) Content Model (Custom Fields spec)
Create **Field Group: Peer Review (Open Reports)** (Article context).

### A. Policy Switches (per article)
- `or_enabled` (Radio: No/Yes) — enables output.  
- `or_mode` (List: **Open Identities**, **Open Reports (anonymized)**, **Summary Only**) — controls visibility.  
- `or_publish_on` (Radio: On Accept / On Publish / Manual) — when reports become public.  
- `or_redact_emails` (Radio: Yes/No, default Yes) — automatic redaction.

### B. Reviewer Reports (Repeatable)
- `or_reviews` (Repeatable Subform):  
  - `or_rev_id` (Hidden; auto GUID)  
  - `or_rev_user` (User — internal reference only; **never displayed** when anonymized)  
  - `or_rev_displayname` (Text — shown when **Open Identities**)  
  - `or_rev_consent_display` (Radio: No/Yes) — required if identities open  
  - `or_rev_recommendation` (List: Accept, Minor Rev, Major Rev, Reject, Other)  
  - `or_rev_scores` (Repeatable Subform — label/value pairs)  
  - `or_rev_text` (Editor — the review body)  
  - `or_rev_attachments` (Media/URLs — optional)  
  - `or_rev_date` (Calendar — completion date)  
  - `or_rev_redactions` (Textarea — editor‑entered summary of redactions)  
  - `or_rev_publish` (Radio: No/Yes) — per‑review publish toggle

### C. Author Response (Repeatable)
- `or_author_responses` (Repeatable Subform):  
  - `or_ar_to_review` (Select — bind to `or_rev_id`)  
  - `or_ar_text` (Editor)  
  - `or_ar_date` (Calendar)

### D. Integrity
- `or_lastcheck` (Calendar — updated on validation)  
- `or_complete` (Checkbox — auto set when valid)

---

## 5) Validation Rules
- If `or_enabled=Yes`:  
  - Require `or_mode`.  
  - For **Open Identities**: each review with `or_rev_publish=Yes` must have `or_rev_consent_display=Yes` and a `or_rev_displayname`.  
  - For **Open Reports (anonymized)**: `or_rev_user` remains internal; plugin redacts PII/email from `or_rev_text` if `or_redact_emails=Yes`.  
  - **Summary Only**: allow publishing only `or_rev_recommendation`, `scores`, and dates; hide body text.  
- On pass: set `or_complete=1`, update `or_lastcheck`.  
- On fail: block **report publish** (and optionally **article publish** if policy requires).

---

## 6) Rendering (Front‑end)
**Open Reports Panel** (below article content):
- **Header**: “Peer‑Review Reports” + mode badge (Open Identities / Anonymized / Summary Only).  
- **Per Review**:  
  - Reviewer name (mode dependent) + date + recommendation + scores.  
  - **Body** (if mode allows): review text with inline redaction markers.  
  - Attachments (links), Redaction note (if present).  
- **Author Responses**: threaded under each review (sorted by `or_ar_date`).  
- **Schema.org enhancements** (optional): annotate with `Review`, `rating`, `author` (if open), `CreativeWork`.  
- Respect view levels: reviewers/editors always see full internal metadata in admin; public sees per `or_mode`.

Use **WebAsset API** to add minimal CSS (panels, badges) and JS (accordion/tabs).

---

## 7) ACL & Workflows
- **Who can edit reports**: Reviewers (own review), Editors, Admin (configurable).  
- **Consent flow**: Editors toggle `or_rev_publish` only after consent recorded; plugin enforces.  
- **Publication timing**:  
  - **On Accept**: expose reports when workflow reaches Accept.  
  - **On Publish**: expose on article publish.  
  - **Manual**: expose when editor flips a dedicated “Publish Reports” field (could be a Tag or boolean).

---

## 8) Action Logs
- On publish of a review: `OPENREPORT_PUBLISH: review={id}, mode={or_mode}`  
- On retract: `OPENREPORT_RETRACT: review={id}`  
- On redaction changes: `OPENREPORT_REDACTED: review={id}`

No raw PII in logs; IDs only.

---

## 9) Mail Templates (optional)
- `mail_or_request_consent` — asks reviewer to approve identity disclosure.  
- `mail_or_published_notice` — informs stakeholders that reports are now public.

Tokens: `{ARTICLE_TITLE}`, `{ARTICLE_LINK}`, `{REVIEWER_DISPLAY}`, `{MODE}`, `{DATE}`

---

## 10) Internationalization (i18n)
Example keys:
```
PLG_CONTENT_OPENREPORTS="Open Reports"
PLG_CONTENT_OPENREPORTS_PANEL="Peer-Review Reports"
PLG_CONTENT_OPENREPORTS_MODE_OPEN="Open Identities"
PLG_CONTENT_OPENREPORTS_MODE_ANON="Open Reports (anonymized)"
PLG_CONTENT_OPENREPORTS_MODE_SUMMARY="Summary Only"
PLG_CONTENT_OPENREPORTS_REVIEW="Review"
PLG_CONTENT_OPENREPORTS_RESPONSE="Author Response"
PLG_CONTENT_OPENREPORTS_REDACTED="[redacted]"
PLG_CONTENT_OPENREPORTS_CONSENT_REQUIRED="Reviewer consent required for identity disclosure."
```

---

## 11) File/Folder Scaffold
```
/plugins/content/openreports/openreports.php
/plugins/content/openreports/openreports.xml
/plugins/content/openreports/services/provider.php
/plugins/content/openreports/tmpl/panel.php
/plugins/content/openreports/media/css/openreports.css
/plugins/content/openreports/media/js/openreports.js
/plugins/content/openreports/language/en-GB/en-GB.plg_content_openreports.ini
/plugins/content/openreports/language/en-GB/en-GB.plg_content_openreports.sys.ini
```

---

## 12) Minimal Manifest (openreports.xml)
```xml
<?xml version="1.0" encoding="utf-8"?>
<extension type="plugin" group="content" method="upgrade" version="5.0">
  <name>plg_content_openreports</name>
  <author>AIEOU.org</author>
  <version>0.1.0</version>
  <description>Publishes peer-review reports and author responses with flexible transparency modes.</description>
  <files>
    <filename plugin="openreports">openreports.php</filename>
    <filename>services/provider.php</filename>
    <folder>tmpl</folder>
    <folder>media</folder>
  </files>
  <languages>
    <language tag="en-GB">language/en-GB/en-GB.plg_content_openreports.ini</language>
    <language tag="en-GB">language/en-GB/en-GB.plg_content_openreports.sys.ini</language>
  </languages>
  <config>
    <fields name="params">
      <fieldset name="basic">
        <field name="default_mode" type="list" default="anon" label="Default mode">
          <option value="open">Open Identities</option>
          <option value="anon">Open Reports (anonymized)</option>
          <option value="summary">Summary Only</option>
        </field>
        <field name="publish_on" type="list" default="on_publish" label="Publish reports">
          <option value="on_accept">On Accept</option>
          <option value="on_publish">On Article Publish</option>
          <option value="manual">Manual</option>
        </field>
        <field name="redact_emails" type="radio" default="1" label="Auto-redact emails"/>
        <field name="block_without_consent" type="radio" default="1" label="Block identity disclosure without consent"/>
      </fieldset>
    </fields>
  </config>
</extension>
```

---

## 13) Test Plan
**Unit/Integration**  
- Blocks identity display when consent missing; allows anonymized report publication.  
- Redaction removes email patterns in display when enabled.  
- Honors timing (accept vs publish vs manual).

**Functional**  
- Open Identities → names and bodies visible as expected; anonymized mode hides names but shows text.  
- Summary Only → shows recommendations/scores but not review text.  
- Author responses threaded under the correct review.

**Regression**  
- Works with template overrides; no schema changes; rendering limited to article views.  
- Non‑ASCII names handled correctly; no PII in Action Logs.

---

## 14) Rollout & Admin Checklist
1. Create **Peer Review (Open Reports)** Field Group & fields (§4).  
2. Enable plugin; set default mode and timing.  
3. Update editorial SOP for consent capture and redaction policy.  
4. Test with a sample article: one open identity, one anonymized review; publish and verify rendering.
