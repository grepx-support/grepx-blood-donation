/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of LifeFlow Blood Camp and is proprietary and confidential.
 * Unauthorised copying, modification or distribution is strictly prohibited.
 */

document.addEventListener('alpine:init', () => Alpine.data('palette', () => ({
  open: false, q: '', active: 0,
  items: JSON.parse(document.getElementById('palette-data').textContent || '[]'),
  init() { this.$watch('q', () => (this.active = 0)); },
  get results() {
    const q = this.q.toLowerCase().trim();
    return this.items.filter((i) => !q || `${i.label} ${i.group} ${i.hint || ''}`.toLowerCase().includes(q)).slice(0, 12);
  },
  show() { this.open = true; this.q = ''; this.$nextTick(() => this.$refs.q.focus()); },
  close() { this.open = false; },
  toggle() { this.open ? this.close() : this.show(); },
  move(d) { const n = this.results.length; if (n) this.active = (this.active + d + n) % n; },
  go() { const it = this.results[this.active]; if (it) location.href = it.url; },
})));
