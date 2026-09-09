# ONE-G0.2 Native Exact Relation Proof — Pre-evidence Invalidation (2026-09-09)

Source lineage through **`4cfd8baaae9493c03b25a3294d08e4fd5eed1ce4`** is scientifically inadmissible for promotion, regardless of any eventual hosted result.

Hostile review found two wrapper-level parity defects before admissible evidence was accepted:

1. the native wrapper returned raw `(start, length)` tuples inside `RelationGrowthResult.runs`, while the Python oracle returns `RelationSpan` values;
2. the native nomination normalization did not explicitly discard negative nominations before constructing the `uint64_t` buffer, unlike the Python oracle.

Neither defect changes the intended native proof algorithm or frozen performance gate, but both violate the experiment's exact-result parity contract. They were therefore repaired without moving the preregistered law.

The corrected source imports/returns `RelationSpan` and matches Python normalization (`int`, non-negative filter, de-duplicate, sort). Exact semantic parity tests remain mandatory before the hosted performance falsifier.

Do not cite run `34350545197` or source `4cfd8baa...` as scientific evidence even if infrastructure later executes it.
