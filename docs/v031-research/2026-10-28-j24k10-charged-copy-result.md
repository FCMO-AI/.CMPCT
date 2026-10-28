# J24K10 — Fully charged source-copy ownership versus repeated VZIP physical witness

Date: **2026-10-28 UTC**. Result status: **H1/H2 CONFIRMED AT COMPONENT ORACLE TIER, NO PRODUCT PROMOTION**.

## Source custody and preregistration
- Parent J24K09 [#653](https://github.com/FCMO-AI/.CMPCT/pull/653) at exact \`2d30cc6da41c136f3b1a412ccf3f1f5686dca54a\`, with unchanged Reader \`e77578505985dd264d69425e3bc816c421ae3cdc\`, codec \`fe692c4595c1303dbc89b7d660501e4ef0f223c3\`, original synthetic fixture \`e3ad370ff8253fff999f003637e30cde53a5ce52\`.
- Frozen prospective preregistration first: \`5ac29be011e9c1cfcae96358e25dc97697f0fd32\`.
- **Result-bearing exact scientific source HEAD**: \`58f630c8a3306bdb7836db034b6d3d33e61d4f67\`; [three-host GitHub Actions run #40648529165](https://github.com/FCMO-AI/.CMPCT/actions/runs/40648529165) **SUCCESS (3/3)**.
- Raw original ZIP artifacts: [Ubuntu #12798409958](https://github.com/FCMO-AI/.CMPCT/actions/runs/40648529165/artifacts/12798409958), [macOS #12798726197](https://github.com/FCMO-AI/.CMPCT/actions/runs/40648529165/artifacts/12798726197), [Windows #12798189726](https://github.com/FCMO-AI/.CMPCT/actions/runs/40648529165/artifacts/12798189726).
- Three-host source-exact installed-wheel checks, original J24K09 fixture and fixed Reader/codec blob hashes passed. Independent stdlib referee passed 12 cells/host, 240 raw arm observations/host, five forged receipts rejected/host. An *additional detached audit* of the downloaded original ZIPs independently verified ZIP CRC/SHA, raw-cell arithmetic, source SHA derivation and agreement with the hosted referee, without modifying the frozen instrument or its evaluator. These are independent evidence checks, not independent CMPCT reader implementations.

## Primary decision: all source bytes matter to cached-proof economics
**Predictions H1 and H2 both confirmed within exact preregistered component scope.** Median speed ratio = (per-query BHDR-proof wall) / (copy full source + prove once + Q ranges wall). A ratio >1 favors copying/prevalidation; <1 favors current per-query proof. Within-host paired comparisons only.

| Source geometry | Q | Ubuntu ratio | macOS ratio | Windows ratio | Decision |
|---|---:|---:|---:|---:|---|
| 512 streams, no unrelated padding (~64 KiB) | 1 | 0.75x | 0.18x | 0.46x | copy loses |
| 512 streams, no padding | 8 | 3.23x | 1.76x | 2.09x | copy wins |
| 512 streams, no padding | 64 | **5.56x** | **4.82x** | **4.33x** | copy wins |
| 512 streams, +64 MiB | 1 | 0.034x | 0.024x | 0.022x | copy loses |
| 512 streams, +64 MiB | 8 | **0.26x** | **0.22x** | **0.16x** | copy loses |
| 512 streams, +64 MiB | 64 | 1.59x | 1.27x | 1.05x | marginal/host-sensitive win |
| 4,096 streams, no unrelated padding (~512 KiB) | 1 | 0.84x | 0.70x | 0.74x | copy loses |
| 4,096 streams, no padding | 8 | 3.44x | 2.82x | 2.98x | copy wins |
| 4,096 streams, no padding | 64 | **5.47x** | **6.15x** | **4.80x** | copy wins |
| 4,096 streams, +64 MiB | 1 | 0.22x | 0.15x | 0.14x | copy loses |
| 4,096 streams, +64 MiB | 8 | 1.39x | 1.13x | **0.93x** | mixed; no universal benefit |
| 4,096 streams, +64 MiB | 64 | 4.31x | 3.44x | 3.38x | copy wins |

**Causal discriminator**: for 512 streams/Q=8, adding 64 MiB of unrelated physical source bytes reverses the winner on **all three platforms**, despite identical logical selected member, stream count, proven BHDR records and one-byte suffix result. Any admission policy based only on number of streams/Q without complete physical-source size is structurally unsound. Copying 64 MiB dominates small-session economics. The 512/Q=64/64MiB Windows +5% relative win is close enough to measurement noise to remain **ambiguous**, not a product permission.

## Charged bytes and sample scope
- Source-copy allocation per session: **65,664 B** (512 streams) or **524,416 B** (4,096 streams) without padding; **67,174,528 B** or **67,633,280 B** with 64 MiB padding.
- Additional Python cached-physical-size table: **18,552 B** or **147,736 B**, respectively. These are retained Python-object byte estimates, not total RSS.
- Original source remained memory-mapped in both arms. The copy arm additionally maps a full private scratch file during the session; mappings have OS/page-cache/workset costs not captured by Python-list size accounting.
- Five ABBA cycles; 10 raw observations per strategy per cell; **36 host/cell results, 720 raw observations**, 15 deliberate forged receipt refusals, complete per-cell wall/CPU/copy and size accounting. CPU measurements with OS quantization remain raw, including zeros.

## Strongest negative / self-critique
This is intentionally **not a complete revision-24 archive, nor an end-to-end CMPCT Reader open/read**. The physical size witness is the true installed Reader method applied to authentic BHDR geometry, and \`range_vzip\` is true installed CMPCT code, but the selected member's skeleton/payload data are supplied by a fixed fixture Python callback. Therefore the experiment proves the **economic effect of full-source copy on repeated physical geometry proof**, **not** that a copied Reader reconstructs from its copied source or that snapshot-cache semantics are safe.

A private disk copy is neither kernel-sealed nor atomic against concurrent source mutation. The original was quiescent. No proof of partial-range SHA authentication, same-inode mutation resistance, full-file integrity, process startup, platform filesystem durability, whole-product CPU/RSS, native Reader parity, or official release benchmarking follows. Full source copying adds I/O and temporary disk footprint equal to the entire archive, not only the selected member. The scratch copy was not fsynced (optimistic lower bound); archive-content copy SHA was not part of the original frozen instrument, so only source SHA and physical proof were authenticated/checked. The detached reviewer reconstructed deterministic source SHA independently, but did not rewrite frozen raw measurements.

## Counterfactual and product decision
Had the first J24K09b design been charged **total source bytes copied** (not only the proof table and logical-member count), the high-Q small-source gain would have been recognized as conditional earlier. A prospectively recognizable discriminator for any future "cached validation" proposal is **source bytes / number of repeated range queries / ownership lifetime**, with mutation safety as a hard prior veto.

**Decision**: Do not promote unconditional source-copying or a per-open physical proof cache. Keep the physically checked lazy Reader candidate as research reference; investigate bounded explicitly immutable source ownership (O26 Linux memfd already measured and carries memory cost; no duplicate implementation) and/or a structural proof/index that does not require cloning the entire archive, while preserving exact format and hostile-source guarantees. Re-run an actual signed r24 installed Reader/equivalent semantics court before claiming product leverage.

No parent code changes, no format/version/CI threshold modifications, no discovery-state mutation, no merge or release. Prior negative J24K09b source-immutability caveat remains.
