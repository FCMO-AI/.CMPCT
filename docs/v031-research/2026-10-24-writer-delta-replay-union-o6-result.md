# O6 source-exact Writer/Reader × indexed journal replay — result and independent bottleneck

**Date:** 2026-10-24 UTC. **Status:** focused implementation/product evidence PASS on measured HEAD; product promotion withheld.
**Preregistration (immutable history):** `docs/v031-research/2026-10-24-writer-delta-replay-exact-union-o6-prereg.md` @ `5f446d0a6ba1ca317936524438aeae5dbaaf8680`. O6b and O6c prospective extensions were separately preregistered as comments on PR #355 before their instruments were written.

## Authority and source custody

- Parent Writer/recovery/security union PR #345 HEAD `33c4ef777542039ab3c1b97797e5ac8ca31af96a`, validator blob `015f619ebf5d775aff4858a51456669247808b21`.
- Independent efficient replay owner PR #348 `0062961be78cd4d28231a9acaf37a4d9cf43920c`, validator blob `1e085db992add64118a9488790096c574fff154d`.
- O6 implementation exact-source test digest SHA256 `35ccdfc6dbdc06cb9ba48e4504f1649fd11cab9d601c2d5bee02eef5a145752a`. It reconstructs all of `validation.py` from parent plus ONLY the original `_apply_delta_indexed`/`_apply_delta` function blocks and one `import heapq`; retains Python strict duplicate MessagePack map hook. The full validator candidate blob is `2bb3f53c918ae93efb105364e2b93ea46aeca034`.
- Product and research **measured on exact code HEAD** `8bd480682128fce24dfe66922ee3ea32fca454d7`, CI [run 40097415479](https://github.com/FCMO-AI/.CMPCT/actions/runs/40097415479), [raw Ubuntu artifact 12561636391](https://github.com/FCMO-AI/.CMPCT/actions/runs/40097415479/artifacts/12561636391). Parent PR remains unchanged.

## Positive O6 product evidence

- Cross-platform hosted O6 workflow **SUCCESS**, with exact-source test on each OS. Ubuntu and macOS each **31/31 inherited/source-bound O1+signed-tree+hardlink/differential tests passed**. Windows O6 job completed successfully; platform-specific branch count must be taken from its own log before separately asserting the number.
- Ubuntu: **3/3 new simultaneous signed journal and hardlink product tests pass**. Original Builder created real content; physically identical blob payload was reindexed with properly authenticated revision-24 primary/footer indexes; a genuine committed journal generation of 20 renames activated the indexed validator while retaining the hardlink owner relationship. Reader extraction preserved the bytes and inode hardlink equivalence; second signed generations containing owner deletion or a non-directory path ancestor were independently rejected.
- Original O1 independent slow-reference replay suite includes 10,000 deterministic mixed/duplicate/failure-operation sequences; original test blob `4e442f329051235950a4de7aef12ef9990658d35` was checked unchanged. All original signed-replay Builder instrument source remains unchanged at blob `02c5f506c9294130db6b0eb9c36c0a61460c3b35`.

## Authenticated journal preflight — O6 measured (median 5 AB/BA observations)

| Rename operations | Complete signed delta archive | Equivalent signed checkpoint | Delta preflight wall | Checkpoint preflight wall | Attributed replay wall |
|---:|---:|---:|---:|---:|---:|
| 128 | 1,627 B | 1,241 B | 0.741 ms | 0.559 ms | 0.143 ms |
| 512 | 2,739 B | 2,191 B | 2.553 ms | 1.838 ms | 0.574 ms |
| 2,048 | 6,953 B | 3,107 B | 9.849 ms | 6.965 ms | 2.641 ms |
| 4,096 | 12,046 B | 4,601 B | 19.313 ms | 13.799 ms | 4.813 ms |

Exact generated final index, physical original data and sampled member bytes were independently checked against the checkpoint. The original #347 historical-source same-runner ABBA showed 25.18× delta preflight improvement at N4096 but the two hosted runs must **not** be directly ratio-divided for a fresh claim. The extra metadata bytes for journal history remain a real cost.

## O6b independent **negative discovery** — Reader open remains quadratic

The untouched #345 Reader's `CMPCT(path)` constructor reconstructs journals in its own `_index_from_footer` algorithm with a linear scan per `ren` and repeated sorting. The same authenticated revision-24 journal/checkpoint cases were compared by actual product Reader constructor; payload reads were verified **outside** timed open, process startup excluded. Observations were five AB/BA-like alternating pairs on one Ubuntu runner.

| Operations | Journal Reader open median | Final-checkpoint Reader open median | Ratio journal/checkpoint |
|---:|---:|---:|---:|
| 512 | 4.794 ms | 0.713 ms | **6.73×** |
| 2,048 | 76.857 ms | 2.424 ms | **31.71×** |
| 4,096 | 362.393 ms | 4.995 ms | **72.56×** |

**Decision:** optimizing `preflight_archive` alone does not optimize the Reader's actual open/list path. The observed scaling is consistent with repeated full-table scans (and sorts). This is a **new material performance bottleneck**, not a newly fixed one. Source artifact JSON `reader-open-o6b-receipt.json` SHA256 **`95ffd850fe1996892ce949fb8f9b3263f027c86ba51c0a6754ee4dfb9170adc7`**. No Reader code was modified, and this child PR earns **zero Reader-speedup product credit**. These cases intentionally compare different physical journal/checkpoint archive sizes; equal final logical tree, identical physical payload source and same runtime isolate metadata representation as main causal factor, not a universal timing proof.

## Exported costs / uncertainties

Indexed signed preflight gains retain independent memory costs: #347 +42.77% Python traced allocation at N4096; #350 about +1 MiB post-call VmRSS at N16384 and no measured within-call peak; hardlink-star ~6–7% overhead inherited from #342. This exact combined HEAD is not a same-runner full release A/B against its direct base. No material create/extract, peak RSS, Windows/macOS performance, hostile destination race, full filesystem fidelity or release claim is earned from these focused tests.

## Honest next decision

(1) Preserve current source-exact validator composition as an unmerged draft, reconcile to #345 owner HEAD; (2) a **separate Reader-owned** scientific lane should test a bounded replay/index representation and direct output/exception/reference equivalence against original Reader, then measure cold open, list, arbitrary negative generations, CPU/RSS and filesystem behavior; (3) close exact-head general suite and **substantively executed** official r24 parity before any promotion. Do not waive zero-byte storage equality, parser limits, frozen comparison, duplicate-map rejection or other Writer/recovery/Reader invariants. Continue the mission in a different bottleneck family rather than further threshold-gardening the preflight mechanism.

**Discovery decision:** O6 material code product integration is validated in its focused court; O6b newly falsifies whole-path performance generalization; no general Discovery Engine policy amendment was earned. The repository's shared `docs/discovery/STATE.json` was left intact as a staleable cache rather than a competing authority.
