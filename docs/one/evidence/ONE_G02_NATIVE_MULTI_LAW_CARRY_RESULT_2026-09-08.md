# ONE-G0.2 native multi-Law carrying cost — exact result

**Date:** 2026-09-08  
**Decision:** `HOLD_NATIVE_MULTI_LAW_CARRY`  
**Admissible source:** `931c51428fe4a0a628c6a78e01247e1192f6ba5e`  
**Workflow run:** `34297969198`  
**Job:** `102298608298`  
**Artifact:** `10083925724`  
**Artifact digest:** `sha256:ededdfda6f520ab904d836a4451af9c38574fb80d4b1eda1ce314ac5934411e4`

## Result

The parent fused nomination substrate remained semantically green, but carrying full per-byte add8/XOR relation statistics inside the otherwise identical native run+reuse pass did not earn its compute budget.

Across the frozen 24-cell matrix:

- median candidate/baseline wall ratio: **1.598892x**;
- median candidate/baseline CPU ratio: **1.598666x**;
- worst wall ratio: **1.825533x**;
- worst CPU ratio: **1.830539x**;
- source scan remained exactly `1.0x` input;
- candidate semantic/support output matched the promoted Python oracle;
- baseline/candidate common run+reuse state matched exactly.

At 1 MiB, candidate wall ratios were:

| family | candidate / baseline wall | candidate MiB/s |
|---|---:|---:|
| long_runs | 1.5046x | 251.6 |
| exact_repeat | 1.5995x | 285.5 |
| add8_ramp | 1.8001x | 340.3 |
| xor_chain | 1.8255x | 344.1 |
| mixed_structured | 1.7876x | 320.9 |
| random | 1.3862x | 216.5 |
| compressed_like | 1.3948x | 216.0 |
| false_pattern | 1.3619x | 214.3 |

Absolute throughput is not the failure: the extra signals still sustain >200 MiB/s in the 1 MiB rows. The causal failure is **marginal information yield**. Compared with the exact same full run+reuse observation work, updating two 256-bin histograms and maintaining the lag-64 XOR relation on every byte adds roughly 60% median compute and up to ~83% on the worst row before any downstream exact synthesis begins.

## Interpretation / stop condition

Do not integrate this full-signal shape into the native observer and do not relax the frozen 1.25x median / 1.40x row gate. The information substrate itself remains promoted; this result says the relation cues must be **sampled, deferred, vectorized, or triggered from cheaper evidence**.

A causally different sparse descendant is therefore admissible: preserve full run/reuse observation, but sample add8/XOR relation evidence at a fixed stride while retaining exact downstream proof. That descendant must maintain generator-distinct relation nominations and prove a lower carrying cost under its own frozen thresholds. It is not a threshold rescue of this HOLD.
