# ONE-G0.2 Sparse Native Seed Transfer — Preregistration (2026-09-09)

## Mission lock / Referee

V3 advanced the writer-envelope rehabilitation by placing the expensive generic relation path behind an exact-source zero-copy native triplet gate. Controls no longer pay the V2 always-on Python witness cost.

The strongest remaining positive-path cost is now structurally obvious: after V3's gate already establishes one candidate relation family/value, the candidate invokes `observe_relation_witnesses(source + target)`, a full Python witness scan, only to recover block seed offsets that exact maximal-span proof subsequently consumes.

This experiment asks whether that full positive-path rescan can be removed without changing representation, exact-proof semantics, V3's pre-gate, incumbent fallback, or the frozen V3 economic floor.

## Falsifiable hypothesis

A second **sparse native triplet pass** for only the V3-selected family/value can emit bounded aligned seed offsets cheaply enough to replace the full Python actionable-witness scan.

Because exact `grow_relation_spans()` remains the truth boundary, sparse native seed offsets are nominations only. False or incomplete nominations may reduce useful coverage, but they can never authorize incorrect stored bytes.

If sparse seed transfer misses required sparse-crack continuation, changes final wire, or fails to reduce positive-path CPU materially, HOLD/INVALIDATE rather than tune the benchmark.

## Candidate

For every V3 two-version object:

1. pay the exact promoted incumbent writer;
2. run the exact admissible V3 zero-copy triplet gate;
3. if V3 nominates nothing, return the incumbent exactly as V3 does;
4. if V3 nominates `(op, value)`, run a second zero-copy native pass using the **same three lanes per aligned 64-byte block**;
5. append a block start offset only when all three probes agree with the already-selected `(op, value)`;
6. feed those aligned offsets directly to the existing `grow_relation_spans()` exact verifier;
7. compile accepted spans through the same generic ONE Program and direct canonical emitter;
8. retain incumbent wire unless the fully validated generic Program is smaller.

No Python actionable-witness scan is allowed in the candidate path.

## Traffic / state contract

The first V3 gate remains exactly **0.046875x combined-input probe traffic**.

On nominated positive rows only, sparse seed transfer may perform one additional three-pair pass, for at most another **0.046875x** combined-input traffic. Therefore total relation nomination probe traffic is bounded at **0.09375x combined input** on positives and remains **0.046875x** on controls rejected by V3.

The seed buffer is bounded by aligned block count. With u64 offsets, worst-case retained seed payload is `8 * floor(version_bytes / 64)`, i.e. at most **0.0625x combined input**. Python/container object overhead is not represented by this algorithmic payload number and must not be presented as RSS.

## Frozen matrix

Use V3's identical three scales and nine families:

- novel: `add8_versioned`, `xor_versioned`, `add8_sparse_cracks`, `xor_sparse_cracks`;
- preserve: `plus1_incumbent`;
- controls: `exact_repeat`, `random`, `compressed_like`, `probe_false_positive`.

Same bytes, seeds, semantics and promoted incumbent as V3.

## Frozen gates

### Hard semantics

- exact two-root reconstruction and SHA-256 equality on every row;
- candidate final wire byte-identical to V3 final wire on every row;
- candidate final selection identical to V3 on every row;
- all novel rows retain the correct relation family/value and at least the same accepted relation bytes as V3;
- no pre-gate vote may bypass exact `grow_relation_spans()` proof.

Any hard-semantic failure => `INVALIDATE_SPARSE_NATIVE_SEED_TRANSFER`.

### Absolute V3 floor retained

The candidate must still satisfy the V3 research floor:

- each novel row saves at least 25% canonical wire versus incumbent;
- median novel marginal yield >= 20 Mbit eliminated / additional CPU-second versus incumbent;
- median control candidate/incumbent CPU <= 1.35x;
- every control CPU ratio <= 1.75x;
- modeled retained relation state <= 0.60x combined input;
- false/control proof <= 8,192 bytes where proof occurs.

### Causal rehabilitation gate

Compared directly with the V3 candidate on identical rows and alternating order:

- median **novel** candidate CPU <= **0.85x V3**;
- no individual novel CPU ratio > **1.00x V3**;
- median control CPU <= **1.10x V3**;
- no individual control CPU > **1.25x V3**;
- V4 performs zero full Python actionable-witness source-scan bytes;
- positive total native relation probe traffic <= **0.09375x combined input**;
- control native relation probe traffic remains exactly **0.046875x combined input** when V3 rejects before seed transfer.

The 0.85x novel target is intentionally material. A complex second native stage that merely breaks even does not earn a permanent place.

## Hostile review

Reject benchmark-specific fixed offsets, family-name dispatch, relaxed V3 thresholds, weakened incumbent work, skipped exact proof, hidden full-buffer copies, or untimed seed-buffer creation.

The native wrapper must use stable read-only pointers to the existing immutable `bytes` objects; `from_buffer_copy` of complete versions is inadmissible.

Sparse cracks are the critical structural adversary: seed transfer must provide enough later nominations for exact growth to resume after true cracks rather than silently truncating the Law to the first span.

## Decision vocabulary

- `ADVANCE_SPARSE_NATIVE_SEED_TRANSFER`
- `HOLD_SPARSE_NATIVE_SEED_TRANSFER`
- `INVALIDATE_SPARSE_NATIVE_SEED_TRANSFER`

An ADVANCE means the V3 opportunity gate can hand actionable geometry to exact proof using sparse native evidence rather than a full Python relation-witness scan. It does not alter reader semantics and does not substitute for the September 11 Genesis comparator decision.
