# R26 — Incremental Backups Product-Floor Diagnostic Preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION**

Authority substrate: PR #56, product code inherited unchanged from `b0e7aeab92c994b4a25c5040fe3fb9f5e208b01a`.

Trigger evidence: exact-head final release authority run `33821608048` aborted canonical product parity on `neutral_hostile_v1/06_incremental_backups` because the published v0.30 product archive was larger than genuine canonical r24 on the same user tree. This is a hard product invariant; no release threshold, locality ceiling, recovery/integrity rule, or comparator may be weakened.

## Question

Which complete-artifact boundary creates the Incremental Backups regression, and can the genuine-r24 floor be restored without borrowing locality debt?

This is a Forge D0–D5 attribution experiment. It is not a release gate and grants no promotion credit.

## Frozen arms

On the deterministic repaired `neutral_hostile_v1/06_incremental_backups` source tree, build and retain three complete archives from the same process environment:

1. **genuine-r24** — unmodified canonical `cmpct.builder.Builder(source).build()` bytes, matching the product-parity comparator.
2. **release-r24** — the promoted product's `_locality_bounded_r24_build()` bytes, including its shipping locality policy and dead-dictionary post-selection elision.
3. **current-product** — `experiments.entropygraph_v030_release_product.build()` with the exact promoted product code inherited from the authority substrate.

All arms must strongly verify and reconstruct the same product user-tree identity. Failure of correctness terminates the experiment; no performance or size interpretation survives it.

## Frozen locality observation

For each complete archive, select the largest regular user-visible member by `(size, path)` and read it through the actual promoted product member operation with operation-derived decoded-context instrumentation. Report logical bytes, decoded-context bytes and decoded-context amplification. Missing or ambiguous locality accounting is a failure, not a default.

The hard ceiling remains **<= 8.0x**. A smaller genuine-r24 archive may not be proposed as a product fallback if its measured selected-member amplification exceeds 8.0x.

## Frozen outputs

Report for every arm:

- archive bytes and SHA-256;
- format revision/profile;
- product user-tree SHA-256;
- strong-verification result;
- selected largest-member path and logical bytes;
- operation-derived decoded-context bytes/amplification;
- build wall time and process peak RSS;
- current-product build selection metadata (`selected`, r24/r25 product bytes, attempted/reject reason) when present.

Also report exact byte deltas:

- `release-r24 - genuine-r24`;
- `current-product - genuine-r24`;
- `current-product - release-r24`.

## Frozen interpretation law

- **D2/R1–R3 candidate:** genuine-r24 is <= current-product, is strongly verified, and selected-member amplification is <=8x. This establishes that a lawful complete-artifact floor exists inside the current information ontology. It does **not** authorize simply adding a third full build; the follow-up Builder must preserve byte exactness while paying global creation/RSS carrying cost.
- **D3/D4 locality-exported debt:** genuine-r24 is smaller but exceeds 8x. The apparent byte floor is not legally borrowable. The next intervention must reduce the representation/locality cost rather than relax the ceiling.
- **D1 measurement/substrate defect:** the current-product archive is not actually larger than genuine-r24 on the frozen tree, or identities do not match. Investigate harness/substrate drift before product changes.
- **D5 transient/integration defect:** current-product is larger only because an already-proven product branch failed to participate or a selector/accounting bug chose the wrong complete artifact. Repair the selector at lowest sufficient radicality and regenerate exact-head authority.
- **R5 return to Foundry:** only if the diagnostic plus subsequent lowest-sufficient Forge probes establish that no legal artifact within the current ontology can meet both genuine-r24 bytes and the hard locality/product constraints.

## Anti-cheating / immutability

After the first result-bearing execution, this document, its arms, source identity, locality target, 8x ceiling, and interpretation law are immutable. An unfavorable result must be preserved. Any material change requires a new superseding preregistration. No benchmark-name routing, hidden representation bytes, deferred metadata, or relaxed product invariant is permitted.
