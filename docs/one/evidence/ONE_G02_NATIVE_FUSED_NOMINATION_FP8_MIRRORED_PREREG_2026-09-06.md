# ONE-G0.2 native fused nomination + mirrored fp8 local view — preregistration

Date: 2026-09-06
Branch: `research/cmpct1`
Experimental line: `ONE-G0.2`
Mission Lock source boundary: current `benchmarks/one/one_g02_fused_native_nomination_kernel.c` (blob `89f25972374c747654ddbf631372929b3f21b970`) plus the already-validated local fp8 representation in `benchmarks/one/one_g02_local_index_fingerprint_view_kernel.c` (blob `00af27f2025e4be4bad92a2e5705cb7f91680584`).

## Referee / falsifiable hypothesis

The fused nomination consumer's 64-entry local first-witness ring performs enough full 64-bit key work to own a material fraction of native elapsed time. Adding the already-validated 128-byte mirrored fp8 rejection view to that exact local ring, while leaving the full keys as sole authority, will reduce whole-consumer elapsed without changing any Gear/minimizer event, local prior, nomination, relation audition, global-index behavior, or downstream semantic result.

Disproof: the candidate is rejected as speed work if semantics differ, if collision/wrap/newest-prior hostile cases differ, if mature productive median whole-consumer elapsed is >0.95x baseline, if any productive row exceeds 1.03x, or if negative/control median exceeds 1.03x. Full-key comparison reduction is diagnostic only and cannot promote the candidate.

## Frozen A/B boundary

Baseline is the exact current fused consumer implementation: offset-only minimizer observation, 64-entry authoritative local ring, demand-grown global index with 64-entry initial allocation and exact 8,192-entry cap, identical audition/proof behavior, and identical emitted anchor trace.

Candidate differs only at local-ring lookup and maintenance:

- retain all 64 full `uint64_t` keys and their starts/used bits as authority;
- add `uint8_t local_fp[128]`, a mirrored view of 64 fp8 values;
- fp8 is exactly `(uint8_t)(key >> 56)`, matching the promoted isolated experiment;
- scan the logical local-ring interval with `memchr` over the mirrored view;
- a fingerprint mismatch skips the full-key check;
- a fingerprint match MUST still compare the authoritative full key;
- on insertion/eviction update both `local_fp[slot]` and `local_fp[slot + 64]`;
- charge the full +128 B state inside `reserved_state_bytes`;
- do not touch the global demand-grown index.

No reader, wire-format, Law grammar, Surprise semantics, locality, integrity, recovery, portability, or resource-cap change is permitted.

## Measurement discipline

Timing must include fp8 generation/maintenance. Prefer one native timed batch boundary using `CLOCK_MONOTONIC_RAW`, with A/B then B/A ordering to reduce drift. Python may orchestrate compilation, inputs, semantic checks, aggregation, and artifacts, but Python↔C call overhead must not be the measured hot boundary.

The harness must compare baseline and candidate on the same bytes, Gear table, window, minimizer span, boundary and trace capacity. It must reject any mismatch in return code, emitted trace, final state, positions considered, cross auditions/exact relations, verification/extension read accounting, local/global peak entries, and all other shared semantic/resource counters except the intentional +128 B candidate state and candidate-only diagnostic lookup counters.

The local-ring decision stream must additionally be checked with a checksum or equivalent exact event-level audit so that a downstream coincidence cannot hide a changed `prior`.

## Frozen workload matrix

Productive relation families: `shift_plus1`, `damage_quarter`, `fragmented_every96`, `fragmented_every32`, and a hit-rich local-reuse stream. Controls/hostiles: `independent_random`, false-pattern/no-relation input, deliberate fp8 collisions with distinct full keys, >64 insert wrap/eviction, and repeated identical keys that require newest/authoritative prior semantics exactly as baseline defines them.

Sizes: 4, 8, 16, 64, and 256 KiB where the family is meaningful. Seeds: 7, 29, and 53. Inputs and semantic conditions may be inherited exactly from existing ONE-G0.2 harness generators; no weakening after results.

## Promotion law

Advance the fp8 mirrored view into the fused discovery baseline only if all of the following hold on the exact-source run:

1. zero semantic/event/prior/nomination mismatches;
2. collision-hostile and wrap/newest-prior audits exact;
3. +128 B candidate state charged;
4. mature productive whole-consumer median ratio <= 0.95x;
5. no productive row > 1.03x;
6. negative/control median ratio <= 1.03x;
7. normal ONE semantic/hostile tests remain green.

A failure is preserved as negative evidence. Thresholds, workload membership, locality, proof semantics, or resource caps must not be changed post hoc to rescue the candidate.

## Hostile Reviewer pre-commit critique

The strongest expected failure is that the isolated local lookup's ~23% speedup owns too little of the fused consumer, exactly as the witness-deferral experiment eliminated ~83% of relation-specific traffic yet delivered ~0.994x native elapsed. A second failure mode is that `memchr` setup and fp maintenance erase the benefit on tiny or hit-heavy streams. A third is that high fp8 collision density collapses the filter to baseline-like full-key work. All three are legitimate falsifiers, not reasons to add thresholds.
