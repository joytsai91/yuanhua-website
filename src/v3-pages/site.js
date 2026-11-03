(function(){
  'use strict';
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var hasIO = 'IntersectionObserver' in window;
  var root = document.documentElement;
  var hdr = document.getElementById('hdr');
  var burger = document.getElementById('burger');
  var nav = document.getElementById('nav');
  function each(list, fn){ Array.prototype.forEach.call(list, fn); }

  /* ---- 1. page hero: image settles, tapes wipe in, copy rises ---- */
  var phero = document.querySelector('.phero');
  if (phero) {
    var pimg = phero.querySelector('.phero-bg img');
    var go = function(){ phero.classList.add('go'); };
    if (!pimg || pimg.complete) requestAnimationFrame(function(){ requestAnimationFrame(go); });
    else { pimg.addEventListener('load', go, { once: true }); pimg.addEventListener('error', go, { once: true }); }
    setTimeout(go, 1200);
  }

  /* ---- 2. mobile menu ---- */
  function closeMenu(){ nav.classList.remove('open'); burger.setAttribute('aria-expanded','false'); burger.setAttribute('aria-label','開啟選單'); }
  burger.addEventListener('click', function(){
    var open = nav.classList.toggle('open');
    burger.setAttribute('aria-expanded', String(open));
    burger.setAttribute('aria-label', open ? '關閉選單' : '開啟選單');
  });
  document.addEventListener('keydown', function(e){ if (e.key === 'Escape' && nav.classList.contains('open')) { closeMenu(); burger.focus(); } });

  /* ---- 3. reveal engine (same as the home page): one-shot, middle band of the viewport ---- */
  var rvEls = document.querySelectorAll('[data-rv], .tl>li');
  var pending = new Set();
  var rio = null;
  function show(el, i){ el.style.setProperty('--i', i); el.classList.add('in'); pending.delete(el); }
  if (!hasIO) { each(rvEls, function(el){ show(el, 0); }); }
  else {
    rio = new IntersectionObserver(function(entries){
      var batch = [];
      entries.forEach(function(e){ if (e.isIntersecting) batch.push(e); });
      batch.sort(function(a, b){ return (a.boundingClientRect.top - b.boundingClientRect.top) || (a.boundingClientRect.left - b.boundingClientRect.left); });
      batch.forEach(function(e, i){ show(e.target, Math.min(i, 6)); rio.unobserve(e.target); });
    }, { rootMargin: '-12% 0px -12% 0px' });
    each(rvEls, function(el){ pending.add(el); rio.observe(el); });
  }
  document.addEventListener('focusin', function(e){
    var el = e.target && e.target.closest ? e.target.closest('[data-rv]') : null;
    while (el) {
      if (pending.has(el)) { el.style.setProperty('--d', '0ms'); show(el, 0); if (rio) rio.unobserve(el); }
      el = el.parentElement ? el.parentElement.closest('[data-rv]') : null;
    }
  });
  function flushBottom(vh){
    var i = 0;
    pending.forEach(function(el){ if (el.getBoundingClientRect().top < vh) { show(el, Math.min(i++, 6)); if (rio) rio.unobserve(el); } });
  }

  /* ---- 4. looping words run only while visible ---- */
  if (!reduce && hasIO) {
    var lio = new IntersectionObserver(function(es){ es.forEach(function(e){ e.target.classList.toggle('run', e.isIntersecting); }); }, { rootMargin: '80px 0px' });
    each(document.querySelectorAll('.foot-loop, .linefield'), function(el){ lio.observe(el); });
  }

  /* ---- 5. scroll engine: header, hero drift, section progress, image parallax ---- */
  var active = new Set();
  var tracked = document.querySelectorAll('[data-sc], .plx');
  if (!reduce && hasIO) {
    var sio = new IntersectionObserver(function(es){
      es.forEach(function(e){ if (e.isIntersecting) active.add(e.target); else active.delete(e.target); });
      schedule();
    }, { rootMargin: '120px 0px' });
    each(tracked, function(el){ sio.observe(el); });
  }
  var raf = 0;
  function schedule(){ if (!raf) raf = requestAnimationFrame(frame); }
  function clamp(v, a, b){ return v < a ? a : (v > b ? b : v); }
  function frame(){
    raf = 0;
    var vh = window.innerHeight, y = window.pageYOffset, max = root.scrollHeight - vh;
    var reads = [];
    active.forEach(function(el){ reads.push([el, el.getBoundingClientRect()]); });
    hdr.classList.toggle('solid', y > 40);
    if (hdr.classList.contains('solid')) root.style.setProperty('--hdr-h', hdr.offsetHeight + 'px');
    hdr.style.setProperty('--sp', (max > 0 ? clamp(y / max, 0, 1) : 0).toFixed(4));
    if (y >= max - 4) flushBottom(vh);
    else if (pending.size) {
      var late = [];
      pending.forEach(function(el){ var r = el.getBoundingClientRect(); if (r.top < vh * 0.88 && r.bottom > vh * 0.12) late.push([el, r]); });
      late.sort(function(p, q){ return (p[1].top - q[1].top) || (p[1].left - q[1].left); });
      late.forEach(function(pair, i){ show(pair[0], Math.min(i, 5)); if (rio) rio.unobserve(pair[0]); });
    }
    if (reduce) return;
    var lim = vh * 0.04;
    reads.forEach(function(pair){
      var el = pair[0], r = pair[1];
      if (el.classList.contains('plx')) {
        var off = (r.top - (vh / 2 - r.height / 2)) * -0.08;
        el.style.setProperty('--py', clamp(off, -lim, lim).toFixed(2) + 'px');
      }
      if (el.hasAttribute('data-sc')) {
        if (el.classList.contains('phero')) { el.style.setProperty('--p', clamp(y / vh, 0, 1).toFixed(4)); return; }
        el.style.setProperty('--p', clamp((vh - r.top) / (vh + r.height), 0, 1).toFixed(4));
        el.style.setProperty('--e', clamp((vh * 0.7 - r.top) / (r.height * 0.85), 0, 1).toFixed(4));
      }
    });
  }
  hdr.addEventListener('transitionend', schedule);
  window.addEventListener('scroll', schedule, { passive: true });
  window.addEventListener('resize', function(){ schedule(); hintTables(); });
  frame();

  /* ---- 6. smooth in-page anchors (easeInOutExpo, ~1s), landing under the header + local nav ---- */
  function settledTop(el){
    var top = el.getBoundingClientRect().top;
    var w = el.closest('[data-rv]');
    while (w) {
      var t = getComputedStyle(w).transform;
      if (t && t !== 'none' && window.DOMMatrixReadOnly) top -= new DOMMatrixReadOnly(t).m42;
      if (pending.has(w)) { w.style.setProperty('--d', '0ms'); show(w, 0); if (rio) rio.unobserve(w); }
      w = w.parentElement ? w.parentElement.closest('[data-rv]') : null;
    }
    return top;
  }
  function easeInOutExpo(t){ return t === 0 ? 0 : t === 1 ? 1 : t < .5 ? Math.pow(2, 20 * t - 10) / 2 : (2 - Math.pow(2, -20 * t + 10)) / 2; }
  function headerOffset(){ return (window.innerWidth <= 1120 ? 66 : 90) + (document.querySelector('.lnav') ? 64 : 14); }
  document.addEventListener('click', function(e){
    var a = e.target.closest('a[href^="#"]');
    if (!a) return;
    var id = a.getAttribute('href');
    if (id.length < 2) return;
    var target = document.getElementById(decodeURIComponent(id.slice(1)));
    if (!target) return;
    e.preventDefault();
    if (nav.classList.contains('open')) closeMenu();
    var from = window.pageYOffset;
    var maxY = root.scrollHeight - window.innerHeight;
    var to = Math.max(0, Math.min(maxY, settledTop(target) + from - headerOffset()));
    if (reduce || Math.abs(to - from) < 2) { window.scrollTo(0, to); }
    else {
      var t0 = performance.now(), dur = 900, cancelled = false;
      var stop = function(){ cancelled = true; };
      window.addEventListener('wheel', stop, { passive: true, once: true });
      window.addEventListener('touchstart', stop, { passive: true, once: true });
      (function step(now){
        if (cancelled) return;
        var t = Math.min(1, (now - t0) / dur);
        window.scrollTo(0, from + (to - from) * easeInOutExpo(t));
        if (t < 1) requestAnimationFrame(step);
      })(t0);
    }
    if (history.replaceState) history.replaceState(null, '', id);
    target.setAttribute('tabindex', '-1'); target.focus({ preventScroll: true });
  });

  /* ---- 7. wide spec tables: show a swipe hint only when they really overflow ---- */
  function hintTables(){
    each(document.querySelectorAll('.tbl-wrap'), function(w){
      var can = w.scrollWidth > w.clientWidth + 2;
      w.classList.toggle('can-scroll', can);
      if (can) { w.setAttribute('tabindex', '0'); w.setAttribute('role', 'region'); }
    });
  }
  hintTables();

  /* ---- 8. tabs (news categories, gallery panels) ---- */
  each(document.querySelectorAll('[data-tabs]'), function(box){
    var btns = box.querySelectorAll('[role="tab"]');
    var mode = box.getAttribute('data-tabs'); // "filter" (one grid) or "panels"
    var scope = box.parentElement;
    function select(btn, focus){
      each(btns, function(b){ var on = b === btn; b.setAttribute('aria-selected', String(on)); b.tabIndex = on ? 0 : -1; });
      var key = btn.getAttribute('data-key');
      if (mode === 'filter') {
        var grid = scope.querySelector('[data-filter-grid]');
        var shown = 0;
        each(grid.children, function(li){
          var ok = key === 'all' || (' ' + li.getAttribute('data-cat') + ' ').indexOf(' ' + key + ' ') > -1;
          li.hidden = !ok; if (ok) shown++;
        });
        var empty = scope.querySelector('[data-empty]');
        if (empty) {
          each(empty.querySelectorAll('[data-for]'), function(p){ p.hidden = p.getAttribute('data-for') !== key; });
          empty.hidden = shown > 0;
        }
      } else {
        each(scope.querySelectorAll('[role="tabpanel"]'), function(p){ p.hidden = p.id !== btn.getAttribute('aria-controls'); });
      }
      if (focus) btn.focus();
      if (history.replaceState && btn.getAttribute('data-hash')) history.replaceState(null, '', '#' + btn.getAttribute('data-hash'));
      hintTables();
    }
    each(btns, function(b, i){
      b.addEventListener('click', function(){ select(b, false); });
      b.addEventListener('keydown', function(e){
        var k = e.key, n = null;
        if (k === 'ArrowRight') n = btns[(i + 1) % btns.length];
        if (k === 'ArrowLeft') n = btns[(i - 1 + btns.length) % btns.length];
        if (k === 'Home') n = btns[0];
        if (k === 'End') n = btns[btns.length - 1];
        if (n) { e.preventDefault(); select(n, true); }
      });
    });
    function fromHash(){
      var want = location.hash.slice(1), hit = null;
      each(btns, function(b){ if (want && b.getAttribute('data-hash') === want) hit = b; });
      return hit;
    }
    select(fromHash() || btns[0], false);
    // header sub-links point at news.html#expo etc.: follow them without a reload
    window.addEventListener('hashchange', function(){
      var b = fromHash(); if (!b) return;
      select(b, false);
      if (nav.classList.contains('open')) closeMenu();
      box.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'center' });
    });
  });

  /* ---- 9. lightbox for photo grids ---- */
  var lb = document.querySelector('.lb');
  if (lb) {
    var lbImg = lb.querySelector('img'), lbCap = lb.querySelector('figcaption');
    var list = [], idx = 0, opener = null;
    function render(){ var b = list[idx]; lbImg.src = b.getAttribute('data-full'); lbImg.alt = b.getAttribute('data-alt') || ''; lbCap.textContent = (idx + 1) + ' / ' + list.length; }
    function open(btn){
      list = Array.prototype.slice.call(btn.closest('.gal').querySelectorAll('button'));
      idx = list.indexOf(btn); opener = btn; render();
      if (lb.showModal) lb.showModal(); else lb.setAttribute('open', '');
      root.style.overflow = 'hidden';
    }
    function close(){ if (lb.close) lb.close(); else lb.removeAttribute('open'); }
    lb.addEventListener('close', function(){ root.style.overflow = ''; if (opener) opener.focus(); });
    document.addEventListener('click', function(e){ var b = e.target.closest('.gal button'); if (b) open(b); });
    lb.querySelector('.x').addEventListener('click', close);
    lb.querySelector('.pv').addEventListener('click', function(){ idx = (idx - 1 + list.length) % list.length; render(); });
    lb.querySelector('.nx').addEventListener('click', function(){ idx = (idx + 1) % list.length; render(); });
    lb.addEventListener('click', function(e){ if (e.target === lb) close(); });
    lb.addEventListener('keydown', function(e){
      if (e.key === 'ArrowRight') { idx = (idx + 1) % list.length; render(); }
      if (e.key === 'ArrowLeft') { idx = (idx - 1 + list.length) % list.length; render(); }
    });
    var sx = null;
    lb.addEventListener('touchstart', function(e){ sx = e.touches[0].clientX; }, { passive: true });
    lb.addEventListener('touchend', function(e){
      if (sx === null) return;
      var dx = e.changedTouches[0].clientX - sx; sx = null;
      if (Math.abs(dx) > 50) { idx = (idx + (dx < 0 ? 1 : -1) + list.length) % list.length; render(); }
    });
  }

  /* ---- 10. click-to-load videos (no third-party player until asked) ---- */
  document.addEventListener('click', function(e){
    var p = e.target.closest('.poster[data-yt]');
    if (!p) return;
    var f = document.createElement('iframe');
    f.src = 'https://www.youtube-nocookie.com/embed/' + p.getAttribute('data-yt') + '?autoplay=1&rel=0';
    f.title = p.getAttribute('aria-label') || '影片';
    f.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture';
    f.allowFullscreen = true;
    p.replaceWith(f);
  });

  /* ---- 11. oil table: highlight one material column ---- */
  var ot = document.querySelector('.otable');
  if (ot) {
    each(document.querySelectorAll('.mat-filter button'), function(b){
      b.addEventListener('click', function(){
        var col = b.getAttribute('data-col');
        each(document.querySelectorAll('.mat-filter button'), function(x){ x.setAttribute('aria-pressed', String(x === b)); });
        each(ot.querySelectorAll('[data-col]'), function(c){
          var m = c.getAttribute('data-col');
          c.classList.toggle('hi', col !== 'all' && m === col);
          c.classList.toggle('dim', col !== 'all' && m !== col);
        });
      });
    });
  }

  /* ---- 12. contact form (demo: validates and confirms, nothing is sent) ---- */
  var form = document.getElementById('ask');
  if (form) {
    var item = new URLSearchParams(location.search).get('item');
    if (item) {
      var sel = form.querySelector('[name="topic"]');
      var msg = form.querySelector('[name="message"]');
      var t = new URLSearchParams(location.search).get('topic');
      if (t && sel) each(sel.options, function(o){ if (o.value === t) sel.value = t; });
      if (msg && !msg.value) msg.value = '想詢問：' + item + '\n';
    }
    form.addEventListener('submit', function(e){
      e.preventDefault();
      var first = null;
      each(form.querySelectorAll('[required]'), function(f){
        var bad = !f.value.trim() || (f.type === 'tel' && !/^[0-9+\-#() ]{6,}$/.test(f.value.trim()));
        f.setAttribute('aria-invalid', String(bad));
        var err = document.getElementById(f.getAttribute('aria-describedby') ? f.getAttribute('aria-describedby').split(' ')[0] : '');
        if (err && err.classList.contains('err')) err.textContent = bad ? (f.type === 'tel' && f.value.trim() ? '請確認電話號碼格式' : '此欄位為必填') : '';
        if (bad && !first) first = f;
      });
      if (first) { first.focus(); return; }
      var done = document.getElementById('ask-done');
      done.hidden = false;
      done.setAttribute('tabindex', '-1'); done.focus();
      form.querySelector('[type="submit"]').disabled = true;
    });
    each(form.querySelectorAll('[required]'), function(f){
      f.addEventListener('input', function(){ if (f.getAttribute('aria-invalid') === 'true' && f.value.trim()) { f.setAttribute('aria-invalid', 'false'); var err = document.getElementById((f.getAttribute('aria-describedby') || '').split(' ')[0]); if (err) err.textContent = ''; } });
    });
  }
})();
