# v0.30 H-EFFORT-4 Adaptive-Effort Economics Mission Lock — 2026-09-13

Status: **frozen preregistration for R0/R3 causal research; no Builder authorized**.

## Trigger

H-EFFORT-3 falsified the fixed-L9 recovery-probe policy while exposing two independent facts:

1. false monotonic stopping is real — 19/20 Analytics L9 recovery probes beat the incumbent;
2. sequential effort itself can be economically dominated — on several transfer surfaces the historical ladder consumes more CPU than a direct L19 encode even when no recovery probe is used.

The next question is therefore not another fixed rung or threshold. It is whether already-paid, workload-blind observations contain enough information to choose among **terminate**, **continue**, and **direct terminal effort**.

## Mission Lock

### Falsifiable hypothesis H-EFFORT-4

Across the frozen stable substrate, useful later-level compression headroom and ladder-economic futility are sufficiently structured at pack level that a future generic selector could be justified using only observations available from the pack itself and work already paid before the decision point.

This hypothesis is supported only if the referee finds transferable causal structure. It is falsified for this mechanism family if later-level winners and economically dominated ladder cases are not separable without workload/path identity or information unavailable before paying the disputed work.

### What this run is allowed to do

Build an **observational referee only**. For each physical pack on the exact frozen stable substrate, measure the same raw bytes at levels `1,3,6,9,12,19` and record:

- raw bytes;
- compressed bytes and codec at every level;
- CPU and wall time at every level under repeated same-process measurement;
- cumulative CPU of the historical `3 -> 6 -> 12 -> 19` ladder until its first strictly-worse stop;
- the historical chosen size/level;
- whether the first worse rung is followed by any later strict size recovery;
- best later level and byte headroom missed by historical stopping;
- whether level 9 detects the existence of a later recovery;
- whether a successful level-9 recovery still leaves material headroom at 12/19;
- direct-L19 CPU versus cumulative ladder CPU;
- generic already-known pack facts such as raw size, level-1 ratio and stream-role/hot status when available.

The referee may compute oracle labels and aggregate distributions. It may not learn or tune a shipping threshold, fit a classifier, encode workload/path identity into decisions, or modify the encoder.

### Frozen surfaces

Use the exact stable substrate asserted by H-EFFORT-3. Office and Analytics remain primary explanatory surfaces only because they motivated the question; every other stable workload remains transfer evidence. Corpus identity may label rows for analysis but may not enter any future decision rule.

### Strong controls

1. Same raw pack bytes for every level.
2. Same codec implementation and process for all compared effort levels.
3. Preserve exact source/corpus fingerprint and physical pack identity.
4. Separate per-level CPU from cumulative policy CPU; do not compare incompatible timing boundaries.
5. Report zero-headroom and incompressible packs rather than discarding them.
6. Record hot-role status but do not treat it as an excuse for density loss; it is an observable product constraint.
7. Preserve any non-monotonic curve even when it contradicts the expected mechanism.

## Decision criteria

H-EFFORT-4 does **not** promote a selector. It decides whether a Builder is scientifically justified.

Classify the result as:

- `EFFORT_ECONOMICS_STRUCTURE_PRESENT` only if both of the following are true across more than one structural surface:
  - a material portion of historical missed-byte headroom occurs in packs whose later recovery is visible from observations already paid by or immediately after the historical stop; and
  - a material portion of cases where the sequential ladder is CPU-dominated by direct terminal effort can be identified by generic pre-terminal observations without workload identity.
- `EFFORT_ECONOMICS_PARTIAL` if only one side (headroom continuation or CPU futility) shows transferable structure.
- `EFFORT_ECONOMICS_UNSEPARATED` if the useful decisions require hindsight, workload identity, or essentially paying the terminal work first.

“Material portion” is an evidence description, not a shipping threshold. The referee must emit the full distributions and byte/CPU-weighted contribution so a subsequent Mission Lock can preregister any actual policy criterion without post-hoc gardening.

## Disproof / retirement

If `EFFORT_ECONOMICS_UNSEPARATED`, do not build another increasingly elaborate level ladder. Retire this local selector family as the primary effort path and either:

- use a simpler fixed/direct strategy where its economics are already honest;
- change representation/search ownership so the expensive decision disappears; or
- return to Foundry if the limitation is the information model rather than effort selection.

If structure is present, the next activation may freeze a minimal Builder using only the transferable observations demonstrated here, with held-out and CPU-budget gates defined before implementation.

## Product-credit boundary

This experiment changes no archive representation, reader grammar, filesystem control, integrity, recovery, locality, platform code, release score or historical benchmark. It is R0/R3 causal evidence only.
