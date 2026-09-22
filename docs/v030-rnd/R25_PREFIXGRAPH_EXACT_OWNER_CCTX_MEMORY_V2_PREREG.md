# r25 exact PrefixGraph CCtx memory attribution v2 preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION**

This supersedes the old `v030-prefixgraph-cctx-memory` attribution lane for the current canonical r25 product. The older lane remains historical but cannot answer shipping ownership because its measured “shipping” arm invokes `entropygraph_v030_prefixgraph_parallel`, while the canonical product uses the private exact semantic owner cloned by `entropygraph_v030_profile_isolation` as `experiments._v030_canonical_prefixgraph`.

## Question

Within the **exact canonical PrefixGraph semantic owner**, how much of its fresh-process incremental peak RSS is accounted for by one live raw-prefix Zstandard compression context (`ZSTD_CCtx`) under the exact frozen Shifted workload?

This is a scoped allocation-attribution question. It does not claim that PrefixGraph alone explains the complete ~400 MiB product peak; exact semantic-owner evidence already falsified that broader claim. A positive result only identifies a concrete allocation class worth attacking inside PrefixGraph without tuning away its byte win.

## Frozen target and identity

- target: `resemblance_hostile_v1 / 01_shifted_versions` from `benchmarks.v030_release_performance._build_corpora`;
- semantic owner: `experiments.entropygraph_v030_profile_isolation.PG`;
- required module identity: `experiments._v030_canonical_prefixgraph`;
- canonical profile magic: `CMP25PG\0`;
- every exact-owner build must strongly verify to the live source tree;
- all exact-owner repetitions must emit one identical complete archive size/SHA-256/tree identity;
- no production source or profile global may be mutated.

## Instrument

Two fresh-process measurements are repeated twice:

1. **exact-owner build** — call the canonical private `PG.build`, charge fresh-process baseline and peak `ru_maxrss`, then strong-verify with the same exact semantic owner;
2. **CCtx profiler** — materialize the same source and direct Zstd-19 floor, then sequentially instantiate the exact owner’s `_prefix_codec` for every nominated anchor. After each compression trial, record `ZstdCompressor.memory_size()` and discard the trial output immediately. Only one prefix compressor is live at a time.

`memory_size()` is allocator/library self-reporting and therefore diagnostic ownership evidence, not an additive process-allocation counter. The decisive comparison is its repeated maximum against the exact-owner **incremental** fresh-process high-water. Total exact-owner peak RSS is also preserved.

## Frozen interpretation bands

Let `share = median(max_reported_single_cctx_bytes) / median(exact_owner_incremental_peak_rss_bytes)`.

- `share >= 0.50`: **`CCTX_MATERIAL_OWNER_SUPPORTED`** — one live CCtx accounts for a material majority of the exact-owner incremental high-water; next intervention may target CCtx lifetime/native/context reuse while preserving compressor settings and candidate bytes.
- `share < 0.20`: **`CCTX_RETIRED_AS_PRIMARY_EXACT_OWNER_ALLOCATION`** — do not spend the next Shifted RSS cycle on CCtx lifetime absent new causal evidence.
- `0.20 <= share < 0.50`: **`CCTX_ATTRIBUTION_AMBIGUOUS`** — require a narrower causal A/B before changing implementation.

These bands are frozen before execution and may not be changed after seeing results.

## Non-borrowable invariants

The experiment changes no representation, compressor level, dictionary bytes, anchor nomination, candidate set, complete-artifact tie law, reader grammar, recovery/integrity rule, locality/decode-unit bound, benchmark threshold, release state, or selected product bytes. It grants **zero release credit**.

## Reopening / next-step law

A positive signal is not permission to reduce anchors, weaken compression level, or serialize away a byte win. It only justifies an R0-R2 engineering experiment that removes or reuses the measured allocation class while requiring exact output identity. A negative result retires CCtx as the primary allocation target within exact PrefixGraph; the next experiment must move to Python-side raw/direct-payload/final-blob ownership or another measured allocation class.
