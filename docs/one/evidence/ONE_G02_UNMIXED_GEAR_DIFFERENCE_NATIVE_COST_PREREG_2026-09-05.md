# ONE-G0.2 — unmixed Gear-difference native carrying-cost preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2
Structural parent: `ONE_G02_UNMIXED_GEAR_DIFFERENCE_CERTIFICATE_RESULT_2026-09-05.md`.

## Mission Lock / Referee

The direct Gear-difference token `L_s` preserves the frozen structural nomination contract without `_mix64`. Separately, the mixed Gear-difference native A/B is already frozen and executing; this preregistration is written without consuming its timings.

The question here is narrower and causal: after the rolling raw-byte word has been algebraically eliminated, can removing the extra phase mix eliminate a further material fraction of writer carrying cost while keeping the exact discovery contract independently verified?

## Frozen variants

Compile from the same source and compiler flags:

1. promoted observer baseline;
2. rejected raw-word/mixed certificate;
3. Gear-difference/mixed certificate;
4. **Gear-difference/unmixed** candidate, identical to (3) except the bottom-K ranking key is `L_s` directly rather than `mix64(L_s ^ constant)`.

All variants retain the same five phases `{0,1,2,30,31}`, stride 32, K=4, exact bottom-K tie semantics, observer work, and no payload rescan. The candidate state remains **280 B**.

Before timing counts, native mixed and unmixed tuples must each equal their own independent Python structural references. Tuple equality between mixed and unmixed is neither required nor expected because the ranking order changes.

## Frozen controls

Reuse the carrying-cost cohort unchanged:

- random 1 MiB;
- zlib-compressed random ~1 MiB;
- repeated-basis 1 MiB;
- shifted/versioned 1 MiB;
- zero 1 MiB;
- alternating-byte hostile 1 MiB;
- random 4 KiB;
- random 64 B.

Use paired alternating timing rounds. Report `unmixed/mixed`, `unmixed/raw`, and `unmixed/baseline` for every row.

## Falsifiable hypothesis

Removing the phase mix will reduce the five-large median native elapsed by at least **10%** versus Gear-difference/mixed, with no >3% regression on any ~1 MiB control.

## Frozen stage gate

Advance the unmixed native candidate only if all are true:

- zero mixed-reference witness mismatches;
- zero unmixed-reference witness mismatches;
- five-large median `unmixed/mixed <= 0.90x`;
- every ~1 MiB `unmixed/mixed <= 1.03x`;
- 4 KiB `unmixed/mixed <= 1.05x`;
- 64 B `unmixed/mixed <= 1.10x`;
- state <=280 B;
- pre-existing ONE semantic/hostile tests pass first.

The original unconditional carrying-cost authority remains `candidate/baseline <=1.12x` on the five-large median. A local `unmixed/mixed` pass does not promote the certificate if that original product-facing gate remains red.

## Disproof / next move

If structural exactness fails, invalidate the candidate regardless of timing.

If exactness holds but the 10% stage gate fails, `_mix64` removal is not a material native repair and should not receive more local tuning. If it passes but the original 1.12x baseline gate remains red, further work must eliminate a stage or make certificate construction opportunity-gated; do not reduce phases/K on this cohort.

No density, reader-speed, format, product, v0.29, or deferred-v0.30 claim follows.