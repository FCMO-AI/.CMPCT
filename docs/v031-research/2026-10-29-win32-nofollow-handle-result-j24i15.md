# J24I15 — source-exact Windows no-follow HANDLE result: speed hypothesis falsified

**Date:** 2026-10-29 UTC. **Decision:** `SAFE_LEAF_COST_WIN_FALSIFIED`. **Classification:** narrow security/control-positive plus performance-negative **research evidence only**; no product code changed, no merge or release.

## Frozen question and exact source
Prospective prediction (before instrument) is [J24I15 prereg](2026-10-29-j24i15-win32-nofollow-handle-prereg.md), commit `e2376aad4905741b35e664a7d8b73833fab261e4`. Source-exact genuine GitHub Actions [run #40831313188](https://github.com/FCMO-AI/.CMPCT/actions/runs/40831313188), original physical [artifact #12878024229](https://github.com/FCMO-AI/.CMPCT/actions/runs/40831313188/artifacts/12878024229), SHA-bound executed HEAD `9449f0f7bb32cf35b29d257960a3d5262b3d5935`; Windows Server 2022 (`Windows-10-10.0.20348-SP0`), installed Python 3.11 CMPCT from site-packages, checkout source unmodified from J24I13 parent `73961bdf991553ce27c74418a72bc9f394155257`.

Physical original artifact includes `head.txt`, `instrument-blob.txt` = `75ace585cd3b2b2e8bdae07de26448826796a675`, `unchanged-builder-blob.txt` = `b3c8cbfbefb9d47ffa849bd939257215ee4b0a09`, and full `receipt.json` with 64 timing samples (two families × A/A and A/B × 4 ABBA rounds × 4 readings). These blobs were compared with the actual repository Git blob identities, not guessed from a file name.

## Result with raw paired control values

A = original O47-like `os.stat(path, follow_symlinks=False)` plus ordinary `open/read`. B = `CreateFileW` leaf `FILE_FLAG_OPEN_REPARSE_POINT`, `GetFileInformationByHandle` physical owner metadata and read via that SAME opened handle. Both SHA/hash exactly the same data and preserve real hardlink ownership. Less time is better.

| Family | A paired wall (ms), 4 rounds | B paired wall (ms), 4 rounds | Paired B/A |
|---|---|---|---|
| 256 independent, 16,384 B read | 23.522 / 21.906 / 21.754 / 22.048 | 46.113 / 46.260 / 43.204 / 43.034 | 1.960 / 2.112 / 1.986 / 1.952 |
| 3-path physical ownership graph, 12,384 B | 0.27985 / 0.28235 / 0.27925 / 0.28010 | 0.53225 / 0.57785 / 0.48675 / 0.52390 | 1.902 / 2.047 / 1.743 / 1.870 |

Independent recomputation from raw receipt gives **median of four paired B/A ratios 1.97322× for 256 regular files** and **1.88616× for three-path graph**, against the required **<=0.90× in at least 3/4 rounds**. Actual favorable rounds: **0/4** on both families. Median standalone four-round means: A **21.97705 ms**, B **44.65820 ms** for the 256-source case. These are **microeconomics of source opening**, not complete CMPCT archive creation or an official release gate.

## Independently reconstructed integrity and semantics
A detached referee reconstructed the full synthetic inputs directly from the fixed test equations, **without importing CMPCT or trusting producer SHA fields**:
- 256 independently named 64-byte files: corpus SHA-256 `154ffac524c7f5f1590c96e864a18dcfb860d2a8c6d660ce00adb8896b887adb`, every one of the 256 physical identities independent, each with link count 1.
- Two physically linked names plus one byte-identical independent copy: corpus SHA-256 `06a27e9a63a556661462f91cb64353f03bc003cd89f8d723d72d4a1ef4c6a0d3`; owner partition `[0,0,1]`, link counts `[2,2,1]`.
- Hostile final symlink targeting an unrelated real file was refused as `RejectedSource` before reading; directory source was refused; legitimate hardlink owner opened and produced expected SHA.
- All 64 timed records retained the exact expected input digest/read bytes, A/A/ABBA order, and positive measured intervals. Recomputed eight ABBA pairs match original producer values.
- The detached referee deliberately falsified six receipt fields (source SHA, physical owner partition, timing ratio, raw trial side, disposition, hardlink count) and **rejected 6/6**.
- This is source-level and research-receipt evidence, not a physically retained archive product oracle: no candidate CMPCT archive was built by this experiment, and no source-tree race under adversarial ancestor mutation was exercised.

## Causal interpretation, strongest negative and counterfactual
The leaf nofollow handle approach *eliminates the earlier final-symlink ambiguity* in this installed Windows regime, and authentic handle file IDs retain the genuine hardlink graph. However, it takes roughly twice as long per loop as the established correct O47 static-source control, largely eclipsing the hoped-for avoidance of one pathname stat. We did not independently decompose kernel calls vs Python ctypes/CRT overhead, so the exact cause of extra time is **UNMEASURED**; the overall scoped route is nonetheless defeated under preregistered economics.

This is not a generic rejection of descriptor-rooted source design: the earlier O52 POSIX provenance negative and O77 Linux rooted-open evidence establish a *separate safety problem* where final-component protection alone cannot secure ancestor symlink/junction changes. If stronger containment is required, architecture should prioritize root/parent source custody and genuine full-product safety, measuring costs afterward, rather than tuning or repeating Win32 leaf metadata variants. An earlier one-shot end-to-end safe opened-handle micro discriminator would have avoided a speculative faster product fork; this supports the existing BONK demand for cheap falsifiers, but does not earn a Discovery policy change.

## Scope, debt, and coordination
- Product/safety scope: O47 #401 and compaction integration #730 retain ownership. No new Builder branch/source implementation is justified by J24I15. Existing stage-name corruption veto #726 remains independent and release-blocking.
- Win32 contract caveat: `BY_HANDLE_FILE_INFORMATION` exposes 64-bit file IDs; Microsoft documents 128-bit `FileIdInfo` as necessary on ReFS for guaranteed uniqueness. No ReFS, SMB, junction-parent races, update/recovery, or process snapshot guarantees were tested.
- Original same-source #733 standard-open fstat micro win remains a **non-equivalent-unsafe-control-only** and must not be mixed with this negative to claim product speed.
- Exact-head General Tests, Engineering Evidence, Native, Fuzz, Version Discipline and r24/ZIP workflows are separate; workflow administrative success or a skipped performance job is not release credit.
- No changes to discovery state/cache, format, benchmark evaluator, released main or numeric version. Original prereg and negatives remain append-only.

**Next action:** communicate narrowed negative to #401/#730; stop the current Win32 *leaf-only speed* family. Focus on architecture required for source root/parent custody or on existing hard compaction publication/security blockers, not another nearby threshold experiment.
