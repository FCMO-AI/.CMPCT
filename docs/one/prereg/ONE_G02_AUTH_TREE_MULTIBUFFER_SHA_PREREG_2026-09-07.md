# ONE-G0.2 authentication-tree true multi-buffer SHA-256 preregistration

**Frozen before result-bearing hosted execution.**

## Mission lock / Referee

Two exact hosted scalar experiments have now narrowed the authentication-tree creation debt:

1. packing each exact node message and replacing low-level SHA updates with OpenSSL's high-level one-shot `SHA256()` was catastrophically slower (3.5034x median candidate/baseline);
2. cloning pre-seeded low-level `SHA256_CTX` state removed almost all repeated prefix initializations but improved median elapsed only ~1.75%, with a 2.39% regression row.

The remaining hypothesis is therefore not about call count. It is about executing the SHA-256 compression work of **independent same-level nodes in parallel lanes**.

Intel Multi-Buffer Crypto for IPsec v2.0 is used here only as a mature external research oracle/prototype for this mechanism. Its SHA-256 hash-burst API schedules independent jobs through architecture-specific multi-buffer machinery. It is not being adopted as a CMPCT dependency, format requirement, reader requirement, portability authority or release component by this experiment.

> **Hypothesis:** true same-level multi-buffer SHA-256 can overcome both scalar per-node overhead and the explicit staging needed by the prototype API, materially reducing exact ONE authentication-tree creation time while preserving every authenticated byte and root.

## Frozen baseline

Baseline is the existing exact low-level OpenSSL tree:

- leaf message: `"ONE-L\\0" || le64(index) || le64(total) || payload`;
- parent message: `"ONE-P\\0" || le32(level) || left32 || right32`;
- root message: `"ONE-R\\0" || le64(total) || le32(leaf_bytes) || tree_root32`;
- SHA-256 commitments are 32 bytes;
- binary tree, duplicate-right behavior and explicit root commitment are unchanged.

Baseline timing includes its normal tree allocations and scalar SHA calls.

## Frozen candidate

Candidate uses Intel Multi-Buffer Crypto for IPsec **v2.0** (`v2.0` release tag) and its checked SHA-256 hash-burst API for independent nodes at each tree level.

Because the public burst interface accepts one contiguous message pointer per job, the candidate must explicitly materialize the exact authenticated message bytes into bounded batch arenas. **All staging, arena allocation, job setup, manager submission and output handling remain inside the timed candidate build.** No staging traffic may be subtracted from elapsed time.

Candidate rules:

- leaf, parent and root message bytes must be byte-for-byte identical to baseline;
- same tree geometry and node order;
- no digest truncation;
- no fanout/leaf-width change;
- no proof/index/reader change;
- no OpenSSL fallback for leaf/parent nodes after timing starts merely to rescue a slow row;
- process arbitrarily large levels in bounded bursts no larger than the library's declared burst capacity;
- report explicit staged message bytes and staged/source ratio.

The multi-buffer library/manager initialization and one-time shared-library build/install are **outside** each timed tree build, analogous to process/library initialization rather than per-archive creation. Per-tree buffers/jobs and all message materialization are inside the timer.

## Frozen matrix

Deterministic roots:

- 64 KiB and 256 KiB;
- leaf widths 80, 96, 112 and 192 bytes;
- 31 repetitions per row;
- alternating baseline/candidate timing order after equivalent warm-up.

The independent Python `experiments.one.auth_tree` evaluator remains the semantic oracle.

## Required evidence

For every row:

1. baseline root == candidate root == independent Python root;
2. identical node geometry;
3. baseline median elapsed;
4. candidate median elapsed;
5. candidate/baseline ratio;
6. explicit staged bytes and staged/source ratio;
7. burst capacity and runtime architecture/features exposed by the library where practical;
8. exact external prototype version provenance.

The external library must be built from the immutable v2.0 tag in the hosted workflow, not from its moving main branch.

## Frozen decision gate

Advance **multi-buffer same-level hashing as a research mechanism** only if all conditions hold:

- zero root/geometry mismatches;
- median candidate/baseline across all 8 rows <= **0.80x**;
- both balanced 112-byte rows <= **0.85x**;
- no row > **0.95x**.

Otherwise reject this staged public-burst prototype as insufficient. Do not rescue it with leaf-size dispatch, weakened authentication or threshold selection after the result.

A PASS does **not** authorize Intel Multi-Buffer as a permanent dependency. It establishes only that same-level cryptographic lane batching is worth implementing behind ONE's own optional/native dispatch boundary. Before product authority, a portable scalar fallback, feature detection, exact semantic vectors, CPU-time/memory accounting, non-x86 strategy and broader ingest measurement remain mandatory.

## Hostile reviewer / disproof

The most likely disproof is that the public burst API's required message packing and job setup consume enough memory traffic/control overhead to erase the SIMD/pipelining benefit at ONE's tiny node sizes. Another disproof is that runner hardware selects a scalar/SHA-NI path whose lane batching does not materially beat OpenSSL.

Any root mismatch is terminal regardless of speed. If the staged prototype fails narrowly while showing a strong kernel-only signal, preserve that distinction but do not call the candidate a pass; the next mechanism would need a custom scatter/gather or pre-seeded multi-lane kernel that avoids complete-message staging.
