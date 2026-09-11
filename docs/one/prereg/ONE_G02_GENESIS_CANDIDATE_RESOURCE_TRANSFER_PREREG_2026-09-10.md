# ONE-G0.2 Genesis candidate resource-transfer preregistration — 2026-09-10

**Mission Lock / Referee:** test whether the current ONE complete-archive surface can be measured reproducibly for creation, whole-read, and authenticated selective-read resource cost on an independent transfer tree, without touching the 15 Genesis workloads and without promoting the surface to the Genesis candidate.

## Falsifiable hypothesis

On a deterministic transfer-only tree that mixes tiny, structured, repeated, locally edited, pseudo-random, already-compressed, mode, directory, and symlink cases, five fresh-process repetitions of the current ONE product worker will:

- produce one deterministic complete persistent wire identity and size;
- reconstruct the complete source-tree semantics exactly;
- reconstruct an independently chosen regular member exactly through authenticated selective read;
- expose finite, non-negative CPU time, elapsed time, and peak RSS for every measured phase;
- keep transfer evidence marked non-production and keep comparisons, scoring, and winner selection false.

## Disproof tests

Return HOLD if any of the following occurs:

1. stored bytes or persistent wire SHA-256 changes across the five build samples;
2. any whole-read sample is not byte- and tree-semantics-exact;
3. any selective sample is not exact for the chosen member;
4. CPU, wall, or peak-RSS evidence is absent, negative, NaN, or infinite;
5. fewer than five fresh-process samples are retained for a measured phase;
6. a Genesis workload generator is imported or any of the frozen 15 trees is generated/read;
7. the result is marked production-eligible, compared, scored, or used to select a winner.

## Corpus boundary

The probe must build its own transfer tree directly. It must not import `one_genesis_gate_readiness`, `neutral_hostile`, `resemblance_hostile`, or their generators. The tree should include at least one symlink and non-default POSIX modes so the worker's new semantic checker is exercised rather than merely present.

## Metrics

Retain all five raw fresh-process samples and report medians plus min/max for CPU seconds, wall seconds, and peak RSS. Report complete stored bytes and persistent wire SHA-256. Selective product-specific access counters may be retained verbatim but are not normalized into a cross-contender metric here.

No performance threshold is preregistered: this experiment validates **observability and repeatability**, not superiority. Timing variation is evidence to preserve, not a reason to tune after observation.

## Decision vocabulary

- `ADVANCE_RESOURCE_OBSERVABILITY_ONLY`: all falsifiers pass. Candidate-boundary manifest remains HOLD.
- `HOLD_RESOURCE_OBSERVABILITY`: evidence is incomplete/noisy or a semantic/resource check fails.

Neither result certifies ONE for the Genesis gate and neither modifies v0.29/v0.30 or the frozen workload authority.
