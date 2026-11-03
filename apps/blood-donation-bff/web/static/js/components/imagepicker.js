/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of LifeFlow Blood Camp and is proprietary and confidential.
 * Unauthorised copying, modification or distribution is strictly prohibited.
 */

// Drag & drop / tap-to-choose pictures with instant previews. Keeps at most `room` files in the real <input type=file>.
document.addEventListener('alpine:init', () => Alpine.data('imagePicker', (room = 3) => ({
  room, items: [], over: false,
  get full() { return this.items.length >= this.room; },
  pick() { this.$refs.file.click(); },
  drop(e) { this.over = false; this.add(e.dataTransfer.files); },
  add(list) {
    for (const f of list) {
      if (!/^image\/(jpeg|png|webp|gif)$/.test(f.type)) { ui.toast(`${f.name}: use JPG, PNG, WebP or GIF`, 'error'); continue; }
      if (f.size > 15 * 1024 * 1024) { ui.toast(`${f.name} is larger than 15 MB`, 'error'); continue; }
      if (this.full) { ui.toast(`Up to ${this.room} picture${this.room === 1 ? '' : 's'}`, 'warning'); break; }
      this.items.push({ file: f, url: URL.createObjectURL(f) });
    }
    this.sync();
    this.$dispatch('pictures', this.items.map((x) => x.url));
  },
  remove(i) { URL.revokeObjectURL(this.items[i].url); this.items.splice(i, 1); this.sync(); this.$dispatch('pictures', this.items.map((x) => x.url)); },
  sync() { const dt = new DataTransfer(); this.items.forEach((x) => dt.items.add(x.file)); this.$refs.file.files = dt.files; },
})));
