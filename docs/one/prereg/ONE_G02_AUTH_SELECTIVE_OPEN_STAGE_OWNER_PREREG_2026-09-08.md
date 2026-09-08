# ONE-G0.2 authenticated selective-open stage owner — preregistration

Date: 2026-09-08
Status: frozen before result
Experimental version: `ONE-G0.2`

## Mission lock

Question: once an authenticated tree already exists, which reader-side stage owns selective-open compute: proof extraction or proof verification/reconstruction?

This is a profiler, not a new reader mechanism and not a promotion gate. It measures the existing generic authenticated-range semantics through two proof-production shapes:

1. `reference`: materialized Python `AuthTree` + `prove_range()`;
2. `packed_interval`: native packed tree + `prove_range_packed_interval()`.

Both feed the same `verify_range()` implementation. Tree creation is outside selective-open timing and remains governed by its separate exact-source evidence.

The packed-interval result is diagnostic even if its independent promotion falsifier later HOLDs; it may not be promoted through this profiler.

## Falsifiable hypothesis

`verify_range()` owns at least 60% of the median selective-open wall and CPU stage sum on at least 12 of 16 decisive rows for each pipeline at 1 MiB.

Disproof: either pipeline has fewer than 12 of 16 rows meeting the 60% threshold on both wall and CPU, or any semantic/proof equality gate fails.

The profiler may instead report `OWNER_PROOF_EXTRACT` if proof extraction owns at least 60% on both wall and CPU in at least 12/16 rows for both pipelines. Otherwise it reports `DISTRIBUTED_AUTH_SELECTIVE_OPEN`.

## Frozen matrix

- source size: 1 MiB;
- authenticated leaf sizes: 80, 96, 112, 192 bytes;
- requests per leaf size: first 4 KiB, middle 4 KiB, final 4 KiB, middle 64 KiB;
- 21 paired alternating repetitions after two warmups;
- deterministic source bytes.

Total decisive cells per pipeline: 16.

## Timed boundaries

`proof_extract` includes creation of the complete generic `RangeProof`, including requested leaf-payload slicing and sibling tuple construction.

`verify` includes leaf hashing, sibling ingestion, parent reconstruction, root commitment check, payload join, requested-range slicing and output validation through unmodified `verify_range()`.

Tree construction, native compilation and source generation are outside these stage timers.

A separately timed composed open (`prove -> verify`) is retained as an audit. Stage-sum/composed ratios are evidence, not a promotion threshold.

All owning references from a preceding arm must be cleared before clocks start; current outputs remain alive until clocks stop.

## Semantic / traffic gates

Every row requires:

- reference and packed roots equal;
- reference and packed interval `RangeProof` objects exactly equal;
- both verifiers return exactly the requested source bytes;
- packed proof reads exactly one 32-byte digest per emitted sibling (enforced independently in semantic tests);
- matrix identity and uniqueness exact.

Any failure returns `INVALIDATE_AUTH_SELECTIVE_OPEN_STAGE_OWNER`.

## Claim boundary

This profiler does not prove product filesystem I/O, sidecar placement, page-cache behavior, peak RSS, remote-range economics, portability, failure isolation, or a canonical format change. It only allocates the next research optimization budget inside the current in-memory generic authenticated selective-open path.
