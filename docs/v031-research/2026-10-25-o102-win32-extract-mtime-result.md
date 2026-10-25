# O102 — Win32 default extractall loses authenticated file and directory mtimes
Date: 2026-10-25
Status: SCIENCE DECISIVE; original installed-product negative confirmed; **NOT A PRODUCT FIX / NO RELEASE CREDIT**.

## Prospective source and frozen test
- Preregistration committed at `1147a23ecbbd28e776edc027d95fadfe56d6d6bd`, before any implementation/observation.
- Original O69 product owner PR #425 at `8fe424ac8575da10bf5ecfdb9660d4b5831f638b`; unchanged Reader Git blob `1122b1d80f2cf76faab8ed2d4e8cb2e346d85e27`.
- Original actual test Git blob `237a58ce488ba8d5632e6b78ef3eea3e5f1d61ec` runs installed CMPCT (not source-tree import).
- Original experiment/head `7777c766a7f9d3887ec7099e883e6a867bc8cfb5`. Workflow: [Actions 40220385087](https://github.com/FCMO-AI/.CMPCT/actions/runs/40220385087).
- Frozen prereg prose names the wall-clock instant as 2020-02-02 12:34:56 UTC; its exact integer literal `1580643296000000000` is **2020-02-02 11:34:56 UTC**. This is a descriptive one-hour timestamp-label correction, appended here without rewriting the prereg or changing the experiment. All machine tests use the exact same integer literal.

## Original result, no replaced test or weakened criterion
Three jobs completed SUCCESS, each **2 actual PASS / 0 SKIP / 0 FAIL**. A scientific PASS on Windows means a product-integrity **negative**: verified byte reconstruction succeeds, but physical timestamp reconstruction fails.

| Original host | Timestamp written in authenticated archive | Actual extracted file mtime | Actual extracted dir mtime | Error from archived timestamp | Interpretation |
|---|---:|---:|---:|---:|---|
| Ubuntu 24.04 | 1580643296000000000 ns | 1580643296000000000 ns | 1580643296000000000 ns | 0 s both | positive restore control |
| macOS 14 | 1580643296000000000 ns | 1580643296000000000 ns | 1580643296000000000 ns | 0 s both | positive restore control |
| Windows 2025 | 1580643296000000000 ns | 1792952196575584900 ns | 1792952196575584900 ns | **212,308,900.5755849 s** both | **metadata=True silent physical loss** |

All three stored the same original payload hash `8d62957ffa980bb7ee094ace9fe185ea64ae31b45c0633e169ff69c3fae263d7`, passed `CMPCT.verify()==1`, `CMPCT.read`, and extracted the original payload bytes. Each host independently proved the filesystem can represent the old timestamp using explicit `os.utime(path, ns=...)` on disposable *known-regular* file/directory AFTER capturing the negative; Windows failure is not lack of host timestamp support. Both original source physical mtimes and r24 Reader index values matched the frozen integer before extraction.

Complete CMPCT files differed in SHA-256 between OS hosts, as expected from host filesystem semantics. No cross-platform byte-identity claim is made. This experiment is about the physical timestamp contract on each genuine installed engine/host.

## Exact original jobs and persistent artifacts
- Ubuntu: job `121250481858`; original artifact [12609053337](https://github.com/FCMO-AI/.CMPCT/actions/runs/40220385087/artifacts/12609053337) SHA256 `715485b19fa4c520415739382303cc68a841b789ea4dd0fc3168db73ea23835f`.
- macOS: job `121250481705`; artifact [12609268047](https://github.com/FCMO-AI/.CMPCT/actions/runs/40220385087/artifacts/12609268047) SHA256 `ad3e660f8d9bdaf8822f69e2079dcb5a27a64e4e179b991b5ce5dda35851d5db`.
- Windows: job `121250481961`; artifact [12609397749](https://github.com/FCMO-AI/.CMPCT/actions/runs/40220385087/artifacts/12609397749) SHA256 `2c6888d1986dfcc5dd88d2e3779ce05e1b3922e4c5a491373704a36db21d27f3`.
- Each artifact holds original JUnit, `source-physical-mtime.json`, `ci-receipt.json`; workflow independently asserts source/test object identity, runs pytest outside repository conftest and checks exact two-test census.

## Causal interpretation and strongest alternative
O69 catches `NotImplementedError` from `os.utime(..., follow_symlinks=False)` on Windows for regular-file and directory restoration. The actual archive retains the desired nanosecond time and the host separately supports explicitly assigning it, but the Reader returns success without applying it. Consistent causal explanation: the `follow_symlinks=False` path is unsupported and O69's portable best-effort catch drops the timestamp operation. This experiment did **not** instrument each `os.utime` exception internally, so the exact per-call mechanism remains source-supported inference rather than direct syscall tracing. The product-level physical loss itself is directly observed.

Windows timestamp fallback via plain `os.utime(path)` is **not** automatically safe: it can follow reparse points/symlinks and change metadata outside the selected extraction tree under concurrent mutation. A correct Reader fix requires an independently defended capability/handle-bound approach or an explicit caller-visible strict metadata mode. Avoid silently claiming general filesystem fidelity from a portable best-effort extraction.

## Losses, limitations and decision
- **Proved:** one r24 signed regular-file and nested-directory archive; exact Windows default `extractall(metadata=True)` returns successfully with a >6-year mtime mismatch; Linux/macOS original positive controls exact.
- **Not proved:** all Windows volumes, symlink metadata, filesystem ACLs, NTFS streams, the behavior of O69 xattr strict flag, malware/races, whole-tree atomicity, file ownership, or full-portability contract.
- **No effect on:** archive bytes semantics, logical payload correctness, released v0.30.0, Builder/Reader source, format r24, native ABI, benchmarks or existing test contracts. This result is scoped science, not a promoted improvement.

**Primary question: CONFIRMED.** This changes O69 owner decision space: the portable default intentionally ignores unsupported timestamp restoration; either disclose that limitation prominently or separately develop/test a safe, opt-in strict timestamp path without conflating it with xattr strictness. Next cheapest unclaimed action is owner-side contract selection and a bounded real Windows handle-based feasibility test, not repeated friendly sample cases. No Discovery Engine policy edit is earned.

## Completion witness / audit boundaries
Exact original source-bound 3/3 platform scientific jobs SUCCESS, 6/6 actual tests PASS, 0 skips. Product defect confirmed within test scope. Other general, native, fuzz, official performance, and new final documentation-head CI remain separate, not inferred from this receipt.
