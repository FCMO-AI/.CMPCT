# ONE-G0.2 — unmixed Gear-difference phase certificate preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2
Parent structural result: `ONE_G02_GEAR_DIFFERENCE_PHASE_CERTIFICATE_RESULT_2026-09-05.md`.

## Mission Lock / Referee

The prefix-difference token `L_s = P_{s+7} - 2^8 P_{s-1} (mod 2^64)` is proven content-local on the frozen matrix and preserves all required nominations when passed through `_mix64`. Native decomposition of the rejected raw-word certificate found phase hashing to be a substantial near-co-dominant cost stage (~0.56–0.71 ns/input-byte on large controls).

This experiment asks whether `_mix64` contributes useful discovery structure or merely permutes an already-diffuse 64-bit Gear-derived token.

## Frozen candidate

Keep everything from the successful Gear-difference certificate unchanged except the witness ranking key:

- stride 32;
- phases `{0,1,2,30,31}`;
- K=4 per phase;
- target phase 0;
- exact 8-byte equality before nomination;
- exact safe relation proof remains authoritative;
- state ceiling 280 B.

Control key: `mix64(L_s ^ 0x9E3779B97F4A7C15)`.
Candidate key: **`L_s` directly**.

The candidate does not claim that raw Gear-difference values are cryptographic hashes. They are writer-side discovery ranking tokens only; exact byte equality and exact relation proof remain downstream.

## Frozen cohort

Reuse the exact successful Gear-difference structural matrix: sizes 4/8/16/64/256 KiB, seeds 11/37/59, and all seven cases (`shift_plus1`, `damage_quarter`, `fragmented_every96`, `hostile_fixed_bands`, `prior_certificate_targeted`, `fragmented_every32`, `independent_random`).

## Falsifiable hypothesis

Removing `_mix64` will preserve every exact-positive nomination and produce zero independent-random false nominations on the frozen matrix, while preserving the Gear-difference identity and sampled-position/state bounds.

## Frozen gate

Advance the unmixed token to native A/B only if:

- zero Gear-difference identity failures;
- zero required-positive misses;
- zero independent-random false nominations;
- maximum sampled-position fraction <=0.19;
- modeled state <=280 B;
- pre-existing ONE semantic/hostile tests pass first.

This gate deliberately does **not** require witness-tuple equality with the mixed control: removing the bijective mix changes bottom-K ordering. It requires preservation of the externally relevant discovery contract instead.

## Disproof / next move

If the candidate misses any required positive or creates any independent-random nomination, retire the unmixed ranking on this frozen geometry; do not add phases/K post hoc. Proceed with native cost work on the already-passing mixed Gear-difference certificate.

If it passes, native cost should compare promoted observer baseline, rejected raw-word/mixed certificate, Gear-difference/mixed, and Gear-difference/unmixed. That will measure whether algebraic reuse can remove both the rolling-word and phase-mix stages in the real fused loop.

No density, reader-speed, format, product, v0.29, or deferred-v0.30 claim follows.