# ONE-G0.2 Native Exact Relation Proof — Parity Correction (2026-09-09)

## Decision

**INVALIDATE_POST_REPAIR_NATIVE_PROOF_LINEAGE_THROUGH_DFB7A4A**

Repository truth exposed a parity mistake in the attempted repair recorded by `ONE_G02_NATIVE_EXACT_RELATION_PROOF_INVALIDATION_2026-09-09.md`.

The authoritative Python oracle in `experiments/one/relation_span_growth.py` defines `RelationGrowthResult.runs` as plain `(start, length)` tuples and returns those tuples directly. It does **not** define or return a `RelationSpan` wrapper type.

The attempted repair lineage imported a nonexistent `RelationSpan` from that module and changed the native wrapper to construct `RelationSpan` values. At current head `dfb7a4a2298da92dfff545a6ac5cf221cbb65db4`, importing `experiments.one.native_relation_span_growth` would therefore fail before the semantic parity benchmark could run.

## Scientific consequence

Source lineage after the earlier pre-evidence invalidation and through:

`dfb7a4a2298da92dfff545a6ac5cf221cbb65db4`

is scientifically inadmissible for native-proof promotion. No run from that lineage may be cited as proof of semantic parity or performance, even if an earlier queued workflow later reports a convenient result.

This does **not** invalidate the already-promoted V3 writer-envelope result at source `780347517de07f81673ae44c25c435e6e6e0b046`; that result predates this native exact-proof experiment.

## Corrective source

Commit `013131242360b50262003c390ddfd48b94f4d6cf` restores the native wrapper to the actual oracle representation:

- import only `RelationGrowthResult`;
- return `tuple((start, length), ...)` exactly like the Python oracle;
- retain the bounded integer/geometry hardening already added to the native proof path;
- retain zero-copy immutable-byte access and the frozen native-proof performance gates.

The existing native parity tests compare the complete dataclass result (`native == py`), so the corrected exact-source CI lane must pass those tests before any performance result is admissible.

## Hostile-review lesson

Do not infer oracle semantics from an evidence note or an intended refactor. Read the current authoritative implementation before changing a parity target. Evidence prose can itself be wrong; executable repository truth wins.

## Next admissible action

Consume only an exact-source native-proof workflow at or after `013131242360b50262003c390ddfd48b94f4d6cf`. Promotion still requires all preregistered semantic and performance gates with no threshold movement.