# R40 — dynamic worker-pull whole-system resource gate

Status: **FROZEN BEFORE RESULT**.

Base product authority: `94dd456ff508ae4e60ba9230bc071fdc9cc4708d`.
Mechanism authority: R39 `WHOLE_BUILD_DYNAMIC_PULL_TRANSFERS` with two independent executions preserving exact archive bytes.

## Question
Does R39's O(W) dynamic worker-pull scheduler retain its complete-build wall-time gain without exporting material cost into process CPU or peak RSS?

## Arms
- baseline: shipping `ThreadPoolExecutor.map` scheduling;
- candidate: exact R39 dynamic shared-index claim + canonical-index result vector, applied only during `Builder.build()`.

No codec, representation, admission, source, worker count, archive layout, comparator, or release threshold may change.

## Frozen evidence
Use frozen R34/R36 full-backups and nested-only source builders, reproducible mode, 8 workers, and **7 independent subprocess repetitions per arm per target**, alternating arm order. Each subprocess reports complete-build wall time, process CPU (`user + system`), peak RSS, archive bytes and SHA-256. Every baseline/candidate archive pair must be byte-identical. Summaries use medians.

## Decision
`RESOURCE_GATE_PASSES` only if on **both** targets: exact archive identity on every repetition; candidate median wall time is at least **2 ms faster**; candidate median process CPU is not more than **3% slower**; candidate median peak RSS is not more than **5% higher**. Otherwise emit `RESOURCE_GATE_FAILS`. Bounds are frozen before result and may not move afterward.

A pass authorizes the minimal Builder product patch plus canonical runtime/release-matrix validation. A fail narrows or retires productization according to measured exported cost; it does not erase R38/R39 mechanism evidence.
