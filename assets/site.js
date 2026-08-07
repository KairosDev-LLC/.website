/* ==========================================================================
   Kairos — shared site behaviour
   No dependencies, no build step. Every component is progressive
   enhancement: if this file fails to load, the pages still read and
   navigate correctly.
   ========================================================================== */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  }

  /* ----------------------------------------------------------------------
     1. Scroll reveal
     ---------------------------------------------------------------------- */
  function initReveal() {
    var els = $$('.reveal');
    if (!els.length) return;

    if (!('IntersectionObserver' in window)) {
      els.forEach(function (el) { el.classList.add('revealed'); });
      return;
    }
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed');
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });
    els.forEach(function (el) { obs.observe(el); });
  }

  /* ----------------------------------------------------------------------
     2. Scroll progress bar
     ---------------------------------------------------------------------- */
  function initScrollProgress() {
    var bar = $('#scroll-progress');
    if (!bar) return;
    var ticking = false;

    function update() {
      var doc = document.documentElement;
      var max = doc.scrollHeight - doc.clientHeight;
      var pct = max > 0 ? Math.min(1, Math.max(0, doc.scrollTop / max)) : 0;
      bar.style.transform = 'scaleX(' + pct + ')';
      ticking = false;
    }
    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; window.requestAnimationFrame(update); }
    }, { passive: true });
    update();
  }

  /* ----------------------------------------------------------------------
     3. Back-to-top button
     ---------------------------------------------------------------------- */
  function initToTop() {
    var btn = $('#to-top');
    if (!btn) return;
    var ticking = false;

    function update() {
      btn.classList.toggle('show', window.scrollY > 600);
      ticking = false;
    }
    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; window.requestAnimationFrame(update); }
    }, { passive: true });
    btn.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
    });
    update();
  }

  /* ----------------------------------------------------------------------
     4. Mobile nav toggle
     ---------------------------------------------------------------------- */
  function initNav() {
    var toggle = $('.nav-toggle');
    var links = $('#nav-links');
    if (!toggle || !links) return;

    toggle.hidden = false;
    toggle.addEventListener('click', function () {
      var open = links.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      toggle.textContent = open ? 'Close' : 'Menu';
    });
    // Collapse after choosing a destination on small screens.
    links.addEventListener('click', function (e) {
      if (e.target.tagName === 'A' && links.classList.contains('open')) {
        links.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
        toggle.textContent = 'Menu';
      }
    });
  }

  /* ----------------------------------------------------------------------
     5. Tabs — [data-tabs] with role=tab buttons and role=tabpanel panels.
        Supports arrow-key roving focus and deep links via #hash.
     ---------------------------------------------------------------------- */
  function initTabs() {
    $$('[data-tabs]').forEach(function (group) {
      var btns = $$('[role="tab"]', group);
      if (!btns.length) return;

      function select(btn, focus) {
        btns.forEach(function (b) {
          var on = b === btn;
          b.setAttribute('aria-selected', on ? 'true' : 'false');
          b.tabIndex = on ? 0 : -1;
          var panel = document.getElementById(b.getAttribute('aria-controls'));
          if (panel) panel.hidden = !on;
        });
        if (focus) btn.focus();
      }

      btns.forEach(function (btn, i) {
        btn.addEventListener('click', function () { select(btn); });
        btn.addEventListener('keydown', function (e) {
          var next = null;
          if (e.key === 'ArrowRight' || e.key === 'ArrowDown') next = btns[(i + 1) % btns.length];
          else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') next = btns[(i - 1 + btns.length) % btns.length];
          else if (e.key === 'Home') next = btns[0];
          else if (e.key === 'End') next = btns[btns.length - 1];
          if (next) { e.preventDefault(); select(next, true); }
        });
      });

      // Honour a #panel-id deep link, else keep the authored default.
      var hash = window.location.hash.slice(1);
      var target = hash && btns.filter(function (b) {
        return b.getAttribute('aria-controls') === hash || b.id === hash;
      })[0];
      select(target || btns.filter(function (b) {
        return b.getAttribute('aria-selected') === 'true';
      })[0] || btns[0]);
    });
  }

  /* ----------------------------------------------------------------------
     6. FAQ filter — live-filters <details> items by question + answer text.
     ---------------------------------------------------------------------- */
  function initFaqSearch() {
    var input = $('#faq-search');
    var list = $('#faq-list');
    if (!input || !list) return;

    var empty = $('#faq-empty');
    var items = $$('.faq-item', list);
    input.hidden = false;

    input.addEventListener('input', function () {
      var q = input.value.trim().toLowerCase();
      var shown = 0;
      items.forEach(function (item) {
        var hit = !q || item.textContent.toLowerCase().indexOf(q) !== -1;
        item.hidden = !hit;
        if (hit) shown++;
        // Auto-open the matches so the answer is visible while filtering.
        if (q && hit) item.open = true;
        if (!q) item.open = false;
      });
      if (empty) empty.hidden = shown !== 0;
    });
  }

  /* ----------------------------------------------------------------------
     7. Pricing billing-period toggle
     ---------------------------------------------------------------------- */
  function initBillingToggle() {
    var toggle = $('#billing-toggle');
    if (!toggle) return;
    var btns = $$('button', toggle);

    function apply(period) {
      btns.forEach(function (b) {
        b.setAttribute('aria-pressed', b.dataset.period === period ? 'true' : 'false');
      });
      $$('[data-price-monthly]').forEach(function (el) {
        el.textContent = period === 'yearly' ? el.dataset.priceYearly : el.dataset.priceMonthly;
      });
      $$('[data-per-monthly]').forEach(function (el) {
        el.textContent = period === 'yearly' ? el.dataset.perYearly : el.dataset.perMonthly;
      });
      $$('[data-note-monthly]').forEach(function (el) {
        el.textContent = period === 'yearly' ? el.dataset.noteYearly : el.dataset.noteMonthly;
      });
    }
    btns.forEach(function (b) {
      b.addEventListener('click', function () { apply(b.dataset.period); });
    });
    apply('monthly');
  }

  /* ----------------------------------------------------------------------
     8. Access-code demo — rolls a fake 6-character share code, matching the
        app's own "send a 6-character code" sharing flow.
     ---------------------------------------------------------------------- */
  function initCodeDemo() {
    var box = $('#code-box');
    var roll = $('#code-roll');
    var copy = $('#code-copy');
    var status = $('#code-status');
    if (!box) return;

    // Unambiguous alphabet: no O/0, no I/1.
    var ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';

    function make() {
      var out = '';
      var rnd = new Uint32Array(6);
      if (window.crypto && window.crypto.getRandomValues) {
        window.crypto.getRandomValues(rnd);
        for (var i = 0; i < 6; i++) out += ALPHABET[rnd[i] % ALPHABET.length];
      } else {
        for (var j = 0; j < 6; j++) {
          out += ALPHABET[Math.floor(Math.random() * ALPHABET.length)];
        }
      }
      return out;
    }

    function setCode(code) { box.textContent = code; }

    if (roll) {
      roll.hidden = false;
      roll.addEventListener('click', function () {
        if (reduceMotion) {
          setCode(make());
          if (status) status.textContent = 'New sample code generated.';
          return;
        }
        // Brief scramble so the roll reads as an action.
        var ticks = 0;
        var timer = setInterval(function () {
          setCode(make());
          if (++ticks >= 8) {
            clearInterval(timer);
            setCode(make());
            if (status) status.textContent = 'New sample code generated.';
          }
        }, 45);
      });
    }

    if (copy && navigator.clipboard) {
      copy.hidden = false;
      copy.addEventListener('click', function () {
        navigator.clipboard.writeText(box.textContent.trim()).then(function () {
          if (status) status.textContent = 'Copied. In the app, this is what you text your family.';
        }, function () {
          if (status) status.textContent = 'Select the code to copy it.';
        });
      });
    }

    setCode(make());
  }

  /* ----------------------------------------------------------------------
     9. Screenshot lightbox
     ---------------------------------------------------------------------- */
  function initLightbox() {
    var shots = $$('.shot');
    var box = $('#lightbox');
    if (!shots.length || !box) return;

    var img = $('#lightbox-img');
    var cap = $('#lightbox-cap');
    var idx = 0;
    var lastFocus = null;

    function show(i) {
      idx = (i + shots.length) % shots.length;
      var src = shots[idx].dataset.full || $('img', shots[idx]).src;
      var alt = shots[idx].dataset.caption || $('img', shots[idx]).alt;
      img.src = src;
      img.alt = alt;
      if (cap) cap.textContent = alt + '  (' + (idx + 1) + ' / ' + shots.length + ')';
    }
    function open(i) {
      lastFocus = document.activeElement;
      show(i);
      box.hidden = false;
      document.body.style.overflow = 'hidden';
      $('#lightbox-close').focus();
    }
    function close() {
      box.hidden = true;
      document.body.style.overflow = '';
      if (lastFocus) lastFocus.focus();
    }

    shots.forEach(function (s, i) {
      s.addEventListener('click', function () { open(i); });
    });
    $('#lightbox-close').addEventListener('click', close);
    $('#lightbox-prev').addEventListener('click', function () { show(idx - 1); });
    $('#lightbox-next').addEventListener('click', function () { show(idx + 1); });
    box.addEventListener('click', function (e) { if (e.target === box) close(); });
    document.addEventListener('keydown', function (e) {
      if (box.hidden) return;
      if (e.key === 'Escape') close();
      else if (e.key === 'ArrowLeft') show(idx - 1);
      else if (e.key === 'ArrowRight') show(idx + 1);
    });
  }

  /* ----------------------------------------------------------------------
     10. Rotation simulator
         Renders a real month calendar for a chosen rotation pattern and a
         chosen cycle start date, plus a live duty status and countdown.

         Patterns use one character per day:
           D = day shift on duty, N = night shift on duty, . = off duty
         These are the schedules named in the App Store listing plus the
         common variants they belong to.
     ---------------------------------------------------------------------- */
  var PATTERNS = {
    '24-48': {
      name: '24/48',
      pattern: 'D..',
      shiftHours: 24,
      startHour: 8,
      blurb: 'One 24-hour shift, then 48 hours off. A 3-day cycle and the most common single-platoon fire schedule.'
    },
    '48-96': {
      name: '48/96',
      pattern: 'DD....',
      shiftHours: 24,
      startHour: 8,
      blurb: 'Two 24-hour shifts back to back, then four days off. A 6-day cycle that keeps every set of days off together, averaging 56 hours a week.'
    },
    'kelly': {
      name: 'Kelly',
      pattern: 'D.D.D....',
      shiftHours: 24,
      startHour: 8,
      blurb: 'Three 24-hour shifts on alternating days, then four consecutive days off. A 9-day cycle averaging 56 hours a week.'
    },
    'panama': {
      name: 'Panama (2-2-3)',
      pattern: 'DD..DDD..DD...',
      shiftHours: 12,
      startHour: 6,
      blurb: 'The 2-2-3: two on, two off, three on. A 14-day cycle giving every other weekend off in full.'
    },
    'dupont': {
      name: 'DuPont',
      pattern: 'NNNN...DDD.NNN...DDDD.......',
      shiftHours: 12,
      startHour: 18,
      blurb: 'A 28-day cycle rotating nights and days, with a full seven-day break at the end of every rotation. Averages 42 hours a week.'
    },
    'pitman': {
      name: 'Pitman nights (2-3-2)',
      pattern: 'NN..NNN..NN...',
      shiftHours: 12,
      startHour: 18,
      blurb: 'The same 14-day 2-3-2 structure as the Panama, worked on nights. Every other weekend comes off in full, at 42 hours a week.'
    },
    '4-on-4-off': {
      name: '4 on / 4 off',
      pattern: 'DDDD....',
      shiftHours: 12,
      startHour: 7,
      blurb: 'Four 12-hour shifts, then four days off. An 8-day cycle common on industrial and transportation crews.'
    },
    '5-2': {
      name: '5 on / 2 off',
      pattern: 'DDDDD..',
      shiftHours: 8,
      startHour: 7,
      blurb: 'The classic weekday rotation, included so you can compare a fixed week against a true rotating cycle.'
    }
  };

  var DOW = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
    'August', 'September', 'October', 'November', 'December'];

  function ymd(d) {
    return d.getFullYear() + '-' +
      String(d.getMonth() + 1).padStart(2, '0') + '-' +
      String(d.getDate()).padStart(2, '0');
  }
  function parseYmd(s) {
    var p = String(s).split('-');
    return new Date(Number(p[0]), Number(p[1]) - 1, Number(p[2]));
  }
  function dayIndex(d) {
    // Whole days since epoch in local time, so DST shifts never move a day.
    return Math.floor(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / 86400000);
  }

  function initSimulator() {
    var root = $('#sim');
    if (!root) return;

    var selPattern = $('#sim-pattern');
    var inpStart = $('#sim-start');
    var grid = $('#sim-grid');
    var monthLabel = $('#sim-month');
    var blurb = $('#sim-blurb');
    var ring = $('#sim-ring');
    var ringPct = $('#sim-ring-pct');
    var statusValue = $('#sim-status-value');
    var countdown = $('#sim-countdown');
    var strip = $('#sim-cycle-strip');
    var sumOn = $('#sim-sum-on');
    var sumOff = $('#sim-sum-off');
    var sumHours = $('#sim-sum-hours');
    var sumCycle = $('#sim-sum-cycle');

    var today = new Date();
    var view = new Date(today.getFullYear(), today.getMonth(), 1);
    var anchorDay;

    root.hidden = false;
    var fallback = $('#sim-fallback');
    if (fallback) fallback.hidden = true;

    // Default the cycle start to the first of the current month.
    if (inpStart && !inpStart.value) inpStart.value = ymd(view);

    function current() { return PATTERNS[selPattern.value] || PATTERNS['24-48']; }

    // What does the pattern say about this specific date?
    function stateFor(date, p) {
      var offset = ((dayIndex(date) - anchorDay) % p.pattern.length + p.pattern.length) % p.pattern.length;
      return p.pattern[offset];
    }

    function renderCalendar(p) {
      var y = view.getFullYear();
      var m = view.getMonth();
      monthLabel.textContent = MONTHS[m] + ' ' + y;

      var html = DOW.map(function (d) {
        return '<div class="cal-dow" aria-hidden="true">' + d + '</div>';
      }).join('');

      var first = new Date(y, m, 1);
      var daysInMonth = new Date(y, m + 1, 0).getDate();
      for (var b = 0; b < first.getDay(); b++) {
        html += '<div class="cal-day is-empty" aria-hidden="true"></div>';
      }
      for (var d = 1; d <= daysInMonth; d++) {
        var date = new Date(y, m, d);
        var st = stateFor(date, p);
        var cls = st === 'D' ? 'on' : (st === 'N' ? 'night' : '');
        var word = st === 'D' ? 'On duty' : (st === 'N' ? 'Night shift' : 'Off duty');
        var isToday = ymd(date) === ymd(today);
        html += '<div class="cal-day ' + cls + (isToday ? ' today' : '') +
          '" title="' + DOW[date.getDay()] + ' ' + MONTHS[m] + ' ' + d + ' — ' + word + '">' +
          '<span class="cal-num">' + d + '</span>' +
          '<span class="cal-mark">' + (st === 'D' ? 'Day' : st === 'N' ? 'Night' : '') + '</span>' +
          '<span class="visually-hidden">' + word + '</span>' +
          '</div>';
      }
      grid.innerHTML = html;
    }

    function renderStrip(p) {
      strip.innerHTML = p.pattern.split('').map(function (ch) {
        var cls = ch === 'D' ? 'on' : (ch === 'N' ? 'night' : '');
        var word = ch === 'D' ? 'day shift' : (ch === 'N' ? 'night shift' : 'off');
        return '<i class="' + cls + '" title="Day ' + word + '"></i>';
      }).join('');
    }

    function renderSummary(p) {
      var on = 0;
      for (var i = 0; i < p.pattern.length; i++) {
        if (p.pattern[i] !== '.') on++;
      }
      var weeks = p.pattern.length / 7;
      var hoursPerWeek = (on * p.shiftHours) / weeks;

      sumOn.textContent = on;
      sumOff.textContent = p.pattern.length - on;
      sumHours.textContent = hoursPerWeek.toFixed(1);
      sumCycle.textContent = p.pattern.length;
    }

    function renderStatus(p) {
      var now = new Date();
      var st = stateFor(now, p);
      var onDuty = st !== '.';

      // Shift boundaries for the current day of the pattern.
      var shiftStart = new Date(now.getFullYear(), now.getMonth(), now.getDate(), p.startHour, 0, 0);
      if (now < shiftStart) shiftStart.setDate(shiftStart.getDate() - 1);
      var shiftEnd = new Date(shiftStart.getTime() + p.shiftHours * 3600000);

      if (onDuty) {
        var total = shiftEnd - shiftStart;
        var pct = Math.min(100, Math.max(0, ((now - shiftStart) / total) * 100));
        ring.style.setProperty('--pct', pct.toFixed(1));
        ringPct.textContent = Math.round(pct) + '%';
        statusValue.textContent = st === 'N' ? 'Night shift' : 'On duty';
        countdown.innerHTML = 'Shift ends in <strong>' + humanGap(shiftEnd - now) + '</strong>';
      } else {
        // Walk forward to the next working day in the pattern.
        var probe = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        var guard = 0;
        do {
          probe.setDate(probe.getDate() + 1);
        } while (stateFor(probe, p) === '.' && ++guard < 400);

        var nextStart = new Date(probe.getFullYear(), probe.getMonth(), probe.getDate(), p.startHour, 0, 0);
        ring.style.setProperty('--pct', '0');
        ringPct.textContent = 'Off';
        statusValue.textContent = 'Off duty';
        countdown.innerHTML = 'Next shift starts in <strong>' + humanGap(nextStart - now) + '</strong>';
      }
    }

    function humanGap(ms) {
      var s = Math.max(0, Math.floor(ms / 1000));
      var d = Math.floor(s / 86400); s -= d * 86400;
      var h = Math.floor(s / 3600); s -= h * 3600;
      var m = Math.floor(s / 60); s -= m * 60;
      if (d) return d + 'd ' + h + 'h ' + m + 'm';
      if (h) return h + 'h ' + m + 'm ' + s + 's';
      return m + 'm ' + s + 's';
    }

    function renderAll() {
      var p = current();
      anchorDay = dayIndex(parseYmd(inpStart.value || ymd(view)));
      blurb.textContent = p.blurb;
      renderCalendar(p);
      renderStrip(p);
      renderSummary(p);
      renderStatus(p);
    }

    selPattern.addEventListener('change', renderAll);
    inpStart.addEventListener('change', renderAll);
    $('#sim-prev').addEventListener('click', function () {
      view.setMonth(view.getMonth() - 1);
      renderCalendar(current());
    });
    $('#sim-next').addEventListener('click', function () {
      view.setMonth(view.getMonth() + 1);
      renderCalendar(current());
    });
    $('#sim-today').addEventListener('click', function () {
      view = new Date(today.getFullYear(), today.getMonth(), 1);
      renderCalendar(current());
    });

    renderAll();
    // Live countdown, same as the app's own countdown badge.
    setInterval(function () { renderStatus(current()); }, 1000);
  }

  /* ----------------------------------------------------------------------
     11. Count-up numbers on the stat cells
     ---------------------------------------------------------------------- */
  function initCountUp() {
    var els = $$('[data-count-to]');
    if (!els.length || !('IntersectionObserver' in window)) return;

    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        obs.unobserve(entry.target);
        var el = entry.target;
        var target = parseFloat(el.dataset.countTo);
        var suffix = el.dataset.countSuffix || '';
        if (reduceMotion) { el.textContent = target + suffix; return; }

        var start = performance.now();
        var dur = 900;
        (function step(now) {
          var t = Math.min(1, (now - start) / dur);
          // easeOutCubic
          var eased = 1 - Math.pow(1 - t, 3);
          el.textContent = Math.round(target * eased) + suffix;
          if (t < 1) requestAnimationFrame(step);
        })(start);
      });
    }, { threshold: 0.4 });
    els.forEach(function (el) { obs.observe(el); });
  }

  /* ----------------------------------------------------------------------
     12. Mark the active nav link from the current path
     ---------------------------------------------------------------------- */
  function initActiveNav() {
    var path = window.location.pathname.replace(/\/index\.html$/, '/').replace(/\.html$/, '');
    if (path === '') path = '/';
    $$('a.navlink, .foot-col a').forEach(function (a) {
      var href = a.getAttribute('href') || '';
      if (href.charAt(0) === '#' || href.indexOf(':') !== -1) return;
      var target = ('/' + href).replace(/\/+/g, '/').replace(/\.html$/, '').replace(/\/index$/, '/');
      if (target === path && a.classList.contains('navlink')) {
        a.setAttribute('aria-current', 'page');
      }
    });
  }

  /* ---------------------------------------------------------------------- */
  function boot() {
    initActiveNav();
    initNav();
    initReveal();
    initScrollProgress();
    initToTop();
    initTabs();
    initFaqSearch();
    initBillingToggle();
    initCodeDemo();
    initLightbox();
    initSimulator();
    initCountUp();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
