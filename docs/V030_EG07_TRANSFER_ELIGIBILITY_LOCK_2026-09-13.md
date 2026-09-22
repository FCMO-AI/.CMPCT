# v0.30 EG07 transfer eligibility map — mission lock

Date: 2026-09-13
Status: baseline-domain mapping; **no EG08 evidence and no release credit**.

## Why this map exists

The first EG08 neutral10 transfer attempted to require EG07/EG08 success on every neutral workload. It stopped immediately on Developer because **EG07 itself** rejected that workload for exceeding its frozen locality/decode limits. The hostile-five transfer likewise showed that the base representation may not be valid on every hostile family.

A transfer cannot fairly call an EG08 mechanism a product loss on an input where its unchanged parent representation is already invalid, and it must not relax the parent's safety/locality limits to manufacture coverage.

## Frozen eligibility rule

Map the domain using **EG07 only**, before consulting any EG08 transfer result.

For each of the ten deterministic current15 workloads and the five deterministic resemblance-hostile workloads, in a fresh process:

1. build `experiments.entropygraph_v030_federated_embedded_fs_candidate_v7`;
2. if build succeeds, run strong verification against the exact source tree;
3. read locality accounting;
4. classify `ELIGIBLE` only if build and strong verify succeed and `within_release_bounds` is true;
5. otherwise classify `INELIGIBLE_BASELINE` and preserve the exact exception/traceback.

No threshold, corpus identity or EG08 result can influence eligibility.

## Use of the map

Only `ELIGIBLE` surfaces may be used for EG08-vs-EG07 generalization claims. `INELIGIBLE_BASELINE` surfaces remain important negative evidence about EG07 coverage, but they are not evidence against the adaptive-effort mechanism because that mechanism deliberately does not alter geometry.

Hostile review of adaptive effort on ineligible EG07 geometries must instead use synthetic fixed-pack controls or another product-valid representation; locality limits may not be widened.

## Preservation

This map changes no representation, selector, locality ceiling, version, release state, Genesis score or ONE evidence. Its only purpose is to prevent invalid transfer accounting.
