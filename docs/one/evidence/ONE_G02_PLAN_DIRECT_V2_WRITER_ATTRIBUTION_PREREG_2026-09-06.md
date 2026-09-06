# ONE-G0.2 plan-direct V2 writer attribution — preregistration

Date: 2026-09-06
Branch: `research/cmpct1`
Experimental line: `ONE-G0.2`

## Mission lock

The exact-source plan-direct V2 writer (`71c0ecc45a4d3b96e689549ad7912046465d404d`) is the current experimental canonical-writer compiler authority: byte-identical ONE0 output with mature productive elapsed `0.7807797801x` versus Program materialization. Its broad Python peak-allocation follow-up was independently falsified.

Do not keep optimizing the removed Program layer. Re-profile the **improved V2 writer boundary** to identify what now owns elapsed time before opening another optimization lane.

## Falsifiable hypothesis

With Program/Node/Ref materialization removed, at least one remaining coarse phase owns a material, stable share of V2 writer elapsed across the mature productive matrix.

Phases are frozen as:

1. `root_hash`: SHA-256 roots only;
2. `admission`: exact existing relation admission/gate;
3. `segment`: exact existing native plan construction when enabled;
4. `direct_wire`: V2 plan-direct canonical serialization only.

No phase may be renamed, merged or split after observing the result.

## Disproof / interpretation gates

The attribution is invalid if instrumentation changes writer semantics/canonical bytes or if profiling overhead is too large.

Instrumentation overhead gates over mature rows (`>=16 KiB`):

- productive median profiled/unprofiled `<=1.03x`;
- worst mature productive row `<=1.08x`;
- mature control median `<=1.05x`.

A phase is a material owner only if:

- its mature productive median share is `>=0.25`;
- and its median share is `>=0.20` at at least two mature sizes.

If no phase qualifies, record diffuse cost; do not pick the largest phase merely because one must be largest.

## Frozen method

- Same relation generator, productive/control cases, sizes and paired round count as the authoritative root-hash writer lanes.
- Alternate unprofiled/profiled execution order each round.
- `time.perf_counter_ns()` phase boundaries; phase shares are computed from phase medians, not from a single noisy run.
- Disable Python GC during timed pairs, restoring it afterward.
- Recheck canonical wire, WireStats, enabled decision, best shift, exact-proof count, plan signature, relation traffic, segmentation count, hierarchy depth, node count and decode/evaluate exactness.
- Native plan must continue to match the independent Python oracle where enabled.
- Full `tests/one` must remain green in CI.

## Claim boundary

This lane attributes elapsed only inside the current adjacent-version root-hash-charged V2 research writer. It does not include arbitrary/fused discovery, durability, filesystem semantics or product-native integration. A material owner found here is a candidate for the next writer optimization, not evidence of whole-system CMPCT1 superiority.
