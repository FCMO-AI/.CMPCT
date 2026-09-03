# r25 Shifted attempt-5 phase-ownership oracle v1 — frozen preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION / FORGE R0 / NO PRODUCT OR RELEASE CREDIT**

Parent diagnosis: `docs/v030-rnd/R25_SHIFTED_SHARED_EARLY_BOUND_OBSERVABILITY_RESULT.md`.

## Question

The accepted Shifted runtime debt is dominated by the losing G0-G4 path after PrefixGraph has already materialized a smaller candidate. The shared v0.29 substrate is in turn dominated by the accepted attempt-5 child. Can any exact stopping intervention that acts only **after the attempt-4 Placement graph has completed** save enough attempt-5 work to plausibly close the current Shifted creation gap?

This experiment does not invent a stopping rule. It measures the latest-stage opportunity budget so Forge can retire an insufficient seam before implementing it.

## Frozen authority and prior gap

Prior independent exact-candidate runtime revalidation (`docs/v030-rnd/R25_RUNTIME_REVALIDATION_3A_RESULT.md`) measured Shifted create ratio **1.252428x** against the unchanged release median ceiling **1.10x**. On that same evidence wave the v0.30 Shifted pack is about 61 s and the accepted v0.29 pack about 49 s; the losing attempt-5 child is about 49 s.

To close 1.252428x to 1.10x without changing the inherited comparator requires removing about **12.17% of complete v0.30 pack time**. Because the attempt-5 child owns only about four-fifths of complete pack wall time, a post-Placement intervention needs roughly **15% of attempt-5 wall** to remain available even under the impossible optimistic assumption that all remaining tail work can be deleted for free.

Frozen conservative seam threshold: **0.15 of attempt-5 wall**. Falling below this on every repetition falsifies post-Placement stopping as the primary Shifted repair. This is intentionally slightly easier to satisfy than the ~15.1% arithmetic implied by the prior receipt.

## Diagnosis / intervention class

- strict target: restore Shifted create to the unchanged fresh-process release band while retaining PrefixGraph bytes, whole-tree RSS, integrity, locality and exact tournament semantics;
- diagnosis: **D2/D3** execution/search architecture;
- instrument radicality: **R0**;
- active saturation: **S5 speculative-work dominance**;
- Forge RPS: **91/100** (release necessity 15, upside 18, root-cause fit 15, generality 7, information gain 15, experiment efficiency 9, product survival 9, portability 3).

## Frozen corpus and implementation

- deterministic `benchmarks.resemblance_hostile_corpus_v1.shifted_versions` workload only;
- accepted `experiments.entropygraph_v029_residual_fast.build_graph` attempt-5 graph path;
- two fresh output repetitions on one generated corpus;
- timing wrappers may surround only `A4.build_graph` (attempt-4 Placement owner) and `_compile_residual` (residual-pack tail);
- wrappers pass identical arguments and return values and may not mutate candidate state;
- final archive identity must be stable across repetitions and `strong_verify` must reproduce the deterministic source tree.

The decisive non-overlapping quantities are:

- `attempt5_total_s` — complete `build_graph` wall time;
- `placement_s` — time inside the exact inherited attempt-4 Placement builder;
- `post_placement_tail_s = attempt5_total_s - placement_s` — an **optimistic upper bound** on wall any intervention beginning only after Placement can remove. It includes residual compilation, winner copy/publication and wrapper overhead rather than undercharging them;
- `post_placement_tail_fraction = post_placement_tail_s / attempt5_total_s`.

Residual compile is reported separately for causal detail but is not the decisive bound.

## Frozen decisions

`POST_PLACEMENT_STOPPING_SEAM_RETIRED`

if and only if:

1. both repetitions are byte-identical and strong-verify the exact source tree;
2. both repetitions have `post_placement_tail_fraction < 0.15`.

Interpretation: even deleting every post-Placement instruction for free cannot plausibly close the already-measured Shifted release gap. The stopping-proof search must move **inside Placement before a material fraction of edge/mosaic work has elapsed**, or the family must be retired if no exact early forced-state/admission proof exists there.

`POST_PLACEMENT_STOPPING_SEAM_REMAINS_PLAUSIBLE`

if either valid repetition leaves >=15% of attempt-5 wall after Placement. This authorizes a later frozen intervention at that seam; it does not authorize a heuristic skip or grant product credit.

`CANDIDATE_INVALID`

for byte drift, verification/tree mismatch, missing timing ownership, or instrument failure.

## Invariants / oracle honesty

Never gifted: archive bytes, source/base bytes, tournament candidate, representation/control bytes, exact reconstruction, integrity, locality, recovery, or winner identity. Timing wrappers receive no semantic authority. Existing builders are unmodified.

This experiment has **zero release credit** under every outcome. It cannot relax the 1.10x/1.25x runtime bands, re-overlap PrefixGraph and G0-G4 lifetimes, or skip G0-G4 in the shipping selector.

## Next action by result

- `...RETIRED`: instrument the earliest exact forced-state/admission seam *inside* attempt-4 Placement; prioritize a proof before exact delta/mosaic work, not after serialization.
- `...PLAUSIBLE`: freeze a post-Placement exact-bound Builder experiment and measure avoided wall plus winner identity.
- `CANDIDATE_INVALID`: repair only the instrument and supersede this freeze if material semantics must change.
