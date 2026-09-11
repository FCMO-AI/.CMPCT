# ONE-G0.2 native Segment SWAR scan — preregistration

Date: 2026-09-06  
Branch: `research/cmpct1`  
Experimental line: `ONE-G0.2`

## Mission Lock

Exact phase attribution on the ref-fused shared-native writer identifies native one-pass segmentation as the second stable simple-relation owner: median **28.88%** of full elapsed on mature `shift_plus1`, >=15% on 5/5 sizes. The larger root-hash owner was attacked first as preregistered; exact per-call two-root threading is a negative seed and must not be rescued by a large-file dispatcher.

The current segmenter is semantically good but scalar: for every target byte it evaluates `target[i] == source[i-1]` and advances one byte at a time until that Boolean changes. Long Ref and long Surprise runs therefore pay one branch/test per byte even though their run class is stable.

## Falsifiable hypothesis

A semantics-identical word-at-a-time classification scan can skip eight bytes at once when their classification is provably uniform:

- Ref run: load 8 target bytes and the corresponding 8 shifted source bytes; `xor == 0` proves all eight are Ref bytes;
- Surprise run: use a standard SWAR zero-byte predicate on the XOR word; absence of any zero byte proves all eight are Surprise bytes;
- otherwise fall back to the exact scalar byte transition for the mixed word and tail.

The Segment grammar, `start`, `length`, `kind`, coverage and ordering remain byte-exact. The optimization is universal and data-dependent only on the same equality predicate that defines the Segment; there is no size/workload/corpus/speed dispatcher.

## Disproof

Reject if any Segment differs from the scalar oracle, any hostile unaligned/tiny/mixed case fails, or mature speed does not show enough headroom to matter to the 28.88% full-path owner. Do not add a threshold to rescue it.

If exact but economically weak, retire word-level segmentation speed work and move to broad pass fusion/overlap instead of adding more local cleverness.

## Frozen arms

Baseline: exact current native scalar segmenter from `one_g02_native_segment_plan_fusion_kernel.c`.

Candidate: same ABI and `SegmentStats`, replacing only byte-at-a-time run advancement with 64-bit SWAR uniform-run skips plus scalar mixed/tail handling.

Both receive already-materialized immutable source/target byte buffers and a preallocated Segment output buffer. Allocation is outside both arms because the full writer already reuses this buffer; all scanning and Segment writes are charged.

## Matrix

Sizes: 1, 7, 8, 9, 31, 32, 63, 64, 65 B for semantic/tail vectors, plus 4/8/16/32/64/128/256 KiB performance sizes.

Frozen productive relation families from the current relation matrix:

- `shift_plus1`;
- `shift_plus1_damage_quarter`;
- `fragmented_every96`.

Hostile synthetic classification families at each relevant size:

- all Ref after byte 0;
- all Surprise;
- alternating Ref/Surprise every byte;
- transition every 7 bytes (crosses 8-byte boundaries);
- transition every 8 bytes;
- deterministic pseudo-random equality mask;
- unaligned source/target views offset by 1 where the harness can provide them safely.

## Correctness / instrumentation

- candidate Segment tuple stream must exactly equal scalar baseline for every vector/row;
- `segments` and `compared_target_bytes` must be identical;
- coverage must equal target length and every segment must have positive length;
- preserve the existing independent Python Segment oracle on the three repository productive families;
- report input bytes, segment count, scalar/candidate median ns, candidate/scalar ratio and ns/input-byte.

## Timing

- 63 paired rounds per performance row;
- alternating baseline/candidate A/B-B/A;
- GC disabled during timed pairs;
- same preallocated buffers and same call boundary;
- semantic/tail vectors need not be timed for promotion.

## Frozen gate

Correctness: zero mismatches across all repository and hostile rows.

Mature performance (>=16 KiB) across the three repository productive families:

- median candidate/scalar <= **0.55x**;
- every mature productive row <= **0.85x**;
- `shift_plus1` mature median <= **0.45x**;
- no tested performance row, including hostile classification patterns, > **1.10x**.

State/resource: no heap allocation inside the candidate kernel; output capacity/state identical to scalar baseline; fixed scalar tail only.

## Promotion boundary

Passing this microkernel gate promotes only the SWAR Segment scanner to a full ref-fused writer A/B. It does not itself promote writer speed, reader changes, stored bytes, product use, v0.29/v0.30 comparison or the Genesis gate.