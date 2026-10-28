# J24C14 — Source-exact published / native / fused Q6 Reader comparison

Date: **2026-10-28 UTC**. Status: **decisive R4 research evidence for measured fixed-RAW S_CHUNKS profiles only; NOT product promotion, release or format authority**.

## Original question / prospective controls
Before implementation, `docs/v031-research/2026-10-28-j24c14-published-fused-triplet-prereg.md` was committed **alone** at `bf337ad29419f99499e9e461294fa571db50b061`. J24C12 #659 showed #641 native-only Reader +8.22–15.0% Q6 loss relative to published v0.30.0 on 262,144 references. J24C13 #662 then proved large Q6 acceleration against native-only, but not the published Reader. J24C14 tested the correct same-runner three-source fork.

Three independent noneditable Python 3.11 wheels on **the same hosted Ubuntu 24.04 runner**:
- `released`: main/v0.30.0 `80c358f8824ec1b20d349c92ed94c898090969b0`, installed Reader Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`.
- `native`: guarded optional ABI3 #641 `a639570c1e9f9b36decae3893265be74a6d185b0`, Reader blob `9bca5d1047f9c78984b945d7ca90e3149fe429ab`.
- `fused`: guarded ABI3 with authenticated stride-256 checkpoints #662 `a66fd593a83cc4c71556d3d86d835c51abd20a96`, Reader blob `c4d1dee0a31527b814d6e1f41b77abe1cc987996`.

The original signed revision-24 fixture builder is independent of all three product Builders. Six identical 16-byte range queries per session cover early/mid/late offsets, with full strong read/verify **only** on the smaller 4,096-reference control. Three balanced cycles, 6 source-exact processes per arm per profile, 3 sessions per process, CPU/wall phases separated from process startup. The source identity and active native or fused scanner were checked inside the installed worker. The baseline published Reader has **weaker hostile-input semantics** and is used only as an economic comparator for *valid identical inputs*, not as a security equivalent.

## Hosted custody, scientific decision
- **Measured instrument source:** `e278ec50f45a33b7915f0cb50edccd9bbc133041` (J24C14 research source, no product changes).
- **Original [hosted run #40668475834](https://github.com/FCMO-AI/.CMPCT/actions/runs/40668475834): SUCCESS**.
- **Artifact** `12806653136` [original signed receipt](https://github.com/FCMO-AI/.CMPCT/actions/runs/40668475834/artifacts/12806653136); archive ZIP SHA-256 `f6dda0110d33d70dcab2e53c6ecf622fd4c9fed089025a4dc4b691565c68da1f`.
- Raw `j24c14-original.json` plus `j24c14-verdict.json`, 72 independent workers / **216 matched sessions**, signed four fixture files, SHA256SUMS, setup/installed wheel metadata and tests.
- **Independent referee:** `J24C14_AUDITOR_PASS`; `STRONG_RELEASED_Q6_REHABILITATION_RESEARCH`. It rejected six forged receipt classes. A separately calculated audit recomputed nested process/sample medians, authenticated both raw receipt checksums plus the four fixture SHAs, and confirmed all four rows against the original referee.
- Dedicated actual-wheel inherited exact-r24 security tests: **48 passed, 1 skipped, 11 subtests passed** before comparison.

## Direct same-runner session performance (lower is better)

| Signed profile | Published wall | #641 ABI3 wall | #662 fused wall | Published / fused | Published CPU | Fused CPU |
|---|---:|---:|---:|---:|---:|---:|
| 4,096 refs / 1 owner, includes full verify | 48.616 ms | 49.036 ms | 48.145 ms | **1.01x** | 48.995 ms | 48.511 ms |
| 65,536 refs / 1 owner | 6.678 ms | 7.169 ms | **1.271 ms** | **5.26x** | 6.678 ms | 1.271 ms |
| 65,536 refs / 256 owners | 6.704 ms | 7.346 ms | **1.642 ms** | **4.08x** | 6.704 ms | 1.639 ms |
| 262,144 refs / 1 owner | 25.780 ms | 28.467 ms | **4.909 ms** | **5.25x** | 25.780 ms | 4.908 ms |

**Prospective strong-win criterion passed 3/3 major Q6 rows**: fused improved both wall and CPU against actually published by at least **5% and 3.0 ms** on each, with no material regression to the native-only control, no >8MiB peak RSS caution. Candidate minus released high-water RSS by profile: +0.090, -0.129, +0.070, +0.121 MiB. The 4,096-reference read/verify control does **not** show a material improvement; no generalized small-file benefit is claimed.

## Exported package cost / whole-system criticism
Same Ubuntu Python3.11 wheel build recorded actual compressed wheels: published `777,635 B` (`cp311-cp311`), native-only `788,622 B` (`cp311-abi3`), fused `793,299 B` (`cp311-abi3`). Thus fused costs **+15,664 B compressed wheel versus released**, **+4,677 B versus native-only** in these same-runner builds, before considering build-maintenance complexity, optional interpreter/compiler support, and installation/runtime dependencies. These are package artifact sizes, not archive bytes or deployed RSS.

Original negative CI attempts and their roots were preserved: an inherited O215 test searched the frozen mixed-codec vector under the GitHub Actions root rather than the nested `candidate/` checkout; a step-level override of runner-owned GITHUB_WORKSPACE did not affect this. The final exact-head run staged an **unmodified byte-identical copy** of the frozen vector into the expected runner location, retaining the same test and original data. A second infrastructure error came from inspecting `_chunk_range_marks` on historical ABI3 #641, where that *new* attribute did not yet exist. The optional access was corrected without modifying any historical source. These are route failures, **not performance evidence**.

## Decision, falsifier and research limitations
**Decision-changing positive:** the source-exact fused candidate demonstrably recovers the **measured** actual released Reader Q6 wall/CPU floor on a hosted Linux runner for three fixed RAW reference profiles. It therefore overturns the narrow claim that the J24C12 negative necessarily persists after the fusion.

**Not established:** released-Q1 performance for high-reference files, randomly positioned nonuniform end-to-end workloads, mixed codec/Zstd/Deflate physical owners, S_CDC/S_SPARSE/hardlinks, full create/extract/update/recovery, broad Windows/macOS released-reader A/B, wheel supply-chain and maintenance economics, complete real-world corpus coverage, mutation of exposed Python descriptor/hint structures, integrity/authenticity on all selective reads, official frozen 15-workload release matrix or normal unrestricted CI. Authenticated source-relative metadata admission is not interchangeable with cryptographically authenticating all selected decoded payload bytes. Results **must not** be presented as universal domination or 0.31 release readiness.

**Counterfactual prospective discriminator:** the correct published comparator could have been included at initial J24C13 materialization; comparing to strict Python or native-only masked absolute released-floor debt. This one transfer-worthy lesson did not justify modifying the normative Discovery Engine or `docs/discovery/STATE.json`. No version, format, test threshold, evaluator or PR ownership changed.

## Next highest-value executable action
Do not tune stride or expand ABI3-only microbenchmarks again. Reconcile remaining unrestricted exact-head CI failures against real semantic/product failures versus historical comparator pinning/expected-extension modes. Then test released vs native vs fused on **held-out large-reference irregular codec/owner mixes, Q1 early and late sessions, multiple files hitting the global checkpoint cap**, and preserve authenticated extraction/recovery/read_range semantics. If these materialize without product debt, owners of #641/#662 can consider a bounded integrated Reader promotion subject to the official release gates. If they fail, preserve the mechanism as a research seed with named regression debt, not a silent version win.

This document was added after the measured source HEAD: the resulting documentation commit is **not** retroactively claimed as the measured original source. The source/product trees remained unchanged.
