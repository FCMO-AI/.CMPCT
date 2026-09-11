# ONE-G0.2 observer-derived local certificate preregistration

## Mission Lock / Referee

The per-byte bottom-8 local Gear certificate carrying shape was rejected at exact source `56fc13f512266010bd0e61ae8ff509eb60770d9d`: mature median 3.358603x and worst mature 4.114829x versus the mandatory observer. The structural local-certification result remains useful, but the implementation paid for a second rolling recurrence and up to eight target hash checks per local window.

This experiment asks whether the same **content-local exact-nomination principle** can be derived from information the Gear observer already computes, rather than maintained as a second rolling signal.

### Hypothesis

For mandatory observer recurrence

`H_i = 2*H_{i-1} + gear[byte_i] (mod 2^64)`,

the weighted fingerprint of the 32-byte suffix ending at `i` is exactly

`W_i = H_i - (H_{i-32} << 32) (mod 2^64)`.

Therefore a local 32-byte fingerprint requires no second Gear lookup or independent rolling recurrence: only a 32-entry delay ring of already-computed observer states, one load/store and one subtraction per eligible byte.

The source retains the eight numerically smallest `(W,position)` witnesses. Because every retained witness is <= the largest retained witness, the target performs a single `W <= max_retained` opportunity gate before scanning the eight hashes. Exact 32-byte equality is still required before nomination.

### Disproof

Reject this shape if either:

1. it fails an independent direct-window oracle or exact nomination/negative controls; or
2. its native carrying cost remains materially above the mandatory observer despite eliminating the second recurrence and almost all eight-way target scans.

Do not rescue failure with file-size dispatch, K tuning, window tuning, threshold tuning or a weaker matrix.

## Frozen arms

Baseline: identical to the previous carrying-cost baseline — one native forward Gear observation over source then target, charging run tracking, `H = 2H + gear[byte]`, 64-byte eligibility and the existing sparse 1/1024 anchor predicate.

Candidate: byte-identical baseline observation plus:

- source/target 32-entry delay ring of mandatory observer `H` states;
- derived 32-byte `W` as `H_i - (H_{i-32} << 32)`;
- source bottom-8 `(W,position)` maintenance;
- target single-threshold gate `W <= max_retained` before any eight-way lookup;
- exact 32-byte equality before nomination;
- target certificate work stops after its first exact nomination while mandatory observer work continues to EOF.

Retained certificate state and temporary derivation scratch are reported separately. Scratch is not allowed to disappear from resource accounting merely because it is stack-local.

## Frozen matrix

Reuse the exact deterministic carrying-cost matrix:

- tiny 4 KiB shifted +1;
- tiny 8 KiB fragmented every 96 bytes;
- 64 KiB shifted +1;
- 256 KiB fragmented every 96 bytes;
- 256 KiB independent random;
- 1 MiB independent random/incompressible;
- 1 MiB already-compressed-like payload;
- 1 MiB repeated/versioned basis.

Warm-up outside timing; input copies outside timing; 101 repetitions; per-repetition A/B-B/A alternation; `-O3 -std=c11 -Wall -Wextra -Werror`.

## Independent oracle / hostile requirements

Before timing, Python independently computes direct 32-byte weighted fingerprints from raw bytes and checks the prefix-derived identity on deterministic samples. It independently computes source bottom-8 witnesses and whether any exact target window should nominate.

Required:

- baseline observer counters identical between arms;
- native nomination boolean equals independent oracle on every row;
- independent random and compressed-like rows produce no exact false nomination;
- retained witness count <=8;
- target eight-way scans occur only after the max-threshold gate;
- target certificate derivation stops after the first exact nomination, but observer counters still cover the entire target.

## Frozen performance gate

This remains a triage gate, not promotion. Advance only if all hold:

- mature (>=64 KiB) median candidate/baseline <= **1.15x**;
- fragmented mature median <= **1.15x**;
- no mature row > **1.25x**;
- tiny median <= **1.25x**;
- all oracle/parity checks pass.

These gates are deliberately looser than the rejected certificate's original 1.08x promotion-triage gate because this experiment first asks whether observer-state reuse changes the cost class enough to merit a full structural/full-observer evaluation. A PASS here does **not** satisfy the old promotion gate and does not authorize writer integration; it licenses a full observer-derived certificate structural + end-to-end A/B.

## Claim boundary

Discovery/carrying-cost research only. No reader-visible mechanism, stored-byte, density, RSS, release, v0.29/v0.30 or full-ingest claim follows.
