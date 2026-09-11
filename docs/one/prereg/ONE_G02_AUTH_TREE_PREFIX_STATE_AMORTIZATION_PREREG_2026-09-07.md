# ONE-G0.2 authentication-tree SHA prefix-state amortization preregistration

**Frozen before result-bearing hosted execution.**

## Mission lock / Referee

The exact hosted packed-one-shot experiment rejected repacking each node into contiguous scratch: median candidate/baseline was 3.5034x and every row regressed materially while roots remained exact. That result shows that reducing API call count through extra message staging attacks the wrong cost boundary.

The surviving cost-owner hypothesis from the native profile is narrower: thousands of leaf and parent hashes repeatedly initialize SHA-256 and feed byte-identical domain prefixes (and, for parents, byte-identical level metadata within each tree level). Those bytes can be absorbed once into a seed context and the resulting SHA state copied into each independent node context, while the actual authenticated message remains exactly unchanged.

> **Hypothesis:** cloning pre-seeded SHA-256 contexts for repeated authentication prefixes/level headers removes enough per-node fixed work to reduce exact-tree native creation time without adding payload staging, changing tree geometry, or weakening authentication.

This is deliberately a cheap falsifier before true multi-buffer/SIMD hashing.

## Frozen baseline

Use the existing exact binary auth-tree grammar and low-level OpenSSL SHA-256 path:

- leaf: `"ONE-L\\0" || le64(index) || le64(total) || payload`;
- parent: `"ONE-P\\0" || le32(level) || left32 || right32`;
- root: `"ONE-R\\0" || le64(total) || le32(leaf_bytes) || tree_root32`;
- SHA-256 commitments: 32 bytes;
- binary tree and duplicate-right behavior unchanged.

Baseline performs ordinary `SHA256_Init`/`SHA256_Update`/`SHA256_Final` for every node.

## Frozen candidate

Candidate may only amortize invariant SHA prefix state:

1. initialize one leaf seed context per complete tree build after consuming exactly `"ONE-L\\0"`; clone that context for each leaf, then consume `le64(index) || le64(total) || payload` and finalize;
2. initialize one parent seed context per tree level after consuming exactly `"ONE-P\\0" || le32(level)`; clone it for each parent on that level, then consume `left32 || right32` and finalize;
3. root commitment may use an analogous seed after `"ONE-R\\0"` or the baseline path; it is one node and cannot decide the experiment;
4. context copies are ordinary bounded in-memory copies of `SHA256_CTX`; no candidate may copy/stage source payload bytes or child digests into a separate complete-message buffer.

No change is allowed to authenticated bytes, hash primitive, commitment width, tree fanout, leaf widths, proof semantics, node order, root semantics or reader representation.

## Frozen matrix

Deterministic roots:

- 64 KiB and 256 KiB;
- leaf widths 80, 96, 112 and 192 bytes;
- 31 repetitions per row;
- alternating baseline/candidate timing order after equivalent warm-up.

The independent Python `experiments.one.auth_tree` evaluator remains the semantic oracle.

## Required accounting

For every row preserve:

- baseline root;
- candidate root;
- independent expected root;
- exact node geometry;
- baseline median elapsed;
- candidate median elapsed;
- candidate/baseline ratio;
- number of baseline SHA initializations;
- candidate seed initializations;
- candidate context clones;
- candidate explicit payload-staging bytes, which must be exactly **0**.

Strict C build: `-std=c11 -O2 -Wall -Wextra -Werror` with the repository's existing OpenSSL deprecation suppression.

## Frozen decision gate

Advance prefix-state amortization as the exact-tree research baseline only if all conditions hold:

- zero root/geometry mismatches;
- explicit payload/message staging added by candidate = 0 bytes;
- median candidate/baseline across all 8 rows <= **0.96x**;
- both balanced 112-byte rows <= **0.98x**;
- no row > **1.00x**.

Otherwise reject this shape as too small or unstable to justify carrying into the broader ingest path. Do not rescue it with size/leaf dispatch or corpus thresholds.

A PASS grants authority only to reuse pre-seeded SHA state in this exact research auth-tree creator. It does not establish product portability because `SHA256_CTX` representation is library-specific, and it does not prove end-to-end ingest, authenticated-range, release or comparator superiority. A production/native ONE implementation would need an equivalent stable internal SHA state abstraction or a measured provider-native mechanism.

## Hostile reviewer / disproof

The strongest disproof is that copying `SHA256_CTX` merely replaces cheap initialization/update work with similar or worse state-copy/cache traffic, producing a median >0.96x or any regression row. Another disproof is any semantic mismatch, which is terminal.

If rejected, do not spend another cycle shaving calls around the scalar per-node API. Advance to true level batching/multi-buffer/vectorized SHA or another mechanism that amortizes cryptographic compression work itself.
