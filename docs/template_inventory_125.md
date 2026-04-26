# eaiou Template Inventory — 125 Items
**Scrubbed 2026-04-12** | Source: 168-item raw list; removed 43 (30 numbered dups + 1 Settings dup + 12 non-eaiou case-management)

Legend: `[built]` = file exists in app/templates/ | `[ut - ...]` = unbuilt concept | no tag = partially wired or wireframe-only

---

## Authentication
- Login.html [built: auth/login.html]
- Register.html [built]
- Password Reset.html [ut - local auth password reset]
- Email Verification.html [ut - email verify flow]
- OAuth Redirect.html [ut - intermediate OAuth splash]

## Public / Discovery
- Home.html [built: index.html]
- About.html [built: about.html]
- Paper List (Public).html [built: papers/list.html]
- Paper Detail (Public).html [built: papers/detail.html]
- Paper Status (Public).html [built: papers/status.html]
- Search (Papers).html [ut - paper search results]
- Search (Gaps).html [ut - gitgap gap search results]
- Gap Detail (Public).html [ut - public gap page]
- ORCID Author Profile.html [ut - public author profile via ORCID]
- Reviewer Profile (Public).html [ut - public reviewer bio page]

## Submission Flow (Author)
- Submit (Intake Wizard).html [built: author/intake.html]
- Submit (Full Form).html [built: author/submit.html]
- Submitted Confirmation.html [built: papers/submitted.html]
- Submission Hub.html [built: author/submission_hub.html]
- Author Dashboard.html [built: author/dashboard.html]
- Author Workspace.html [built: author/workspace.html]
- File Drawer.html [built: author/drawer.html]
- Version Control.html [wireframe: views/29_version_control.html]
- Transparency.html [wireframe: views/24_transparency.html]
- Notifications.html [wireframe: views/14_notifications.html]
- Messages (Communication Center).html [wireframe: views/01_communication_center.html]
- Messages v2.html [wireframe: views/17_communication_center.html]
- Revision Response Form.html [ut - author responds to revision request]
- Revision History.html [ut - full revision round timeline]
- Gap Anchor Card.html [ut - author links paper to gitgap gap]
- IntelliD Disclosure Form.html [ut - author declares AI contributors]

## Editor Workflow
- Editor Dashboard.html [built: editor/dashboard.html]
- Editor Queue.html [built: editor/queue.html]
- Paper Detail (Editor).html [built: editor/paper_detail.html]
- Status Transition Form.html [built: inline in paper_detail.html]
- Rejection Form.html [ut - standalone rejection reason/notes form]
- Revision Request Form.html [ut - standalone revision instructions form]
- Publication Form.html [ut - DOI + Zenodo receipt on publish]
- Q Score Panel.html [ut - dedicated Q score management page]
- Q Score Breakdown.html [ut - visual Q breakdown (basin/investigation/completeness/gap)]
- Reviewer Assignment.html [wireframe: views/16_reviewer_matching.html]
- Reviewer Management.html [wireframe: views/18_reviewer_management.html]
- Conflict Detection.html [wireframe: views/20_conflict_detection.html]
- Review Model.html [wireframe: views/21_review_model.html]
- Reviewer Performance.html [wireframe: views/15_reviewer_performance.html]
- Reviewer Database.html [wireframe: views/19_reviewer_database.html]
- Online Platforms.html [wireframe: views/25_online_platforms.html]

## Report / Coverage Analysis
- Report Form.html [built: report.html]
- Report Results.html [built: inline in report.html]
- Coverage Breakdown.html [ut - standalone coverage detail view]
- Plagiarism Check.html [wireframe: views/23_plagiarism_check.html]

## Article View
- The Article.html [wireframe: views/22_the_article.html]
- Article CoA Seal.html [ut - integrity seal verification page]
- Article IntelliD Graph.html [ut - contributor network visualization]
- Article Trajectory Tree.html [ut - rewrite/branch history tree]

## Admin
- Admin Dashboard.html [built: admin/dashboard.html]
- Admin Users.html [built: admin/users.html]
- Admin User Form.html [built: admin/user_form.html]
- Admin Settings.html [ut - site-wide configuration panel]
- Admin Groups.html [ut - group management]
- Admin Notifications Log.html [ut - all notification history]
- Admin Paper Export.html [ut - bulk export for editorial records]
- Admin Gap Sync.html [ut - manual gitgap webhook retry]

## IntelliD / Intelligence
- IntelliD Registry.html [ut - list of all registered intelligence instances]
- IntelliD Detail.html [ut - single intellid + all contributions]
- IntelliD Contribution Form.html [ut - add/edit contribution record]
- Temporal Blindness Policy.html [built: policy/temporal-blindness.html]
- AI Disclosure Policy.html [built: policy/ai-disclosure.html]
- Intelligence Blindness Policy.html [built: policy/intelligence-blindness.html]
- Open Access Policy.html [built: policy/open-access.html]
- SAID Overview.html [ut - SAID framework explainer page]

## Gitgap Integration
- Gap Map (Dial).html [ut - interactive gap dial/visualization]
- Gap Detail (Editor).html [ut - editor view of linked gap + lifecycle]
- Gap Submission Portal.html [ut - submit paper directly against a gap]
- NCF Lifecycle Explainer.html [ut - NAUGHT/CAUGHT/FOUND explainer]
- Gitgap Webhook Log.html [ut - admin view of all fired webhooks]

## Reviewer Interface (Future)
- Reviewer Dashboard.html [ut - assigned paper queue for reviewers]
- Review Form.html [ut - structured review submission]
- Review View.html [ut - read-only view of submitted review]
- Reviewer Invite.html [ut - editor sends invitation to reviewer]
- Volley Log.html [ut - interrogation/volley history for a paper]

## Notifications
- Notification Center.html [ut - full notification list with mark-read]
- Notification Email Preview.html [ut - admin: preview what author receives]

## Errors / System
- 404 Not Found.html [built: errors/404.html]
- 500 Server Error.html [built: errors/500.html]
- 403 Forbidden.html [ut - explicit 403 page (currently redirects)]
- Maintenance Mode.html [ut - system-wide maintenance splash]

## Policies / Legal
- Terms of Service.html [ut]
- Privacy Policy.html [ut]
- AI Disclosure Policy.html [built: policy/ai-disclosure.html]
- Open Access Policy.html [built: policy/open-access.html]
- Temporal Blindness Policy.html [built: policy/temporal-blindness.html]
- Intelligence Blindness Policy.html [built: policy/intelligence-blindness.html]
- Cookie Notice.html [ut]

## Onboarding / Help
- Getting Started (Author).html [ut - author onboarding wizard]
- Getting Started (Editor).html [ut - editor onboarding wizard]
- Help Center.html [ut - FAQ / how-to index]
- Keyboard Shortcuts.html [ut - modal or page listing shortcuts]

## Wireframe Views (numbered, locked UXPilot designs)
- views/01_communication_center.html [wired: /author/messages]
- views/13_status_tracking.html [wired: /papers/status/{id}]
- views/14_notifications.html [wired: /author/notifications]
- views/15_reviewer_performance.html [not routed]
- views/16_reviewer_matching.html [not routed]
- views/17_communication_center.html [wired: /author/messages-v2]
- views/18_reviewer_management.html [not routed]
- views/19_reviewer_database.html [not routed]
- views/20_conflict_detection.html [not routed]
- views/21_review_model.html [not routed]
- views/22_the_article.html [wired: /papers/{id}]
- views/23_plagiarism_check.html [not routed]
- views/24_transparency.html [wired: /author/papers/{id}/transparency]
- views/25_online_platforms.html [not routed]
- views/28_submission_form.html [wired: /author/intake]
- views/29_version_control.html [wired: /author/papers/{id}/versions]
- views/30_submission_dashboard.html [wired: /author/]

## Base / Layout Shells (consolidation target)
- base.html [built: base.html — public pages]
- base_author.html [built: author/base_author.html]
- base_editor.html [built: editor/base_editor.html]
- base_admin.html [built: admin/base_admin.html]
- base/base.html [built: wireframe base]
- base/layout_a.html [built: wireframe layout A]
- base/layout_b.html [built: wireframe layout B — sidebar]
- base/layout_c.html [built: wireframe layout C]
- base_public.html [ut - NEW: unified public shell]
- base_app.html [ut - NEW: unified authenticated shell (author+editor+reviewer)]

---

**Counts:**
- Built (live in app/templates/): ~40
- Wireframe (UXPilot, partially wired): 17
- Unbuilt [ut]: ~68
- Total: 125
