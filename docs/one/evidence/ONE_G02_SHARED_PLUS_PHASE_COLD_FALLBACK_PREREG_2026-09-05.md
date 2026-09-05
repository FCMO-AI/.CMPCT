# ONE-G0.2 — shared observer + sparse phase cold fallback preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2

## Mission Lock

Two facts are now established:

1. the already-paid shared Gear/reuse observer is structurally useful but has small-root blind spots;
2. the unchanged sparse bounded-shift phase certificate is not a complete standalone nominator: one 4 KiB quarter-damage positive was missed because all four content-ranked witnesses for the relevant phase landed inside the damaged region.

The intended ONE architecture is opportunity-gated. Therefore the next falsifiable question is **complementarity**, not standalone perfection: can the unchanged sparse phase certificate run only when the shared observer is silent and recover every economically valid relation opportunity in a generator-distinct envelope?

## Frozen cascade

For each source/target pair:

1. run the existing shared observer and record whether it emits cross-object exact-reuse evidence;
2. if and only if shared evidence is absent, run the unchanged phase certificate from `one_g02_bounded_shift_phase_certificate_validation.py`;
3. nomination is `shared OR cold_phase`;
4. the exact safe relation dispatcher remains the oracle and sole Law authority.

No phase-certificate parameter changes are permitted: stride 32, 8-byte words, source phases `{0,1,2,30,31}`, target phase 0, four witnesses per source phase, 240-byte transient fallback state.

The phase certificate is replayable from fixed input positions; unlike the retired late-minimizer rescue, it does not require state that disappeared before activation. This experiment explicitly records fallback activations and sample work to verify that property rather than assuming it.

## Frozen validation envelope

Sizes: 4, 8, 16, 64 and 256 KiB.

Generator-distinct seeds: 13, 43 and 67.

Cases:

- ordinary +1 shift;
- contiguous quarter damage;
- mutation every 96 bytes;
- four fixed-band hostile edits;
- prior rolling-certificate-targeted hostile case;
- mutation every 32 bytes;
- independent-random negative.

## Frozen structural gate

Advance the **cascade** to native carrying-cost measurement only if:

- every exact-relation positive is nominated by `shared OR cold_phase` at every size and seed;
- every positive missed by shared observation alone is recovered by the unchanged phase fallback;
- independent-random negatives remain unnominated by the combined cascade;
- phase fallback is never executed on rows where shared evidence already nominates the pair;
- fallback sampled positions remain <=19% of source bytes whenever activated;
- fallback state remains exactly 240 bytes and is transient, not continuously retained;
- the existing ONE semantic/hostile suite remains green.

`fragmented_every32` may still reach the phase nominator even though exact relation is rejected; this is not hidden. Such rows must be counted as cascade false nominations and passed to the already-existing sparse relation falsifier in the next native experiment. If that added proof pressure erases the compute win, the cascade fails there.

## Disproof

Any positive missed by both signals falsifies this exact composition. Any independent-random combined nomination falsifies its current false-pattern discipline. Do not increase witness count, adjust stride/phases, or weaken hostile cases after seeing the result.

A pass grants only the next native-cost experiment. It does not promote a writer path, stored-byte claim, reader claim, canonical format change, or comparator victory.