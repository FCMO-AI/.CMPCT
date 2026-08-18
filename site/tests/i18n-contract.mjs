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

/* CMPCT curated-language contract — Surface 0.29.k.
   Footnote: no automatic metric can prove literary taste. This gate proves the failure modes that *are*
   machine-checkable: catalogue completeness, source-order integrity, placeholder preservation, protected
   technical vocabulary, implausible compact-copy expansion, README discoverability/evidence parity and
   accidental introduction of runtime machine-translation services. */

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../..");
const errors = [];
const fail = (message) => errors.push(message);
const placeholders = (value) => [...String(value).matchAll(/\{([A-Za-z0-9_]+)\}/g)].map((m) => m[1]).sort();
const words = (value) => String(value).replace(/\s+/g, " ").trim();

// Footnote: these are deliberately narrow technical loanwords/identifiers that may naturally remain unchanged
// in one or more languages. Ordinary prose cannot use this escape hatch; unchanged English prose is a defect.
const SAFE_SAME_TECHNICAL = new Set([
  "Runner", "Build", "ZIP / DEFLATE", "7Z / LZMA2", "Corpus", "LOCAL", "Magic",
  "Benchmarks ↗", "commit:", "Repository", "Repository ↗", "Record", "media", "sparse",
  "Engine", "Lab", "Contract", "Format",
]);

if (DEFAULT_LOCALE !== "en") fail("English must remain the canonical semantic source locale");
if (SUPPORTED_LOCALES.length < 20) fail(`expected at least 20 supported locales, got ${SUPPORTED_LOCALES.length}`);
if (QUALITY_CONTRACT.machineTranslationAtRuntime !== false) fail("runtime machine translation must stay disabled");
if (QUALITY_CONTRACT.mode !== "curated-semantic-adaptation") fail("unexpected i18n quality mode");
if (QUALITY_CONTRACT.catalogueRevision !== "0.29.k") fail(`stale catalogue revision: ${QUALITY_CONTRACT.catalogueRevision}`);

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
    if (value === source && !entry.allowSame && !SAFE_SAME_TECHNICAL.has(source)) {
      fail(`${locale} left English source unchanged without technical exemption: ${source}`);
    }
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
if (!runtime.includes('"zh-Hant"') || !runtime.includes('"zh-Hans"')) fail("Chinese script/region resolution is missing");

// Human-facing README parity is part of the same public localization contract. The English README remains
// canonical, but every supported non-English locale must be directly discoverable and retain the current
// release/format/surface/evidence markers so translated documentation cannot silently fossilize.
const rootReadme = fs.readFileSync(path.join(root, "README.md"), "utf8");
for (const locale of SUPPORTED_LOCALES.filter((key) => key !== DEFAULT_LOCALE)) {
  const relative = `docs/readme/README.${locale}.md`;
  const absolute = path.join(root, relative);
  if (!fs.existsSync(absolute)) { fail(`missing localized README: ${relative}`); continue; }
  if (!rootReadme.includes(relative)) fail(`root README does not link ${relative}`);
  const readme = fs.readFileSync(absolute, "utf8");
  if (readme.length < 2500) fail(`${relative} is implausibly short (${readme.length} chars)`);
  for (const marker of ["v0.29.0", "r24", "0.29.k", "47,147,764 B", "Apache"]) {
    if (!readme.includes(marker)) fail(`${relative} missing current authority/evidence marker ${marker}`);
  }
  if (readme.includes("0.29.j") || readme.includes("0.28.a")) fail(`${relative} contains stale surface marker`);
  if (!readme.includes(`?lang=${locale}`)) fail(`${relative} does not preserve locale when handing off to the website`);
}

if (errors.length) {
  console.error(`Curated i18n contract failed with ${errors.length} error(s):`);
  for (const error of errors) console.error(`- ${error}`);
  process.exit(1);
}
console.log(`Curated i18n contract passed ${PHRASES.length} phrases × ${SUPPORTED_LOCALES.length} locales, ${Object.keys(MESSAGES).length} dynamic templates and ${SUPPORTED_LOCALES.length - 1} localized READMEs.`);
