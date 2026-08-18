/* CMPCT curated locale catalogue assembly — Surface 0.29.i.
   Footnote: locale content lives in reviewable source-keyed or source-order packs. This assembly deliberately
   contains no translation logic and cannot synthesize missing copy. Missing entries remain quality-gate failures. */
import { META as EN_META, SOURCE_PHRASES, SOURCE_MESSAGES, PROTECTED_TOKENS, QUALITY_CONTRACT } from './locales/en.js';
import { META as ES_META, PHRASES as ES_PHRASES, MESSAGES as ES_MESSAGES } from './locales/es-419.js';
import { META as PT_META, PHRASES as PT_PHRASES, MESSAGES as PT_MESSAGES } from './locales/pt-br.js';
import { META as FR_META, PHRASES as FR_PHRASES, MESSAGES as FR_MESSAGES } from './locales/fr.js';
import { META as DE_META, PHRASES as DE_PHRASES, MESSAGES as DE_MESSAGES } from './locales/de.js';
import { EXTENDED_LOCALES, EXTENDED_META } from './extended-meta.js';
import { EXTENDED_MESSAGES, EXTENDED_PHRASE_VALUES } from './extended-packs.js';
import { makePhraseMap } from './locale-pack.js';

export const DEFAULT_LOCALE = 'en';
export const SUPPORTED_LOCALES = Object.freeze(['en', 'es-419', 'pt-BR', 'fr', 'de', ...EXTENDED_LOCALES]);
export const LOCALE_META = Object.freeze({
  en: EN_META,
  'es-419': ES_META,
  'pt-BR': PT_META,
  fr: FR_META,
  de: DE_META,
  ...EXTENDED_META,
});

const packs = {
  'es-419': ES_PHRASES,
  'pt-BR': PT_PHRASES,
  fr: FR_PHRASES,
  de: DE_PHRASES,
  ...Object.fromEntries(EXTENDED_LOCALES.map((locale) => [locale, makePhraseMap(SOURCE_PHRASES, EXTENDED_PHRASE_VALUES[locale], locale)])),
};
const messagePacks = {
  'es-419': ES_MESSAGES,
  'pt-BR': PT_MESSAGES,
  fr: FR_MESSAGES,
  de: DE_MESSAGES,
  ...EXTENDED_MESSAGES,
};

export const PHRASES = Object.freeze(SOURCE_PHRASES.map((source) => Object.freeze({
  ...source,
  ...Object.fromEntries(SUPPORTED_LOCALES.filter((locale) => locale !== 'en').map((locale) => [locale, packs[locale]?.[source.en]])),
})));

export const MESSAGES = Object.freeze(Object.fromEntries(Object.entries(SOURCE_MESSAGES).map(([key, en]) => [key, Object.freeze({
  en,
  ...Object.fromEntries(SUPPORTED_LOCALES.filter((locale) => locale !== 'en').map((locale) => [locale, messagePacks[locale]?.[key]])),
})])));

export { PROTECTED_TOKENS, QUALITY_CONTRACT };
