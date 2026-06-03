(function() {
  'use strict';

  if (window.dawCounterAnimationLoaded) return;
  window.dawCounterAnimationLoaded = true;

  function isInViewport(el) {
    var rect = el.getBoundingClientRect();
    var threshold = window.innerHeight * 0.85;
    return rect.top < threshold && rect.bottom > 0;
  }

  var NUMBERS_CACHED = false;
  var NUMBER_CACHE = [];

  function cacheNumbers() {
    if (NUMBERS_CACHED) return;
    var items = document.querySelectorAll('.daw-counter-item');
    items.forEach(function(item) {
      var numberModule = item.querySelector('.et_pb_number_counter');
      if (!numberModule) return;
      var percentEl = numberModule.querySelector('.percent p');
      if (!percentEl) return;
      var raw = percentEl.textContent.trim();
      var isPercent = raw.indexOf('%') !== -1;
      var target = parseFloat(raw.replace(/[^0-9.]/g, ''));
      if (isNaN(target)) return;
      NUMBER_CACHE.push({ el: percentEl, target: target, isPercent: isPercent, counted: false });
    });
    NUMBERS_CACHED = true;
  }

  function animateCounter(cacheEntry) {
    if (cacheEntry.counted) return;
    cacheEntry.counted = true;

    var duration = 2000;
    var target = cacheEntry.target;
    var isPercent = cacheEntry.isPercent;
    var startTime = null;

    function step(timestamp) {
      if (!startTime) startTime = timestamp;
      var progress = Math.min((timestamp - startTime) / duration, 1);
      var eased = 1 - Math.pow(1 - progress, 3);
      var current = Math.round(eased * target);
      cacheEntry.el.textContent = current + (isPercent ? '%' : '');
      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        cacheEntry.el.textContent = target + (isPercent ? '%' : '');
      }
    }
    requestAnimationFrame(step);
  }

  function scanAndAnimate() {
    cacheNumbers();
    NUMBER_CACHE.forEach(function(entry) {
      if (entry.counted) return;
      var parent = entry.el.closest('.daw-counter-item');
      if (parent && isInViewport(parent)) {
        animateCounter(entry);
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      setTimeout(scanAndAnimate, 500);
    });
  } else {
    setTimeout(scanAndAnimate, 500);
  }

  var ticking = false;
  window.addEventListener('scroll', function() {
    if (!ticking) {
      requestAnimationFrame(function() {
        scanAndAnimate();
        ticking = false;
      });
      ticking = true;
    }
  });
})();