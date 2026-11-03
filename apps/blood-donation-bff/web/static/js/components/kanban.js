/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Drag & drop board (SortableJS). Each column: <div data-col="status">, each card: data-id. Server URL gets {id, status}.
document.addEventListener('alpine:init', () => Alpine.data('kanban', (url) => ({
  counts: {},
  init() {
    this.cols().forEach((col) => Sortable.create(col, {
      group: col.hasAttribute('data-locked') ? { name: 'board', pull: false, put: false } : 'board', animation: 150,
      sort: !col.hasAttribute('data-locked'), easing: 'cubic-bezier(.2,.8,.2,1)',
      forceFallback: true, fallbackOnBody: true, fallbackTolerance: 4,   // same smooth drag on every browser and on touch screens
      delay: 150, delayOnTouchOnly: true,                                // phones: a short press picks up, a swipe still scrolls
      emptyInsertThreshold: 80, swapThreshold: 0.6, invertSwap: true,    // dropping anywhere over a column works, even an empty one
      scroll: true, bubbleScroll: true, scrollSensitivity: 90,
      filter: () => document.body.classList.contains('selecting'), preventOnFilter: false,  // no dragging while picking cards
      ghostClass: 'sortable-ghost', chosenClass: 'sortable-chosen', fallbackClass: 'sortable-fallback',
      onStart: () => document.body.classList.add('dragging'),
      onMove: (e) => { this.hover(e.to); return true; },
      onEnd: (e) => { document.body.classList.remove('dragging'); this.hover(null); this.moved(e); },
    }));
    this.recount();
  },
  hover(col) { this.cols().forEach((c) => c.classList.toggle('kanban-over', c === col)); },
  cols() { return [...this.$el.querySelectorAll('[data-col]')]; },
  recount() { this.cols().forEach((c) => (this.counts[c.dataset.col] = c.children.length)); },
  async moved(e) {
    if (e.from === e.to) return;
    this.recount();
    try {
      const r = await ui.post(url, { id: e.item.dataset.id, status: e.to.dataset.col });
      ui.toast(r.message);
      if (['donated', 'done'].includes(e.to.dataset.col)) ui.celebrate();
    } catch (err) {
      e.from.insertBefore(e.item, e.from.children[e.oldIndex] || null); this.recount();
      ui.toast(/^\d+$/.test(err.message) ? "Couldn't move that card — please try again." : err.message, 'warning');
    }
  },
})));
