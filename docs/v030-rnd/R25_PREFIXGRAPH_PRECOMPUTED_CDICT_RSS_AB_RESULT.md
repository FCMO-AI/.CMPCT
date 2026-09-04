# r25 exact PrefixGraph precomputed-CDict RSS A/B result

Status: **CLOSED / FORGE NEGATIVE / NO RELEASE CREDIT**

This record closes the frozen experiment in `R25_PREFIXGRAPH_PRECOMPUTED_CDICT_RSS_AB_PREREG.md` without changing its candidate grammar, thresholds, corpus, compressor level, dictionary bytes, anchor set, or interpretation.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`
- exact result-bearing source: `aa48dde959ddba9ef46d0885faa2c8c4163ef47a`
- workflow: `CMPCT v0.30 PrefixGraph precomputed-CDict RSS A/B`
- workflow run: `33628914135`
- substantive job: `100244017670` (`precomputed-cdict-ab`)
- artifact id: `9846129969`
- artifact: `v030-prefixgraph-precomputed-cdict-rss-ab-aa48dde959ddba9ef46d0885faa2c8c4163ef47a`
- artifact digest: `sha256:1d11315220b8f4158caf43fe8874f3f6318413f49f7faf9034530b9e16b2d968`
- schema: `cmpct-v030-prefixgraph-precomputed-cdict-rss-ab-v1`
- release credit: `false`

The substantive measurement, exact-byte identity ratchet, frozen decision ratchet and CI-topology self-check all completed successfully.

## Frozen identity gate

The A/B compared the current exact raw-prefix dictionary constructor with the same dictionary bytes and level-19 compressor after calling `precompute_compress(level=19)`.

The stronger candidate-set identity gate passed: the all-direct candidate plus every one of the 18 nominated anchor candidates had the same complete bytes and SHA-256 under both constructor paths. The final selected archive also matched exactly across all six measured builds:

- semantic owner: `experiments._v030_canonical_prefixgraph`;
- source tree SHA-256: `d9106dcdc8f965d45236c241d6c45f773e10b84ac204acc3c3521d889cd3a8fd`;
- selected anchor: `0`;
- anchor auditions: `18`;
- complete selected archive: **1,700,242 B**;
- archive SHA-256: `61305dc8fff0853f773d8847631c7b7476a8465c259c49c3c1b93c3aa93ec745`;
- strong verification: pass in every repetition.

This rules out a semantic/output change as the explanation for the memory result.

## Exact result

| arm | median total peak RSS | median incremental peak RSS | median wall time |
|---|---:|---:|---:|
| inherited raw-content CDict | **199,568 KiB** | **76,536 KiB** | **15.0308 s** |
| precomputed CDict | **229,252 KiB** | **106,220 KiB** | **15.2667 s** |

Per-round inherited incremental peaks were 77,260 / 76,536 / 76,104 KiB. Precomputed-CDict incremental peaks were 105,780 / 106,220 / 107,180 KiB.

Frozen metrics:

- `rss_reduction = -0.3878436291` — i.e. precomputation made incremental peak RSS **38.784% worse**;
- `wall_ratio = 1.0156964925` — about **1.57% slower**.

Frozen retirement threshold: `rss_reduction < 0.05`.

## Decision

**`PRECOMPUTED_CDICT_RETIRED`**

Precomputing the raw-content dictionary's level-19 compression tables is not a rehabilitation path for the supported PrefixGraph CCtx allocation on the frozen Shifted workload. It preserves the complete candidate set exactly but increases memory materially and slightly worsens runtime.

Do not productize this constructor change for RSS and do not rerun it with altered thresholds, levels, dictionary bytes, anchor sets or corpus identity. A different zstandard implementation or materially different compressor-construction API is a distinct hypothesis and requires its own freeze.

## Causal interpretation

The predecessor v2 attribution remains valid: one live raw-prefix `ZSTD_CCtx` is still a material exact-owner allocation, accounting for about 88.51% of PrefixGraph's measured incremental high-water under that experiment. This negative says only that **precomputed CDict tables do not reduce that cost**. In fact, the implementation appears to retain additional prepared state while the same compressor still allocates its large context.

The result therefore narrows the next Forge question from "is CCtx material?" to "which same-semantics compressor construction/lifetime route can avoid or contain that workspace?" The answer may also be that the exact level-19 dictionary-compression semantics intrinsically require roughly this workspace in the current zstandard implementation; that must be demonstrated rather than assumed.

## Scope and release law

No production source changed. No benchmark, locality/decode-unit, recovery, integrity, grammar, selected bytes or competitor setting changed. This is diagnostic causal evidence only and grants no release credit. Complete-product Shifted RSS remains governed by the unchanged v0.30 release authority.

## Reopening predicate

Reopen precomputed-CDict preparation only if the zstandard binding/library or the exact compressor-construction semantics materially change and there is new allocator evidence that the precomputed path no longer retains the measured extra state. Runner noise or a different reporting denominator is not a reopening predicate.
