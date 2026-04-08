# Plugin 04 — Deadline Nudger (plg_system_deadline_nudger)
**Status:** Draft (Planning)  
**Target Stack:** Joomla 5.3 (LAMP) — Core‑first, strict MVC, **no custom DB tables**  
**Plugin Type:** `system` (uses Joomla Scheduler)  
**Goal:** Automate deadline reminders and escalations for submissions, reviews, and revisions using **native Articles, Custom Fields, Workflows, Mail Templates, and Scheduler**. All state lives in core; the plugin only reads fields, sends emails, and writes Action Logs.

---

## 1) Purpose
- Send **timely, templated reminders** for:  
  1) **Reviewer invitation response due**  
  2) **Review due**  
  3) **Author revision due**  
  4) Optional **editorial follow‑ups** (stalled decisions)  
- **Escalate** overdue items to editors after grace windows.
- Provide **dry‑run** mode (logs only) for safe testing.
- Zero schema changes; **no new tables**.

---

## 2) Core‑first Dependencies
- **com_content (Articles)** hold the submission record.  
- **Custom Fields** (Article) store due dates, assignees, and status markers.  
- **Workflows** define states (Draft → Review → Revisions → Accepted → Published).  
- **Users/Groups/ACL** identify Authors, Reviewers, Editors, EIC.  
- **Scheduler** (core) executes tasks; **Execution History** provides traceability.  
- **Mail Templates** produce branded, localized emails.  
- **Action Logs** record each notification or block.

---

## 3) Events & Hooks
- **Scheduler task** (primary): runs by CRON/webcron on the site, at configured intervals.  
- **onAfterInitialise**: register scheduler task via services provider (J5).  
- **onAfterRoute** (optional dev): expose a protected test endpoint for admins (toggle by plugin param).

---

## 4) Content Model (Custom Fields spec)
Create **Field Group: Deadlines** (Article context).

### A. Reviewer Invitation
- `rev_invite_assignments` (Repeatable Subform):  
  - `rev_user` (User) **required**  
  - `rev_invite_sent` (Calendar)  
  - `rev_invite_due` (Calendar) **required** (respond accept/decline)  
  - `rev_invite_status` (List: Pending, Accepted, Declined, Replaced)  
  - `rev_invite_escalated` (Checkbox auto)

### B. Review Due
- `rev_due_date` (Calendar) — per article overall **or** per reviewer if needed:  
  - If per reviewer is needed, add `rev_due_date` and `rev_due_escalated` inside **rev_invite_assignments**.

### C. Author Revision
- `auth_rev_due` (Calendar)  
- `auth_rev_escalated` (Checkbox auto)

### D. Editorial Follow‑up
- `ed_followup_due` (Calendar) — (e.g., **decision deadline** after last review)  
- `ed_followup_escalated` (Checkbox auto)

> Note: Where the journal needs per‑reviewer due dates, the plugin supports both **article‑level** dates and **per‑assignment** dates inside the repeatable field. Keep it simple at first; enable per‑assignment via a param.

---

## 5) Scheduler Task Logic
**Task ID:** `plg_system_deadline_nudger.checkDue`

1) **Collect candidates** via a filtered Article query (core model) + Smart Search index (optional) using:  
   - Category(ies) = journals/sections in scope (plugin param).  
   - Workflow states: *Under Review*, *Revisions*, *Awaiting Decision* (param).  
   - Presence of relevant **deadline fields**.  

2) **Evaluate deadlines** for each candidate:  
   - Compute **D‑X**, **D‑day**, **D+grace** windows (values from params).  
   - Skip if already escalated/acknowledged (checkbox flags).

3) **Dispatch emails** using **Mail Templates** and **per‑role recipients**:  
   - Reviewer: invite response reminder / review due reminders.  
   - Author: revision reminders.  
   - Editor: escalations after grace.  
   - Use language overrides and tokens (Article title, URL, due date, days late, reviewer name).

4) **Write Action Logs** for each message:  
   - `NUDGER_SENT: context={invite|review|revision|editor}, user={id}, article={id}, due=ISO8601, deltaDays=N`  
   - If dry‑run: `NUDGER_DRYRUN: ...`

5) **Mark escalation** flags on success (set `_escalated` checkboxes) to avoid duplicate escalations.

6) **Summary**: push a one‑line Scheduler history note with counts.

---

## 6) Email Templates (core Mail Templates)
Create these keys and templates in the admin (translatable, brandable):
- `mail_reviewer_invite_reminder` — “Please accept/decline your review invitation”  
- `mail_reviewer_due_reminder` — “Your review is due on {DATE}”  
- `mail_author_revision_reminder` — “Your revision is due on {DATE}”  
- `mail_editor_escalation` — “Escalation: {ARTICLE} is {N} days overdue for {CONTEXT}`

**Tokens available** (example):  
`{ARTICLE_TITLE}`, `{ARTICLE_LINK}`, `{DUE_DATE}`, `{DAYS_LATE}`, `{REVIEWER_NAME}`, `{AUTHOR_NAME}`, `{EDITOR_NAME}`

---

## 7) Params (admin)
- **Scope**: Category include/exclude; Workflow states include.  
- **Windows**: Days before due to remind (e.g., 7, 3, 1), grace after due (e.g., 3, 7).  
- **Per‑reviewer mode**: On/Off.  
- **Throttle**: max emails per run; min minutes between repeats to same user/article.  
- **Dry‑run**: On/Off (log only).  
- **Test endpoint**: On/Off + Access Level.  
- **Timezone**: force or inherit from site.  
- **Copy to**: CC/BCC addresses (journal inbox).

---

## 8) ACL
- Only **Editors/EIC/Admin** can configure or run test endpoint.  
- Emails respect **privacy**: recipients get only their relevant info (no PII leak).

---

## 9) UI/UX (no DB)
- **No admin component**; configuration is the plugin params UI.  
- Optional small **dashboard module** in a later plugin for KPIs (not in scope here).

---

## 10) Internationalization (i18n)
Example keys:
```
PLG_SYSTEM_DEADLINE_NUDGER="Deadline Nudger"
PLG_SYSTEM_DEADLINE_NUDGER_DRYRUN="Dry run: no emails sent."
PLG_SYSTEM_DEADLINE_NUDGER_SUMMARY="Nudger run: {count} notifications, {esc} escalations."
PLG_SYSTEM_DEADLINE_NUDGER_INVITE="Reviewer invite reminder"
PLG_SYSTEM_DEADLINE_NUDGER_REVIEW="Review due reminder"
PLG_SYSTEM_DEADLINE_NUDGER_REVISION="Author revision reminder"
PLG_SYSTEM_DEADLINE_NUDGER_ESCALATION="Editorial escalation"
```
Mail Templates are separate in the core Mail manager.

---

## 11) File/Folder Scaffold
```
/plugins/system/deadline_nudger/deadline_nudger.php
/plugins/system/deadline_nudger/deadline_nudger.xml
/plugins/system/deadline_nudger/services/provider.php
/plugins/system/deadline_nudger/language/en-GB/en-GB.plg_system_deadline_nudger.ini
/plugins/system/deadline_nudger/language/en-GB/en-GB.plg_system_deadline_nudger.sys.ini
```
- `provider.php` registers the **Scheduler task** and any event subscribers.

---

## 12) Minimal Manifest (deadline_nudger.xml)
```xml
<?xml version="1.0" encoding="utf-8"?>
<extension type="plugin" group="system" method="upgrade" version="5.0">
  <name>plg_system_deadline_nudger</name>
  <author>AIEOU.org</author>
  <version>0.1.0</version>
  <description>Scheduler-based reminders and escalations for review workflows.</description>
  <files>
    <filename plugin="deadline_nudger">deadline_nudger.php</filename>
    <filename>services/provider.php</filename>
  </files>
  <languages>
    <language tag="en-GB">language/en-GB/en-GB.plg_system_deadline_nudger.ini</language>
    <language tag="en-GB">language/en-GB/en-GB.plg_system_deadline_nudger.sys.ini</language>
  </languages>
  <config>
    <fields name="params">
      <fieldset name="basic">
        <field name="categories" type="category" multiple="true" extension="com_content" label="Categories in scope"/>
        <field name="states" type="text" default="under-review,revisions,awaiting-decision" label="Workflow states in scope"/>
        <field name="windows" type="text" default="7,3,1" label="Reminder days before due (CSV)"/>
        <field name="grace" type="number" default="3" label="Grace days after due for escalation"/>
        <field name="per_reviewer" type="radio" default="0" label="Per-reviewer due dates"/>
        <field name="throttle_max" type="number" default="100" label="Max emails per run"/>
        <field name="throttle_repeat_minutes" type="number" default="1440" label="Min minutes between repeats to same user/article"/>
        <field name="dry_run" type="radio" default="1" label="Dry run (log only)"/>
        <field name="test_endpoint" type="radio" default="0" label="Enable admin test endpoint"/>
        <field name="timezone" type="text" label="Timezone (leave blank to use site)"/>
        <field name="cc" type="text" label="CC addresses (CSV)"/>
        <field name="bcc" type="text" label="BCC addresses (CSV)"/>
      </fieldset>
    </fields>
  </config>
</extension>
```

---

## 13) Test Plan
**Unit/Integration**  
- Task finds due items and honors `dry_run`.  
- Throttle prevents repeats; escalation flags set once.  
- Per‑reviewer mode correctly targets the right users.

**Functional**  
- Reviewer receives invite and due reminders at D‑7/3/1; grace triggers editor escalation.  
- Author gets revision reminders; overdue triggers escalation.  
- Scheduler history shows counts; Action Logs reflect sends.

**Regression**  
- No emails to users without access to the article.  
- No double‑escalations; tags/flags idempotent; no schema changes.

---

## 14) Rollout & Admin Checklist
1. Create **Deadlines** Field Group & fields (§4).  
2. Configure plugin params (categories, windows, grace, throttle).  
3. Create **Mail Templates** (§6).  
4. Enable the plugin; enable Scheduler CRON.  
5. Run in **Dry‑run** for 1–2 cycles; check logs; then turn on sending.
