# r25 exact PrefixGraph CCtx memory attribution v2 result

Status: **ACCEPTED DIAGNOSTIC CAUSAL EVIDENCE / FORGE-CUSTODY / NO RELEASE CREDIT**

This result closes the frozen experiment in `R25_PREFIXGRAPH_EXACT_OWNER_CCTX_MEMORY_V2_PREREG.md`. It supersedes the historical CCtx attribution lane for current canonical r25 ownership because v2 measures the exact private PrefixGraph semantic owner used by shipping rather than the parallel research wrapper.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`
- exact result-bearing source: `cc43f3c49c088025a0478938a5acac15183e8554`
- workflow: `CMPCT v0.30 exact PrefixGraph CCtx attribution v2`
- workflow run: `33626847194`
- substantive job: `100236532743` (`exact-owner-cctx-v2`)
- artifact id: `9845200025`
- artifact: `v030-prefixgraph-exact-owner-cctx-v2-cc43f3c49c088025a0478938a5acac15183e8554`
- artifact digest: `sha256:82173140a91c340a86c8cba19eb7882027bc1cf719643c8c8a05b9334eb99580`
- schema: `cmpct-v030-prefixgraph-exact-owner-cctx-memory-v2`
- release credit: `false`

The scientific measurement and the frozen identity/decision ratchet both completed successfully. The workflow's terminal failure occurred later in the CI-topology self-check and therefore does not invalidate the already-uploaded result-bearing artifact; it also does not make the workflow globally green. The subsequent branch commit `0598c3dbecdce4b9b618bfc8f52a9d88d66aa96d` repaired the exact-SHA concurrency-group topology without changing the measured implementation, corpus, thresholds, or result.

## Frozen target and exact identity

Target: `resemblance_hostile_v1 / 01_shifted_versions`.

Required semantic owner identity was satisfied:

- module: `experiments._v030_canonical_prefixgraph`
- canonical PrefixGraph magic: `CMP25PG\0`
- exact source tree SHA-256: `d9106dcdc8f965d45236c241d6c45f773e10b84ac204acc3c3521d889cd3a8fd`
- exact archive size in both build repetitions: **1,700,242 B**
- exact archive SHA-256 in both repetitions: `61305dc8fff0853f773d8847631c7b7476a8465c259c49c3c1b93c3aa93ec745`
- strong verification: pass in both repetitions
- anchor auditions: 18 in both repetitions

No production source, compressor level, dictionary bytes, candidate set, tie law, grammar, recovery/integrity rule, locality/decode-unit bound, benchmark threshold, or release state changed for this experiment.

## Exact result

Exact-owner build repetitions:

| repetition | baseline RSS | peak RSS | incremental peak | wall time |
|---|---:|---:|---:|---:|
| 1 | 123,012 KiB | 201,124 KiB | 78,112 KiB | 11.2214 s |
| 2 | 123,012 KiB | 200,604 KiB | 77,592 KiB | 11.2002 s |
| **median** | — | **200,864 KiB** | **77,852 KiB** | — |

For every nominated anchor, the raw-prefix Zstandard compressor began at 5,280 B of self-reported CCtx memory and grew to approximately **70,559,923 B** after the sibling compression trials (the final anchor reported 70,559,912 B).

The frozen attribution ratio was therefore:

`70,559,923 B / (77,852 KiB * 1024) = 0.8850919026`

or **88.51%** of the exact-owner incremental fresh-process high-water.

Frozen threshold: `share >= 0.50` => `CCTX_MATERIAL_OWNER_SUPPORTED`.

## Decision

**`CCTX_MATERIAL_OWNER_SUPPORTED`**

Within the exact canonical PrefixGraph semantic owner on the frozen Shifted workload, one live raw-prefix `ZSTD_CCtx` is a material allocation owner. Its self-reported maximum is approximately 67.29 MiB and accounts for about **88.5%** of the measured exact-owner incremental peak RSS.

This is materially stronger than a vague correlation: the experiment first fixed the semantic-owner identity error from the historical lane, then measured the same private owner used by canonical r25, preserved byte/tree identity across repetitions, and crossed the preregistered 50% support threshold by a wide margin.

## Scope and non-claims

This result does **not** say that PrefixGraph alone owns the complete shipping r25 ~400 MiB Shifted peak. Prior exact semantic-owner evidence already falsified that broader attribution: isolated PrefixGraph peaks around ~200 MiB while complete shipping is materially higher.

`ZstdCompressor.memory_size()` is allocator/library self-reporting, not an additive OS allocation counter. The 88.5% ratio is therefore a scoped ownership signal inside the exact PrefixGraph owner, not permission to subtract 67 MiB mechanically from complete-product RSS.

This result grants **zero release credit** and does not authorize weaker Zstd settings, fewer anchors, different dictionary bytes, changed candidate pricing, or altered output bytes.

## Forge implication

The next intervention may now target the supported allocation class at R0-R2, but must preserve the exact candidate set, compressor settings, complete selected archive bytes/SHA/tree, and all release invariants. Prefer an intervention that changes CCtx construction/lifetime/implementation without changing compression semantics. A plausible first discriminator is whether precomputing the raw-content dictionary's compression tables before constructing the same level-19 compressor lowers exact-owner fresh-process peak RSS while emitting byte-identical candidates. If that does not move total peak materially, preserve the negative and escalate to another implementation-level way of supplying the same compression semantics rather than tuning the codec.

## Reopening law

The positive attribution remains scoped to the exact canonical PrefixGraph owner, Python `zstandard` implementation, frozen Shifted corpus, and current level-19/raw-content-dictionary path. Re-evaluate the attribution if the semantic owner, zstandard binding/library, compressor construction path, or source regime materially changes. Do not generalize it to G0-G4, ML, Logs, or complete-product memory without separate evidence.
