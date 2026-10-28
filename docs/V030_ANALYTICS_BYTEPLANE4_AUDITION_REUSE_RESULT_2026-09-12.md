# v0.30 Analytics BytePlane4 audition-reuse result — 2026-09-12

Status: **negative; audition-byte reuse retired without tuning**.

Source head: `0830bd258db4bac1d2c7fdfd848bdbe2fb5f1a40`
Hosted run: `34731795608`
Schema: `cmpct-v030-analytics-bp4-audition-reuse-v1`

## Exact hosted result

| mode | archive bytes | median complete verified create | process CPU | peak RSS |
|---|---:|---:|---:|---:|
| direct L17 | **6,210,959 B** | **3.622724326 s** | 3.774859162 s | 475,376 KiB |
| reuse transformed L1 audition | **6,197,497 B** | **3.791841699 s** | 3.943675367 s | 475,376 KiB |
| strong BP4+L17 | **6,134,444 B** | **3.840354422 s** | 3.990261735 s | 475,376 KiB |
| direct L19 | **6,135,703 B** | **8.588048995 s** | 8.738972116 s | 475,376 KiB |

Accepted v0.29 remains **6,135,172 B**.

The reuse candidate selected only **1** transformed level-1 payload from 50 auditions / 2 cheap winners. It saved only **13,462 B** versus direct L17 and therefore remained **62,325 B larger than v0.29**. The strong BP4+L17 seed still saves 76,515 B versus L17 and crosses v0.29 by 728 B.

Timing also falsified the hoped-for shortcut. Reuse was only **1.263% faster** than the strong BP4+L17 seed, far below the preregistered 10% hurdle. It added 0.1691 s versus direct L17 and executed zero transformed-L17 calls exactly as required.

Verdict: **`RETIRE_AUDITION_REUSE`**.

## Interpretation

The cheap transformed L1 encode is useful as a structural detector, but not as a sufficiently dense final representation on the frozen Analytics workload. One of the two strong structural winners needs the additional L17 search to retain the byte floor. The strong transformed encode is therefore not broadly redundant work on Analytics.

This result also corrects any temptation to infer the `counter32` hostile-transfer cost directly onto Analytics. `counter32` exposes an extreme case where transformed-L17 work dominates a tiny raw baseline; Analytics pays much less transformed-L17 cost and needs the density it buys.

Do not tune transformed levels, widths or reuse thresholds from this negative. The best surviving Analytics research point remains the fixed **BP4+L17 seed at 6,134,444 B**, with the generator-distinct generalization claim retired until a different execution mechanism or stronger product-economic representation earns another test.

## Next action

For Analytics, stop local compression-level micro-tuning. The next useful work is product-economic integration: quantify how much additional r25 reader-visible metadata/auth/recovery/native machinery the 728-byte research margin would require, and either find a general metadata compaction that creates real headroom or declare the current seed too thin for promotion.

In parallel, continue the independent tiny-files/developer compact-control attribution lane; it is not coupled to BytePlane4.

No aggregate score, canonical version, ONE result or `research/cmpct1` authority changes.
