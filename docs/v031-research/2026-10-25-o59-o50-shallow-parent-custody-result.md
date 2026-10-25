# O59 — Cross-checkout exact-parent Builder source custody: hosted result

Date: 2026-10-25 UTC. **Research/evidence-enable result**, not a product or release result.

## Authority, lineage and preregistration

- Canonical repository `FCMO-AI/.CMPCT`, unchanged release v0.30.0 / archive revision 24.
- Immutable composition owner [O50 #405](https://github.com/FCMO-AI/.CMPCT/pull/405) at `17c96603e33b02b3f2f9e0079eec2b128f293be8`.
- Independent child [O59 #414](https://github.com/FCMO-AI/.CMPCT/pull/414). Prospective [preregistration](2026-10-25-o59-o50-shallow-parent-custody-prereg.md) committed at `4547cd3be2ffa12482f5c34c605f2662cd29bb41` **before** test and workflow implementation.
- The source-under-test Builder remains Git blob `21a9ec696df13961c25301654feb607a7e161a4c`. Historical unchanged O47 parent Builder is Git blob `6f60dfe63742ff4b777f959a15d6fb828ae29610` from commit `29d9688ae6bff6d1eccc27f019893866abe5b5c3`.
- O59 substantive final source HEAD `044a865cb7b63b1908ac8e6b481ef8b335aa72ae`. Focused [Actions run **40165919196**](https://github.com/FCMO-AI/.CMPCT/actions/runs/40165919196), all five jobs **SUCCESS**. Actual installed package, unchanged original three historical O50 assertions, original complete archive exact-byte parity, SHA verification, FIFO negative where POSIX, explicit Windows platform skips.

## Original failure and negative evidence retained

Generic [O50 Tests #40158561054](https://github.com/FCMO-AI/.CMPCT/actions/runs/40158561054) were **7 FAIL / 790 PASS**. Three newly introduced original O50 parent A/B tests failed before comparison because `git show <O47-parent>:src/cmpct/builder.py` was unavailable under shallow generic checkout. Four additional v0.30 fingerprint/public-surface tests failed for inherited unrelated reasons. O50's original clean-installed [3-OS court #40158561118](https://github.com/FCMO-AI/.CMPCT/actions/runs/40158561118) independently passed with full Git history.

O59 first [run 40165499250](https://github.com/FCMO-AI/.CMPCT/actions/runs/40165499250) **FAILED before testing**: executing the original test in `tests/` imported unrelated repo-wide conftest requiring a missing optional `zstandard` native/library dependency. We then copied the **same unchanged test** into isolated test collection, matching O50's original correct isolation. A second [run 40165616482](https://github.com/FCMO-AI/.CMPCT/actions/runs/40165616482) proved 4/5 jobs, while **Windows depth=1 failed 2 assertions before product execution**: ordinary worktree `.read_bytes()` reflected Windows text checkout CRLF conversion and yielded unexpected `3b864c24...` instead of the expected historical Git blob. Git's original committed blob was correct. The final correction obtains `HEAD:tests/fixtures/o50_o47_parent_builder.py` via `git rev-parse`, asserts the historical blob, and loads the *Git blob bytes* via `git cat-file blob` rather than transformed worktree bytes. Actual original parent `git show` retains priority when available; existing parent with missing path fails closed. Neither correction touched production Builder, nor relaxed historical comparisons or skips.

## Final hosted raw decision

| Job in run 40165919196 | Historical source route | Genuine tests | Failures | O50 byte parity |
| --- | --- | ---: | ---: | --- |
| Ubuntu 24.04 depth=1 — job `121086861095` | frozen exact Git blob | 3 PASS | 0 | tiny and mixed exact |
| Ubuntu 24.04 depth=0 — job `121086861262` | actual original `git show` | 3 PASS | 0 | tiny and mixed exact |
| macOS 14 depth=1 — job `121086861314` | frozen exact Git blob | 3 PASS | 0 | tiny and mixed exact |
| Windows 2025 depth=1 — job `121086861382` | frozen exact Git blob | 2 PASS, 1 FIFO POSIX-only SKIP | 0 | tiny and mixed exact |
| Windows 2025 depth=0 — job `121086861244` | actual original `git show` | 2 PASS, 1 FIFO POSIX-only SKIP | 0 | tiny and mixed exact |

**Total: 13 substantive PASS / 2 justified platform skips / zero FAIL.** All five raw job logs explicitly report the expected source route and **the identical historical parent Git blob `6f60dfe...`**. In Ubuntu full and shallow jobs, tiny comparison produced *complete* archives of **5,859 bytes / SHA-256 `af430fffae97f1b18074f614a7e70dc59f51e2719d8c104f1e7e75c8eeae6364`**, always identical between historical Builder and combined Builder within the job. On Windows full and shallow, same case produced 5,859 bytes / SHA-256 `9bd9b9c5f631d607725f11e5aeef602dfc0da1083657397d3192197e26c00458`; the **comparison is inside one job on the identical source**, never across hosts. Mixed-case archive sizes/hashes vary across jobs due regenerated source/metadata; those do not imply a size regression and cannot be cross-job benchmark data.

GitHub workflow artifact names `o59-<host>-depth-<0|1>` retain JUnit and full logs (30-day default retention). Raw logs record actual package installed outside checkout. The frozen fixture is ~22 KB of test evidence, not output archive bytes. No new CPU/RSS/benchmark claims.

## Falsification and counterfactual

**Disproof conditions (not observed in final run):** original O47 source Git blob divergence, full/shallow selected source difference, true original complete archive inequality, lost POSIX FIFO assertion, test bypass, broken clean-install import or unclassified skip. First two intermediary failures were genuine *instrument failures*, preserved above.

Counterfactual: checking exact `git cat-file -e <parent>^{commit}` and retrieving the existing historical blob during CI design would have avoided both generic O50 source-custody test failures and duplicative full-clone cost. Windows source comparison requires inspecting Git **blob** bytes, not trusting text checkout bytes. This is a concrete reproducible test-infrastructure lesson; it is not grounds to rewrite the Discovery Engine or lower release gates.

## Limits, ownership and next decisive action

This is **an evidence-enablement change** only: no changed `src/`, encoder, Reader, Writer, native ABI, r24 format, release gate, benchmark comparator or official baseline. O50 owner original workflow deliberately SHA-locks the original test file and will **FAIL source identity on an O59 child that updates that test**; do not weaken or reclassify that historically correct fail. The original four v0.30 historical tests and O52/O54 mutable Builder sources, O57 NTFS ADS, #408 product safety, release ABI/performance remain separate. A passing focused O59 court is not generic/full release CI.

**Next:** owner of #405 can incorporate the tiny historical test-source custody correction into a coherent Builder integration after reconciling its inherited locks. Compare exact-head general Tests; preserve inherited negative release-fingerprint tests. Do not merge or publish solely on O59.

**Discovery: primary source-custody question `PASS`**, final result decision-changing for O50's generic-CI evidence path. No concurrency collision identified (child branch/PR only), Discovery `STATE.json` unchanged, no normative discovery-policy lesson warranted from one repair. Promotion credit **zero**.
