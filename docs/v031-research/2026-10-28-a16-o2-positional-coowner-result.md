# A16-O2 positional co-owner proof — current research result (2026-10-28 UTC)

Status: **SCIENTIFIC LOCAL NEGATIVE/BOUNDARY; SOURCE-EXACT HOSTED COURT PENDING**. This document does not change CMPCT product state. The frozen pre-implementation prediction is `2026-10-28-a16-o2-positional-coowner-prereg.md`, commit `a0b75a33f17c67c749c467227266092ba799c224`.

## Problem, source and strongest controls

Published `main@80c358f8824ec1b20d349c92ed94c898090969b0` remains v0.30.0/r24. A16-O0/O1 PR #683 source `acaa48a74c2e8859e476c629bf1debab25e89f37` supplied identical deterministic 32 x 64KiB inputs, the optimized fixed 4KiB CHUNKREF, independent whole-member direct Zstd-19 and a binary shared-class SEGREF. The old binary family measured a 7.855x storage explosion on incompatible co-owner overlaps. The current isolated A16-O2 branch changes the **proof frame** to exact position-scoped member incidence, not a threshold or a codec.

For each 4KiB position and exact byte value, compute the full member-incidence bitmask. Merge adjacent positions in a member only if those incidence sets are exactly equal. If the two sets are the same S, all members in S contain both original byte strings at the same positions; their concatenation is identical across S. Induction extends the statement to longer runs. Complete input bytes, not a digest match alone, decide membership. It is **not** a proof of smaller compressed bytes, better extraction, or safe on-disk/Reader integration.

## Reproducible local component observations

A local Python 3.13.5 / libzstd / zstd CLI experiment ran all 16 cases, reconstructed all 2,048 source members independently across four scientific arms, and a separately implemented parser/referee rejected 14/14 selected forged receipts or corrupt-envelope cases. These observations come from a standalone local prototype, **not yet from the newly committed exact GitHub source**, so numerical CPU/wall claims remain preliminary until the hosted court returns source-bound receipts.

| Case (same size across two seeds) | Fixed CHUNKREF | Old binary SEGREF | Exact positional SEGREF | Positional / fixed |
|---|---:|---:|---:|---:|
| 12-block shared prefix | 582,132 B | 576,446 B | 576,446 B | 0.990232 |
| 12-block shared suffix | 582,132 B | 576,446 B | 576,446 B | 0.990232 |
| Identical members | 68,524 B | 66,878 B | 66,878 B | 0.975980 |
| Alternate sharing | 1,095,740 B | 1,096,796 B | 1,096,796 B | 1.000964 |
| Independent members | 2,122,956 B | 2,100,044 B | 2,100,044 B | 0.989207 |
| Incompatible overlapping co-owners | 267,340 B | **2,100,044 B** | **267,596 B** | **1.000958** |
| Shifted repeated blocks (held-out) | **689,824 B** | 739,620 B | 739,620 B | **1.072188** |
| Aligned permuted co-owner groups (held-out) | 267,340 B | 2,034,458 B | **264,428 B** | **0.989108** |

The **5x+ hostile amplification is eliminated** in this research envelope without modifying the inherited control. On the two shifted held-outs, even the exact co-owner rule still increases complete physical bytes by **7.22%** versus fixed 4KiB blocks; positional safety is not compression dominance. The charged portfolio `min(direct, fixed, positional)+1 selector byte` avoids this stored-byte loss by selecting fixed on shifted/hostile. It does **not** erase creator CPU/memory or renderer complexity paid to discover/attempt candidates.

On prefix/suffix, positional grouping keeps two decode units/member. Local seven-repetition in-process full-member Q32 decode observed roughly 2.34–2.60x lower wall than fixed, under explicit per-member re-decode and SHA verification. The inherited joint hypothesis remains **FALSE** because a 0.9768% byte improvement is below the preregistered 1.0% threshold, regardless of decode speed. This is not product-level proof. On the held-out aligned permuted groups, the local component produced about 1.97–2.11x lower wall with about 1.09% fewer bytes; a useful **synthetic seed**, not evidence of natural prevalence.

Python `tracemalloc` during isolated incidence-and-encoding found ~4.25–6.48 MiB peak traced allocations in the local research implementation, depending on entropy/unique owners. Its traced create timing is **observer-perturbed** and must not be equated to a fair untraced production benchmark. The hosted court separately times untraced creation and probes incidence memory, but still does not measure installed Reader RSS, cold-open, filesystem I/O, multi-platform service economics, real-source prevalence, or reliable concurrent source ownership.

## Falsification, causal implications and counterfactual

The positional co-owner condition is sufficient to preserve shared *concatenated bytes* at aligned locations. It is insufficient to guarantee a storage win, and is expensive to discover through per-position full byte comparison. The shifted counterexample, with consistent inputs and unchanged controls, is a structural disproof of universal byte dominance. Selector fallback is a storage safeguard, not a free performance oracle.

A cheaper earlier discriminator could have counted precise member-incidence sets (not just binary shared flags), then tested the source-size bound on conflicting co-owner runs before ever building the huge old SEGREF frame. This supports a prospective **experiment-order lesson**, not modifying Discovery policy or release law.

## Coordination, safety and promotion boundaries

This branch descends from PR #683 without modifying it; all new files belong to O2 research/CI/docs. Existing #574 Discovery reconciliation, #662/#676 ABI3 Reader, recovery, MessagePack and v0.30 benchmark/frozen history stay untouched. The detached evidence tests exact source SHA, frame/member SHA, reference bounds, full reconstruction, and positional partitions; hostile mutations are required to fail.

Research envelopes marked `SR16` are not native CMPCT archives. No new codec, reference grammar, filesystem semantics, persistent metadata, release version or shipped Reader behavior is implemented. Numerical sizes are scientific complete envelopes, not released CMPCT archive measurements.

**Decision:** positional incidence proof removes the prior catastrophic sharing error, but does not satisfy the inherited joint criterion or generalize to all shifted structural inputs. Do not productize it. The next justified work would require actual non-synthetic incidence prevalence, bounded generic owner discovery, strong direct/fixed competition, optional admission without exported create/RSS losses, and real installed-Reader security/locality. Existing product-oriented owner claims should receive priority unless such evidence emerges.

## Source-exact hosted verification handoff

Workflow `.github/workflows/v031-a16-o2-positional-coowner.yml` targets two Ubuntu environments, requires a real PR HEAD checkout and records `source-head.txt`, independent re-decoding, and all raw envelopes/receipts even on a negative outcome. **No hosted result or final-head green check is claimed in this document until GitHub Actions supplies it.** If a hosted result contradicts these preliminary local observations, preserve both, diagnose the source/host distinction, and prefer the source-bound result.
