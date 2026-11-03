/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Global helpers: toasts (Notyf), confetti, icons (Lucide), CSRF-aware JSON POST.
(() => {
  const notyf = new Notyf({ duration: 4500, dismissible: true, ripple: true, position: { x: 'right', y: 'top' },
    types: [{ type: 'warning', background: '#f59e0b', icon: false }, { type: 'info', background: '#0ea5e9', icon: false }] });
  const KNOWN = ['success', 'error', 'warning', 'info'];
  const csrf = () => document.querySelector('meta[name=csrf-token]').content;
  const ui = window.ui = {
    toast(message, type = 'success') { notyf.open({ type: KNOWN.includes(type) ? type : 'info', message }); },
    celebrate() { window.confetti && confetti({ particleCount: 150, spread: 85, origin: { y: 0.7 }, colors: ['#e11d48', '#fb7185', '#f59e0b', '#ffffff'] }); },
    // Icons are drawn by css/icons.css straight away. lucide.js only fills in a name that isn't in that file yet.
    icons() {
      if (!window.lucide) return;
      const missing = [...document.querySelectorAll('i[data-lucide]')].filter((el) => !getComputedStyle(el).getPropertyValue('--i').trim());
      missing.forEach((el) => el.setAttribute('data-icon-fallback', el.getAttribute('data-lucide')));
      if (missing.length) lucide.createIcons({ nameAttr: 'data-icon-fallback' });
    },
    // Copy that also works on plain http (where navigator.clipboard does not exist)
    async copy(text, done = 'Link copied!') {
      try { await navigator.clipboard.writeText(text); }
      catch (_) {
        const ta = Object.assign(document.createElement('textarea'), { value: text, readOnly: true });
        ta.style.cssText = 'position:fixed;opacity:0'; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); ta.remove();
      }
      ui.toast(done);
    },
    async post(url, data) {
      const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() }, body: JSON.stringify(data) });
      if (!r.ok) { let m = ''; try { m = (await r.json()).message; } catch (_) {} throw new Error(m || r.status); }
      return r.json();
    },
  };
  document.addEventListener('DOMContentLoaded', () => {
    ui.icons();
    JSON.parse(document.getElementById('flashes').textContent || '[]').forEach(([kind, msg]) => {
      ui.toast(msg, kind === 'celebrate' ? 'success' : kind);
      if (kind === 'celebrate') ui.celebrate();
    });
  });
  document.body.addEventListener('toast', (e) => ui.toast(e.detail.message, e.detail.type));
  document.addEventListener('htmx:afterSwap', ui.icons);
  // Back/forward cache: never show a stored copy of a page; re-ask the server (logged-out users get the login page).
  window.addEventListener('pageshow', (e) => { if (e.persisted) location.reload(); });
})();
// Auto-refresh guard: skip live updates while dragging, typing inside the element, in a dialog, or when the tab is hidden.
document.addEventListener('htmx:beforeRequest', (e) => {
  const el = e.detail.elt;
  if (!el.hasAttribute || !el.hasAttribute('data-live')) return;
  const busy = document.hidden || document.body.classList.contains('dragging') || document.querySelector('dialog[open], .modal-open') || el.contains(document.activeElement);
  if (busy) e.preventDefault();
});

// Form rules (attributes come from validation/rules.py, the same limits the server checks):
// phone boxes only accept digits, spaces, dashes and a leading +; every rule shows a friendly message instead of the browser default.
document.addEventListener('input', (e) => {
  const el = e.target;
  if (!(el instanceof HTMLInputElement)) return;
  if (el.hasAttribute('data-phone')) {
    const clean = el.value.replace(/[^\d+\s\-()]/g, '').replace(/(?!^)\+/g, '');
    if (clean !== el.value) { el.value = clean; el.dispatchEvent(new Event('input', { bubbles: true })); }
  }
  if (el.dataset.msg) el.setCustomValidity('');
}, true);
document.addEventListener('invalid', (e) => {
  const el = e.target;
  if (el.dataset && el.dataset.msg && !el.validity.valueMissing) el.setCustomValidity(el.dataset.msg);
}, true);

// Auto-refresh safety: only swap a live section when the reply really contains it. A logged-out reply (login page)
// or a server error must never blank the section; if the session ended, reload so the login page shows.
document.addEventListener('htmx:beforeSwap', (e) => {
  const el = e.detail.elt;
  if (!el || !el.hasAttribute || !el.hasAttribute('data-live')) return;
  const xhr = e.detail.xhr;
  if (xhr.status >= 400 || !xhr.responseText.includes(`id="${el.id}"`)) {
    e.detail.shouldSwap = false;
    if (/\/login/.test(xhr.responseURL || '')) location.reload();
  }
});
