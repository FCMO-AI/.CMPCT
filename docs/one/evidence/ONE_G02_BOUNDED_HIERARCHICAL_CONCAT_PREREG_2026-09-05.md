# ONE-G0.2 bounded hierarchical concat — preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2

## Mission lock / referee

The actual temporal-adjacency ONE writer exposed a bounded-reader failure: a sufficiently fragmented +1 relation is naturally described by more than 4,096 alternating Ref/Surprise parts, while the current experimental ONE reader rejects a single concat whose reference count exceeds its hard cap. Raising the cap or introducing a shift opcode would evade the ONE thesis rather than solve the representation problem.

**Hypothesis:** the exact same generic Ref+Surprise Law can be compiled as a shallow tree of existing `concat` nodes, using the declared `Limits.max_nodes` value as the fanout bound at every level. This should make the representation wire-decodable without changing reader ontology or Surprise bytes.

The fanout is not tuned from benchmark results: each concat uses at most the already-declared hard cap, minimizing the number of extra hierarchy nodes needed for validity.

## Frozen corpus

Deterministic sizes: 4, 8, 16, 32, 64, 128, 256 KiB.

Cases inherited unchanged from the relation-transfer generator:
- `shift_plus1_damage_quarter`
- `fragmented_every96`

The known hostile focus is 256 KiB `fragmented_every96`, whose flat relation contains more than 4,096 parts.

## Frozen measurements and gates

For every row:

1. hierarchical encode -> decode -> evaluate reconstructs both previous and current roots byte-exactly;
2. Surprise bytes are exactly identical to the flat generic relation program;
3. every concat node has <= declared `max_nodes` references;
4. total program node count remains <= declared `max_nodes`;
5. hierarchy uses no operation outside the existing six-op ONE grammar;
6. where the flat program is already reader-valid, hierarchical wire bytes must be exactly equal to flat wire bytes (no gratuitous hierarchy);
7. where hierarchy is required, hierarchical wire size may exceed the ideal flat encoded bytes by at most **0.50%**;
8. hierarchy depth must remain <=4 for the frozen corpus;
9. full reconstruction work amplification versus evaluating the ideal flat Program in memory must be reported and must remain <=2.10x on every hierarchy-required row;
10. materialized bytes and node counts are reported; no speed claim is inferred from Python timing.

The benchmark must explicitly demonstrate that the flat hostile wire is rejected by the bounded decoder while the hierarchical form succeeds. A pass therefore repairs a real resource-semantic failure rather than merely producing another equivalent representation.

## Disproof semantics

- Any semantic or Surprise-byte mismatch retires this compiler form.
- Node-cap failure means hierarchy alone is insufficient; do not raise limits post hoc.
- Wire overhead >0.50% means the current generic control representation is too expensive under fragmentation and Law-control density becomes the next owner.
- Work amplification >2.10x means bounded hierarchy is semantically viable but reconstruction fusion is mandatory before promotion as an efficient reader path.

## Claim boundary

A pass establishes only bounded generic representation of the tested fragmented adjacent relation. It does not establish arbitrary relation discovery, writer admission cost, native writer speed, selective-read authentication, or superiority to v0.29/deferred-v0.30.
