# ONE-G0.2 demand-grown nomination index carrying cost — preregistration

Date: 2026-09-06
Experimental line: `ONE-G0.2`
Authoritative branch: `research/cmpct1`
Status: frozen before result-bearing timing; execute only if the demand-grown semantic/resource gate passes

## Mission Lock

The fixed-index fused nominator is semantically exact and beats the exact two-stage native baseline on every frozen mature row, but it reserves 198,144 B of research event-index state and still carries a ~31.99% median premium over selector-only. The demand-grown rehabilitation preserves the 8,192-entry hard cap while allocating global first-witness entries geometrically as needed.

Test whether the memory repair preserves the economically useful one-pass elapsed shape after charging every allocation and reallocation performed by the candidate.

## Frozen baseline and candidate

Use the same one-call-per-arm native timing wrappers as the terminal fused carrying-cost experiment:

- selector-only: carrying-cost reference, not same semantics;
- two-stage native selector + trace + event consumer: exact same-semantics baseline;
- fused demand-grown nominator: candidate.

All timing is C-to-C behind one Python->C transition per arm. The semantic/resource demand-index gate is a prerequisite and must be cited independently.

## Frozen envelope

Exactly the mature 36-row envelope used by the fixed-index carrying-cost result:

- relation sizes: 64 KiB and 256 KiB;
- seeds: 7, 29, 53;
- cases: `shift_plus1`, `damage_quarter`, `fragmented_every96`, `hostile_fixed_bands`, `fragmented_every32`, `independent_random`;
- 31 paired samples per row after 5 warmups;
- alternate two-stage/fused order A/B-B/A.

## Falsifiable hypothesis

Demand-grown allocation can cut resident event-index state by roughly an order of magnitude on the frozen envelope without erasing the one-pass elapsed advantage. Because growth is bounded and occurs only at 64/128/256/... capacities, allocation/copy work should remain secondary to the eliminated second scan.

### Disproof

The rehabilitation fails if memory drops but the same-semantics elapsed advantage disappears or negative controls regress systematically.

## Decision law

Prerequisite: demand-grown semantic/resource gate passes exactly.

- `advance_demand_index_carrying_shape` if median fused/two-stage <= **0.92x**, no row > **1.05x**, worst negative-control row <= **1.00x**, and median fused/selector-only <= **1.35x**.
- `hold_demand_index_carrying_shape` if fused/two-stage median < **1.00x** but one stronger condition above is missed.
- `retire_demand_index_carrying_shape` if fused/two-stage median >= **1.00x** or systematic negative-control regression exceeds **1.05x**.

The 0.92 threshold intentionally allows modest allocator/copy debt relative to the fixed prototype's exact-run 0.90623x while still requiring a material same-semantics win.

## Hostile Reviewer

A pass still does not make always-hot nomination product-worthy: selector-only carrying premium remains explicit debt. The result only decides whether demand-grown state is the preferred implementation shape for subsequent integration. If it passes but selector premium remains near ~1.3x, the next owner is nomination lookup/proof/control work, not allocation. If it fails, investigate arena/pre-sizing or sparse opportunity gating rather than restoring the 198 KiB fixed reservation by default.
