# v0.30 H-EFFORT-5B RAW-Terminal Mosaic Transfer Mission Lock — 2026-09-13

Status: **frozen independent hostile transfer preregistration; same candidate predicate; no encoder modification authorized**.

## Motivation

H-EFFORT-5 tested the pre-existing level-1 `codec == RAW` state on `resemblance_hostile_corpus_v1`. The candidate produced zero counterexamples on 80 RAW packs / 10.6 MiB, but all applicable packs belonged to one incompressible workload family, so the frozen verdict was correctly `RAW_TERMINAL_INSUFFICIENT_TRANSFER`.

This experiment does not weaken or rewrite that result. It opens a second independent court using an already-existing hostile suite designed for a different research question.

## Unchanged hypothesis

> If the existing level-1 physical encoder chooses RAW (`codec == 0`) for a pack, later compression-effort levels do not produce a strictly smaller admitted payload for that same raw pack.

Candidate predicate remains exactly `level1 codec == 0`. No ratio threshold, path, extension, fixture hash, workload name, content label, entropy estimator, or post-result classifier is allowed.

## Frozen second court

Use all eight workloads from `benchmarks/mosaic_hostile_corpus_v1.py`:

1. `01_two_parent_branch_merge`
2. `02_four_way_cherry_pick`
3. `03_reordered_two_parent_merge`
4. `04_source_tree_merge`
5. `05_single_parent_control`
6. `06_false_mosaic_sources`
7. `07_incompressible_control`
8. `08_duplicate_root_pressure`

This corpus predates H-EFFORT-5 and was built to falsify multi-root Mosaic assumptions, not adaptive compression effort. It combines branch merges, reordered modules, source-like content, near-duplicate controls, deceptive common-header/footer sources, random controls, and duplicate-root pressure. That independent purpose makes it a useful second court.

## Procedure

Use the exact H-EFFORT-4/H-EFFORT-5 fixed-geometry effort semantics:

- build the existing deterministic Mosaic hostile corpus;
- create the regular-file physical profile without changing filesystem-control semantics;
- recover exact raw physical packs;
- measure deterministic admitted payloads at levels `1,3,6,9,12,19`, three repeated same-process measurements per level;
- isolate only packs whose level-1 admitted codec is RAW;
- preserve every later level result and exact raw SHA-256;
- measure historical post-L1 ladder CPU/wall on those packs for materiality only.

## Frozen verdict

### `RAW_TERMINAL_SECOND_COURT_TRANSFERS`

Only if all are true:

- at least **two distinct Mosaic hostile workload families** contain at least one level-1 RAW pack;
- **zero** level-1 RAW packs produce a strictly smaller admitted payload at any measured later level;
- every pack uses byte-identical raw input across all levels;
- substrate/profile/provenance checks pass.

### `RAW_TERMINAL_SECOND_COURT_FALSIFIED`

If **any** valid level-1 RAW pack is strictly smaller at any later level. One counterexample kills the hard-terminal formulation. Preserve workload, pack index, raw SHA-256, raw bytes, winning level, byte gain, CPU and wall.

### `RAW_TERMINAL_SECOND_COURT_INSUFFICIENT`

If fewer than two distinct Mosaic workload families contain RAW packs, or provenance/identity is invalid.

No result from this second court changes the frozen H-EFFORT-5 verdict. If this second court transfers, a later synthesis may argue that two independent hostile suites jointly support a Builder, but product policy still requires a separately frozen product-valid experiment with zero deterministic byte regression.

## Strong controls

- Same exact `_encode` semantics as H-EFFORT-4/H-EFFORT-5.
- RAW is existing codec identity, not a newly inferred ratio.
- No tuning after result-bearing execution starts.
- Report non-RAW counts and all RAW counts per workload.
- No product/release/reader/recovery/locality/format/platform credit.

## Disproof consequence

Any counterexample retires RAW as a hard terminal. Do not rescue it inside this experiment by adding a size threshold or special-case exclusion.
