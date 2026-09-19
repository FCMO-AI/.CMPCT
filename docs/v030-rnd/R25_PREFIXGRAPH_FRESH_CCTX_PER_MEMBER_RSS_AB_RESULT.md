# r25 exact PrefixGraph fresh-CCtx-per-member RSS A/B result

Status: **CLOSED / ACCEPTED SCOPED FORGE NEGATIVE / NO RELEASE CREDIT**

This record closes the frozen experiment in `R25_PREFIXGRAPH_FRESH_CCTX_PER_MEMBER_RSS_AB_PREREG.md`. The experiment tested whether canonical PrefixGraph's reuse of one same-semantics level-19 raw-dictionary `ZstdCompressor` across sibling trials materially inflated its exact-owner RSS high-water. It changed no production code, representation grammar, candidate set, dictionary bytes, compression level, tie law, locality/decode-unit rule, recovery/integrity requirement, benchmark threshold, or release state.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`
- exact result-bearing source: `1934fd7bf19606df80d56da3ad42c7d5d5995166`
- workflow: `CMPCT v0.30 PrefixGraph fresh-CCtx-per-member RSS A/B`
- workflow run: `33671324742`
- substantive job: `100386481503` (`fresh-cctx-ab`)
- artifact id: `9862827590`
- artifact: `v030-prefixgraph-fresh-cctx-rss-ab-1934fd7bf19606df80d56da3ad42c7d5d5995166`
- artifact digest: `sha256:211230d3bc15b30ad805da41a8bd89dcfd284a3d3df9b8db4a7c221f1f677647`
- schema: `cmpct-v030-prefixgraph-fresh-cctx-per-member-rss-ab-v1`
- runner: Ubuntu 24.04.4 / Python 3.11.16 / zstandard 0.25.0
- rounds: 3, alternating arm order
- experiment valid: `true`
- release credit: `false`

The exact-output measurement, decision ratchet, CI-topology self-check, and artifact upload all completed successfully. This is substantive result-bearing evidence, not a classifier-only green.

## Frozen identity gate

The candidate arm kept the exact canonical PrefixGraph semantic owner, raw-content dictionary bytes, level-19 compression semantics, all-direct candidate, every nominated anchor candidate, pricing, and selection law. The only intervention was compressor lifetime: baseline reused one compressor across an anchor's sibling trials; fresh-per-member constructed a new compressor with the same dictionary and level for each `.compress(raw)` call.

The workflow proved:

- full candidate-set byte identity: **true**;
- complete selected-build identity: **true**;
- source tree identity: **true**;
- strong verification: **pass**;
- no production change: **true**.

Therefore the memory/runtime comparison is interpretable as a same-semantics CCtx lifetime test.

## Exact result

| arm | median total peak RSS | median incremental peak RSS | median wall time |
|---|---:|---:|---:|
| inherited persistent CCtx | **199,136 KiB** | **76,056 KiB** | **10.1600 s** |
| fresh CCtx per sibling member | **199,348 KiB** | **76,268 KiB** | **21.6988 s** |

Frozen derived metrics:

- `rss_reduction = -0.0027874198` — fresh construction made incremental peak RSS about **0.279% worse**;
- `wall_ratio = 2.1357041983x` — fresh construction made wall time about **113.57% slower**.

Frozen retirement threshold: `rss_reduction < 0.10`.

## Terminal decision

**`FRESH_CCTX_LIFETIME_RETIRED_AS_PRIMARY_OWNER`**

The exact canonical PrefixGraph high-water is not materially explained by accumulation/growth caused by reusing one compressor across sibling trials. Destroying and reconstructing the same level-19 raw-dictionary compressor for each trial leaves peak RSS essentially unchanged while more than doubling wall time.

Do not productize fresh-per-member compressors and do not continue tuning compressor reuse/lifetime as the primary Shifted RSS explanation without a documented reopening predicate.

## Causal interpretation

This result combines with `R25_PREFIXGRAPH_EXACT_OWNER_CCTX_MEMORY_V2_RESULT.md` and `R25_PREFIXGRAPH_PRECOMPUTED_CDICT_RSS_AB_RESULT.md` to narrow the PrefixGraph memory problem substantially:

1. one live canonical raw-prefix `ZSTD_CCtx` is a material exact-owner allocation (~67.29 MiB self-reported; ~88.5% of measured exact-owner incremental peak in the predecessor experiment);
2. precomputing the same dictionary's compression tables made RSS materially worse;
3. replacing persistent CCtx reuse with fresh same-semantics contexts does not lower high-water at all and carries severe runtime debt.

The surviving explanation is therefore no longer ordinary object lifetime/reuse. Under the tested Python `zstandard`/libzstd implementation and level-19 raw-content-dictionary semantics, the large per-compression workspace itself is the next justified boundary. Forge should move to an implementation/workspace discriminator rather than another scheduler, shell, reclamation, CDict-preparation, or CCtx-lifetime tweak.

This result does **not** prove that the ~67 MiB self-reported context can be mechanically subtracted from complete-product RSS, nor that PrefixGraph alone owns the complete Shifted product peak. It only establishes the scoped same-semantics negative inside the exact canonical PrefixGraph owner.

## Reopening predicate

Reopen persistent-vs-fresh CCtx lifetime only if one of the following materially changes the causal regime:

1. the zstandard binding or linked libzstd implementation changes;
2. new allocator traces show cumulative state specifically retained across sibling calls that this experiment did not actually destroy;
3. canonical PrefixGraph changes to multiple simultaneously live compressors or a different compressor ownership topology; or
4. an exact-output implementation supplies the same level-19/raw-dictionary semantics through a materially different workspace lifecycle.

Runner noise, altered thresholds, fewer anchors, lower compression levels, different dictionary bytes, or simply repeating more rounds are not reopening predicates.

## Forge decision

**`ESCALATE_RADICALITY` within same-semantics implementation rehabilitation.** Preserve PrefixGraph's proven byte gain. The next decisive Shifted memory experiment should ask whether the required level-19 raw-dictionary semantics can be executed by a lower-workspace implementation/API path, or whether the measured workspace is intrinsic to the current compressor parameters. Any intervention must preserve the complete candidate set and exact selected archive bytes before it can advance.

No merge, tag, version bump, publication, or release credit follows from this diagnostic.
