/* CMPCT cinematic behavior.
   Footnote: every effect has a semantic job. The dot field compresses from logical space toward physical
   roots; pointer response reveals depth; the chapter rail exposes information architecture. None of these
   effects owns benchmark truth or Browser Lab behavior. */
(() => {
  const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  const canvas = document.querySelector('#entropy-sun');
  const hero = document.querySelector('.hero');

  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const fract = (v) => v - Math.floor(v);
  const noise = (n) => fract(Math.sin(n * 91.917 + 17.23) * 43758.5453123);
  let compressionRatio = 0.615;

  async function readRatio() {
    try {
      const response = await fetch('project-data.json', { cache: 'no-store' });
      if (!response.ok) return;
      const data = await response.json();
      const evidence = data?.public_evidence;
      const rows = evidence?.structural?.competitors || [];
      const short = evidence?.structural?.headline_comparator_short || 'ZIP / Deflate';
      const row = rows.find((item) => item.short === short);
      const candidate = Number(evidence?.structural?.candidate_bytes);
      const baseline = Number(row?.bytes);
      if (candidate > 0 && baseline > 0) compressionRatio = clamp(candidate / baseline, .34, .96);
    } catch (_) {
      /* Footnote: the graphic keeps a conservative fallback ratio when viewed as a static preview. */
    }
  }

  function initEntropySun() {
    if (!canvas || !hero) return;
    const ctx = canvas.getContext('2d', { alpha: true });
    if (!ctx) return;
    const golden = Math.PI * (3 - Math.sqrt(5));
    const points = Array.from({ length: 1120 }, (_, i) => {
      const t = (i + .5) / 1120;
      const r = Math.sqrt(t);
      const angle = i * golden + (noise(i) - .5) * .14;
      const corona = noise(i + 3000) > .91;
      return {
        r,
        angle,
        corona,
        size: .52 + noise(i + 1000) * (corona ? 2.1 : 1.25),
        alpha: .14 + noise(i + 2000) * (corona ? .56 : .42),
        kind: noise(i + 4000),
        phase: noise(i + 5000) * Math.PI * 2,
      };
    });

    let width = 0, height = 0, dpr = 1;
    let pointerX = 0, pointerY = 0;
    let scrollCompression = 0;
    const start = performance.now();
    let raf = 0;

    function resize() {
      const rect = canvas.getBoundingClientRect();
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = Math.max(1, rect.width);
      height = Math.max(1, rect.height);
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function draw(now, staticOnly = false) {
      ctx.clearRect(0, 0, width, height);
      const cx = width * .5;
      const cy = height * .5;
      const base = Math.min(width, height) * .43;
      const elapsed = Math.max(0, now - start);
      const settleT = staticOnly ? 1 : clamp(elapsed / 1900, 0, 1);
      const settle = 1 - Math.pow(1 - settleT, 4);
      const breath = staticOnly ? 0 : Math.sin(now * .00034) * .008;
      const finalScale = .60 + compressionRatio * .28;
      const packedScale = 1 - (1 - finalScale) * (.54 + .46 * scrollCompression);
      const px = pointerX * base * .018;
      const py = pointerY * base * .014;

      ctx.save();
      ctx.translate(cx + px, cy + py);
      ctx.globalCompositeOperation = 'lighter';

      // Footnote: construction rings make the field read as one authored physical system, not confetti.
      ctx.lineWidth = .7;
      for (const q of [.34, .61, .89]) {
        ctx.beginPath();
        ctx.strokeStyle = q === .61 ? 'rgba(253,82,4,.075)' : 'rgba(255,255,255,.032)';
        ctx.arc(0, 0, base * q * (packedScale + .08), 0, Math.PI * 2);
        ctx.stroke();
      }
      ctx.beginPath();
      ctx.strokeStyle = 'rgba(253,82,4,.11)';
      ctx.arc(0, 0, base * (packedScale + .05), -1.15, .72);
      ctx.stroke();

      for (const p of points) {
        const logicalRadius = base * (.08 + p.r * .94) * (p.corona ? 1.08 : 1);
        const physicalRadius = logicalRadius * (packedScale + p.r * .07);
        const radius = logicalRadius + (physicalRadius - logicalRadius) * settle;
        const wave = staticOnly ? 0 : Math.sin(now * .00055 + p.phase + p.r * 5) * base * .0026;
        const a = p.angle + (staticOnly ? 0 : now * .000012 * (p.corona ? -1 : 1)) + pointerX * .008 * (1 - p.r);
        const x = Math.cos(a) * (radius + wave);
        const y = Math.sin(a) * (radius + wave) * (.94 + p.r * .055) + pointerY * (1 - p.r) * 2.2;
        const edgeFade = 1 - Math.max(0, p.r - .72) / .34;
        let alpha = p.alpha * clamp(edgeFade, .15, 1);
        if (p.corona) alpha *= .58 + (1 - settle) * .7;
        let fill = `rgba(244,240,232,${alpha.toFixed(3)})`;
        if (p.kind > .89) fill = `rgba(253,82,4,${Math.min(.78, alpha * 1.22).toFixed(3)})`;
        if (p.kind > .987) fill = `rgba(215,255,63,${Math.min(.72, alpha * 1.08).toFixed(3)})`;
        ctx.beginPath();
        ctx.fillStyle = fill;
        ctx.arc(x, y, p.size * (1 + breath), 0, Math.PI * 2);
        ctx.fill();
      }

      // Footnote: one intervention axis crosses the field. It is localized, not generic decoration.
      const axis = base * (packedScale + .12);
      const grad = ctx.createLinearGradient(-axis, 0, axis, 0);
      grad.addColorStop(0, 'rgba(253,82,4,0)');
      grad.addColorStop(.42, 'rgba(253,82,4,.18)');
      grad.addColorStop(.56, 'rgba(253,82,4,.43)');
      grad.addColorStop(1, 'rgba(253,82,4,0)');
      ctx.strokeStyle = grad;
      ctx.lineWidth = .7;
      ctx.beginPath();
      ctx.moveTo(-axis, base * .04);
      ctx.lineTo(axis, -base * .06);
      ctx.stroke();
      ctx.restore();

      if (!staticOnly) raf = requestAnimationFrame(draw);
    }

    const onPointer = (event) => {
      const rect = hero.getBoundingClientRect();
      pointerX = clamp(((event.clientX - rect.left) / Math.max(rect.width, 1) - .5) * 2, -1, 1);
      pointerY = clamp(((event.clientY - rect.top) / Math.max(rect.height, 1) - .5) * 2, -1, 1);
    };

    const onScroll = () => {
      const rect = hero.getBoundingClientRect();
      const travel = Math.max(hero.offsetHeight * .72, 1);
      scrollCompression = clamp(-rect.top / travel, 0, 1);
    };

    onScroll();
    resize();
    window.addEventListener('resize', resize, { passive: true });
    if (!reduce) window.addEventListener('scroll', onScroll, { passive: true });
    if (!reduce) hero.addEventListener('pointermove', onPointer, { passive: true });
    if (reduce) draw(performance.now(), true);
    else raf = requestAnimationFrame(draw);

    window.addEventListener('pagehide', () => cancelAnimationFrame(raf), { once: true });
  }

  function initSpotlights() {
    if (reduce) return;
    document.querySelectorAll('.cinematic-surface').forEach((surface) => {
      surface.addEventListener('pointermove', (event) => {
        const rect = surface.getBoundingClientRect();
        surface.style.setProperty('--spot-x', `${event.clientX - rect.left}px`);
        surface.style.setProperty('--spot-y', `${event.clientY - rect.top}px`);
      }, { passive: true });
    });
  }

  function initChapterRail() {
    if (window.innerWidth < 1180 || reduce) return;
    const chapters = [...document.querySelectorAll('[data-chapter]')];
    if (!chapters.length) return;
    const rail = document.createElement('nav');
    rail.className = 'chapter-rail';
    rail.setAttribute('aria-label', 'Page chapters');
    const links = [];
    for (const section of chapters) {
      const chapter = section.dataset.chapter || '';
      if (!section.id) section.id = `chapter-${chapter}`;
      const eyebrow = section.querySelector('.eyebrow')?.textContent?.replace(/^\d+\s*\/\s*/, '') || `Chapter ${chapter}`;
      const link = document.createElement('a');
      link.href = `#${section.id}`;
      link.innerHTML = `<i></i><span>${chapter} ${eyebrow}</span>`;
      rail.appendChild(link);
      links.push([section, link]);
    }
    document.body.appendChild(rail);
    const observer = new IntersectionObserver((entries) => {
      const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (!visible) return;
      for (const [section, link] of links) link.classList.toggle('active', section === visible.target);
    }, { rootMargin: '-30% 0px -55% 0px', threshold: [0, .1, .35, .7] });
    chapters.forEach((section) => observer.observe(section));
  }

  function initHeader() {
    const header = document.querySelector('[data-header]');
    if (!header) return;
    const update = () => header.classList.toggle('scrolled', window.scrollY > 18);
    update();
    addEventListener('scroll', update, { passive: true });
  }

  readRatio().finally(() => {
    initEntropySun();
    initSpotlights();
    initChapterRail();
    initHeader();
  });
})();
