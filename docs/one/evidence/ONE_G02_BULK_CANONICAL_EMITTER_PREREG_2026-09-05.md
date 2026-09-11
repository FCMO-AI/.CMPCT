# ONE-G0.2 bulk canonical emitter — preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2
Authoritative branch: `research/cmpct1`
Parent evidence: post-segment control cost-owner run `33991674157`, job `101374903105`, artifact `9976832534`.

## Mission Lock / Referee

The exact-head cost-owner experiment established that, after segment discovery is removed from the timed region, ordinary canonical encoding dominates Program graph construction on all 21 productive relation rows and all seven tested size classes. Within the encode boundary, prevalidated canonical byte emission owns a median 0.7854046845 share while validation owns 0.2145953155. The frozen terminal decision was `advance_bulk_canonical_emitter`.

The next causal question is therefore not whether validation can be weakened and not whether the ONE graph should change. It is whether the exact current ONE0 canonical bytes can be emitted with materially less Python allocation/copy overhead by sizing once, allocating one output buffer, and writing varints/refs/blobs directly into that buffer.

## Falsifiable hypothesis

For already-valid Programs, a sized single-buffer canonical emitter can preserve byte-for-byte ONE0 output and WireStats while reducing prevalidated emission elapsed time materially across literal controls and generic Ref/Surprise relation Programs.

Mechanism: the baseline repeatedly creates small bytearrays/bytes for every varint, ref and node and then appends them into larger bytearrays. The candidate computes exact wire size, allocates one bytearray, and fills it in place. It does not alter validation, canonical ordering, tags, varints, roots, integrity bytes, ONE operations or reader semantics.

## Hard invariants

- `encode_program(candidate_program)` bytes are the canonical authority.
- Candidate bytes must be byte-for-byte identical for every row.
- Candidate `WireStats` must be identical.
- Full `decode_program -> evaluate` reconstruction remains exact.
- Existing six-op ONE grammar only.
- No validation or hostile-input check is removed from the normal public candidate entrypoint.
- The benchmark may use an explicitly prevalidated internal entrypoint only to isolate emission cost, matching the parent cost-owner experiment.
- No format revision and no project-version change.

## Frozen envelope

Reuse the post-segment matrix:

- sizes: 4, 8, 16, 32, 64, 128, 256 KiB;
- productive: `shift_plus1`, `shift_plus1_damage_quarter`, `fragmented_every96`;
- controls: `fragmented_every32`, `independent_random`;
- 51 rounds per timed path;
- include the 256 KiB hierarchy-required hostile row.

Add direct semantic vectors for all six ONE operations and multiple canonically sorted roots so the candidate is not relation-shape-specific.

## Promotion / retirement law

Semantic gate is absolute: any byte, stats, decode/reconstruction, cap or operation mismatch => `retire_bulk_canonical_emitter`.

Performance promotion requires all of:

1. median candidate/baseline prevalidated emission ratio across the 21 productive rows <= 0.80;
2. at least 18/21 productive rows <= 0.90;
3. all seven size-class medians <= 0.90;
4. no productive row > 1.03;
5. literal/false-pattern controls remain byte-exact and no control size-class median > 1.03.

If exactness passes but these timing gates fail, preserve the negative result and do not tune corpus thresholds. Re-profile allocation/copy ownership or move the same mechanism to native implementation only if evidence justifies it.

## Claim boundary

Passing establishes a Python research-harness emission optimization and stronger causal evidence for bulk canonical construction. It does not establish native/product writer throughput, arbitrary relation discovery, authenticated selective reads, recovery, portability supremacy, or superiority over frozen v0.29/deferred-v0.30.