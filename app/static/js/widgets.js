/* ═══════════════════════════════════════════════════════════════════════════
   eaiou Widget System v1
   - Drag-and-drop columns via SortableJS
   - Layout persistence via localStorage
   - Notification clock bounce on 120s timer
   ═══════════════════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  const STORAGE_KEY    = 'eaiou-widget-layout-v1';
  const BOUNCE_MS      = 120000; // 2 minutes
  const BOUNCE_CLASS   = 'eaiou-bounce';
  const CLOCK_SELECTOR = '.eaiou-clock-icon';

  /* ── Layout persistence ───────────────────────────────────────────────── */

  function saveLayout(leftId, rightId) {
    const leftOrder  = getWidgetIds(leftId);
    const rightOrder = getWidgetIds(rightId);
    const stored = loadAllLayouts();
    const pageKey = window.location.pathname;
    stored[pageKey] = { left: leftOrder, right: rightOrder };
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
    } catch (_) {}
  }

  function loadAllLayouts() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    } catch (_) { return {}; }
  }

  function getWidgetIds(colId) {
    const col = document.getElementById(colId);
    if (!col) return [];
    return Array.from(col.querySelectorAll('.eaiou-widget'))
                .map(w => w.dataset.widgetId)
                .filter(Boolean);
  }

  function restoreLayout(leftId, rightId) {
    const stored  = loadAllLayouts();
    const pageKey = window.location.pathname;
    const layout  = stored[pageKey];
    if (!layout) return;

    const leftCol  = document.getElementById(leftId);
    const rightCol = document.getElementById(rightId);
    if (!leftCol || !rightCol) return;

    // Collect all widgets from both columns
    const allWidgets = {};
    [leftCol, rightCol].forEach(col => {
      col.querySelectorAll('.eaiou-widget').forEach(w => {
        if (w.dataset.widgetId) allWidgets[w.dataset.widgetId] = w;
      });
    });

    // Re-order left column
    layout.left.forEach(id => {
      if (allWidgets[id]) leftCol.appendChild(allWidgets[id]);
    });

    // Re-order right column
    layout.right.forEach(id => {
      if (allWidgets[id]) rightCol.appendChild(allWidgets[id]);
    });
  }

  /* ── SortableJS column init ───────────────────────────────────────────── */

  function initWidgetColumns(leftId, rightId, toolbarId) {
    if (typeof Sortable === 'undefined') {
      console.warn('eaiou widgets: SortableJS not loaded');
      return;
    }

    const leftCol  = document.getElementById(leftId);
    const rightCol = document.getElementById(rightId);
    const toolbar  = document.getElementById(toolbarId);

    const sharedConfig = {
      animation: 150,
      ghostClass: 'sortable-ghost',
      chosenClass: 'sortable-chosen',
      dragClass: 'sortable-drag',
      group: 'eaiou-widgets',
      handle: '.eaiou-widget',
      onEnd: function () { saveLayout(leftId, rightId); }
    };

    if (leftCol)  new Sortable(leftCol,  { ...sharedConfig });
    if (rightCol) new Sortable(rightCol, { ...sharedConfig });

    // Toolbar is drag-source only (no reorder within toolbar)
    if (toolbar) {
      new Sortable(toolbar, {
        animation: 150,
        ghostClass: 'sortable-ghost',
        group: { name: 'eaiou-widgets', pull: 'clone', put: false },
        sort: false,
        onEnd: function () { saveLayout(leftId, rightId); }
      });
    }

    // Restore saved layout after init
    restoreLayout(leftId, rightId);
  }

  /* ── Widget toolbar toggle ────────────────────────────────────────────── */

  window.eaiouToggleToolbar = function () {
    const toolbar = document.getElementById('eaiou-widget-toolbar');
    if (!toolbar) return;
    toolbar.classList.toggle('open');
    const btn = document.getElementById('eaiou-widget-btn');
    if (btn) btn.setAttribute('aria-expanded', toolbar.classList.contains('open'));
  };

  /* ── Squeeze column expand/collapse ──────────────────────────────────── */

  window.eaiouToggleSqueeze = function (side) {
    const col = document.getElementById('eaiou-squeeze-' + side);
    if (!col) return;
    col.classList.toggle('open');
  };

  /* ── Notification clock bounce timer ─────────────────────────────────── */

  function triggerBounce() {
    document.querySelectorAll(CLOCK_SELECTOR).forEach(function (el) {
      el.classList.remove(BOUNCE_CLASS);
      // Force reflow so animation retriggers if already applied
      void el.offsetWidth;
      el.classList.add(BOUNCE_CLASS);
      el.addEventListener('animationend', function handler() {
        el.classList.remove(BOUNCE_CLASS);
        el.removeEventListener('animationend', handler);
      });
    });
  }

  function startBounceTimer() {
    // Only run if there are clock icons on the page
    if (document.querySelectorAll(CLOCK_SELECTOR).length === 0) return;
    setInterval(triggerBounce, BOUNCE_MS);
  }

  /* ── Public API ───────────────────────────────────────────────────────── */

  window.eaiouWidgets = {
    init: initWidgetColumns,
    startBounceTimer: startBounceTimer,
    triggerBounce: triggerBounce,
    saveLayout: saveLayout,
    restoreLayout: restoreLayout
  };

  /* ── Auto-init on DOMContentLoaded if data attrs present ─────────────── */

  document.addEventListener('DOMContentLoaded', function () {
    const app = document.getElementById('eaiou-widget-app');
    if (app) {
      const left    = app.dataset.leftCol    || 'eaiou-left-col';
      const right   = app.dataset.rightCol   || 'eaiou-right-col';
      const toolbar = app.dataset.toolbarCol || 'eaiou-widget-toolbar-items';
      initWidgetColumns(left, right, toolbar);
    }
    startBounceTimer();
  });

})();
