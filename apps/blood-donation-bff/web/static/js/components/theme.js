/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of LifeFlow Blood Camp and is proprietary and confidential.
 * Unauthorised copying, modification or distribution is strictly prohibited.
 */

document.addEventListener('alpine:init', () => Alpine.data('theme', () => ({
  dark: document.documentElement.dataset.theme === 'lifeflow-dark',
  toggle() {
    this.dark = !this.dark;
    const t = this.dark ? 'lifeflow-dark' : 'lifeflow';
    document.documentElement.dataset.theme = t;
    try { localStorage.setItem('theme', t); } catch (e) {}
    window.dispatchEvent(new CustomEvent('themechange'));
  },
})));
