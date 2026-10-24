# CMPCT v0.31 — prospective source-exact Writer/salvage × full-PR parity-admission composition

**Status:** preregistered, *before* any source overlay or hosted result.  
**Date (UTC):** 2026-10-24.  
**Authority:** current repository AGENTS.md, r24 release-parity law, existing owner evidence. This is a narrow integration court, **not** a release or format change.

## Primary question and stronger control

Can the full-PR source-impact selector from [PR #320](https://github.com/FCMO-AI/.CMPCT/pull/320) repair the observed false-green parity admission on the actual multi-owner Writer + bounded-salvage + prospective-custody product [PR #311](https://github.com/FCMO-AI/.CMPCT/pull/311), **without** changing any product code, benchmark workload, comparison semantics or released v0.30 history?

Frozen exact input owners:

- Product/Reader/Writer/salvage/custody: PR #311 `c1e75370281ca6b721ef10edf1ed15e6c5ef48f7`.
- CI admission source: PR #320 `c7e3a101836c01363d69a5507bae1f628c39be9b`.
- The stacked base is PR #311's branch, **not** the canonical v0.31 development HEAD.
- Product source sentinels from #311: `src/cmpct/transactions.py` blob `a3b9c3375ed19f0b37d40ee47ead7b5d5b8905ee`; `src/cmpct/reader.py` `c548a2ae4d650e928eb46ed1c2431423e49765b5`; `src/cmpct/cli.py` `94bcd91af4ec8fa8282e3b1900d3c1d07a7a3235`; `docs/V030_RELEASE_LOCK.json` `988a7b05ad4e0833fac0453de74133b38f890f87`. These may not be silently altered.

## Preregistered mechanism and immutable overlay

Copy **exact Git blobs**, no handwritten approximation or cherry-pick rewrite, for these seven disjoint PR #320 files:

| Path | Exact PR #320 Git blob SHA |
| --- | --- |
| `.github/workflows/v031-zip-scope-court.yml` | `4ac716423c26d565dbb847b8430da60d8b472599` |
| `.github/workflows/zip-parity.yml` | `f77ba07cb6ee8dfa0c8cef0be7135a536a872efb` |
| `docs/v031-research/2026-10-24-parity-full-pr-impact-prereg.md` | `0b5af9b48f69eb42560da597488152efc8ecb65f` |
| `tests/test_performance_base_native_wiring.py` | `b413285c3e633c6ebd4ba9dd7be9ca276171a418` |
| `tests/test_v031_zip_parity_scope.py` | `74b9b43b80cd489e97cc65d27cbc27e8f8daa876` |
| `tools/check_ci_topology.py` | `1a2143ff517608379769d46749650bf7d006d35e` |
| `tools/classify_zip_parity_scope.py` | `c7107c71733077a062c424cbf3ee4b94039bff13` |

The preexisting PR #311 Writer/Reader/scanner blobs and candidate fingerprint must remain byte-identical. The underlying #320 classifier examines `merge-base(event.base, exact head)..head` (push uses before..after) and fails closed if immutable history is inaccessible. It does not alter ABBA reps, time/size thresholds or actual base-vs-candidate source.

## Prediction, falsifiers and alternatives

**Prediction:** exact source sentinels all match; hosted Linux 12 Git DAG admission tests and 2 native wiring controls pass; `run_performance=true` on this stacked PR because the full PR tree includes materially relevant tests/tool/benchmark-workflow changes despite any final documentation-only commit; the substantive `performance` job starts, its correctness preflight passes on the assembled product that already owns prospective v0.31 custody. The actual ABBA may still fail due to performance variability; a comparator red is not hidden and cannot be reclassified as success. Existing dedicated Writer/salvage platform courts should retain prior behavior.

**Falsify/narrow if:** source blob drift, skipped substantive performance job on a material PR, historical corpus or v0.30 lock mutation, regression of any inherited Writer/salvage/Reader guarantee, four inherited general custody contradictions reappear, mismatch of Git event/base/head, actual price of performance exceeds the unmodified gate, or CI supplies only a green workflow wrapper around a skipped job.

**Strong simpler control:** the unchanged PR #311 product branch with its old last-commit classifier SKIPs the real performance job; #320 alone RUNs the job but inherited four epoch-custody test failures block comparison. A composition must beat those *specific* deficiencies without weakening the courts. A one-off `workflow_dispatch` would produce performance numbers but **not** repair routine PR admission; it is an auxiliary diagnostic, not the proposed solution.

## Evidence and exported-cost accounting

The independent decision needs: immutable Git trees/commits and per-blob identities; exact-head CI logs showing classifier output and job conclusion separately; green real focused cross-owner suite and general tests; and if ABBA executes, complete exported size/wall/CPU/RSS/temporary I/O and provenance before any promotion claim. Shipping bytes/performance are expected unchanged because no product source is edited. The full-history checkout and potentially redundant 45-minute CI job consume GitHub Actions resources; do not claim a speed or compression gain.

**Alternatives/reversibility:** do not overwrite #311/#320 owner branches, mix Writer regions by hand, change comparator thresholds or rewrite published records. If the composition fails, preserve failure and keep the owner PRs intact; the stacked branch/PR remains draft research. No discovery-policy edit is earned by this prospective hypothesis.

## Pending until observed

All GitHub CI, native/product tests, Windows parity, ABBA timing, release suitability and merge status are **UNMEASURED** at this preregistration. Never infer CI SUCCESS from creating a branch or PR.
