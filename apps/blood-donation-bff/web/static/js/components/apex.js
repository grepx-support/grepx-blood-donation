/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

document.addEventListener('alpine:init', () => Alpine.data('apex', (opts) => ({
  chart: null,
  init() {
    const mode = () => (document.documentElement.dataset.theme === 'lifeflow-dark' ? 'dark' : 'light');
    this.chart = new ApexCharts(this.$el, {
      ...opts,
      chart: { background: 'transparent', fontFamily: 'inherit', toolbar: { show: false }, ...(opts.chart || {}) },
      colors: ['#e11d48', '#f59e0b', '#8b5cf6', '#0ea5e9', '#10b981', '#ec4899', '#14b8a6', '#64748b'],
      noData: { text: 'No data yet' }, theme: { mode: mode() }, tooltip: { theme: mode() },
    });
    this.chart.render();
    window.addEventListener('themechange', () => this.chart.updateOptions({ theme: { mode: mode() }, tooltip: { theme: mode() } }));
  },
})));
