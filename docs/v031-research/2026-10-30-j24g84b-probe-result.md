# J24G84b — charged low-level selector falsifies frontcoded metadata product path

Date: 2026-10-30. **DECISIVE NEGATIVE O0 RESEARCH RESULT — NOT PRODUCT EVIDENCE.**
Frozen before code: [J24G84b prereg](2026-10-30-j24g84b-probe-prereg.md), commit `311a6cabbe0e06afd0cab0179f561e750c3ce6dc`.
Measured code blob `463b5b54b08e7d5d4bdba2beb41d485bde5ea8a8`; exact hosted HEAD `c1db6c5fa69448e39e74f71847b9d34e30ac3bd3`; GitHub [Actions #41063716261](https://github.com/FCMO-AI/.CMPCT/actions/runs/41063716261), **SUCCESS** on Ubuntu 24.04, original [artifact #12981002517](https://github.com/FCMO-AI/.CMPCT/actions/runs/41063716261/artifacts/12981002517). Independently downloaded ZIP SHA-256 `7133d0eb6db7c589505edbac836bc6c56314b57628a250b7c95233eb95ab1257`, matching the original GitHub provider digest. Detached no-CMPCT arithmetic audit reproduced all six rows/median/selection/decision and passed. The historical J24G84 O0 negative remains in [the first result](2026-10-30-j24g84-frontcode-o0-result.md).

## Prediction, actual result, negative knowledge

Prospective H1 required (a) zero false positive L19 byte admission, (b) >=2 of 6 representative real-Builder index families saving >=5% AND >=256 full compressed index bytes after one candidate tag, and (c) full L1-dual-probe + final L19 policy median wall at most 1.15x direct L19 baseline in **every** case. The criterion **failed**: `CHARGED_L1_SCOUT_NOT_PRODUCT_ELIGIBLE`. Three families won bytes, one held-out structurally different family **lost 97 bytes** to a false L1-based frontcoding admission, and **three families exceeded +15% creation wall overhead**.

### Real complete-index Zstd19 evidence

| Authentic index family | Zstd1 original / frontcoded (B) | Zstd19 original (B) | Charged chosen (B) | Signed saved (B) | Selector choice | Whole-encoding wall ratio |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| Flat | 1,710 / 488 | 1,257 | 465 | +792 | frontcode | **1.2425x** |
| Deep | 8,249 / 1,849 | 4,221 | 1,414 | +2,807 | frontcode | 0.6587x |
| Random/hash | 69,360 / 70,492 | 65,921 | 65,921 | 0 | original | **1.5027x** |
| Unicode | 12,195 / 5,307 | 8,708 | 3,477 | +5,231 | frontcode | 0.5449x |
| Held-out random salt | 52,276 / 53,031 | 49,054 | 49,054 | 0 | original | **1.4995x** |
| Held-out deep with hashed leaf | 39,533 / 38,653 | 35,803 | **35,900** | **-97** | frontcode (false) | 0.7411x |

Wall medians derive from ten direct L19 repetitions vs ten calls which fully charge L1 probes, construction of the candidate and the chosen L19. Zstd19 values are **complete compressed index payloads**, not complete stored CMPCT archive bytes; candidate pays one optimistic selector/tag byte and skips no existing metadata. Actual physical base archives were created with the unmodified Builder. The candidate representation never became a valid revision-24 archive. Hence **no archive-size/product win or new release evidence**.

### Causal interpretation / counterfactual

- A cheap Zstd1 probe correctly rejects the purely random and salted-random negative families, but **misclassifies mixed deep/hash-like siblings**: at L1, frontcoded 38,653 B beats 39,533 B, while at L19 its 35,899 B is worse than original 35,803 B; the optimistic 1-byte tag increases the loss to 97 B. At the full original-index boundary, cheap compression ordering is **not order-preserving** under stronger compression. Any generic rule that assumes L1 ranks L19 is false.
- The policy also spends 1.50x wall on obvious strongly negative random classes, because it constructs and compresses both alternatives at L1 before falling back to ordinary L19. Thus this scout *exports substantial CPU/wall without byte benefit* on exactly the inputs where fallback matters most.
- The three positive cases are preserved as **scoped representation headroom**, not a sufficient basis for a product codec or per-fixture admission. A gifted oracle choosing the L19 min has zero false admission but is a computational upper bound: performing both complete L19 encodes, plus decode complexity, cannot be assumed free.
- Early observable that could have stopped escalation sooner: original O0 random-name compressed-loss already required a conditional selector. A minimal L1-vs-L19 ordering check on a deep/hash adversarial case plus CPU charge would have rejected the simplistic policy without a six-case full file build. This *prospective structural adversary class* is transferable to future candidate admission gates; no discovery-policy change follows from only this family.

### Strongest limitations
One Ubuntu host, warm in-process Python, 2048 small files per structural family, partly deduplicated file content; no native, Windows/macOS, RSS, cold index, selective access, replay, hardlinks/xattrs, full product archive or ZIP/Zstd competitor measurement. `cpu_debt_families` in the raw JSON field name is **misnamed**: the detector actually uses **wall-time >1.15x**, not CPU; retain raw trace and interpret it correctly. Do not rewrite frozen receipts because the field name is clumsy. The candidate path's additional tag/framing might exceed the optimistic 1 B, strengthening the negative; no hidden format-credit.

## Decision / frontier

**Retire unconditional path frontcoding as generic index replacement and the unconditional double-Zstd1 scout as economically bounded admission.** The scoped ~60–66% complete index savings of flat/deep/Unicode remain research seeds, but a narrower future mechanism needs a *prospective input-structural guard* that can reject low-common-prefix/high-entropy name cohorts **without performing two full compressions**. Before code, preregister a cheap structural predictor and challenge it on mixed hash/deep, Unicode, deep random, disordered and hostile path lists. Material cost must be charged against canonical Reader/writer and full archive, including restart-index/random-access decoding, authentication and format tag. Until then, return allocation to established higher-value Writer/Reader owners #833/#829/#795; avoid a third variant of the same selector mechanism without new causal evidence.

No change to policy, benchmark, release law, Discovery STATE (owned by #574) or shipping code. **Credit: research negative and bounded headroom only; product/release=0.**
