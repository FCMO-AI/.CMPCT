import fs from "node:fs/promises";
import path from "node:path";
import { chromium } from "playwright";
import { SUPPORTED_LOCALES } from "../src/assets/i18n/catalog.js";

/* CMPCT locale render contract — Surface 0.29.k.
   Footnote: the base viewport matrix already proves the authored English composition across 16 physical
   ratios. This complementary matrix renders every non-English locale at three translation-stress geometries:
   compact phone, landscape phone and short laptop. It targets word expansion, CJK compression, CTA pressure,
   dynamic evidence leakage and accidental untranslated prose. */

const baseUrl = process.argv[2] || "http://127.0.0.1:4173/";
const artifactDir = process.argv[3] || "locale-artifacts";
const locales = SUPPORTED_LOCALES.filter((locale) => locale !== "en");
const viewports = [
  { name: "compact-phone", width: 320, height: 568 },
  { name: "landscape-phone", width: 844, height: 390 },
  { name: "short-laptop", width: 1366, height: 768 },
];

await fs.mkdir(artifactDir, { recursive: true });
const browser = await chromium.launch({ headless: true });
const report = [];
let failures = 0;

try {
  for (const locale of locales) {
    for (const viewport of viewports) {
      const page = await browser.newPage({ viewport });
      const url = new URL(baseUrl);
      url.searchParams.set("lang", locale);
      await page.goto(url.toString(), { waitUntil: "networkidle" });
      await page.waitForFunction(() => window.__CMPCT_I18N__?.ready === true, null, { timeout: 15_000 });
      await page.waitForFunction(() => document.querySelector("#hero-gain")?.textContent?.trim() !== "—", null, { timeout: 15_000 }).catch(() => {});
      await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));

      const result = await page.evaluate(() => {
        const state = window.__CMPCT_I18N__ || {};
        const doc = document.documentElement;
        const body = document.body;
        const switcher = document.querySelector(".language-switcher");
        const hero = document.querySelector(".hero-copy h1");
        const rect = (node) => node?.getBoundingClientRect?.() || null;
        const switchRect = rect(switcher);
        const heroRect = rect(hero);
        const viewportWidth = window.innerWidth;
        const overflow = Math.max(doc.scrollWidth, body.scrollWidth) - viewportWidth;
        const switcherVisible = Boolean(switchRect && switchRect.width >= 40 && switchRect.height >= 34 && switchRect.right > 0 && switchRect.left < viewportWidth);
        const heroVisible = Boolean(heroRect && heroRect.width > 0 && heroRect.height > 0 && heroRect.bottom > 0);
        return {
          htmlLang: doc.lang,
          locale: state.locale,
          supportedCount: state.supported?.length || 0,
          missing: state.missing || [],
          overflow,
          switcherVisible,
          heroVisible,
          heroText: hero?.textContent?.replace(/\s+/g, " ").trim() || "",
          title: document.title,
        };
      });

      const issues = [];
      if (result.locale !== locale) issues.push(`runtime locale ${result.locale} != ${locale}`);
      if (result.htmlLang !== locale) issues.push(`html lang ${result.htmlLang} != ${locale}`);
      if (result.supportedCount !== SUPPORTED_LOCALES.length) issues.push(`runtime exposes ${result.supportedCount}/${SUPPORTED_LOCALES.length} locales`);
      if (result.overflow > 1) issues.push(`horizontal overflow ${result.overflow}px`);
      if (!result.switcherVisible) issues.push("language switcher is not physically usable");
      if (!result.heroVisible) issues.push("hero headline is not physically visible");
      if (!result.heroText || /Archive formats made peace with compromise/i.test(result.heroText)) issues.push("hero remained English");
      if (result.missing.length) issues.push(`untranslated authored copy: ${result.missing.join(" | ")}`);

      const name = `${locale.replace(/[^A-Za-z0-9-]/g, "-")}-${viewport.name}`;
      await page.screenshot({ path: path.join(artifactDir, `${name}.png`), fullPage: true });
      report.push({ locale, viewport, result, issues });
      if (issues.length) failures += 1;
      await page.close();
    }
  }
} finally {
  await browser.close();
}

await fs.writeFile(path.join(artifactDir, "report.json"), JSON.stringify({ failures, localeCount: locales.length, cases: report }, null, 2));
if (failures) {
  console.error(`Localized viewport contract failed ${failures}/${report.length} cases.`);
  for (const item of report.filter((row) => row.issues.length)) {
    console.error(`- ${item.locale} ${item.viewport.width}x${item.viewport.height}: ${item.issues.join("; ")}`);
  }
  process.exit(1);
}
console.log(`Localized viewport contract passed ${report.length} rendered cases across ${locales.length} non-English locales with zero untranslated authored strings.`);
