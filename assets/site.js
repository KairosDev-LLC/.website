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

    function showAll() {
      els.forEach(function (el) { el.classList.add('revealed'); });
    }

    // Respect reduced motion, and bail out to plain visible content if the
    // browser lacks IntersectionObserver.
    var reduced = window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced || !('IntersectionObserver' in window)) {
      showAll();
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

    // Failsafe: content must never be permanently invisible. If the observer
    // never fired for anything that is plainly on screen, treat it as broken
    // (headless capture, exotic browser, viewport resized after load) and
    // drop reveal entirely rather than leaving the page blank.
    function rescue() {
      var onscreen = els.filter(function (el) {
        var r = el.getBoundingClientRect();
        return r.top < window.innerHeight && r.bottom > 0;
      });
      var shown = onscreen.filter(function (el) {
        return el.classList.contains('revealed');
      });
      if (onscreen.length && !shown.length) {
        document.documentElement.classList.add('reveal-off');
        showAll();
      }
    }
    window.addEventListener('load', function () { setTimeout(rescue, 800); });
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

      // Honour a deep link. Accept the natural short form (#sharing) as well
      // as the explicit #panel-sharing / #tab-sharing forms, and keep
      // responding to later hash changes so back/forward works.
      function btnForHash(hash) {
        if (!hash) return null;
        return btns.filter(function (b) {
          var ctrl = b.getAttribute('aria-controls') || '';
          return ctrl === hash ||
                 b.id === hash ||
                 ctrl.replace(/^panel-/, '') === hash ||
                 b.id.replace(/^tab-/, '') === hash;
        })[0] || null;
      }

      function applyHash(focus) {
        var btn = btnForHash(window.location.hash.slice(1));
        if (btn) select(btn, focus);
      }

      select(btnForHash(window.location.hash.slice(1)) ||
        btns.filter(function (b) {
          return b.getAttribute('aria-selected') === 'true';
        })[0] || btns[0]);

      window.addEventListener('hashchange', function () { applyHash(false); });
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


/* ==========================================================================
   Gallery layer — theme switch, nav menus, ⌘K search, chip filter + pager
   Everything here is progressive enhancement. Without JavaScript the page
   still shows every card, every nav destination and a working footer.
   ========================================================================== */
(function () {
  'use strict';

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  }

  /* ---------- 1. Light / dark switch ---------- */
  function initTheme() {
    var btn = $('#theme-toggle');
    if (!btn) return;
    function apply(mode) {
      document.documentElement.setAttribute('data-theme', mode);
      btn.setAttribute('aria-label', mode === 'light'
        ? 'Switch to dark mode' : 'Switch to light mode');
      var meta = document.querySelector('meta[name="theme-color"]');
      if (meta) meta.setAttribute('content', mode === 'light' ? '#ffffff' : '#0a0a0b');
    }
    btn.addEventListener('click', function () {
      var next = document.documentElement.getAttribute('data-theme') === 'light'
        ? 'dark' : 'light';
      apply(next);
      try { localStorage.setItem('kairos-theme', next); } catch (e) {}
    });
    apply(document.documentElement.getAttribute('data-theme') || 'dark');
  }

  /* ---------- 2. Nav dropdown panels ---------- */
  function initNavMenus() {
    var menus = $$('.nav-menu');
    if (!menus.length) return;

    function close(menu) {
      menu.setAttribute('data-open', 'false');
      var b = menu.querySelector('button');
      if (b) b.setAttribute('aria-expanded', 'false');
    }
    function open(menu) {
      menus.forEach(close);
      menu.setAttribute('data-open', 'true');
      var b = menu.querySelector('button');
      if (b) b.setAttribute('aria-expanded', 'true');
    }

    menus.forEach(function (menu) {
      var btn = menu.querySelector('button');
      if (!btn) return;
      btn.addEventListener('click', function (e) {
        e.stopPropagation();
        if (menu.getAttribute('data-open') === 'true') { close(menu); } else { open(menu); }
      });
      menu.addEventListener('mouseenter', function () { open(menu); });
      menu.addEventListener('mouseleave', function () { close(menu); });
    });

    document.addEventListener('click', function () { menus.forEach(close); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') menus.forEach(close);
    });
  }

  /* ---------- 3. Command-K search ---------- */
  var SEARCH_INDEX = [
    { t: '24/48', u: '/rotations#24-48', d: 'One 24-hour shift, then 48 hours off. 56 hrs/wk.' },
    { t: '48/96', u: '/rotations#48-96', d: 'Two 24-hour shifts, then four days off. 56 hrs/wk.' },
    { t: 'Kelly', u: '/rotations#kelly', d: 'Three 24-hour shifts on alternating days, then four off.' },
    { t: 'Panama (2-2-3)', u: '/rotations#panama', d: 'Two on, two off, three on, 12-hour shifts. 42 hrs/wk.' },
    { t: 'Pitman nights (2-3-2)', u: '/rotations#pitman', d: 'The 2-3-2 worked on nights. 42 hrs/wk.' },
    { t: 'DuPont', u: '/rotations#dupont', d: 'Rotating nights and days with a seven-day break.' },
    { t: '4 on / 4 off', u: '/rotations#4-on-4-off', d: 'Four 12-hour shifts, then four days off.' },
    { t: '5 on / 2 off', u: '/rotations#5-2', d: 'The fixed weekday baseline. 40 hrs/wk.' },
    { t: 'Rotation simulator', u: '/rotations#simulator', d: 'Draw any rotation onto a live calendar in your browser.' },
    { t: 'Features', u: '/features', d: 'Live duty status, sharing, widgets, watch app and calendar.' },
    { t: 'Shared schedules', u: '/features#sharing', d: 'Share your rotation with a 6-character access code.' },
    { t: 'Home Screen widgets', u: '/features#widgets', d: 'Small, medium and large widgets on iOS.' },
    { t: 'Pricing', u: '/pricing', d: 'Free to download. Kairos Pro from $4.99 a month.' },
    { t: 'Changelog', u: '/changelog', d: 'What shipped, and when.' },
    { t: 'FAQ', u: '/faq', d: 'Answers about rotations, sync, sharing and billing.' },
    { t: 'Support', u: '/support', d: 'Get help from the people who build Kairos.' },
    { t: 'Privacy policy', u: '/privacy', d: 'On-device storage, CloudKit sync, no accounts.' }
  ];

  function initSearch() {
    var overlay = $('#search-overlay');
    var input = $('#search-input');
    var list = $('#search-results');
    var opener = $('#search-open');
    if (!overlay || !input || !list) return;
    var active = 0;

    function render(q) {
      var terms = q.toLowerCase().trim();
      var hits = SEARCH_INDEX.filter(function (item) {
        if (!terms) return true;
        return (item.t + ' ' + item.d).toLowerCase().indexOf(terms) !== -1;
      }).slice(0, 8);
      active = 0;
      if (!hits.length) {
        list.innerHTML = '<li class="search-empty">No matches. Try “Kelly”, “widgets” or “sharing”.</li>';
        return;
      }
      list.innerHTML = hits.map(function (h, i) {
        return '<li class="' + (i === 0 ? 'is-active' : '') + '"><a href="' + h.u + '">' +
          h.t + '<small>' + h.d + '</small></a></li>';
      }).join('');
    }

    function show() {
      overlay.hidden = false;
      render('');
      input.value = '';
      input.focus();
    }
    function hide() { overlay.hidden = true; }

    if (opener) opener.addEventListener('click', show);
    overlay.addEventListener('click', function (e) { if (e.target === overlay) hide(); });
    input.addEventListener('input', function () { render(input.value); });

    document.addEventListener('keydown', function (e) {
      var key = (e.key || '').toLowerCase();
      if (key === 'k' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); show(); return; }
      if (overlay.hidden) return;
      var items = $$('li', list).filter(function (li) { return li.querySelector('a'); });
      if (e.key === 'Escape') { hide(); }
      else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        if (!items.length) return;
        active = (active + (e.key === 'ArrowDown' ? 1 : items.length - 1)) % items.length;
        items.forEach(function (li, i) { li.classList.toggle('is-active', i === active); });
      } else if (e.key === 'Enter') {
        var current = items[active];
        if (current) { window.location.href = current.querySelector('a').getAttribute('href'); }
      }
    });
  }

  /* ---------- 4. Chip filter + pagination ---------- */
  function initGallery() {
    var grid = $('#gallery-grid');
    var row = $('#chip-row');
    var pager = $('#pager');
    var empty = $('#gallery-empty');
    if (!grid || !row) return;

    var cards = $$('.g-card', grid);
    var perPage = parseInt(grid.getAttribute('data-per-page'), 10) || 8;
    var filter = 'all';
    var page = 1;

    function matches(card) {
      if (filter === 'all') return true;
      return (' ' + card.getAttribute('data-cats') + ' ').indexOf(' ' + filter + ' ') !== -1;
    }

    function draw() {
      var visible = cards.filter(matches);
      var pages = Math.max(1, Math.ceil(visible.length / perPage));
      if (page > pages) page = pages;
      var start = (page - 1) * perPage;

      cards.forEach(function (card) { card.hidden = true; });
      visible.slice(start, start + perPage).forEach(function (card) {
        card.hidden = false;
        card.classList.add('revealed');
      });
      if (empty) empty.hidden = visible.length !== 0;

      if (pager) {
        $$('button[data-page]', pager).forEach(function (b) {
          var n = parseInt(b.getAttribute('data-page'), 10);
          b.hidden = n > pages;
          b.setAttribute('aria-current', n === page ? 'true' : 'false');
        });
        var first = $('button[data-nav="first"]', pager);
        var prev = $('button[data-nav="prev"]', pager);
        var next = $('button[data-nav="next"]', pager);
        var last = $('button[data-nav="last"]', pager);
        if (first) first.disabled = page === 1;
        if (prev) prev.disabled = page === 1;
        if (next) next.disabled = page === pages;
        if (last) last.disabled = page === pages;
        pager.hidden = pages < 2;
      }
    }

    row.addEventListener('click', function (e) {
      var chip = e.target.closest ? e.target.closest('.chip') : null;
      if (!chip) return;
      filter = chip.getAttribute('data-filter');
      page = 1;
      $$('.chip', row).forEach(function (c) {
        c.setAttribute('aria-pressed', c === chip ? 'true' : 'false');
      });
      draw();
    });

    if (pager) {
      pager.addEventListener('click', function (e) {
        var btn = e.target.closest ? e.target.closest('button') : null;
        if (!btn || btn.disabled) return;
        var visible = cards.filter(matches);
        var pages = Math.max(1, Math.ceil(visible.length / perPage));
        var nav = btn.getAttribute('data-nav');
        if (nav === 'first') page = 1;
        else if (nav === 'prev') page = Math.max(1, page - 1);
        else if (nav === 'next') page = Math.min(pages, page + 1);
        else if (nav === 'last') page = pages;
        else if (btn.getAttribute('data-page')) page = parseInt(btn.getAttribute('data-page'), 10);
        draw();
        var head = document.querySelector('.chip-row');
        if (head) head.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    }

    // Deep link: /?filter=fire selects a chip on load, so shared links land
    // on the same view the sender was looking at.
    var q = (window.location.search.match(/[?&]filter=([a-z0-9-]+)/i) || [])[1];
    if (q) {
      var target = $('.chip[data-filter="' + q + '"]', row);
      if (target) {
        filter = q;
        $$('.chip', row).forEach(function (c) {
          c.setAttribute('aria-pressed', c === target ? 'true' : 'false');
        });
      }
    }
    draw();
  }

  /* ---------- 5. "See more" filters ---------- */
  function initChipMore() {
    var btn = $('#chip-more');
    var row = $('#chip-row');
    if (!btn || !row) return;
    btn.addEventListener('click', function () {
      var open = row.classList.toggle('is-expanded');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      btn.textContent = open ? 'See less' : 'See more';
    });
  }

  function boot() {
    initTheme();
    initNavMenus();
    initSearch();
    initGallery();
    initChipMore();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
}());


/* ==========================================================================
   3D layer — pointer/scroll driven depth
   No WebGL, no libraries. If any of this fails the page is still a flat,
   readable document, which is why every effect is applied to existing
   markup rather than generating the content it decorates.
   ========================================================================== */
(function () {
  'use strict';

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  }

  var reduced = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var coarse = window.matchMedia &&
    window.matchMedia('(pointer: coarse)').matches;

  function clamp(v, lo, hi) { return v < lo ? lo : (v > hi ? hi : v); }

  /* ---------- 1. Hero deck ----------
     The deck answers to the pointer on desktop and to the device tilt or
     scroll position elsewhere, so it is never a dead prop. */
  function initDeck() {
    var stage = $('#stage3d');
    var deck = $('#deck');
    if (!stage || !deck || reduced) return;

    var baseX = 12, baseY = -16;
    var targetX = baseX, targetY = baseY;
    var curX = baseX, curY = baseY;
    var raf = null;

    function frame() {
      curX += (targetX - curX) * 0.12;
      curY += (targetY - curY) * 0.12;
      deck.style.setProperty('--rx', curX.toFixed(2) + 'deg');
      deck.style.setProperty('--ry', curY.toFixed(2) + 'deg');
      if (Math.abs(targetX - curX) > 0.05 || Math.abs(targetY - curY) > 0.05) {
        raf = window.requestAnimationFrame(frame);
      } else {
        raf = null;
      }
    }
    function kick() { if (!raf) raf = window.requestAnimationFrame(frame); }

    if (!coarse) {
      window.addEventListener('pointermove', function (e) {
        var r = stage.getBoundingClientRect();
        var cx = r.left + r.width / 2;
        var cy = r.top + r.height / 2;
        targetY = clamp(((e.clientX - cx) / r.width) * 34, -26, 26) - 6;
        targetX = clamp(-((e.clientY - cy) / r.height) * 22, -18, 22) + 6;
        kick();
      }, { passive: true });
      stage.addEventListener('pointerleave', function () {
        targetX = baseX; targetY = baseY; kick();
      });
    } else {
      // Touch devices: let the scroll position drive the rotation instead.
      window.addEventListener('scroll', function () {
        var r = stage.getBoundingClientRect();
        var p = clamp(1 - (r.top + r.height) / (window.innerHeight + r.height), 0, 1);
        targetX = baseX - p * 14;
        targetY = baseY + p * 22;
        kick();
      }, { passive: true });
    }

    // The deck is a tab panel: each tab brings its calendar to the front and
    // pushes the rest back in Z. Auto-advance runs until the reader takes
    // over, and stops for good after that.
    var cards = $$('.deck-card', deck);
    var tabs = $$('.deck-tab');
    var front = 0;
    var auto = null;

    function layout() {
      var n = cards.length;
      cards.forEach(function (card, i) {
        var depth = (i - front + n) % n;
        card.style.setProperty('--z', (-depth * 58) + 'px');
        card.style.setProperty('--x', (depth * 26) + 'px');
        card.style.setProperty('--y', (depth * -16) + 'px');
        card.style.setProperty('--s', (1 - depth * 0.045).toFixed(3));
        card.classList.toggle('is-mid', depth === 1);
        card.classList.toggle('is-back', depth > 1);
        card.style.zIndex = String(20 - depth);
      });
      tabs.forEach(function (tab, i) {
        var on = i === front;
        tab.setAttribute('aria-selected', on ? 'true' : 'false');
        tab.tabIndex = on ? 0 : -1;
      });
    }

    function show(i) {
      front = (i + cards.length) % cards.length;
      layout();
    }

    function stopAuto() {
      if (auto) { window.clearInterval(auto); auto = null; }
    }

    tabs.forEach(function (tab, i) {
      tab.addEventListener('click', function () { stopAuto(); show(i); });
      tab.addEventListener('keydown', function (e) {
        var d = e.key === 'ArrowRight' ? 1 : (e.key === 'ArrowLeft' ? -1 : 0);
        if (!d) return;
        e.preventDefault();
        stopAuto();
        show(front + d);
        tabs[front].focus();
      });
    });

    if (cards.length > 1 && !reduced) {
      auto = window.setInterval(function () {
        if (!document.hidden) show(front + 1);
      }, 4200);
      window.addEventListener('pagehide', stopAuto);
      stage.addEventListener('pointerenter', stopAuto);
    }
    layout();

    kick();
  }

  /* ---------- 2. Card tilt ---------- */
  function initTilt() {
    if (reduced || coarse) return;
    var cards = $$('.g-card');
    if (!cards.length) return;

    cards.forEach(function (card) {
      card.classList.add('tilt');
      card.addEventListener('pointermove', function (e) {
        var r = card.getBoundingClientRect();
        var px = (e.clientX - r.left) / r.width;
        var py = (e.clientY - r.top) / r.height;
        card.classList.add('is-tilting');
        card.style.setProperty('--ty', ((px - 0.5) * 11).toFixed(2) + 'deg');
        card.style.setProperty('--tx', ((0.5 - py) * 9).toFixed(2) + 'deg');
        card.style.setProperty('--tz', '12px');
        card.style.setProperty('--gx', (px * 100).toFixed(1) + '%');
        card.style.setProperty('--gy', (py * 100).toFixed(1) + '%');
      }, { passive: true });
      card.addEventListener('pointerleave', function () {
        card.classList.remove('is-tilting');
        card.style.setProperty('--ty', '0deg');
        card.style.setProperty('--tx', '0deg');
        card.style.setProperty('--tz', '0px');
      });
    });
  }

  /* ---------- 3. Tab panels enter in 3D ---------- */
  function initTabs3d() {
    var wraps = $$('[data-tabs]');
    if (!wraps.length) return;
    wraps.forEach(function (wrap) {
      wrap.classList.add('tabs-3d');
      if (reduced) return;
      wrap.addEventListener('click', function (e) {
        var btn = e.target.closest ? e.target.closest('.tab-btn') : null;
        if (!btn) return;
        // The existing tab script flips `hidden`; animate whatever it reveals.
        window.setTimeout(function () {
          $$('.tab-panel', wrap).forEach(function (panel) {
            if (panel.hidden) return;
            panel.classList.remove('is-entering');
            void panel.offsetWidth;
            panel.classList.add('is-entering');
          });
        }, 0);
      });
    });
  }

  function boot() {
    initDeck();
    initTilt();
    initTabs3d();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
}());
