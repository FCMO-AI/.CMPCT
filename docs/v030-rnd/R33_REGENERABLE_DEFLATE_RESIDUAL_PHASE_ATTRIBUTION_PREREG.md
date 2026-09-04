# R33 — Regenerable-Deflate Residual Runtime Phase Attribution Preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION**

Parent evidence: `docs/v030-rnd/R32_REGENERABLE_DEFLATE_OUTPUT_DEAD_ZSTD_ELISION_RESULT.md`.

Authority product substrate: `b0e7aeab92c994b4a25c5040fe3fb9f5e208b01a`.

## Question

After R32 removed an output-dead ordinary-Zstd audition, what phase/function family owns the remaining material create-time debt versus `release-all-exact`?

This is a diagnostic only. It may identify the next causal target; it cannot authorize product policy or release credit.

## Forge classification

- diagnosis: **D2/D3 residual execution/search debt**;
- intervention: **R0 phase attribution**;
- active saturation: **S5** — speculative candidate work has already been shown material and partially retired;
- RPS: **86/100** (release necessity 15, upside 15, root-cause fit 15, generality 7, information gain 15, efficiency 9, product survival 7, simplicity 3).

## Frozen substrate and targets

Reuse the exact R32 instrument and semantic policy without edits:

- `benchmarks/v030_r32_regenerable_deflate_output_dead_zstd_elision.py`;
- full `neutral_hostile_v1/06_incremental_backups`;
- exact isolated `snapshot_2.zip` projection;
- arms: `release-all-exact` and `no-ordinary-zstd` only;
- 3 fresh profiled builds per arm/target.

The generated corpus tree and nested member identity must match R32. Every build must strongly verify and reproduce the exact R32 complete archive bytes and SHA-256:

- full/release: `8,088,619 B`, `dc789b874da673584046af26e7f21f593cfcc1fa8cd365bc6298942c2f752eb7`;
- full/no-Zstd: `8,056,193 B`, `d812ffa7a0002e4e137e578918010d5ce00dfb8055a4c9fb188ebbd9212c79e9`;
- nested/release: `2,231,160 B`, `6d6973cb4931edcc2ed776b8fdb8500dc80da084f0b06681e87eff544646d6ef`;
- nested/no-Zstd: `2,197,414 B`, `b2cb86d7c51eecec959989b3e592f344311c3da32af3d47ed1251284f2223bea`.

Profiler overhead is diagnostic and must never be compared directly to unprofiled release thresholds. Only paired profiled-arm deltas and call/cumulative-time attribution are interpreted.

## Frozen measurement

Use Python `cProfile` around the existing R32 `_build_arm` call. For each repetition record:

- profiled wall time;
- exact archive bytes/SHA;
- strong verification;
- cumulative and internal time by function signature for all entries under `src/cmpct/`, the R32 instrument, and dead-dictionary product helpers;
- top 40 cumulative-time functions.

For each target compute median per-function cumulative time in both arms and the signed `no-Zstd - release` delta. Rank positive deltas.

Because cumulative times overlap through call stacks, **do not sum them into a fake percentage of total time**. The experiment is for owner localization, not additive accounting.

## Frozen terminal grammar

`PHASE_OWNER_LOCALIZED`

iff all six builds per target reproduce the frozen R32 bytes/SHA and verify, and at least one stable function signature has a positive median cumulative-time delta of >=10 ms on the nested target and the same sign on the full target.

`RESIDUAL_DISTRIBUTED_OR_BELOW_ATTRIBUTION_FLOOR`

iff identity/verification pass but no function satisfies that cross-target >=10 ms localization rule.

`SUBSTRATE_OR_IDENTITY_FAILURE`

for any corpus, archive identity, verification, execution or result-structure failure.

## Success handoff

A localized owner authorizes only a new superseding Builder/preregistration aimed at that measured phase. The next intervention must preserve R32's exact byte/locality behavior and must use the lowest R1-R3 tier justified by the owner.

## Failure handoff

If the residual is distributed, do not guess another codec. Escalate to an execution-architecture trace that measures non-overlapping build phases, or retire the current rehabilitation path if the remaining debt is below realistic closure headroom.
