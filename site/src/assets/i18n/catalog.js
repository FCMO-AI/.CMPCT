/* CMPCT curated locale catalogue assembly — Surface 0.29.k.
   Footnote: locale content lives in reviewable source-keyed or source-order packs. This assembly deliberately
   contains no translation logic and cannot synthesize missing copy. Missing entries remain quality-gate failures. */
import {
  META as EN_META,
  SOURCE_PHRASES,
  SOURCE_MESSAGES,
  PROTECTED_TOKENS,
  QUALITY_CONTRACT as SOURCE_QUALITY_CONTRACT,
} from './locales/en.js';
import { META as ES_META, PHRASES as ES_PHRASES, MESSAGES as ES_MESSAGES } from './locales/es-419.js';
import { META as PT_META, PHRASES as PT_PHRASES, MESSAGES as PT_MESSAGES } from './locales/pt-br.js';
import { META as FR_META, PHRASES as FR_PHRASES, MESSAGES as FR_MESSAGES } from './locales/fr.js';
import { META as DE_META, PHRASES as DE_PHRASES, MESSAGES as DE_MESSAGES } from './locales/de.js';
import { EXTENDED_LOCALES, EXTENDED_META } from './extended-meta.js';
import { EXTENDED_MESSAGES, EXTENDED_PHRASE_VALUES } from './extended-packs.js';
import { ATTRIBUTION_MESSAGES } from './attribution-messages.js';
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

const coreMessages = Object.fromEntries(Object.entries(SOURCE_MESSAGES).map(([key, en]) => [key, Object.freeze({
  en,
  ...Object.fromEntries(SUPPORTED_LOCALES.filter((locale) => locale !== 'en').map((locale) => [locale, messagePacks[locale]?.[key]])),
})]));

function phraseGroup(source, prefix = '') {
  // Footnote: DOM markup can split one authored sentence into punctuation + text around emphasized children.
  // Reuse the already-curated canonical phrase rather than duplicating twenty independent translations.
  const entry = PHRASES.find((candidate) => candidate.en === source);
  if (!entry) throw new Error(`CMPCT i18n: missing source phrase for derived message: ${source}`);
  return Object.freeze(Object.fromEntries(SUPPORTED_LOCALES.map((locale) => [locale, `${prefix}${entry[locale]}`])));
}

const UI_MESSAGES = Object.freeze({
  confirmedSpeedRegressionFragment: phraseGroup('Confirmed speed regression outside the same-runner noise envelope:', '. '),
  // Footnote: the cinematic chapter rail is created after initial DOM translation. Its accessibility name must
  // therefore live in the dynamic message catalogue instead of remaining an English-only JS literal.
  pageChapters: Object.freeze({
    en: 'Page chapters',
    'es-419': 'Capítulos de la página',
    'pt-BR': 'Capítulos da página',
    fr: 'Chapitres de la page',
    de: 'Seitenkapitel',
    it: 'Capitoli della pagina',
    nl: 'Paginaonderdelen',
    pl: 'Sekcje strony',
    cs: 'Sekce stránky',
    hu: 'Oldalszakaszok',
    ro: 'Secțiunile paginii',
    tr: 'Sayfa bölümleri',
    sv: 'Sidavsnitt',
    da: 'Sideafsnit',
    fi: 'Sivun osiot',
    id: 'Bagian halaman',
    ja: 'ページの章',
    ko: '페이지 섹션',
    'zh-Hans': '页面章节',
    'zh-Hant': '頁面章節',
  }),
});

// Footnote: attribution strings are a newer main-line stewardship concern. They join the same static-message
// catalogue rather than bypassing i18n, so dynamically inserted maker provenance is translated and validated
// without changing the older canonical English phrase identities or the extended packs' source-order mapping.
export const MESSAGES = Object.freeze({ ...coreMessages, ...ATTRIBUTION_MESSAGES, ...UI_MESSAGES });

// Footnote: the English source file describes the original localization campaign. The assembled catalogue
// advances with the public-surface milestone so CI can reject stale translation evidence without rewriting the
// canonical English phrase identities that all locale packs key against.
export const QUALITY_CONTRACT = Object.freeze({ ...SOURCE_QUALITY_CONTRACT, catalogueRevision: '0.29.k' });
export { PROTECTED_TOKENS };
