# ONE-G0.2 V2 segment-phase sub-attribution — preregistration

Date: 2026-09-06
Branch: `research/cmpct1`
Experimental line: `ONE-G0.2`

## Mission lock

Plan-direct V2 writer attribution localized the broad `segment` phase as the primary mature productive owner at a `35.1295%` median share. That phase currently includes two materially different mechanisms inside `_native_plan`:

1. the native C one-pass segment classifier/emitter;
2. Python marshalling of the emitted C segment buffer into immutable plan tuples, including copying Surprise payload bytes from the target.

Do not assume the native byte scan owns the whole phase merely because it is the lowest-level loop.

## Falsifiable hypothesis

Python plan marshalling is the dominant remaining cost inside the V2 segment phase on plan-dense productive relations, while the native C scan dominates or remains material for sparse-plan relations. Across the frozen mature productive matrix, at least one subphase will own a stable material share.

Frozen subphases:

- `native_kernel`: only the `segment_fn(...)` C call;
- `plan_marshalling`: only the exact loop that converts `seg_buf[0:segments]` into the current tuple plan and copies Surprise payload bytes.

No semantic work may move across these timers after observing the result.

## Frozen validity gates

For 31 paired A/B–B/A rounds comparing ordinary `_native_plan` to the profiled equivalent:

- exact plan signatures must match each other and the independent Python segmentation oracle;
- profiled/unprofiled mature productive median `<=1.03x`;
- worst mature productive row `<=1.08x`.

If timing perturbation exceeds those bounds, invalidate attribution.

## Frozen owner rules

Over mature productive sizes 16/32/64/128/256 KiB and the frozen productive relations (`shift_plus1`, `shift_plus1_damage_quarter`, `fragmented_every96`):

- a subphase is a **primary** owner if its median share is `>=0.50` and it is `>=0.50` at at least three mature sizes;
- a subphase is **material** if its median share is `>=0.25` and it is `>=0.20` at at least three mature sizes.

If both are material, preserve both; do not force a single owner. If neither qualifies, record diffuse segment-phase cost.

## Claim boundary

Attribution only inside the current adjacent-version V2 `_native_plan` boundary. It changes no Law/Surprise semantics, wire bytes, reader behavior or writer policy and grants no v0.29/v0.30 comparison authority.

Workflow registration followed the Builder; this non-semantic line exists only to trigger the already-frozen exact-source attribution lane.
