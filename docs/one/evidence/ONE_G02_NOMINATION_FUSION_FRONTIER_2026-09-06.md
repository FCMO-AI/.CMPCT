# ONE-G0.2 nomination-fusion frontier handoff

Date: 2026-09-06
Experimental line: `ONE-G0.2`
Authoritative branch: `research/cmpct1`

This handoff reconciles the exact nomination/discovery execution frontier. Immutable result receipts remain authority for individual claims.

## What is now proven

1. **Native minimizer trace -> reference nomination is exact.**
   `ONE_G02_NATIVE_NOMINATION_TRACE_BRIDGE_RESULT_2026-09-06.md`: 93 ONE tests; zero trace/signal/nomination mismatches. The promoted native rightmost-min selector emits sufficient information to reproduce the existing nomination policy.

2. **Native event/index consumption is exact.**
   `ONE_G02_NATIVE_NOMINATION_EVENT_CONSUMER_RESULT_2026-09-06.md`: frozen 90 rows; zero trace/audition/exact/false-exact mismatches. Python no longer owns nomination event semantics.

3. **Nomination can be fused into the selector pass exactly.**
   `ONE_G02_FUSED_NATIVE_NOMINATION_RESULT_2026-09-06.md`: frozen 90 rows; exact selector trace and nomination outcomes; candidate sequential observation traffic exactly 0.5x the two-stage native oracle; no intermediate anchor trace required by the nomination path.

4. **Fusion improves elapsed versus the exact same-semantics two-stage path, but is not yet cheap enough.**
   `ONE_G02_FUSED_NATIVE_NOMINATION_CARRYING_COST_RESULT_2026-09-06.md`: 36 mature rows; median fused/two-stage 0.90623x, worst 0.95340x, no row regressed; median fused/selector-only 1.31987x. Decision is HOLD, not promotion.

5. **The unconditional 136-byte local Gear certificate is retired as an always-hot path.**
   `ONE_G02_LOCAL_GEAR_CERTIFICATE_NATIVE_COST_RESULT_2026-09-05.md`: large median 2.29410x the promoted observer. Rich supplementary evidence must be cold/sparse/gated rather than paid per byte.

## Current rehabilitation

The fixed fused research prototype reserved 198,144 B for its event indices even though the terminal 256 KiB envelope observed at most 64 local + 272 global live entries (8,064 B at the 24-byte research entry layout).

`ONE_G02_FUSED_NOMINATION_BOUNDED_DEMAND_INDEX_PREREG_2026-09-06.md` therefore governs the current Builder:

- preserve local 64-entry semantics;
- preserve the exact 8,192 global hard cap;
- global allocation grows 64 -> 128 -> 256 -> 512 -> ... only when required;
- do not lower the cap to fit the corpus;
- allocation failure is explicit;
- semantic/resource gate precedes timing.

The demand-grown candidate is implemented in `one_g02_fused_native_nomination_kernel.c`; its exact result is pending CI at this handoff.

## Parallel causal diagnostic

`ONE_G02_NOMINATION_INDEX_PROBE_ATTRIBUTION_PREREG_2026-09-06.md` asks whether the frequently queried 64-entry local linear FIFO, rather than the larger but sparse global index, owns most key comparisons. This is comparison-count attribution only; it cannot substitute for native elapsed evidence.

## Next decision tree

1. If demand-grown semantic/resource gate fails: repair exactness/cap accounting before timing.
2. If it passes: run the already-frozen demand-index carrying-cost gate with realloc/copy charged.
3. If demand-grown fused/two-stage remains materially <1.0 and memory drops sharply: use it as the preferred native nomination research shape.
4. If selector-only premium remains around ~1.3x, consume the probe-attribution diagnostic and attack the measured lookup/proof/control owner rather than the eliminated second scan.
5. Only after nomination carrying cost is credible should the campaign execute the frozen integrated discovery + safe-relation-dispatch A/B.

No result in this chain changes the ONE reader ontology, comparator authority, or September 11 Genesis gate.
