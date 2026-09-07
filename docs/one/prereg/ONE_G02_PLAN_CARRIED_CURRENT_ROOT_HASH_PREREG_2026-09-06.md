# ONE-G0.2 plan-carried current-root hash — preregistration

## Mission Lock / Referee

### Question
The current root SHA-256 is presently charged as an independent whole-target pass before the adjacent-version research writer. A validated ONE segment plan already defines the current output in logical order: every Ref contributes a source range and every Surprise contributes the corresponding target range. Can the exact current-root SHA-256 be carried through that already-required logical plan traversal cheaply enough to justify eliminating the separate whole-target root-hash pass in a later integrated writer?

This is **not** a new ONE opcode, integrity scheme, reader behavior, or fallback codec. SHA-256 semantics remain byte-identical. This experiment is a native feasibility falsifier only; it does not promote a writer change.

### Falsifiable hypothesis
For the frozen adjacent-version relation matrix, native incremental SHA-256 over the validated Law+Surprise segment sequence produces exactly `SHA256(target)` and has sufficiently low incremental cost versus one native whole-target SHA-256 that an integrated writer experiment is warranted.

### Frozen matrix
Use the existing ONE-G0.2 relation-case generator and sizes 4, 8, 16, 32, 64, 128 and 256 KiB. Cover the three productive cases used by the direct-writer line (`shift_plus1`, `shift_plus1_damage_quarter`, `fragmented_every96`) plus `fragmented_every32` and `independent_random` controls. Productive cases use the authoritative native one-pass segment plan. Controls are represented as one full-target Surprise, matching the literal current-root semantics.

### Candidate
A native OpenSSL EVP SHA-256 context receives logical current bytes in segment order. Ref segments update from `source + start`; Surprise segments update from `target + start`. No payload is synthesized, copied or rediscovered. The segment plan is prebuilt and excluded from both hash timing arms because this falsifier asks only whether carrying SHA state through an already-required traversal has viable marginal cost.

### Baseline
One native OpenSSL EVP SHA-256 over the complete target buffer.

### Semantic gates
- candidate digest == baseline digest == Python `hashlib.sha256(target)` on every row;
- segment plan covers exactly the logical target length;
- productive native plan remains equal to the existing Python oracle;
- input buffers are unchanged.

### Performance disproof gate
Use alternating A/B-B/A medians after warm-up, 101 rounds per row.

Advance to an integrated writer falsifier only if all hold:
- mature productive (>=16 KiB) median candidate/baseline <= **1.05x**;
- every mature productive row <= **1.15x**;
- fragmented mature median <= **1.10x**;
- control mature median <= **1.08x**.

These are intentionally feasibility, not promotion, thresholds. A candidate near parity can still be useful when fused because the separate target-hash pass and its scheduling/cache boundary disappear. A materially slower segmented digest is rejected without thresholds based on segment count or case classification.

### Disproof meaning
Failure means the per-segment SHA update/control overhead consumes too much of the possible pass-elimination value in this form. Do not rescue it with a `segment_count` dispatcher. Reopen only if SHA state can be advanced in larger already-present canonical spans without adding a new classifier.

### Claim boundary
Native hash-carry feasibility after representation discovery only. No full-writer speed, RSS, selective-access, auth-tree, durability, arbitrary discovery, v0.29/v0.30 or release authority.
