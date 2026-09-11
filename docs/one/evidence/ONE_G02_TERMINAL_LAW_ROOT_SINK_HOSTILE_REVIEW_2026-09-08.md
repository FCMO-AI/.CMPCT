# ONE-G0.2 terminal Law root-sink hostile review — 2026-09-08

Status: **pre-result review**. No admissible hosted result from the dedicated root-sink lane has been consumed while writing this receipt.

## Mission-lock check

The candidate does not alter the stored Program, wire grammar, Fill semantics, root commitments, limits, or discovery boundary. It is a reader execution strategy for existing terminal `surprise`/`fill` children under a root `concat`. Unsupported graph shapes fail closed.

## Attacks and dispositions

1. **Fake work reduction by changing accounting.** Both literal control and run-Fill candidate use the same fused evaluator and the same modeled traffic definition. The old reference evaluator's `work_bytes` is retained separately and is not rewritten retroactively.
2. **Hidden terminal materialization.** Fill writes directly into the allocated root sink with `ctypes.memset`. Hostile review then found that the first root-sink implementation used `node.surprise[start:end]`, which creates a payload-sized Python bytes slice not represented in modeled traffic. This was repaired before accepting any hosted verdict: Surprise now writes through a `memoryview` slice, avoiding the hidden payload copy. Any root-sink performance/traffic result from source SHA `f6f96ef19d340c17f7944e9eb3281a8210746309` or earlier is therefore **inadmissible for promotion**, even if its workflow later completes green.
3. **Gifted preprocessing.** Programs are built before reader timing for both arms because the falsified question is reader execution of the same stored graph. No reconstructed bytes or hashes are precomputed outside the timed evaluator call.
4. **Root integrity weakened.** Every reconstructed root is independently SHA-256 checked against the Program commitment after generic preflight. Tampered-root tests must fail.
5. **Resource bounds bypassed.** The candidate runs the existing generic `_preflight()` before materialization, preserving unchanged node/depth/output/work bounds. This dependence on a private research helper is acceptable only for this semantic experiment; promotion would need a stable shared preflight surface.
6. **Python/ctypes portability inflated into format authority.** `ctypes.memset` is research implementation machinery. A green result does not make ctypes, libc layout, or this Python reader canonical.
7. **Selective-read claim laundering.** This experiment reconstructs complete roots. It may rehabilitate full-root memory traffic and execution time only. Selective-range amplification remains unproven and must receive a separate range-sink experiment.
8. **Too many tiny Fill calls.** The 1 MiB `long_runs` case has 220 Fill spans, so repeated ctypes boundaries can still defeat the 1.05 timing gate. That is a legitimate HOLD: it would motivate one native bulk schedule only after semantic/traffic equivalence is demonstrated, not a relaxed threshold.
9. **Control accidentally disadvantaged.** Literal control also flows through the root sink and pays stored Surprise read, sink write, root hash scan, and immutable-output freeze. No candidate-only exemption is present.
10. **Density win hides reader complexity.** The prior `0.501x` long-run wire win is not sufficient. Traffic, temporary memory, semantic, root, and timing gates remain mandatory.

## Frozen interpretation

- Green traffic + semantics but red timing means **semantic Law fusion is valid but Python per-piece dispatch is still too expensive**; the next allowed step is a preregistered native bulk sink over the same graph.
- Red traffic means the proposed fusion does not actually solve the prior `4/3` access/work problem and the direct run-Fill line remains HOLD.
- Semantic/root failure invalidates the candidate regardless of speed or density.

No v0.29/v0.30 or Genesis supersession claim is authorized by this experiment.