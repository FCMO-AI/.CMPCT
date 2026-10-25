# O39 — Held-out 32k hardlink Reader scaling: source-exact positive research receipt

**Date:** 2026-10-25 UTC. **Status: RESULT-BEARING SCIENCE; no product merge/release credit.** The immutable prediction is [O39 prereg](2026-10-25-o38-heldout-hardlink-scale-o39-prereg.md), committed **before implementation** at `baeb17f7881edf6a19ceb4842105d0e99ba2b769`. This result does not amend its criteria or the official zero-byte/performance promotion gate.

## Exact observed experiment identity

- Parent **O38 product Reader**: [PR #392](https://github.com/FCMO-AI/.CMPCT/pull/392), commit `dffc6da03b588e209843f2fc6e219e5bce3a7800`, source Reader blob `4aee9e8ddf50ff3c3e0db20ebf7671e2ac477867`.
- Stronger historical **O31 control**: [PR #385](https://github.com/FCMO-AI/.CMPCT/pull/385), commit `0edb7bc6e832deb1b403fea50c36e655da9844fd`, Reader blob `de9accf6607aca7cf70dfe71d7b299a02e298a2d`.
- Actual O39 research **evidence checkout HEAD** `50bfcce78b9fd6331930dba5eb5e36a325be64aa`. Its tracked entire `src/` and `native/` trees are source-identical to the exact O38 product parent, not a separate product variant. The instrument asserts O31 checkout HEAD equality, O38 ancestry, equality of full product/native trees and both Reader blobs before measuring; the raw receipt separately records the evidence checkout HEAD.
- Hosted **actual** [O39 run 40146154694](https://github.com/FCMO-AI/.CMPCT/actions/runs/40146154694): successful `latest-head-impact` and actual `exact-source-scale` job; **25/25** original hostile/positive tests PASS; **128/128** ABBA/BAAB fresh-process measurements collected across eight authentic SHA-committed revision-24 fixture archives (8192/32768 members × plain/fanout/chain/noncanonical).
- Original raw JSON artifact [#12580562343](https://github.com/FCMO-AI/.CMPCT/actions/runs/40146154694/artifacts/12580562343), ZIP SHA-256 reported by GitHub Actions: `12d451e69295a73493a81684537db9c436533648b933abeaa6d34ea07440b0de`. Raw `o39-raw.json` SHA-256 reported by the producing process **`df0b9ed16feaa008aeb344aaa77ba2db861b411146c6ada9a79f8a4a6a426ff4`**. Do not imply an independent download audit of the ZIP was performed: evidence here is the source-bound hosted execution and its own raw-checksummed artifact.
- Ubuntu 24.04 / Python 3.11, one hosted runner. Each exact archive is generated once, strongly preflighted and read/range/SHA/strong-verified before timing, then given unchanged to both engines in eight independent fresh processes each. Kernel page cache is **not** guaranteed cold; only processes are fresh.

## Direct measurements (median constructor wall milliseconds)

| Signed r24 structure | O31 8,192 | O38 8,192 | O31 32,768 | O38 32,768 | 32,768 result |
| --- | ---: | ---: | ---: | ---: | --- |
| Plain regular members | 14.873 | 14.927 | 55.218 | 55.403 | **0.185 ms slower / +0.335%** |
| Exact-key hardlink fanout | 28.105 | 21.128 | **111.963** | **82.169** | **29.794 ms saved / 26.611% less** |
| Exact-key hardlink chain | 27.654 | 21.073 | **112.728** | **81.137** | **31.592 ms saved / 28.025% less** |
| Valid noncanonical separator target (fallback forced) | 30.179 | 31.124 | **119.109** | **121.752** | **2.642 ms slower / +2.218%** |

The exact-key 32,768 fanout candidate processes complete in **170.267 ms** median versus **199.514 ms** historical (**29.247 ms saved**, 14.659% of entire subprocess wall). Constructor CPU medians track the improvement (112.169→82.350 ms), weakening pure timing-noise explanations.

**Memory export:** fanout-32,768 post-constructor RSS **42,996→42,972 KiB** (candidate 24 KiB lower); chain **45,468→45,562 KiB** (+94 KiB); plain **39,546→39,640 KiB** (+94 KiB); noncanonical **42,988→43,028 KiB** (+40 KiB). These are not function-level allocation traces and may conceal short peaks; reported HWM increment for fanout 19,360→19,368 KiB (+8 KiB).

## Prospective fork decision

The preregistered candidate **PASSED** the research criteria:
- Fanout 32,768 direct constructor gain **29.794 ms**, greater than required **8 ms**.
- Ordinary/plain 32,768 cost +0.185ms (+0.335%) and noncanonical fallback +2.642ms (+2.218%); neither meets both 5ms AND 10% adverse thresholds.
- No selected corpus meets both +4,096 KiB AND +10% postopen RSS regression thresholds.
- 25 unchanged hostile tests passed; all eight corpus shapes were preflighted and strongly read/verified before measurement, and all 128 samples completed.
- The original 4,096-instance O38 gain is independently **generalized within this larger, still synthetic, same-semantics family**, not extrapolated to arbitrary workloads.

**Falsified/narrowed:** the concern that the O38 shortcut only survives its 4,096 friendly input was **not supported** in this 32,768-fanout regime. The positive decision is about Reader constructor and process performance in this tested family, **not** an extractor or general storage-size win. The valid noncanonical fallback is slightly slower, and this negative remains part of the Pareto assessment; it is not hidden by the exact-key gain.

## Infrastructure negative and correction

Initial [run 40145892467](https://github.com/FCMO-AI/.CMPCT/actions/runs/40145892467) passed 25 inherited hostile tests but produced **zero O39 timing observations**: the newly derived research script incorrectly demanded that its *evidence-only* branch HEAD equal the immutable O38 *product* HEAD, even though their Reader blobs matched. This was an instrument-provenance predicate mistake, **not a product/algorithm loss**. The subsequent source-check correction requires exact O31 HEAD and a candidate checkout descendant of O38 with identical tracked `src/` and `native/` trees, and the next correction separately records the actual evidence checkout SHA; neither changes the frozen O39 prediction, Reader, benchmark, comparator or gate. Full successful source-bound run and raw receipt are above.

## Concurrency and scientific lessons

This is a separately preregistered **independent replication** and never modifies the product owner [#392](https://github.com/FCMO-AI/.CMPCT/pull/392). That owner was informed before execution. The O39 question differs from its 4,096 benchmark: cardinality, shape diversity and a forced canonical fallback with complete memory/process accounting. The cheapest prospective discriminator is the high-cardinality exact-hit fanout versus an equally sized noncanonical target family. The source-HEAD mistake also shows why a benchmark must distinguish *product identity* from the evidence branch commit; the narrow correction is enough, and no Discovery Engine policy modification is earned.

## Completion status / next decision

**Science:** positive and decision-changing for held-out synthetic high-cardinality Reader opens. **Product implementation:** none in O39 (O38 separately owns implementation). **Infrastructure:** exact-source workflow and raw evidence functional; first provenance failure preserved. **Shipping/release:** no new code, merge, version bump or release. The O38 product owner should consider O39 a supplemental scaling receipt, reconcile its own full exact-head suites/installed packages/official parity, and then return to a materially different product frontier rather than optimizing the same local mechanism further. Do not generalize beyond signed r24 checkpoints with one small physical RAW payload and this Linux runner; storage bytes, large decode, extraction inode semantics, concurrency and recovery were **not** benchmarked here.
