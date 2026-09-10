# ONE-G0.2 fused cache versus native fresh observer — result

Date: 2026-09-09 America/Mexico_City  
Experimental version: **ONE-G0.2**  
Decision: **DEMOTE_CACHE_PROMOTE_NATIVE_BASELINE**

## Exact hosted authority

- branch: `research/cmpct1`
- exact evidence source: `0b4aabbd5e35d6903ed59f524ac9219b82787737`
- workflow: `CMPCT1 ONE-G0.2 cache vs native fresh observer`
- scientific run: `34429523923`
- job: `102721864182`
- artifact: `10133958562`
- artifact name: `one-g02-cache-vs-native-fresh-0b4aabbd5e35d6903ed59f524ac9219b82787737`
- artifact digest: `sha256:4c7dba3017c5b1eadeac89424fc2b788563d6b59ce0a51b98ce184b5882d066d`
- inherited native/cache/cost-ledger semantic suite: **43 passed**

A duplicate push/PR run (`34429528332`) was cancelled during dependency installation and is not evidence. The result-bearing run above completed the semantic suites and frozen falsifier, then intentionally exited non-zero because the preregistered scientific decision was demotion rather than ADVANCE; its artifact was retained successfully.

## Mission lock

Earlier fused-cache experiments showed large speedups against the Python fresh observer. Once a semantically equivalent native fresh observer became available, that comparator was no longer competent enough to justify carrying persistent incremental state.

The frozen question was therefore whether the existing positional fused cache still produced a material current-version observation advantage over native fresh observation on identical bytes and exact ONE observation semantics.

Frozen gates required:

- exact cache/native Observation parity;
- exact-repeat and one-block sparse edit median wall/CPU <= `0.90x` native;
- dispersed eight-block edit <= `0.95x` native;
- no productive row above `1.05x`;
- shifted-insertion hostile control <= `1.25x`;
- persistent cache payload <= `0.20x` base-root bytes.

No gate was changed after results were visible.

## Result

Semantic parity remained exact, but the economic thesis failed decisively.

- semantic gates: **PASS**;
- payload gate: **FAIL**;
- productive timing gates: **FAIL**;
- shifted-control gate: **FAIL**;
- frozen decision: **`DEMOTE_CACHE_PROMOTE_NATIVE_BASELINE`**.

Representative cache/native CPU ratios:

| scale/family | exact repeat | one-block edit | eight-block edit | shifted insert control | persistent payload/root |
|---|---:|---:|---:|---:|---:|
| 256 KiB structured | 1.543x | 1.859x | 4.335x | 10.799x | 0.23068x |
| 256 KiB random | 2.183x | 2.858x | 8.051x | 25.895x | 0.16650x |
| 256 KiB compressed-like | 1.760x | 2.260x | 5.886x | 18.142x | 0.16650x |
| 1 MiB structured | 1.515x | 1.601x | 2.299x | 10.457x | 0.23057x |
| 1 MiB random | 2.146x | 2.312x | 3.687x | 25.529x | 0.16650x |
| 1 MiB compressed-like | 1.748x | 1.916x | 2.871x | 18.728x | 0.16650x |

The cache lost even on exact repeats where no feature blocks were recomputed. For example, at 1 MiB structured exact-repeat, the cache spent ~20.56 ms CPU versus ~13.57 ms for native fresh observation despite reusing all 256 cached blocks. At 1 MiB random exact-repeat it spent ~15.13 ms versus ~7.05 ms native.

Sparse changes become progressively worse because validation, cache integrity, feature-payload reads and Python-side changed-block handling remain while the fresh native observer simply performs a very fast bulk pass. Shifted insertion is particularly hostile to the positional cache: roughly half the blocks lose positional identity, producing 10–26x regressions versus native fresh observation.

## Causal interpretation

This falsifies the current cache shape as the preferred **general observer-speed path**. The old cache wins were substantially confounded by bypassing Python interpreter work. Once the same fresh-observation semantics run natively, persistent positional state is not free enough to repay validation/integrity/replay overhead.

The result is valuable because it removes architecture rather than adding it:

> For ordinary current-version observation, use the competent native fused fresh pass unless a future cache design proves a real marginal-information-yield advantage against that baseline.

This does not falsify incremental computation in principle. A compact native cache, a changed-cone authority supplied by a transactional storage layer, or a workload where change locality can be known without rescanning/validating the complete object may reopen ONE-07. The current Python positional cache must not be carried merely because earlier experiments against Python fresh observation were green.

## State / traffic truth

The persistent state limit also failed on the structured family:

- 256 KiB structured: `60,472 B`, **0.230682x** root size;
- 1 MiB structured: `241,768 B`, **0.230568x** root size.

Random/compressed-like rows remained around **0.166504x**, but timing still lost materially. The cache continues to validate the current bytes and charge cache-integrity work; none of those costs should be hidden to manufacture an incremental-computation win.

## Hostile reviewer / regression debt

1. **Do not threshold-rescue the present cache from this matrix.** The losses are broad, causal and large.
2. **Do not delete the cache research.** It remains durable negative evidence and a useful oracle for future native/compact changed-cone designs.
3. **Do not infer that all persistent discovery state is useless.** Prior-version indices may still earn their bytes when they remove expensive search beyond the cheap native observation pass; that must be proven separately.
4. **Do not compare future cache work to the Python observer.** `ADVANCE_NATIVE_FRESH_OBSERVER` makes the native implementation the competent general baseline.
5. **The workflow currently duplicates push and PR execution under different concurrency groups.** This is CI-compute debt, not scientific evidence.

## Comparator / Genesis status

Frozen Genesis authorities remain unchanged:

- v0.29: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`;
- deferred v0.30: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`.

No September 11 gate corpus was encoded or scored in this experiment.

## Next decisive action

Promote native fresh observation into the charged research-writer envelope and measure total writer cost with root hashing, relation admission, segmentation, Program construction, validation and canonical emission intact. In parallel, keep ONE-07 open only for causally different incremental designs whose source/change authority lets them avoid enough work to beat this native baseline after state, integrity and invalidation are charged.
