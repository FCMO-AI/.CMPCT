# J24G101 — Root-rebase / reader-epoch ownership: preliminary local physical result

**Evidence class:** independent **local Linux POSIX O0**, not a shipping CMPCT measurement or hosted exact-head result. This is an adjacent, not duplicate, falsifier for J24G100 in [PR #869](https://github.com/FCMO-AI/.CMPCT/pull/869). First preregistration: [parent comment #6537678039](https://github.com/FCMO-AI/.CMPCT/pull/869#issuecomment-6537678039), before the experiment; repository copy frozen at `05904b367f845e84a37ecfcda7df0dc47e3b627b`. Parent J24G100 source was `281bf0332709b3de2ec2cb676753c44ac9e7eb2e`. This document describes an **earlier independent local Python variant**, not the newly committed code's uncompleted hosted result.

## Concrete negative: the base is also an owned physical dependency

The J24G100 consumer pins a historical *tail* FD and releases the manifest gate, but later reopens `base.bin` by pathname. Under a cooperative one-writer root rebase, the new generation replaces the *base pathname* with an authentic earlier signed CMPCT prefix while retaining an old selected Reader. That Reader then reads the **new base + old tail**; the old manifest SHA rejects it. It fails closed, not silently accepting a new archive. Pinning the old base FD **under the same gate** before release, or giving each immutable base generation a unique filename, restores the precise previous physical CMPCT archive.

Four exact public Writer source archives from [#853](https://github.com/FCMO-AI/.CMPCT/pull/853), Ubuntu/Windows *origins* at N=4,096/8,192, each with 64 actual signed r24 footers, were tested on one **Linux** runtime. Provider ZIP checksums: `19e600a5c1f1798eb2ffeafffc3dd4fbaa81f09fc83090c4610d3d1f2ed42e0b` and `c697febe772527c0bb488d406325470837774b6df6c30aea191e4e383c61fcab`. The second-root referee was independently implemented without importing the producer or CMPCT; 7/7 forged receipts were rejected.

| Original physical source | Historical old Reader using pathname | Old root+tail FDs | Versioned immutable root name | Retained-root peak allocated ratio (root FD) |
|---|---|---|---|---:|
| Ubuntu 4,096 | FAIL CLOSED | exact PASS | exact PASS | 2.000× |
| Ubuntu 8,192 | FAIL CLOSED | exact PASS | exact PASS | 2.000× |
| Windows-origin 4,096 | FAIL CLOSED | exact PASS | exact PASS | 2.009× |
| Windows-origin 8,192 | FAIL CLOSED | exact PASS | exact PASS | 2.000× |

The four noncooperative **same-inode** one-byte mutation negatives were also detected by SHA even with a shared advisory lock; open FDs alone **do not immobilize in-place bytes**. All old tails were held while readers ran and became reclaimable after exit. New base+tail reconstructed the complete latest original archive byte-for-byte.

## Critical exported cost / architectural implication

The 2.000–2.009× figures are **lower-bound visible allocated data blocks around rebasing under one overlapping historical Reader**: current root+tail+HEAD, old base held through its FD or versioned name, and old tail. They do not include every transient staging file, directory/inode metadata, memory or power-fail durability. On this Linux overlay host the held old base alone retained 438,272–933,888 B of blocks, although its pathname was atomically replaced. A path-only `glob` after compaction would miss that hidden inode cost.

This narrows J24G99's earlier 1.004–1.019× *current-only* active-byte evidence: **immutable historical readers plus root rebasing are a materially different resource regime**. A robust system must trade off: (a) deferring compaction until readers finish, (b) retaining both immutable bases during overlap, (c) versioning/COW/reflink with real shared-block semantics and portability penalties, or (d) keeping a fixed root and paying rolling-tail write amplification. No option has earned product credit.

## Reproduction / provenance

Local instrument `j24g101_base_rebase_court.py`: SHA-256 `797f54203c3d7de62d3516a5c61842595079584aec1696d4eaa67176164146d5`.
Local independent auditor `j24g101_detached_referee.py`: SHA-256 `80fdd57f61d0fc5970d40507c4a6541a2a42e2e92e390f819c5631cb01833192`.
Local raw JSON receipt: SHA-256 `1ee895d8274caa902a0fc68417ab136c22c78a7227e9d97d787f3801f96abdd8`.

The **separate checked-in** experiment and referee are `research/j24g101_root_rebase_o0.py`, `research/j24g101_root_rebase_referee.py` and `.github/workflows/j24g101-root-rebase.yml` on this branch; unlike the local variant, their hosted exact-head result must be established independently. Do **not** substitute this local result for hosted CI, source-exact wheel or published product evidence.

## Self-critique, decision and next discriminatory action

**Decision:** `LOCAL_BASE_REBASE_OLD_READER_PATHNAME_LIVENESS_FAIL; FD/VERSIONED_CONTROLS_SURVIVE`. This is a **liveness/fail-closed distinction**, not an exploit against a shipped CMPCT Reader (the composition is an O0 research layout). Single cooperative writer; POSIX only. No real power cut; HEAD and base require separate renames, so atomicity of their pair is unproved. No multiwriter CAS, malicious same-UID source custody, Windows/macOS validation, native Reader, full RSS or end-to-end product economics. The base+tail FD remedy must also bind all metadata to the exact historical manifest and be refused when the original physical bytes mutate.

Cheapest decisive next action: obtain **exact-head hosted** J24G101 proof. If it survives, register the invariant with J24G100 owner: *every immutable physical component of a selected generation must be pinned before releasing its publication/GC gate*; assess retained-old-root blocks explicitly. Do not keep tuning fragment thresholds. Compare against the much simpler current CMPCT contiguous append + #823 optimized Reader and prioritize #857 committed ancestry / #290 Writer CAS / #749 verified publication.

**Counterfactual:** source inspection of J24G100's `read_selected(root,m,tailfd,...)` call after gate release shows a base pathname reopen and would have exposed this obligation before adding a GC protocol. It is a transferable prospective design check, but one experiment alone does not authorize changing discovery doctrine. Discovery `STATE.json` belongs to #574; unchanged.