# J24M01e — hosted full-suite RSS process-boundary result (2026-10-29 UTC)

**SCIENTIFIC RESULT / EVIDENCE ONLY. Not a released Reader fix, not an assertion change, not a product CI PASS.**

## Exact authority and preserved failure

- Canonical released main: `80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0 / on-disk revision 24.
- Source candidate: #738 at `ec112a87ea34349b63885f3f0bea4689f192bd2f`; science PR #768 source/execution HEAD `410b7458cbab71528cff6f4dac1ec708304756dc`.
- Existing unchanged test: `tests/test_j24v01_sparse_verify_streamed.py` blob `dc31bd4a46c117e6621a76a91b7bdeef85579ebf`; **strict limit remains less than 131072 KiB**.
- Original complete suite on exact research HEAD: [Actions #40900353249](https://github.com/FCMO-AI/.CMPCT/actions/runs/40900353249), job `full-suite-original-child-sidecar` **SUCCESS as scientific evidence job**, because its workflow intentionally preserves raw failing pytest exit code. Original pytest ran unmodified and returned **795 passed / 5 failed**, exit code **1**.
- Original child stdout: `{"verified":1,"peak_kib":180420}`; the assertion failed unchanged. Four unrelated release/history/fingerprint tests also failed unchanged.
- Original provider ZIP: artifact [#12909507940](https://github.com/FCMO-AI/.CMPCT/actions/runs/40900353249/artifacts/12909507940), downloaded and SHA-256 verified `8c001e91a8125d113d77deb969d4d9fd11f1103d04605aba0b1ed0858a5ba03b`, 4,514 bytes. ZIP contains exact-head, original suite log, original exit code, environment fingerprint and the source-locked probe record. Do not confuse workflow SUCCESS with pytest PASS.

## Source-locked observed measurements

The optional pytest plugin did **not** replace the original test child, script, arguments, timeout, stdout/stderr, assertion or 128-MiB limit; it measured the parent immediately before the original `subprocess.run` call and launched a separate following child on the **same physical archive** for a different measurement. Both children returned `verified=1`.

| Observation | KiB |
|---|---:|
| Parent `RUSAGE_SELF.ru_maxrss` **immediately before** original test child's fork/exec | **180420** |
| Original (unchanged) test child's `ru_maxrss` after verify | **180420** |
| Separate following child `ru_maxrss`, **before CMPCT import** | **180420** |
| Separate following child `ru_maxrss`, after import/open/verify | **180420** |
| Separate following child **post-exec `/proc/self/status:VmHWM`**, before CMPCT import | **14780** |
| Separate following child post-exec VmHWM, after import | **21888** |
| Separate following child post-exec VmHWM, after verify | **23536** |
| Separate following child post-exec VmRSS, after verify | **22676** |

Source and exact input: Reader blob `f2bf7e5ca79f35706bc7d09a496eba9ef151fc1f` at `src/cmpct/reader.py`; physical archive `9380bb61e19c3bce95eebe99029402996380cdb02df3dfabd77c1c2edaaaa2e9` / 1162 bytes; member `large.bin` is genuine `S_SPARSE` tag 3, 256 MiB logical, two 4096-byte extents (8192 bytes data), logical SHA `50c7a6d6fe5cdff870a4c4041bf456719fef36f62bf693570cf128b6ff74a90e`. Reader cache remains empty.

**Direct observation:** original child and parent both report identical 180420-KiB `ru_maxrss`; the distinct source-locked sidecar inherits that same prior high water even *before* importing CMPCT while kernel post-exec VmHWM remains 23,536 KiB after complete verification. A separate hosted no-CMPCT kernel experiment in the **same Actions run** deliberately touched 160 MiB in its parent, released it, then spawned a child: child `ru_maxrss=175532` KiB versus actual post-exec `VmHWM=10888` KiB, confirming the mechanism without CMPCT. Its artifact is #12907943667.

## Decision / causal scope

The observed full-suite `ru_maxrss=180420` measurement **cannot be treated as independent evidence that the Reader materialized 180 MiB after exec**. Parent inherited high water is a sufficient mechanism that explains this reported value on this host, while the separate same-archive sidecar's post-exec VmHWM is ~23 MiB. The historical test failure remains a true result of its historical evaluator; the **original first child did not export its own VmHWM**, so the result does **not** prove the original child's actual post-exec peak and does not justify retrospectively calling the suite green.

Counterfactual discriminator: record **both** `ru_maxrss` and Linux post-exec `/proc/self/status:VmHWM` inside the *same original test subprocess* under unchanged suite order and unchanged strict 128-MiB assertion. This avoids conflating inherited process memory with verification memory. An editable-source correction should be owned by a separate test/evidence PR, not silently land in research #768. Preserve original 5 failures and use a pre-modification causal test proving parent-high-water distortion. Do not relax any resource threshold.

## Self-critique / promotion debt

- Separate sidecar is **not** the original child; its VmHWM cannot be substituted as a measurement of the terminated child. Parent/proc evidence + independent no-CMPCT control support a strong causal explanation, not an all-platform theorem.
- Linux/CPython 3.11 only; test suite full 795/5 remains red. No macOS/Windows performance, archive size/create/extract benchmark, crash recovery, native ABI or global release credit.
- #749 demonstrates a separate stage publication identity safety failure; safe compaction promotion remains blocked even if the test metric is corrected. Other historical release/fingerprint failures remain real.
- No modification to `docs/discovery/STATE.json` (stale and owned by #574). No evidence-based general discovery-policy amendment earned.

## Coordination / next executable action

Provide the exact archive/source/job/metric identity to #738 owner. The cheapest safe next step is a separate narrowly scoped test-only candidate that changes **measurement origin, not ceiling** to post-exec Linux VmHWM, preserving pre-existing ordinary-reader and physical sparse coverage. Test it under the **full original 800-test order** and direct positive kernel allocation controls, inspect exact-head failures, then separately address #749 publication and unrelated release tests. Do not merge on this research evidence alone.
