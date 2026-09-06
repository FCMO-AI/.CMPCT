# ONE-G0.2 fused nomination actual-state audit — preregistration

Date: 2026-09-06
Activation T0: 2026-09-06T02:04:36Z
Experimental line: ONE-G0.2
Authority: research/cmpct1

## Mission Lock

The existing fused-native-nomination carrying-cost gate reports a fixed 198,144-byte research event-index debt, while the fused C kernel itself allocates its global nomination index geometrically from 64 entries and reports actual `reserved_state_bytes`. Determine whether 198,144 B is truly carried by the fused candidate or is primarily a property of the fixed two-stage/oracle consumer.

## Baseline / invariant

Baseline is the promoted offset-only selector state plus the exact two-stage nomination consumer used as semantic oracle. Candidate is the existing fused kernel; no algorithm, threshold, reader operation, nomination policy, proof policy, or ONE representation may change in this audit.

## Falsifiable hypothesis

On the frozen 64 KiB and 256 KiB relation matrix, actual fused reserved state is materially below 198,144 B and remains bounded near the selector state because global storage grows only to observed demand.

## Disproof / decision law

For every row, fused anchor count/final state and cross-audition/cross-exact outputs must match the independent two-stage selector+consumer oracle exactly.

- `advance_actual_state_rehabilitation` only if semantic mismatches are empty, max fused reserved state <= 65,536 B, max fused/selector reserved-state ratio <= 1.35x, and every fused reserved-state value is < 198,144 B.
- `hold_actual_state_rehabilitation` if semantics are exact and fused state is below 198,144 B but either tighter state gate fails.
- `reject_actual_state_rehabilitation` on semantic mismatch or any fused state >= 198,144 B.

No elapsed claim is made here; the existing carrying-cost run remains elapsed authority. This audit exists solely to identify the real state owner before changing code.

## Frozen matrix

Sizes: 64 KiB, 256 KiB. Seeds: 7, 29, 53. Cases: shift_plus1, damage_quarter, fragmented_every96, hostile_fixed_bands, fragmented_every32, independent_random.

## Hostile review

A dynamic allocation can hide capacity rather than eliminate it, so the audit records `reserved_state_bytes`, local/global peak entries and the selector baseline for every row. A low observed state is scoped to this frozen envelope and is not a proof that arbitrary future workloads cannot approach the 8,192-entry hard cap. If the audit passes, later work must still bound/adapt the worst-case carrying cost rather than silently treating observed demand as a universal bound.
