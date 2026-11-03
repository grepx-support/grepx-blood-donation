/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of LifeFlow Blood Camp and is proprietary and confidential.
 * Unauthorised copying, modification or distribution is strictly prohibited.
 */

document.addEventListener('alpine:init', () => Alpine.data('countUp', (to) => ({
  v: 0,
  init() {
    const io = new IntersectionObserver(([e]) => {
      if (!e.isIntersecting) return;
      io.disconnect();
      const t0 = performance.now();
      const step = (t) => { const p = Math.min(1, (t - t0) / 1200); this.v = Math.round(to * (1 - (1 - p) ** 3)).toLocaleString(); if (p < 1) requestAnimationFrame(step); };
      requestAnimationFrame(step);
    });
    io.observe(this.$el);
  },
})));
