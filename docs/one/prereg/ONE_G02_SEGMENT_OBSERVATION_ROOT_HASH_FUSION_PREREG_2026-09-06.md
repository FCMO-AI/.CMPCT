# ONE-G0.2 segment-observation + current-root hash fusion — preregistration

## Mission Lock / Referee

### Causal predecessor
`ONE_G02_PLAN_CARRIED_CURRENT_ROOT_HASH_RESULT_2026-09-06.md` rejected per-segment SHA carry. Semantic identity was exact, controls were near parity, but fragmented productive plans paid ~1.31x because hash-update/control count scaled with Law fragmentation.

This experiment does **not** rescue that mechanism with a threshold. It tests a causally different implementation in which SHA update boundaries are fixed regular blocks and therefore independent of segment count.

### Question
The current ordinary research envelope performs native one-pass maximal segmentation and, separately, a whole-target SHA-256. Can one native traversal own segmentation while advancing current-root SHA in coarse contiguous target blocks, preserving the exact Segment plan and digest, without paying more compute than the two independent calls?

### Baseline
For each frozen input:
1. authoritative `one_g02_segment_plan_one_pass(source, target)`;
2. native OpenSSL EVP SHA-256 over the entire target.

Both operations are inside the timed baseline region.

### Candidate
One native function reproduces the exact one-pass maximal segmentation algorithm. As logical scan progress passes fixed **16 KiB** boundaries, it feeds only completed contiguous target blocks to one EVP SHA-256 context; a final tail update completes the digest. Hash update count is `ceil(target_len / 16 KiB)`, independent of Segment fragmentation.

The candidate is still allowed to reread bytes inside OpenSSL; this falsifier asks whether eliminating the separate traversal boundary and keeping those rereads temporally local has meaningful marginal value. It does not claim a magical one-load SHA implementation.

### Frozen matrix
Use the existing ONE-G0.2 relation generator at 4, 8, 16, 32, 64, 128 and 256 KiB across:
- `shift_plus1`;
- `shift_plus1_damage_quarter`;
- `fragmented_every96`;
- `fragmented_every32` hostile false-pattern/control;
- `independent_random` hostile/control.

All rows execute segmentation in both arms here, deliberately stress-testing the fused primitive even where an upstream opportunity gate would normally avoid it.

### Semantic disproof gates
- candidate Segment array == baseline Segment array byte-for-byte for all emitted entries;
- segment stats identical;
- candidate digest == baseline native digest == Python SHA-256;
- exact target coverage; no changed source/target buffers;
- strict C warnings-as-errors build;
- current ONE semantic/hostile test suite green.

Any semantic mismatch invalidates the experiment.

### Performance method
101 alternating A/B-B/A rounds after untimed warm-up. Charge EVP context init/finalization, segmentation, fixed-block control and hashing to their respective arms.

### Advance gate
Advance to the broader ingest/writer envelope only if all hold:
- mature (>=16 KiB) all-row median candidate/baseline <= **0.97x**;
- mature productive median <= **0.96x**;
- mature fragmented (`every96` + `every32`) median <= **0.98x**;
- no mature row > **1.05x**.

No block-size tuning after observing the result. The 16 KiB boundary is frozen for this falsifier. A later implementation may revisit block size only if another already-required observation block size becomes canonical for independent reasons.

### Disproof meaning
Failure means merely interleaving a cryptographic reread with segmentation is not enough; ordinary current-root hashing should remain a separate regular bulk operation until a genuinely shared fused-observation kernel can consume the same loaded vectors for both purposes.

### Claim boundary
Native segmentation + current-root observation component only. No Program construction, canonical emission, authenticated placement, full ingest, RSS, selective access, recovery, arbitrary discovery, comparator or release authority.
