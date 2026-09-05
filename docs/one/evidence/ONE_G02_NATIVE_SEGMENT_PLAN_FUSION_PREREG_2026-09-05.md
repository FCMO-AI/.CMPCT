# ONE-G0.2 — native damaged-relation segment-plan fusion preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2
Status: frozen before result-bearing execution

## Mission lock

The minimal-overflow representation passed all frozen density and reader-resource gates, but reference-Python construction remained roughly 9x–65x literal. This experiment attacks one concrete creation-cost owner without changing reader semantics: producing the exact maximal `+1` match/mismatch segment plan required by the generic `Ref + Surprise + concat` compiler.

The candidate is one native streaming pass that emits the plan as it observes bytes. The baseline is a native two-pass implementation that first counts exact segment boundaries, then rescans the same bytes to emit the identical plan. Pair identity and the already-proven relation admission decision are outside this microbenchmark; neither implementation performs reader discovery.

## Falsifiable hypothesis

For the frozen damaged productive relations, a one-pass emitter will produce a byte-for-byte identical segment plan to both the two-pass native baseline and an independent Python oracle while materially reducing input traffic and elapsed time.

## Frozen corpus

Sizes: `4, 8, 16, 32, 64, 128, 256 KiB`.
Cases: `shift_plus1_damage_quarter`, `fragmented_every96` from the existing frozen relation generator.

## Plan semantics

Each segment is `(kind,start,length)`, where kind 0 is a ranged source ref and kind 1 is Surprise. For a ref segment, `start` is the source offset. For Surprise, `start` is the target offset. Adjacent segments of the same kind are impossible by maximality. The plan does not become a wire format or reader operation; it is transient writer state consumed by the already-passed generic ONE compiler.

## Frozen gates

- exact plan equality: one-pass native == two-pass native == independent Python oracle on all 14 rows;
- exact segment count and covered length on all rows;
- no plan buffer overflow and no input mutation;
- logical input comparison traffic: candidate exactly one target-length scan; baseline exactly two target-length scans;
- candidate logical scan traffic <=0.51x baseline on every row;
- for sizes >=16 KiB, candidate median elapsed <=0.70x baseline on every row;
- no row may exceed 1.03x baseline elapsed;
- candidate transient plan bytes must equal baseline plan bytes; no extra persistent state.

Timing: 101 interleaved rounds after warmup, native `-O3`, same preallocated output buffers. Python allocation, ctypes conversion and oracle work stay outside timed regions.

## Disproof

Any equality failure retires the fused emitter immediately. A timing failure with exact plans preserves representation viability but means one-pass segmentation is not a useful native cost reduction on this implementation. Do not tune corpus spacing, size boundaries, or timing thresholds after result.

## Claim boundary

A pass establishes only a native writer-side segment-plan construction improvement. It does not include relation admission, generic Program allocation/wire encoding, arbitrary pair discovery, product creation speed, or v0.29/v0.30 comparison.
