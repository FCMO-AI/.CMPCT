# v0.30 pathdict exact buffer-reuse v16 — 2026-09-13

Status: **negative research evidence; mechanism retired; no release credit**

Measured head: `a71caf1ec8df726780c28334048a1d970da39eed`

Hosted run: `34751248025`, job `103708057828`

Artifact: `v030-pathdict-v16-a71caf1ec8df726780c28334048a1d970da39eed` (`10316171131`)

Artifact digest: `sha256:46c2c56aae106c344892535657817624c898d8c5546848289ac4e13fc5903338`

## Mission lock

v15 established that the v14 CDict proxy gate generalizes 15/15 while preserving archive identity, but the remaining historical exact `zcd` calls still dominate pathdict creation debt, especially Tiny Files. v16 tested whether a material fraction of that cost was merely Python/ctypes allocation and copying around `ZSTD_compress_usingDict`.

The candidate preserved the frozen v14 selector and proxy, raw dictionary bytes, Zstd level 12, exact historical `ZSTD_compress_usingDict` API, pathdict representation, locality, recovery, integrity and comparator semantics. It reused one `ZSTD_CCtx`, one dictionary buffer and a geometrically grown destination buffer, while passing immutable Python source bytes directly with an explicit length.

Preregistered promotion required all exact frames and complete artifacts to remain byte-identical, plus at least **15% lower exact-call CPU** and at least **3% lower fused-portfolio CPU**. Thresholds were not changed after observing the result.

## Identity / disproof surface

The proof build compared every optimized exact frame against `cmpct.codec.zcd(data, dictionary, 12)`.

- exact calls checked: **5,481 / 5,481**
- frame mismatches: **0**
- complete dictionary artifact identity: **5/5**
- independent artifact identity: **5/5**
- proxy/exact/exact-reject count parity with v14: **preserved**
- normal encode cache misses: **0**

The optimization is therefore semantically and bytewise valid, but performance does not earn promotion.

## Measured result

Across the frozen five-target referee:

| Metric | v14 baseline | v16 | v16 / v14 |
| --- | ---: | ---: | ---: |
| exact-call CPU | 6.7394 s | 6.7177 s | **0.9968x** |
| exact-call wall | 6.7444 s | 6.7216 s | **0.9966x** |
| fused portfolio CPU | 15.4244 s | 15.4005 s | **0.9984x** |
| fused portfolio wall | 15.8053 s | 15.7763 s | **0.9982x** |

This is only about **0.32% exact-call CPU** and **0.16% portfolio CPU** improvement, far below the frozen 15% / 3% hurdle.

The largest remaining source, Tiny Files, executed **4,256 exact calls**. Its exact-call CPU moved only `5.7998 -> 5.7880 s` (**0.99797x**) and portfolio CPU `12.3500 -> 12.3321 s` (**0.99856x**). Developer was effectively flat (`0.99962x` exact CPU). False-neighbor hostile input improved modestly (`0.96148x` exact CPU, `0.96481x` portfolio CPU) but cannot rescue the aggregate mechanism.

The complete v16 fused portfolio remains **2.0316x CPU / 2.0631x wall** versus a single independent build on the same five targets.

## Interpretation

The v14/v15 residual exact cost is not materially caused by repeatedly allocating ctypes source/dictionary/destination buffers. It is dominated by real historical level-12 `ZSTD_compress_usingDict` work for candidates that the safe CDict proxy cannot reject.

Therefore **exact buffer reuse is retired as a performance research line**. Do not follow this result with additional Python allocation micro-tuning or relaxed timing thresholds. Any future pathdict creation win must eliminate, reuse, batch or avoid genuinely necessary compression work while preserving the exact output contract—or explicitly open a new representation experiment whose changed bytes repay all correctness/native/recovery/portability debt from zero.

## Strategic consequence

Pathdict remains useful evidence for a locality-friendly independent-member design and the v14 proxy remains an earned compute reduction. But Tiny Files/pathdict optimization must not become the primary research sink: the frozen Genesis deficit map attributes roughly **96.8% of gross v0.30-vs-v0.29 byte deficit to Office + Analytics**, where the historic mature advantage is primarily representation/physical-context structure.

The next primary density work should therefore return to the strongest unresolved Office/Analytics representation frontier while preserving v14/v15 as the pathdict compute baseline. No Genesis score, R4 aggregate, canonical Builder, format, package version or ONE evidence changes as a result of v16.
