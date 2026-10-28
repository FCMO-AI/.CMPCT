# F-01 / O0.1 accepted result

Status: **Foundry evidence / accepted O0.1 result / research only / no release credit**.

## Authority

This record interprets the immutable result produced by the preregistered F-01/O0.1 instrument. It does not modify the frozen grammar, comparator, corpus contract, thresholds or decision law.

Accepted evidence:

- source commit: `c3ef298bcc3fb7f95a65245c9341f112581aa175`;
- workflow run: `33465582063`;
- artifact digest: `sha256:3c4a5ed2195e8f9e0d3937a4f12863645e8f8bd152a49dc615dcac056f881323`;
- schema: `cmpct-v030-foundry-f01-o01-v2`;
- corpus fingerprint: `6b6438aff98e7a9e69ee834fe3f2135cc03acde0babac42100c544519e56c574`;
- frozen decision: **`ADVANCE_COMPOSITION`**.

## What changed in the worldview

The one-stage manual representation frontier is not complete even inside the deliberately tiny O0.1 vocabulary.

Two different exact compositions beat the best whole-target one-stage control after charging the complete serialized research program:

1. mixed lane + record structure: `SPLIT(LANE[8]+DELIM[10])`, 2090 B -> 1538 B, **552 B / 26.41% saved**;
2. adjacent mixed lane widths: `SPLIT(LANE[8]+LANE[16])`, 3086 B -> 2525 B, **561 B / 18.18% saved**.

A post-freeze transfer case also retained material headroom:

- `SPLIT(LANE[8]+DELIM[103])`, 1843 B -> 1416 B, **427 B / 23.17% saved**.

All hostile controls fell back without a false composition win. Exact reconstruction passed for every case.

This is enough to reject the narrow assumption that a bounded one-stage tournament spans all useful structure available to the tested primitive set.

## What did not change

O0.1 does **not** prove:

- production discovery speed;
- full-archive byte wins;
- broad real-world prevalence;
- arbitrary split-boundary synthesis;
- whole-archive locality or recovery;
- native/platform viability;
- superiority to every historical CMPCT research mechanism;
- release fitness.

Search cost remains gifted O0 debt. The result is headroom evidence only.

## Strongest simpler explanation

The winning representation could still be a narrow mixed-structure effect whose value is fully explained by manually combining already-known LANE and DELIM transforms at one obvious segmentation boundary. If so, the best output of F-01 may be a smaller fixed primitive/admission mechanism rather than a general compiler.

That explanation is now the main causal target.

## Operator-space evidence

Observed O0.1 nomination counts:

- DIRECT: 343;
- LANE: 1372;
- DELIM: 203;
- SPLIT: 167.

Winning participation showed SPLIT on three composition winners, LANE on five winning programs and DELIM on three. SPLIT accounts for 1540 aggregate bytes of recovered composition gain relative to the one-stage control on its winning cases.

These counts are not sufficient to claim operator necessity or to prune lane widths. That requires explicit ablation.

## Thesis decision

**ADVANCE_COMPOSITION -> causal ablation.**

Do not expand the grammar. Freeze and run operator-removal tests that answer:

1. does removing SPLIT erase the observed composition headroom as expected;
2. does removing each participating structural family increase the exact best representation on the witnesses that use it;
3. do any existing LANE widths have zero effect on the exact best result across the tested O0.1 regime and therefore qualify as scoped search liabilities;
4. does the evidence point toward a reusable distilled primitive rather than a growing universal DSL.

The next contract is `docs/v030-rnd/F01_CAUSAL_ABLATION_PREREG.md`.
