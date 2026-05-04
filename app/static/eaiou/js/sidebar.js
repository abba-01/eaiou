/* ============================================================================
   sidebar.js — eaiou authoring-surface sidebar state persistence
   ============================================================================
   Persists left + right sidebar collapse/hidden state to localStorage,
   keyed per (user_id, manuscript_id) so each manuscript remembers its own
   layout mode.

   Reads body data attributes (set in layout/base.html):
     data-user-id="<id>"
     data-manuscript-id="<id>"

   Watches body class changes for these collapse/hidden flags:
     kt-sidebar-collapse        (left collapsed to icon rail)
     kt-sidebar-hidden          (left hidden — ajax-removed)
     kt-sidebar-right-collapse  (right collapsed)
     kt-sidebar-right-hidden    (right hidden)

   Persists on every change. Restoration happens earlier — in the inline
   <script> block in base.html, before this script loads — so the page
   never flashes the wrong layout.
   ============================================================================ */
(function () {
  'use strict';

  const userId = document.body.dataset.userId;
  const manuscriptId = document.body.dataset.manuscriptId;

  // No persistence if we can't key the state. Authoring pages always have a
  // manuscript loaded; admin/static pages don't and that's fine — sidebar
  // state on those is session-only.
  if (!userId || !manuscriptId) return;

  const storageKey = `eaiou-sidebar-${userId}-${manuscriptId}`;

  function persist() {
    try {
      const cls = document.body.classList;
      localStorage.setItem(storageKey, JSON.stringify({
        leftCollapsed:  cls.contains('kt-sidebar-collapse'),
        leftHidden:     cls.contains('kt-sidebar-hidden'),
        rightCollapsed: cls.contains('kt-sidebar-right-collapse'),
        rightHidden:    cls.contains('kt-sidebar-right-hidden'),
      }));
    } catch (e) {
      // localStorage unavailable (private mode, quota exceeded). Fail silent.
    }
  }

  // MutationObserver on body class is the cleanest hook — Metronic toggles
  // body classes via data-kt-toggle, our header buttons toggle via inline
  // onclick, both routes converge through body.classList changes.
  const observer = new MutationObserver(persist);
  observer.observe(document.body, {
    attributes: true,
    attributeFilter: ['class'],
  });

  // Persist once on load to capture the initial state (in case something
  // changed during boot before the observer attached).
  persist();
})();
