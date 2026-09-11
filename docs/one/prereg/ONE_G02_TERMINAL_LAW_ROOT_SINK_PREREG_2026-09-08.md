# ONE-G0.2 terminal Law root-sink rehabilitation preregistration — 2026-09-08

## Mission Lock / Referee

The exact-source observer-run compiler at `bf676f0615de0e38ffe60911bf97d667029da8c2` produced a useful density signal but `HOLD_OBSERVER_RUN_FILL_LAW`: on every row that actually compiled Fill, the reference evaluator reported `1.333333x` control reader work. The 1 MiB long-runs row reached `0.501019x` wire but `1.110941x` wall / `1.111013x` CPU and `1.333333x` reader work.

The candidate graph is already valid ONE: terminal `surprise`/`fill` pieces feeding ordinary `concat`. The reference evaluator materializes each child, rereads every child into `concat`, writes the concatenated root, then reads/hashes the root. That execution shape adds an avoidable complete pass over the current root.

## Falsifiable hypothesis

A reader can execute the **same stored Program and same reader-visible grammar** by sending terminal `surprise`/`fill` pieces directly into one bounded current-root sink. This should preserve exact reconstruction and root authentication while removing intermediate child materialization and the extra child->concat memory pass.

This is Law fusion, not a new opcode. The stored wire, Program nodes, root hashes, Surprise bytes, Fill spans, dependency depth, node/ref limits and discovery boundary remain unchanged.

## Independent semantic oracle

The existing `experiments.one.vm.evaluate()` remains authoritative semantic oracle. A research fused reader must:

1. call `Program.validate_shape()` and fail closed on unsupported graph shapes;
2. accept only a full-root `concat` whose referenced children are terminal `surprise` or `fill` nodes with valid ranges, plus direct terminal roots;
3. reconstruct `previous` and `current` byte-for-byte equal to the reference evaluator;
4. independently SHA-256 every reconstructed root and require equality with the stored root commitment;
5. preserve unchanged `Limits` and reject overflow/range/depth violations before output materialization;
6. never perform discovery in the reader.

Unsupported shapes must fall outside this experiment rather than silently changing semantics.

## Frozen matrix

Reuse exactly the observer-run compiler families and sizes:

- sizes: 64 KiB, 256 KiB, 1 MiB;
- families: `structured`, `compressed_like`, `long_runs`, `random`, `near_repeats`;
- compiler: existing `program_from_observed_runs()` with `MIN_FILL_RUN=32`;
- semantic oracle: reference `evaluate()` over canonical encode/decode round-trip.

Both literal control and run-Fill candidate are evaluated through the fused reader when their graph is supported, so the experiment cannot gift the candidate a special work definition.

## Traffic accounting

Record separately:

- bytes read from stored Surprise payloads;
- bytes written to reconstructed root sinks;
- bytes scanned for root SHA-256;
- temporary materialized bytes beyond final root outputs;
- total modeled memory traffic = the sum above.

Fill generation has no stored payload read; its emitted bytes count as root-sink writes. A direct terminal Surprise root reads stored bytes and writes the requested root sink before authentication. No child materialization may be hidden outside accounting.

The old reference `EvaluationStats.work_bytes` remains reported for comparison but is not redefined.

## Performance / access decision

For every row:

- fused outputs and root hashes must equal the independent reference evaluator exactly;
- candidate wire must never exceed literal control wire;
- candidate fused modeled traffic must be `<=1.05x` fused literal-control traffic;
- candidate fused temporary bytes beyond final root outputs must be `<=1.05x` control;
- controls with no qualifying Fill must remain `<=1.05x` control wall and CPU in a paired fused-reader timing.

At 1 MiB:

- `long_runs` wire must remain `<=0.55x` control;
- `structured` wire must remain `<=0.90x` control;
- `long_runs` fused-reader wall and CPU must be `<=1.05x` the fused literal control;
- `structured` fused-reader wall and CPU must be `<=1.05x` control.

Decision:

- any semantic/root/limit mismatch -> `INVALIDATE_TERMINAL_LAW_ROOT_SINK`;
- any traffic, density or timing gate miss -> `HOLD_TERMINAL_LAW_ROOT_SINK`;
- only a complete matrix passing all gates -> `ADVANCE_TERMINAL_LAW_ROOT_SINK`.

## Hostile-review constraints frozen before implementation

- Do not alter `MIN_FILL_RUN`, family generators, source sizes, wire grammar, root authentication, `Limits`, or the prior compiler's density thresholds after seeing results.
- Do not precompute reconstructed bytes outside the timed reader.
- Do not claim selective-read improvement from a full-root benchmark. A green result only rehabilitates full-root reconstruction traffic and creation/reader execution economics; selective range fusion requires its own experiment.
- Do not add a Fill-specific reader opcode or opaque fast path. The candidate is an execution strategy over existing generic nodes.
- Do not claim Genesis comparator progress: this experiment does not compare v0.29/v0.30 or the 15-workload contract.