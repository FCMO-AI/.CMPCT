# ONE-G0.2 native fresh observer — result

Date: 2026-09-09 America/Mexico_City  
Experimental version: **ONE-G0.2**  
Decision: **ADVANCE_NATIVE_FRESH_OBSERVER**

## Exact hosted authority

- branch: `research/cmpct1`
- exact evidence source: `553e7205f889dc2bf2ffd71f0ac7652e7e458cfc`
- workflow: `CMPCT1 ONE-G0.2 native fresh observer`
- run: `34429421537`
- job: `102721547940`
- artifact: `10133903310`
- artifact name: `one-g02-native-fresh-observer-553e7205f889dc2bf2ffd71f0ac7652e7e458cfc`
- artifact digest: `sha256:3caa7a04e69f10ef43d11cee74a20bc104828f129cbfdb756f2e399ae24cdd4c`
- exact semantic suite: **27 passed**

The original evidence attempts at source `1ac8fcb00f9307b5719ccd862fc9cebfd825e919` were cancelled by workflow concurrency before producing admissible evidence. Source `553e720...` changes only a workflow comment to re-arm the already frozen lane; candidate implementation, benchmark, semantic contract and thresholds are unchanged.

## Mission lock / disproof test

The frozen question was whether the current Python fresh observer's exact ONE-G0.2 semantics could be transferred into one native bulk implementation without changing the discovered runs/reuse opportunities, statistics, retained-index accounting or reader-visible representation, while reducing both median wall and CPU to at most `0.25x` Python on every frozen row.

The matrix uses 64 KiB, 256 KiB and 1 MiB inputs across structured, seeded-random/incompressible, compressed-like, long-run and near-repeat families, with paired alternating timing and 15 repetitions per row.

## Frozen result

All semantic and timing gates passed.

- exact `Observation` parity: **PASS on all 15 rows**;
- exact observation statistics: **PASS on all 15 rows**;
- every wall ratio <= `0.25x`: **PASS**;
- every CPU ratio <= `0.25x`: **PASS**;
- median native/Python CPU: **0.037096x** (~26.96x faster);
- worst native/Python CPU: **0.076546x** (~13.06x faster);
- best native/Python CPU: **0.019508x** (~51.26x faster).

Largest-scale (1 MiB) CPU ratios were:

| family | native / Python CPU |
|---|---:|
| structured | 0.053394x |
| random | 0.025212x |
| compressed-like | 0.033045x |
| long runs | 0.076546x |
| near repeats | 0.023689x |

Representative 1 MiB absolute native CPU medians ranged from about **5.19 ms** (near repeats) / **5.40 ms** (random) to **16.33 ms** (long runs), versus roughly **213–219 ms** for the Python observer on the same rows.

## Interpretation

This is implementation-transfer evidence, not a new representation mechanism. The native observer returns the same ONE observation semantics and accounting while removing Python byte-loop overhead. It therefore becomes the competent fresh-observation baseline for subsequent writer-observation economics.

The result also changes how earlier fused-cache wins must be interpreted. The cache previously produced very large speedups against Python fresh observation, but Python fresh observation is now shown to be roughly 13–51x slower than the equivalent native implementation on this matrix. The earlier cache result therefore cannot by itself justify carrying persistent incremental state. The preregistered `ONE_G02_CACHE_VS_NATIVE_FRESH_OBSERVER` comparison is now decisive.

## Hostile review / remaining debt

1. `observe_native()` currently uses a ctypes input buffer copy before entering the C kernel. That copy is inside timed calls, so the speed result does not hide it, but the wrapper is not yet a zero-copy authority.
2. The observer reports semantic source/verification traffic inherited from the reference observer; this experiment does not prove physical DRAM or cache traffic with hardware counters.
3. No whole-writer, archive, density, selective-read or Genesis comparator advantage is claimed here.
4. A fast fresh observer can make persistent caching economically unnecessary. Cache research must now beat this result rather than the Python baseline.

## Comparator / gate status

Frozen Genesis authorities remain unchanged:

- v0.29: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`;
- deferred v0.30: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`.

No Genesis 15-workload encoding or scoring was executed.

## Next decisive action

Run the already-preregistered fused-cache versus native-fresh-observer falsifier without changing its productive or hostile gates. If the current cache loses, demote it as the preferred general observer-speed path rather than preserving state merely because it beat Python. If it wins, carry the result into the full authenticated ingest envelope and charge persistent state, re-seeding, peak RSS and source/memory traffic explicitly.
