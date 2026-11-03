/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of LifeFlow Blood Camp and is proprietary and confidential.
 * Unauthorised copying, modification or distribution is strictly prohibited.
 */

// Mermaid flowcharts, themed to match light/dark mode.
document.addEventListener('DOMContentLoaded', () => {
  if (!window.mermaid || !document.querySelector('pre.mermaid')) return;
  const dark = document.documentElement.dataset.theme === 'lifeflow-dark';
  mermaid.initialize({ startOnLoad: false, theme: 'base', fontFamily: '"Plus Jakarta Sans", system-ui, sans-serif', themeVariables: {
    primaryColor: dark ? '#3b0d19' : '#ffe4e6', primaryTextColor: dark ? '#f5efee' : '#1c1917', primaryBorderColor: '#e11d48',
    lineColor: '#e11d48', secondaryColor: dark ? '#2a2124' : '#fff7ed', tertiaryColor: dark ? '#171214' : '#ffffff' } });
  mermaid.run({ querySelector: 'pre.mermaid' });
  window.addEventListener('themechange', () => location.reload());
});
