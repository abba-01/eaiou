# Module 05 — Reviewer Queue (mod_reviewer_queue)
**Status:** Draft (Planning)  
**Target Stack:** Joomla 5.3 (LAMP) — Core-first, strict MVC, **no custom DB tables**  
**Extension Type:** `module` (site/admin positions)  
**Goal:** Provide reviewers a focused, ACL‑aware queue of their assigned manuscripts with due dates, statuses, and quick actions—purely from **core Articles, Custom Fields, Workflows**. No new schema.

---

## 1) Purpose
- Display each logged‑in **Reviewer’s** assigned manuscripts with: title, category (journal/section), current workflow state, **invite status**, **review due date**, days remaining/late, and quick links.  
- Support **per‑reviewer** assignments stored in Article Custom Fields (repeatable) as defined in Plugin 04 (Deadline Nudger).  
- Respect ACL: only show items the user is assigned to or allowed to review.  
- Zero business logic outside core; the module is a **reader/formatter** + small helper actions.

---

## 2) Core‑first Dependencies
- **com_content (Articles)** as the single source of truth.  
- **Custom Fields** (Article) for reviewer assignments and due dates:  
  - Field Group **Deadlines** repeatable `rev_invite_assignments` with:  
    - `rev_user` (User), `rev_invite_status` (Pending/Accepted/Declined/Replaced), `rev_due_date` (Calendar), `rev_invite_sent`, etc.  
- **Workflows** for state names and transitions (display only here).  
- **Users/Groups/ACL** to recognize Reviewer role.  
- **Smart Search** (optional) for faster filtered queries.

---

## 3) Data Model Assumptions
Each Article may contain zero or more **reviewer assignment entries**. A row is *in the reviewer’s queue* if:
- `rev_user` equals the logged‑in user **and**
- `rev_invite_status` is **Pending** or **Accepted** **and**
- Article workflow state is **Under Review** (configurable).

Overdue is computed as `today > rev_due_date` (with optional grace window purely for color coding; not enforcement).

---

## 4) UI / Rendering
- **Card/List view** (toggle via module params).  
- Columns (list) or sections (cards):  
  - **Title** (linked to article view or reviewer form)  
  - **Category** (journal/section)  
  - **State** (workflow state name)  
  - **Invite Status** (Pending/Accepted/Declined)  
  - **Due Date** (ISO) + **D‑remaining** (e.g., 5d, due today, 3d late)  
  - **Badges** (if present): `AI-Logged`, `Un Scientific`, `Un Research`  
  - **Quick Actions**: Accept/Decline invite (if Pending), Open review form, Contact editor (mailto with context)
- Color rules:  
  - Due >7d: neutral; 7–1d: warning; 0d: alert; <0d: overdue (danger).

Frontend assets via **WebAsset API**; CSS minimal and template‑friendly.

---

## 5) Quick Actions (lightweight)
- **Accept/Decline Invite**: optional action links calling a protected endpoint handled by a tiny helper in the module **or** (preferable) by a micro **system plugin** that listens to a signed token.  
  - On Accept → set `rev_invite_status=Accepted` for that row; write Action Log `REVIEW_INVITE_ACCEPTED`.  
  - On Decline → set `rev_invite_status=Declined`; Action Log `REVIEW_INVITE_DECLINED`.  
- **Open Review Form**: link to Article edit or reviewer‑specific form (editorial SOP).  
- **Contact Editor**: `mailto:` with subject templated; no PII leaks.

> If avoiding writes from the module, we can disable inline Accept/Decline and route users to a **dedicated menu item** that runs via `plg_system_deadline_nudger` or a tiny accept/decline plugin. Keep module read‑only if desired (param).

---

## 6) Module Parameters
- **Mode**: List / Card.  
- **Scope categories** (multi‑select): limit to specific journals/sections.  
- **Workflow states in scope**: default `under-review`.  
- **Show badges**: AI‑Logged / Un Scientific / Un Research.  
- **Overdue windows**: warning days (default 7), danger threshold (default 0).  
- **Show quick actions**: Accept/Decline / Open Review / Contact Editor (checkboxes).  
- **Read‑only**: if enabled, disables Accept/Decline inline actions.  
- **Link target**: Article view / Review form menu item / External URL.  
- **Max items**: default 20.  
- **Cache**: Joomla module cache enable/disable; cache TTL.

---

## 7) ACL
- **Access**: only users in Reviewer (or higher) groups.  
- Per‑item visibility requires the assignment to the logged‑in user; else the item is not shown.  
- Quick actions require ownership; otherwise hidden.

---

## 8) Badges Integration (read‑only)
- **AI‑Logged**: checks `ai_used=Yes` (from Plugin 02 fields).  
- **Un Scientific**: checks `unsci_active=Yes` (from Plugin 03 fields).  
- **Un Research**: a Tag `un-research` or boolean field.  
- Badges are purely visual indicators; no extra queries besides the article’s fields/tags.

---

## 9) Performance
- Query only **current user’s assignments** via a join on fields (efficient when Smart Search index or com_content model filters are used).  
- Module caching can be enabled; cache key includes user id to avoid data leaks.

---

## 10) Action Logs
- If quick actions enabled: log `REVIEW_INVITE_ACCEPTED` / `REVIEW_INVITE_DECLINED`.  
- Otherwise read‑only; no logs written.

---

## 11) Internationalization (i18n)
Example keys:
```
MOD_REVIEWER_QUEUE="Reviewer Queue"
MOD_REVIEWER_QUEUE_TITLE="Assigned Manuscripts"
MOD_REVIEWER_QUEUE_STATE="State"
MOD_REVIEWER_QUEUE_DUE="Due"
MOD_REVIEWER_QUEUE_STATUS="Invite Status"
MOD_REVIEWER_QUEUE_ACCEPT="Accept"
MOD_REVIEWER_QUEUE_DECLINE="Decline"
MOD_REVIEWER_QUEUE_OPEN_REVIEW="Open Review"
MOD_REVIEWER_QUEUE_CONTACT_EDITOR="Contact Editor"
MOD_REVIEWER_QUEUE_OVERDUE="Overdue"
MOD_REVIEWER_QUEUE_DUE_TODAY="Due Today"
MOD_REVIEWER_QUEUE_DAYS_LEFT="%s days left"
```

---

## 12) File/Folder Scaffold
```
/modules/mod_reviewer_queue/mod_reviewer_queue.php
/modules/mod_reviewer_queue/mod_reviewer_queue.xml
/modules/mod_reviewer_queue/helper.php
/modules/mod_reviewer_queue/tmpl/default.php
/modules/mod_reviewer_queue/tmpl/cards.php
/modules/mod_reviewer_queue/media/css/reviewer_queue.css
/modules/mod_reviewer_queue/media/js/reviewer_queue.js
/modules/mod_reviewer_queue/language/en-GB/en-GB.mod_reviewer_queue.ini
/modules/mod_reviewer_queue/language/en-GB/en-GB.mod_reviewer_queue.sys.ini
```

- `helper.php` queries Articles + fields for the current user, computes status and labels.  
- Templates choose list or cards based on param.  
- Optional action endpoint implemented by a signed link validated either by module helper or a small system plugin.

---

## 13) Minimal Manifest (mod_reviewer_queue.xml)
```xml
<?xml version="1.0" encoding="utf-8"?>
<extension type="module" client="site" method="upgrade" version="5.0">
  <name>mod_reviewer_queue</name>
  <author>AIEOU.org</author>
  <version>0.1.0</version>
  <description>Displays assigned manuscripts and due dates for reviewers.</description>
  <files>
    <filename module="mod_reviewer_queue">mod_reviewer_queue.php</filename>
    <filename>helper.php</filename>
    <folder>tmpl</folder>
    <folder>media</folder>
  </files>
  <languages>
    <language tag="en-GB">language/en-GB/en-GB.mod_reviewer_queue.ini</language>
    <language tag="en-GB">language/en-GB/en-GB.mod_reviewer_queue.sys.ini</language>
  </languages>
  <config>
    <fields name="params">
      <fieldset name="basic">
        <field name="mode" type="list" default="list" label="Display Mode">
          <option value="list">List</option>
          <option value="cards">Cards</option>
        </field>
        <field name="categories" type="category" multiple="true" extension="com_content" label="Categories in scope"/>
        <field name="states" type="text" default="under-review" label="Workflow states in scope"/>
        <field name="show_badges" type="checkboxes" label="Show Badges">
          <option value="ai">AI-Logged</option>
          <option value="unsci">Un Scientific</option>
          <option value="unresearch">Un Research</option>
        </field>
        <field name="warn_days" type="number" default="7" label="Warning threshold (days)"/>
        <field name="danger_days" type="number" default="0" label="Danger threshold (days)"/>
        <field name="quick_accept" type="radio" default="1" label="Enable Accept/Decline actions"/>
        <field name="readonly" type="radio" default="0" label="Read-only mode"/>
        <field name="link_target" type="text" label="Review form menu item URL (optional)"/>
        <field name="max_items" type="number" default="20" label="Max items"/>
        <field name="cache_time" type="number" default="300" label="Cache time (seconds)"/>
      </fieldset>
    </fields>
  </config>
</extension>
```

---

## 14) Test Plan
**Unit/Integration**  
- Helper returns only items assigned to current user; correct overdue calculations.  
- Honors read‑only vs quick action modes; ensures tokens validated if actions enabled.

**Functional**  
- Reviewer sees queue with correct due labels; accepts/declines if allowed; Action Logs written on action.  
- Badges appear when related fields/tags present.  
- Module caching does not leak cross‑user data.

**Regression**  
- Works with template overrides; no assumptions about custom components.  
- No schema added; fields absent → items gracefully skip.

---

## 15) Rollout & Admin Checklist
1. Ensure **Deadlines** repeatable field is configured (see Plugin 04).  
2. Create a menu item or URL for **review form** (or leave to article view).  
3. Place module in desired position, restrict **Access** to Reviewer.  
4. Configure scope categories, badges, thresholds, and quick action behavior.  
5. Test with two dummy reviewers; verify ACL and caching.
