# ONE-G0.2 direct generic-control streaming — preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2

## Mission lock / referee

The frozen native segment-plan fusion removed a redundant full target scan, but it still writes a transient `Segment[]` and the next writer stage must read that plan again. On fragmented relations that transient structure can be large (65,568 B in the 256 KiB `fragmented_every96` corroboration run).

**Hypothesis:** once a maximal Ref or Surprise run has been observed, its generic control record can be emitted immediately. Streaming identical control bytes should eliminate transient plan write/read traffic while preserving the exact same Ref+Surprise decomposition.

This is a writer implementation experiment, not a new ONE opcode or wire-format proposal. The research control stream is deliberately simple and deterministic so candidate and baseline can be compared byte-for-byte:

- record: 1-byte kind + LE32 start + LE32 length;
- Ref record contains no payload;
- Surprise record is followed by exactly `length` target bytes.

The baseline uses the already-promoted one-pass segmenter to materialize a `Segment[]`, then encodes this stream from the plan. The candidate scans source/target once and emits the same stream when each maximal run closes, with no segment array.

## Frozen corpus

Deterministic relation sizes: 4, 8, 16, 32, 64, 128, 256 KiB.

Cases:
- `shift_plus1_damage_quarter`
- `fragmented_every96`

These are intentionally inherited unchanged from the native segment-plan gate so the only experimental variable is transient plan materialization/readback.

## Frozen gates

For every row:

1. baseline bytes == candidate bytes == independent Python oracle bytes;
2. decoded record coverage is exactly target length and Ref starts are exact;
3. neither input mutates and output capacity is never exceeded;
4. candidate target comparison traffic == baseline target comparison traffic == target length (one observation pass each);
5. candidate transient segment-plan bytes == 0;
6. baseline transient segment-plan bytes == `segment_count * sizeof(Segment)`;
7. candidate emitted bytes == baseline emitted bytes, so no density claim can be manufactured from implementation choice;
8. no row may exceed 1.03x baseline median elapsed;
9. for `fragmented_every96` at sizes >=16 KiB, candidate median elapsed must be <=0.90x baseline;
10. median candidate/baseline elapsed across all 14 rows must be <=0.95x.

Timing protocol: native `-O3`, preallocated output and baseline plan buffers, 101 interleaved rounds after an untimed warmup. Output allocation is excluded from both timed regions; output writes are included equally.

## Disproof semantics

- Any byte/coverage/input mismatch retires the direct streaming emitter in this form.
- Exactness with timing failure preserves one-pass segmentation but falsifies the claim that eliminating the transient plan is worth a separate writer implementation at this layer.
- A failure on dense-damage rows alone does not authorize threshold tuning. The frozen all-row 1.03x cap still applies; a future opportunity gate would need its own independent causal argument.

## Claim boundary

A pass would establish only that generic Ref+Surprise control can be emitted directly from one native relation observation pass with lower transient writer traffic. It does not establish relation admission cost, arbitrary pair discovery, production ONE wire speed, authenticated persistence, reader speed, or superiority to v0.29/deferred-v0.30.
