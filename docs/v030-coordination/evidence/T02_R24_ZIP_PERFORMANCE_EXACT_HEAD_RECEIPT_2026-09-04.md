# v0.30 exact-head r24 core / ZIP performance custody receipt — 2026-09-04

Status: **ACCEPTED R24 CORE REGRESSION EVIDENCE ONLY — not v0.30 product-selector, external-frontier, or strict-release authority**

This receipt persists the first substantive exact-head `zip-parity.yml` performance result after restoration of the historical `benchmarks/shipping_vs_frontier_v029.py` substrate. It closes the benchmark-executability regression that previously caused full pytest collection and the ZIP performance lane to fail before measurement. It does not change any corpus, comparator, timing boundary, byte threshold, release hurdle, product-selection law, or accepted repair-v6 identity.

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

## Performance result

The unchanged promotion policy was applied:

- deterministic archive-size regression tolerance: **0 bytes**;
- timing failure boundary: slowdown must exceed both **10%** and **3 ms** on the same runner.

Terminal gate result: **PASS**

- confirmed regressions: **0**;
- measured timing improvements: **10**;
- every apparent slowdown remained inside the documented timing-noise envelope;
- the compatibility argument `--max-size-regression=0.01` was explicitly ignored by the checker for promotion semantics; the zero-byte rule remained authoritative.

Representative measured improvements from the exact run:

- media library create: `29.477 -> 29.094 ms` (**-1.30%**);
- media CLI create: `192.977 -> 191.457 ms` (**-0.79%**);
- source CLI create: `110.803 -> 109.111 ms` (**-1.53%**);
- media library extract: `4.498 -> 4.410 ms` (**-1.94%**).

Largest notable apparent slowdown still inside the frozen noise envelope:

- combined CLI create: `+20.508 ms / +3.04%` — below the 10% relative boundary, therefore not a confirmed regression.

## Causal interpretation

Before `3dd19aa3`, the release path failed during import because `benchmarks/shipping_vs_frontier_v029_repair_v6.py` depended on a historical base module that had been deleted during an earlier broad revert. Restoring the exact pre-revert historical blob removed that substrate failure without changing benchmark semantics. The exact-head workflow then reached and completed the full correctness + ABBA performance path.

This is therefore evidence that the restoration repaired a broken measurement substrate rather than evidence of a new compression mechanism.

## Authority boundary

This receipt authorizes only canonical r24 core regression / ZIP-parity custody for the stated exact source and corpus. The workflow itself records the same boundary: it **does not measure the promoted v0.30 r24/r25 product selector and does not satisfy v0.30 external creation-speed dominance**.

It does **not** satisfy or substitute for:

- T02 `compression-generalization`;
- canonical r24-vs-r25 product parity;
- T02 `shared-build-rehab`;
- T02 `runtime-memory-selective`;
- T02 `external-competitors` strict 15/15 ZIP/Zstd-19 dominance;
- physical Android/platform authority;
- strict final release lock.

On the same source, final-release workflow run `33915108939` completed only its classifier; `contracts`, `compression-and-product-parity`, `runtime-and-selective-read`, and `external-frontier` were all skipped. External-competitor workflow run `33915108260` likewise skipped its result-bearing `external-frontier` job. Those green workflow shells grant no release credit.

## Decision

- benchmark-executability blocker caused by the missing shipping-frontier substrate: **RETIRED**;
- r24 core regression / ZIP performance gate on `3dd19aa3`: **GREEN**;
- T02 remains **CLAIMED**;
- v0.30 release authority remains **LOCKED**.
