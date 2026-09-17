# R40 dynamic worker-pull resource result

Decision: **RESOURCE_GATE_PASSES — independently replicated**.

Evidence head: `208d0f989e5e652fc800fc8daf3c2b1bfc3e1606`  
GitHub Actions run: `35225768762`  
Original result-bearing job: `105216836236`; artifact id `10498909932`, zip SHA-256 `dd3371030fce117e4bfc77ce02dec4d2e3936b609f839b77a1d16c4b87a158b1`.  
Independent rerun job: `105217756421`; artifact id `10497834679`, zip SHA-256 `b28bdd2d95b4550fb36db89cc883549cfeaf28726567e7ac3d9be15c5124b7da`.  
Environment: GitHub hosted `ubuntu-24.04`, image `20260907.300.1`, CPython `3.11.16`.

The earlier green run `35225496249` is explicitly **not evidence**: its first classifier inspected GitHub's PR merge checkout and skipped all result-bearing steps. Run `35225768762` fixed custody by checking out and asserting the exact PR head before classification and measurement.

## Frozen-gate measurements — original execution

Seven independent subprocess repetitions per arm per target, alternating arm order, 8 workers, frozen R34/R36 sources, reproducible mode.

| target | archive identity | baseline wall median | dynamic wall median | wall saved | CPU ratio | RSS ratio |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| full-backups | yes | 0.559864 s | 0.554103 s | **5.760 ms (1.03%)** | **0.994515x** | **1.000081x** |
| nested-only | yes | 0.467824 s | 0.459557 s | **8.267 ms (1.77%)** | **0.992348x** | **0.995639x** |

Frozen pass bounds were: exact archive identity on every repetition; >=2 ms median wall saving; <=1.03x process-tree CPU; <=1.05x conservative process-tree peak RSS on both targets. Every bound passed.

## Independent identical rerun

The exact same frozen job was rerun before productization. It again emitted `RESOURCE_GATE_PASSES` with exact archive identity:

| target | baseline wall median | dynamic wall median | wall saved | CPU ratio | RSS ratio |
| --- | ---: | ---: | ---: | ---: | ---: |
| full-backups | 0.570958 s | 0.555892 s | **15.067 ms (2.64%)** | **0.996323x** | **1.000805x** |
| nested-only | 0.476839 s | 0.466351 s | **10.488 ms (2.20%)** | **0.991689x** | **0.992187x** |

The rerun strengthened rather than merely repeated the wall result, while CPU again did not regress and RSS remained effectively flat/better. The variability in absolute wall gain confirms runner sensitivity, so product validation must measure the real patch rather than inherit the research percentage.

## Claim boundary

This is new research/productization evidence for the R39 dynamic worker-pull mechanism, not release credit and not a product-state mutation. It establishes twice that the R39 wall-time gain survived the frozen CPU/RSS exported-cost gate with exact archive bytes on these two targets. It does **not** establish unmeasured temporary-I/O behavior, cross-platform performance, or canonical release-matrix success.

The next authorized step is the minimal Builder-local product patch: claim indices directly from Builder's existing canonical `ordered` list, submit only `min(W,N)` long-lived worker futures, keep `_encode_candidate` outside the claim lock, write results by canonical index, preserve the one-worker path, and avoid the research monkeypatch's extra `list(zip(...))` materialization. Then attack that real patch with direct edge/exception/determinism tests and broader canonical runtime/resource validation before any product credit.
