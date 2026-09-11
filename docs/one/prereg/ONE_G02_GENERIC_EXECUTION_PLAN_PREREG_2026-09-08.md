# ONE-G0.2 Generic Execution Plan — preregistration

## Mission lock

The terminal-specific optimization line is closed by `HOLD_NATIVE_MIXED_TERMINAL_PLAN`. The next question must be general: can the existing six-operation ONE graph be validated and range-resolved once, then replayed as a deterministic topological plan without re-walking the graph or rediscovering slice geometry on every read?

This experiment changes execution only. Stored ONE grammar remains exactly `surprise`, `concat`, `repeat`, `fill`, `xor`, `add8`; no historical codec/mechanism or run-specific opcode is introduced.

## Falsifiable hypothesis

Across multiple Law shapes—not merely Fill/long-runs—compile-once generic replay will preserve exact outputs/work accounting while reducing repeated Python graph-control cost enough to be at least non-regressive at 1 MiB and materially faster on a broad subset of the 18-cell matrix.

## Frozen matrix

Sizes: 64 KiB, 256 KiB, 1 MiB.

Families: terminal Surprise+Fill+Concat, Repeat, sliced multi-parent Concat, two-parent XOR, three-parent add8, and shared-basis Repeat+Fill+Concat.

Nine paired repetitions per cell with alternating arm order. Compilation is timed separately and is never gifted into the replay claim.

## Decision law

`INVALIDATE_GENERIC_EXECUTION_PLAN` if semantics/work accounting disagree or the exact 18-cell matrix is incomplete.

`ADVANCE_GENERIC_EXECUTION_PLAN` only if all six 1 MiB rows are <=1.05x the reference evaluator on both median wall and CPU time, and at least 8/18 rows are <=0.95x on both.

Otherwise `HOLD_GENERIC_EXECUTION_PLAN`.

Compile break-even is reported per row when replay is faster. A green replay result does not imply one-shot cold-read superiority.

## Claim boundary

This is full-root hosted-Python execution evidence. It does not claim product-native throughput, selective-range amplification, RSS improvement, wire/index changes, recovery changes, or a canonical execution-plan format. A plan is reader-internal derived state; the reader still performs no discovery.

## Retirement rule

If the generic plan only benefits terminal/run-shaped workloads, or if 1 MiB XOR/add8/reuse composition regresses beyond 1.05x, do not add workload dispatch to manufacture a win. Preserve the negative and move to a more general bulk/dataflow execution boundary or higher-level reconstruction-cost model.