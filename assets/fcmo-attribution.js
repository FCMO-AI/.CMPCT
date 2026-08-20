const PUBLIC_STEWARD_URL = 'https://github.com/FCMO-AI';

function ensureMeta(name, content) {
  let node = document.head.querySelector(`meta[name="${name}"]`);
  if (!node) {
    node = document.createElement('meta');
    node.setAttribute('name', name);
    document.head.appendChild(node);
  }
  node.setAttribute('content', content);
}

async function synchronizeSurfaceLabel() {
  // Footnote: gh-pages is generated serving output and can occasionally be promoted in small, safe pieces
  // while hosted CI is unavailable. The tiny machine-readable receipt is therefore the final authority for
  // the visible surface label; this prevents a stale static chip without teaching branding code project truth.
  try {
    const response = await fetch('surface-revision.txt', { cache: 'no-store' });
    if (!response.ok) return;
    const surface = (await response.text()).trim();
    if (!/^\d+\.\d+\.[a-z]+$/.test(surface)) return;

    const chip = document.querySelector('.release-chip');
    if (chip) chip.textContent = chip.textContent.replace(/surface\s+\d+\.\d+\.[a-z]+/i, `surface ${surface}`);

    const truthSurface = [...document.querySelectorAll('.truth-line span')]
      .find((node) => /^Surface\s+/i.test(node.textContent || ''));
    if (truthSurface) truthSurface.textContent = `Surface ${surface}`;
  } catch {
    // Progressive enhancement only: a failed provenance fetch must never disturb the static site.
  }
}

function installQuietProvenance() {
  // Footnote: attribution belongs to the provenance layer, not the evidence renderer. It is inserted once
  // at the persistent footer so FCMO remains discoverable without competing with CMPCT's product hierarchy.
  const footer = document.querySelector('.site-footer');
  if (!footer || footer.querySelector('[data-fcmo-attribution]')) return;

  const credit = document.createElement('div');
  credit.className = 'fcmo-attribution';
  credit.dataset.fcmoAttribution = 'quiet-provenance';
  credit.setAttribute('aria-label', 'CMPCT project stewardship');
  credit.innerHTML = [
    '<span>CMPCT by <a href="https://github.com/FCMO-AI" rel="author">FCMO AI</a></span>',
    '<span class="fcmo-attribution-group">From the FCMO group</span>',
  ].join('<i aria-hidden="true"></i>');
  footer.appendChild(credit);

  // Footnote: standards-friendly document metadata gives crawlers and browser tooling a machine-readable
  // stewardship hint without adding another visible badge or coupling attribution to benchmark truth.
  ensureMeta('author', 'FCMO AI');
  ensureMeta('creator', 'FCMO AI');

  const existingAuthorLink = document.head.querySelector('link[rel="author"]');
  if (!existingAuthorLink) {
    const link = document.createElement('link');
    link.rel = 'author';
    link.href = PUBLIC_STEWARD_URL;
    document.head.appendChild(link);
  }
}

function startProvenance() {
  installQuietProvenance();
  void synchronizeSurfaceLabel();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', startProvenance, { once: true });
} else {
  startProvenance();
}
