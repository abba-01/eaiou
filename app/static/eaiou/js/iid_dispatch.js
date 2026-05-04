/* ============================================================================
   iid_dispatch.js — client-side IID action dispatcher.
   ============================================================================
   Exports window.eaiou.iidDispatch({ providerId, actionName, inputs, manuscriptId }).

   Flow:
     1. Generate Idempotency-Key (UUID) per click
     2. Insert placeholder card (animated, "running...") into [data-iid-output-stream]
     3. POST /api/iid/invoke with { provider_id, action_name, inputs, manuscript_id }
     4. Server returns { ...action, html_fragment } where html_fragment is the
        rendered _iid_output_card.html (with mandatory disclosure block)
     5. Replace placeholder with html_fragment via outerHTML
     6. On error: replace placeholder with error variant; preserve audit row

   Compliance:
     * No chaining: each click is a single dispatch with original inputs only
     * No background invocation: only fired by user click events (Rule 2)
     * Disclosure block: server emits it in html_fragment; client never strips
   ============================================================================ */
(function () {
  'use strict';

  window.eaiou = window.eaiou || {};

  /**
   * Dispatch one IID action.
   * @param {object} args
   * @param {string|number} args.providerId
   * @param {string} args.actionName
   * @param {object} args.inputs
   * @param {string|number|null} args.manuscriptId
   * @returns {Promise<object>} the server's action record
   */
  window.eaiou.iidDispatch = async function ({ providerId, actionName, inputs, manuscriptId }) {
    const stream = document.querySelector('[data-iid-output-stream]');
    if (!stream) {
      console.warn('No [data-iid-output-stream] on page; output will not render');
    }

    const idemKey = (window.crypto && window.crypto.randomUUID)
      ? window.crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

    // Placeholder card — visible during the round-trip
    const placeholder = renderPlaceholder({ providerId, actionName });
    if (stream) {
      stream.prepend(placeholder);
    }

    try {
      const res = await fetch('/api/iid/invoke', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Idempotency-Key': idemKey,
        },
        credentials: 'same-origin',
        body: JSON.stringify({
          provider_id: parseInt(providerId, 10),
          action_name: actionName,
          inputs: inputs || {},
          manuscript_id: manuscriptId ? parseInt(manuscriptId, 10) : null,
        }),
      });

      if (!res.ok) {
        const errBody = await safeReadBody(res);
        throw new Error(`HTTP ${res.status}: ${errBody}`);
      }

      const payload = await res.json();
      if (placeholder.parentNode) {
        if (payload.html_fragment) {
          // Server-rendered card with mandatory disclosure block — drop in directly
          const wrapper = document.createElement('div');
          wrapper.innerHTML = payload.html_fragment;
          const card = wrapper.firstElementChild;
          if (card) {
            placeholder.replaceWith(card);
          } else {
            // Fallback: server returned text but no element
            placeholder.querySelector('[data-iid-status]').textContent = payload.result_text || 'completed';
          }
        } else {
          // No fragment from server; client-side fallback render
          placeholder.replaceWith(renderClientCard(payload));
        }
      }
      return payload;
    } catch (err) {
      console.error('IID dispatch failed', err);
      if (placeholder.parentNode) {
        const status = placeholder.querySelector('[data-iid-status]');
        if (status) {
          status.textContent = `failed: ${err.message || err}`;
          status.style.color = 'var(--color-acad-red)';
        }
        placeholder.classList.remove('animate-pulse');
        placeholder.dataset.iidFailed = '1';
      }
      throw err;
    }
  };

  // ── Internal renderers ──────────────────────────────────────────────────────

  function renderPlaceholder({ providerId, actionName }) {
    const el = document.createElement('article');
    el.className = 'kt-module animate-pulse';
    el.dataset.iidPlaceholder = '1';
    el.innerHTML = `
      <div class="flex items-center gap-2 mb-2">
        <span class="iid-chip">${escape(actionName)}</span>
        <span class="text-xs text-muted-foreground" data-iid-status>running...</span>
      </div>
      <div class="text-sm text-muted-foreground italic">Awaiting IID response — provider ${escape(String(providerId))}</div>
    `;
    return el;
  }

  function renderClientCard(payload) {
    // Fallback when server didn't include html_fragment.
    // Renders a minimal card with disclosure block.
    const el = document.createElement('article');
    el.className = 'kt-module';
    el.dataset.iidOutputId = payload.id;
    el.dataset.iidIntellid = payload.intellid;
    el.dataset.provider = (payload.provider && payload.provider.name) || '';

    const provider = payload.provider || {};
    const action = payload.action || {};
    const body = payload.body_html || (payload.result_text ? `<p>${escape(payload.result_text)}</p>` : '<p class="text-muted-foreground italic">(no result body)</p>');

    el.innerHTML = `
      <header class="flex items-center justify-between mb-2 flex-wrap gap-2">
        <div class="flex items-center gap-2">
          <span class="iid-chip iid-chip-${escape(provider.name || 'custom')}">${escape(provider.display_name || provider.name || 'Provider')} · ${escape(action.name || '')}</span>
          <span class="text-xs text-muted-foreground">${escape(payload.created_at_display || 'just now')}${payload.cost_display ? ' · ' + escape(payload.cost_display) : ''}</span>
          ${payload.stub ? '<span class="iid-chip" style="background:#FEF3C7;color:#92400E;border:1px solid #F59E0B;">⚠ STUB</span>' : ''}
        </div>
      </header>
      <div class="kt-manuscript-body text-[14px] leading-[1.6] space-y-2">${body}</div>
      <footer class="iid-disclosure mt-3" data-iid-disclosure>
        provider=${escape(provider.legal_name || provider.display_name || '')} ·
        model_family=${escape(payload.model_family || '')} ·
        instance_hash=${escape(payload.instance_hash || '')}<br>
        action=${escape(action.name || '')} ·
        timestamp=${escape((payload.created_at && (payload.created_at.toString())) || '')}Z
      </footer>
    `;
    return el;
  }

  function escape(s) {
    return String(s ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  async function safeReadBody(res) {
    try {
      const txt = await res.text();
      return txt.slice(0, 500);
    } catch (e) {
      return res.statusText || 'unknown error';
    }
  }
})();
