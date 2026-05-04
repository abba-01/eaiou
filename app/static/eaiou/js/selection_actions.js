/* ============================================================================
   selection_actions.js — Floating action-bar wiring for the manuscript editor.
   ============================================================================
   Listens for text selections inside [data-manuscript-editor]; positions
   #selection_action_bar above the selection rectangle; collects selected
   text and target metadata; hands off to window.eaiou.iidDispatch on
   button click.

   Lifecycle:
     selectionchange → if selection inside editor → show bar at rect
                     → if selection outside or collapsed → hide bar
     click on button → dispatch action with selected_text + manuscript_id

   Defensive defaults:
     — no-op if either DOM target is missing (page may not have the bar)
     — passes selection.toString() snapshot at click time, not at hover time
       (so author can re-select before invoking)
     — does NOT auto-execute on selection (Rule 5: author-owned text)
   ============================================================================ */
(function () {
  'use strict';

  const bar = document.getElementById('selection_action_bar');
  if (!bar) return;

  const editor = document.querySelector('[data-manuscript-editor]');
  if (!editor) return;

  const manuscriptId = editor.dataset.manuscriptId || null;

  function withinEditor(node) {
    if (!node) return false;
    const el = node.nodeType === 1 ? node : node.parentElement;
    return el && editor.contains(el);
  }

  function placeBar(rect) {
    bar.classList.remove('hidden');
    bar.classList.add('flex');
    // Position above selection. If insufficient space above, position below.
    const barH = bar.offsetHeight || 40;
    const padding = 8;
    let top = window.scrollY + rect.top - barH - padding;
    if (top < window.scrollY + 8) {
      top = window.scrollY + rect.bottom + padding;
    }
    bar.style.top = `${top}px`;
    bar.style.left = `${window.scrollX + Math.max(rect.left, 8)}px`;
  }

  function hideBar() {
    bar.classList.add('hidden');
    bar.classList.remove('flex');
    delete bar.dataset.selectedText;
  }

  document.addEventListener('selectionchange', () => {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed) {
      hideBar();
      return;
    }
    if (!withinEditor(sel.anchorNode)) {
      hideBar();
      return;
    }
    const range = sel.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    if (rect.width === 0 && rect.height === 0) {
      hideBar();
      return;
    }
    bar.dataset.selectedText = sel.toString();
    placeBar(rect);
  });

  // Hide bar on Escape — predictable, audit-friendly UX
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') hideBar();
  });

  bar.addEventListener('click', (ev) => {
    const btn = ev.target.closest('[data-iid-action]');
    if (!btn) return;
    if (!window.eaiou || typeof window.eaiou.iidDispatch !== 'function') {
      console.error('eaiou.iidDispatch not loaded; cannot invoke', btn.dataset.actionName);
      return;
    }
    const selectedText = bar.dataset.selectedText || '';
    if (!selectedText) {
      console.warn('No selection to act on; ignoring click');
      return;
    }
    window.eaiou.iidDispatch({
      providerId: btn.dataset.providerId,
      actionName: btn.dataset.actionName,
      manuscriptId: manuscriptId,
      inputs: { selected_text: selectedText },
    });
    hideBar();
  });
})();
