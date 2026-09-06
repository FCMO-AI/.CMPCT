# ONE-G0.2 shared native writer transfer — terminal result

Date: 2026-09-06  
Branch: `research/cmpct1`  
Experimental line: `ONE-G0.2`

## Exact evidence

- source/head: `eafc17fe92a0f2c3f623382334d8d20f047c6b57`
- workflow: `ONE-G0.2 shared native writer transfer`
- run: `34051873091`
- job: `101536824153`
- artifact: `9994824613`
- artifact digest: `sha256:28d101847d00da5d7f037cce1e6860b94ef8c2a3a97ab85e2d264dbd78c5193e`
- frozen rounds: `31`

The Actions job is intentionally red at the falsifier step. Installation, the full ONE semantic/hostile suite, the independent native-writer max-nodes probe, and evidence upload all passed. The benchmark exited non-zero because the preregistered performance breadth gate failed.

## Correctness / reader truth

- semantic failures: **0**
- independent Segment-oracle failures: **0**
- malformed native-buffer probes: **PASS**
- independent max-nodes hostile probe: **PASS**
- canonical ONE0 wire: byte-identical to plan-direct V2 on every row
- exact reconstruction: PASS on every row
- stored bytes, Surprise bytes, hierarchy depth, node count and reader work/materialization: semantically unchanged relative to V2 for the same case

No reader opcode, wire grammar, root ordering, relation decision, resource limit or recovery/locality requirement changed.

## Frozen performance result

Mature productive candidate/V2:

- median: **0.2468426132473778x** (~75.32% elapsed reduction)
- rows <=0.90x: **11/15**
- worst: **0.9693553343068838x**

Mature controls:

- median: **0.9523258605330005x**
- worst: **0.9807975114417786x**

The preregistered gate required productive median <=0.80x, 15/15 mature productive rows <=0.90x, productive worst <=1.03x, control median <=1.03x and control worst <=1.08x. Every gate except breadth passed.

The four breadth misses are all `shift_plus1` with exactly two Segments:

| bytes | ratio candidate/V2 | baseline ns | native ns |
|---:|---:|---:|---:|
| 32,768 | 0.928137x | 93,789 | 87,049 |
| 65,536 | 0.942929x | 171,104 | 161,339 |
| 131,072 | 0.953848x | 327,246 | 312,143 |
| 262,144 | 0.969355x | 631,366 | 612,018 |

For contrast, the segment-rich productives are dramatically faster. At 262,144 B, `shift_plus1_damage_quarter` measured **0.243903x** with 516 segments and `fragmented_every96` measured **0.079719x** with 5,464 segments. The same qualitative split appears throughout the mature sizes.

## Decision

**`reject_shared_native_writer_transfer`** as the promoted shared native writer **as-is** because the frozen 15/15 breadth requirement was not met.

This is not evidence that native bounded ONE0 construction is economically weak. It is a breakthrough seed with explicit regression debt: segment-rich writer work collapses by roughly 4–12x relative to the Python plan/direct V2 while simple two-segment relations improve only modestly.

Do not rescue the rejected seed with workload, size, segment-count, Surprise-density or corpus dispatch. Any rehabilitation must make a causal, representation-independent change and re-run the original gate unchanged.

## Mechanism-level interpretation

Inspection of the exact source identifies derived staging in the candidate writer: every enabled relation materializes `one_level_ref[]` from an already-validated native Segment buffer and then rereads that temporary structure to emit the final concat. For the non-hierarchical case, the Segment buffer already contains all information needed for those refs. That is a legitimate Law-fusion target because eliminating it changes no ONE semantics.

A preregistered follow-up tests generic direct Segment-to-final-concat ref emission while retaining the old bounded hierarchy path whenever the canonical `ONE_MAX_NODES` limit requires intermediate concat nodes. If that does not close the four simple rows, the remaining cost should be attributed upward rather than threshold-tuned.

## Comparator scope

This result has no v0.29/v0.30, full 15-workload Genesis, product ingest, authenticated placement or release authority. Frozen comparators remain unchanged.