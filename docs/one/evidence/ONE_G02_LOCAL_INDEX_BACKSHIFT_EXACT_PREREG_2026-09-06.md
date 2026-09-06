# ONE-G0.2 tombstone-free exact local-index A/B — preregistration

Date: 2026-09-06
Experimental line: ONE-G0.2
Authority: `research/cmpct1`

## Mission Lock

The exact 64-entry local nomination ring performs approximately one scalar key comparison per input byte on mature measured rows. A 128-bucket open-address locator preserved semantics and won on the smallest rows, but its tombstone deletion accumulated probe debt and became 1.72x–2.27x slower by size median at mature sizes. Saturation-triggered rebuild did not solve the cause.

The next question is deliberately narrow: can the exact same key -> authoritative-ring-slot mapping be maintained with open addressing **without tombstones or rebuild policy**, so ordinary misses remain bounded by the live cluster rather than historical deletions?

## Competing hypotheses considered

1. **Tombstone threshold/rebuild tuning:** rejected before implementation because it preserves the failure mechanism and merely moves the crossover.
2. **Sorted auxiliary map / binary search:** lookup is bounded, but every miss/insertion would require ordered maintenance; likely exports O(64) movement at the same 64-byte cadence.
3. **SIMD/fingerprint filtering of the authoritative ring:** attractive and more regular, but first test whether the already-small exact hash map failed only because deletion semantics were poor. This remains the next family if tombstone-free hashing fails.

## Frozen arms

Both arms:

- scan identical bytes and update identical Gear state;
- issue local lookups at exactly the same 64-byte cadence;
- suppress run-dominated windows identically;
- retain the same authoritative 64-entry circular ring;
- insert only after a miss;
- return exactly the same prior start on every hit;
- change no ONE reader operation, Law, wire byte or format.

**Baseline:** current linear search of the live 64-entry ring.

**Candidate:** 128-bucket linear-probed locator with only EMPTY/OCCUPIED states. Eviction removes the old key with **backward-shift deletion**: subsequent occupied buckets whose probe path crosses the hole move backward until the first empty bucket. There are no tombstones, no tombstone threshold and no table rebuild operation.

The ring remains authoritative storage. The locator is only a creation-time accelerator and may never alter a hit/miss/prior decision.

## Frozen matrix

Use the same generator-distinct matrix as the preceding exact-hash experiment:

- relation sizes: 4, 8, 16, 64 and 256 KiB;
- seeds: 7, 29 and 53;
- `shift_plus1`;
- `damage_quarter`;
- `fragmented_every96`;
- `hostile_fixed_bands`;
- `fragmented_every32`;
- `independent_random`;
- `cyclic_local_hits`.

Retain the independently generated low-bucket-collision key stream. It is an exactness/complexity hostile case and must not be removed if it makes the candidate look bad.

## Measurements

Record per row:

- exact hit/miss/prior-position checksum parity;
- lookup events and hits;
- baseline key comparisons;
- candidate bucket probes;
- candidate backward-shift moves;
- candidate maximum probe length;
- baseline/candidate state bytes;
- alternating A/B-B/A native elapsed.

All input scanning, Gear work, deletion and shift work are charged inside the native timing boundary. No Python loop is part of timed lookup execution.

## Disproof / promotion law

Semantic gates are hard:

- zero decision mismatches;
- identical hit count and live-entry count;
- capacity never exceeds 64 live ring entries;
- candidate fails closed on internal inconsistency.

Advance to fused-consumer integration only if semantics are exact and all of these hold:

- aggregate candidate probes <= **0.30x** baseline key comparisons;
- elapsed candidate/baseline size medians <= **0.90x** for relation sizes >=16 KiB;
- no measured row > **1.03x**;
- candidate fixed state <= **2.5x** baseline local-ring state.

If semantics pass but performance fails, retire this tombstone-free open-address shape rather than adding corpus/size dispatch. The next allowed family is a more regular authoritative-ring search accelerator (SIMD/fingerprint/set-associative filtering), not another open-address maintenance threshold.

## Claim boundary

A pass would prove only that exact local-ring lookup can be accelerated in isolation without historical deletion debt. The subsequent required gate is integration into the native fused nomination consumer with all observer carrying cost charged.
