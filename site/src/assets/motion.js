const root = document.documentElement;
const hero = document.querySelector('.hero');
const score = document.querySelector('.hero-score');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

// Footnote: this layer enhances an already-complete static page. Nothing here is allowed to become
// required for benchmark data, navigation, Browser Lab, or accessibility-critical behavior.
root.classList.add('motion-enabled');

function installHeroField() {
  if (!hero || reducedMotion.matches) return;

  const field = document.createElement('div');
  field.className = 'hero-motion-field';
  field.setAttribute('aria-hidden', 'true');

  for (const className of ['orbit-a', 'orbit-b', 'orbit-c']) {
    const orbit = document.createElement('span');
    orbit.className = `motion-orbit ${className}`;
    field.appendChild(orbit);
  }

  const particles = [
    [8,18,2,8.2,-1.2],[14,63,3,10.8,-4.8],[21,37,2,7.4,-2.3],[29,78,4,12.1,-7.2],
    [38,12,2,9.5,-3.1],[46,57,3,11.2,-5.6],[53,28,2,8.9,-6.9],[61,84,3,13.4,-2.1],
    [67,44,2,9.9,-8.2],[73,16,4,12.8,-4.2],[79,69,2,7.8,-1.7],[86,35,3,10.4,-6.1],
    [91,79,2,11.7,-3.6],[95,22,2,8.6,-5.1]
  ];

  for (const [x, y, size, duration, delay] of particles) {
    const particle = document.createElement('i');
    particle.className = 'motion-particle';
    particle.style.setProperty('--particle-x', `${x}%`);
    particle.style.setProperty('--particle-y', `${y}%`);
    particle.style.setProperty('--particle-size', `${size}px`);
    particle.style.setProperty('--particle-duration', `${duration}s`);
    particle.style.setProperty('--particle-delay', `${delay}s`);
    field.appendChild(particle);
  }

  hero.prepend(field);
}

function installPointerDepth() {
  if (!hero || reducedMotion.matches) return;

  let frame = 0;
  let nextX = 0;
  let nextY = 0;

  const paint = () => {
    frame = 0;
    hero.style.setProperty('--hero-pointer-x', nextX.toFixed(3));
    hero.style.setProperty('--hero-pointer-y', nextY.toFixed(3));

    if (score) {
      score.style.setProperty('--score-tilt-x', `${(-nextY * 3.2).toFixed(2)}deg`);
      score.style.setProperty('--score-tilt-y', `${(nextX * 4.2).toFixed(2)}deg`);
      score.style.setProperty('--score-glow-x', `${((nextX + 1) * 50).toFixed(1)}%`);
      score.style.setProperty('--score-glow-y', `${((nextY + 1) * 50).toFixed(1)}%`);
    }
  };

  hero.addEventListener('pointermove', (event) => {
    const rect = hero.getBoundingClientRect();
    nextX = Math.max(-1, Math.min(1, ((event.clientX - rect.left) / rect.width - .5) * 2));
    nextY = Math.max(-1, Math.min(1, ((event.clientY - rect.top) / rect.height - .5) * 2));
    if (!frame) frame = requestAnimationFrame(paint);
  }, { passive: true });

  hero.addEventListener('pointerleave', () => {
    nextX = 0;
    nextY = 0;
    if (!frame) frame = requestAnimationFrame(paint);
  }, { passive: true });
}

function installScrollDepth() {
  if (!hero || reducedMotion.matches) return;
  let ticking = false;

  const paint = () => {
    ticking = false;
    const rect = hero.getBoundingClientRect();
    const progress = Math.max(-220, Math.min(220, -rect.top));
    const normalized = Math.max(0, Math.min(1, -rect.top / Math.max(hero.offsetHeight * .72, 1)));
    hero.style.setProperty('--hero-scroll', progress.toFixed(1));
    root.style.setProperty('--hero-progress', normalized.toFixed(4));
    // Footnote: normalized progress is presentation-only state. It lets authored light fields contract
    // with the same hero scroll journey without coupling decoration to benchmark or archive semantics.
  };

  const requestPaint = () => {
    if (!ticking) {
      ticking = true;
      requestAnimationFrame(paint);
    }
  };

  paint();
  addEventListener('scroll', requestPaint, { passive: true });
  addEventListener('resize', requestPaint, { passive: true });
}

function installRevealObserver() {
  const targets = document.querySelectorAll([
    '.regression-banner', '.section-head', '.arena', '.performance-split', '.graph-stage',
    '.mechanism-grid', '.canonical-band', '.parity-kpis', '.benchmark-table-wrap',
    '.benchmark-notes', '.lab-status', '.lab-grid', '.release-rail', '.site-footer'
  ].join(','));

  if (reducedMotion.matches || !('IntersectionObserver' in window)) {
    targets.forEach((target) => target.classList.add('is-visible'));
    return;
  }

  targets.forEach((target) => target.classList.add('reveal-target'));
  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      entry.target.classList.add('is-visible');
      observer.unobserve(entry.target);
    }
  }, { rootMargin: '0px 0px -10% 0px', threshold: .08 });

  targets.forEach((target) => observer.observe(target));
}

function pulseValue(node) {
  if (!(node instanceof HTMLElement) || reducedMotion.matches) return;
  node.classList.remove('value-pop');
  void node.offsetWidth;
  node.classList.add('value-pop');
}

function installDataPulse() {
  const nodes = [
    document.querySelector('#hero-gain'),
    ...document.querySelectorAll('#hero-metrics strong'),
    document.querySelector('#workload-score')
  ].filter(Boolean);

  if (!nodes.length || !('MutationObserver' in window)) return;
  const observer = new MutationObserver((records) => {
    const touched = new Set(records.map((record) => record.target.parentElement || record.target));
    touched.forEach((node) => pulseValue(node));
  });

  nodes.forEach((node) => observer.observe(node, { childList: true, characterData: true, subtree: true }));
}

function start() {
  installHeroField();
  installPointerDepth();
  installScrollDepth();
  installRevealObserver();
  installDataPulse();
  requestAnimationFrame(() => root.classList.add('motion-ready'));
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', start, { once: true });
} else {
  start();
}
