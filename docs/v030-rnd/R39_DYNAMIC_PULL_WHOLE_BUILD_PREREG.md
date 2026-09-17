# R39 — dynamic worker-pull whole-build gate

Status: FROZEN BEFORE RESULT.
Base authority: `94dd456ff508ae4e60ba9230bc071fdc9cc4708d`.

## Question
Does R38's transferable O(W) dynamic worker-pull gain survive complete, uninstrumented `Builder.build()` execution while preserving complete archive bytes?

## Arms
- baseline: shipping `ThreadPoolExecutor.map` scheduling;
- candidate: same Builder and same 8 workers, but `ThreadPoolExecutor.map` is replaced only for the duration of `Builder.build()` by R38's dynamic shared-index claim + canonical-index result vector.

No codec, representation, admission, source, worker count, archive layout, comparator, or release threshold may change.

## Frozen evidence
Use the frozen R34/R36 full-backups and nested-only source builders. Reproducible mode is mandatory so archive-byte identity is meaningful. Warm both arms, then run 9 alternating repetitions per target. Complete archive SHA-256 and byte count must be identical on every repetition.

## Decision
`WHOLE_BUILD_DYNAMIC_PULL_TRANSFERS` only if both targets preserve exact archive identity and candidate median complete-build time is at least 2 ms faster than baseline on each target. Otherwise `WHOLE_BUILD_DYNAMIC_PULL_DOES_NOT_TRANSFER`.

A positive result authorizes a minimal Builder product patch and broader CPU/RSS/I/O + runtime-matrix validation. It does not itself earn product or release credit. A negative result retires this scheduling-granularity family unless new causal evidence changes the mechanism.
