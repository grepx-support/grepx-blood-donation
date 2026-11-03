/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of LifeFlow Blood Camp and is proprietary and confidential.
 * Unauthorised copying, modification or distribution is strictly prohibited.
 */

document.addEventListener('alpine:init', () => Alpine.data('calendar', (url) => ({
  init() {
    new FullCalendar.Calendar(this.$el, {
      initialView: innerWidth < 768 ? 'listWeek' : 'dayGridMonth', firstDay: 1, height: 'auto', nowIndicator: true, eventDisplay: 'block',
      headerToolbar: { left: 'prev,next today', center: 'title', right: 'dayGridMonth,timeGridWeek,listWeek' }, events: url,
    }).render();
  },
})));
