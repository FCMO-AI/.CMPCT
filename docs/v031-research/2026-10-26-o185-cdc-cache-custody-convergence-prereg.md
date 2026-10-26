# O185 — preregistered source-exact CDC × bounded Reader cache composition

Date: 2026-10-26 UTC
Status: PRE-RESULT / UNMEASURED
Research tier: integrated product-candidate correctness and convergence. No release or merged-product credit.

## Authority, baseline and ownership

Published checkpoint: CMPCT v0.30.0, revision-24 grammar. Candidate is a *child* of O173 PR #509, exact base `62792a7fc61b033b306b4445c337ed123946514d`, which already composes O169's bounded Reader cache with PR #266 prospective source custody. Independent native CDC owner PR #228 and O163/O166 integration PR #501 produced the immutable CDC source Git blob `a6253beece20ce8aad3cdb605a6d9fcaa50d9364` at their candidate HEAD `5e99cdcdc213d91792ca616881570976362b7d98`. This episode copies that exact file, without rewriting either mechanism. The live research owners remain responsible for their original branches; this child owns only the *composition question*.

## Primary falsifiable question

Can **the exact immutable-gear native CDC implementation** coexist with **the exact bounded Python Reader cache** and **prospective v0.31 source custody** on one installed revision-24 package, with no loss of conformance, general correctness, negative safety tests or official same-input size/create/extract parity? One concern is that changing native CDC may alter encoder boundary choices or native build/source fingerprints on a branch whose Reader now differs from both owner PRs.

**Prediction:** the original `native/cmpct_cdc.c` Git blob from #501 is transplanted byte-for-byte; all O169/O173 Reader and tests remain identical to #509. The independent CDC cold-start oracle's original 24-thread, 48-call/source design remains unchanged. A healthy combined candidate passes O169/O173 cache tests, source-custody checks, general tests, native core/fuzzing and source-exact CDC differential testing. Complete r24 ZIP-parity ABBA has deterministic zero-byte regressions and no timing regressions outside the unchanged release envelope. Until actual checks execute these are predictions, not findings.

**Strong simpler control:** leave #509 Reader+custody unchanged and keep #501 CDC+custody as *separately* green candidates. That does not prove they coexist; if the only evidence change on this child is generic CI, reject extra branch weight rather than claim integration success.

**Alternative explanation:** a green new workflow might skip its scientific job due to path filters, run stale source, or merely pass a cached build. Require inspected job steps and source blobs; administrative success is insufficient. A red native/Tsan build could reflect runner/toolchain infrastructure rather than product failure, to be classified without relaxing the actual failure test.

**Kill/narrow condition:** mismatch in original CDC Git blob, any edited inherited Reader/cache tests/frozen benchmark comparator, functional divergence, missing/failed exact-source evidence, any deterministic archive size regression, confirmed create/extract slowdown, unsafe memory ownership, or unmeasured platform portability. No merge, release, format/version mutation, or v0.30 release-lock rewrite.

## Experiment tiers and costs

1. Source identity (Git blobs; free): old Reader/cache tests/fingerprint unchanged; CDC source exact #501 owner blob.
2. Focused source-exact old/new native cold-start ThreadSanitizer witness (24×48 shared first use), with independent deterministic fold control.
3. Real installed combined package: targeted cache tests, general pytest, native and fuzz checks. Distinguish historical per-source CI reds from functional regressions.
4. Release ABBA (full stored bytes, create/extract medians, same corpus/semantics/host) required before promotion. Unchanged compressed archive bytes alone cannot establish parity of CPU, RSS, cache warm scans or native concurrency. Additional O175 warm-scan + real RSS debt from the inherited Reader remains open and must never be erased.

Costs: no intended new archive bytes, no new runtime dependency or exposed API; the constant CDC table is inherited. The bounded Reader's known adversarial warm-scan +25.61% / RSS -14.99% tradeoff remains an inherited limitation, not credited as resolved. Source-custody tests and native builds may add CI cost. Conformance on Windows/macOS and ThreadSanitizer beyond Linux remain unmeasured until run.

## Concurrency and continuation

Before writing, checked open PRs and searched the exact O163/O173 combination: no same narrow integration owner found. Existing #228, #266, #501, #506, #509, #510 are authoritative for their independent work. This branch must never overwrite them or shared discovery state. Read current shared target files before late updates. If a new owner is found, stop duplicate implementation and hand off source-backed evidence.

Future activation should recover this preregistration, exact child head, tests and Actions artifact identities; promote conservatively and keep source-count/CI/branch debt honest.
