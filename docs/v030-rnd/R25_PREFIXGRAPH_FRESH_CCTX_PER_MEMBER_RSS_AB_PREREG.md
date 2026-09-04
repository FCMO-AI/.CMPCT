# r25 exact PrefixGraph fresh-CCtx-per-member RSS A/B preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION**

This experiment follows the accepted exact-owner attribution in `R25_PREFIXGRAPH_EXACT_OWNER_CCTX_MEMORY_V2_RESULT.md`, which showed that one live raw-prefix level-19 `ZSTD_CCtx` accounts for about 88.5% of canonical PrefixGraph's incremental fresh-process high-water on frozen Shifted. It also respects the closed `R25_PREFIXGRAPH_PRECOMPUTED_CDICT_RSS_AB_RESULT.md`; dictionary-table precomputation is retired and is not reopened here.

## Question

Does the current PrefixGraph pattern of reusing one `ZstdCompressor` across all sibling trials for an anchor materially inflate peak RSS because that context grows/retains workspace across successive compressions, compared with constructing a fresh same-level compressor for each sibling trial while preserving the exact raw-content dictionary bytes and every candidate byte?

This is a Forge D1/D2, R0-R2 same-semantics lifetime discriminator. It is not a representation or codec-setting experiment.

## Frozen target and semantic owner

- target: `resemblance_hostile_v1 / 01_shifted_versions` from `benchmarks.v030_release_performance._build_corpora`;
- semantic owner: `experiments.entropygraph_v030_profile_isolation.PG`;
- required private module identity: `experiments._v030_canonical_prefixgraph`;
- required canonical magic: `CMP25PG\0`;
- payload compression level remains exactly `19`;
- dictionary bytes remain exactly the selected anchor raw bytes with `DICT_TYPE_RAWCONTENT`;
- anchor nomination, full candidate set, complete-artifact pricing and `(archive_bytes, anchor)` tie law remain unchanged;
- production source is not changed by this experiment.

## Arms

1. **baseline / persistent-CCtx:** inherited exact owner. `_prefix_codec(anchor_raw)` constructs one raw-content dictionary and one level-19 `ZstdCompressor`; that compressor is reused for every non-anchor sibling trial for the anchor.
2. **fresh-per-member:** construct the same raw-content dictionary once for the anchor, but the object supplied to `_serialize_candidate` creates a new `ZstdCompressor(level=19, dict_data=same_dictionary)` for each `.compress(raw)` call and drops it immediately after that trial.

No trial may change input bytes, dictionary bytes, compression level, candidate eligibility or selection.

## Exact identity gate

Before RSS interpretation, baseline and fresh-per-member must match for the all-direct candidate and every nominated anchor candidate on:

- complete candidate byte count;
- complete candidate SHA-256;
- `prefix_records`;
- `payload_saving_bytes`;
- source tree SHA-256.

Across measured builds, both arms must also produce one identical selected archive byte count/SHA-256/tree, selected anchor and audition count, and strong verification must pass. Any mismatch => `INVALID_EXACT_BYTE_IDENTITY`; no performance conclusion.

## Measurement

Run three alternating-order fresh-process rounds per arm on Ubuntu 24.04. Record baseline `ru_maxrss`, total peak `ru_maxrss`, incremental peak, and wall time. The decisive memory metric is the median incremental peak RSS of fresh-per-member relative to baseline. Total peak remains preserved for context.

Let:

- `rss_reduction = 1 - fresh_median_incremental_rss / baseline_median_incremental_rss`;
- `wall_ratio = fresh_median_wall / baseline_median_wall`.

## Frozen decision bands

- `rss_reduction >= 0.20` and `wall_ratio <= 1.25` => **`FRESH_CCTX_LIFETIME_REHAB_SUPPORTED`**. Context growth/reuse is a material owner worth productizing/rehabilitating next, still subject to full product gates.
- `rss_reduction < 0.10` => **`FRESH_CCTX_LIFETIME_RETIRED_AS_PRIMARY_OWNER`**. Do not spend the next Shifted cycle on compressor reuse/lifetime; move to the intrinsic compressor-workspace/implementation boundary or another measured owner.
- otherwise => **`FRESH_CCTX_LIFETIME_AMBIGUOUS`**. Require a narrower allocator/workspace discriminator before production change.

The thresholds are frozen before result-bearing execution and may not be edited afterward.

## Hidden costs and non-borrowable invariants

Charge all compressor construction work inside wall time. No benchmark threshold, representation bytes, locality/decode-unit bound, recovery/integrity rule, parser state, native/platform requirement or release condition changes. This experiment grants **zero release credit**.

A supported result does not authorize lower Zstd levels, fewer anchors, different dictionaries or candidate pruning. A retired result means the current same-semantics fresh-context lifetime idea is closed absent a materially different zstandard binding/implementation or new allocator evidence.

## Forge audit

- strict target: Shifted release peak RSS `2.9603316534x -> <=1.25x` versus genuine r24;
- diagnosis: D1/D2 within a D5 product candidate;
- minimum radicality: R0 discriminator, at most R2 if supported;
- saturation context: S2/S4 warns against more scheduler/shell micro-tuning; this test attacks a newly measured 67 MiB-class exact-owner allocation instead;
- RPS: 86/100 — release necessity 15, upside 17, root-cause fit 15, generality 8, information gain 15, experiment efficiency 7, product survival 7, simplicity/portability 2;
- strongest failure explanation: one fresh level-19 raw-dictionary CCtx already needs roughly the same maximum workspace, so destroying/recreating it cannot lower `ru_maxrss` and may worsen runtime/allocator churn.

Terminal action is exactly one of: `PROMOTE_NEXT_PREREQUISITE` if supported, `ESCALATE_RADICALITY` if retired, or `REHABILITATE_DEBT` only after a supported implementation survives exact product evidence.
