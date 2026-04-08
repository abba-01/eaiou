# Module 06 — Editor Dashboard KPIs (mod_editor_dashboard)
**Status:** Draft (Planning)  
**Target Stack:** Joomla 5.3 (LAMP) — Core-first, strict MVC, **no custom DB tables**  
**Extension Type:** `module` (admin; optionally site for private dashboards)  
**Goal:** Give Editors/EIC a live KPI panel sourced only from **core Articles, Custom Fields, Workflows, Action Logs, and Scheduler history**. Zero schema changes.

---

## 1) Purpose
Present actionable editorial metrics at a glance:
- Submissions by workflow state (today / 7d / 30d)
- Time-to-first-decision (TTFD) median / P90
- Overdue items (reviews, revisions, decisions) counts
- Reviewer throughput (assigned, completed, late) + top bottlenecks
- Acceptance / rejection rates over a window
- Aging buckets per state (0–7, 8–14, 15–30, 31–60, 60+ days)
- Queue by editor/section

All numbers computed from **core records**; nothing stored.

---

## 2) Core-first Dependencies
- **com_content (Articles)** for submissions, states, dates (created, modified, publish_up).  
- **Custom Fields**: Deadlines (from Plugin 04), AI/Un Scientific flags (Plugins 02/03).  
- **Workflows**: state IDs/names, transitions (used to infer decisions).  
- **Action Logs**: timestamps for events (e.g., decision, review submitted) when available.  
- **Scheduler**: optional count of last nudger runs and sent emails (read-only).

---

## 3) KPIs & Computation (read-only)
### A. State Snapshot
- Cards: **New**, **Under Review**, **Revisions**, **Awaiting Decision**, **Accepted**, **Published**, **Rejected**  
- Filter by **Categories** (journals/sections) and **Date window** (created within).

### B. Overdue
- **Reviews overdue**: reviewer assignment rows where `rev_due_date < today` and status `Accepted` (or `Pending` beyond invite due).  
- **Revisions overdue**: `auth_rev_due < today`.  
- **Decisions overdue**: `ed_followup_due < today`.

### C. TTFD (Time to First Decision)
- For items that reached a decision state (Accept/Reject/Revise), compute `decision_time = decision_timestamp - created`.  
- Decision timestamp inferred from:  
  1) Workflow transition logs if available; otherwise  
  2) First time state became one of {Accepted, Rejected, Revisions Requested}.  
- Show **Median** and **P90**; optional histogram bars.

### D. Reviewer Throughput
- Per reviewer: assigned count (window), completed count (window), on-time %, avg days to submit.  
- Uses **rev_invite_assignments** entries and action logs for completion (or a boolean field if present).

### E. Rates & Trends
- Acceptance / Rejection rates in window.  
- Submissions trend (sparkline) by week.  
- Reviews completed per week.

### F. Aging Buckets by State
- Buckets by `today - created` for items in each state.

### G. Flags Summary
- Count of items with **AI-Logged**, **Un Scientific**, **Un Research** within filters.

> All of the above are derived from Articles + Fields + Logs only; no writes.

---

## 4) UI / Rendering
- **Grid of KPI cards**, mini charts (SVG) and tables.  
- Tabs: **Overview**, **Overdue**, **Reviewers**, **Trends**, **Flags**.  
- Filters bar (top): Date window, Categories, States, Editor, Reviewer.  
- Export buttons: CSV for visible tables (produced on the fly).

Assets via **WebAsset API**; no global CSS pollution.

---

## 5) Module Parameters
- **Client**: Admin / Site.  
- **Scope categories** (multi-select).  
- **States in scope** (CSV list).  
- **Date window**: last N days (default 30).  
- **Overdue thresholds**: use `rev_due_date`, `auth_rev_due`, `ed_followup_due`.  
- **Reviewer mode**: Per-assignment field name (defaults to spec from Plugin 04).  
- **Charts**: enable micro charts (Yes/No).  
- **Export**: enable CSV export (Yes/No).  
- **Cache**: enable; **TTL** (seconds).

---

## 6) ACL
- **Access**: Editors, Section Editors, EIC, Admin.  
- Site variant (if used) must be restricted to private access level.

---

## 7) Data Sources & Queries
- Use **\Joomla\Component\Content\Site\Model\ArticlesModel** with filter overrides (categories, dates, states).  
- Join on **fields** JSON to read deadlines and flags.  
- Read **Action Log** model for decision/complete timestamps when available.  
- Optionally read **Scheduler history** for last nudger run counts (display-only).

---

## 8) Internationalization (i18n)
Example keys:
```
MOD_EDITOR_DASHBOARD="Editor Dashboard"
MOD_EDITOR_DASHBOARD_OVERVIEW="Overview"
MOD_EDITOR_DASHBOARD_OVERDUE="Overdue"
MOD_EDITOR_DASHBOARD_REVIEWERS="Reviewers"
MOD_EDITOR_DASHBOARD_TRENDS="Trends"
MOD_EDITOR_DASHBOARD_FLAGS="Flags"
MOD_EDITOR_DASHBOARD_TTFD="Time to First Decision"
MOD_EDITOR_DASHBOARD_P90="P90"
MOD_EDITOR_DASHBOARD_MEDIAN="Median"
MOD_EDITOR_DASHBOARD_ACCEPT_RATE="Acceptance Rate"
MOD_EDITOR_DASHBOARD_REJECT_RATE="Rejection Rate"
MOD_EDITOR_DASHBOARD_AGING="Aging Buckets"
MOD_EDITOR_DASHBOARD_EXPORT="Export CSV"
```

---

## 9) File/Folder Scaffold
```
/modules/mod_editor_dashboard/mod_editor_dashboard.php
/modules/mod_editor_dashboard/mod_editor_dashboard.xml
/modules/mod_editor_dashboard/helper.php
/modules/mod_editor_dashboard/tmpl/default.php
/modules/mod_editor_dashboard/tmpl/overdue.php
/modules/mod_editor_dashboard/tmpl/reviewers.php
/modules/mod_editor_dashboard/tmpl/trends.php
/modules/mod_editor_dashboard/tmpl/flags.php
/modules/mod_editor_dashboard/media/css/editor_dashboard.css
/modules/mod_editor_dashboard/media/js/editor_dashboard.js
/modules/mod_editor_dashboard/language/en-GB/en-GB.mod_editor_dashboard.ini
/modules/mod_editor_dashboard/language/en-GB/en-GB.mod_editor_dashboard.sys.ini
```

- `helper.php` composes all KPI queries and structures data.  
- Templates are modular per tab for clarity.  
- CSV export generated from the current dataset in memory (no storage).

---

## 10) Minimal Manifest (mod_editor_dashboard.xml)
```xml
<?xml version="1.0" encoding="utf-8"?>
<extension type="module" client="administrator" method="upgrade" version="5.0">
  <name>mod_editor_dashboard</name>
  <author>AIEOU.org</author>
  <version>0.1.0</version>
  <description>Admin KPI dashboard for editorial workflows using core content only.</description>
  <files>
    <filename module="mod_editor_dashboard">mod_editor_dashboard.php</filename>
    <filename>helper.php</filename>
    <folder>tmpl</folder>
    <folder>media</folder>
  </files>
  <languages>
    <language tag="en-GB">language/en-GB/en-GB.mod_editor_dashboard.ini</language>
    <language tag="en-GB">language/en-GB/en-GB.mod_editor_dashboard.sys.ini</language>
  </languages>
  <config>
    <fields name="params">
      <fieldset name="basic">
        <field name="categories" type="category" multiple="true" extension="com_content" label="Categories in scope"/>
        <field name="states" type="text" default="new,under-review,revisions,awaiting-decision,accepted,published,rejected" label="Workflow states in scope"/>
        <field name="window_days" type="number" default="30" label="Date window (days)"/>
        <field name="charts" type="radio" default="1" label="Enable mini charts"/>
        <field name="export" type="radio" default="1" label="Enable CSV export"/>
        <field name="cache_time" type="number" default="300" label="Cache time (seconds)"/>
      </fieldset>
    </fields>
  </config>
</extension>
```

---

## 11) Test Plan
**Unit/Integration**  
- Helper filters by categories/states/window; aggregates counts correctly.  
- TTFD calculations robust when decision timestamps come from logs vs state changes.  
- Overdue counts reflect deadline fields; no false positives when fields missing.

**Functional**  
- Dashboard updates with filters; charts toggle on/off.  
- CSV export matches the visible table rows.  
- Cache isolates admin sessions; no cross-user leakage.

**Regression**  
- Works with admin template overrides; no schema assumptions.  
- Handles missing fields gracefully; zero writes.

---

## 12) Rollout & Admin Checklist
1. Ensure **Deadlines** Field Group exists; plugins 02–04 configured.  
2. Place module in **cpanel** or an admin position; set ACL to Editors+.  
3. Configure categories/states/window; test metrics with sample data.  
4. (Optional) Enable site variant with a private menu & access level.
