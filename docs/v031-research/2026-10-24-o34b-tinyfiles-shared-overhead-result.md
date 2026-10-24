# O34b — Tiny-files inherited product overhead (2026-10-24)

**Decision: 46,049 B genuine-r24 product-byte loss is shared by unchanged shipping v0.30 and frozen compact-r24; it is NOT a differential compact-policy regression on this row. O34's frozen no-promotion decision remains unchanged.**

## Source, verification and reproducibility

- Parent decisive frozen full-court failure: [O34 run 40138113211](https://github.com/FCMO-AI/.CMPCT/actions/runs/40138113211) on HEAD `17a000f150f68e724efb6cdcdd3d1dddb079c5ca`, job `121003877559`, failed at `neutral_hostile_v1/08_many_tiny_files` before full 15+15 summary.
- Bounded post-hoc **different** question, hosted [O34b run 40142620847](https://github.com/FCMO-AI/.CMPCT/actions/runs/40142620847) on HEAD `b21edb08aff2b6713309b4eef761c9fc90c9df4c`, job `121017345403`: **SUCCESS** with source/ancestry/six frozen source Git blobs passing.
- Artifact `12578949883`, archive ZIP SHA-256 `d92424f196691253eee189852a6baa8b35aadb6161251eb287b3950e3a88092e`, includes `o34b-three-way.json`, raw `o34b-run.log` and exit code.
- Input: exactly one accepted historical-identity `08_many_tiny_files` generator, 5,000 regular files. Pre/post historical SHA-256 equals accepted `a62a03735deaaaebadacb961326c760aff09c1a4e031a44df02a9e95f8f5093f`.
- Three actual product archives were created and strongly verified via **independent fresh Python processes** against the *same unchanged source tree*. This matters because importing the frozen candidate mutates global policy owners in-process.

## Complete physical archive bytes

| Executed engine | Full bytes | SHA-256 / effective choice |
|---|---:|---|
| Genuine revision-24 `cmpct.builder.Builder` | **679,037** | `1df8a1442bf30451f221d91cc4b5cf1228b352f5b123f3e495e28fd542a8f7c6` |
| Unchanged v0.30 shipping front door | **725,086** | `128aa8bd34d8068d38bb37997e96d7a6a1839606cb7fcc9204a7431a8e3472c9`; `r24-fallback`, revision 24 |
| Frozen compact-r24 candidate `b878f40a...` | **725,086** | **same exact SHA-256** `128aa8bd34d8068d38bb37997e96d7a6a1839606cb7fcc9204a7431a8e3472c9`; `r24-fallback`, revision 24 |

All archives passed their corresponding explicit strong verification. Shipping and frozen candidate returned the same logical semantic tree identity `6c7c1ceb77a9c3a5950c973756f373bcbcb90951d74d477fb28e86e7ec03dae3`. The genuine-r24 control reconstructs the same input tree through the original revision-24 Builder/Reader.

**Measured difference: shipping minus genuine r24 = +46,049 B; compact minus genuine r24 = +46,049 B; compact minus shipping = exactly 0 B and byte-identical archives.** This is a single Linux/Python 3.11 hosted source-exact observation, not a noisy timing estimate.

## Causal scope and strongest counterevidence

This demonstrates the frozen compact policy did **not** introduce or amplify the many-tiny-files complete-byte overhead relative to the current shipping v0.30 product in this exact corpus. The overhead is already present under the shipping product's `r24-fallback` selection; **which specific shipping encoder-policy or metadata behavior caused it remains UNPROVEN**. It would be incorrect to attribute the 46,049 B to compact's 64-KiB Deflate rule or removal of medium-binary admission without a separate causal code diff / same-input A/B.

The **original O34 product gate still fails**: its frozen comparator is authentic `cmpct.builder.Builder` r24, not the shipping v0.30 branch. A measured negative against that control is not made positive by showing an inherited cause. The uncompleted 15+15 O34 matrix remains unmeasured in full; this post-hoc one-row test does not substitute a release or historical-compression claim.

Counterfactual value: an independent 5,000-tiny-file early product-parity canary would have flagged this exact-byte floor before ~45 minutes of full historical computation. Because this row was selected *after* observing the O34 failure, **prospective selection value for arbitrary future candidates is unproven** and no discovery policy modification is earned.

## Cost / integrity boundaries / next executable target

No new archive grammar, product change, promotion criteria, benchmark corruption or compression win; source custody passed and payload equality was independently verified. The three elapsed-wall single process observations are not comparable release timing evidence; full CPU/RSS/portability/selective recovery remain unmeasured.

**Actionable decision:** preserve compact as research seed where independent evidence warrants it, but do not promote this frozen candidate. If a materially different ownership/representation route requires this tiny-file overhead, first identify why the shipping r24 fallback exceeds the genuine r24 Builder on the same filesystem tree. Compare a minimal source-exact control and fully charge any proposed fix; do not garden thresholds or repeat the frozen matrix. Otherwise move to the higher-leverage v0.31 integration frontier.

This record is an append-only scientific result. Original O34 artifact, frozen science and promotion law remain immutable.

## Independent exact-head repetition — source metadata caveat (added 2026-10-24)

The repaired O34b workflow was **actually rerun on a newer exact source HEAD**: [run 40142869486](https://github.com/FCMO-AI/.CMPCT/actions/runs/40142869486), job `121018075003`, HEAD `bf65e97f2d8fff7966a7ee1bc96a1a5d6d09da83`, artifact `12579985869`, **SUCCESS**. Only the diagnostic workflow checkout/custody and this research note changed relative to the prior run; the Builder, promoted product, frozen compact candidate, corpus generator and experiment tool stayed source-identical.

The second independently regenerated source tree passed the **same accepted content-only** historical hash `a62a03735deaaaebadacb961326c760aff09c1a4e031a44df02a9e95f8f5093f` and yielded shipping/candidate identical full archive SHA within the run, but **not the same complete archive bytes as the first run**:

| Execution | Genuine r24 | Unchanged shipping v0.30 | Frozen compact | Shared excess | Frozen compact − shipping |
|---|---:|---:|---:|---:|---:|
| First, run 40142620847 | 679,037 B | 725,086 B | 725,086 B | +46,049 B | **0 B** |
| Independent exact-head, run 40142869486 | 676,749 B | 723,246 B | 723,246 B | +46,497 B | **0 B** |

The second run's genuine-r24 SHA was `3a0c296c73fd32fef3b378852d38e1550302722c1f4c61fe025d8fa2d3c326d3`; shipping/candidate both `6b732b3c487ef48942cf0868f4d4fc3d28efe822436671b43af8b94a04481c93`. Its full archive results were independently verified in-process. Its input semantic tree hash `6c7c1ceb77a9c3a5950c973756f373bcbcb90951d74d477fb28e86e7ec03dae3` also matched the first run.

**Critical scope correction:** the accepted historical tree hash authenticates regular-file names/lengths/content, **not all source metadata**; the product's user-tree SHA also deliberately excludes mutable metadata. Actual `src/cmpct/builder.py` stores `st_mtime_ns` per file/directory in the physical r24 index, so regenerated trees with identical logical content can have differing physical archives when metadata differ. Metadata is a plausible cause, **not proven as the sole cause** of the cross-run byte variation. Neither original byte count is a universal reproducible constant for this fixture without pinning filesystem metadata. The correct robust result is **within-run** product-relative parity: on both independent regenerations, frozen compact = shipping *byte-for-byte* and both exceed genuine r24 by 46,049 or 46,497 B respectively. This strengthens the attribution to shipping-inherited overhead while exposing a source-metadata comparability boundary for future *cross-run* claims.

No attempt was made to normalize timestamps retroactively, alter the frozen corpus or threshold, or compare archive bytes across different regenerated filesystem metadata as if they were identical complete-source trees. Stronger future metadata-level source provenance would need to account for all relevant metadata and runner/filesystem semantics before claiming deterministic cross-run stored-byte reproducibility. The frozen O34 NO-PROMOTION decision is unchanged. This second run is scientific replication/measurement-scope evidence, not release credit.

## O34c — decisive one-factor pack-budget attribution (2026-10-24)

**New direct evidence:** [Actions run 40143242776](https://github.com/FCMO-AI/.CMPCT/actions/runs/40143242776), job `121019173832`, exact-source HEAD `43f1020664cd47186f282110f2d4468aa9062d91`, **SUCCESS**, artifact `12579661831`. Frozen source ancestry/blob gate passed. Accepted historical regular-file content SHA remained `a62a03735deaaaebadacb961326c760aff09c1a4e031a44df02a9e95f8f5093f`; all **four physically distinct, fresh-process** archive builds were strongly verified.

| Same regenerated tiny-files source | Full stored bytes | Full archive SHA-256 |
|---|---:|---|
| Genuine revision-24 Builder unchanged | **677,765** | `be30a81436e3388bae48c8cebb44a4c6c224a1e6b4a4dfdbbb45ba6a71895a8c` |
| Genuine revision-24 Builder with **ONLY** `micro_pack_target` changed | **724,194** | `aab430dec254c7701495904c5ecb66634a27a614a47e02de41dad01669af21df` |
| Unchanged shipping v0.30 `r24-fallback` | **724,194** | **identical SHA** `aab430dec254c7701495904c5ecb66634a27a614a47e02de41dad01669af21df` |
| Frozen compact-r24 `r24-fallback` | **724,194** | **identical SHA** `aab430dec254c7701495904c5ecb66634a27a614a47e02de41dad01669af21df` |

The maximum regular file in this 5,000-file tree was **753 B**. The mature Builder uses `micro_pack_target=262,144 B`; the shipping product explicitly sets `min(2 MiB,8 × 753)=6,024 B` to preserve selected-member read-amplification budget. Changing **that one field alone** on the identical genuine r24 Builder emitted exactly the **same 724,194-byte archive and SHA-256** as the shipping and compact front doors. Difference from mature Builder is **+46,429 B** on this source regeneration; `shipping-minus-one-factor=0 B`, `compact-minus-shipping=0 B`.

**Causal conclusion, restricted to this exact source and environment:** the *release-only micro-PACK target reduction* is **sufficient** to reproduce the full complete-archive storage deficit. This is stronger evidence than a mere source-level hypothesis; no other shipping knobs are necessary to produce the observed bytes here. It does **not** prove there is no interaction on different corpora, nor that changing the pack target is safe for release. The shipping cap protects the frozen selected-member locality/≤8× decode-amplification invariant. Simply reverting the cap to gain ~46 KiB could export enormous selective-read amplification, violating the product's full Pareto contract. The source file itself is not a product fix; O34c was a post-hoc one-factor research instrument.

**Architectural next fork:** can a physically larger shared compression context retain ≤8× *bounded selective reconstruction* via genuinely independent sub-blocks, a reusable cross-block exact structure, or another generically admitted representation whose entire index/decoder/dependency cost is charged? Compare against the stronger simpler 6,024-byte locality-constrained product and the 262,144-byte larger-compression control, with full physical bytes **and** selective physical/logical work, CPU, RSS and read latency. A size-only reversal is not product progress. If no decision-changing plausible mechanism survives an inexpensive fully-charged bound, retire this local family and advance integration debt rather than gardening thresholds.

O34 frozen NO-PROMOTION remains intact: the 0-byte size regression gate against genuine r24 was not altered, the baseline had weaker locality policy, and the authentic failure remains. This also explains why successful compact-vs-shipping parity does not imply it can meet the stricter original comparator. Complete 15+15 O34 rows were not emitted. No product code, format, release gate or discovery policy changes. No release credit.
