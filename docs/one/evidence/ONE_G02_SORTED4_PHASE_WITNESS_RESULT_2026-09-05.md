# ONE-G0.2 — sorted-4 phase-witness selector result

Date: 2026-09-05
Experimental line: ONE-G0.2
Decision: **retire selection-local rehabilitation**

## Exact evidence

- source: `835e7c6d3bb3d4660f4455a11a7566e2198c6fba`
- workflow: `33974219690`
- artifact: `9971862552`
- artifact digest: `sha256:f3b1ebb8455f4730bb322c4d2de99b6836db5caf3b209466fae91cd3056fae56`
- control witness mismatches: 0
- candidate witness mismatches: 0
- modeled incremental state: 248 B

## Result

The sorted-4 representation is semantically exact but does not materially reduce ordinary large-loop cost. Five-large-control median candidate/control elapsed was **1.0124087853x**, versus the frozen <=0.90x requirement.

Per control:

- random 1 MiB: 1.01196x
- compressed-like ~1 MiB: 1.01282x
- repeated 1 MiB: 1.01303x
- shifted/versioned 1 MiB: 1.01241x
- zeros 1 MiB: 0.84184x
- alternating hostile 1 MiB: 1.01794x
- random 4 KiB: 0.97747x
- random 64 B: 0.89224x

The isolated win on zero/tiny controls is not enough to rescue the common large path and must not be promoted by corpus-weighting after the fact.

## Hostile Reviewer

This result strengthens the owner decomposition rather than contradicting it. Bottom-K was the stable *first* owner, but raw-window and hash costs were close. Re-spelling the exact selector mostly moves branches/data motion around; it does not remove the repeated work that makes the unconditional fused certificate uneconomic.

Per preregistration, do not try another heap/sorted spelling on this cohort. Selection-local rehabilitation is retired as the immediate route.

## Next action

Pursue mechanism-level work elimination: derive content-local relation evidence from already-required observer state, or gate the richer certificate from independent cheap evidence. The Gear-difference certificate is the current concrete candidate.

No density, reader-speed, format, product, v0.29, or deferred-v0.30 claim follows.