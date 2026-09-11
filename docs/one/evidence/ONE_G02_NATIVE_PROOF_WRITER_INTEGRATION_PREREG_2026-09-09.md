# ONE-G0.2 Native Exact-Proof Writer Integration — Preregistration (2026-09-09)

## Mission lock / Referee

V4 (`ADVANCE_SPARSE_NATIVE_SEED_TRANSFER`) made relation nomination and seed transfer cheap enough that Python exact proof dominates the productive relation path. The separate native exact-proof experiment tests whether that proof can be accelerated without changing the Python oracle semantics.

This experiment asks the systems question that follows **only if the native proof is semantically admissible**: does replacing V4's Python `grow_relation_spans()` proof call with the exact native verifier materially improve the complete writer while preserving V4's final wire, accepted coverage, incumbent fallback, and no-op behavior?

No reader-visible opcode, wire grammar, Law family, integrity rule, or comparator setting changes.

## Dependency gate

A result from this integration lane may be promoted only after an exact-source `ADVANCE_NATIVE_EXACT_RELATION_PROOF` has been preserved for the native verifier lineage used by the integration source.

If the standalone native-proof lane is HOLD or INVALIDATE, this integration result is automatically **inadmissible for promotion**, regardless of timing.

## Candidate

For each V4 row:

1. pay the exact incumbent temporal writer;
2. run V4's promoted zero-copy sparse opportunity gate;
3. on a positive gate only, run V4's zero-copy sparse seed transfer;
4. replace only Python exact span proof with `grow_relation_spans_native_metered()`;
5. construct, validate, and emit the same generic ONE Program as V4;
6. select generic wire only when strictly smaller than incumbent, exactly as V4 does.

Controls rejected by the gate must never enter native exact proof.

## Frozen matrix

Reuse V4's exact 27-row matrix and deterministic inputs: three per-version scales across the same novel add8/XOR exact and sparse-crack families, mature +1 relation, exact-repeat, random, compressed-like, and deliberate probe-false-positive controls.

## Semantic gates

Every row must satisfy all of the following:

- incumbent wire exactly matches V4's incumbent wire;
- candidate final wire is byte-identical to V4;
- candidate selection is identical to V4;
- accepted relation coverage is identical to V4;
- `previous` and `current` roots are identical to V4 and reconstruct exactly;
- gate choice is identical to V4;
- controls do not enter exact proof;
- native metered proof result is the result used to build the Program.

Any mismatch => `INVALIDATE_NATIVE_PROOF_WRITER_INTEGRATION`.

## Density and writer-economics gates

Retain V4's existing economic law:

- every novel row saves at least **25%** canonical wire versus incumbent;
- median novel marginal yield remains at least **20 Mbit eliminated / additional CPU-second**;
- median control candidate/incumbent CPU <= **1.35x**;
- every control candidate/incumbent CPU <= **1.75x**.

Causal improvement over V4:

- median candidate/V4 CPU across novel rows <= **0.60x**;
- no novel row > **0.80x** V4 CPU;
- median control candidate/V4 CPU <= **1.10x**;
- no control row > **1.25x** V4 CPU.

These thresholds are frozen before hosted timing.

## Proof traffic / resource gate

The native verifier must expose both semantic comparison bytes and actual bytes loaded from each input. Because SIMD may load lanes beyond the semantic first mismatch:

- actual loaded bytes per input must be >= semantic `compared_bytes`;
- physical proof-load amplification (`loaded / max(compared_bytes,1)`) must be <= **1.01x** on every row that enters proof;
- aggregate parent+child native proof traffic is `2 * loaded` and must be retained in evidence;
- relation nomination traffic remains exactly V4's 0.046875x on controls and at most 0.09375x combined input on positives;
- modeled relation state remains <= **0.60x** combined input.

The 1.01x load ceiling is deliberately generous relative to a 16-byte vector's maximum 15-byte over-read at an individual failed verification frontier, while preventing hidden bulk over-read from being waved away as a semantic comparison count.

## Timing discipline

Use alternating/rotating incumbent, V4, and native-proof candidate order; disable GC during timed rounds; exclude C compilation and one-time loader warmup; use the same V4 repetition count. Charge all Python/ctypes marshaling and result construction inside the candidate timer.

## Hostile review

Reject any apparent win caused by:

- changing V4 input families or scale;
- weakening exact proof or using hashes/sketches as proof;
- skipping sparse-crack recovery;
- changing final wire or accepted coverage;
- timing only the native kernel while excluding wrapper/allocation cost;
- hiding SIMD memory traffic behind semantic `compared_bytes`;
- letting controls enter proof;
- weakening the incumbent or V4 baseline.

## Decision vocabulary

- `ADVANCE_NATIVE_PROOF_WRITER_INTEGRATION`
- `HOLD_NATIVE_PROOF_WRITER_INTEGRATION`
- `INVALIDATE_NATIVE_PROOF_WRITER_INTEGRATION`

An ADVANCE is an implementation-level writer efficiency improvement to the same ONE representation and proof semantics. It is not a Genesis supersession claim and does not resume v0.30 work.