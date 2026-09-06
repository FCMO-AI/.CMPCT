# ONE-G0.2 native segment SSE2-mask falsifier — preregistration

Date: 2026-09-06
Branch: `research/cmpct1`
Experimental line: `ONE-G0.2`

## Mission lock

Exact-source V2 writer attribution localized the native one-pass segment-plan constructor as the primary remaining measured writer owner: mature productive median phase share `35.1295%`, stable at roughly `34.27–35.47%` over 16–256 KiB.

The existing kernel classifies every target byte scalarly with the exact predicate:

`is_ref(i) := i > 0 && dst[i] == src[i-1]`

and emits maximal runs of equal predicate value as either source `Ref` or target `Surprise` segments.

## Falsifiable hypothesis

The exact same segmentation can be constructed materially faster on the x86-64 CI research target by evaluating 16 predicates at once with SSE2 byte comparisons, converting the equality vector to a 16-bit mask, and scanning run transitions from that mask instead of branching once per byte.

No segment boundary, start, length, kind or policy may change.

## Builder constraint

Candidate implementation:

- position `0` remains scalar Surprise by definition;
- positions `1..n-1` are compared as unaligned 16-byte vectors (`dst+i` versus `src+i-1`);
- `_mm_cmpeq_epi8` + `_mm_movemask_epi8` produces the exact Ref/SURPRISE predicate mask;
- runs may cross vector boundaries and must be merged exactly as the scalar baseline does;
- scalar tail handles fewer than 16 remaining bytes;
- output ABI and `one_g02_segment` layout remain unchanged;
- no approximate fingerprints, hashing or overreads are permitted.

This is an x86-64/SSE2 research kernel lane only. It does not authorize a product portability claim; a promoted implementation would require scalar fallback/runtime dispatch and platform evidence.

## Frozen semantic matrix

Use the authoritative temporal relation generator and include:

- `shift_plus1`;
- `shift_plus1_damage_quarter`;
- `fragmented_every96`;
- `fragmented_every32`;
- `independent_random`;
- additional transition-hostile alternating equality/no-equality input;
- exact lengths around SIMD/tail boundaries: 1, 2, 15, 16, 17, 31, 32, 33, 63, 64, 65;
- mature sizes 4/8/16/32/64/128/256 KiB.

For every row, scalar and SSE2 plans must be byte-for-byte identical over every emitted segment and segment count. Reconstruction from either plan must equal the target. Any mismatch invalidates the lane.

The semantic authority is three-way: scalar C, SSE2 C, and an independent Python oracle that directly emits maximal runs of the frozen `is_ref(i)` predicate. Both C arms must equal the Python oracle exactly before their timing data can count.

## Frozen performance gates

Native segment-kernel elapsed only, paired A/B–B/A with `CLOCK_MONOTONIC_RAW` inside C and enough batches to amortize call overhead.

Advance to integrated-writer testing only if all are true:

- semantic mismatches: `0`;
- mature productive median candidate/baseline `<=0.80x`;
- no mature productive row `>1.03x`;
- mature control median `<=1.00x`;
- no mature control row `>1.03x`;
- transition-hostile mature median `<=1.03x`.

A native-kernel win does **not** promote the writer. If it advances here, the exact same candidate must next be charged inside the plan-direct V2 writer and clear an independent integrated speed gate.

## Disproof

Reject this implementation if vector setup/mask-run handling consumes most of the theoretical gain, if dense transitions erase the advantage, or if exact plan identity fails. Do not rescue it with size/case thresholds after seeing results.

Workflow registration followed the Builder; this semantic-audit amendment was frozen before accepting any SSE2 timing result and also retriggers the exact-source lane.
