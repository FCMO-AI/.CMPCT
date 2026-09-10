# CMPCT1 / ONE Genesis selective-request plan preregistration — 2026-09-09

Experimental state: **ONE-G0.2**  
Purpose: freeze selective-read requests before the September 11 scored comparison.  
Hard boundary: **request generation may inspect only the accepted uncompressed source tree. It must not inspect any contender archive layout, Law graph, chunking, index or score.**

## Hypothesis / bias-control objective

A fair selective-access gate should ask every contender for identical `(logical path, offset, length)` ranges chosen independently of its physical layout. If requests are selected after observing archive chunk boundaries, reconstruction cones or hot paths, the benchmark can manufacture locality wins.

## Source substrate

Use the same accepted 15-workload portable substrate as Genesis readiness:

- 10 `neutral_hostile_v1` workloads normalized by accepted repair-v6;
- 5 `resemblance_hostile_v1` workloads;
- exact source-tree identity recorded per workload before request selection.

## Target-file selection

For each workload, consider non-empty regular files only and sort deterministically by `(size descending, relative POSIX path ascending)`.

Select at most two distinct targets:

1. **largest** — first file in that ordering;
2. **small-window** — the smallest file whose size is at least 4096 bytes, ties by relative path, when it is not already the largest target.

This intentionally covers a large-object locality case plus a smaller independently addressable object without using filename extensions, content class labels or contender layout.

If a workload contains no non-empty regular file, retain an explicit no-request row rather than inventing a zero-cost selective measurement.

## Range geometry

For each selected target, derive requests only from logical file length `N`:

- `prefix64`: `(0, min(64, N))`;
- `prefix4k`: `(0, min(4096, N))`;
- `middle4k`: centered 4096-byte window when `N > 4096`, otherwise the complete file;
- `cross4k`: when `N > 4160`, a 128-byte request centered across logical offset 4096 (`start=4032`); otherwise omit it;
- `suffix257`: final `min(257, N)` bytes.

Deduplicate identical `(offset,length)` requests caused by small targets, preserving the order above.

The 4096 crossing is **logical-coordinate geometry only**. It is not synchronized with any contender's physical chunk/Merkle/block boundary. If a contender happens to align there, that is part of its own representation behavior, not benchmark knowledge.

## Required plan identity

Every request row records:

- suite/workload;
- source `tree_sha256`;
- target role and relative path;
- full logical file length and SHA-256;
- request name, offset and length;
- SHA-256 of the expected returned logical bytes.

This freezes both query geometry and exact answer before archives exist.

## Disproof / HOLD

The plan is invalid if:

- it does not regenerate the accepted repair-v6 15-workload substrate exactly;
- any request is out of bounds, empty or depends on archive output;
- request bytes/hash cannot be reproduced from the source tree;
- target/path ordering is nondeterministic;
- changing a contender implementation can change the request plan while source bytes remain fixed;
- generation performs any CMPCT1/v0.29/v0.30 encoding or scoring.

## Gate use

On September 11, every contender receives the same frozen requests for a workload. Implementations may expose different integrity/locality semantics; those differences must be classified under the Genesis measurement contract and their actual touched/decoded/proof work charged honestly. An unavailable selective operation is `unavailable`, never zero cost.
