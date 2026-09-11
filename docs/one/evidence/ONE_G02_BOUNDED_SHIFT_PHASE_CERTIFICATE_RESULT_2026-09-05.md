# ONE-G0.2 — sparse bounded-shift phase certificate result

Date: 2026-09-05
Experimental line: ONE-G0.2
Decision: **reject as a standalone complete nominator; preserve unchanged for cold-complement testing**

## Exact-source receipt

- source: `b081fc3760f4b5bdfe7cf2b899af82621527504b`
- workflow: `33971678648`
- job: `101321187363`
- artifact: `9971128616`
- artifact digest: `sha256:ce9edaa1bbb65812935bf1c75bc9e96d8ff6479e92568c3a8544642843cb8d16`
- semantic/hostile ONE suite: passed before the result-bearing validation

The workflow is red because the frozen validator exits nonzero when any required positive is missed. Artifact preservation succeeded.

## Frozen gate result

The sparse phase certificate missed **1 required positive** in the 105-row matrix:

- 4 KiB;
- seed 59;
- contiguous quarter-damage case;
- exact relation oracle: enabled, best shift `+1`, four exact proofs;
- phase certificate: no nomination.

All independent-random negatives remained unnominated. Maximum sampled-position fraction was **0.18749237060546875**, below the frozen 19% ceiling. Modeled retained witness payload remained **240 bytes**.

The candidate therefore fails its preregistered standalone structural gate. Do not change stride, phase set, witness count, or threshold to relabel this run as a pass.

## Causal replay of the single miss

For a `+1` relation, the target phase-0 sample maps to source phase 31. On the exact failing generator, the four globally bottom-ranked phase-31 source witnesses were at positions:

- 1375
- 1631
- 1759
- 1919

Their matching target positions are 1376, 1632, 1760 and 1920. The quarter-damage interval is target `[1365, 2389)`. **Every one of the four selected witnesses is therefore destroyed by the same contiguous damaged region.**

This localizes the failure: the sparse phase geometry is not the immediate problem; global content ranking provides no spatial-diversity guarantee. A larger bottom-K would be threshold tuning and is forbidden by the frozen disproof rule.

## Why the mechanism is not yet discarded as discovery knowledge

The intended architecture is a cascade, not a standalone replacement for existing observation:

1. the promoted shared Gear/reuse observer runs anyway;
2. only if it is silent does a replayable content-local fallback run;
3. a sparse relation falsifier rejects cheap false patterns;
4. exact relation proof remains authoritative.

The standalone phase certificate was deliberately tested more strictly than that cascade requires. Its single miss may be irrelevant if the already-paid shared observer nominates that same pair. Conversely, the phase certificate is only useful if it recovers **shared-observer misses** without making the cascade expensive.

That complementarity is a new falsifiable composition and must be preregistered on generator-distinct seeds. The certificate itself remains unchanged; no post-result parameter rescue is allowed.

## Strongest negative / self-critique

A bounded static witness set can spatially cluster even when its hash values look diverse. Content diversity is not spatial diversity. This is precisely the kind of structural brittleness that a writer-side opportunity gate must expose before native optimization.

## Claim boundary

No density, reader-speed, release, or v0.29/v0.30 comparison claim is authorized. The only supported conclusion is that the fixed 20-witness sparse phase certificate is **not a complete standalone nominator** in its frozen form.