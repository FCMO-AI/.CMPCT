# r25 serialized candidate reclaim RSS result

Status: **accepted Forge R0 causal evidence / scoped negative / no release credit**

This record preserves the result of the frozen experiment in `docs/v030-rnd/R25_CANDIDATE_RECLAIM_RSS_PREREG.md`. The experiment asked whether generic Python garbage collection or allocator-page reclamation after PrefixGraph completion materially lowers the complete-process Shifted peak while retaining the exact PrefixGraph result for later winner selection.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`;
- exact source head: `5f2633c016304f4743359fb841727c10c85628b6`;
- workflow: `CMPCT v0.30 candidate reclaim RSS attribution`;
- workflow run: `33609963936`;
- substantive job: `100182642770` (`candidate-reclaim-rss`);
- artifact: `v030-r25-candidate-reclaim-rss-5f2633c016304f4743359fb841727c10c85628b6`;
- artifact id: `9839034196`;
- artifact ZIP SHA-256: `8b5bdc6eabbf1d23fd034e036a6074d43af4734899644dfe12c150e2de3797c6`;
- schema: `cmpct-v030-r25-candidate-reclaim-rss-v1`;
- experiment valid: `true`;
- repetitions: exactly 3 per arm;
- worker failures: 0;
- release credit: false.

The substantive job checked out the exact source SHA, compiled the frozen instrument, ran all nine fresh-process measurements, ratcheted the frozen claim boundary, passed the CI-topology self-check and uploaded the evidence artifact. This is not classifier-only evidence.

## Exact result

| arm | median complete-process peak RSS | median wall time | median pre-action VmRSS | median post-action VmRSS | median live-RSS drop | retained PrefixGraph Python object census |
|---|---:|---:|---:|---:|---:|---:|
| control | **422,760 KiB** | **67.391 s** | 264,412 KiB | 264,412 KiB | 0 KiB | 1,764 B |
| `gc.collect()` | **423,564 KiB** | **67.502 s** | 265,004 KiB | 265,004 KiB | 0 KiB | 1,764 B |
| `gc.collect()` + `malloc_trim(0)` | **423,152 KiB** | **69.011 s** | 264,848 KiB | **110,852 KiB** | **153,996 KiB** | 1,764 B |

Frozen derived quantities:

- GC peak reduction fraction: **0.0**;
- GC entry reclaim fraction: **0.0**;
- allocator-trim peak reduction fraction: **0.0**;
- allocator-trim entry reclaim fraction: **0.3642634119**;
- retained-result fraction by recursive Python `sys.getsizeof`: **0.0000040748** of the control peak.

Frozen decision: **`GENERIC_RECLAIM_RETIRED_AS_PRIMARY`**.

Every valid arm retained the same final selected archive identity, selected representation, physical SHA-256, format revision, r24/r25 complete-product prices and strongly verified canonical filesystem tree. Candidate semantics, selection, grammar, locality, recovery and release thresholds were unchanged.

## Causal interpretation

The result separates **live allocator residency** from **complete-process high-water ownership**.

`malloc_trim(0)` proves that a large amount of allocator-owned memory is returnable after PrefixGraph completion: median live `VmRSS` falls by **153,996 KiB**, about **36.43% of the control process peak**. That fact is real and potentially useful for steady-state residency.

However, reclaiming those pages does **not** reduce the subsequent complete-process `ru_maxrss` at all. The trim arm peaks slightly above control, and GC alone likewise provides no peak benefit. Under the frozen decision law, generic post-PrefixGraph reclamation therefore cannot be the primary explanation or primary release-RSS repair.

The most important implication is temporal: the ~423 MiB high-water is either already reached before the reclaim point, or later live work recreates/exceeds it after reclamation. A large post-PrefixGraph live-RSS drop must not be narrated as a peak-memory fix when the authoritative peak metric remains unchanged.

The retained Python return object is also far too small by ordinary recursive Python ownership accounting to explain the peak directly. The 1,764 B census does not include native allocations or external buffers referenced indirectly, so it is a scoped diagnostic rather than a proof that the result has zero native carrying cost.

## Scoped negative constraint

For the exact repaired Shifted target, exact canonical semantic owners and frozen serialized PrefixGraph-before-G0-G4 seam:

1. Python cyclic-GC reclamation after PrefixGraph completion is not a material peak-RSS intervention;
2. generic glibc allocator trimming after PrefixGraph completion is not a material peak-RSS intervention, despite a large immediate live-RSS reduction;
3. do not promote `gc.collect()`, `malloc_trim(0)` or an equivalent generic post-candidate reclaim hook as the Shifted peak-RSS fix on this evidence;
4. do not use the large `VmRSS` drop as release credit; complete-process peak remains authoritative.

This does **not** prove allocator retention is irrelevant to steady-state memory, nor that candidate-process isolation cannot help. It says the tested between-candidate reclaim point cannot lower the complete-process high-water under this exact product composition.

## Reopening predicate

Reopen generic post-PrefixGraph reclamation as a primary peak-RSS hypothesis only if one of the following changes materially:

- the product/candidate execution order changes so the current high-water-producing work no longer precedes or follows the reclaim point;
- a phase-resolved exact measurement proves the release high-water occurs specifically because reclaimable pages overlap a later live allocation class and a portable intervention prevents that overlap;
- candidate/process isolation changes the lifetime boundary and demonstrates a material **system peak** reduction while preserving exact product bytes and exposing its wall-time/platform cost.

A lower live `VmRSS` after the same high-water has already been reached is not a reopening predicate.

## Forge decision and next decisive test

**Retire generic between-candidate reclamation as the primary Shifted peak-RSS repair.**

The next R0 experiment should resolve *when* the high-water is created under shipping-equivalent product composition, rather than try another reclaim primitive. Instrument exact r24, PrefixGraph, G0-G4 and final publication/verification boundaries with fresh-process phase receipts and live RSS, while preserving exact selected bytes/tree. The decisive question is whether the peak is owned by one build phase, an overlap between independently necessary phases, or cumulative product-process lifetime.

If phase attribution shows the required live state is individually bounded but cumulative lifetime creates the high-water, a subprocess/isolation R2 A/B becomes justified. If one exact phase itself reaches the high-water, optimize or redesign that phase instead of adding scheduler/reclamation complexity.
