# J24V03 — signed sparse hardlink verification: three-host + source-exact ABBA
Observed UTC: 2026-10-27. **Product-candidate and research evidence, not a merge/release decision.**

## Source and preregistration
- Released control: v0.30.0 / physical r24, unmodified.
- Exact inherited product control: J24V01 #613 `3b2bf3c2e033fa27d77b2355821dc0087aa46873`, Reader blob `b2b7774c13a5c8235ff89786d171b7ea3ff20710`.
- Prospective J24V03 prereg commit: `db01e0f2d47526b5338025df81850b5303af7fcc`; implementation `9b4c2dfce9d735e4bb38dc9ca88de4b174c0bdb6`, Reader blob `f2bf7e5ca79f35706bc7d09a496eba9ef151fc1f`.
- Source-exact receipt at head `14009cbfd8b8eb600335d69faca665bef27432f6`; source ancestry #613 verified via Git in hosted workflow. Separate draft [PR #620](https://github.com/FCMO-AI/.CMPCT/pull/620). No code change to #613 or #615/#569.
- Primary rule: sparse hardlinks use the existing J24V01 bounded SHA path; only alias terminal resolutions are memoized, not successful content verification results; signed size equality is checked at every chain hop.

## Functional court — hosted original J24V03 head
[Three-host Actions #40585007249](https://github.com/FCMO-AI/.CMPCT/actions/runs/40585007249): **SUCCESS**.
- Ubuntu 24.04: new signed J24V03 **12 PASS**, inherited untouched J24V01 **2 PASS**, including real Builder-produced 64MiB sparse owner+hardlink verification.
- macOS 14: new **11 PASS, 1 Linux-only skip**, inherited **1 PASS, 1 skip**.
- Windows Server 2022: new **11 PASS, 1 Linux-only skip**, inherited **1 PASS, 1 skip**.
- Total **38 PASS**, **4 legitimate platform skips** across 3 hosts. New tests reauthenticate both index copies and footer from the independent frozen r24 sparse vector, preserve physical bytes, assert absence of whole-member read/cache retention, reject signed alias size mismatches at middle/outer hops, missing/cyclic/nonregular targets, and check 1024-alias lookup bound. Ubuntu fresh-process own VmHWM on a genuine 64MiB sparse archive with os.link: **23,492 KiB**, wall **88.145ms** (single process, not an A/B statistic), 2 logical members verified.
- The underlying source archive must have K_FILE/S_SPARSE owner plus a real K_HARDLINK alias, not merely an invented sparse mode.

## Source-exact materiality — same-wire historical ABBA
[GitHub Actions #40585007258](https://github.com/FCMO-AI/.CMPCT/actions/runs/40585007258): **SUCCESS** on Ubuntu 24.04. A single authentic Builder-produced archive per size was consumed by *both* exact source trees in fresh Python processes. Each size ran three baseline→candidate→candidate→baseline rounds: 6 processes per arm × 2 sizes = **24 processes**. The raw JSON, Reader file SHA-256 and archive bytes SHA-256 are retained in the workflow artifact. Elapsed and CPU exclude process startup but include Reader open, verify of **two logical entries**, and close. Own kernel VmHWM, not inherited child ru_maxrss.

| Logical sparse owner + alias | J24V01 baseline | J24V03 candidate | Candidate effect |
| --- | ---: | ---: | ---: |
| 64 MiB: median peak RSS | 154,754 KiB | 25,512 KiB | **−129,242 KiB** |
| 64 MiB: median wall | 165.625 ms | 87.502 ms | **1.89× faster** |
| 64 MiB: median CPU | 165.568 ms | 87.496 ms | **1.89× less CPU time** |
| 256 MiB: median peak RSS | 547,956 KiB | 25,446 KiB | **−522,510 KiB** |
| 256 MiB: median wall | 651.830 ms | 341.358 ms | **1.91× faster** |
| 256 MiB: median CPU | 651.744 ms | 341.306 ms | **1.91× less CPU time** |

The baseline here is **J24V01, not the released v0.30.0**, which is important because the one-file owner already receives J24V01 streaming. New measured improvement is removal of the *hardlink alias materialization*. The unchanged-owner direct sparse behavior is inherited from J24V01/J24V02 and is not counted as newly invented.

[Independent stdlib referee](../research/j24v03_sparse_hardlink_referee.py) recomputed all medians, checked distinct Reader SHA identities and stable raw archive bytes, ABBA order, source ancestry and 24 unique samples; rejected **5/5 deliberately corrupted receipt variations**. Scientific verdict: `RSS_PASS_NO_MATERIAL_CPU_WALL_VETO`. It is independent receipt analysis, **not** an independent alternate Reader implementation.

## Strongest negative / limits
- The candidate still hashes the whole sparse logical byte stream **once for every hardlink alias**. On many aliases of one giant owner, CPU remains O(aliases × logical_bytes), even though memory is bounded. A future evidence-bound physical proof-owner/dedup experiment could test this without silently weakening verification of concurrent mutable files; no such claim is earned here.
- New graph memoization stores O(number of aliases) references for one `verify()` pass, and this cost has not been fully charged at millions of tiny files. 1024-hop structural lookup bound is not an end-to-end million-file benchmark.
- ABBA measured one Linux runner and two genuinely sparse geometries only. Other storage kinds, 4GiB files, many extents, cold open/list, physical I/O amplification, mutation/recovery, full filesystem topology, Windows ACL fidelity and official frozen release parity remain unmeasured.
- Signed malformed alias rejection is *local to explicit verify()* and cannot replace the still-unmerged strict preflight fix #615. Reader #569 remains in substantial cold-open regression debt (27–28× in its high-reference case), unrelated to this new RSS result.
- Full general/test/release checks must be independently verified on the final integrated Reader; a focused court alone is not promotion credit.

## Decision and next executable action
**Advance the bounded sparse-hardlink verifier as an independently source-bound candidate. Do not merge/release.** Handoff to J24V01 #613 and Reader #569; compose with memoized strict hardlink-size validation #615 while keeping per-alias integrity semantics explicit. Before integration, evaluate a small extreme case (1 sparse owner, many aliases) to decide whether optional proof dedup is justified, and measure added O(alias count) cache RSS against the strongest simpler control. Preserve zero format/version mutation and signed index consistency.
