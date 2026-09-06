# ONE-G0.2 simple-relation linear phase attribution — preregistration

Date: 2026-09-06  
Branch: `research/cmpct1`  
Experimental line: `ONE-G0.2`

## Mission Lock

The shared-native writer seed and generic final-ref fusion both preserve exact semantics and produce very large gains on segment-rich relations, but both fail the unchanged 15/15 breadth gate only on large `shift_plus1` rows with two Segments. Final-ref staging fusion did not repair those rows. The remaining ratio approaches parity as bytes rise, indicating that continued O(segments) micro-tuning is unlikely to own enough of the charged O(n) writer boundary.

Before changing another mechanism, attribute the current ref-fused candidate's broad linear phases on the same mature relation sizes.

## Hypothesis

At least one of the following charged phases owns a stable, material share of the simple two-segment path and therefore provides a more credible optimization boundary than additional final-writer staging work:

1. root SHA-256 + raw-digest preparation;
2. relation admission / exact proof gate;
3. native one-pass segmentation;
4. native bounded ONE0 validation/emission + output exposure.

If no phase is a stable >=15% owner on the mature simple-shift rows, the correct conclusion is to move the optimization boundary upward/fuse phases rather than micro-optimize an individual function.

## Frozen source / semantics

Use the exact current ref-fused shared-native writer and the exact admission/segment kernels inherited from the shared-native transfer. No Law/Surprise decision, root identity, Segment semantics, wire grammar, node/ref/root ordering, resource limits or reader semantics may change.

The diagnostic does not promote code. It attributes elapsed only.

## Matrix

Mature sizes only: 16, 32, 64, 128, 256 KiB.

Cases:

- `shift_plus1` — the breadth-debt target;
- `shift_plus1_damage_quarter` — moderate segment density;
- `fragmented_every96` — high segment density / known native-writer win;
- `independent_random` — relation-disabled control.

## Timing discipline

- 63 rounds after untimed correctness/warmup;
- GC disabled during timing;
- each phase timed independently with all required inputs already present except the work assigned to that phase;
- full candidate path timed uninstrumented using the same ref-fused writer ABI;
- report median ns and ns/input-byte;
- report `phase_median_ns / full_candidate_median_ns` as an attribution indicator, but do not require isolated phase shares to sum exactly to 1 because cache state and call boundaries differ;
- report `sum(isolated_phase_medians) / full_candidate_median_ns` to expose attribution distortion rather than hiding it.

The native-writer isolated phase must include C allocation, bounded validation, canonical emission, `ctypes.string_at` output exposure and free, matching the candidate's existing charged boundary. The hashing phase must reproduce the existing `hexdigest -> raw digest` preparation exactly.

## Correctness gate

Before timing each row:

- admission result matches the full candidate;
- segmentation succeeds when enabled;
- full ref-fused candidate reconstructs exactly and its canonical wire decodes under ONE;
- no semantic mismatch is tolerated.

## Interpretation rule

A phase is a **credible individual owner** only if its isolated share is >=15% on at least 4/5 mature `shift_plus1` sizes and its median share across those sizes is >=15%.

If multiple qualify, rank by median share and by bytes-scaled growth. Prefer removing/fusing a pass over optimizing arithmetic inside a pass.

If none qualifies, preregister a broad fused-boundary experiment; do not invent workload dispatch or resume final-writer allocation micro-tuning.

## Claim boundary

This is attribution on an adjacent-version research writer. It has no stored-byte, product, RSS/native peak, authenticated placement, v0.29/v0.30 or 15-workload Genesis authority.