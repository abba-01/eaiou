/* ============================================================================
   manuscript_autosave.js — debounced autosave for the manuscript editor
   ============================================================================
   Wires:
     [data-manuscript-title-input]   → PATCH /api/manuscripts/{id} (title)
     [data-manuscript-editor]        → PUT /api/manuscripts/{id}/blocks (full block list)
     [data-save-state]               → updates the chip (saved / saving / unsaved)

   Debounce:
     Title:  1s after last keystroke (or immediately on blur)
     Body:   2s after last keystroke (longer to avoid hammering on bursty typing)

   Block extraction: walks the contenteditable [data-manuscript-editor] DOM
   and extracts a flat block array with { type, sort_index, text, html, anchor }.
   Phase 0: handles heading_2, heading_3, paragraph. Phase 1+ extends to
   code, blockquote, list_item, math_block, table, figure_caption.

   Concurrency: each save sends the full block array. If a stale tab POSTs after
   a fresh save, the stale version overwrites — known limitation; Phase 1 adds
   ETag / If-Match conditional requests.
   ============================================================================ */
(function () {
  'use strict';

  const editor = document.querySelector('[data-manuscript-editor]');
  const titleInput = document.querySelector('[data-manuscript-title-input]');
  const stateChip = document.querySelector('[data-save-state]');

  const manuscriptId =
    (editor && editor.dataset.manuscriptId) ||
    (titleInput && titleInput.dataset.manuscriptId);

  if (!manuscriptId) return;

  let titleTimer = null;
  let bodyTimer = null;
  let lastSavedTitle = titleInput ? titleInput.value : null;

  // ── Save-state chip helpers ─────────────────────────────────────────────────
  function setState(s) {
    if (!stateChip) return;
    stateChip.dataset.state = s;
    if (s === 'saved') {
      stateChip.innerHTML = '<i class="ki-filled ki-shield-tick"></i> saved';
      stateChip.style.color = 'var(--color-acad-green)';
    } else if (s === 'saving') {
      stateChip.innerHTML = '<i class="ki-filled ki-time"></i> saving…';
      stateChip.style.color = 'var(--color-acad-yellow)';
    } else if (s === 'unsaved') {
      stateChip.innerHTML = '<i class="ki-filled ki-information"></i> unsaved';
      stateChip.style.color = 'var(--color-acad-yellow)';
    } else if (s === 'error') {
      stateChip.innerHTML = '<i class="ki-filled ki-cross-circle"></i> save failed';
      stateChip.style.color = 'var(--color-acad-red)';
    }
  }

  // ── Title autosave ──────────────────────────────────────────────────────────
  if (titleInput) {
    titleInput.addEventListener('input', () => {
      setState('unsaved');
      if (titleTimer) clearTimeout(titleTimer);
      titleTimer = setTimeout(saveTitle, 1000);
    });
    titleInput.addEventListener('blur', () => {
      if (titleInput.value !== lastSavedTitle) saveTitle();
    });
  }

  async function saveTitle() {
    if (!titleInput || titleInput.value === lastSavedTitle) return;
    setState('saving');
    try {
      const res = await fetch(`/api/manuscripts/${manuscriptId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ title: titleInput.value }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      lastSavedTitle = titleInput.value;
      setState('saved');
    } catch (err) {
      console.error('title save failed', err);
      setState('error');
    }
  }

  // ── Body autosave ───────────────────────────────────────────────────────────
  if (editor) {
    editor.addEventListener('input', () => {
      setState('unsaved');
      if (bodyTimer) clearTimeout(bodyTimer);
      bodyTimer = setTimeout(saveBody, 2000);
    });
    // Also save on Ctrl/Cmd+S
    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        if (bodyTimer) clearTimeout(bodyTimer);
        saveBody();
      }
    });
  }

  async function saveBody() {
    if (!editor) return;
    setState('saving');
    try {
      const blocks = extractBlocks(editor);
      const res = await fetch(`/api/manuscripts/${manuscriptId}/blocks`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ blocks: blocks }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const result = await res.json();
      setState('saved');
      // Update word count if header has the field
      const wcEl = document.querySelector('[data-word-count]');
      if (wcEl && result.word_count != null) {
        wcEl.textContent = `${result.word_count} words`;
      }
    } catch (err) {
      console.error('body save failed', err);
      setState('error');
    }
  }

  // ── Block extraction (Phase 0: H2/H3/P) ─────────────────────────────────────
  function extractBlocks(rootEl) {
    const blocks = [];
    let idx = 0;
    rootEl.querySelectorAll('h2, h3, p').forEach((el) => {
      const tag = el.tagName.toLowerCase();
      const type = (tag === 'h2') ? 'heading_2' : (tag === 'h3') ? 'heading_3' : 'paragraph';
      const text = el.textContent || '';
      const html = (type === 'paragraph') ? el.innerHTML : null;
      const anchor = el.id || null;
      blocks.push({
        type,
        sort_index: idx++,
        text: text.trim(),
        html: html,
        anchor: anchor,
      });
    });
    return blocks;
  }

  // ── Section anchor click handler ───────────────────────────────────────────
  // Section navigator links go to #section-{anchor}; resolve to the actual
  // editor element with that id.
  document.querySelectorAll('a[href^="#section-"]').forEach((link) => {
    link.addEventListener('click', (e) => {
      const target = link.getAttribute('href').replace('#section-', '');
      const el = document.getElementById(target) || editor && editor.querySelector(`#${CSS.escape(target)}`);
      if (el) {
        e.preventDefault();
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
})();
