# ONE-G0.2 hierarchy validation-span fusion result — 2026-09-06

Status: **terminal diagnostic FAIL; hierarchy micro-optimization line closed pending a causally different system-level need**.

## Authority

- Branch: `research/cmpct1`
- Result-bearing source: `097c6adf5f3271c65435c686782cd019f65d6f8b`
- Workflow: `ONE-G0.2 hierarchy validation-span fusion diagnostic`
- Run: `34075410915`
- Job: `101600419802`
- Preregistration: `docs/one/prereg/ONE_G02_HIERARCHY_VALIDATION_SPAN_FUSION_PREREG_2026-09-06.md`

## Hypothesis tested

The predecessor removed the full first-level hierarchy ref array but still reread every Segment length to compute each 4,096-item concat span. This follow-up captured those group spans during the already-required validation scan and charged that bookkeeping inside the timed candidate path.

## Frozen result

Hostile validation rejection parity: **PASS**. Canonical hierarchy semantic/byte parity: **PASS**.

| row | seed transient | candidate transient | elapsed ratio |
| --- | ---: | ---: | ---: |
| hier-4097-ref | 163,960 B | 96 B | 0.820026x |
| hier-4097-mixed | 163,960 B | 96 B | 0.771802x |
| hier-16384-ref | 655,520 B | 192 B | 0.808097x |
| hier-65536-mixed | 2,622,080 B | 768 B | 0.806863x |

Median validation+hierarchy-emission elapsed = **0.807480x**. Locked gate required `<=0.75x`; every row also had to remain `<=0.95x`, which they did. The median gate therefore fails decisively.

## Decision

**FAIL and close ordinary hierarchy micro-optimization work.** Do not lower the gate, add Surprise-rate dispatch, specialize around the 4,097 mixed row, or continue shaving bookkeeping from this isolated boundary merely because every row is faster than seed.

The two consecutive diagnostics establish a useful causal result:

1. full first-level derived-ref staging is wasteful and can be removed while preserving exact ONE bytes;
2. carrying group spans from mandatory validation does not materially deepen the speed gain once validation itself is charged;
3. the remaining local benefit is about a 19–20% class improvement on an uncommon hierarchy branch, not the stronger system-level breakthrough required to justify further Genesis attention.

The next research move should return to the broader native writer / ingest envelope where direct final-buffer emission already has stronger evidence and where eliminating whole representation boundaries can affect ordinary workloads. Reopen hierarchy-specific work only if a system-level profile later proves this branch is a dominant owner or if the representation changes so the entire hierarchy boundary can disappear.

## Hostile-review note

The candidate's nominal transient reduction remains enormous, but requested/staged bytes are not peak RSS evidence. No RSS claim is authorized by this diagnostic.
