# O173-S1 — preregistered scan-thrash cost witness, separate from product promotion

Status: PROSPECTIVE, recorded before adding the O173-S1 test. Source baseline: exact O169 Reader blob `1434c0b1485bfa59bd3dfe6f604ab555e35002a8`; custody base #266 `c5ea5b97a86bf9d0bffe9dad54c5fd2a6f0b6fb1`. All previous O169 source/test blobs remain unchanged.

## Primary falsifiable instrument question
What decoder work does the exact O169 shared LRU perform for a sequential repeated set one item larger than its admitted byte budget, compared with a set exactly at the budget? Its shared budget is 64 MiB in the real product; use a **test-only scaled** 8 KiB instance budget and nine versus eight distinct 1 KiB VZIP members to isolate replacement policy at micro rung.

Prediction: two forward scans of nine members trigger **18** reconstruction calls (full scan thrash; zero second-pass hits), whereas two scans of eight members trigger **8** reconstructions (all second-pass hits). Every returned byte string remains exact; retained payload is <=8 KiB in both cases, and the original cache tests remain unchanged. One changed count or byte mismatch disproves the scoped observation.

## Evidence boundaries
The test runs the genuine `CMPCT.read` dispatch and its source-exact `_cached_decoded` / `_retain_decoded` methods, with **mocked `rebuild_vzip`** providing deterministic 1 KiB objects, and does **not** invoke the real decompressor or Builder. Therefore it is an admission-policy/decoder-invocation oracle, **not** measured product wall/CPU/RSS, and a PASS revealing 2× decode work is an explicit **negative resource-cost observation**, not a performance improvement. It cannot establish the benefit/cost of 64 MiB in a representative workload. The stronger control would be an actual installed Reader with comparable archives and same-input repeated selectivity.

The test is a meaningful new source test, also ensuring the last O173 commit has a substantive `tests/**` path, so the existing unmodified release performance workflow can run its exact-head correctness and ABBA rather than report a misleading documentation-only administrative success. No direct edits to `.github/workflows/zip-parity.yml`, historical v0.30 validators or thresholds are authorized. Every red outcome remains a red.

## Tradeoff / follow-up
The LRU is intentionally bounded; repeated scans larger than the cache are expected to exchange retained memory for potentially large repeated reconstruction cost. If product tests establish that this cost is material, consider a scan-resistant admission policy or workload adaptation rather than raising the byte cap without evidence. Model each decoder-invocation cost separately; cannot infer throughput from call count alone.

**quality-ratchet:** preserve exact Reader output and all historical release gates while making the potential decode-work export explicit.
**disproof:** a byte mismatch, budget overflow or call-count discrepancy defeats the microscale observation.