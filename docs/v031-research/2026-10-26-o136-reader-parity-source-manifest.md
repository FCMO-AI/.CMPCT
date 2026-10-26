# O136 exact-source integration manifest — BEFORE hosted outcome

Date: 2026-10-26 (UTC)
Status: **INTEGRATED / UNMEASURED**. This is a documentation-only last commit intentionally exercising the historical last-commit-only false-skip of the r24 performance gate. It is not a success receipt.

## Source-bound structure
- Stacked baseline: O134 PR #482 `70cee90989d9734d74298fdd0eca4fb0ee05db94`.
- Preregistration (separate earlier commit): `7bcf9fdd1434ec5df015acdfbe312ee52651bea8`.
- Exact eleven-file donor overlay: `af26561a916d79aaccbd05e03f67a0bfabbad09f`.
- Upstream donor: PR #328 commit `36c5c737c2896b9ad9ee68c491ff921fbd36aaa4`; its `zip-parity` and `classify_zip_parity_scope` components also preserve PR #320.
- Reader product blob `src/cmpct/reader.py@5ce013f80c0220c7e7771041c60740a7111fff8a`; unchanged from O134.
- This note is added **after** the source overlay, so the final commit modifies only this documentation path. Official parity must consider the complete PR diff from the merge-base.

## Imported original Git blobs
| Path | Exact donor Git blob |
| --- | --- |
| `.github/workflows/zip-parity.yml` | `f77ba07cb6ee8dfa0c8cef0be7135a536a872efb` |
| `tools/classify_zip_parity_scope.py` | `c7107c71733077a062c424cbf3ee4b94039bff13` |
| `tools/check_ci_topology.py` | `1a2143ff517608379769d46749650bf7d006d35e` |
| `tools/check_performance_regression.py` | `2cea1b4d0cfe52259e5bc6b870c8207b4c889610` |
| `tests/test_v031_zip_parity_scope.py` | `74b9b43b80cd489e97cc65d27cbc27e8f8daa876` |
| `tests/test_performance_base_native_wiring.py` | `b413285c3e633c6ebd4ba9dd7be9ca276171a418` |
| `tests/test_v031_parity_metric_truth.py` | `b6c547573914c3a7692c3d29dac9f04842868bac` |
| `tests/test_v031_parity_admission_metric_union_r267.py` | `c1bb8e265147330f9afb095c9213ac3fb92cb168` |
| `tests/test_v031_parity_legacy_alias_monotonicity_r272.py` | `d8f36c20eb90af97d25c4ccc0b49f0bb61f4e06a` |
| `tests/test_v031_parity_logical_input_custody_r271.py` | `437e9652a6a6c1086fdd6fea22116f4f3257fc6d` |
| `tests/test_v031_parity_policy_args_failclosed_r270.py` | `9b23bb7b222d344ce478af2c397d96e97378ebb6` |

## Required run custody
The *new integrated* head must pass the original O134/Reader ordinary tests, imported hostile comparator cases, and exact-history controls without altered historical benchmark semantics. CI Topology and Engineering Evidence must approve this head. The official performance workflow must log `run_performance=true` and a **non-skipped** substantive performance job. Preserve exact-head `source_sha`, direct comparison base, changed paths, raw measured base/candidate JSON and final result. A green workflow wrapper with a SKIPPED job is a failure to establish this question.

The comparison is expected to be r24 A/A for identical Reader/Writer/Builder product source on stacked O134 base. Any apparent performance improvements are statistical observations, not a product speed claim. Failure of one host-specific inherited court (notably O124 sparse on macOS) remains visible and unwaived. No format, version, canonical branch or historical release files changed. No product promotion without independent owner review.
