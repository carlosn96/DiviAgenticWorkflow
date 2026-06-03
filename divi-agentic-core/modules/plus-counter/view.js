(function () {
  'use strict';

  function animateCounters() {
    var counters = document.querySelectorAll('.daw-pc-number[data-target]');
    if (!counters.length) return;

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var el = entry.target;
          if (el.dataset.animated) return;
          el.dataset.animated = '1';

          var target = parseFloat(el.dataset.target) || 0;
          var suffix = el.dataset.suffix || '';
          var isPercent = el.dataset.percent === 'on';
          var display = el.querySelector('.daw-pc-number-value');
          if (!display) return;

          var duration = 2000;
          var start = 0;
          var startTime = null;

          function step(timestamp) {
            if (!startTime) startTime = timestamp;
            var progress = Math.min((timestamp - startTime) / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 3);
            var current = start + (target - start) * eased;

            if (Number.isInteger(target)) {
              display.textContent = Math.round(current) + suffix + (isPercent ? '%' : '');
            } else {
              display.textContent = current.toFixed(1) + suffix + (isPercent ? '%' : '');
            }

            if (progress < 1) {
              requestAnimationFrame(step);
            } else {
              if (Number.isInteger(target)) {
                display.textContent = target + suffix + (isPercent ? '%' : '');
              } else {
                display.textContent = target.toFixed(1) + suffix + (isPercent ? '%' : '');
              }
            }
          }

          requestAnimationFrame(step);
          observer.unobserve(el);
        });
      },
      { threshold: 0.3 }
    );

    counters.forEach(function (el) {
      observer.observe(el);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', animateCounters);
  } else {
    animateCounters();
  }
})();