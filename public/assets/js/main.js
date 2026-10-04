(() => {
  'use strict';

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  /* ---------- Первый экран: один поставленный момент при загрузке ---------- */

  const hero = $('.hero');
  if (hero) {
    const heroImg = $('.hero__img', hero);
    const ready = () => requestAnimationFrame(() => hero.classList.add('is-ready'));
    if (heroImg && !heroImg.complete) {
      heroImg.addEventListener('load', ready, { once: true });
      heroImg.addEventListener('error', ready, { once: true });
      setTimeout(ready, 1500);
    } else {
      ready();
    }
  }

  /* ---------- Меню: группы разделов, мобильное раскрытие и подсветка текущей главы ---------- */

  const nav = $('#site-nav');
  const toggle = $('.menu-toggle');
  const groups = nav ? $$('.nav-group', nav) : [];

  const closeGroups = (except) => {
    groups.forEach((group) => { if (group !== except) group.open = false; });
  };

  const closeMenu = () => {
    nav.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
  };

  if (nav && toggle) {
    toggle.addEventListener('click', () => {
      const open = nav.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', String(open));
      if (!open) closeGroups();
    });
    nav.addEventListener('click', (e) => {
      if (!e.target.closest('a')) return;
      closeGroups();
      closeMenu();
    });
    // Одновременно открыта одна группа (для браузеров без <details name>).
    groups.forEach((group) => {
      group.addEventListener('toggle', () => { if (group.open) closeGroups(group); });
    });
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.nav-group')) closeGroups();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key !== 'Escape') return;
      const openGroup = groups.find((group) => group.open);
      if (openGroup) {
        openGroup.open = false;
        $('summary', openGroup).focus();
      } else if (nav.classList.contains('is-open')) {
        closeMenu();
        toggle.focus();
      }
    });
  }

  const navLinks = nav ? $$('a[href^="#"]', nav) : [];
  const spied = navLinks
    .map((link) => ({ link, target: $(link.getAttribute('href')), group: link.closest('.nav-group') }))
    .filter((item) => item.target);

  if (spied.length && 'IntersectionObserver' in window) {
    const visible = new Set();
    const spy = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) visible.add(entry.target);
        else visible.delete(entry.target);
      });
      // Активна последняя по порядку глава из тех, что пересекают полосу под шапкой;
      // вместе с ней подсвечивается её группа в верхней строке.
      let current = null;
      spied.forEach((item) => { if (visible.has(item.target)) current = item; });
      spied.forEach((item) => {
        const active = item === current;
        item.link.classList.toggle('is-active', active);
        if (active) item.link.setAttribute('aria-current', 'true');
        else item.link.removeAttribute('aria-current');
      });
      groups.forEach((group) => {
        $('summary', group).classList.toggle('is-active', Boolean(current) && current.group === group);
      });
    }, { rootMargin: '-30% 0px -60% 0px' });
    spied.forEach((item) => spy.observe(item.target));
  }

  /* ---------- Появление в поле зрения: линия маршрута и следы маркера ---------- */

  const reveal = $$('[data-route], .shot');
  $$('[data-route] .route__num').forEach((num, i) => num.style.setProperty('--i', i));

  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-in');
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.35 });
    reveal.forEach((el) => io.observe(el));
  } else {
    reveal.forEach((el) => el.classList.add('is-in'));
  }

  /* ---------- Вкладки ---------- */

  $$('[data-tabs]').forEach((root) => {
    const tabs = $$('[role="tab"]', root);
    const vertical = root.hasAttribute('data-tabs-vertical');
    const prevKey = vertical ? 'ArrowUp' : 'ArrowLeft';
    const nextKey = vertical ? 'ArrowDown' : 'ArrowRight';

    const select = (tab, focus) => {
      tabs.forEach((t) => {
        const on = t === tab;
        t.setAttribute('aria-selected', String(on));
        t.tabIndex = on ? 0 : -1;
        const panel = document.getElementById(t.getAttribute('aria-controls'));
        if (panel) panel.hidden = !on;
      });
      if (focus) tab.focus();
    };

    tabs.forEach((tab, i) => {
      tab.addEventListener('click', () => select(tab, false));
      tab.addEventListener('keydown', (e) => {
        let to = null;
        if (e.key === nextKey) to = tabs[(i + 1) % tabs.length];
        else if (e.key === prevKey) to = tabs[(i - 1 + tabs.length) % tabs.length];
        else if (e.key === 'Home') to = tabs[0];
        else if (e.key === 'End') to = tabs[tabs.length - 1];
        if (to) {
          e.preventDefault();
          select(to, true);
        }
      });
    });
  });

  /* ---------- Карусель экранов ---------- */

  $$('[data-carousel]').forEach((root) => {
    const track = $('.carousel__track', root);
    const slides = $$('.carousel__slide', root);
    const prev = $('[data-carousel-prev]', root);
    const next = $('[data-carousel-next]', root);
    const current = $('[data-carousel-current]', root);
    if (!track || !slides.length) return;

    const step = () => {
      const gap = parseFloat(getComputedStyle(track).columnGap) || 0;
      return slides[0].getBoundingClientRect().width + gap;
    };
    const update = () => {
      const max = track.scrollWidth - track.clientWidth;
      const atEnd = track.scrollLeft >= max - 2;
      const index = atEnd ? slides.length - 1 : Math.min(slides.length - 1, Math.round(track.scrollLeft / step()));
      current.textContent = String(index + 1);
      prev.disabled = track.scrollLeft <= 2;
      next.disabled = atEnd;
    };

    prev.addEventListener('click', () => track.scrollBy({ left: -step() }));
    next.addEventListener('click', () => track.scrollBy({ left: step() }));
    track.addEventListener('scroll', () => requestAnimationFrame(update), { passive: true });
    window.addEventListener('resize', update);
    update();
  });

  /* ---------- Экран целиком ---------- */

  const lightbox = $('#lightbox');
  if (lightbox && typeof lightbox.showModal === 'function') {
    const img = $('.lightbox__img', lightbox);
    const scroller = $('.lightbox__scroll', lightbox);

    const open = (source) => {
      img.src = source.dataset.lightbox;
      img.alt = source.dataset.lightboxAlt || '';
      img.width = Number(source.dataset.lightboxW) || 0;
      img.height = Number(source.dataset.lightboxH) || 0;
      lightbox.showModal();
      scroller.scrollTo(0, 0);
    };

    document.addEventListener('click', (e) => {
      const direct = e.target.closest('[data-lightbox]');
      if (direct) return open(direct);
      const trigger = e.target.closest('[data-lightbox-trigger]');
      if (trigger) {
        const source = $('[data-lightbox]', trigger.closest('figure'));
        if (source) open(source);
      }
    });

    // Клик по затемнению вокруг снимка закрывает окно.
    scroller.addEventListener('click', (e) => {
      if (e.target === scroller) lightbox.close();
    });
    lightbox.addEventListener('close', () => { img.removeAttribute('src'); });
  }

  /* ---------- Кнопка внизу экрана на телефоне ---------- */

  const mobileCta = $('.mobile-cta');
  const heroActions = $('.hero__actions');
  const request = $('#request');
  if (mobileCta && heroActions && request && 'IntersectionObserver' in window) {
    const state = { hero: true, request: false };
    const update = () => mobileCta.classList.toggle('is-visible', !state.hero && !state.request);
    new IntersectionObserver(([entry]) => { state.hero = entry.isIntersecting; update(); }).observe(heroActions);
    new IntersectionObserver(([entry]) => { state.request = entry.isIntersecting; update(); }).observe(request);
  }
})();
