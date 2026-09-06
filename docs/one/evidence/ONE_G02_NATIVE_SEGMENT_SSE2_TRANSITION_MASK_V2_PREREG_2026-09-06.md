# ONE-G0.2 native segment SSE2 transition-mask V2 — preregistration

Date: 2026-09-06
Branch: `research/cmpct1`
Experimental line: `ONE-G0.2`

## Mission lock

The first SSE2 equality-mask candidate was rejected because its per-run mask decoder regressed the deliberately alternating every-byte hostile stream to `1.5518232542x`, even while mature productive rows improved to a `0.2169355752x` median. Preserve the bulk equality classification; remove the identified decoder tax without classifying workloads or sizes.

## Falsifiable hypothesis

An exact transition-bitset decoder can preserve the productive SIMD gain while eliminating the dense-transition regression.

For each 16-byte equality predicate mask `p` and incoming predicate bit `prev`, define exact transition positions as:

`transitions = p XOR (((p << 1) | prev) & 0xffff)`.

A set bit means the predicate toggles at that byte position, and therefore marks an exact maximal-run boundary. This representation lets the decoder reason directly about boundaries rather than repeatedly recomputing same-run length from shifted tail masks.

## Frozen Builder design

- Keep the exact SSE2 `_mm_cmpeq_epi8` + `_mm_movemask_epi8` classifier.
- Compute `transitions` exactly as above.
- `transitions == 0`: no segment boundary in the block; continue immediately.
- `transitions == 0xffff`: all 16 byte positions are boundaries; emit them in one tight fixed-count loop, toggling the predicate each byte. This is an exact bit-pattern specialization, not a workload/size classifier.
- Otherwise enumerate set transition bits directly with `ctz(transitions)` and `transitions &= transitions - 1`.
- Scalar tail remains exact.
- Segment ABI, kind/start/length semantics and canonical policy remain unchanged.
- No input-size thresholds, transition-density thresholds or case labels are permitted.

## Independent authority

Before timing any row, scalar C, SSE2 V2 and an independent Python maximal-run oracle must emit identical segment tuples and reconstruct the exact target. Any disagreement invalidates the lane.

## Frozen matrix and gates

Use the same matrix and 101-round native A/B–B/A timing contract as the first SSE2 lane:

- productive: `shift_plus1`, `shift_plus1_damage_quarter`, `fragmented_every96`;
- controls: `fragmented_every32`, `independent_random`;
- hostile: every-byte alternating equality/no-equality;
- tail/transition boundary lengths: 1, 2, 15, 16, 17, 31, 32, 33, 63, 64, 65;
- mature 4/8/16/32/64/128/256 KiB.

Advance to integrated plan-direct V2 writer testing only if all are true:

- semantic/oracle failures: `0`;
- mature productive median candidate/baseline `<=0.80x`;
- no mature productive row `>1.03x`;
- mature ordinary-control median `<=1.00x`;
- no mature ordinary-control row `>1.03x`;
- mature transition-hostile median `<=1.03x`;
- no mature transition-hostile row `>1.08x`.

If the dense-transition regression remains, reject the transition-mask implementation rather than introducing another adaptive threshold.

## Claim boundary

Native x86-64/SSE2 segment-kernel implementation only. Even a pass here authorizes only an integrated writer falsifier, not writer/product promotion or a portability claim.

Workflow registration followed the Builder; this non-semantic line exists only to trigger the already-frozen exact-source V2 lane.
