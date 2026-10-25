# O66 — O59 historical source custody × actual O63 composition: hosted result

Date: 2026-10-25 UTC. Category: **product-evidence enablement / source-exact installed tests**, NOT format, compression performance, release or canonical merge.

## Frozen input and genuine execution

Parent O63 PR #418: `18e32cae012f5dca9fc47f10d194f8b81005c85c`; O63 Builder Git blob `382e60983bf1e8e7595ea7112f3a5553dc33dcc0`; codec blob `dc3446b0eed82edfba9380e3885a20aa45577899`. Original O59 historical fixture `6f60dfe63742ff4b777f959a15d6fb828ae29610` and O59 comparator `20faf26980693342439c7730f62bd0bab8daca0f` copied byte-for-byte from existing O62 #417. Neither test assertions nor product source were changed.

Prospective question and predicted disproof: [O66 preregistration](2026-10-25-o66-o63-historical-parent-custody-prereg.md), first commit `87e495bdcf31d8bd72bef048dd3553d8734d8349`.

**Result-bearing source HEAD:** `897eb82d4825ed7063b7188afdb5ec964cc4f3cc`.

**Original hosted run:** [GitHub Actions #40173828076](https://github.com/FCMO-AI/.CMPCT/actions/runs/40173828076).

All **five actual installed** combinations succeeded, not administratively skipped:

| Host | Checkout depth | Historical source mode | O50 | O60 | O63 | Result |
|---|---:|---|---|---|---|---|
| Ubuntu 24.04 | 1 | frozen-exact-blob | 3 pass | 12 pass | 7 pass | PASS |
| Ubuntu 24.04 | 0 | git-parent | 3 pass | 12 pass | 7 pass | PASS |
| macOS 14 | 1 | frozen-exact-blob | 3 pass | 12 pass | 7 pass | PASS |
| Windows 2025 | 1 | frozen-exact-blob | 2 pass, 1 POSIX-only skip | 12 pass | 7 pass | PASS |
| Windows 2025 | 0 | git-parent | 2 pass, 1 POSIX-only skip | 12 pass | 7 pass | PASS |

**110 JUnit testcases collected, 108 actually passed, 2 justified POSIX FIFO skips, zero failures/errors.** All five judges verified the exact O63 Builder/codec and untouched O59/O60/O63 test Git blobs, the noneditable installed Python import path, preserved historical O47 parent identity, actual full-archive byte parity on tiny/mixed supported source trees and adversarial O60/O63 assertions.

### Original immutable evidence artifacts

- Ubuntu depth=0 — GitHub artifact `12591242759`, ZIP SHA-256 `1a2573fa5f25d24afffd144edc92bf7e51b2379940a07501d8acd6bf26be16d7`.
- Ubuntu depth=1 — artifact `12591665786`, SHA-256 `94b97b11436d043e327876a4fdf4248fe2478a894a9cbc7aef9be49d97a85c2e`.
- macOS depth=1 — artifact `12591720801`, SHA-256 `762160b9a44a9e5613a5004b98f568e2a86f5a4b42214cb5203c0473722164b3`.
- Windows depth=1 — artifact `12591047969`, SHA-256 `6d2b8eba3f21049de47bfe88754eb3576ddbf21f3501a562aff57879e8de0002`.
- Windows depth=0 — artifact `12591940446`, SHA-256 `2bf90521f945182f71fe53bc5e26ebacefad8aced1bc4d9482404cea2e819768`.

These SHA-256 values are the GitHub artifact digests as reported by its artifact listing. The in-run source/junit assertions are stronger than trusting these archive hashes alone.

## General CI contradiction preserved, not waived

The same source HEAD [general Tests #40173827982](https://github.com/FCMO-AI/.CMPCT/actions/runs/40173827982) completed with **812 passed, 4 failed**, versus O63 original source **809 passed, 7 failed**. This is a *real regression-gate reduction of three missing-historical-commit failures*, but **not an overall general-tests PASS**.

Exactly four pre-existing v0.30 test/surface/fingerprint failures remain:
1. `tests/test_performance_base_native_release_custody.py::test_historical_native_materializer_is_release_fingerprinted` — historical helper missing from v0.30 fingerprint globs.
2. `tests/test_public_attribution.py::test_surface_revision_records_attribution_campaign` — expected revision `0.29.k`, actual `0.30.a`.
3. `tests/test_v030_ci_topology_split_receipts.py::test_authoritative_v2_classifier_is_release_fingerprint_driven` — `docs/PUBLIC_SURFACE.md` absent from selected release fingerprint inputs.
4. `tests/test_v030_release_fingerprint_surface.py::test_release_fingerprint_covers_r25_oracle_and_android_custody_inputs` — missing canonical R25 oracle and Android inputs from selected fingerprint set.

These checks must be resolved under their actual v0.30 provenance/release owners without shrinking globs, weakening tests, fabricating release identity or rewriting published receipts. Original O50 source-pinned workflow [#40173827939](https://github.com/FCMO-AI/.CMPCT/actions/runs/40173827939) intentionally rejects the changed comparator blob `20faf...` rather than the old `5b7e...`; it was not relabeled as a product failure/pass.

Original official [r24/ZIP workflow #40173827941](https://github.com/FCMO-AI/.CMPCT/actions/runs/40173827941) is administratively SUCCESS, but its **effective performance job SKIPPED**. It provides **NO** O66 or O63 performance credit.

CI topology/version discipline/native core/fuzzing/R36 executed green on the result-bearing head. Engineering Evidence initially rejected incomplete PR *metadata headings*, not product; PR description must be brought into compliance without weakening the validator.

## Scientific decision and counterfactual

**Decision changed:** the exact immutable original O47 Builder comparator can successfully validate the actual O63 combination on *shallow and full* Git checkouts, Linux/macOS/Windows, without source-counterfeiting or changing production files. The three generic missing-parent failures have a directly verified repair.

**Counterfactual:** carrying the small original O47 source fixture into the test tree earlier and verifying its Git blob, rather than requiring every generic CI checkout to fetch parent history, would have prevented three nondiagnostic CI reds at O50/O60/O63. This is an experiment-specific source custody lesson, not sufficient evidence to change the general Discovery Engine policy.

**Open decision:** O63 cannot be merged/promoted while four inherited general reds and a real official performance comparison remain unresolved. Inherited archives and negative scientific results must not be overwritten. O67 is a separate source-bound economic investigation; do not import its future conclusion into O66 without exact-head scope.

**Concurrency:** original #414, #417 and #418 ownership preserved; this result is scoped to isolated child PR #422. No shared `STATE.json`, frozen corpus, release, format or core source edit.
