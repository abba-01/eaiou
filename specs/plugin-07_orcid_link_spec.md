# Plugin 07 — ORCID Link (plg_system_orcid_link)
**Status:** Draft (Planning)  
**Target Stack:** Joomla 5.3 (LAMP) — Core‑first, strict MVC, **no custom DB tables**  
**Plugin Type:** `system`  
**Goal:** Allow users (authors/reviewers/editors) to **link their ORCID iD** to their Joomla user profile via OAuth, storing only the **ORCID iD** (and optionally public record URL) in **User Custom Fields**. No tokens persisted by default; privacy‑first. Action Logs record linkage events.

---

## 1) Purpose
- Provide a one‑click **“Connect ORCID”** flow on the user profile page (front/back) and optional login module.  
- Store the verified **ORCID iD** (e.g., `0000-0002-1825-0097`) in a **User Custom Field**.  
- Optionally fetch **public record** (affiliations, works count) for display only (discard after render; no storage by default).  
- Use **no new DB tables**; rely on User Custom Fields + Action Logs.

---

## 2) Core‑first Dependencies
- **Users / User Profiles** (core).  
- **User Custom Fields** for `orcid_id` and `orcid_url`.  
- **Action Logs** for provenance (link/unlink).  
- **Mail Templates** (optional) for confirmation notices.  
- **WebAsset API** for minimal UI scripts/styles.

---

## 3) OAuth Overview (ORCID)
- **Auth endpoint**: `https://orcid.org/oauth/authorize`  
- **Token endpoint**: `https://orcid.org/oauth/token`  
- **Scopes**: minimal — `openid` (authenticate), `read-limited` only if admins explicitly enable profile fetch.  
- **Redirect URI**: plugin exposes a secure endpoint (signed, CSRF‑checked).

> Default behavior: **do not store** access/refresh tokens. Retrieve `orcid` (sub) and `name` from ID token response; persist only the iD and public URL.

---

## 4) Events & Hooks
- **onAfterInitialise**: register a **callback route** (e.g., `/index.php?orcid=callback&token=...`).  
- **onUserAfterSave**: ensure field creation or normalization when user profile is edited.  
- **onContentPrepareForm** (context `com_users.profile` & `com_users.user`): add a **“Connect ORCID / Disconnect”** button next to the custom field.  
- (Optional) **onAfterRoute**: handle signed actions (disconnect), enforce ACL.

---

## 5) User Custom Fields (Profile)
Create Field Group **External IDs** (User context):

- `orcid_id` (Text; **readonly** once verified).  
- `orcid_url` (URL; auto‑derived `https://orcid.org/{orcid_id}`).  
- (Optional) `orcid_verified_at` (Calendar — set when linkage succeeds).

All within core **User Fields** (no new schema).

---

## 6) UI/UX
- **Profile view (frontend/backend)**:  
  - If not linked → show **Connect ORCID** button (opens ORCID authorize).  
  - If linked → show iD & ORCID badge + **Disconnect** link.  
- **Article author box (optional)**: tiny renderer in content plugin (future) to display ORCID badge when author has an iD.  
- **Security**: use Joomla CSRF token and a signed **state** parameter; validate on callback.

---

## 7) Callback & Verification
- Receive `code` and `state`; validate **state** (anti‑CSRF).  
- Exchange for tokens at ORCID token endpoint; parse **ID token / JSON** to obtain the user’s **ORCID iD**.  
- Write to **User Field** `orcid_id`; derive `orcid_url`.  
- **Do not persist tokens** (default). If admin enables “Store token to fetch read‑limited”, encrypt at rest (Joomla secret) and store in plugin params or user field (discouraged; default OFF).

---

## 8) Action Logs
- On link success: `ORCID_LINKED: user={id}, orcid={iD}`  
- On disconnect: `ORCID_DISCONNECTED: user={id}`  
- On failed callback/validation: `ORCID_LINK_FAIL: reason={}`

No PII beyond iD is written to logs.

---

## 9) Plugin Parameters
- **Client ID / Client Secret** (required).  
- **Redirect URL** (display only; auto‑computed from site base + plugin route).  
- **Scopes**: `openid` (default), optional `read-limited`.  
- **Store Tokens**: No (default) / Yes (encrypted).  
- **Auto‑render button** on user profile: Yes/No.  
- **Allowed Groups**: which user groups can link ORCID.  
- **Require ORCID for**: Authors / Reviewers / Editors (block publish or assignment if missing — coordination with other plugins).  
- **UI Texts**: customizable button labels and messages.

---

## 10) Internationalization (i18n)
Example keys:
```
PLG_SYSTEM_ORCID_LINK="ORCID Link"
PLG_SYSTEM_ORCID_LINK_CONNECT="Connect ORCID"
PLG_SYSTEM_ORCID_LINK_DISCONNECT="Disconnect ORCID"
PLG_SYSTEM_ORCID_LINK_VERIFIED="ORCID verified"
PLG_SYSTEM_ORCID_LINK_REQUIRED="ORCID iD is required for this role."
PLG_SYSTEM_ORCID_LINK_ERROR="ORCID linking failed. Please try again."
```

---

## 11) File/Folder Scaffold
```
/plugins/system/orcid_link/orcid_link.php
/plugins/system/orcid_link/orcid_link.xml
/plugins/system/orcid_link/services/provider.php
/plugins/system/orcid_link/language/en-GB/en-GB.plg_system_orcid_link.ini
/plugins/system/orcid_link/language/en-GB/en-GB.plg_system_orcid_link.sys.ini
/plugins/system/orcid_link/media/js/orcid_link.js
/plugins/system/orcid_link/media/css/orcid_link.css
```
- `provider.php` registers the route/callback and any event subscribers.  
- No DB tables; uses core User Fields.

---

## 12) Minimal Manifest (orcid_link.xml)
```xml
<?xml version="1.0" encoding="utf-8"?>
<extension type="plugin" group="system" method="upgrade" version="5.0">
  <name>plg_system_orcid_link</name>
  <author>AIEOU.org</author>
  <version>0.1.0</version>
  <description>Enable users to link a verified ORCID iD to their Joomla profile via OAuth.</description>
  <files>
    <filename plugin="orcid_link">orcid_link.php</filename>
    <filename>services/provider.php</filename>
    <folder>media</folder>
  </files>
  <languages>
    <language tag="en-GB">language/en-GB/en-GB.plg_system_orcid_link.ini</language>
    <language tag="en-GB">language/en-GB/en-GB.plg_system_orcid_link.sys.ini</language>
  </languages>
  <config>
    <fields name="params">
      <fieldset name="basic">
        <field name="client_id" type="password" label="ORCID Client ID" required="true"/>
        <field name="client_secret" type="password" label="ORCID Client Secret" required="true"/>
        <field name="scopes" type="text" default="openid" label="Scopes (CSV)"/>
        <field name="store_tokens" type="radio" default="0" label="Store tokens (encrypted)"/>
        <field name="auto_render" type="radio" default="1" label="Auto-render button on user profile"/>
        <field name="allowed_groups" type="usergrouplist" multiple="true" label="Allowed user groups"/>
        <field name="require_roles" type="checkboxes" label="Require ORCID for roles">
          <option value="author">Authors</option>
          <option value="reviewer">Reviewers</option>
          <option value="editor">Editors</option>
        </field>
      </fieldset>
    </fields>
  </config>
</extension>
```

---

## 13) Test Plan
**Unit/Integration**  
- Callback validates `state`, exchanges `code`, parses iD; writes to `orcid_id`.  
- Disconnect clears fields; logs event.  
- Require‑roles param blocks actions in cooperating plugins (e.g., on publish) if missing.

**Functional**  
- Button appears on profile; linking shows verified badge; link redirects back correctly.  
- If `read-limited` is enabled, profile fetch renders preview but stores nothing by default.

**Security/Privacy**  
- No tokens stored unless enabled; secrets kept in plugin params with encryption.  
- CSRF/state and signature checks; rate‑limit callback processing.

---

## 14) Rollout & Admin Checklist
1. Register ORCID application; obtain **Client ID/Secret**.  
2. Create **User Fields**: `orcid_id` (Text, readonly), `orcid_url` (URL), `orcid_verified_at` (Calendar).  
3. Enable plugin; paste credentials; set scopes and UI behavior.  
4. Add profile menu link; verify Connect/Disconnect flow.  
5. (Optional) Coordinate with content plugins to **require ORCID** for publish/assignment.
