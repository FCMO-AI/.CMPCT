# J24G86 — result: ordinary dense complete-index checkpoints fail byte budget on two physical histories

**2026-10-30, after immutable prospective preregistration at 6542b67af41f1ad533afdc33dbf03397aa849752. Research O0 only, not installed-product proof.**

## Primary question and verdict
Would fixed signed *complete-index* checkpoints every 8, 16 or 32 updates reduce a genuine pre-checkpoint cold Reader's maximum delta applications >=2x while increasing archive bytes no more than 5% on both authentic 8,192-file and 32,768-file 64-update histories?

**Result: DENSE_FULL_CHECKPOINTS_TRIAGE_FAIL on this authentic two-case family.** Existing 64-update checkpoint remains the simpler physical-byte winner among the tested policies. This is not a proof that no denser temporal representation can win; it is a negative specifically for independently serializing the entire existing r24 index at each additional checkpoint. In fact, the unchanged blob/recipe/fsmeta planes suggest a different *factorized* checkpoint model worth an independent cheap oracle.

## Original physical custody
Input: original J24G83 #833 detached ZIP SHA256 6d0542f0938740a0d82acb0e3f1a57a46fffc9ecafcc6c4bea79187cc607e016; inner GitHub-hosted ZIP SHA256 f8e21fdb7d7f52eb230ef2abdb0c06b24ae56ee165b3763c651128cf1460bc5a. No CMPCT import. Independently authenticated r24 header, initial index, linked 65 signed footers, 63 original DELETE ops and final checkpoint; verified CMA4 CRC32 and SHA256 for 8,192/32,768 original blobs; rejected deliberate mutation of a signed intermediate footer. Each physical archive matches the three public/fresh/owned alternatives in the original evidence.

- 8,192 middle deletes: 1,017,260 original bytes; archive SHA256 5e10557902c3bfe33f1136e4b99819eec0f6e9e98df3db1270c2d05cea37e26a.
- 32,768 tail deletes: 4,084,062 original bytes; archive SHA256 8402712cb12b53faf7868f60c27fb6c79b97272c76e5808d54c4b8aa623f8f81.
- Full index after each candidate generation preserved all original fields and retained blob descriptors. The independently derived final generation 64 index and its actual MessagePack SHA matched the source-authenticated physical checkpoint.

## Frozen criterion and measurements
The synthetic alternate footer serializes the *complete* effective index via MessagePack and optimistically chooses the smallest valid independently Zstandard-compressed body among levels 1, 3 and 19. Each replacement pays its entire 68-byte signed footer/body and deducts the exact authentic delta footer/body displaced. These are full-archive charged estimates, NOT rewritten runnable CMPCT archives.

| Source | Cadence K | Additional bytes | Archive overhead | Worst pre-final delta steps | Reduction of worst-case steps | Research gate |
|---|---:|---:|---:|---:|---:|---|
| 8,192 files | 8 | 524,590 | 51.569% | 7 | 9.00x | FAIL |
| 8,192 files | 16 | 224,854 | 22.104% | 15 | 4.20x | FAIL |
| 8,192 files | 32 | 74,954 | 7.368% | 31 | 2.03x | FAIL |
| 32,768 files | 8 | 1,983,983 | 48.579% | 7 | 9.00x | FAIL |
| 32,768 files | 16 | 851,774 | 20.856% | 15 | 4.20x | FAIL |
| 32,768 files | 32 | 281,058 | 6.882% | 31 | 2.03x | FAIL |

Even the *single additional* generation-32 full snapshot crosses 5% on both authentic archives. This negative is causally sharper than claiming all checkpointing is futile.

## Hostile independent codec check and contradiction preserved
A separate independent script used the **/usr/bin/zstd command-line frontend**, rather than ctypes ZSTD_compress, to reconstruct and compress the checkpoint-32 state with a declared stdin stream size and levels 1,3,19,22. At 8,192 files the CLI produced 74,348 B at level 1, versus 76,766 B from the single-shot native level-1 path. The codec frontends are *not* byte-identical; do not claim equality or hide the contradiction. The strongest CLI compressed snapshot still exceeds the original archive's 5% budget (50,863 B). At 32,768 files the strongest CLI snapshot was 281,091 B, versus the native 281,087 B, both exceeding the 5% budget (204,203 B). The research verdict remains unchanged under this independently better coding control. Larger or structurally different temporal encodings remain open.

## Alternatives / limits / cost transfer
- Replay counts are a **logical work proxy**, not measured Reader wall time, CPU or RSS. Zstd-19 encode work may add significant creation cost; raw per-level encode nanoseconds are present in the local research receipt, not claimed as product timing.
- Correctly charging a full authenticated index means including files, blobs, recipes, dict_blob, fsmeta, features and every footer. Partial field omission or silently deleting history would be an invalid same-semantics comparison.
- The source is two synthetic delete-only families under Ubuntu; signed-xattr/hardlink and mixed inserts are not proven. No release or general cross-platform claim is authorized.
- The external original physical archives are immutable; this experiment did not build a new functional r24 archive or test alternate Reader crash recovery. O0 evidence cannot earn O2 product credit.
- The selected 5% budget is an explicitly preregistered research filter, **not** a released performance threshold. A real product may accept different size/speed tradeoffs after full measurement.

## Counterfactual and next distinct-frame action
One generation-32 full checkpoint plus exact physical charging suffices to falsify the <=5% family in both archived cases (7.368% and 6.882%), without building new Writer machinery or running all 7/3 extra checkpoints. This discriminator was available prospectively from the authentic 65-footer archive. Next cheapest **different representation**: model the effective path/member plane as a signed snapshot while referring by authenticated immutable identity to unchanged blob/recipe/fsmeta planes; fully charge pointer, reader complexity and stability. Such a factorized checkpoint requires new explicitly versioned semantics and cannot be silently accepted by r24 Reader. Its usefulness must beat both the original deltas and optimized owned Reader #820/823, not only this deliberately large full-snapshot control.

## Evidence status / concurrency
Original script is in research/j24g86_periodic_checkpoint_oracle.py. The stronger local binary/full-CMA4 audit and independent CLI crosscheck plus their raw receipts are preserved in the run evidence archive. This branch owns no Reader/Writer lease, no #834 path frontcoding, no #795 journal implementation, no #574 discovery STATE and no frozen CI comparator. No CI, merge, release or exact-head product benchmark is claimed by this local O0 result. Do not treat historical CI from #833 as this branch's CI.
