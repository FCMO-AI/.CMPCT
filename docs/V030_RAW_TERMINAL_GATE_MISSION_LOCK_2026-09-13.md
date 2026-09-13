# v0.30 H-EFFORT-5 RAW-Terminal Gate Mission Lock — 2026-09-13

Status: **frozen held-out transfer preregistration; observational/referee work only; no encoder modification authorized by this experiment**.

## Trigger

H-EFFORT-4 established transferable pack-effort structure while also showing that a broad skip-middle/terminal policy can easily trade too much CPU for density. The strongest simpler mechanism in the exact frozen census is not a tuned ratio threshold:

> The level-1 encoder already emits an explicit RAW fallback (`codec == 0`) when level-1 Zstd does not beat raw bytes by the product's admitted margin.

On the H-EFFORT-4 design substrate, this state occurred on **222 packs**. Those packs had:

- **0 packs** with later measured byte headroom across levels `3,6,9,12,19`;
- **0 missed bytes** from terminating at the level-1 RAW payload;
- **222 / 222** cases where the historical later effort ladder spent additional CPU without improving stored payload bytes;
- **4.1939 s** of historical post-L1 ladder CPU in aggregate on those packs, versus zero post-L1 effort under a RAW-terminal gate.

That is unusually strong but still in-sample evidence. A higher compression level can in principle compress data that level 1 leaves raw, so the observation must not be promoted by inspection alone.

## Falsifiable hypothesis H-EFFORT-5

Across a structurally different deterministic held-out corpus not used by H-EFFORT-4, packs for which the existing level-1 physical encoder selects RAW contain no useful later-level compression headroom under the same exact `_encode` semantics.

If true, `codec == RAW` is a content-derived exact opportunity gate for terminating additional compression-effort search on that pack. If false even once on the held-out court, this **hard terminal** formulation is falsified; do not tune a ratio threshold inside this experiment to rescue it.

## Frozen held-out court

Use the five workloads from `benchmarks/resemblance_hostile_corpus_v1.py`, which were not part of the H-EFFORT-4 ten-workload stable substrate:

1. `01_shifted_versions`
2. `02_false_neighbors`
3. `03_boundary_churn`
4. `04_deflate_family`
5. `05_incompressible`

These workloads deliberately span shifted near-versions, deceptive common-header/footer neighbors, boundary churn, already-DEFLATEd containers, and deterministic incompressible data. Their historical purpose is unrelated to adaptive effort, which makes them useful hostile transfer rather than a new hand-picked success corpus.

No workload name, path, fixture identity, extension, or corpus label may enter the candidate decision. The only candidate predicate is the already-produced level-1 codec identity: `codec == 0`.

## Referee procedure

For each held-out workload:

1. build the deterministic corpus from its existing generator;
2. profile it through the same explicit filesystem-control path used for non-primary H-EFFORT-4 held-outs;
3. recover the exact physical raw pack units;
4. measure deterministic payload identity, bytes, CPU, and wall at levels `1,3,6,9,12,19` using the same encode implementation and repetition semantics as H-EFFORT-4;
5. isolate every pack whose level-1 codec is RAW (`0`);
6. test whether any later measured level yields fewer payload bytes than the level-1 RAW payload;
7. reconstruct the historical first-worse ladder CPU on those same packs so avoided post-L1 effort is measured rather than assumed.

The referee must preserve and report every counterexample.

## Frozen gates

Classify exactly as follows.

### `RAW_TERMINAL_TRANSFERS`

Only if:

- at least **two distinct held-out workload families** contain at least one level-1 RAW pack, so the result is not a one-family accident;
- **zero** level-1 RAW packs have a strictly smaller payload at any of levels `3,6,9,12,19`;
- every reported RAW pack is measured from the same raw bytes at every effort level;
- no corpus/profile/physical-unit identity check fails.

The referee must report observed pack count, raw bytes, avoided historical post-L1 CPU/wall, and the closest later-level byte result even when the gate passes. These quantities describe materiality; they are not tunable pass thresholds.

### `RAW_TERMINAL_FALSIFIED`

If **any** level-1 RAW pack has a strictly smaller payload at any later measured effort level. One valid counterexample kills the hard-terminal claim. Preserve the exact workload, pack identity, raw SHA-256, raw bytes, winning level, byte gain, and CPU cost.

### `RAW_TERMINAL_INSUFFICIENT_TRANSFER`

If fewer than two held-out workload families contain level-1 RAW packs, or if evidence identity/provenance is invalid. Do not call absence of applicable packs a successful transfer.

## Strong controls

- Same raw pack bytes at every effort level.
- Same `_encode` implementation and codec semantics as H-EFFORT-4.
- Three repeated same-process measurements per level, preserving deterministic payload identity.
- No learned threshold, classifier, workload label, path rule, or post-result mutation.
- RAW means the encoder's existing codec decision, not an inferred compression-ratio band.
- Report non-RAW packs separately enough to confirm the corpus is not accidentally all one regime.
- This referee measures effort economics only; it grants no reader, recovery, locality, filesystem, format, platform, release, or historical benchmark credit.

## Disproof / continuation

If falsified, preserve the counterexample and retire **RAW as a hard terminal**. A later experiment may investigate RAW as a probabilistic/conditional signal only under a new preregistration; do not weaken this gate.

If it transfers, the next action may be a minimal Builder that short-circuits later compression-effort evaluation for level-1 RAW packs while leaving archive representation and reader grammar unchanged. That Builder must compare direct baseline vs candidate on the repository's then-current product/release corpus and require zero deterministic byte regression plus measured creation-CPU/wall improvement outside noise before promotion.

## Product-credit boundary

H-EFFORT-5 changes no encoder, archive bytes, format, reader, recovery, integrity, locality, platform implementation, version, score, or release authority. It is a held-out falsifier for one generic opportunity-gating mechanism.