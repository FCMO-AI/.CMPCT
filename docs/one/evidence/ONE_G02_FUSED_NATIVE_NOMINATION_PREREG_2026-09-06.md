# ONE-G0.2 fused native nomination — preregistration

Date: 2026-09-06
Experimental line: `ONE-G0.2`
Authoritative branch: `research/cmpct1`
Status: frozen before result-bearing execution

## Mission Lock

The native nomination event consumer exactly reproduces the reference pair-nomination semantics, but it intentionally consumes an intermediate native anchor trace in a second full byte pass. ONE's speed/efficiency law prefers one fused observation pass and reusable state.

The promoted minimizer kernel already has the exact `(selected_value, selected_position)` pair at the moment a new rightmost-min anchor is emitted. That is precisely the global nomination signal currently reconstructed later from the trace. The local fixed-window signal is also the current Gear state already present in the same loop.

This Builder therefore fuses the already-proven event/index consumer into the native minimizer observation pass. It must not change selector semantics, nomination policy, exact witness proof, or reader representation.

## Baseline / independent oracle

Semantic oracle is the now-terminal two-stage path:

1. `one_g02_minimizer_offset_only_kernel.c` emits the native anchor trace;
2. `one_g02_native_nomination_event_consumer_kernel.c` consumes that trace.

That two-stage path already agrees exactly with the independent Python rightmost-min and pair-nomination reference over the frozen 90-row envelope.

## Falsifiable hypothesis

The native minimizer's already-live Gear/run/argmin state contains all information needed to consume local and global nomination events in the same pass. A fused implementation can therefore reproduce the exact two-stage result while eliminating one complete scan of the combined prior+current bytes and eliminating the intermediate anchor trace from the candidate path.

### Disproof

Reject or repair if any frozen row has:

- selector anchor-count/final-state mismatch;
- cross-audition or cross-exact mismatch against the two-stage native oracle;
- false exact nomination;
- different `covered_until` consequences observable through nomination counts;
- local/global index bound violation;
- a second source scan hidden inside the fused candidate;
- reader-visible ONE changes.

## Frozen envelope

Same 90 rows as the terminal event-consumer result:

- sizes: 4, 8, 16, 64, 256 KiB;
- seeds: 7, 29, 53;
- cases: `shift_plus1`, `damage_quarter`, `fragmented_every96`, `hostile_fixed_bands`, `fragmented_every32`, `independent_random`.

Persist per row:

- baseline/fused anchor count and final Gear state;
- baseline/fused cross auditions and exact nominations;
- fused local/global peak index entries;
- verification and extension read bytes;
- modeled sequential source bytes scanned by selector/event machinery;
- whether an intermediate trace is required by each arm.

## Resource / traffic law

The semantic two-stage baseline scans the combined input once in the selector and once in the event consumer: modeled sequential observation traffic = `2 * len(data)` before exact proof reads.

The fused candidate may scan the combined input only once: modeled sequential observation traffic = `len(data)`. Exact witness/extension proof reads are charged separately and must remain semantically identical.

The candidate may not claim that eliminating the trace eliminates the selector's existing bounded minimizer state; only the trace buffer and second sequential scan are removable in this experiment.

## Promotion law

Advance iff:

- all semantic/hostile ONE tests pass;
- all 90 rows match the two-stage native oracle on selector and nomination outcomes;
- zero false exact nominations;
- candidate modeled sequential observation traffic is exactly **0.5x** the two-stage baseline on every row;
- candidate requires no intermediate anchor trace for nomination;
- no new reader-visible operation or weakened resource bound is introduced.

No elapsed-time threshold is frozen yet. First establish exact one-pass fusion and traffic removal. A subsequent paired native timing gate may decide whether the extra in-loop event/index work is economically acceptable against the promoted observer.

## Decisions

- `advance_fused_native_nomination_semantics` — exact one-pass fusion passes every frozen gate;
- `repair_fused_native_nomination` — semantic/resource disagreement;
- `retire_fused_native_nomination_shape` — only if exact fusion forces unreasonable state/complexity.

## Hostile Reviewer

A one-pass implementation can still be slower if it injects expensive irregular index work into the minimizer hot loop. Passing this experiment therefore proves **work/traffic fusion**, not elapsed-time superiority. The next gate must compare elapsed native carrying cost on nominated and negative regimes before integrated safe-relation dispatch is promoted.
