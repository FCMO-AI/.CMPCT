# Shifted product-metadata determinism causal preregistration

Status: **FROZEN FORGE D2 / CUSTODY CAUSAL CHECK / ZERO RELEASE CREDIT**

## Motivation

The frozen PrefixGraph Builder S6 receipt on exact source `169333c9f43e05ed07590ba666da0a56535d486e` invalidated because its preregistered genuine-r24 product identity was `29,883,732 B`, while four fresh product-front-door builds in the first result-bearing run all produced `29,883,726 B`. An exact rerun on the same source then produced `29,883,728 B` in both arms. Both runs were internally deterministic, strongly verified, and used the accepted Shifted content-tree bytes, so changing the frozen S6 constant to either observed value would be post-hoc and scientifically invalid.

The Shifted generator writes deterministic contents but does not normalize filesystem mtimes. Canonical r24 preserves filesystem metadata including nanosecond mtimes. This experiment tests the narrow causal hypothesis that fresh-generation mtime variation is sufficient to explain the cross-run product-byte identity drift.

## Frozen target and source contract

- authoritative branch: `agent/v030-authoritative-integration`
- workload: `resemblance_hostile_v1 / 01_shifted_versions`
- generator: `benchmarks/resemblance_hostile_corpus_v1.py::shifted_versions`
- accepted historical content-tree identity: the exact value returned by `benchmarks.v030_release_generalization._accepted_v029_rows()` for this row
- materialization helper: `benchmarks.v030_release_performance._build_corpora`
- measured product front door: `experiments.entropygraph_v030_release_product`
- repetitions per arm: **3 fresh independently generated corpora**
- no release, size, runtime, locality, recovery, integrity, or S6 threshold changes are permitted.

The historical content-tree hash deliberately excludes filesystem metadata. Every generated corpus must still reproduce that accepted historical hash before any product identity is interpreted.

## Arms

### `fresh`

Generate the Shifted corpus through the current runtime-gate materializer and immediately measure it without changing filesystem metadata.

### `fixed-mtime`

Generate the same corpus independently, then set only atime/mtime on the workload root and every descendant to the fixed nanosecond timestamp:

`1767225600000000000` (2026-01-01T00:00:00Z)

No path, file byte, mode, file type, symlink target, or content may change.

## Measurements

For each repetition record:

1. accepted historical content-tree hash;
2. canonical product tree hash;
3. complete selected product bytes/SHA and strong-verification tree;
4. `r24_product_bytes` reported by the promoted product front door;
5. all regular-file mtimes, summarized by a deterministic SHA-256 manifest plus minimum/maximum values.

The experiment is valid only if all six generated corpora reproduce the same accepted historical content-tree hash and every selected product strongly verifies to its own canonical product tree.

## Frozen decisions

`SHIFTED_MTIME_METADATA_CAUSAL_SUPPORTED` iff:

- the three `fresh` repetitions have more than one canonical product-tree identity **and** more than one `r24_product_bytes` value;
- the three `fixed-mtime` repetitions have exactly one canonical product-tree identity and exactly one `r24_product_bytes` value;
- the fixed-mtime metadata manifest is identical in all three repetitions;
- historical content-tree identity is unchanged across every arm/repetition.

`SHIFTED_MTIME_METADATA_NOT_SUFFICIENT` iff the experiment is valid but the support condition above is false.

Any generation, historical-hash, strong-verification, metadata-normalization, or product-front-door failure yields `INVALID_EXPERIMENT` and no causal interpretation.

## Interpretation / next action

Support does **not** authorize changing the old S6 preregistration or claiming the isolation mechanism passed. It authorizes a new superseding S6 freeze whose corpus metadata is deterministic before either control or candidate is built, while preserving the original S6 performance/size/helper/integrity thresholds unchanged. The old invalid receipts remain immutable.

A non-support result retires mtime normalization as the explanation for this exact cross-run drift and requires attribution of the next metadata or product-state owner before any S6 identity is superseded.

Release credit: **false**.
