# O173 — preregistered Reader decoded-cache × prospective source-custody convergence

Date: 2026-10-26 UTC. Status: PROSPECTIVE / before implementation composition. This is a narrow independently claimed integration, not a third cache implementation or release.

## Authority and exact baselines
CMPCT canonical `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; published v0.30.0 / r24 remains frozen. O169 cache owner PR #506 exactly `6c4338481df5f887c3bd201bb0d2d8621b0e73d1` has a new shared decoded-cache 64 MiB / 32768 entry cap and focused tests. Its original generic CI run `40301792602` observed **790 passed, 4 failed**, all historical v0.30 fingerprint/surface assertions; its performance run `40301792569` stopped at correctness, so **no ABBA numbers** were produced. O169 focused tests were in the 790 passes, not independently identified as a full-product result. This is baseline negative, not license to waive those tests.

Independent source-custody owner PR #266 exactly `c5ea5b97a86bf9d0bffe9dad54c5fd2a6f0b6fb1` separates prospective v0.31 source identity from frozen v0.30 release custody, addressing the same four mismatched historical assertions. O163 #501 independently showed the same prospective-custody base can combine with an unrelated native CDC fix; that is inherited context, not O173 evidence.

## Question / hypothesis / prediction
Can O169's **exact, unchanged** Reader and focused regression-test blobs coexist with the **exact, unchanged** PR #266 source-custody files and historical v0.30 lock on a single prospective v0.31 HEAD?

Predict unchanged Reader output semantics and original cache budget invariants, no new historical fingerprint test failures, green focused unit/fuzz/native/general CI if the causes are orthogonal. The full official performance gate **must execute its actual ABBA steps** before economic parity may be claimed; the 64 MiB LRU may have repeat-read/decode cost not measured by a release corpus. Product improvement is retention-bound candidate only, not process RSS or new compression.

## PARETOBONK and cheapest decisive controls
1. O169 alone: functionality but generic CI historical false-epoch reds block numeric gate.
2. O266 alone: correct prospective custody, no cache retention bound.
3. Rewrite O169 cache / v0.30 historical receipts / fake test expectations: rejected for duplication or weakening release law.
4. Selected source-exact transplant of O169 Reader + its test + its original preregistration, on the PR #266 exact source. Verify source blobs remain identical; avoid any new cache heuristics. Build/test run on one HEAD, then repeated charged ABBA if permitted.

## Falsifiers and scope
Any Reader or original O169-test blob mismatch, missing original tests, new functional failure, memory-accounting overflow, duplicate-read deadlock, historical v0.30 lock mutation, or new deterministic complete-archive-byte regression disproves composition/product parity. Generic inherited failure that still appears is **FAIL**, not relabeled success. The release gate may stop for infrastructure reasons; classify separately and do not infer performance. All inherited historical tests and thresholds remain unchanged except the exact preexisting prospective source-custody changes from PR #266.

## Concurrency and economics
Before this independent integration, GitHub PR search found no existing O169 × #266 combination; owners #506 and #266 retain their source branches, and O173 will not modify either. This integration branch does not edit shared `docs/discovery/STATE.json`. The project remains pre-1.0 and unreleased v0.31. Actual read-cache repeats, decode amplification, reader RSS, concurrent misses, and long-lived workload behavior remain independent costs not resolved by this composition. Hold integration Draft and hand source-exact evidence back to owners when measured.

**quality-ratchet:** retain every released/frozen historical guarantee while demonstrating whether a bounded retained Reader cache can coexist with authentic prospective CI custody.
**disproof:** altered original donor SHA, any new product regression, missing full ABBA, or weakening source/history validators prevents promotion.