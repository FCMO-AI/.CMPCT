# G04 screen-order reversal hostile — held-out falsifier

**Status:** research evidence only; not complete-artifact product credit  
**Candidate under test:** PR #211 / `agent/v030-g04-screen-productization-final@eecbeebcb638610902258ca8ce9f7598d65a9258`  
**Evidence branch:** `agent/phased3-g04-screen-order-falsifier`

## Question

Does the zero-threshold rule

`best transformed level-6 bytes >= direct level-6 bytes => skip all level-19 Hierarchical Geometry finalists`

preserve exact candidate admission for arbitrary valid inputs?

## Held-out structural hostile

The committed regression test constructs one deterministic printable 21,759-byte input with no filename,
extension, schema parser, workload identity or RNG dependency. It has 160 rows, eight fixed-width printable
fields per row, pipe as a secondary separator and newline as a primary separator.

Local independent reproduction against the repository's current Zstandard semantics measured:

- direct level 6: **6,114 B**
- best transformed level 6: **6,143 B**
- direct level 19: **5,858 B**
- exact top-three Hierarchical Geometry winner: **5,663 B**
- exact payload saving: **195 B**
- winner: primary `0x0A`, secondary `0x7C`, prefix planes enabled
- flat Geometry incumbent: direct at **5,858 B**

Therefore the screen guard fires even though the historical exact top-three policy has a valid winner above
the frozen 64-byte mechanism floor.

The committed test deliberately avoids pinning those absolute compressor byte counts. It verifies the
cross-level ordering reversal with relative inequalities, then requires the productized `HG.audition` result
to preserve or dominate the independent bounded-screen control.

## Decision boundary

This falsifies universal **representation-level** screen-order preservation if reproduced by repository CI.
It does **not** yet establish the complete G04 archive-size delta or the prevalence of order reversals.

The cheapest next product-level discriminator is a complete G04 artifact A/B on this hostile. If the guarded
artifact is larger, the zero-threshold finalist-pruning lane meets its own kill condition and should be retired
without margin/threshold gardening. If complete artifact bytes remain equal, the primitive remains a correctness
warning and a stronger provable admission rule is still required before arbitrary-data preservation can be claimed.

## Counterfactual discriminator

For any proposal that replaces exact-level candidate admission with a cheaper compressor-level screen, test
candidate-order stability across screen and exact levels on held-out structural perturbations before productizing.
Frozen-corpus equality is empirical evidence for those workloads, not a proof of the cross-level implication.

No Discovery Engine policy modification is earned from one counterexample.
