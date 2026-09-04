# v0.30 exact-head r24 core / ZIP performance custody receipt — 2026-09-04

Status: **DIAGNOSTIC / SUPERSEDED FOR PROMOTION — benchmark executability proven, normative 5% timing authority requires rerun**

This record persists the first substantive exact-head `zip-parity.yml` performance result after restoration of the historical `benchmarks/shipping_vs_frontier_v029.py` substrate. It proves that the prior import/executability regression was retired. Hostile review then found that the workflow invoked a deprecated compatibility option with a 10% relative timing envelope while `docs/PERFORMANCE_RELEASE_GATE.md` requires 5% plus 3 ms. The run is therefore preserved as evidence but is not promoted as release-performance authority.

No corpus, comparator, byte threshold, release hurdle, product-selection law, or accepted repair-v6 identity was changed to resolve this custody defect.

## Exact source and run

- PR: `#56`
- branch: `agent/v030-authoritative-integration`
- source commit: `3dd19aa392b302593141674cacac1a4743ee9641`
- workflow: `CMPCT r24 core / ZIP performance gate`
- workflow run: `33915108857`
- result-bearing job: `101161302887` (`performance`)
- Python: `3.11.16`
- runner: Ubuntu 24.04 / AMD EPYC 7763 / 4 CPUs / 15 GiB RAM
- direct comparison base: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- candidate project version: `0.29.0`
- candidate canonical format revision: `24`
- exact-head checkout/binding: passed
- immutable release-corpus fingerprint: `b0cc877945eb66602e9ac5e3d7626d3935462aed616ac6011de1afd57858688f`
- release corpus: `7,713` files / `303,738,466` logical bytes / fixed mtime `1767225600000000000`
- full Python correctness gate: **721 passed in 262.61 s**
- release design: symmetric ABBA, median of two 7-repetition run medians per engine
- artifact: `cmpct-r24-core-performance-3dd19aa392b302593141674cacac1a4743ee9641`
- artifact id: `9953340332`
- artifact ZIP SHA-256: `9e848c09726d8667cd7a16b80d589a35bf88a2685816043676d4bbc66ad30450`

## Observed result and policy mismatch

The executed command used:

- deterministic archive-size regression tolerance: **0 bytes**;
- timing failure boundary: slowdown exceeding both **10%** and **3 ms**.

The normative repository policy is stricter: slowdown exceeding both **5%** and **3 ms** is a confirmed timing regression. Because the executed relative threshold was too weak, the workflow's terminal `PASS` is not itself release authority even though the raw observations do not reveal an obvious 5%+3 ms failure.

Observed terminal result under the superseded invocation:

- confirmed regressions: **0**;
- measured timing improvements: **10**;
- representative improvements: media library create `29.477 -> 29.094 ms` (-1.30%), media CLI create `192.977 -> 191.457 ms` (-0.79%), source CLI create `110.803 -> 109.111 ms` (-1.53%), media library extract `4.498 -> 4.410 ms` (-1.94%).

The largest apparent slowdown in absolute time was combined CLI create at `+20.508 ms / +3.04%`, below the normative 5% relative side. Apparent slowdowns above 5% were sub-3-ms cases (for example nested library create `+0.625 ms / +5.52%` and sparse library extract `+0.180 ms / +6.22%`). This suggests the same raw run would likely pass the normative conjunction, but repository law requires the corrected fail-closed gate itself to execute before promotion.

## Custody repair

The defect was repaired in two layers:

1. `.github/workflows/zip-parity.yml` now invokes `--max-time-regression 0.05` rather than `0.10`.
2. `tools/check_performance_regression.py` now encodes policy maxima of 5% and 3 ms and rejects command-line options, including the deprecated compatibility alias, that attempt to loosen either envelope. Future stale callers therefore fail closed instead of silently diluting release policy.

## Causal interpretation

Before `3dd19aa3`, the release path failed during import because `benchmarks/shipping_vs_frontier_v029_repair_v6.py` depended on a historical base module deleted during an earlier broad revert. Restoring the exact pre-revert historical blob removed that substrate failure without changing benchmark semantics. The exact-head workflow then reached and completed the full correctness + ABBA performance path.

The restoration therefore repaired a broken measurement substrate. The subsequent threshold finding was a separate D0 Custody defect in release admission, not a compression regression and not permission to change the policy.

## Authority boundary

This record does not satisfy or substitute for:

- a corrected exact-head r24 core regression / ZIP performance receipt;
- T02 `compression-generalization`;
- canonical r24-vs-r25 product parity;
- T02 `shared-build-rehab`;
- T02 `runtime-memory-selective`;
- T02 `external-competitors` strict 15/15 ZIP/Zstd-19 dominance;
- physical Android/platform authority;
- strict final release lock.

On the same source, final-release workflow run `33915108939` completed only its classifier; `contracts`, `compression-and-product-parity`, `runtime-and-selective-read`, and `external-frontier` were all skipped. External-competitor workflow run `33915108260` likewise skipped its result-bearing `external-frontier` job. Those green workflow shells grant no release credit.

## Decision

- missing shipping-frontier benchmark executability blocker: **RETIRED**;
- 10%-vs-5% timing-policy drift: **REPAIRED IN SOURCE; corrected exact-head rerun pending**;
- run `33915108857`: **PRESERVED DIAGNOSTIC, NOT PROMOTION AUTHORITY**;
- T02 remains **CLAIMED**;
- v0.30 release authority remains **LOCKED**.
