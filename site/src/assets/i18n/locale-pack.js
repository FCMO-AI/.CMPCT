/* CMPCT compact curated locale-pack helper — Surface 0.29.i.
   Footnote: extended locales store one reviewed translation per canonical English phrase in the exact
   SOURCE_PHRASES order. The factory refuses length drift, so adding/removing English copy forces every
   extended language pack to be updated explicitly instead of silently shifting translations. */
export function makePhraseMap(sourcePhrases, values, locale) {
  if (!Array.isArray(values) || values.length !== sourcePhrases.length) {
    throw new Error(`CMPCT locale ${locale}: expected ${sourcePhrases.length} curated phrases, got ${values?.length ?? "non-array"}`);
  }
  return Object.freeze(Object.fromEntries(sourcePhrases.map((entry, index) => [entry.en, values[index]])));
}

export function phraseBlock(block) {
  // Footnote: blank lines are significant defects rather than formatting; trimming only the outer block
  // keeps one physical source line equal to one canonical phrase and makes reviews/counting straightforward.
  return String(block).replace(/^\n|\n$/g, "").split("\n");
}
