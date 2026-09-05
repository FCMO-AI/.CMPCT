# ONE-G0.2 — one-pass fixed + epoch native signal fusion

**Status:** native pass-fusion win preserved; structural replacement remains blocked by edited-version negative  
**Exact result-bearing source:** `df6bb7b5b0ad06671d23583d065de639b9565862`  
**Workflow:** `33947907823`  
**Job:** `101257217039`  
**Artifact:** `9963910257`  
**Artifact digest:** `sha256:049d3fb353bbdeef62af77ed23329b439a0ac03291f672e17f8ef68382656498`  
**Experiment:** `ONE-G0.2`

## Referee freeze

The complete-reference integration A/B showed that epoch-min's economics survive index/proof bookkeeping, but both arms still scanned the input twice. ONE prefers a fused observation pass. This experiment isolated that execution question only.

Baseline: two native scans, one fixed-signal call plus the exact standalone epoch-min call.  
Candidate: one native byte-forward loop producing both fixed and epoch traces.

Frozen gates required exact fixed trace equality against an independent Python oracle, exact epoch trace/final-state/accounting equality against the standalone native epoch kernel, one source scan instead of two, <=0.95x elapsed on every >=64 KiB row, and <=1.05x on the hard ~8 KiB rescue row.

## Result

All **50 ONE semantic tests** passed. Exact fixed and epoch traces matched on every row. Gate failures: **none**. Frozen decision:

`advance_one_pass_signal_fusion_to_index_integration`

| Case | Two-pass median | One-pass fused median | Fused / baseline | Elapsed reduction |
|---|---:|---:|---:|---:|
| random 1 MiB | 4.127619 ms | 2.832379 ms | **0.685622x** | **31.4%** |
| zlib-random ~1 MiB | 4.130568 ms | 2.830381 ms | **0.685562x** | **31.4%** |
| repeated 64 KiB basis / 1 MiB | 4.040528 ms | 2.790915 ms | **0.684819x** | **31.5%** |
| shifted 512 KiB pair + 1 byte | 4.156625 ms | 2.840456 ms | **0.682927x** | **31.7%** |
| hard starved 8 KiB + 1 byte | 34.048 us | 23.772 us | **0.699363x** | **30.1%** |

The fused loop reduces explicit source scans from **2 to 1** while preserving the fixed signal and epoch-min signal exactly. Fixed scalar state is 32 B; epoch signal state remains 2,088 B.

## Causal interpretation

Duplicate source traversal is a real D2 execution cost: fusing the two cheap signals removes roughly 30–32% of native signal-generation elapsed across all tested regimes, including the hard rescue case. This is materially larger than timer noise and survives exact trace equality.

The result supports ONE's fused-observation design principle. It does not show that the entire discovery system will improve by the same amount once bounded indexes, exact proof, extension and Law compilation are in the native loop.

## Hostile review / relationship to the edited-version negative

A later exact-head structural-transfer experiment found one internally edited temporal/versioned row where scalar epoch-min misses **1,008 B** of mature-minimizer opportunity. That negative has higher priority for selector replacement than this speed win.

Therefore this receipt does **not** authorize replacing the mature selector with epoch-min. The fused-loop implementation remains useful infrastructure and causal evidence: if the missing predictive relationship can be absorbed into a bounded sufficient statistic, it should be integrated into this one-pass shape rather than reviving a second discovery pass or a reader-visible mechanism zoo.

No stored-byte, product-speed, reader/wire, v0.29/v0.30 superiority, release, integrity, recovery or portability authority is created.

## Terminal decision

**Preserve the one-pass fusion result, but pause promotion work until the 1,008-byte edited-version loss is causally localized.**
