# CMPCT1 / ONE Genesis gate result — 2026-09-11

Status: **FINAL GATE VERDICT — REACTIVATE_V030_NEAR_TERM**

This record adjudicates the preregistered one-week CMPCT1 / ONE Genesis gate without changing any contender, workload, repetition count, input identity, semantic requirement, integrity requirement, access requirement, or comparator setting after observing results.

## Frozen contenders

- CMPCT1 / ONE-G0.2 candidate: `38f17f4a45686a59a853bf62f0c840e228879e17`
- frozen v0.29: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- frozen v0.30: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

All three dossiers contain 15 rows and the row identities are exactly equal on `(suite, name, files, logical_bytes, tree_sha256)`. Total logical input is `265,969,714 B` for every contender.

## Evidence provenance

The first sealed real-gate run produced complete ONE and v0.29 dossiers but failed before completing v0.30. Its retained artifact is:

- workflow run `34573437613`
- artifact `10191000395`
- artifact digest `sha256:bd9d767874bddf02fcd03d67a6de7ed7a7d1378456e47da2e2f198f7992706ba`
- harness head `7ff0e55e68a296d16d6beee37190fd0d369d7a48`

A narrow v0.30 resume diagnostic was then used only to recover the missing frozen-comparator measurements. During diagnosis, the historical worker was found to have allowed `cmpct` imports from the current harness checkout rather than the frozen comparator checkout. This was a comparator-hermeticity defect, not a v0.30 loss. The harness was repaired to prepend the frozen `src`, frozen `experiments`, and frozen checkout roots and to fail closed unless every loaded `cmpct` module resolves under the frozen checkout. The workflow was also provisioned with v0.30's declared audio dependency (`soundfile>=0.12`) and pinned to the event SHA rather than a moving branch ref.

The source-sealed v0.30 recovery completed successfully:

- workflow run `34594599804`
- job `103251512822` (`v030-resume`)
- exact harness SHA `7e14e6867a329bc3281e9016e673c46dc3feb081`
- artifact `10263288496`
- artifact digest `sha256:1e73f88c597bf0e16f60375b2f51c0ec0a79cf8204683adb7c00dde32b44c148`
- v0.30 source SHA inside dossier: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`
- 15/15 rows complete
- every row reports `runtime_source_provenance.status = source_sealed`
- loaded `cmpct` modules resolve under the frozen v0.30 checkout

The resume diagnostic executed raw measurements only. It did not compare contenders, score rows, or select a winner.

## Complete 15-workload density and creation-CPU matrix

| Workload | ONE bytes | v0.29 bytes | v0.30 bytes | ONE create CPU s | v0.29 | v0.30 |
|---|---:|---:|---:|---:|---:|---:|
| 01_developer_repository | 3,175,855 | 744,337 | 870,602 | 0.2481 | 16.9662 | 4.3005 |
| 02_office_workspace | 16,408,441 | 5,954,026 | 15,445,458 | 0.0931 | 24.8509 | 0.5402 |
| 03_media_library | 29,456,838 | 28,719,497 | 27,448,641 | 0.1468 | 48.1739 | 0.9835 |
| 04_analytics_and_database | 31,920,630 | 6,135,172 | 10,392,494 | 0.1517 | 209.7236 | 1.6541 |
| 05_logs_and_telemetry | 17,354,869 | 3,550,609 | 3,550,345 | 0.0944 | 122.0224 | 1.3203 |
| 06_incremental_backups | 14,581,152 | 8,223,844 | 8,088,093 | 0.1936 | 23.8332 | 1.2357 |
| 07_incompressible_and_encrypted_like | 10,930,856 | 10,193,958 | 10,218,575 | 0.2559 | 17.3849 | 0.9445 |
| 08_many_tiny_files | 2,720,700 | 420,318 | 722,674 | 0.9616 | 8.8586 | 3.2571 |
| 09_ml_artifacts | 18,553,871 | 13,836,439 | 13,674,829 | 0.0968 | 50.8913 | 3.1460 |
| 10_large_mixed_binary | 34,254,292 | 12,593,372 | 12,590,160 | 0.1810 | 27.8649 | 0.2699 |
| 01_shifted_versions | 34,233,736 | 1,723,056 | 1,700,667 | 0.1657 | 104.9743 | 6.1731 |
| 02_false_neighbors | 40,667,358 | 34,698,771 | 34,649,280 | 0.2649 | 54.5913 | 1.1373 |
| 03_boundary_churn | 9,954,062 | 79,876 | 76,032 | 0.1088 | 74.9268 | 7.1097 |
| 04_deflate_family | 134,759 | 14,597 | 17,754 | 0.0307 | 6.6890 | 0.5515 |
| 05_incompressible | 10,872,482 | 10,611,653 | 10,609,971 | 0.0859 | 14.7856 | 0.4371 |

## Aggregate density

| Contender | Authenticated stored bytes | Stored / logical |
|---|---:|---:|
| ONE-G0.2 | **275,219,901 B** | **1.034779x** |
| v0.29 | **137,499,525 B** | **0.516974x** |
| v0.30 | **150,055,575 B** | **0.564183x** |

Deterministic per-workload density outcomes:

- ONE vs v0.29: ONE wins `0/15`, v0.29 wins `15/15`.
- ONE vs v0.30: ONE wins `0/15`, v0.30 wins `15/15`.
- v0.29 vs v0.30: v0.29 wins `6/15`, v0.30 wins `9/15`.

ONE therefore stores about `2.0016x` v0.29's bytes and about `1.8341x` v0.30's bytes on the same 15 physical inputs.

## Creation compute

Sum of the 15 per-workload median fresh-process creation CPU measurements:

- ONE-G0.2: `3.0791 s`
- v0.29: `806.5369 s`
- v0.30: `33.0603 s`

Per-workload creation CPU:

- ONE beats v0.29 on `15/15`; median v0.29/ONE speed factor is about `217.6x` (range about `9.2x` to `1382.2x`).
- ONE beats v0.30 on `15/15`; median v0.30/ONE speed factor is about `6.70x` (range about `1.49x` to `65.3x`).
- v0.30 beats v0.29 on `15/15` creation CPU rows.

The ONE creation result is a real breakthrough seed and must be preserved. It is not sufficient to win this gate because the gate requires a materially stronger path with credible ability to supersede both mature lines across density + speed + compute/access/resource semantics, not creation speed alone.

## Resource/access cautions

- v0.29 has no proven frozen selective-member surface in this harness and remains `unavailable`; unavailable is not zero and is not an automatic loss.
- ONE and v0.30 have selective measurements on 14/15 rows.
- Whole-read timing is retained as evidence but **not used as decisive supersession evidence** here because the historical worker's `whole_read` path performs `strong_verify()` followed by a full `extract()`, while ONE's authenticated read path is not structured identically. That semantic-accounting debt must be resolved before making a strong decode-throughput claim.
- v0.30 recovery rows show a large process peak RSS (`511,176,704 B`) in this hosted environment. It is preserved as measured evidence and is not averaged away.

## Mechanism-level interpretation

The frozen ONE candidate's strongest negative is not merely its aggregate expansion. Across the prior Genesis analysis it had `9,253` file roots, accepted `0` Law roots, and emitted `9,253` Surprise roots. The current discovery system therefore failed to identify useful predictive structure on the gate corpus even though mature CMPCT mechanisms demonstrably exploit such structure.

This falsifies the sufficiency of **ONE-G0.2 discovery**, not the Law + Surprise representation principle itself.

The rehabilitation target is to absorb the predictive structure rather than reintroduce a reader-visible codec zoo:

1. fused observation;
2. bounded non-adjacent candidate indexing;
3. shift/range/multi-parent hypotheses expressed through the same ONE grammar;
4. cheap falsification and branch-and-bound using marginal information yield;
5. exact proof only for survivors;
6. compact authenticated Crystallization, especially for tiny-file cases;
7. preserve the reader rule: no discovery during reconstruction.

The earlier `boundary_churn` result (~35.7 MB exact-proof work for zero accepted Laws) is explicit evidence that proof opportunity gating is required. The authenticated-manifest overhead (~7.18 MB in the frozen ONE dossier) is likewise a concrete compact-Crystallization target; removing authentication is not an acceptable repair.

## Gate adjudication

The preregistered rule says CMPCT1 remains primary only if the week demonstrates a materially stronger path and credible ability to supersede both frozen v0.29 and the deferred v0.30 frontier. It does not.

ONE-G0.2 loses deterministic stored bytes to both comparators on every workload, by a large aggregate margin. Its very large creation-compute win is important research evidence, but it does not make the present candidate a credible near-term replacement for both mature lines.

**Decision: `REACTIVATE_V030_NEAR_TERM`.**

Operational meaning:

- Reactivate v0.30 as the primary near-term research line.
- Preserve CMPCT1 / ONE as an active research line and preserve its creation-speed breakthrough plus all Genesis negative evidence.
- Do not retroactively modify or rerun the frozen ONE candidate to manufacture a gate win.
- Future ONE work must rehabilitate the density/discovery and authenticated-metadata debt while retaining its compute-efficiency advantage before it can challenge for primary status again.
- No ordinary v0.30 comparator result from this gate should be mistaken for permission to weaken existing v0.30 correctness, locality, integrity, recovery, safety or portability requirements.
