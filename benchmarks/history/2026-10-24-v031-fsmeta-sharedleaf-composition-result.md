# v0.31: fsmeta structural validation × shared-leaf publication — result

Date (UTC): 2026-10-24
Status: **FOCUSED INTEGRATION SUCCESS / GENERAL RELEASE PROMOTION NOT EARNED**.
This is not a project release, new archive format, benchmark-headline win or native portability claim.

## Authority / exact source

- Canonical repository: `FCMO-AI/.CMPCT`, shipping checkpoint v0.30.0/r24.
- Stacked draft PR: [#305](https://github.com/FCMO-AI/.CMPCT/pull/305), parent [#297](https://github.com/FCMO-AI/.CMPCT/pull/297) head `811722a0726af3de9b2c6fdcb67c3c4392ec5015`.
- Independent fsmeta owner: [#303](https://github.com/FCMO-AI/.CMPCT/pull/303) head `dcc7371b4a34ad9c6cc666f96368324041a1f1ea`.
- Initial composed product head: `ae0236b2230a5551beef3241d4e722fd594d08de` (Reader blob `fba0beed60a26755b05dc479895b68b1783fa6b1`; imported validator blob `6064569afa61204674423862e064dd27c067ae62`, **exactly** PR #303).
- Exact-head integrated + benchmark script: `0d7a48175a6ffc6d20ccc43536cd453de7b4ccd2`.
- Preserved owner fsmeta test blob: `91acd4efe6a9f0e63538107cb4973e93013521b6`; parent atomic test blob: `7a144568e8e5eec331ab6b80f93432aacc03c7af`; newly preregistered independent interaction test blob: `8dccaf916d632033f5b03d6329662ab0eb7795f0`; ABBA attribution script Git blob `e600a901965939c424e6cf06394cfbc62a06cfca`.

## Scientific question and prospective falsifier

Does digest-consistent but structurally invalid rev24 `fsmeta` cause the Reader to publish an archive member on top of an existing hardlink-shared destination leaf before rejecting malformed metadata? The prediction and counterfactual were recorded **before implementation** in [the preregistered note](2026-10-24-v031-fsmeta-sharedleaf-composition-prereg.md).

Independent controls use an authentic Builder-produced r24 archive. They alter fsmeta only while reserializing *both* index copies and footer digest, preserve the real compressed blob body and use the same original test across both source heads. A pre-existing destination hardlink to a sibling file outside extraction is measured by SHA-256, size, mode, device, inode and link count; valid xattrs are checked on both old/new inodes. Crucially `CMPCT.extractall(...,atomic_shared_leaf=True)` is invoked **without calling preflight_archive**.

## Source-exact baseline negative, before changing Reader

[Run 40045147686](https://github.com/FCMO-AI/.CMPCT/actions/runs/40045147686) on `47e8e08e4ba1d3546e9b3a918683179cb12ca642` (Reader blob `d1fdf5839c5ead102b7dd5787bb99215c8fbff3b`) installed and exercised genuine package/native code. **Six expected signed-index malformed-xattr/owner cases failed and two valid controls passed**. For metadata restoration enabled, malformed value caused a late `TypeError` and truncated owner caused late `ValueError`, after the extractor had proceeded toward destination writing; when metadata was disabled and in duplicate-field cases, extraction silently did not reject invalid structural grammar. This fails the preregistered fail-closed boundary. Baseline run evidence must not be reclassified as an infrastructure failure.

An earlier run [40045068268](https://github.com/FCMO-AI/.CMPCT/actions/runs/40045068268) failed *only* because the CI receipt folder was created before a Git-cleanliness assertion. The assertion was moved earlier, not deleted. That earlier run did not reach the product court.

## Implementation and exact-head result

The composition copies **one existing PR #303 validator blob verbatim** and adds only its import, one host `chown` `OverflowError` normalization, and two entry-point grammar calls to PR #297 Reader, retaining the original hardlink and atomic paths. It does not change `Builder`, archive bytes, format revision, old tests, comparator or release gates.

- [Run 40045320814](https://github.com/FCMO-AI/.CMPCT/actions/runs/40045320814), source `ae0236...`: **8/8 new interaction controls PASS + 43/43 original owner controls PASS = 51/51 PASS**. Artifact `12540977717`.
- [Run 40045494583](https://github.com/FCMO-AI/.CMPCT/actions/runs/40045494583), current head `0d7a48175a6ffc6d20ccc43536cd453de7b4ccd2`: **8/8 + 43/43 PASS**, plus true-product validator ablation research SUCCESS. Product/test receipts artifact `12541290785`, SHA256 of ZIP `9f8612c5d4949b57598f57cdf60ae5301f3fe104f28e01275ab811494dd868b0`. The untouched tests' Git blobs are independently checked at CI runtime.

The fix resolves the specific case: malformed signed-index metadata is rejected **before any destination operation**, and genuine valid xattrs restore on a new leaf while the external pre-existing alias remains unchanged.

## True-product mechanism-attribution economics (research; not release parity)

The ABBA court [run 40045494583](https://github.com/FCMO-AI/.CMPCT/actions/runs/40045494583) uses the same actual Reader/Builder, identical valid archive content and hardlink namespace, eight alternating ABBA rounds, and a **sham validator omission on valid metadata only** to isolate incremental grammar-check work. It measures library-only wall/CPU; it does not compare equivalent *security guarantees* and therefore **cannot** establish release parity or justify removing validation.

| Valid fsmeta xattr pairs | Whole archive bytes | Validator wall median | Sham wall median | Added median wall (derived, not paired delta) | `tracemalloc` peak validator-only |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 925 | 0.16018 ms | 0.15567 ms | +0.00451 ms | 480 B |
| 1,000 | 5,653 | 0.28771 ms | 0.15756 ms | +0.13015 ms | 41,536 B |
| 10,000 | 36,835 | 1.44025 ms | 0.16701 ms | +1.27324 ms | 655,936 B |

All tested logical payload SHA identities and external hardlink sentinel inode/bytes survived. **No claim that each of 10,000 xattr names is physically supported on one Linux inode:** the signed revision-24 index is valid structural model, but not necessarily a Builder-produced physical xattr cardinality. The experiment measures Reader archive-grammar economics, not OS xattr restoration.

Raw repeated observations, CPU medians, platform, source identity and allocations are in artifact `12540827608`, ZIP SHA256 `b7a37da89b4dd015f7369a77ffd3a8c8c8b72d808314f6d33473d5c9b714ea18`.

**Negative/economic interpretation:** the validator's cost scales materially with metadata cardinality, not primarily data bytes. The low-cardinality fast path adds negligible measured wall; high-cardinality accepted indices can add ~1.3 ms at 10k pairs before any metadata publication. This is not a practical impossibility proof and not a regression gate failure. It creates a finite follow-up question if full-product release parity reveals a material loss; do not optimize away structural integrity on evidence from ablation. Larger indices, cold open, peak process RSS, network FS, Windows/macOS and destructive concurrent directory swaps are **unmeasured**.

## Exact-head CI and promotion constraints

Focused source-exact court is green. The complete GitHub CI matrix for final head must be queried separately: pre-existing v0.30 Public Proof project-version mismatch (site/tests/release_evidence_contract.py:35) is not a Reader defect and is tracked by other owners, while full tests, native, fuzz, full comparative performance and broader portability may remain pending. Any administrative workflow SUCCESS with a skipped benchmark is **not** a performance PASS.

Neither original source owner was modified. No merge, release, version bump, mutable discovery cache overwrite, comparator threshold change or policy amendment was made.

## Counterfactual / next unclaimed action

The cheapest discriminator was a digest-consistent index carrying malformed *nested* fsmeta, paired with a shared-inode destination and a valid-metadata control. Merely performing `preflight_archive` outside the Reader or testing default non-atomic extraction could not establish the combined guarantee. Future agents should first finish the exact-head full CI/performance interpretation; then reconcile overlapping Reader integrations in PR #270 and consider fd-relative destination authority against concurrent pathname swaps, without attributing race-safety to this static fix. Preserve all original negatives and source/test identities.
