# Mosaic v0.29 attempt #7 — Cross-Base Residual Program Packing

Status: **preregistered research / no v0.29.0 claim**.

## Mission

Attempt #5 introduced bounded Residual Program Packing but groups one-base delta programs by direct
`base_id` before physical packing. CMPNX11 does not require that restriction: each `delta_pack`
descriptor already stores its own direct `base_id`, residual record id, recipe slice offset/length,
target length and target hash. The unchanged reader authenticates the physical record, slices one
recipe, and only then decodes that recipe against the descriptor's own direct base.

Attempt #7 asks whether removing the **encoder-only same-base grouping restriction** can materially
increase residual-stream compression while preserving the exact attempt-5 reader, dependency depth,
integrity/recovery model, 256 KiB residual-record ceiling and <=2x additional recipe over-read.

## Why the bar is high

The accepted attempt #5 hostile structural aggregate is **47,147,764 B**. The latest same-run structural
evidence measured tar+Zstd-19 at **47,065,652 B** and ZPAQ m5 at **47,062,643 B**. Merely saving a few
physical headers is not a revision-sized result: attempt #7 must exploit shared recipe entropy strongly
enough to cross the mature size competitors with margin.

## Frozen structural gate

On one freshly generated `resemblance_hostile_v1` aggregate consumed by every tool in the same job,
attempt #7 survives only if all are true:

- exact attempt #7 archive is **strictly smaller than exact attempt #5** on the same tree;
- the selected encoder plan contains at least **one genuinely mixed-base residual group** with at least
  two members, so any byte claim is causally attributable to the new mechanism;
- unchanged attempt-5 reader strong-verifies the selected archive;
- `delta_pack` dependency depth remains exactly one direct base;
- residual physical records remain **<=256 KiB**;
- additional recipe over-read remains **<=2.0x for every member**;
- tar+Zstd-19 and ZPAQ m5 both produce positive same-run measurements;
- CMPCT is strictly smaller than both competitors; and
- CMPCT finishes at least **16 KiB smaller than the strongest of those two competitors**.

Given the preserved attempt-5 bytes, the latest same-run evidence implies roughly **101.5 KiB** of
additional saving would be needed if competitor bytes reproduce exactly. That number is context, not a
stale-byte acceptance rule; only the new same-run measurements decide the gate.

## Experimental policies fixed before execution

Two deterministic physical orderings are allowed:

1. `target`: stable target-id order, independent of base identity.
2. `recipe-prefix`: first 32 bytes of the already-generated delta recipe, then recipe size / target id /
   base id as stable tie-breakers. Delta recipes are opcode/varint streams, so this is a cheap structural
   similarity hint rather than a trained workload classifier.

For each ordering, the existing frozen residual limits (4, 8, 16, 32, 64, 128, 256 KiB) are auditioned.
The existing real compressor determines physical cost. The accepted attempt-5 plan wins **all estimated
byte ties**, even when a cross-base plan has lower read amplification; changing physical layout for zero
estimated byte gain is out of scope. The accepted attempt-5 artifact is built independently and remains
the final byte-for-byte fallback.

The oracle records the winning strategy, limit, estimated net saving, mixed-base group/member counts and
whether cross-base planning actually displaced the same-base planner. A smaller artifact without those
causal diagnostics cannot satisfy the gate.

## Disproof

Reject attempt #7 if it misses the structural margin, if gains arise only from a stale competitor
comparison, if no mixed-base pack actually caused the selected artifact, if any locality/integrity
invariant changes, or if a new reader grammar would be required. A clean miss is durable evidence and
should move the campaign to a different representation hypothesis (for example a bounded columnar
residual oracle or proven-redundant integrity metadata), not to looser thresholds.

## Claim boundary

A pass would show that cross-base physical recipe co-location is a meaningful encoder improvement. It
would still not authorize v0.29.0: creation-cost admission, canonical reader/native parity, recovery,
portable benchmark identity, and release-performance evidence remain separate gates.
