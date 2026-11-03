/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of LifeFlow Blood Camp and is proprietary and confidential.
 * Unauthorised copying, modification or distribution is strictly prohibited.
 */

// Donor grid selection: keeps ticked ids across pages/filters, or "all N matching" the current filters.
document.addEventListener('alpine:init', () => Alpine.data('donorGrid', (total, qs) => ({
  selected: [], allMatching: false, total, qs, editing: {},
  has(id) { return this.allMatching || this.selected.includes(id); },
  toggle(id) { this.allMatching = false; this.has(id) ? (this.selected = this.selected.filter((x) => x !== id)) : this.selected.push(id); },
  pageIds() { return [...this.$root.querySelectorAll('[data-row-id]')].map((el) => +el.dataset.rowId); },
  pageAllChecked() { const ids = this.pageIds(); return ids.length && ids.every((id) => this.has(id)); },
  togglePage(on) { this.allMatching = false; const ids = this.pageIds(); this.selected = on ? [...new Set([...this.selected, ...ids])] : this.selected.filter((x) => !ids.includes(x)); },
  clear() { this.selected = []; this.allMatching = false; },
  get count() { return this.allMatching ? this.total : this.selected.length; },
  refreshed(total, qs) { this.total = total; this.qs = qs; this.allMatching = false; },
  open(id) { document.getElementById(id).showModal(); },
})));
