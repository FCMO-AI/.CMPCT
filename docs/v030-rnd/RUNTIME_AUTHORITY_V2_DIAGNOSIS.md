# Authority-v2 runtime owner diagnosis — 2026-09-15

**Scope:** diagnosis of preserved exact-head runtime evidence from authority-v2 run `34919975890`. This note does not change a benchmark threshold, product byte, release gate, or release claim.

## Direct evidence inspected

The failed runtime artifact `10377997083` contains both `runtime-v2.json` and `runtime-tree-rss.json`. The latter measures whole process-tree RSS and is the correct custody surface for child-process-heavy creation.

## What is actually red

Whole-process-tree evidence shows peak RSS is **not** the current blocker. Maximum v0.30/v0.29 pack-RSS ratios are shifted `0.9538x`, logs `0.6295x`, ML `0.7297x`; the aggregate peak ratio is `1.0x`, within the frozen `1.25x` ceiling. The parent-only receipt's shifted `2.1099x` signal is therefore a measurement-custody artifact, not a product RSS regression.

Runtime debt is concentrated in two rows:

- `09_ml_artifacts`, selected `geometry-g04`: median create `1.4162x` (`~37.9 s` v0.30 vs `~27.3 s` v0.29) and median extract `2.0339x` (`~0.181 s` vs `~0.090 s`). It violates both `1.25x` per-workload ceilings. The row still saves about `161.6 KiB`, so deleting G04 merely to turn the runtime matrix green would discard material byte value rather than rehabilitate the mechanism.
- `05_logs_and_telemetry`: median create is `~0.0085x`, but extract is `1.3342x` (`~0.051 s` vs `~0.038 s`). This violates the per-workload extract ceiling and drives the three-row median extract ratio to `1.3342x`, above the frozen `1.10x` ceiling. The exact byte margin is only about `264 B` in this receipt, so carrying-cost/admission deserves explicit scrutiny if the extraction debt cannot be removed cheaply.
- `01_shifted_versions` is not a runtime blocker in the process-tree receipt: create `1.0585x`, extract `0.9101x`, RSS `0.9538x`.

All three measured rows remained byte-nonregressing.

## Diagnostic contamination found

`benchmarks/v030_g04_ml_extract_cprofile.py` wraps the shipping `PRODUCT.build()` and `PRODUCT.extract()` route in the private `PRODUCT.C._revision25_profile_context()`. The authoritative fresh-process worker does not do this; the shipping product owns its internal profile context. The diagnostic previously failed to get past `shipping_build_started` within a 15-minute envelope even though authority-v2 builds the same ML product in roughly 38 seconds. That mismatch is strong evidence that the profiler perturbs the route it is supposed to diagnose.

Do **not** optimize product code from the profiler's timeout/checkpoint. First rerun ownership profiling through the unwrapped shipping front door. The diagnostic remains research/evidence-enablement only; cProfile wall time itself receives no release credit.

## Next falsifiable action

1. Remove the external private r25 context from the ML extraction profiler while leaving the shipping product unchanged.
2. Require the diagnostic archive to remain G04 and strong-verify to the exact source tree before profiling.
3. Profile exactly one `PRODUCT.extract()` after one unprofiled warm extraction.
4. Use function-level ownership to choose the smallest product change capable of closing the `~2.03x` ML extraction debt without weakening authentication, verified restoration, transactionality, path semantics, or output budgets.
5. Separately attribute the ML creation delta (`~10.6 s`) from shipping build stats; do not mix that investigation with extraction unless the same owner is demonstrated.

`runtime-memory-selective` remains open and v0.30 remains merge/release locked.