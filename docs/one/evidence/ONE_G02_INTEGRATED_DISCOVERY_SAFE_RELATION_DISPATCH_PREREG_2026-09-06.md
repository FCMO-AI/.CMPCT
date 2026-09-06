# ONE-G0.2 — integrated discovery + overlap-safe relation dispatch preregistration

Date: 2026-09-06
Experimental line: `ONE-G0.2`
Authoritative branch: `research/cmpct1`
Status: frozen before result-bearing execution

## Mission Lock

The generalized bounded-shift relation primitive has already survived an overlap-safe no-alias structural-transfer gate from 4 KiB through 256 KiB. The remaining question is not whether `restrict` can make an isolated proof kernel fast; it is whether that implementation recovery survives when the writer pays the opportunity/nominator and admission/proof envelope that decides whether relation work should run at all.

This experiment therefore integrates the already-evidenced pair-nomination path with the overlap-safe relation dispatcher. It does not add a new reader operation, change ONE0 wire bytes, or invent a relation-specific storage mode.

## Baseline and candidate

Both arms MUST use the same input pairs, same nomination evidence, same amortization policy, same exact bounded-shift semantics, same accepted relation, and same downstream Law + Surprise representation.

- **Baseline:** nomination/opportunity gate -> alias-conservative generic relation proof.
- **Candidate:** identical nomination/opportunity gate -> dynamic source/target disjointness proof -> no-alias relation proof only when disjoint; otherwise the alias-conservative fallback.

The candidate may not assume disjointness from Python object identity or test-generator construction. The native address ranges used by the proof kernel are authoritative. Overlap must take the fallback path.

## Falsifiable hypothesis

For writer-relevant nominated relations, proving disjointness once and exposing that fact to the compiler removes enough alias-conservative work that the safe dispatch remains a measurable end-to-end improvement after nomination, opportunity gating, negative-control work, and fallback dispatch are charged.

### Disproof

The hypothesis is constrained or rejected if any of the following occurs:

1. nomination/accepted-relation semantics differ between arms;
2. any overlapping layout enters the no-alias path;
3. a negative control enables a false exact relation;
4. the integrated candidate loses the isolated gain so thoroughly that its productive aggregate is not materially below baseline under the frozen timing law;
5. the gain depends on weakening the amortization gate or dropping hostile/negative cases;
6. source traffic, proof traffic, retained state, or fallback work is silently moved outside the measured boundary.

## Frozen envelope

Use deterministic cases across 4, 8, 16, 32, 64, 128 and 256 KiB where applicable:

- exact `shift_plus1`;
- quarter-damaged +1;
- `fragmented_every96` productive relation;
- `fragmented_every32` false-pattern control;
- independent-random control;
- explicit same-allocation overlapping source/target slices, including at least one productive semantic relation and one negative control.

Where the existing shared-observer nomination family has a previously documented blind spot, the row remains visible and is classified as nomination debt rather than gifted to either arm. The benchmark may also include legitimately known adjacent-version pairs as a separate stratum, but may not mix that stratum into arbitrary-discovery claims.

## Required accounting

Persist per row:

- relation bytes and case;
- nomination outcome and nomination work/traffic;
- whether exact relation proof was attempted;
- accepted relation and best shift;
- direct/candidate exact result equality;
- dynamic disjointness result;
- fast-path versus overlap-fallback incidence;
- source/target bytes inspected by cheap gate and exact proof where instrumentable;
- elapsed time over the same complete measured boundary using paired/alternating order;
- persistent and transient state attributable to the integration;
- false nominations and false exact acceptances.

Reader decode, stored bytes, selective access, integrity/recovery and v0.29/v0.30 comparison remain outside this experiment unless explicitly added and charged symmetrically.

## Frozen promotion law

Correctness/safety gates are absolute:

- exact relation/result agreement on every row;
- zero overlap rows entering the no-alias path;
- zero false exact relations;
- no weakening of existing bounded-shift/resource semantics;
- no added reader-visible ONE operation.

Performance gate, evaluated only after those absolute gates pass:

- productive integrated median candidate/baseline `<= 0.95x`;
- no productive row `> 1.03x`;
- negative-control median `<= 1.03x` baseline;
- the 4 KiB fixed-cost regime may fail to show a large win but may not exceed the 1.03x non-inferiority bound;
- all reported timing uses repeated paired/alternating order; a single unpaired measurement has no promotion authority.

These thresholds are deliberately stricter than merely showing a statistically detectable improvement: integration is worthwhile only if the isolated mechanism-level gain remains meaningful after the surrounding writer work is charged.

## Decisions

- `advance_safe_relation_dispatch_into_discovery` — all semantic/safety gates and the performance law pass.
- `hold_relation_gain_diluted_by_nomination` — semantics pass but integrated elapsed does not.
- `reject_safe_relation_dispatch_integration` — safety/semantic invariants fail or the candidate exports material regression.

A hold sends the next Builder to nomination/admission cost decomposition. It does **not** authorize another isolated relation micro-optimization.

## Hostile Reviewer before execution

The most dangerous benchmark error would be to time only rows already known to be productive, thereby gifting the cost of deciding *whether* to attempt the relation. Negative controls and nomination misses therefore remain in the matrix. The second danger is undefined behavior from applying a no-alias contract to overlapping buffers; overlap fallback is an explicit correctness gate, not optional telemetry.

## Claim boundary

This is writer-discovery integration evidence only. Passing it would not establish full ingest, product-native writer speed, authenticated placement, density superiority, or the September-11 Genesis decision.