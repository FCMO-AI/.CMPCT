# R40 dynamic worker-pull resource result

Decision: **RESOURCE_GATE_PASSES**.

Evidence head: `208d0f989e5e652fc800fc8daf3c2b1bfc3e1606`  
GitHub Actions run: `35225768762`  
Artifact: `v030-r40-dynamic-pull-resource-208d0f989e5e652fc800fc8daf3c2b1bfc3e1606` (artifact id `10498909932`, zip SHA-256 `dd3371030fce117e4bfc77ce02dec4d2e3936b609f839b77a1d16c4b87a158b1`).  
Environment: GitHub hosted `ubuntu-24.04`, image `20260907.300.1`, CPython `3.11.16`.

The earlier green run `35225496249` is explicitly **not evidence**: its first classifier inspected GitHub's PR merge checkout and skipped all result-bearing steps. Run `35225768762` fixed custody by checking out and asserting the exact PR head before classification and measurement.

## Frozen-gate measurements

Seven independent subprocess repetitions per arm per target, alternating arm order, 8 workers, frozen R34/R36 sources, reproducible mode.

| target | archive identity | baseline wall median | dynamic wall median | wall saved | baseline CPU median | dynamic CPU median | CPU ratio | baseline peak RSS | dynamic peak RSS | RSS ratio |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| full-backups | yes | 0.559863701 s | 0.554103458 s | **5.760243 ms** | 1.137448 s | 1.131209 s | **0.994515x** | 99,348 KiB | 99,356 KiB | **1.000081x** |
| nested-only | yes | 0.467823992 s | 0.459556551 s | **8.267441 ms** | 0.932482 s | 0.925347 s | **0.992348x** | 44,024 KiB | 43,832 KiB | **0.995639x** |

Frozen pass bounds were: exact archive identity on every repetition; >=2 ms median wall saving; <=1.03x process-tree CPU; <=1.05x conservative process-tree peak RSS on both targets. Every bound passed.

Relative wall improvement is about **1.03%** on full-backups and **1.77%** on nested-only. CPU did not regress in this execution; medians improved about **0.55%** and **0.77%** respectively. Peak RSS was effectively flat on full-backups (+8 KiB median, +0.008%) and lower by 192 KiB (-0.44%) on nested-only.

## Claim boundary

This is new research/productization evidence for the R39 dynamic worker-pull mechanism, not release credit and not a product-state mutation. It establishes that the measured R39 wall-time gain survived the frozen CPU/RSS exported-cost gate with exact archive bytes on these two targets. It does **not** establish unmeasured temporary-I/O behavior, cross-platform performance, or canonical release-matrix success.

The next authorized step is the minimal Builder-local product patch: claim indices directly from Builder's existing canonical `ordered` list, submit only `min(W,N)` long-lived worker futures, keep `_encode_candidate` outside the claim lock, write results by canonical index, preserve the one-worker path, and avoid the research monkeypatch's extra `list(zip(...))` materialization. Then attack that real patch with direct edge/exception/determinism tests and broader canonical runtime/resource validation before any product credit.
