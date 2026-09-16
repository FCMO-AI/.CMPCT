# v0.30 EG08 ladder stopping-oracle Mission Lock — 2026-09-13

Status: **counterfactual causal referee; no encoder change and no promotion credit**

## Entering evidence

The corrected low-yield attribution found that `10_large_mixed_binary` spends `97.50%` of measured ladder CPU on candidate bytes that are not stored, while hostile `05_incompressible` spends `100%`. Both execute the full `(3,6,12,19)` ladder with zero first-worse early stops. Conversely, EG11 proved a crucial counterexample: one Office pack stored RAW by the inherited level-1 admission later becomes compressible and saves `129,782 B` at higher effort.

Therefore a useful gate must distinguish *continued opportunity* from repeated proof traffic. Rules such as `RAW incumbent => stop` or `first tie => stop` are already scientifically unsafe.

## Question

Can a simple, content/codec-derived stopping predicate cut a material fraction of the frozen EG08 ladder while preserving the exact final stored choice across the full eligible-nine domain, including the Office RAW-incumbent promotion?

This referee does not alter archives. It executes the complete EG08 ladder and evaluates fixed counterfactual stopping predicates against the observed exact final choice.

## Frozen predicate family

Evaluate all of the following, report all outcomes, and do **not** add/remove predicates after seeing results:

- `P1_stop_after_level3_no_strict_win`: stop after level 3 when level 3 did not strictly improve stored size over the inherited incumbent.
- `P2_stop_after_3_6_no_strict_win`: stop after level 6 when neither level 3 nor level 6 strictly improved the incumbent.
- `P3_stop_after_two_consecutive_storage_ties`: stop after any two consecutive ladder rungs whose stored sizes equal the current best stored size.
- `P4_stop_after_3_6_same_candidate_size`: stop after level 6 when levels 3 and 6 produce the same candidate stored size, regardless of whether they improved the incumbent.
- `P5_jump_3_to_19_on_level3_no_strict_win`: after a non-winning level 3, skip levels 6 and 12 but still execute level 19; accept only if the final stored choice remains exact.

These are diagnostic hypotheses, not product policy. P5 is included because it retains the high-effort escape hatch that EG10 accidentally removed.

## Exactness oracle

For every non-hot physical pack in each frozen eligible-nine workload:

1. reproduce the full EG08 ladder and exact final codec/payload;
2. simulate each predicate using only information available at its stopping point;
3. record whether the predicate's counterfactual final storage codec, stored size and payload bytes equal the full EG08 result;
4. count avoided compression rungs and estimate avoidable measured ladder CPU/wall by summing the actually measured calls that would not execute;
5. preserve the Office RAW-incumbent promotion as an explicit named counterexample check.

A predicate with one false negative is **not exact** and cannot seed an exact-EG08 Builder.

## Surfaces

Exactly the already-frozen eligible-nine domain:

Neutral/current15: Office, Analytics, Logs, ML, Large Mixed.

Hostile: Shifted Versions, False Neighbors, Boundary Churn, Incompressible.

No workload is added or removed after observing predicate behavior.

## Success vocabulary

This referee does not select a winner by threshold. For every predicate publish:

- false-negative pack count;
- false-negative stored-byte delta;
- avoided calls and share;
- avoided measured CPU/wall share;
- whether the Office RAW promotion survives.

`EXACT` means zero final-payload mismatches on all nine. Anything else is `FALSIFIED` and the counterexample is preserved.

If no predicate is exact, do not threshold-tune another one in the same activation. That would indicate that exact-EG08 proof traffic needs work reuse or a stronger bound rather than a shallow heuristic.

No Genesis/R4 score, v0.29 comparator, locality, integrity/recovery, format revision, numeric version or ONE status changes.
