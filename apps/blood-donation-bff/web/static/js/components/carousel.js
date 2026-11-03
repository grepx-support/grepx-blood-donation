/*
 * Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
 * This file is part of LifeFlow Blood Camp and is proprietary and confidential.
 * Unauthorised copying, modification or distribution is strictly prohibited.
 */

document.addEventListener('alpine:init', () => Alpine.data('carousel', () => ({
  init() {
    new Swiper(this.$refs.swiper, {
      slidesPerView: 1.08, spaceBetween: 20, grabCursor: true,
      autoplay: { delay: 5000, disableOnInteraction: false, pauseOnMouseEnter: true },
      pagination: { el: this.$refs.dots, clickable: true },
      navigation: { nextEl: this.$refs.next, prevEl: this.$refs.prev },
      breakpoints: { 768: { slidesPerView: 2.1 }, 1200: { slidesPerView: 3 } },
    });
  },
})));
