import { chromium } from 'playwright';
import fs from 'node:fs/promises';
import path from 'node:path';

/* CMPCT responsive render contract.
   Footnote: CSS presence is not visual evidence. This script loads the built site in a real Chromium
   engine across width, height and aspect-ratio classes, records screenshots, and fails on measurable
   composition defects that previously survived source-only review. */

const baseURL = process.argv[2] || 'http://127.0.0.1:4173/';
const outputDir = path.resolve(process.argv[3] || 'viewport-artifacts');

const viewports = [
  { name: 'phone-compact-320x568', width: 320, height: 568 },
  { name: 'phone-standard-360x800', width: 360, height: 800 },
  { name: 'phone-tall-390x844', width: 390, height: 844 },
  { name: 'phone-large-430x932', width: 430, height: 932 },
  { name: 'phone-landscape-844x390', width: 844, height: 390 },
  { name: 'fold-inner-540x720', width: 540, height: 720 },
  { name: 'tablet-portrait-768x1024', width: 768, height: 1024 },
  { name: 'tablet-portrait-large-820x1180', width: 820, height: 1180 },
  { name: 'tablet-landscape-1024x768', width: 1024, height: 768 },
  { name: 'short-panel-1024x600', width: 1024, height: 600 },
  { name: 'laptop-short-1366x768', width: 1366, height: 768 },
  { name: 'laptop-16x10-1440x900', width: 1440, height: 900 },
  { name: 'desktop-5x4-1280x1024', width: 1280, height: 1024 },
  { name: 'desktop-16x9-1920x1080', width: 1920, height: 1080 },
  { name: 'ultrawide-2560x1080', width: 2560, height: 1080 },
  { name: 'large-qhd-2560x1440', width: 2560, height: 1440 },
];

const keySelectors = [
  '.site-header',
  '.hero-copy h1',
  '.hero-score',
  '#hero-metrics',
  '.regression-banner',
  '.arena',
  '.performance-split',
  '.graph-stage',
  '.canonical-band',
  '.benchmark-table-wrap',
  '.lab-grid',
  '.release-rail',
  '.site-footer',
];

/* Footnote: the historical motion layer reveals later chapters with IntersectionObserver. A full-page
   screenshot does not itself guarantee those observers are exercised. Scroll representative chapter
   surfaces through the real viewport first, then return to the hero; visibility assertions can remain
   strict instead of incorrectly treating intentional pre-reveal opacity as a responsive failure. */
const revealSelectors = [
  '.hero-score',
  '#hero-metrics',
  '.arena',
  '.performance-split',
  '.graph-stage',
  '.canonical-band',
  '.benchmark-table-wrap',
  '.lab-grid',
  '.release-rail',
  '.site-footer',
];

function overlap(a, b) {
  const x = Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left));
  const y = Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));
  return x * y;
}

async function inspect(page, viewport) {
  return page.evaluate(({ keySelectors, viewport }) => {
    const visible = (el) => {
      if (!el) return false;
      const s = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      return s.display !== 'none' && s.visibility !== 'hidden' && Number(s.opacity || 1) > 0 && r.width > 0 && r.height > 0;
    };
    const rect = (el) => {
      const r = el.getBoundingClientRect();
      return { left: r.left, top: r.top, right: r.right, bottom: r.bottom, width: r.width, height: r.height };
    };
    const boxes = {};
    for (const selector of keySelectors) {
      const el = document.querySelector(selector);
      boxes[selector] = visible(el) ? rect(el) : null;
    }

    const root = document.documentElement;
    const body = document.body;
    const gain = document.querySelector('#hero-gain');
    const score = document.querySelector('.hero-score');
    const headerChildren = ['.brand', '.top-nav', '.header-right']
      .map((selector) => document.querySelector(selector))
      .filter(visible)
      .map((el) => ({ className: el.className, ...rect(el) }));
    const heroCopy = document.querySelector('.hero-copy');
    const heroScore = document.querySelector('.hero-score');
    const graphNodes = [...document.querySelectorAll('.graph-node')].filter(visible).map(rect);
    const buttons = [...document.querySelectorAll('button, .button, .inspect-picker')].filter(visible).map((el) => ({
      tag: el.tagName,
      className: el.className,
      ...rect(el),
    }));

    return {
      viewport,
      innerWidth: window.innerWidth,
      innerHeight: window.innerHeight,
      documentScrollWidth: Math.max(root.scrollWidth, body.scrollWidth),
      boxes,
      gain: visible(gain) ? rect(gain) : null,
      score: visible(score) ? rect(score) : null,
      heroCopy: visible(heroCopy) ? rect(heroCopy) : null,
      heroScore: visible(heroScore) ? rect(heroScore) : null,
      headerChildren,
      graphNodes,
      buttons,
      bodyOverflowX: getComputedStyle(body).overflowX,
      title: document.title,
      surfaceText: document.querySelector('.release-chip')?.textContent || '',
    };
  }, { keySelectors, viewport });
}

function validate(result) {
  const errors = [];
  const { innerWidth: w, boxes } = result;
  if (result.documentScrollWidth > w + 1) {
    errors.push(`document horizontal overflow: ${result.documentScrollWidth}px > ${w}px`);
  }

  for (const [selector, box] of Object.entries(boxes)) {
    if (!box) {
      errors.push(`required surface not rendered: ${selector}`);
      continue;
    }
    if (box.left < -1 || box.right > w + 1) {
      errors.push(`${selector} escapes viewport horizontally: left=${box.left.toFixed(1)} right=${box.right.toFixed(1)} width=${w}`);
    }
    if (box.width < 1 || box.height < 1) errors.push(`${selector} collapsed to zero geometry`);
  }

  if (result.gain && result.score) {
    const tolerance = 3;
    if (result.gain.left < result.score.left - tolerance || result.gain.right > result.score.right + tolerance) {
      errors.push(`hero proof value clips outside score card: gain ${JSON.stringify(result.gain)} score ${JSON.stringify(result.score)}`);
    }
  }

  // Footnote: desktop hero copy and proof card are separate authored objects. On stacked responsive layouts
  // vertical proximity is expected, but an area intersection on the wide composition indicates a regression.
  if (w > 1100 && result.heroCopy && result.heroScore && overlap(result.heroCopy, result.heroScore) > 4) {
    errors.push('desktop hero copy overlaps proof card');
  }

  for (let i = 0; i < result.headerChildren.length; i += 1) {
    for (let j = i + 1; j < result.headerChildren.length; j += 1) {
      if (overlap(result.headerChildren[i], result.headerChildren[j]) > 2) {
        errors.push(`header collision between ${result.headerChildren[i].className} and ${result.headerChildren[j].className}`);
      }
    }
  }

  for (let i = 0; i < result.graphNodes.length; i += 1) {
    for (let j = i + 1; j < result.graphNodes.length; j += 1) {
      if (overlap(result.graphNodes[i], result.graphNodes[j]) > 8) {
        errors.push(`information-graph node collision between node ${i + 1} and ${j + 1}`);
      }
    }
  }

  // Buttons are already >=48px in the base system. Allow text-only links to be shorter, but interactive
  // cards and actual controls must not shrink below a practical 40px floor at any tested ratio.
  for (const control of result.buttons) {
    const textOnly = String(control.className).includes('button-text');
    if (!textOnly && control.height < 40) {
      errors.push(`interactive control below 40px height: ${control.className || control.tag} (${control.height.toFixed(1)}px)`);
    }
  }

  return errors;
}

await fs.mkdir(outputDir, { recursive: true });
const browser = await chromium.launch({ headless: true });
const report = [];
let failed = false;

try {
  for (const viewport of viewports) {
    const context = await browser.newContext({
      viewport: { width: viewport.width, height: viewport.height },
      deviceScaleFactor: 1,
      reducedMotion: 'no-preference',
    });
    const page = await context.newPage();
    const pageErrors = [];
    page.on('pageerror', (error) => pageErrors.push(String(error?.stack || error)));

    await page.goto(baseURL, { waitUntil: 'networkidle', timeout: 30_000 });
    await page.waitForFunction(() => {
      const gain = document.querySelector('#hero-gain')?.textContent?.trim();
      return gain && gain !== '—';
    }, { timeout: 15_000 });
    await page.evaluate(() => document.fonts?.ready);
    await page.waitForTimeout(160);

    for (const selector of revealSelectors) {
      const target = page.locator(selector).first();
      if (await target.count()) {
        await target.scrollIntoViewIfNeeded();
        await page.waitForTimeout(100);
      }
    }
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(160);

    const result = await inspect(page, viewport);
    const errors = [...pageErrors, ...validate(result)];
    failed ||= errors.length > 0;
    report.push({ ...result, errors });

    await page.screenshot({
      path: path.join(outputDir, `${viewport.name}.jpg`),
      type: 'jpeg',
      quality: 78,
      fullPage: true,
      animations: 'disabled',
    });
    console.log(`${errors.length ? 'FAIL' : 'PASS'} ${viewport.name}${errors.length ? ` — ${errors.join('; ')}` : ''}`);
    await context.close();
  }
} finally {
  await browser.close();
}

await fs.writeFile(path.join(outputDir, 'viewport-report.json'), `${JSON.stringify(report, null, 2)}\n`, 'utf8');

if (failed) {
  console.error(`Responsive viewport matrix failed. Inspect ${outputDir}/viewport-report.json and screenshots.`);
  process.exit(1);
}
console.log(`Responsive viewport matrix passed ${viewports.length} physical viewport classes.`);
