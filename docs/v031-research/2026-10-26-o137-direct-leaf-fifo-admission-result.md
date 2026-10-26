# O137 result — static prewrite nonregular direct-output admission

**Status: PRODUCT-CANDIDATE FOCUSED POSITIVE ON UBUNTU AND MACOS; INHERITED FULL CI/RELEASE NOT GREEN. No canonical merge or release.**

Date: 2026-10-26 UTC. PR [#487](https://github.com/FCMO-AI/.CMPCT/pull/487) stacked on O136 [#485](https://github.com/FCMO-AI/.CMPCT/pull/485), direct source base `44ccdc03f12538691f9df3465d5166a3cdc2ec19`. Prediction frozen **before product code** in commit `6efb789b61bfedcf51d7d2800310a21a6cf9c237`. Product change commit `5b8b5381f1b8794119560f5cfabbe3bd4be04922`: `src/cmpct/reader.py` blob `5ce013f80c0220c7e7771041c60740a7111fff8a` → `e5301ccf24a63577cfbfa169be9c1e452a0d14bd`. Change is one static `S_ISREG` check in existing `lstat` direct-writer path; no new filesystem calls, no codec/format/ABI change.

## Source-exact hosted evidence

- **Result-bearing HEAD:** `d5f57cac8db47bbf81bf2b55de68814db1611bd0` (minor workflow-only correction after initial research fixture failure).
- [Specialist Actions run 40261529555](https://github.com/FCMO-AI/.CMPCT/actions/runs/40261529555): **SUCCESS Ubuntu 24.04 and macOS 14**, actual installed CMPCT under checked source; unchanged source/test/golden Git blob checks before execution.
- Ubuntu job `121374758303`, raw artifact [12623928901](https://github.com/FCMO-AI/.CMPCT/actions/runs/40261529555/artifacts/12623928901): **11 passed / 0 fail / 0 skip in 0.60s**.
- macOS job `121374758492`, raw artifact [12624741000](https://github.com/FCMO-AI/.CMPCT/actions/runs/40261529555/artifacts/12624741000): **11 passed / 0 fail / 0 skip in 0.68s**.

Per-host exact instrument cases:
1. `S_PACK` authentic Builder source storage 4: fresh and pre-existing regular extraction exact; FIFO promptly refused with `O137_REJECTED:nonregular direct-output destination leaf`; symlink-to-FIFO refused with existing symlink policy. No child timeout.
2. `S_VZIP` authentic Builder source storage 2: same four outcomes; full source archive SHA unchanged.
3. **Builder-independent frozen r24 S_CHUNKS and S_CDC** archives from unchanged `v24-chunk-maps.json` Git blob `91141405bb10b2e1226b0652e3aa0a13ba41846c`: FIFO destination successfully replaced with exact verified regular output in **both hosts** (preserves atomic replacement exception).
4. Two-member genuine Builder archive: **later-member FIFO** rejected during global prewrite scan; earlier pre-existing sentinel bytes preserved, last FIFO inode remained FIFO.

The negative baseline is published O121 PR #471, [Actions 40237296369](https://github.com/FCMO-AI/.CMPCT/actions/runs/40237296369): installed **original** Reader timed out after >8s on each pre-existing FIFO and symlink-to-FIFO for true `S_PACK/S_VZIP` in both hosts; direct regular controls exact. O137 does not rewrite or replace that negative; it checks a distinct new repair acceptance criterion. This evidence supports **static safe-mode availability**, not concurrent race closure.

## Infrastructure failure preserved

The first O137 hosted run [40261266955](https://github.com/FCMO-AI/.CMPCT/actions/runs/40261266955) on `dab4df5abb6f7a948509daa6257f16c7bf882355`: Ubuntu focused court **SUCCESS**; macOS **FAIL during pytest conftest collection before a single O137 case**, because unrelated inherited `tests/conftest.py` imports experimental `libzstd.so` by Linux spelling unavailable under hosted macOS. This is **not a product failure**. Workflow-only commit `d5f57cac8db47bbf81bf2b55de68814db1611bd0` copies the exact original test bytes to a repository-root scientific artifact directory and verifies `cmp` equality before pytest. That avoids unrelated directory-wide `conftest.py` and retains all O137 cases/assertions **without changing test source or any validator**. The fresh result above passes on both hosts.

## Negative and promotion boundary

- The prewrite `lstat` is not race resistant: after the check a concurrent actor can replace the leaf with a FIFO or another object. No `openat2`, capability-root, secure publication or anti-TOCTOU claim.
- `safe_symlinks=False` is intentionally not improved. Windows named pipes, devices and junctions not tested in this POSIX acceptance court.
- Original existing hardlink alias static rejection is source-preserved, but its independent inherited full host court has **not** passed on this new Reader source yet.
- O131 and O124 **source-exact research workflows** intentionally pin the **older** Reader Git blob, so their automatic checks fail on a new product-source branch *at source admission*, not at an evaluated product verdict. Never replace their frozen science identities or mislabel the source mismatch as a new Reader semantic failure. A new independent acceptance court or owned source-rebinding needs a separate preregistered integration and real host tests.
- General tests, fuzzing, native, r24 official ABBA and owner sign-off are separate obligations; historical v0.30 release-lock and format r24 unchanged. No speed or archive-size win claimed from this focused test.
- The O136 direct-base r24 ABBA [40255845479](https://github.com/FCMO-AI/.CMPCT/actions/runs/40255845479) **PASS/zero regressions** applies to the **prior** code on the O136 result-bearing HEAD, not to the O137 patched Reader.

## Discovery decision and handoff

Primary question was whether the **already-paid** static `lstat` decision can close the known no-reader FIFO hang for direct representation outputs without sacrificing atomic S_CHUNKS/S_CDC publication. It **passes the focused two-host installed court**. Counterfactual: inspecting the new Reader's static preflight immediately after O121's source-exact negative predicts the missing `S_ISREG` condition, obviating duplicate per-mode fixes; genuine mode/wire evidence was still required to justify any product claim. No concurrency collision: #269 was informed at [owner comment](https://github.com/FCMO-AI/.CMPCT/pull/269#issuecomment-6407168448) before focused results, without modifying its branch. This is not a Discovery Engine policy update.

**Next highest-value target:** obtain same-source generic CI and official parity terminal receipts; reconcile hardlink safety and frozen source-bound host courts through owner review without weakening them; only then consider integration/promotion. Keep pending metrics honest and do not modify shared `docs/discovery/STATE.json` owned by #440.
