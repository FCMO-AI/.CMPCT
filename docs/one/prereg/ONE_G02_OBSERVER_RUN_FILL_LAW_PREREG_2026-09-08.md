# ONE-G0.2 observer-run → generic fill-Law compiler preregistration — 2026-09-08

## Mission lock / referee

The native observer now has a preferred transient handoff shape: empty for zero opportunities, one inline scalar slot for exactly one opportunity, and exact used-prefix packed bytes for larger outputs. Exact-source result `b04cbb84b325fc8690634a3a3e145a1cd22cf2cc` advanced that handoff without changing ONE bytes or reader semantics.

That work also exposes a larger systems problem: in rejected temporal roots the research writer charges native observation and then commonly emits the current root as literal Surprise. In particular, `long_runs` is already discovered as maximal constant runs, while ONE already has the generic reader-visible relation `fill`. Continuing to optimize a transient observation representation without compiling discovered predictive structure into Law would optimize dead bookkeeping instead of information yield.

This experiment asks whether existing maximal-run evidence can compile directly into the same bounded ONE grammar and reduce stored Surprise materially without a new reader mode.

## Candidate principle

Compile qualifying maximal constant runs discovered by the existing observer into ordinary ONE `fill` nodes. Preserve all non-run bytes as ordinary Surprise and join pieces with ordinary `concat`.

This is **not** a run-length codec opcode. The reader sees only the existing generic relations:

- `surprise`
- `fill`
- `concat`

No legacy format, hidden subcodec, or reader-side discovery is allowed.

### Economic qualification

Do not encode every 8-byte observer run merely because it exists. A run is eligible for the first compiler experiment only when `length >= 32` bytes.

The 32-byte floor is frozen before results as a conservative representation-cost bound, not a timing crossover or source-size dispatcher: under the current ONE0 node/ref/uvarint grammar, a 32-byte constant span is comfortably larger than the bounded per-piece fill + concat-reference control needed to replace literal bytes. No source-length condition is allowed.

The experiment must report the exact wire delta of every admitted fill span. If the bound proves wrong on any row, the candidate holds; do not move the threshold after seeing the matrix.

### Bounded construction

- Node 0 remains the exact previous-root Surprise used by the current pair writer.
- Qualifying runs are ordered, non-overlapping, and checked against an independent Python maximal-run oracle.
- Gaps remain Surprise.
- Qualifying runs become `fill(value, count)`.
- Pieces are joined only through ordinary bounded `concat`.
- If the generic node/ref cap cannot represent the candidate without Crystallization, the experiment must record that as boundedness debt rather than silently increasing limits.
- No secondary stored fallback syntax is introduced. Literal Surprise remains part of the same ONE grammar and is the control representation.

## Falsifiable hypothesis

The observer is discovering useful Law structure that the current rejected-root writer leaves on the floor.

If that is true, compiling maximal constant runs into generic `fill` should materially reduce current-root Surprise/wire bytes on run-rich inputs while leaving no-opportunity/compressed/random controls exact and bounded. The creation-cost premium must be small enough that bits eliminated per additional CPU time remains favorable.

Disproof:

- any semantic mismatch;
- any hidden source-size or family selector required to avoid a red row;
- any wire-byte regression on a control caused by the compiler;
- failure to deliver material density reduction on the frozen run-rich rows;
- node/resource blow-up that merely trades bytes for an unsafe reader graph;
- creation cost so high that the mechanism loses the project's density+compute-efficiency objective.

A negative is preserved; do not rescue the candidate by adding a portfolio of run-length bands or bespoke reader operations.

## Frozen matrix

Sizes:

- 64 KiB
- 256 KiB
- 1 MiB

Families use the existing deterministic observer generators:

- `structured`
- `long_runs`
- `compressed_like`
- `random`
- `near_repeats`

The previous root remains an unrelated deterministic source of the same length so this experiment measures current-root intra-object Law discovery rather than temporal reuse.

Each arm must pay the same native observation scan. The control discards run evidence and emits the current root as literal Surprise. The candidate consumes only qualifying run records into generic fill/concat Law.

## Independent oracle / hard semantic gates

For every row:

1. independently scan the target in Python for maximal constant runs and require equality with the native observer for all qualifying `>=32` spans;
2. validate Program shape under unchanged `Limits`;
3. encode/decode through the independent ONE0 reader;
4. reconstruct exact previous and current bytes;
5. verify both root SHA-256 identities;
6. require only `{surprise, fill, concat}` in the candidate current-root cone;
7. preserve unchanged reader caps;
8. record node count, concat refs, hierarchy depth, Surprise bytes, total wire bytes, reader work/materialization and creation wall/CPU.

Any semantic/resource disagreement is `INVALIDATE_OBSERVER_RUN_FILL_LAW`.

## Frozen density gates

At 1 MiB:

- `long_runs`: candidate/control total wire bytes <= **0.55x**;
- `structured`: candidate/control total wire bytes <= **0.90x**.

Across all 15 rows:

- candidate total wire bytes must never exceed control;
- candidate Surprise bytes must never exceed control;
- `compressed_like`, `random`, and `near_repeats` may remain literal/no-op, but may not be made larger merely to claim generality.

These are pair-container wire ratios: the unchanged previous root is charged in both arms, so the gate does not hide that only the current root is being improved.

## Frozen compute/resource gates

Use fresh-row subprocess timing with paired alternating repetitions after warmup.

- no run-rich row may exceed **1.10x** control on both median wall and CPU creation time;
- no control row may exceed **1.05x** control on either wall or CPU;
- reader work/materialization may not exceed control by more than **1.05x** on any row;
- Program node count and concat fanout remain within existing hard limits;
- report bytes eliminated per millisecond and bytes eliminated per added CPU millisecond where the candidate costs more CPU.

A density win that buys bytes by exploding writer or reader work does not advance.

## Decisions

- `ADVANCE_OBSERVER_RUN_FILL_LAW` only if all semantic, density, compute and resource gates pass.
- `HOLD_OBSERVER_RUN_FILL_LAW` if semantics are exact but any frozen economic gate fails.
- `INVALIDATE_OBSERVER_RUN_FILL_LAW` on semantic, oracle, root, reconstruction, or hard-resource disagreement.

## Hostile review / claim boundary

- This experiment compiles one already-discovered predictive structure into ONE; it does not prove arbitrary Law discovery.
- It earns no authenticated-placement, recovery, filesystem, portability, v0.29, deferred-v0.30, or Genesis supersession authority.
- It must not add a run-specific reader operation: `fill` and `concat` are already canonical research-IR relations.
- The 32-byte eligibility floor is frozen before result consumption and may not be tuned from this matrix.
- Do not count the observer scan as free. Both candidate and control pay it.
- A pass would be a representation/compiler result, not merely an observer-handoff speed result, because it must reduce canonical ONE0 bytes while preserving the same reader grammar.
