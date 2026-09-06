# ONE-G0.2 shared native writer exact-capacity build evidence — 2026-09-06

Status: **BUILT / NOT YET RESULT-BEARING**. This is not a promotion receipt.

## Authority

- Branch: `research/cmpct1`
- Starting campaign HEAD for this activation: `3ac294defd4183dfb43c4d0d086aaa79083fd0fb`
- Preregistration: `docs/one/prereg/ONE_G02_SHARED_NATIVE_WRITER_EXACT_CAPACITY_PREREG_2026-09-06.md`
- Seed writer: `benchmarks/one/native/one_g02_shared_native_writer_ref_fused.c`
- Builder/oracle: `benchmarks/one/native/one_g02_exact_wire_size.c`
- Smoke workflow: `.github/workflows/one-g02-exact-wire-size-smoke.yml`

## Falsifiable mechanism

The current ref-fused writer completely validates Segment metadata, then requests a conservative output allocation:

`4096 + 64*segment_count + 64*intermediate_nodes + source_len + target_len`.

Canonical ONE0 byte length is already determined by the validated node/ref/root metadata plus Surprise lengths. The Builder therefore computes the exact encoded length without reading source or target payload bytes. This is a writer resource experiment only: no reader-visible mechanism, opcode, Law, Surprise, hierarchy or canonical byte choice changes.

The preregistered claim deliberately distinguishes **requested allocation capacity** from physical RSS. A smaller `malloc` request is not itself evidence of a resident-memory win.

## Builder state

The exact-size oracle now counts:

- `ONE0` magic and resource limits;
- node count;
- source and target/segment Surprise node encoding;
- Ref varints and lengths;
- generic concat hierarchy and final concat;
- sorted `current` / `previous` roots and 32-byte digests.

The common `segment_count <= ONE_MAX_NODES` path counts concat refs directly from Segment metadata and does not allocate an intermediate ref array. The generic hierarchy path is retained for the canonical bound case.

## Hostile Reviewer finding: acceptance-domain drift

The first Builder draft had a serious semantic/resource flaw even though its byte counting could be correct: exact canonical wire length can fit under `ONE_MAX_WIRE` for an input whose seed writer rejects because the seed's deliberately loose `checked_cap()` exceeds `ONE_MAX_WIRE`.

Using exact capacity as the sole acceptance gate would therefore silently broaden the seed writer's accepted domain. That violates the preregistered same-semantics requirement and would turn an allocator experiment into an unreviewed resource-semantics change.

This was caught before promotion. The hardened oracle now mirrors the seed `checked_cap()` overflow and `ONE_MAX_WIRE` acceptance boundary first, then computes exact length only inside that same accepted domain. A future change to the resource contract may reconsider this conservatism, but this experiment does not.

## Planned parity coverage

The smoke harness is configured for strict C (`-std=c11 -O2 -Wall -Wextra -Werror`) and checks the seed writer against the exact-size oracle for:

- fixed mixed Ref/Surprise plan;
- disabled full-Surprise path;
- all-Surprise plan;
- 1000 deterministic randomized valid segment partitions;
- a >4096-segment hierarchy case;
- hostile unknown kind, zero-length segment and incomplete coverage rejection.

For accepted plans it requires exact parity of emitted wire length, Surprise bytes, hierarchy depth and node count; the seed allocation must be no smaller than emitted length.

## CI truth

**No result-bearing exact-capacity workflow run has been observed for the Builder commits in this activation.** The GitHub Actions query for the hardened smoke commit returned zero runs/check contexts. Connector-authored commits therefore cannot be treated as having passed CI merely because no red check exists.

The first smoke draft also contained a harness-only scalar-initializer form that would fail the workflow's own `-Werror` policy. It was corrected and the parity matrix expanded, but the corrected workflow still has no observed result-bearing run at the time of this receipt.

Accordingly:

- no semantic pass is claimed yet;
- no requested-capacity reduction distribution is claimed yet;
- no elapsed ratio is claimed yet;
- no RSS reduction is claimed yet;
- no promotion decision is made.

## Next decisive action

Obtain an exact-source execution path for the hardened parity harness. If parity passes, integrate exact sizing into a candidate copy of the ref-fused writer while preserving the seed acceptance gate, then run the preregistered full matrix reporting seed requested capacity, exact requested capacity, emitted bytes, elapsed, and peak RSS only where measured robustly.

If the exact-count bookkeeping materially regresses full-writer elapsed or the real allocator/RSS effect is negligible, preserve the negative rather than adding size/density dispatch.
