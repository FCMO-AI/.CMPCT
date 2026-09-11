# ONE-G0.2 — direct sparse cold-rescue preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2

## Mission Lock

A pre-result hostile review of the phase-certificate cascade found a structural compute concern: its five source phases plus one target phase sample approximately `1.50n` payload bytes before sparse falsification, while the existing eager exact dispatcher's coverage scan is bounded at approximately `0.15625n` counted comparison bytes before proof.

This experiment tests the narrower same-principle repair: **after shared observation is silent, remove the standalone phase-certificate rescan and invoke the already-frozen 16-probe sparse relation gate directly.** If that gate fires, the unchanged exact safe dispatcher remains the sole authority.

No threshold, shift set, sparse-probe count, exact proof rule, reader operation, or ONE representation changes.

## Falsifiable hypothesis

On the exact same 34 shared-silent pairs used by the frozen native cascade, direct sparse rescue will retain all four eager exact positives while avoiding enough unnecessary full exact dispatches to beat eager exact rescue by at least 10% median elapsed time across sizes.

This is not assumed merely because the sparse gate touches less data. Native timing is authority.

## Frozen input

Use the existing shared-silent matrix exactly:

- 4 KiB: 9 pairs;
- 8 KiB: 7 pairs;
- 16 KiB: 6 pairs;
- 64 KiB: 6 pairs;
- 256 KiB: 6 pairs;
- total: 34 pairs;
- total eager exact positives expected: 4.

Pair generation and shared-silent selection remain outside both timed arms exactly as in the prior native-cascade experiment.

## Candidate

For every shared-silent pair:

1. run the unchanged `one_g02_shift_relation_sparse_gate()` directly;
2. the gate uses its already-frozen 16 evenly spaced probes and shifts `{-2,-1,+1,+2}`;
3. fewer than two supporting probes rejects the pair without exact proof;
4. a firing gate invokes the unchanged exact safe dispatcher;
5. exact safe dispatch remains the only enabling authority.

The sparse gate charges every byte comparison. Its worst-case logical probe accounting is bounded by `16 * (2 + 4*2) = 160` compared bytes per pair, independent of relation length. This accounting bound is a hypothesis-supporting reason to test, not a speed claim.

Modeled incremental transient state over the exact-dispatch result object is 24 bytes: four 32-bit hit counters plus one 64-bit compared-byte counter. Persistent reader/wire state remains zero.

## Timing

Native A-B-B-A timing over complete same-size batches:

- A: eager exact safe dispatch for every pair;
- B: direct unchanged sparse gate, with exact safe dispatch only if it fires.

Use the same repetitions and internal batch scaling as the frozen phase-cascade A/B so timing is directly interpretable.

## Frozen promotion gate

Advance direct sparse rescue toward fused writer integration only if all are true:

- eager exact positives total exactly 4;
- all four are retained with identical best shift;
- no eager-negative pair becomes enabled;
- exact full-dispatch executions in the direct-sparse arm are <=60% of eager pair count over the complete 34-row matrix;
- median `direct_sparse / eager` elapsed ratio across the five sizes is <=0.90x;
- no size exceeds 1.05x eager;
- every sparse compared byte, fire, reject, exact execution, positive retention and negative enable is reported;
- pre-existing ONE semantic/hostile tests pass first.

## Disproof and next interpretation

If opportunity retention fails, retire this direct sparse form; do not tune the two-hit threshold or 16-probe geometry on the frozen matrix.

If retention holds but native elapsed fails, opportunity gating itself is not disproven; the remaining problem is likely exact-dispatch cost on false fires or compiler/branch overhead. Profile that owner before proposing another gate.

If this passes while the phase-certificate cascade fails, the causal conclusion is that the standalone phase rescan was unnecessary compute. If both pass, prefer the simpler direct-sparse path unless the phase path demonstrates a separate retained-opportunity advantage on a newly frozen hostile set.

A pass is conditional writer-discovery evidence only. It is not a density, decoder, format, v0.29, or deferred-v0.30 win.