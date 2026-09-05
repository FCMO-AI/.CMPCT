# ONE-G0.2 — Gear-difference fused native carrying-cost preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2
Parent structural evidence: `ONE_G02_GEAR_DIFFERENCE_PHASE_CERTIFICATE_RESULT_2026-09-05.md`.

## Mission Lock / Referee

The mixed Gear-difference certificate preserved all required structural nominations with zero algebra-identity failures and zero independent-random false nominations. The rejected raw-word fused certificate was exact but cost 2.7600x the promoted observer on the five-large median.

This experiment asks whether deriving the same class of content-local relation evidence from the already-live prefix Gear state removes a material fraction of that writer cost in native code.

## Frozen implementations

Build all variants from one C source, one compiler invocation, and the same Gear table / exact bottom-K `offer()` implementation:

1. **baseline** — promoted observation control: run tracking + prefix Gear + anchor test;
2. **raw-mixed** — the exact rejected raw-word fused phase certificate from `df083da415fb8aa426c3f6a1ed84cd6d25f5e32d`;
3. **gear-difference-mixed** — no rolling raw-byte word. At each required phase event, derive the 8-byte content-local token from live prefix states as `L_s = P_{s+7} - 2^8 P_{s-1}` modulo 2^64, then apply the same `_mix64` and exact bottom-K maintenance.

The Gear-difference implementation retains five `uint64_t` prefix snapshots, one for each source start phase `{0,1,2,30,31}`. Snapshot 0 is initialized to the `P_-1 = 0` boundary state. Later snapshots are captured only on their five predecessor phases; no payload rescan or outgoing-byte load is permitted.

The candidate modeled incremental state is 280 B.

## Frozen controls and timing

Reuse the rejected raw-fused carrying-cost controls and repetition policy unchanged:

- random 1 MiB;
- zlib-compressed random ~1 MiB;
- repeated-basis 1 MiB;
- shifted/versioned 1 MiB;
- zero 1 MiB;
- alternating-byte hostile 1 MiB;
- random 4 KiB;
- random 64 B.

Before timing can count, the native Gear-difference witness tuples must equal the independent Python Gear-difference reference on every control. The raw control must still equal its independent raw-word reference.

Use paired alternating timing rounds for raw-mixed vs Gear-difference-mixed while also measuring baseline in each round.

## Falsifiable hypothesis

Algebraic observer reuse will reduce total fused carrying cost by at least **15%** versus the rejected raw-word certificate on the five-large median, without creating a >3% regression on any ~1 MiB control.

## Frozen stage gate

Advance Gear-difference native rehabilitation if all are true:

- zero raw-control witness mismatches;
- zero Gear-difference candidate witness mismatches;
- five-large median `gear/raw <= 0.85x`;
- every ~1 MiB `gear/raw <= 1.03x`;
- 4 KiB `gear/raw <= 1.05x`;
- 64 B `gear/raw <= 1.10x`;
- candidate state <=280 B;
- pre-existing ONE semantic/hostile tests pass first.

Always report `gear/baseline`. Passing this stage gate does **not** revive unconditional certificate carrying. If the five-large `gear/baseline` median remains above the original 1.12x product-facing carrying-cost gate, the unconditional path remains retired and further mechanism-level work elimination is required.

## Disproof / next move

If exactness fails, the candidate is invalid regardless of timing.

If exactness holds but the 15% stage gate fails, retire prefix-difference carrying as a direct compute repair; the algebra may remain useful for cold/opportunity-gated certificates.

If the stage gate passes but the original 1.12x baseline gate still fails, combine only with independently validated work elimination such as an unmixed `L_s` ranking token or opportunity-gated activation. Do not tune phase count/K on this cohort.

No density, reader-speed, format, product, v0.29, or deferred-v0.30 claim follows.