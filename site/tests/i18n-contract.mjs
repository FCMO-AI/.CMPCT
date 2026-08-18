import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  DEFAULT_LOCALE,
  LOCALE_META,
  MESSAGES,
  PHRASES,
  PROTECTED_TOKENS,
  QUALITY_CONTRACT,
  SUPPORTED_LOCALES,
} from "../src/assets/i18n/catalog.js";

/* CMPCT curated-language contract.
   Footnote: no automatic metric can prove literary taste. This gate proves the failure modes that *are*
   machine-checkable: catalogue completeness, placeholder preservation, protected technical vocabulary,
   implausible compact-copy expansion and accidental introduction of runtime machine-translation services. */

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../..");
const errors = [];
const fail = (message) => errors.push(message);
const placeholders = (value) => [...String(value).matchAll(/\{([A-Za-z0-9_]+)\}/g)].map((m) => m[1]).sort();
const words = (value) => String(value).replace(/\s+/g, " ").trim();

if (DEFAULT_LOCALE !== "en") fail("English must remain the canonical semantic source locale");
if (QUALITY_CONTRACT.machineTranslationAtRuntime !== false) fail("runtime machine translation must stay disabled");
if (QUALITY_CONTRACT.mode !== "curated-semantic-adaptation") fail("unexpected i18n quality mode");

for (const locale of SUPPORTED_LOCALES) {
  const meta = LOCALE_META[locale];
  if (!meta) { fail(`missing metadata for ${locale}`); continue; }
  for (const field of ["label", "short", "htmlLang", "title", "description"]) {
    if (!words(meta[field])) fail(`empty locale metadata: ${locale}.${field}`);
  }
}

const seen = new Set();
for (const entry of PHRASES) {
  const source = words(entry.en);
  if (!source) fail("empty English phrase");
  if (seen.has(source)) fail(`duplicate English phrase: ${source}`);
  seen.add(source);
  for (const locale of SUPPORTED_LOCALES) {
    const value = words(entry[locale]);
    if (!value) { fail(`missing ${locale} phrase: ${source}`); continue; }
    if (locale === DEFAULT_LOCALE) continue;
    // Footnote: a non-English catalogue entry that silently copies the English source is not curated
    // localization. Universal technical terms may opt in explicitly with allowSame on the canonical entry.
    if (value === source && !entry.allowSame) fail(`${locale} left English source unchanged without allowSame: ${source}`);
    const ratio = value.length / Math.max(source.length, 1);
    const limit = entry.compact ? QUALITY_CONTRACT.compactExpansionLimit : QUALITY_CONTRACT.generalExpansionLimit;
    if (source.length >= 6 && ratio > limit) fail(`${locale} expansion ${ratio.toFixed(2)}× > ${limit}×: ${source}`);
    for (const token of PROTECTED_TOKENS) {
      if (source.includes(token) && !value.includes(token)) fail(`${locale} dropped protected token ${token}: ${source}`);
    }
  }
}

for (const [key, group] of Object.entries(MESSAGES)) {
  const canonical = placeholders(group.en);
  for (const locale of SUPPORTED_LOCALES) {
    if (!words(group[locale])) { fail(`missing ${locale} message template: ${key}`); continue; }
    const actual = placeholders(group[locale]);
    if (JSON.stringify(actual) !== JSON.stringify(canonical)) {
      fail(`${locale} placeholder mismatch for ${key}: expected ${canonical.join(",")} got ${actual.join(",")}`);
    }
  }
}

const runtime = fs.readFileSync(path.join(root, "site/src/assets/i18n.js"), "utf8");
for (const forbidden of ["translate.googleapis.com", "google-translate", "api.deepl.com", "api.cognitive.microsofttranslator.com"]) {
  if (runtime.toLowerCase().includes(forbidden)) fail(`runtime translation provider forbidden: ${forbidden}`);
}
if (!runtime.includes("navigator.languages")) fail("automatic browser-locale selection is missing");
if (!runtime.includes("MutationObserver")) fail("dynamic evidence translation observer is missing");

if (errors.length) {
  console.error(`Curated i18n contract failed with ${errors.length} error(s):`);
  for (const error of errors) console.error(`- ${error}`);
  process.exit(1);
}
console.log(`Curated i18n contract passed ${PHRASES.length} phrases × ${SUPPORTED_LOCALES.length} locales plus ${Object.keys(MESSAGES).length} dynamic templates.`);
