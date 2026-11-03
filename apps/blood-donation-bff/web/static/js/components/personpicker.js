/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of LifeFlow Blood Camp and is proprietary and confidential.
 * Unauthorised copying, modification or distribution is strictly prohibited.
 */

// Search-as-you-type person picker (works with tens of thousands of people). Optionally bound to a task object `t`.
document.addEventListener('alpine:init', () => Alpine.data('personPicker', (bindTask = false) => ({
  q: '', results: [], openList: false, ownId: '', ownName: 'Unassigned', bindTask,
  get pickedId() { return this.bindTask ? (this.t.assignee_id === 'none' ? '' : this.t.assignee_id || '') : this.ownId; },
  get pickedName() { return this.bindTask ? (this.t.assignee_id === 'none' || !this.t.assignee_id ? 'Unassigned' : this.t.assignee || 'Me') : this.ownName; },
  pick(id, name) {
    if (this.bindTask) { this.t.assignee_id = id ? String(id) : 'none'; this.t.assignee = name; } else { this.ownId = id ? String(id) : ''; this.ownName = name; }
    this.q = ''; this.results = []; this.openList = false;
  },
  async search() {
    const q = this.q.trim(); this.openList = true;
    const r = await fetch('/admin/tasks/people?q=' + encodeURIComponent(q), { headers: { Accept: 'application/json' } });
    this.results = r.ok ? await r.json() : [];
  },
})));
