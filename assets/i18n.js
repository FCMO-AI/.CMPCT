/* CMPCT curated internationalization runtime — Surface 0.29.k.
   Footnote: this module performs locale selection and deterministic application only. It never translates
   text itself and never contacts a translation provider. All wording is reviewable in i18n/catalog.js. */
import {
  DEFAULT_LOCALE,
  LOCALE_META,
  MESSAGES,
  PHRASES,
  SUPPORTED_LOCALES,
} from "./i18n/catalog.js";

const STORAGE_KEY = "cmpct.locale";
const ORIGINAL_TEXT = new WeakMap();
const ORIGINAL_ATTR = new WeakMap();
const phraseByEnglish = new Map(PHRASES.map((entry) => [entry.en, entry]));
const staticMessageByEnglish = new Map(
  Object.entries(MESSAGES).filter(([, group]) => !String(group.en).includes("{")).map(([key, group]) => [group.en, key]),
);
const missing = new Map();
let observer = null;
let locale = DEFAULT_LOCALE;
let applying = false;

const normalize = (value) => String(value ?? "").replace(/\s+/g, " ").trim();

function interpolate(template, values) {
  return String(template).replace(/\{([a-zA-Z0-9_]+)\}/g, (_, key) => String(values[key] ?? `{${key}}`));
}

function message(key, values = {}, targetLocale = locale) {
  const group = MESSAGES[key];
  return group ? interpolate(group[targetLocale] || group[DEFAULT_LOCALE], values) : "";
}

function canonicalRequestedLocale(raw) {
  const requested = String(raw || "").trim().replace(/_/g, "-");
  if (!requested) return null;
  const lower = requested.toLowerCase();
  const exact = SUPPORTED_LOCALES.find((candidate) => candidate.toLowerCase() === lower);
  if (exact) return exact;

  // Footnote: Chinese cannot safely use the generic language-family fallback. Script/region tags decide
  // which curated writing system is appropriate; unknown generic zh intentionally defaults to Simplified.
  if (lower === "zh" || lower.startsWith("zh-")) {
    if (/(?:^|-)hant(?:-|$)|(?:^|-)(tw|hk|mo)(?:-|$)/.test(lower)) return "zh-Hant";
    if (/(?:^|-)hans(?:-|$)|(?:^|-)(cn|sg|my)(?:-|$)/.test(lower)) return "zh-Hans";
    return "zh-Hans";
  }

  const base = lower.split("-")[0];
  return SUPPORTED_LOCALES.find((candidate) => candidate.toLowerCase().split("-")[0] === base) || null;
}

function localeFromBrowser() {
  const requested = [...(navigator.languages || []), navigator.language].filter(Boolean);
  for (const raw of requested) {
    const candidate = canonicalRequestedLocale(raw);
    if (candidate) return candidate;
  }
  return DEFAULT_LOCALE;
}

function resolveLocale() {
  const query = new URLSearchParams(location.search).get("lang");
  const queryLocale = canonicalRequestedLocale(query);
  if (queryLocale) return queryLocale;
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    const storedLocale = canonicalRequestedLocale(stored);
    if (storedLocale) return storedLocale;
  } catch {
    // Footnote: storage may be unavailable in hardened/private contexts. Locale selection remains fully
    // functional through the URL and browser preferences; persistence is an enhancement, not a dependency.
  }
  return localeFromBrowser();
}

function preserveWhitespace(source, replacement) {
  const leading = source.match(/^\s*/)?.[0] || "";
  const trailing = source.match(/\s*$/)?.[0] || "";
  return `${leading}${replacement}${trailing}`;
}

function translatePattern(source, targetLocale) {
  let match;
  if ((match = source.match(/^(\d[\d,.]*) files?$/i))) {
    const n = match[1];
    return message(source.toLowerCase().endsWith(" file") ? "file" : "files", { n }, targetLocale);
  }
  if ((match = source.match(/^(.+) logical$/))) return message("logical", { bytes: match[1] }, targetLocale);
  if ((match = source.match(/^(.+) logical input · ([\d,.]+) files$/))) {
    return message("logicalInputFiles", { bytes: match[1], n: match[2] }, targetLocale);
  }
  if ((match = source.match(/^([\d.]+)% smaller than (.+)$/))) return message("smallerThan", { pct: `${match[1]}%`, name: match[2] }, targetLocale);
  if ((match = source.match(/^smaller than (.+)$/))) {
    const full = message("smallerThan", { pct: "__PCT__", name: match[1] }, targetLocale);
    // Footnote: `__PCT__` is an internal sentinel used only to reuse each locale's natural word order when
    // the source fragment omits a percentage. Remove the token itself rather than assuming a trailing ASCII
    // space; CJK templates can place it directly beside punctuation or translated words.
    return normalize(full.replace("__PCT__", ""));
  }
  if ((match = source.match(/^([\d.]+)% larger than (.+)$/))) return message("largerThan", { pct: `${match[1]}%`, name: match[2] }, targetLocale);
  if ((match = source.match(/^larger than (.+)$/))) {
    const full = message("largerThan", { pct: "__PCT__", name: match[1] }, targetLocale);
    return normalize(full.replace("__PCT__", ""));
  }
  if ((match = source.match(/^same stored bytes as (.+)$/))) return message("sameStored", { name: match[1] }, targetLocale);
  if ((match = source.match(/^vs (.+)$/))) return message("versus", { name: match[1] }, targetLocale);
  if ((match = source.match(/^If (.+) stores 100 MB on this matched test, CMPCT needs about ([\d.]+) MB\.$/))) {
    return message("heroIf", { name: match[1], value: match[2] }, targetLocale);
  }
  if ((match = source.match(/^CMPCT currently needs about ([\d.]+) MB for every 100 MB stored by (.+) on this matched test\.$/))) {
    return message("heroNeeds", { value: match[1], name: match[2] }, targetLocale);
  }
  if ((match = source.match(/^Serious size baseline: (.+)\.$/))) return message("seriousBaseline", { relation: match[1] }, targetLocale);
  if ((match = source.match(/^Scoped scheduler result: ([\d.]+)% lower wall time on its fixed gate\.$/))) {
    return message("scopedScheduler", { pct: match[1] }, targetLocale);
  }
  if ((match = source.match(/^Canonical format remains r(\d+)\.$/))) return message("canonicalRemains", { revision: match[1] }, targetLocale);
  if ((match = source.match(/^(\d+)\/(\d+) smaller · (\d+) larger$/))) {
    return message("categoryScore", { wins: match[1], total: match[2], losses: match[3] }, targetLocale);
  }
  if ((match = source.match(/^(\d+)\/(\d+) wins vs (.+)$/))) return message("winsAgainst", { wins: match[1], total: match[2], name: match[3] }, targetLocale);
  if ((match = source.match(/^(\d+)× median$/))) return message("repetitionsMedian", { n: match[1] }, targetLocale);
  if ((match = source.match(/^Portable writer verified for canonical format r(\d+)\.$/))) return message("writerVerified", { revision: match[1] }, targetLocale);
  if ((match = source.match(/^Browser writer paused after format revision (\d+)\.$/))) return message("writerPaused", { revision: match[1] }, targetLocale);
  if ((match = source.match(/^This build is verified for r(\d+); it refuses to guess a newer grammar\.$/))) return message("writerRefuses", { supported: match[1] }, targetLocale);
  if ((match = source.match(/^([\d.]+(?: [KMGT]i?B| B)) smaller$/))) return message("smaller", { bytes: match[1] }, targetLocale);
  if ((match = source.match(/^([\d.]+(?: [KMGT]i?B| B)) overhead$/))) return message("overhead", { bytes: match[1] }, targetLocale);
  if ((match = source.match(/^([\d,.]+) logical files → ([\d,.]+) unique blobs · ([\d,.]+) Deflate \/ ([\d,.]+) RAW\.$/))) {
    return message("logicalFilesUnique", { logical: match[1], unique: match[2], deflate: match[3], raw: match[4] }, targetLocale);
  }
  if ((match = source.match(/^Benchmark data unavailable: (.+)$/))) return message("benchmarkUnavailable", { error: match[1] }, targetLocale);
  if ((match = source.match(/^(.+) · ([\d,.]+) files on the matched structural tree\.(?: (Serious size baseline: .+?\.))?(?: (Scoped scheduler result: [\d.]+% lower wall time on its fixed gate\.))? Canonical format remains r(\d+)\.$/))) {
    const serious = match[3] ? ` ${translate(match[3], targetLocale)}` : "";
    const speed = match[4] ? ` ${translate(match[4], targetLocale)}` : "";
    return message("frontierQualification", { frontier: match[1], files: match[2], serious, speed, revision: match[5] }, targetLocale);
  }
  if ((match = source.match(/^(.+) input$/)) && /(?:B|KiB|MiB|GiB|TiB)$/.test(match[1])) {
    return `${match[1]} ${message("input", {}, targetLocale).toLowerCase()}`;
  }
  if ((match = source.match(/^(.+ (?:smaller|overhead)) · ([\d.]+%)$/))) {
    return `${translate(match[1], targetLocale) || match[1]} · ${match[2]}`;
  }
  return null;
}

function exactTranslation(source, targetLocale) {
  const entry = phraseByEnglish.get(source);
  return entry ? entry[targetLocale] || entry[DEFAULT_LOCALE] : null;
}

function translate(source, targetLocale) {
  if (targetLocale === DEFAULT_LOCALE) return source;
  const exact = exactTranslation(source, targetLocale);
  if (exact) return exact;
  const staticKey = staticMessageByEnglish.get(source);
  if (staticKey) return message(staticKey, {}, targetLocale);
  return translatePattern(source, targetLocale);
}

function isTechnicalOrDataLabel(text, node) {
  if (!text || text.length < 3) return true;
  if (/^(v?\d+(?:\.\d+){1,3}|r\d+|[0-9.,%+−×/:· -]+)$/.test(text)) return true;
  if (/^(CMPCT|ZIP|ZSTD|Zstd|LZMA2|ZPAQ|RAW|Deflate|GitHub|SHA-256|CRC32|CLI|MiB|KiB|GiB)$/i.test(text)) return true;
  if (/^[A-Fa-f0-9]{12,}$/.test(text)) return true;
  if (/^[\w.-]+\.(?:json|md|txt|cmpct)$/i.test(text)) return true;
  if (/^https?:\/\//i.test(text)) return true;
  const parent = node?.parentElement;
  if (parent?.closest("code, pre, option, .release-chip, .truth-line, #benchmark-record, .language-switcher")) return true;
  if (/^(AMD|Intel|Apple|ARM|Linux|Windows|macOS)\b/i.test(text)) return true;
  if (/^[\d.,]+ (?:B|KiB|MiB|GiB|TiB)(?: → [\d.,]+ (?:B|KiB|MiB|GiB|TiB))?$/.test(text)) return true;
  // Release-document titles are durable provenance labels. Their descriptive UI wrapper is localized,
  // while the canonical document title itself remains verbatim so links and repository history agree.
  if (parent?.closest(".release-node p")) return true;
  return false;
}

function recordMissing(text, node) {
  if (!node) return;
  if (locale === DEFAULT_LOCALE || isTechnicalOrDataLabel(text, node) || !/[A-Za-zÀ-ÿ]/.test(text) || text.length < 4) {
    missing.delete(node);
    return;
  }
  missing.set(node, text);
}

function applyTextNode(node) {
  if (!node || node.nodeType !== Node.TEXT_NODE) return;
  if (node.parentElement?.closest("script, style, template")) return;
  if (!ORIGINAL_TEXT.has(node)) ORIGINAL_TEXT.set(node, node.nodeValue || "");
  const original = ORIGINAL_TEXT.get(node) || "";
  const source = normalize(original);
  if (!source) return;
  const replacement = translate(source, locale);
  if (replacement) {
    missing.delete(node);
    const next = preserveWhitespace(original, replacement);
    if (node.nodeValue !== next) node.nodeValue = next;
  } else {
    if (node.nodeValue !== original) node.nodeValue = original;
    recordMissing(source, node);
  }
}

const TRANSLATABLE_ATTRIBUTES = ["aria-label", "title", "placeholder"];

function applyAttributes(element) {
  if (!(element instanceof Element)) return;
  if (!ORIGINAL_ATTR.has(element)) ORIGINAL_ATTR.set(element, {});
  const originals = ORIGINAL_ATTR.get(element);
  for (const attr of TRANSLATABLE_ATTRIBUTES) {
    if (!element.hasAttribute(attr)) continue;
    if (!(attr in originals)) originals[attr] = element.getAttribute(attr);
    const source = normalize(originals[attr]);
    if (!source) continue;
    const replacement = translate(source, locale);
    element.setAttribute(attr, replacement || originals[attr]);
    if (replacement) missing.delete(element);
    else recordMissing(source, element);
  }
}

function walk(root = document.body) {
  if (!root) return;
  if (root.nodeType === Node.TEXT_NODE) {
    applyTextNode(root);
    return;
  }
  if (root instanceof Element) applyAttributes(root);
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
  let node = walker.nextNode();
  while (node) {
    if (node.nodeType === Node.TEXT_NODE) applyTextNode(node);
    else applyAttributes(node);
    node = walker.nextNode();
  }
}

function updateMetadata() {
  const meta = LOCALE_META[locale] || LOCALE_META[DEFAULT_LOCALE];
  document.documentElement.lang = meta.htmlLang;
  document.title = meta.title;
  const description = document.querySelector('meta[name="description"]');
  if (description) description.setAttribute("content", meta.description);
}

function exposeState() {
  const state = window.__CMPCT_I18N__ || {};
  Object.assign(state, {
    ready: true,
    locale,
    supported: [...SUPPORTED_LOCALES],
    humanReviewed: Boolean(LOCALE_META[locale]?.humanReviewed),
    missing: [...new Set([...missing.entries()].filter(([node]) => node?.isConnected).map(([, text]) => text))].sort(),
    setLocale,
  });
  window.__CMPCT_I18N__ = state;
}

function syncSelector() {
  const select = document.querySelector("#cmpct-locale-select");
  if (select && select.value !== locale) select.value = locale;
}

function setLocale(next, { persist = true, url = true } = {}) {
  next = canonicalRequestedLocale(next) || DEFAULT_LOCALE;
  locale = next;
  missing.clear();
  applying = true;
  updateMetadata();
  walk(document.body);
  applying = false;
  syncSelector();
  if (persist) {
    try { localStorage.setItem(STORAGE_KEY, locale); } catch { /* see persistence footnote above */ }
  }
  if (url) {
    const current = new URL(location.href);
    if (locale === DEFAULT_LOCALE) current.searchParams.delete("lang");
    else current.searchParams.set("lang", locale);
    history.replaceState(null, "", `${current.pathname}${current.search}${current.hash}`);
  }
  exposeState();
  document.dispatchEvent(new CustomEvent("cmpct:localechange", { detail: { locale } }));
}

function installSelector() {
  if (document.querySelector("#cmpct-locale-select")) return;
  const host = document.createElement("label");
  host.className = "language-switcher";
  host.setAttribute("aria-label", "Language");
  host.innerHTML = `<span aria-hidden="true">文/A</span><select id="cmpct-locale-select" aria-label="Language"></select>`;
  const select = host.querySelector("select");

  // Footnote: English is not just a fallback. It is the canonical semantic source and therefore remains the
  // first explicit selectable language even as the catalogue grows. Grouping the source separately makes
  // translation provenance visible without making the compact control wider in its closed state.
  const sourceGroup = document.createElement("optgroup");
  sourceGroup.label = "Canonical source";
  const translatedGroup = document.createElement("optgroup");
  translatedGroup.label = "Curated translations";
  select.append(sourceGroup, translatedGroup);

  for (const key of SUPPORTED_LOCALES) {
    const option = document.createElement("option");
    option.value = key;
    option.textContent = LOCALE_META[key].short;
    option.title = key === DEFAULT_LOCALE ? `${LOCALE_META[key].label} — canonical source` : LOCALE_META[key].label;
    (key === DEFAULT_LOCALE ? sourceGroup : translatedGroup).append(option);
  }
  select.value = locale;
  select.addEventListener("change", () => setLocale(select.value));

  // Footnote: insert before the release receipt rather than after the outbound links. This keeps language
  // control in the utility cluster while preserving GitHub as the visual terminal action on wide layouts.
  const headerRight = document.querySelector(".header-right");
  const releaseChip = headerRight?.querySelector(".release-chip");
  if (headerRight) headerRight.insertBefore(host, releaseChip || headerRight.firstChild);
  else document.body.prepend(host);
}

function installObserver() {
  observer?.disconnect();
  observer = new MutationObserver((records) => {
    if (applying) return;
    applying = true;
    for (const record of records) {
      if (record.type === "characterData") applyTextNode(record.target);
      for (const node of record.addedNodes) walk(node);
    }
    applying = false;
    exposeState();
  });
  observer.observe(document.body, { childList: true, subtree: true, characterData: true });
}

function boot() {
  locale = resolveLocale();
  installSelector();
  updateMetadata();
  walk(document.body);
  installObserver();
  exposeState();
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, { once: true });
else boot();
