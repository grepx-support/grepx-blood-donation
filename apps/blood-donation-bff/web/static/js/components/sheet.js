/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of LifeFlow Blood Camp and is proprietary and confidential.
 * Unauthorised copying, modification or distribution is strictly prohibited.
 */

// Spreadsheet-style entry: type into cells or paste straight from Excel/Google Sheets (tab separated).
document.addEventListener('alpine:init', () => Alpine.data('sheet', (keys) => ({
  keys, rows: [],
  init() { this.addRows(8); },
  blank() { return Object.fromEntries(this.keys.map((k) => [k, ''])); },
  addRows(n) { for (let i = 0; i < n; i++) this.rows.push(this.blank()); },
  paste(e, r, c) {
    const text = (e.clipboardData || window.clipboardData).getData('text');
    if (!text.includes('\t') && !text.includes('\n')) return;  // single value: let the browser paste normally
    e.preventDefault();
    text.replace(/\r/g, '').split('\n').filter((l) => l.trim()).forEach((line, i) => {
      if (!this.rows[r + i]) this.rows.push(this.blank());
      line.split('\t').forEach((v, j) => { if (this.keys[c + j]) this.rows[r + i][this.keys[c + j]] = v.trim(); });
    });
    ui.toast('Pasted ' + text.trim().split('\n').length + ' rows');
  },
  get filled() { return this.rows.filter((r) => Object.values(r).some((v) => v)).length; },
  get json() { return JSON.stringify(this.rows); },
})));
