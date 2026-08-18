/* CMPCT extended curated locale assembly — Surface 0.29.k.
   Footnote: keeping the 15-language import fan-out here prevents catalog.js from becoming an unreadable
   dependency wall while still making every locale a static, reviewable, cacheable source module. */
import { PHRASE_VALUES as IT, MESSAGES as IT_M } from './locales/it.js';
import { PHRASE_VALUES as NL, MESSAGES as NL_M } from './locales/nl.js';
import { PHRASE_VALUES as PL, MESSAGES as PL_M } from './locales/pl.js';
import { PHRASE_VALUES as CS, MESSAGES as CS_M } from './locales/cs.js';
import { PHRASE_VALUES as HU, MESSAGES as HU_M } from './locales/hu.js';
import { PHRASE_VALUES as RO, MESSAGES as RO_M } from './locales/ro.js';
import { PHRASE_VALUES as TR, MESSAGES as TR_M } from './locales/tr.js';
import { PHRASE_VALUES as SV, MESSAGES as SV_M } from './locales/sv.js';
import { PHRASE_VALUES as DA, MESSAGES as DA_M } from './locales/da.js';
import { PHRASE_VALUES as FI, MESSAGES as FI_M } from './locales/fi.js';
import { PHRASE_VALUES as ID, MESSAGES as ID_M } from './locales/id.js';
import { PHRASE_VALUES as JA, MESSAGES as JA_M } from './locales/ja.js';
import { PHRASE_VALUES as KO, MESSAGES as KO_M } from './locales/ko.js';
import { PHRASE_VALUES as ZH_HANS, MESSAGES as ZH_HANS_M } from './locales/zh-hans.js';
import { PHRASE_VALUES as ZH_HANT, MESSAGES as ZH_HANT_M } from './locales/zh-hant.js';

// Footnote: percentage-bearing comparison templates receive a localized percent string from the runtime.
// Turkish normally prefixes the percent sign, but keeping the sign in both template and value would render
// `%%`. These two comparison forms therefore use the supplied localized value verbatim; scheduler copy keeps
// its own `%{pct}` because that runtime path supplies a bare number.
const TR_MESSAGES = Object.freeze({
  ...TR_M,
  smallerThan: '{name} değerinden {pct} daha küçük',
  largerThan: '{name} değerinden {pct} daha büyük',
});

export const EXTENDED_PHRASE_VALUES = Object.freeze({
  it: IT, nl: NL, pl: PL, cs: CS, hu: HU, ro: RO, tr: TR, sv: SV, da: DA, fi: FI, id: ID,
  ja: JA, ko: KO, 'zh-Hans': ZH_HANS, 'zh-Hant': ZH_HANT,
});
export const EXTENDED_MESSAGES = Object.freeze({
  it: IT_M, nl: NL_M, pl: PL_M, cs: CS_M, hu: HU_M, ro: RO_M, tr: TR_MESSAGES, sv: SV_M, da: DA_M, fi: FI_M, id: ID_M,
  ja: JA_M, ko: KO_M, 'zh-Hans': ZH_HANS_M, 'zh-Hant': ZH_HANT_M,
});
