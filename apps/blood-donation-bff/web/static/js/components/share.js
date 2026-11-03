/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Share sheet: WhatsApp, Telegram, Facebook, X, Email, copy link, and the phone's own share menu when there is one.
// Works on plain http too (the browser's clipboard/share APIs only exist on https, so copying falls back to execCommand).
document.addEventListener('alpine:init', () => Alpine.data('shareSheet', (url, title, text, image = '') => ({
  url, title, text, image, native: !!navigator.share && window.isSecureContext,
  get message() { return `${this.text}\n\n${this.url}`; },  // link on its own line = clickable in WhatsApp/Telegram/SMS
  link(kind) {
    const u = encodeURIComponent(this.url), m = encodeURIComponent(this.message), t = encodeURIComponent(this.title);
    return {
      whatsapp: `https://wa.me/?text=${m}`,
      telegram: `https://t.me/share/url?url=${u}&text=${encodeURIComponent(this.text)}`,
      facebook: `https://www.facebook.com/sharer/sharer.php?u=${u}`,
      x: `https://twitter.com/intent/tweet?text=${encodeURIComponent(this.text)}&url=${u}`,
      linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${u}`,
      threads: `https://www.threads.net/intent/post?text=${m}`,
      reddit: `https://www.reddit.com/submit?url=${u}&title=${t}`,
      email: `mailto:?subject=${t}&body=${m}`,
      sms: `sms:?&body=${m}`,
    }[kind];
  },
  copy() { ui.copy(this.url); },
  // Instagram has no web share link: share the picture itself (phones), otherwise save it to post from the app.
  async instagram() {
    if (!this.image) return this.copy();
    try {
      const blob = await (await fetch(this.image)).blob();
      const file = new File([blob], 'blood-donation.png', { type: blob.type || 'image/png' });
      if (window.isSecureContext && navigator.canShare && navigator.canShare({ files: [file] })) {
        await this.copy(); await navigator.share({ files: [file], text: this.message }); return;
      }
    } catch (_) { /* fall back to download */ }
    this.download(); ui.toast('Picture saved and caption copied: open Instagram and post it 📸');
    try { await navigator.clipboard.writeText(this.message); } catch (_) {}
  },
  download() { const a = Object.assign(document.createElement('a'), { href: this.image, download: 'blood-donation.png' }); document.body.appendChild(a); a.click(); a.remove(); },
  async more() { try { await navigator.share({ title: this.title, text: this.text, url: this.url }); } catch (_) { /* closed */ } },
})));
