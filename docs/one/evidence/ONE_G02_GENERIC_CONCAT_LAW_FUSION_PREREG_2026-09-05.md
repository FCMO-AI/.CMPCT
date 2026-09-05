# ONE-G0.2 generic concat Law fusion — preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2

## Mission lock / referee

Bounded hierarchical concat repaired the 4,096-reference hard-cap failure at only 21 B of wire overhead on the 256 KiB fragmented hostile case, but the reference VM materializes the added intermediate concat and raises modeled reconstruction work by 28.5% versus the ideal flat graph.

**Hypothesis:** nested concat is associative at the representation level and can be executed as one reconstruction cone. A reader may flatten nested concat traversal while preserving the exact stored Program, references, Surprise bytes and hard bounds. This should remove the *execution* tax of the resource-safe hierarchy without changing the ONE ontology.

The existing `RangeEvaluator` is the independent baseline/oracle. The candidate evaluator changes only concat execution: leaf ranges are reconstructed exactly as before, but intermediate concat outputs are not separately materialized; only the requested root concat output is materialized. No discovery occurs in the reader.

## Frozen corpus

Use the exact bounded-hierarchy corpus unchanged:
- 4, 8, 16, 32, 64, 128, 256 KiB;
- `shift_plus1_damage_quarter`;
- `fragmented_every96`.

The known hierarchy-required witness is 256 KiB `fragmented_every96`.

## Frozen gates

For every row:

1. candidate full-current-root bytes == generic `RangeEvaluator` bytes == original target bytes;
2. decoded hierarchical Program is byte-for-byte unchanged by evaluation;
3. candidate uses no operation outside the existing six-op ONE grammar and performs no discovery;
4. candidate obeys declared depth and work limits;
5. where hierarchy is not required, candidate modeled work bytes and materialized bytes must equal the ordinary full-range evaluator exactly;
6. where hierarchy is required, candidate modeled work and materialized bytes must equal the full-range evaluator applied to the *ideal flat in-memory graph* exactly, proving that hierarchy itself adds no execution tax;
7. on every hierarchy-required row, candidate work and materialization must be strictly lower than the ordinary hierarchical full-range evaluator;
8. stored wire bytes and Surprise bytes are unchanged; this experiment earns no density claim;
9. nodes touched and maximum traversal depth are reported; no native elapsed-time claim is inferred from Python.

## Disproof semantics

- Any byte mismatch retires the fusion evaluator.
- If candidate accounting is below the ideal flat oracle, the accounting model is wrong; do not promote it.
- If candidate still pays more than ideal flat work/materialization, nested-concat execution remains an unresolved reader tax.
- If resource checks must be weakened, the experiment fails; do not raise caps.

## Claim boundary

A pass establishes only that bounded nested generic concat can be *executed* without materializing hierarchy intermediates under the current modeled resource semantics. It does not establish production/native decoder speed, authentication, arbitrary Law discovery, or comparator supremacy.
