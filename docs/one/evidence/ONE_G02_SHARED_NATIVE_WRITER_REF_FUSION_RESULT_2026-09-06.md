# ONE-G0.2 shared-native writer final-ref fusion rehabilitation — terminal result

Date: 2026-09-06  
Branch: `research/cmpct1`  
Experimental line: `ONE-G0.2`

## Exact evidence

- source/head: `cefc43cb6d3d068ff7031edc8ea37e8a115247af`
- workflow: `ONE-G0.2 shared native writer ref fusion`
- run: `34052564585`
- job: `101538662595`
- artifact: `9994993704`
- artifact digest: `sha256:0d2c6f3c48216398fa4792d596385a6f87eaa6fe7fc933c87d4ea1ce246cfee5`
- frozen rounds: `31`

CI truth: project install PASS; full ONE semantic/hostile tests PASS; independent ref-fused max-nodes probe PASS; performance falsifier intentionally exits non-zero; evidence upload PASS.

## Correctness / safety

- semantic failures: **0**
- independent Segment-oracle failures: **0**
- malformed native-buffer probes: **PASS**
- independent max-nodes probe: **PASS**
- canonical ONE0 wire: byte-identical to V2 on every row
- exact reconstruction: PASS on every row
- gain-retention check on mature `fragmented_every96`: PASS

The Builder changes only derived creator staging. For one-level concats it emits canonical refs directly from the already-validated native Segment buffer. If intermediate concat hierarchy is required by the existing `ONE_MAX_NODES` bound, the old bounded level construction remains in force. No workload or speed classifier exists.

## Frozen result

Mature productive candidate/V2:

- median: **0.2768343534922528x**
- rows <=0.90x: **11/15**
- worst: **0.965981102814759x**

Mature controls:

- median: **0.9493999346784597x**
- worst: **0.9952773656366644x**

Mature `fragmented_every96` median: **0.10209115670506x**, comfortably below the frozen <=0.15x gain-retention guard.

The four remaining breadth misses are again `shift_plus1` with exactly two Segments:

| bytes | candidate/V2 |
|---:|---:|
| 32,768 | 0.910904x |
| 65,536 | 0.952066x |
| 131,072 | 0.965981x |
| 262,144 | 0.954745x |

At 16,384 B the same case passes at `0.859227x`; segment-rich rows remain dramatically faster (`shift_plus1_damage_quarter` roughly 0.27–0.31x; `fragmented_every96` roughly 0.097–0.124x in the mature matrix).

## Decision

**`reject_shared_native_writer_ref_fusion`** under the unchanged original breadth gate.

This cleanly falsifies the hypothesis that one-level `one_level_ref[]` staging was the missing broad cost owner. Removing it is semantically sound and can reduce candidate work, but it does not establish <=0.90x across all mature productive rows.

Do not add a workload/size/segment-count dispatch to rescue the result.

## Causal interpretation / next owner

The simple-shift ratio tends back toward parity as relation size rises while segment-rich relations retain very large gains. That scaling is what we expect when an O(segments) Python/staging cost has been removed but both arms remain dominated by common O(n) work: root hashing, admission/proof, native segmentation and unavoidable source/wire byte movement.

The next experiment should therefore **attribute the charged simple-relation writer boundary by broad linear phases before changing code again**. In particular measure root SHA-256, admission/proof, native segmentation, final native writer/output exposure and full candidate elapsed on the same frozen simple-shift rows, with an uninstrumented full-path control. If the sum/profile shows one stable >=15% owner, attack that owner with a fused-pass or eliminated-pass design. If no phase owns enough, move the optimization boundary upward instead of continuing native writer micro-tuning.

## Comparator / claim boundary

No v0.29/v0.30, product ingest, authenticated placement, RSS/native peak, full Genesis matrix or release authority is claimed. Frozen comparators remain unchanged.