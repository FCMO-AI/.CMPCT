# ONE-G0.2 native selective Repeat bulk rehabilitation — preregistration

Date: 2026-09-09  
Status: frozen before result-bearing execution

## Mission lock

`HOLD_NATIVE_SELECTIVE_REPEAT_LOWERING` proved that generic modular Repeat lowering is semantically correct and cone-proportional, but lowering one repeat period at a time into Python-built COPY commands is economically poor: 2.059911x median CPU, 2.455025x worst CPU, and 1.329897x median modeled movement versus the authenticated generic reader.

The causal owners are per-period Python command construction and the full-cone packed-source copy.

This rehabilitation changes neither ONE IR nor stored format. `repeat` remains the existing ordinary ONE relation. The candidate adds only an internal native bulk execution kernel for a *validated direct periodic source cone*: copy a requested periodic view of one Surprise basis directly into the final cone sink. There is no reader-visible Repeat opcode and no discovery.

## Falsifiable hypothesis

For direct `Repeat(Surprise)` cones, a validated periodic view can execute in bulk from the original immutable Surprise basis without constructing O(cone/basis) Python commands and without building a packed full-cone source copy.

If this is the real cost owner, authenticated selective CPU should beat the generic reader while modeled movement falls to parity or better. If it does not, native Repeat execution is not worth carrying and the generic evaluator remains the correct backend.

## Comparator / candidate

Both arms use the same compact `ValidatedProgram`, same `AuthTree`, same expected auth root, and same requested range.

Comparator: `reconstruct_validated_authenticated_range(...)`.

Candidate: `reconstruct_validated_authenticated_native_range(...)` after adding a direct periodic bulk plan for validated `Repeat(Surprise)` cones. All other supported ONE topology retains the existing schedule; unsupported topology remains fail-closed.

The periodic bulk plan must:

- borrow the immutable validated Surprise basis rather than copy it into a full-cone source plan;
- execute directly into the final cone sink;
- account one source byte read per emitted byte, one sink write per emitted byte, zero source-plan writes, and ordinary proof payload/hash movement;
- use bounded arithmetic from validated basis width / phase / requested length;
- preserve zero-count, count-one, empty-child, range, work, depth and authentication semantics through inherited validation.

## Frozen matrix

Retain the V1 matrix exactly:

- basis: 32 B, 64 B, 256 B, 4 KiB;
- roots: 32 KiB, 128 KiB, 512 KiB;
- auth leaf: 4 KiB;
- requests: first 64 B, first 4 KiB, period-crossing 4 KiB, middle 8 KiB, final 257 B;
- five paired warmed CPU rounds.

Add hostile semantic tests for zero-count Repeat, count-one Repeat, empty repeated source with zero-length output, non-empty request from an empty repeated source rejection, and a sliced Repeat Ref whose requested phase does not begin at period zero.

## Frozen gates

Hard gates:

1. exact candidate/comparator/reference bytes on every row;
2. exact authentication against the same commitment;
3. same authenticated cone geometry;
4. no whole-root reconstruction/hash shortcut;
5. fixed 4 KiB request traffic/state does not grow with unrelated root size 32 KiB -> 128 KiB -> 512 KiB;
6. direct periodic positive rows use **zero full-cone source-plan write bytes**;
7. direct periodic positive rows use **one bulk periodic execution descriptor**, not O(cone/basis) Python terminal commands;
8. peak temporary state <= 2x cone bytes + proof payload/hashes (the packed full-cone source allocation is gone);
9. inherited malformed/resource/authentication tests remain fail-closed.

Economic gates, unchanged in spirit from V1:

- median candidate/comparator CPU <= **0.75x**;
- worst candidate/comparator CPU <= **1.10x**;
- median candidate modeled movement/comparator movement <= **1.00x**.

No gate may move after execution.

## Interpretation

`ADVANCE_NATIVE_SELECTIVE_REPEAT_BULK` means the V1 failure was causally rehabilitated by removing its two measured physical stages. The bulk kernel is an execution implementation of the already-stored ONE Repeat relation, not a new representation mechanism.

`HOLD_NATIVE_SELECTIVE_REPEAT_BULK` means native Repeat is still economically inferior after those owners are removed; preserve generic Repeat as the preferred execution backend and stop spending research effort forcing this Law into native execution.

Any semantic/authentication/resource mismatch is `INVALIDATE_NATIVE_SELECTIVE_REPEAT_BULK`.
