# ONE-G0.2 relation root fusion — preregistration

Date: 2026-09-08
Branch authority: `research/cmpct1`
Research version: ONE-G0.2

## Mission lock / referee

The exact relation-granularity frontier demonstrated density in the existing generic grammar but exposed a 2.333x reader-work / 2.5x materialization penalty. The next causal question is whether that penalty belongs to the stored representation or to materializing every intermediate graph value and recopied root Concat.

## Frozen hypothesis

Without changing one stored Program byte, operation, root, node limit, integrity rule or resource setting, direct execution of root `concat` children and generic `add8/xor(Surprise, Fill(constant))` cones into one bounded root sink will materially reduce work/materialization and recover most of the execution deficit.

The fusion receives an already-authoritative Program, runs the ordinary complete preflight, executes only a narrowly proven root geometry, and fails closed otherwise. It performs no discovery and adds no reader-visible opcode.

## Frozen matrix

- sizes: 64 KiB, 256 KiB, 1 MiB;
- relation spans: 512, 1024, 2048, 4096 bytes;
- existing relation ops: add8 and xor;
- exact 24 cells;
- 11 median wall/CPU repetitions after warmup;
- reference evaluator remains the semantic oracle;
- current native prepared-plan reader remains the execution comparator.

## Promotion law

Any semantic/root mismatch, Program mutation, duplicate/missing matrix cell or malformed accounting invalidates.

For both decisive 1 MiB / 4096-byte rows, all must hold:

- fused modeled work / literal reference work <= 1.50;
- fused materialized bytes / literal materialized bytes <= 1.10;
- fused median wall and CPU / literal <= 1.50;
- fused median wall and CPU / current native prepared reader <= 0.50.

Passing yields `ADVANCE_RELATION_ROOT_FUSION`, scoped only to execution geometry. It does **not** make relation Laws canonical. Literal-parity remains a stronger diagnostic target at <=1.05x wall+CPU.

## Resource/accounting rule

The fused model charges stored source reads, final sink writes, one byte of relation arithmetic per derived byte, and two root-length charges matching the reference root range/hash accounting. The root sink is materialized; a translated relation block is bounded transient state and included in peak temporary bytes. Full Fill operands and full relation child values are not charged as retained materialization because this execution never constructs them.

## Disproof interpretation

- If work/materialization do not fall: graph fusion does not address the causal geometry; keep relation evidence density-only.
- If work falls but wall/CPU remains poor: the representation principle survives, but this Python execution boundary is not a system solution. Do not relax thresholds or add a relation codec.
- If the fused path beats current native replay but remains >1.05x literal: preserve the scoped execution advance and continue only with a general reconstruction compiler if the same technique can serve multiple Law shapes.
- If <=1.05x literal on both decisive rows: record system-ready timing evidence, still without changing canonical format authority.
