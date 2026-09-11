# ONE-G0.2 shared-native writer ref-fusion rehabilitation — preregistration

Date: 2026-09-06  
Branch: `research/cmpct1`  
Experimental line: `ONE-G0.2`

## Mission Lock / observed baseline

The exact shared-native writer transfer run at `eafc17fe92a0f2c3f623382334d8d20f047c6b57` is a strong but non-promotable research seed. It preserves exact ONE0 semantics, independent Segment-oracle agreement, malformed-buffer rejection and the independent max-nodes resource probe. On mature productives it measured median candidate/V2 `0.2468426132473778x`, worst `0.9693553343068838x`, and 11/15 rows at or below `0.90x`; mature controls measured median `0.9523258605330005x`, worst `0.9807975114417786x`. The frozen transfer gate required 15/15 mature productives <=0.90x, so the transfer shape is rejected as-is.

All four breadth misses are the same structural case: `shift_plus1` with exactly two native Segments at 32/64/128/256 KiB (`0.928137x`, `0.942929x`, `0.953848x`, `0.969355x`). Do not rescue this with a workload, size, segment-count, Surprise-density or corpus dispatcher.

Code inspection exposes a representation-independent staging cost in the native writer: for every enabled relation whose final concat fits within `ONE_MAX_NODES`, it allocates and populates an `one_level_ref[]` array, then immediately rereads those refs to emit the final concat. The authoritative native Segment buffer already contains all information needed to emit those refs exactly. This staging array is therefore derived temporary state, not Law or Surprise.

## Falsifiable hypothesis

A generic native Law-fusion step that emits the final one-level concat directly from the already-validated Segment buffer—without allocating/materializing `one_level_ref[]`—will retain the large shared-native writer gain while closing the simple two-segment breadth debt. The optimization is structural: it applies whenever no intermediate concat hierarchy is required by the existing `ONE_MAX_NODES` semantic bound. It is not selected by workload identity or measured speed.

For relations requiring intermediate hierarchy (`segment_count > ONE_MAX_NODES`), retain the existing bounded level construction exactly. No reader operation, wire grammar, node ordering, root ordering, Law/Surprise decision, hierarchy cap or resource limit changes.

## Disproof / retirement

Reject this rehabilitation if any semantic/oracle/wire/resource-hostile mismatch occurs, if the original large fragmented-relation gain is materially lost, or if the frozen breadth gate below still fails. Do not follow a failure with a post-hoc workload/size/segment-count dispatcher.

If the optimization remains correct but the four simple-shift rows still fail, conclude that their elapsed is dominated by costs outside final-ref staging (hashing/admission/segmentation/source-wire copying/output allocation/FFI) and move cost attribution upward instead of micro-tuning this array.

## Frozen arms

Baseline: promoted root-hash-charged plan-direct V2 writer:

`root hashes -> admission -> native one-pass segmentation -> Python plan/direct ONE0 writer`

Candidate:

`root hashes -> admission -> native one-pass segmentation -> shared native bounded ONE0 writer -> direct Segment-to-final-concat ref emission when hierarchy is unnecessary`

Both arms retain the exact source/target bytes, root hashes, admission, Segment producer, relation enable decision, canonical ONE0 bytes, ONE limits and reader semantics used by the shared-native transfer falsifier.

## Required semantic / hostile gates

- canonical wire byte-identical to V2 on every row;
- exact WireStats, roots and reconstruction;
- independent native Segment oracle exact;
- same admission/best-shift/proof facts;
- existing malformed native-buffer probes pass;
- independent max-nodes overflow probe still rejects with the same resource semantics;
- no new reader opcode, format revision or weakened integrity/locality/recovery/portability behavior.

## Frozen workload and timing method

Reuse the exact shared-native transfer workload matrix, mature threshold (>=16 KiB), 31 paired rounds, alternating A/B-B/A order and GC discipline. Root SHA-256, admission, segmentation, native writer execution, result exposure and all costs already inside the seed timing boundary remain charged.

Record canonical bytes, Surprise bytes, elapsed, segment count, reader work/materialization and native output allocation. Stored bytes must remain exactly 1.0x.

## Frozen rehabilitation gate

Use the original transfer gate unchanged so the repair cannot redefine success:

- semantic failures = 0; oracle failures = 0; malformed/resource probes pass;
- mature productive median candidate/V2 <= **0.80x**;
- **15/15** mature productive rows <= **0.90x**;
- no mature productive row > **1.03x**;
- mature control median <= **1.03x**;
- no mature control row > **1.08x**.

Gain-retention guard: mature `fragmented_every96` median ratio must remain <= **0.15x**, preventing rehabilitation from optimizing away the breakthrough on the segment-dense rows.

## Claim boundary

If this passes, it promotes only the shared-native adjacent-version research-writer principle with generic final-ref fusion. It grants no arbitrary/fused-discovery, product ingest, authenticated placement, RSS/native peak, v0.29/v0.30 or 15-workload Genesis authority.