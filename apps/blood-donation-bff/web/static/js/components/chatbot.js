/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of LifeFlow Blood Camp and is proprietary and confidential.
 * Unauthorised copying, modification or distribution is strictly prohibited.
 */

document.addEventListener('alpine:init', () => Alpine.data('chatbot', () => ({
  isOpen: false, started: false, typing: false, messages: [], options: [], link: null, info: null, text: '', progress: 0, seq: 0,
  open() { this.isOpen = true; if (!this.started) { this.started = true; this.send('__start__', true); } this.$nextTick(() => this.$refs.input.focus()); },
  toggle() { this.isOpen ? (this.isOpen = false) : this.open(); },
  restart() { this.messages = []; this.send('__start__', true); },
  submit() { const t = this.text.trim(); if (t) { this.text = ''; this.send(t); } },
  add(text, me) { this.messages.push({ id: ++this.seq, text, me }); this.$nextTick(() => this.$refs.log.scrollTo({ top: 1e9, behavior: 'smooth' })); },
  async send(message, silent = false) {
    if (!silent) this.add(message, true);
    this.options = []; this.link = null; this.info = null; this.typing = true;
    try {
      const [r] = await Promise.all([ui.post('/api/chat', { message }), new Promise((ok) => setTimeout(ok, 450))]);
      this.add(r.reply, false); this.options = r.options || []; this.link = r.link || null; this.info = r.info || null; this.progress = r.progress ?? 100;
      if (r.eligible) ui.celebrate();
    } catch (e) { this.add('Sorry, I lost connection. Please try again.', false); }
    this.typing = false;
  },
})));
