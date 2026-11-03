/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of LifeFlow Blood Camp and is proprietary and confidential.
 * Unauthorised copying, modification or distribution is strictly prohibited.
 */

document.addEventListener('alpine:init', () => Alpine.data('countdown', (date) => ({
  d: 0, h: 0, m: 0, s: 0, timer: null,
  init() {
    const target = new Date(`${date}T09:00:00`);
    const tick = () => {
      const x = Math.max(0, target - new Date()) / 1000;
      this.d = Math.floor(x / 86400); this.h = Math.floor((x % 86400) / 3600); this.m = Math.floor((x % 3600) / 60); this.s = Math.floor(x % 60);
    };
    tick(); this.timer = setInterval(tick, 1000);
  },
  destroy() { clearInterval(this.timer); },
  pad(n) { return String(n).padStart(2, '0'); },
  get label() { return this.d > 1 ? `${this.d} days to go` : this.d === 1 ? 'Tomorrow' : 'Happening today'; },
})));
