/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of LifeFlow Blood Camp and is proprietary and confidential.
 * Unauthorised copying, modification or distribution is strictly prohibited.
 */

document.addEventListener('alpine:init', () => Alpine.data('qr', (text) => ({
  init() { const q = qrcode(0, 'M'); q.addData(text); q.make(); this.$el.innerHTML = q.createSvgTag(4, 0); },
})));
