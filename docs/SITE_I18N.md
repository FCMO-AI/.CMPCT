# CMPCT curated localization contract

Status: **public-surface quality gate** beginning with Surface `0.29.i`.

CMPCT localization is not runtime machine translation. English remains the canonical semantic source and
all supported translations are committed in source-keyed, review-sized locale packs under `site/src/assets/i18n/locales/`, assembled by `site/src/assets/i18n/catalog.js`.
The browser automatically chooses a supported locale from `?lang=`, a saved explicit choice, or the
browser language list, in that order. Unsupported languages fall back to English.

## Supported locales

- English (`en`) — canonical source;
- Latin American Spanish (`es-419`);
- Brazilian Portuguese (`pt-BR`);
- French (`fr`);
- German (`de`).

Adding a language is deliberately more work than adding a machine-translation provider. A locale is not
supported until its copy and layout pass the same public proof contract as English.

## Translation doctrine

Translate **intent**, not English syntax. A good CMPCT localization must preserve:

1. the authority level of every claim — research stays research, canonical stays canonical;
2. benchmark caveats and losses without softening or upgrading them;
3. numbers, version identities, codec names and protected technical terminology;
4. CTA force and editorial rhythm where the source is deliberately punchy;
5. plain-language clarity where the source is explanatory;
6. the authored visual hierarchy across physical viewports.

A shorter native sentence is preferred to a literal translation that reads like translated English. A
more elegant sentence is not allowed to make a benchmark claim stronger than its committed evidence.

## Runtime boundary

`site/src/assets/i18n.js` does only deterministic application:

- resolve locale;
- update document language, title and description;
- apply committed exact phrases and parameterized templates;
- observe later DOM updates from the proof renderer and Browser Lab;
- expose `window.__CMPCT_I18N__` for validation;
- record visible authored English copy that lacks a curated transformation.

It contains no network translation endpoint and no runtime generative fallback. Missing copy stays a
release defect instead of silently falling back to low-quality translation.

## Verification

`site/tests/i18n-contract.mjs` checks catalogue completeness, template placeholders, protected technical
terms, compact-copy expansion and the absence of known runtime translation-provider endpoints.

`site/tests/i18n-viewport.mjs` renders every non-English locale in Chromium at three stress geometries:
compact phone, landscape phone and short laptop. It fails on horizontal overflow, an unusable language
control, an untranslated hero or any currently visible authored string reported as missing. Screenshots
and a machine-readable report are retained as CI artifacts.

The existing 16-case physical viewport matrix remains authoritative for general composition. The locale
matrix is additive and specifically attacks localization regressions.

## Updating site copy

When English public copy changes:

1. change the English source normally;
2. add/update the matching catalogue entry or dynamic template for every supported locale;
3. preserve benchmark qualifiers exactly in meaning, especially new `known_losses` text;
4. run the catalogue contract;
5. build/enhance the site and run both the base and locale Chromium matrices;
6. inspect localized screenshots, not just green exit codes;
7. advance `SURFACE_REVISION` only when the coherent presentation milestone warrants it.

If a new benchmark introduces prose that the current catalogue does not know, locale CI is expected to
fail. That failure is intentional: benchmark evidence should not arrive in one language while the rest
of the public proof surface pretends to be localized.

## What the tests cannot prove

Automation can prove completeness, protected terms, placeholders and physical layout. It cannot prove
that a sentence is elegant or culturally natural. The committed source-keyed locale packs exist so a
bilingual reviewer can audit those qualities directly against the canonical English keys. Do not label a locale “human reviewed” unless a
qualified human actually reviewed it.
