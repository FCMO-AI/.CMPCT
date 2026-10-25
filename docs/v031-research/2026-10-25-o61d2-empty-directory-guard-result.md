# O61-D2 — Calling O57's regular-file stream guard on a plain NTFS directory is a false fix

2026-10-25 UTC. **Decision: NAIVE_GUARD_REUSE_REJECTED** at lower-rung authentic Win32 source API and installed helper. This is a design falsifier, not a new current-product regression.

## Prospective source

[O61-D2 preregistration](2026-10-25-o61d2-empty-directory-guard-prereg.md) committed first as `26d8f19b1a8a4604ad76c828d68fbbbdd85861a3` before writing its implementation test.

Unchanged O57 parent [#413](https://github.com/FCMO-AI/.CMPCT/pull/413) at `d9f9fa724c139c6281f0e2a92c66601bee912618`, product Builder blob `7a13545c7dc22ea973f90930fae6cf053f13f1f2`, Win32 helper blob `23207ac06797fb21322cf327e97928fdbb5241c2`; independent [O61-D PR #416](https://github.com/FCMO-AI/.CMPCT/pull/416). Original O61-D [result](2026-10-25-o61d-ntfs-directory-ads-result.md) proved stable nested directory 676-byte ADS loss.

## Genuine evidence

[Windows 2025 GitHub Actions #40168640242](https://github.com/FCMO-AI/.CMPCT/actions/runs/40168640242) source-exact executable HEAD `d4348fc93146cc2f3db9af594288c3a7a75d2a92`; JUnit/log artifact [#12589037568](https://github.com/FCMO-AI/.CMPCT/actions/runs/40168640242/artifacts/12589037568). Real Python 3.11 CMPCT installed into `site-packages` outside checkout, Git blob locks, three unmodified O57 tests. Actual **6 PASS / 0 ERROR / 0 FAIL / 0 SKIP**, including original two O61-D scientific controls and one additional O61-D2 native test.

On an ordinary freshly created empty NTFS directory, independent real `FindFirstStreamW` returned `INVALID_HANDLE_VALUE` with **Win32 ERROR_HANDLE_EOF = 38**; because a directory lacks an unnamed default `::$DATA` stream, there were no listed $DATA streams. Calling the current installed `refuse_unsupported_named_streams(directory)` nevertheless raised `OSError(38, ...)`; the same unchanged helper accepted an ordinary regular file without additional streams. Source-exact log witness:

```
O61D2_EMPTY_DIRECTORY_WIN32_ERROR=38
O61D2_FALSE_REMEDY_CONFIRMED=naive-O57-guard-refuses-plain-directory legitimate-file-control=accepted
O61D_REAL_TESTS=6 FAILURES=0 ERRORS=0 SKIPS=0
```

## Engineering decision / counterfactual

The source O61-D showed a coverage hole; O61-D2 immediately falsifies the cheapest seeming patch (`refuse_unsupported_named_streams(e.path)` inside the K_DIR branch). That naïve patch would reject healthy NTFS directories, which violates the quality ratchet despite fixing directory ADS loss.

A candidate directory guard must distinguish **no named $DATA streams** (normal, acceptable) from **any named $DATA streams** (currently unrepresentable, refuse). For directories only, an initial `FindFirstStreamW` `ERROR_HANDLE_EOF` may be a valid empty stream enumeration; other errors must not be indiscriminately swallowed. This policy must be constrained by actual source type and live native API observations, and should check source root coverage explicitly if the product commits that contract. Do not touch existing ordinary-file refusal semantics or enable unsafe fallback on enumerator errors.

The result is *not* a CMPCT Builder fix and did not benchmark runtime, memory, whole-file archive size or portability. It proves only the helper behavior on real NTFS Windows 2025. A future integrated candidate must test nested directories with/without ADS and regular/hardlink sources on actual installed Windows plus inherited O47/O48/O50/O57 and release gates. Neither original test nor checks were weakened. No policy or Discovery Engine change earned by this single episode.
