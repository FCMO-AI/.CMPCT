# v0.30 H-EFFORT-5B RAW-Terminal Mosaic Transfer Result — 2026-09-13

Status: **`RAW_TERMINAL_SECOND_COURT_TRANSFERS`; independent hostile research evidence; no product/release credit**.

## Evidence identity

- Frozen mission lock: `docs/V030_RAW_TERMINAL_MOSAIC_TRANSFER_MISSION_LOCK_2026-09-13.md`
- Exact result-bearing head: `d7b3b7426daad6f2fd2c6af66fca951ed0863bd6`
- Hosted run: `34784700929`
- Artifact: `10325798482`
- Artifact digest: `sha256:48905ac9608a812459290bc53adddbcf3b564d17558d0029283b0057dcea5e74`
- Referee exit code: `0`

## Result

Across all eight pre-existing Mosaic hostile workloads, the fixed-geometry referee measured **42 physical packs**:

- **34** level-1 RAW packs;
- **8** level-1 non-RAW packs;
- level-1 RAW bytes: **7,864,605 B**;
- RAW applicability transferred across **six distinct hostile workload families**;
- **0 counterexamples** at levels `3,6,9,12,19`;
- closest later payload delta versus level-1 RAW: **0 B** (tie, never improvement);
- historical post-L1 effort on those RAW packs consumed **0.371994056 s CPU** and **0.372129504 s wall** that a correct level-1 RAW terminal would avoid.

Applicable families:

- `01_two_parent_branch_merge`: 3 / 3 packs RAW
- `02_four_way_cherry_pick`: 5 / 5
- `03_reordered_two_parent_merge`: 3 / 3
- `05_single_parent_control`: 5 / 5
- `07_incompressible_control`: 5 / 5
- `08_duplicate_root_pressure`: 13 / 13

The source-like `04_source_tree_merge` and deceptive-common-header `06_false_mosaic_sources` surfaces remained non-RAW and therefore correctly contributed no evidence for or against the gate.

**Verdict: `RAW_TERMINAL_SECOND_COURT_TRANSFERS`.**

## Combined evidence with H-EFFORT-5

The first independent court (`resemblance_hostile_corpus_v1`) was insufficient in family breadth but produced 80 RAW packs / 10,606,293 B and zero counterexamples.

The second court adds 34 RAW packs / 7,864,605 B across six applicable families, again with zero counterexamples.

Together the two frozen hostile courts have now tested:

- **114 level-1 RAW packs**;
- **18,470,898 raw bytes**;
- structurally different branch/merge, reordered, near-duplicate, duplicate-pressure, and incompressible families;
- **zero** later-level byte improvements after the existing level-1 encoder chose RAW.

This does not prove a mathematical universal law of Zstd levels. It provides strong scope-matched engineering evidence that the encoder's already-existing RAW admission is an effective cheap terminal signal on the tested CMPCT pack universe.

## Strongest limitation

The tested suites remain synthetic deterministic corpora and the level-1 RAW decision itself includes the current encoder's admitted payload economics. Future codec/library behavior or materially different pack regimes can invalidate transfer. The product Builder therefore must preserve zero-byte-regression fallback and be judged against the then-current direct baseline rather than treating this result as eternal codec truth.

## Authorized next step

A minimal Builder may short-circuit **additional adaptive-effort exploration only when the incumbent level-1 physical payload already has `codec == RAW`**. It must not alter physical geometry, reader grammar, archive representation, hot/locality semantics, or RAW admission itself.

The Builder must be preregistered before result-bearing execution and must require:

- deterministic archive bytes **identical to direct baseline** on the product-valid court (zero-byte tolerance, not merely non-regression);
- strong verification / filesystem fidelity unchanged;
- locality/decode-unit semantics unchanged;
- measurable creation CPU/wall improvement outside the applicable timing noise rule, or otherwise no promotion claim;
- explicit accounting of how many later encode attempts were skipped;
- no changes to compressor thresholds, effort levels, workload coverage, or competitor settings.

If archive bytes differ anywhere, the optimization is not the mechanism tested here and must fail closed.

## Product-credit boundary

This result changes no product bytes or shipping code. It earns permission to build and measure one minimal execution optimization; nothing more.