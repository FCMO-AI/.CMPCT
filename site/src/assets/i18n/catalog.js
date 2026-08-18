/* CMPCT curated locale catalogue assembly — Surface 0.29.i.
   Footnote: locale content lives in reviewable source-keyed packs. This assembly deliberately contains no
   translation logic and cannot synthesize missing copy. Missing entries stay failures in the quality gate. */
import { META as EN_META, SOURCE_PHRASES, SOURCE_MESSAGES, PROTECTED_TOKENS, QUALITY_CONTRACT } from './locales/en.js';
import { META as ES_META, PHRASES as ES_PHRASES, MESSAGES as ES_MESSAGES } from './locales/es-419.js';
import { META as PT_META, PHRASES as PT_PHRASES, MESSAGES as PT_MESSAGES } from './locales/pt-br.js';
import { META as FR_META, PHRASES as FR_PHRASES, MESSAGES as FR_MESSAGES } from './locales/fr.js';
import { META as DE_META, PHRASES as DE_PHRASES, MESSAGES as DE_MESSAGES } from './locales/de.js';

export const DEFAULT_LOCALE = 'en';
export const SUPPORTED_LOCALES = ['en', 'es-419', 'pt-BR', 'fr', 'de'];
export const LOCALE_META = Object.freeze({ en: EN_META, 'es-419': ES_META, 'pt-BR': PT_META, fr: FR_META, de: DE_META });
const packs = { 'es-419': ES_PHRASES, 'pt-BR': PT_PHRASES, fr: FR_PHRASES, de: DE_PHRASES };
const messagePacks = { 'es-419': ES_MESSAGES, 'pt-BR': PT_MESSAGES, fr: FR_MESSAGES, de: DE_MESSAGES };
export const PHRASES = Object.freeze(SOURCE_PHRASES.map((source) => Object.freeze({
  ...source,
  'es-419': packs['es-419'][source.en],
  'pt-BR': packs['pt-BR'][source.en],
  fr: packs.fr[source.en],
  de: packs.de[source.en],
})));
export const MESSAGES = Object.freeze(Object.fromEntries(Object.entries(SOURCE_MESSAGES).map(([key, en]) => [key, Object.freeze({
  en, 'es-419': messagePacks['es-419'][key], 'pt-BR': messagePacks['pt-BR'][key], fr: messagePacks.fr[key], de: messagePacks.de[key],
})])));
export { PROTECTED_TOKENS, QUALITY_CONTRACT };
