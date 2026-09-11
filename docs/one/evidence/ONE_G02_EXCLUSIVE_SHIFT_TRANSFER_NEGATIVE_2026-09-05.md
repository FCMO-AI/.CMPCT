# ONE-G0.2 — Exclusive shift hostile transfer negative — 2026-09-05

## Authority

Result-bearing source: `2894fd309ff09df539b10cfaa0d78bd1d9941679`  
Workflow: `33960204464` (`CMPCT1 ONE-G0.2 exclusive shift hostile transfer`)  
Job: `101290660276`  
Artifact: `9967691575`  
Artifact digest: `sha256:fb0ad4823450f5ab77df8b519aa874e2e96881e3c5187320e971e9d357fead49`

All ONE semantic tests preceding the transfer passed. The transfer step failed because its frozen scientific decision was negative, not because CI failed to execute.

Claim boundary: hostile writer-discovery transfer only; no reader, wire, product, comparator or release authority.

## Frozen question

The first exclusive non-zero-shift gate passed its original matrix with the inherited 4/8 threshold and sharply reduced probe cost. Before any promotion, this transfer tested both displacement signs, +/-2 displacement, low-entropy periodic controls, independent random data, and an adversarial phase case where a genuine global +1 relation was modified only around the eight deterministic sample locations.

Frozen disproof: any positive-marginal false negative or zero-marginal false positive retires deterministic eight-point sampling as a general gate. No sample locations, displacement set, or threshold may be changed after result-bearing execution.

## Result

Decision: **`retire_deterministic_point_sample_gate`**.

The gate transferred correctly to ordinary signed displacement:

- +1: +65,535 B marginal opportunity, 8/8 exclusive matches, enabled;
- -1: +65,535 B, 8/8, enabled;
- +2: +65,534 B, 8/8, enabled;
- -2: +65,534 B, 8/8, enabled.

It also correctly rejected independent random, zero-filled, AB-periodic and ABC-periodic controls.

### Decisive hostile failure

`phase_damaged_plus1_64k` retained **64,991 B** of genuine minimizer-only marginal reuse opportunity over fixed observation. Only the neighborhoods around the eight deterministic probe sites were damaged. The gate observed:

- fixed opportunity: 0 B;
- minimizer opportunity: 64,991 B;
- exclusive shift matches: 0;
- gate decision: disabled.

This is a direct positive-marginal false negative. The first-gate speed win therefore does not justify general promotion.

## Causal interpretation

The failure is not evidence that exclusive non-zero-shift evidence is useless. It is evidence that **eight fixed point samples are not a sufficient observation topology**. The signal can be locally blinded while almost all of the useful global shifted relation survives.

Reopening predicates must change the observation topology or fuse the signal into already-paid work. Merely moving the eight points, increasing their byte width, hand-adding more points, or relaxing the 4/8 threshold is not a valid reopening.

A separate prior edge-pulse scheduling family is not an escape hatch: exact-head native evidence on source `a0c5c05...` showed only ~15% of promoted state but **1.45x–1.62x** promoted elapsed on large cases and **2.8895x** on an 8 KiB shifted transfer case. Broad always-on sparse scheduling can export more compute than it saves.

## Next research direction

A credible successor should make opportunity evidence a by-product of the fused observation stream, or use a coverage rule whose work scales far below the selector while being materially harder to phase-blind. It must explicitly charge extra source/derived-state traffic and should tie its activation rule to marginal information yield rather than merely detecting resemblance.

Until such a successor passes hostile transfer, the promoted 8 KiB tail-return selector remains the encoder-discovery baseline and the deterministic point gate is retired.
