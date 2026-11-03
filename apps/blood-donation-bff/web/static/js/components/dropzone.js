/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of LifeFlow Blood Camp and is proprietary and confidential.
 * Unauthorised copying, modification or distribution is strictly prohibited.
 */

document.addEventListener('alpine:init', () => Alpine.data('dropzone', () => ({
  over: false, name: '',
  pick() { this.$refs.file.click(); },
  drop(e) { this.over = false; if (e.dataTransfer.files.length) { this.$refs.file.files = e.dataTransfer.files; this.submit(); } },
  submit() {
    const f = this.$refs.file.files[0];
    if (!f) return;
    if (!/\.xlsx$/i.test(f.name)) return ui.toast('Please choose an Excel .xlsx file', 'error');
    this.name = f.name; this.$root.closest('form').submit();
  },
})));
