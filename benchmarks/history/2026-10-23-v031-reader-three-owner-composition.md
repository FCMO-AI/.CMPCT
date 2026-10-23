# v0.31 Reader three-owner independent integration court

Date: 2026-10-23
Status: **PR-only product-integration hypothesis; no merge/release authorization.**
Frozen base: `PR #262 @ 24f4de54a86f4aef33a1bf684e504a04bcea5ad5`, itself stacked on PR #261 scientific source.
Imported exact source: PACK physical SHA `PR #258 @ 2cf7c3915cd618b9a72a5dc26bdd15a25cb75230`; native decoder worker closure `PR #231 @ d9528682307076a4c4757bdb74cadbbbb974d477`.

## Primary question and prediction (before hosted run)

Can the exact proven owner-first hardlink extractor coexist with explicit physical micro-PACK SHA authentication and with executor-shutdown-before-native-resources closure, without changing revision-24 bytes, baseline test meaning, or the original owners' branches?

Prediction: 7 existing hardlink integration tests + 3 PACK tests + 4 worker-lifetime tests pass unchanged, along with both independent source-correctness scripts; corrupted PACK SHA rejects, hardlink aliases retain inode/content identity, and active workers join before native resource release.

Disproof: any required test/script fails; original source SHA mismatch; changed format/Builder/benchmark semantics; regression in general tests; or confirmed complete-product create/extract slowdown outside the existing gates. Test green is *necessary*, not sufficient, for promotion.

## Chosen mechanism and alternatives

Choose deterministic composition of two disjoint function scopes in the actual Reader while retaining PR #262's hardlink implementation byte-for-byte elsewhere. Copy the owners' product test and independent PACK oracle unchanged. Alternatives rejected: manually reimplementing those mechanisms (semantic drift), merging owners directly (loses isolated review), or accepting three disjoint green PRs as proof of their shared execution.

## Product/evidence boundaries

No Builder/format/index/parser change is proposed. Direct output bytes unchanged as a code-level hypothesis, not a freshly measured release fact. The pack check adds one SHA-256 scan per unique physical PACK during explicit `verify()`. Hardlink extraction retains auxiliary O(entry count) metadata and no duplicate content payload. Closing decoder workers may wait for currently active decoding. Actual wall/CPU/RSS/platform/runner parity remain unmeasured until exact-head CI and follow-up controlled evidence.

Inherited release v0.30.0 / physical revision 24. No validator threshold, workload, comparator, historical result, release/public version or discovery state is modified. Inherited CI evidence and environmental blockers must be reported distinctly from newly failing product paths.

## Coordination

Do not modify PR #231, PR #258 or PR #262 branches. This is an independent integration branch *stacked on PR #262*, not a second implementation of any owner's narrow mechanism. Their source SHAs above are the fixed baseline for this court; any later upstream changes require explicit re-reconciliation. The active Bounded Drift and destination-capability work remain separately owned.

## Completion gates

1. Exact-head hosted tests including inherited hardlink oracle and independent PACK oracle.
2. General/core/fuzz performance gates and explicit handling of inherited release-custody reds.
3. Held-out hardlink+PACK mixed tree and failure-under-worker-activity adversarial tests if the first composition survives.
4. Controlled create/extract/RSS comparison, recovery/portability review, and owner reconciliation before merge.
