/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of LifeFlow Blood Camp and is proprietary and confidential.
 * Unauthorised copying, modification or distribution is strictly prohibited.
 */

document.addEventListener('alpine:init', () => Alpine.data('datatable', (opts = {}) => ({
  init() {
    const table = this.$el.tagName === 'TABLE' ? this.$el : this.$el.querySelector('table');
    if (!table || !table.tBodies[0] || !table.tBodies[0].rows.length) return;
    const dt = new simpleDatatables.DataTable(table, {
      perPage: 10, perPageSelect: [10, 25, 50, 100], fixedHeight: false,
      labels: { placeholder: 'Search…', noRows: 'Nothing found', info: 'Showing {start}–{end} of {rows}', perPage: 'per page' }, ...opts,
    });
    ['datatable.page', 'datatable.search', 'datatable.sort', 'datatable.perpage', 'datatable.init'].forEach((ev) => dt.on(ev, () => ui.icons()));
  },
})));
