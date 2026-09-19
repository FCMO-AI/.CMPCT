# v0.30 H-EFFORT-3 Adaptive-Effort Recovery Probe Result — 2026-09-13

Status: **durable negative research evidence; no release, R4, locality, geometry, filesystem-control, or product credit**.

## Evidence identity

- Exact result-bearing source: `96a71b17862e6edb59d7201740a6a68f731a4c70`
- Hosted workflow run: `34783539452`
- Job: `103794773985`
- Artifact: `10326151069`
- Artifact ZIP SHA-256: `e5e53c2b99520273668876d1b537c06514fabda4c85b2b567f2024881264148f`
- Historical policy source blob: `dc76dbfb17b8157cf453c2bb21c27459b34b1b7c`
- Referee verdict: **`RECOVERY_PROBE_NOT_READY`**

This receipt is the first H-EFFORT-3 execution that reached the scientific question. Earlier red runs were Custody/harness failures and receive no product or hypothesis-loss credit: the transfer court initially named nonexistent corpus surfaces, then incorrectly applied an Office product-locality verifier to held-out geometry, then coerced held-out explicit filesystem controls through the implicit-v4 restore path. Each defect was separated before this result-bearing run.

## Frozen hypothesis and gates

H-EFFORT-3 changed exactly one historical C25EG08 behavior: after the first strictly worse policy rung, permit exactly one fixed level-9 recovery probe if level 9 had not already been passed. No workload identity, path, fixture hash, learned threshold, or post-result selector was permitted.

The preregistered transfer court was the exact ten-workload current15 stable substrate. Office and Analytics were primary causal surfaces; all other eight workloads were held out. The gates were:

1. Office and Analytics each recover at least 90% of the full level-19 physical-byte oracle;
2. no held-out workload increases physical bytes versus historical C25EG08;
3. recovery-probe CPU is below 90% of direct level-19 CPU on every measured surface.

Observed gate state:

- `primary_ge_90pct_oracle = false`
- `heldout_no_density_regression = true`
- `all_cpu_lt_90pct_l19 = false`

The experiment therefore fails exactly as preregistered. Do not weaken or reinterpret these gates after the result.

## Result matrix

| Workload | Historical physical B | Probe physical B | L19 physical B | Probe share of L19 oracle | Probe/L19 CPU | Probe wins / probes | Locality product-bound state |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Developer Repository | 717,513 | 717,513 | 702,089 | 80.85% | 0.784x | 0 / 6 | pre-existing geometry debt |
| Office | 5,951,012 | **5,950,957** | 5,949,878 | **99.78%** | 0.738x | 1 / 2 | within bounds |
| Media | 28,726,832 | **28,724,216** | 28,724,268 | 100.37% | **1.093x** | 1 / 1 | pre-existing geometry debt |
| Analytics | 6,548,321 | **6,444,999** | 6,134,114 | **67.63%** | 0.733x | **19 / 20** | within bounds |
| Logs / Telemetry | 3,549,757 | 3,549,757 | 3,549,757 | 100.00% | **1.115x** | 0 / 0 | within bounds |
| Incremental Backups | 8,212,068 | 8,212,068 | 8,213,235 | 101.53% | 0.740x | 0 / 1 | pre-existing geometry debt |
| Incompressible / Encrypted-like | 10,185,390 | 10,185,390 | 10,185,390 | 100.00% | **1.062x** | 0 / 0 | pre-existing geometry debt |
| Many Tiny Files | 376,950 | 376,950 | 376,950 | 100.00% | **1.288x** | 0 / 0 | pre-existing geometry debt |
| ML Artifacts | 14,010,555 | **13,973,867** | 13,878,279 | **35.98%** | 0.365x | 5 / 11 | within bounds |
| Large Mixed Binary | 12,592,704 | 12,592,704 | 12,592,704 | 100.00% | **1.112x** | 0 / 0 | within bounds |

All held-out density comparisons are non-regressing. Filesystem fidelity and tail recovery passed on every held-out control. Held-out surfaces that exceed release locality bounds remain explicit geometry debt and receive zero locality/product credit; H-EFFORT-3 does not alter their geometry.

## What the negative proves

### 1. A fixed L9 recovery probe is not a sufficient universal repair

Analytics improves from 6,548,321 B to 6,444,999 B, a **103,322 B** gain over historical C25EG08 on the same physical geometry. However, it captures only **67.63%** of the L19 oracle and leaves **310,885 B** of physical residual. The 90% primary gate therefore fails materially rather than narrowly.

Office was already close to its oracle and gains only 55 B from the probe, reaching 99.78% of the oracle.

ML Artifacts independently transfers some of the mechanism — 36,688 B better than historical C25EG08 — but reaches only 35.98% of its L19 oracle. Developer Repository performs six recovery probes with zero wins.

### 2. Recovery existence is common in Analytics, but L9 is not the final depth

The strongest mechanism signal is that **19 of 20 Analytics recovery probes win**. The old `break on first worse` monotonic assumption is therefore decisively wrong on this surface. But a successful L9 observation does not imply that stopping at L9 captures the later L12/L19 headroom. H-EFFORT-3 fixes detection of recovery more often than it fixes the economic decision of how far to continue.

### 3. Sequential effort economics are a separate problem

The universal CPU gate fails even on several surfaces where the recovery probe does nothing:

- Logs: 1.115x direct-L19 CPU;
- Incompressible / Encrypted-like: 1.062x;
- Many Tiny Files: 1.288x;
- Large Mixed Binary: 1.112x.

Media also reaches 1.093x while obtaining a tiny density gain. This means the cost problem is not merely “the extra L9 probe.” On some pack populations, paying several historical ladder levels costs more CPU than simply executing the final expensive level once, while on other populations the ladder remains much cheaper than L19. A universal sequential ladder is therefore itself an economic assumption that needs causal admission.

## Strongest self-critique

The initial H-EFFORT-3 harness conflated three independent layers: effort selection, filesystem-control representation, and physical locality. That produced multiple red hosted runs before any scientific result. Those runs are infrastructure/Custody evidence only. The final referee deliberately holds physical units fixed, preserves implicit-v4 only on the primary surfaces where it is semantically admitted, preserves explicit-v1 filesystem semantics on held-outs, measures held-out locality without gifting product credit, and requires fidelity/recovery everywhere.

The repaired harness makes the negative stronger, not weaker: the selector loses after the confounds are removed.

## Decision

**Do not productize H-EFFORT-3. Do not tune its fixed L9 probe or relax its gates. Preserve it as a falsified universal policy.**

The next decisive question moves from “which one fixed rescue rung?” to **effort economics and bounded continuation**:

> Given only generic observations already paid for by the current pack evaluation, can CMPCT decide whether to terminate, buy one or more later recovery rungs, or jump directly to a terminal high-effort encode, while capturing most useful later-level headroom and avoiding the sequential-ladder CPU tax where direct L19 is cheaper?

The next experiment should be an R0/R3 causal referee, not a threshold-tuned Builder. It should expose per-pack size/CPU curves for levels 1/3/6/9/12/19 across primary and held-out surfaces, quantify oracle decisions under honest compute budgets, and test whether generic already-paid signals separate: (a) false-stop recovery packs, (b) packs worth continuing after recovery, and (c) packs where the ladder itself is economically dominated. Only after such separability transfers should a new selector be implemented.
