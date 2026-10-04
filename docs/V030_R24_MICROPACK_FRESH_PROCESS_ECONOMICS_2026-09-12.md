# v0.30 r24 locality-derived micro-pack fresh-process economics — 2026-09-12

Status: **research evidence; no release credit**

Exact measured head: `54edb4f1670ce07689362da7d42c3730d67bf263`
Hosted workflow run: `34737160471`
Receipt artifact: `v030-micropack-fresh-dominate-db-321911-54edb4f1670ce07689362da7d42c3730d67bf263`
Scientific verdict: `MICROPACK_DENSITY_AND_CREATION_DOMINATE`

## Mission lock

The already-earned locality-derived micro-pack mechanism had causal same-grammar density evidence, but product convergence still required a direct fresh-process economics check. The hypothesis was that, on current-fingerprint workloads where the mechanism emits groups, the derived candidate would remain strictly smaller than the shared-scan independent control **without regressing median fresh-process creation CPU or wall time**. The 8x locality law, strong tree identity, same membership grammar, source seal, and three alternating fresh-process rounds were fixed before execution. RSS was diagnostic only pending runtime/import attribution.

## Hosted result

The hypothesis passed on all three grouped workloads. No density, locality, tree, CPU, or wall failures were recorded.

| Workload | Independent bytes | Derived bytes | Delta | Independent CPU median | Derived CPU median | CPU ratio | Independent wall median | Derived wall median | Wall ratio | Max amp | Max decode unit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Developer repository | 971,421 | 916,933 | **-54,488** | 1.990726 s | 1.358719 s | **0.6825x** | 1.783232 s | 1.134386 s | **0.6361x** | 7.4659x | 17,490 B |
| Incremental backups | 8,124,689 | 8,120,712 | **-3,977** | 1.320467 s | 1.258691 s | **0.9532x** | 1.109526 s | 1.045581 s | **0.9424x** | 7.2068x | 41,342 B |
| Many tiny files | 1,021,059 | 757,613 | **-263,446** | 7.571840 s | 2.209128 s | **0.2918x** | 7.411510 s | 1.988992 s | **0.2684x** | 8.0000x | 5,264 B |

Aggregate over the three measured workloads:

- independent stored bytes: **10,117,169 B**
- derived stored bytes: **9,795,258 B**
- delta: **-321,911 B**
- independent fresh CPU sum of medians: **10.883034 s**
- derived fresh CPU sum of medians: **4.826538 s**
- independent fresh wall sum of medians: **10.304268 s**
- derived fresh wall sum of medians: **4.168959 s**
- maximum member amplification: **8.0x**
- maximum physical decode unit: **41,342 B**

This is a mechanism-level result: the derived grouping reduces both representation overhead and the amount of independent-object creation work. It is not a threshold-only density trade.

## RSS interpretation

Both contenders reported a median hosted-process peak RSS of **476,244 KiB** on every measured workload, yielding a measured delta of 0 KiB. That equality strongly suggests the observed peak is dominated by common runtime/import/harness state rather than the micro-pack product delta itself. Per the referee contract, RSS remains diagnostic-only until runtime/import attribution isolates the product-state component. This result therefore provides **no claim of RSS improvement**, only no observed differential at the current measurement surface.

## What this does and does not earn

Earned:

- same-input stored-byte wins on all three workloads where groups were emitted;
- strong-tree exactness;
- <=8x member locality;
- fresh-process CPU non-regression and fresh-process wall non-regression on all three workloads;
- a large creation-speed win on Developer and Tiny Files rather than a density-for-compute exchange.

Not earned:

- canonical builder change;
- release or version bump;
- a frozen Genesis rescore;
- universal generalization outside the measured grouped workloads;
- RSS improvement;
- permission to retain path/extension heuristics without causal ablation;
- permission to skip authenticated-integrity, recovery, reader, portability, or current15 transfer gates.

## Hostile-review consequence

The strongest remaining questions are now **generalization and unnecessary policy dependence**, not creation economics. In particular, the research builder still uses filename-extension information to form buckets. A separate causal ablation must determine whether extension-specific bucketing buys real stored-byte value under the same eligibility set and 8x law. The current15 transfer must also be rerun whenever shared physical/membership helpers change so stale evidence cannot survive mechanism repairs.
