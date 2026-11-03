/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of the GrepX platform and is proprietary and confidential.
 * Unauthorised copying, use, modification or distribution is strictly prohibited.
 */

// Camera QR check-in (html5-qrcode). Needs https or localhost for camera access.
document.addEventListener('alpine:init', () => Alpine.data('scanner', (url) => ({
  open: false, cam: null, busy: false,
  start() {
    this.open = true;
    this.$nextTick(() => {
      this.cam = new Html5Qrcode('qr-reader');
      this.cam.start({ facingMode: 'environment' }, { fps: 10, qrbox: { width: 240, height: 240 } }, (text) => this.found(text))
        .catch(() => { ui.toast('Camera unavailable — allow camera access (works on https or localhost).', 'error'); this.open = false; });
    });
  },
  stop() { this.open = false; if (this.cam) this.cam.stop().catch(() => {}).finally(() => this.cam.clear()); },
  async found(code) {
    if (this.busy) return;
    this.busy = true;
    try {
      const r = await ui.post(url, { code });
      ui.toast(r.message); ui.celebrate();
      htmx.ajax('GET', location.href, { target: '#attendees', select: '#attendees', swap: 'outerHTML' });
    } catch (e) { ui.toast("That QR code isn't a donor card.", 'error'); }
    setTimeout(() => (this.busy = false), 2500);
  },
})));
