# CMPCT curated localization contract

Status: **public-surface quality gate** at Surface `0.29.k`.

CMPCT localization is not runtime machine translation. English remains the canonical semantic source.
Supported translations are committed as reviewable locale packs under `site/src/assets/i18n/locales/`,
assembled by `site/src/assets/i18n/catalog.js`, and applied deterministically by the browser. The same
language set also has static human-facing README variants under `docs/readme/`.

The browser chooses a supported locale in this order:

1. explicit `?lang=` request;
2. the visitor's saved manual selection;
3. `navigator.languages` / browser preference;
4. English fallback.

Chinese receives explicit script/region handling rather than a naive `zh` family fallback:
`zh-Hant`, `zh-TW`, `zh-HK` and `zh-MO` resolve to Traditional Chinese; `zh-Hans`, `zh-CN`, `zh-SG`
and `zh-MY` resolve to Simplified Chinese; generic `zh` defaults to Simplified Chinese.

## Supported locales

CMPCT currently exposes **20 locales**:

- English (`en`) — canonical semantic source;
- Latin American Spanish (`es-419`);
- Brazilian Portuguese (`pt-BR`);
- French (`fr`);
- German (`de`);
- Italian (`it`);
- Dutch (`nl`);
- Polish (`pl`);
- Czech (`cs`);
- Hungarian (`hu`);
- Romanian (`ro`);
- Turkish (`tr`);
- Swedish (`sv`);
- Danish (`da`);
- Finnish (`fi`);
- Indonesian (`id`);
- Japanese (`ja`);
- Korean (`ko`);
- Simplified Chinese (`zh-Hans`);
- Traditional Chinese (`zh-Hant`).

Adding a language is deliberately more work than enabling a translation provider. A locale is not
supported until its site copy, dynamic templates, metadata, README handoff and rendered layout satisfy
the same public-proof discipline as the existing set.

## Translation doctrine

Translate **intent**, not English syntax. A good CMPCT localization must preserve:

1. the authority level of every claim — research stays research, canonical stays canonical;
2. benchmark caveats and losses without softening or upgrading them;
3. numbers, version identities, codec names and protected technical terminology;
4. CTA force and editorial rhythm where the source is deliberately punchy;
5. plain-language clarity where the source is explanatory;
6. the authored visual hierarchy across physical viewports;
7. the same public-surface, licensing and canonicality boundaries in the README.

A shorter native sentence is preferred to a literal translation that reads like translated English. A
more elegant sentence is never allowed to make a benchmark claim stronger than its committed evidence.

The extended locale packs are **model-curated and source-controlled**, not Google Translate output and
not runtime generation. They are deliberately **not** labelled as human-reviewed. A qualified bilingual
human can later add that assurance only after actually reviewing the relevant locale.

## Runtime boundary

`site/src/assets/i18n.js` performs deterministic presentation only:

- resolve locale;
- update document language, title and description;
- apply committed exact phrases and parameterized templates;
- observe later DOM updates from the proof renderer and Browser Lab;
- expose `window.__CMPCT_I18N__` for validation;
- record visible authored English copy that lacks a curated transformation.

It contains no network translation endpoint and no runtime generative fallback. Missing copy remains a
release defect instead of being papered over by lower-quality machine translation.

Source-order locale packs add another invariant: one physical translation line corresponds to one
canonical English phrase. `makePhraseMap()` refuses a locale if its phrase count no longer matches the
English source, so a source-copy edit cannot silently shift every following translation onto the wrong
sentence.

## Human-facing README localization

`README.md` in English remains the canonical repository introduction. Every non-English supported locale
has a directly linked static Markdown adaptation under `docs/readme/README.<locale>.md`.

Those variants must preserve the current project authority markers and evidence-bearing facts, including:

- project/core version;
- canonical on-disk format revision;
- surface revision;
- current benchmark headline and known losses;
- research-frontier vs canonical-reader distinction;
- executable quick-start commands;
- version discipline;
- public-surface restrictions;
- proposed-vs-adopted license status.

The localized README may compress repetitive explanatory prose when that makes the target language more
natural, but it may not omit a decision boundary, material caveat or evidence-bearing number. Links from
the translated README to the website preserve the chosen locale through `?lang=`.

## Verification

`site/tests/i18n-contract.mjs` checks:

- at least 20 supported locales;
- catalogue completeness and source-order integrity;
- parameter placeholder parity;
- protected technical terms;
- implausible compact-copy expansion;
- accidental unchanged English prose except narrow technical loanwords;
- absence of known runtime translation-provider endpoints;
- Chinese script-aware locale routing;
- localized README existence, discoverability and current v0.29/r24/0.29.k/evidence markers.

`site/tests/i18n-viewport.mjs` automatically renders **every non-English supported locale** in Chromium at
three translation-stress geometries: compact phone, landscape phone and short laptop. With the current 19
non-English locales this is **57 localized render cases**. Each case fails on horizontal overflow, an
unusable language control, an untranslated hero, an incorrect document language, an incomplete runtime
locale list or any currently visible authored English string reported as missing. Full-page screenshots
and a machine-readable report are retained as CI artifacts.

The existing English physical viewport matrix remains authoritative for general composition. The locale
matrix is additive and specifically attacks localization regressions such as long Finnish/German strings,
compact CJK typography, header pressure and dynamic evidence leakage.

## Updating public copy

When English site or human-facing README copy changes:

1. change the canonical English source normally;
2. add/update the matching site phrase or dynamic template for every supported locale;
3. update the localized README variants when the human-facing narrative or evidence changes;
4. preserve benchmark qualifiers exactly in meaning, especially losses and semantic-parity caveats;
5. run the catalogue/README contract;
6. build/enhance the site and run both the base and locale Chromium matrices;
7. inspect localized screenshots, not only green exit codes;
8. advance `SURFACE_REVISION` only when the coherent presentation milestone warrants it.

If a new benchmark introduces public prose that the locale catalogue does not know, locale CI is expected
to fail. That failure is intentional: benchmark evidence should not arrive in one language while the rest
of the public proof surface pretends to be localized.

## What automation cannot prove

Automation can prove completeness, source alignment, protected terms, placeholders, authority markers and
physical layout. It cannot prove that every sentence is elegant, culturally natural or preferred by a
native technical editor. The committed packs and README variants exist precisely so those qualities can
be audited directly against the canonical English source.

Do not label a locale **human reviewed** unless a qualified human actually reviewed it.
