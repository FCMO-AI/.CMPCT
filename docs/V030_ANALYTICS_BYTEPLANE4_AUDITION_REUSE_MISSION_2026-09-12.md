# v0.30 Analytics BytePlane4 audition-reuse mission — 2026-09-12

Status: **research-only Mission Lock / Referee** following the level-17 crossover and hostile-transfer negative. No format/release/comparator/ONE authority changes.

## Causal evidence

The fixed BytePlane4 + L17 Analytics seed crossed accepted v0.29 at **6,134,444 B** and was 55.5% faster than direct L19. A generator-distinct hostile transfer then failed only because `counter32` spent ~0.378 s recompressing the already-transposed payload at level 17; both structured positives had huge byte wins and both entropy-dense negatives produced zero transform selections.

Implementation review shows the width-4 shuffle and a **Zstd-1 transformed payload** are already computed inside the cheap audition before that expensive strong encode. Recompressing the same shuffled bytes at level 17 may therefore be redundant work.

## Falsifiable hypothesis

Freeze direct baseline level 17, BytePlane width 4, the same frame marker and the same path-blind cheap gate. When `framed(Zstd-1(BytePlane4(raw)))` is smaller than direct Zstd-1 and also strictly smaller than direct Zstd-17, store those already-computed framed level-1 bytes directly. Do **not** run a transformed level-17 encode.

The reuse mechanism earns continuation only if, on the frozen Analytics tree:

1. archive bytes are **<= accepted v0.29 6,135,172 B**;
2. reconstruction and deterministic size are exact;
3. complete verified creation is at least **10% faster** than the already-positive strong BP4+L17 seed measured in the same rotated run; and
4. candidate adds no more than **0.35 s** versus direct L17.

The 10% hurdle is material but intentionally smaller than the previous crossover hurdle because the strong L17 seed is already a major speed improvement. The 0.35 s ceiling prevents a cheap-proof mechanism from quietly moving cost elsewhere.

## Referee contract

- Same normalized `neutral_hostile_v1/04_analytics_and_database` input.
- Four modes, three rotated rounds: direct L17, audition-reuse BP4+L17, prior strong BP4+L17, direct L19.
- Freeze level=17, width=4, exact existing shuffle/inverse, frame marker and level-1 gate. No sweep.
- The reuse candidate may execute direct L17 plus the already-required direct-L1 / transformed-L1 audition. It may never execute transformed L17.
- Store transformed L1 only when its fully framed bytes beat direct L17 exactly; otherwise fall back to direct L17.
- Measure archive bytes, verified creation, CPU/wall/RSS, gate CPU, selected count, selected transformed bytes and bytes saved.
- Path, extension, workload identity and pack ordinal are forbidden policy inputs.
- Green CI means a valid receipt, not a positive result.

## Decision

- **PASS — `AUDITION_BYTES_ARE_PRODUCTIVE_OUTPUT`:** all four continuation gates pass. Preserve the mechanism and rerun the exact frozen hostile fixtures with no generator changes.
- **FAIL — `RETIRE_AUDITION_REUSE`:** any gate fails. Preserve the negative; do not tune compression level, width or audition threshold. Keep the strong BP4+L17 seed as the best Analytics research point and move to a different global execution mechanism.

This is explicitly an ONE-derived efficiency lesson (reuse already-computed proof work) applied inside v0.30 semantics, not a transplant of ONE representation. `research/cmpct1` and frozen Genesis remain unchanged.
