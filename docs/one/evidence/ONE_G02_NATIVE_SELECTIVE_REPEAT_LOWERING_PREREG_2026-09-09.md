# ONE-G0.2 native selective Repeat lowering — preregistration

Date: 2026-09-09  
Status: frozen before result-bearing execution

## Mission lock

`repeat` is one of the six existing ONE relations, but the promoted native selective cone lowering currently accepts `surprise`, `fill`, `add8`, `xor`, and `concat` topology and rejects `repeat` as unsupported. The generic authenticated range evaluator already reconstructs Repeat selectively.

The next question is whether Repeat can compile into the same existing native COPY/FILL/ADD8/XOR terminal schedule without a Repeat-specific reader opcode, whole-root expansion, or source-size-scaling work.

## Hypothesis

A requested interval of a Repeat node can be lowered by modularly mapping only that interval onto the repeated child Ref and recursively compiling those child slices. For a fixed requested authenticated cone, source traffic and temporary state should depend on the cone and basis width, not on the total repeated-root length.

## Comparator / candidate

Both arms first use the same `ValidatedProgram` authority and the same `AuthTree` commitment.

Comparator: `reconstruct_validated_authenticated_range(...)` using the generic Python `RangeEvaluator`.

Candidate: the existing `reconstruct_validated_authenticated_native_range(...)` after adding generic Repeat topology lowering to `native_law_range_plan.py`.

The candidate may emit several existing terminal commands when a requested interval crosses repeat periods. It may not add a reader-visible Repeat command or materialize the whole repeated node.

## Frozen matrix

Repeat bases: 32 B, 64 B, 256 B, and 4 KiB.  
Root lengths: 32 KiB, 128 KiB, 512 KiB.  
Authenticated leaf: 4 KiB.  
Requests per root:

- first 64 B;
- first 4 KiB;
- a 4 KiB request beginning one byte before a repeat-period boundary;
- a middle 8 KiB request;
- final 257 B.

Each basis is deterministic non-constant Surprise bytes. Root lengths are exact multiples of the basis for the frozen matrix.

## Hard gates

1. exact candidate/comparator/reference byte parity on every row;
2. exact authentication against the same root commitment on every row;
3. no whole-root reconstruction/hash shortcut;
4. candidate cone bytes remain Merkle-leaf aligned and equal comparator cone geometry;
5. for a fixed 4 KiB request and fixed basis, candidate packed source/read/write bytes do not grow as root length grows 32 KiB -> 128 KiB -> 512 KiB;
6. candidate peak temporary bytes remain <= 3x authenticated cone bytes + proof hashes;
7. inherited malformed/resource/authentication tests remain fail-closed.

## Economic gates

Promotion requires all hard gates plus:

- median candidate/comparator CPU <= **0.75x**;
- worst candidate/comparator CPU <= **1.10x**;
- median candidate modeled movement / comparator range-work+proof movement <= **1.00x**;
- command count is bounded by `ceil(cone_bytes / basis_bytes) + 2` for the direct Surprise-basis cases.

The thresholds are fixed before hosted execution.

## Interpretation

`ADVANCE_NATIVE_SELECTIVE_REPEAT_LOWERING` means Repeat joins the same native generic cone execution surface without adding a mechanism-specific reader format.

`HOLD_NATIVE_SELECTIVE_REPEAT_LOWERING` means semantics are exact but the tested lowering is economically poor; preserve the result and attack command coalescing or repeated-source reuse rather than special-casing corpus names.

Any semantic/authentication/resource mismatch is `INVALIDATE_NATIVE_SELECTIVE_REPEAT_LOWERING`.
