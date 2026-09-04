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
- 3 fresh-process profiled builds per arm/target.

Each repetition MUST execute in a new Python process. Module state, allocator state, codec contexts, candidate caches, and mutable release-profile state may not carry from one profiled repetition to another.

The generated corpus tree and nested member identity must match R32. Every build must strongly verify and reproduce the exact R32 complete archive bytes and SHA-256:

- full/release: `8,088,619 B`, `dc789b874da673584046af26e7f21f593cfcc1fa8cd365bc6298942c2f752eb7`;
- full/no-Zstd: `8,056,193 B`, `d812ffa7a0002e4e137e578918010d5ce00dfb8055a4c9fb188ebbd9212c79e9`;
- nested/release: `2,231,160 B`, `6d6973cb4931edcc2ed776b8fdb8500dc80da084f0b06681e87eff544646d6ef`;
- nested/no-Zstd: `2,197,414 B`, `b2cb86d7c51eecec959989b3e592f344311c3da32af3d47ed1251284f2223bea`.

Profiler overhead is diagnostic and must never be compared directly to unprofiled release thresholds. Only paired profiled-arm deltas and function-level attribution are interpreted.

## Frozen measurement

Use Python `cProfile` around the existing R32 `_build_arm` call. For each fresh-process repetition record:

- profiled wall time;
- exact archive bytes/SHA;
- strong verification;
- cumulative and internal/exclusive time by function signature for project functions plus profiler-visible C/native call entries;
- top 40 cumulative-time functions and top 40 positive internal-time deltas.

For each target compute median per-function cumulative and internal time in both arms and the signed `no-Zstd - release` deltas.

Cumulative times overlap through call stacks. A broad wrapper such as `Builder.build()` can inherit the full child cost and therefore **cannot by cumulative delta alone establish an owner**. Do not sum cumulative times into a fake percentage of total time, and do not permit an outer-wrapper cumulative delta to satisfy the localization gate.

The localization gate uses **internal/exclusive time**, which charges time to the function or profiler-visible C/native call actually consuming it rather than every ancestor on the stack.

## Frozen terminal grammar

`PHASE_OWNER_LOCALIZED`

iff all six builds per target reproduce the frozen R32 bytes/SHA and verify, and at least one stable function/C-call signature has a positive median **internal/exclusive-time** delta of >=10 ms on the nested target and the same positive sign on the full target.

`RESIDUAL_DISTRIBUTED_OR_BELOW_ATTRIBUTION_FLOOR`

iff identity/verification pass but no signature satisfies that cross-target >=10 ms internal-time localization rule.

`SUBSTRATE_OR_IDENTITY_FAILURE`

for any corpus, archive identity, verification, execution or result-structure failure.

## Success handoff

A localized owner authorizes only a new superseding Builder/preregistration aimed at that measured phase. The next intervention must preserve R32's exact byte/locality behavior and must use the lowest R1-R3 tier justified by the owner.

## Failure handoff

If the residual is distributed, do not guess another codec. Escalate to an execution-architecture trace that measures explicitly non-overlapping build phases, or retire the current rehabilitation path if the remaining debt is below realistic closure headroom.

## Pre-execution hostile-review note

The first draft used cumulative-time deltas for the terminal gate. Before any result-bearing R33 receipt executed, hostile review showed that this would be structurally permissive: an outer build wrapper could inherit the entire residual delta and trigger `PHASE_OWNER_LOCALIZED` without identifying its child owner. The freeze was corrected before execution to use internal/exclusive time and to include profiler-visible C/native calls. No result, corpus, comparator, byte identity, repetition count, or measured product behavior was observed before this correction.
