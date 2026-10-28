# r25 exact PrefixGraph precomputed-CDict RSS A/B preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION**

Predecessor: `R25_PREFIXGRAPH_EXACT_OWNER_CCTX_MEMORY_V2_RESULT.md` established that one live raw-prefix Zstandard compression context self-reports about 70.56 MB and accounts for **88.51%** of the exact canonical PrefixGraph owner's incremental fresh-process RSS on the frozen Shifted workload. This A/B tests the lowest-radicality implementation response that can plausibly move that supported allocation class without changing compression semantics.

## Question

Does precomputing the raw-content dictionary's level-19 compression tables before constructing the same PrefixGraph compressor materially reduce exact-owner fresh-process peak RSS while preserving **every auditioned candidate byte-for-byte**?

The candidate changes only dictionary preparation: after constructing the same `ZstdCompressionDict(prefix, DICT_TYPE_RAWCONTENT)`, call `precompute_compress(level=PAYLOAD_LEVEL)` before constructing `ZstdCompressor(level=PAYLOAD_LEVEL, dict_data=dictionary)`. Compression level, raw dictionary bytes, anchor set, trial order and all archive semantics remain frozen.

## Frozen target and owner

- target: `resemblance_hostile_v1 / 01_shifted_versions` from `benchmarks.v030_release_performance._build_corpora`;
- semantic owner: `experiments.entropygraph_v030_profile_isolation.PG`;
- required private module: `experiments._v030_canonical_prefixgraph`;
- required magic: `CMP25PG\0`;
- repetitions: 3 per build arm, fresh process for every arm, alternating baseline/candidate order;
- exact source tree identity must match between all arms.

## Exact-byte custody

Before performance interpretation, a separate fresh-process identity sweep must construct the all-direct candidate plus **every nominated anchor candidate** under both constructor paths. For every candidate key, complete archive length and SHA-256 must match exactly. The final `PG.build` archive size, SHA-256, tree SHA-256, selected anchor and strong verification must also match across all repetitions.

Any byte/candidate mismatch makes the experiment invalid and grants no intervention credit. A selected-output coincidence is insufficient.

## Frozen measurement

For each build arm record:

- fresh-process baseline and peak `ru_maxrss`;
- incremental peak RSS;
- build wall time;
- complete archive bytes/SHA/tree;
- selected anchor and anchor-audition count;
- strong verification.

Let:

- `rss_reduction = 1 - median(candidate_incremental_peak_rss) / median(baseline_incremental_peak_rss)`;
- `wall_ratio = median(candidate_wall_s) / median(baseline_wall_s)`.

Total fresh-process peaks are retained as diagnostics; the predecessor attribution was defined on incremental high-water, so the primary A/B remains in that same ownership domain.

## Frozen decision bands

Provided the full candidate-set byte-identity gate passes:

- `rss_reduction >= 0.20` **and** `wall_ratio <= 1.10`: **`PRECOMPUTED_CDICT_REHAB_SUPPORTED`** — advance to an exact product-level Builder experiment while preserving output identity and all existing gates;
- `rss_reduction < 0.05`: **`PRECOMPUTED_CDICT_RETIRED`** — precomputed CDict preparation does not materially rehabilitate the supported CCtx allocation; do not productize it for RSS;
- otherwise: **`PRECOMPUTED_CDICT_AMBIGUOUS`** — preserve the result and require a narrower ownership/implementation A/B before product code changes.

A >=20% memory reduction with >10% wall-time debt remains ambiguous, not a win. Thresholds are frozen before result-bearing execution.

## Non-borrowable invariants

No change to compression level, Zstd parameter set requested by PrefixGraph, dictionary bytes, anchor nomination, candidate set, complete-artifact pricing/tie law, representation grammar, locality/decode-unit bound, integrity/recovery, corpus identity, benchmark thresholds or release state. No production module is edited by this experiment. Release credit is **false**.

## Terminal law

If supported, the next step is a Referee->Builder->Hostile Reviewer product A/B on the canonical private owner with exact output identity plus the full Shifted product RSS/runtime gate. If retired, move to another measured CCtx implementation route or the next large Python/native allocation class; do not reduce level/window/anchors to manufacture a memory win.
