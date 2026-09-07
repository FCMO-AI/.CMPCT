# ONE-G0.2 auth-tree packed one-shot SHA preregistration

**Frozen before result-bearing execution.**

## Mission lock / Referee

Existing native auth-tree evidence shows the exact ONE research tree is no longer catastrophically slow in C/OpenSSL, but still costs about 2.68x–5.07x a whole-root SHA pass. At the balanced 112-byte leaf it costs about 4.10x–4.20x while presenting only ~1.86x source-equivalent bytes to SHA. The receipt identifies per-node init/finalize and tiny-message API overhead as the remaining native creation debt and explicitly names batching/multi-buffer work as the next engineering direction.

This experiment asks one narrower causal question before attempting SIMD or parallel multi-buffer SHA:

> Can the exact existing leaf/parent/root messages be packed contiguously and hashed with one one-shot SHA256 call per node, instead of multiple SHA256_Update calls per node, while preserving byte-identical roots and materially reducing exact-tree creation time?

This changes no authenticated information, tree grammar, leaf geometry, proof bytes, commitment width, reader semantics, security primitive or canonical format. It is writer-only compute work.

## Frozen baseline

The committed `one_g02_auth_tree_openssl.c` grammar:

- leaf message: `"ONE-L\\0" || le64(index) || le64(total) || payload`;
- parent message: `"ONE-P\\0" || le32(level) || left32 || right32`;
- root message: `"ONE-R\\0" || le64(total) || le32(leaf_bytes) || tree_root32`;
- SHA-256 commitments remain 32 bytes;
- binary tree, duplicate-right behavior and root commitment remain exact.

Baseline uses `SHA256_Init` + multiple `SHA256_Update` calls + `SHA256_Final` for every node.

## Frozen candidate

Candidate forms the exact same message in bounded contiguous scratch and invokes one-shot `SHA256(message, len, out)` once per node. Maximum leaf scratch is `6 + 16 + 192 = 214 B` on the frozen matrix; parent scratch is 74 B; root scratch is 50 B. No persistent state is added.

No leaf-size tuning, fanout change, digest truncation, proof change or row-specific dispatch is allowed after results.

## Frozen matrix

Deterministic roots:

- 64 KiB and 256 KiB;
- leaf widths 80, 96, 112 and 192 bytes;
- 31 repetitions per row;
- alternating baseline/candidate order per repetition after equivalent warm-up.

The exact deterministic data generator and independent Python auth-tree evaluator used by the existing native profile remain the semantic oracle.

## Required evidence

For every row:

1. baseline root == candidate root;
2. both roots == independent Python `experiments.one.auth_tree` root;
3. identical node count and tree geometry;
4. baseline/candidate median native elapsed;
5. candidate/baseline ratio;
6. no extra persistent state; bounded scratch reported explicitly.

Strict C build: `-std=c11 -O2 -Wall -Wextra -Werror`.

## Frozen decision gate

This is a native auth-tree creation optimization, not product promotion.

Advance packed one-shot as the auth-tree creation baseline only if all conditions hold:

- zero root/geometry mismatches;
- median candidate/baseline across all 8 rows <= **0.85x**;
- balanced 112-byte rows at both sizes <= **0.90x**;
- no row > **0.98x**.

Otherwise reject this shape as insufficient. Do not rescue it with leaf-size thresholds, size dispatch, digest truncation, changed tree fanout or relaxed authentication.

A PASS grants authority only to replace the per-node hashing call shape in the exact existing research auth tree. It does not prove end-to-end ingest, authenticated-range, release, native portability or v0.29/v0.30 superiority. A later full authenticated-placement/ingest gate must still charge tree creation, proof/index bytes, selective reads and writer work.

## Hostile reviewer / disproof

The primary disproof is that packing/copying tiny node messages costs as much as the removed Update-call overhead, producing >=0.85x median or any regression row. Another disproof is any root mismatch, which is terminal regardless of speed.

Security, integrity and recovery are non-borrowable. SHA-256, commitment width, tree grammar and proof semantics are frozen.
