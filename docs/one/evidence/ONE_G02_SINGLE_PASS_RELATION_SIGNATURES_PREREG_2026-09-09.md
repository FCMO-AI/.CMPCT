# ONE-G0.2 Single-Pass Relation Signatures — Preregistration (2026-09-09)

## Mission lock / Referee

V4 (`ADVANCE_SPARSE_NATIVE_SEED_TRANSFER`) removed the positive-path full Python relation-witness scan. It retained exact V3 wire/coverage while reducing median novel CPU to ~0.673x V3. Its remaining nomination inefficiency is now simple: positive rows read the same three sparse source/target pairs twice—once to select `(op,value)`, then again to recover aligned seeds.

This experiment tests whether the first sparse pass can retain a compact per-block relation signature, select the global winner, and derive exact-proof seeds from that retained signature record **without rereading source bytes**.

## Falsifiable hypothesis

A single native sparse source pass can reproduce V4's selected relation, seed geometry, exact proof coverage, final Program/wire, and control behavior while halving positive relation-nomination source traffic from 0.09375x to 0.046875x combined input and reducing the nomination-stage CPU materially.

If signature retention changes V4 wire/coverage, increases whole-writer CPU materially, or requires hidden full-buffer copying, HOLD/INVALIDATE rather than weaken the gate.

## Candidate

For each aligned 64-byte version block, the native pass reads V4's exact same three source/target pairs. It computes at most one non-zero add8 candidate byte and one non-zero XOR candidate byte when all three probes agree, packs the pair into one `uint16_t` block signature, and updates the same 256-bin add/XOR histograms used by V3/V4.

After the source pass ends, the kernel selects the winning `(op,value)` with V3's exact 7/8 decision law and tie behavior, then scans only the compact signature array in memory. Matching block indices become aligned proof seeds. The source versions are not reread during seed derivation.

Exact `grow_relation_spans()` remains the truth boundary. No signature authorizes storage.

## Traffic and state

- source probe traffic on all rows: exactly **0.046875x combined input**;
- no second source-probe pass;
- signature payload: 2 bytes per aligned version block = at most **0.015625x combined input**;
- proof-seed payload: u32 block indices, at most 4 bytes per block = at most **0.03125x combined input**;
- fixed gate histograms remain 4 KiB;
- these are algorithmic payload models, not RSS.

## Matrix

Exactly V4's 27 rows: three scales and nine families (`add8_versioned`, `xor_versioned`, sparse-crack variants, `plus1_incumbent`, `exact_repeat`, `random`, `compressed_like`, `probe_false_positive`). Same deterministic bytes and incumbent.

## Hard parity

Every row must preserve:

- exact two-root reconstruction and SHA-256 identity;
- final canonical wire byte-identical to V4;
- final selection identical to V4;
- novel selected `(op,value)` identical to V4;
- accepted relation bytes identical to V4;
- exact-proof bytes no greater than V4;
- controls/preserve rows must not enter expensive relation proof.

Any failure => `INVALIDATE_SINGLE_PASS_RELATION_SIGNATURES`.

## Economic gates

Retain all V4 absolute floors:

- >=25% wire saving on every novel row;
- median novel marginal yield >=20 Mbit eliminated / additional CPU-second vs incumbent;
- median control candidate/incumbent CPU <=1.35x;
- every control <=1.75x;
- exact semantics and incumbent fallback.

Causal V5-vs-V4 requirements:

- positive relation-nomination source traffic exactly **0.046875x**, a 50% reduction from V4;
- median **gate+seed-derivation CPU** <= **0.60x V4 gate+seed-transfer CPU**;
- no novel gate+seed-derivation CPU > **0.80x V4**;
- median whole-writer novel CPU <= **1.00x V4**;
- no novel whole-writer CPU > **1.03x V4**;
- median control whole-writer CPU <= **1.05x V4**;
- no control > **1.15x V4**.

The whole-writer gate is deliberately non-regressive rather than demanding a large total speedup, because V4 evidence shows exact proof dominates positive CPU (~45–49 ms at 1 MiB) while nomination is ~1 ms. The experiment earns its place primarily by eliminating source traffic and duplicate observation work.

## Hostile review

Reject fixed benchmark-family dispatch, altered probe lanes, altered 7/8 threshold, changed incumbent work, `from_buffer_copy` of the versions inside the candidate gate, skipped exact proof, uncharged signature/seed construction, or comparing against anything weaker than exact V4.

## Decision vocabulary

- `ADVANCE_SINGLE_PASS_RELATION_SIGNATURES`
- `HOLD_SINGLE_PASS_RELATION_SIGNATURES`
- `INVALIDATE_SINGLE_PASS_RELATION_SIGNATURES`

An ADVANCE is evidence for `observe once` relation nomination. It is not the Genesis supersession decision and does not change reader semantics.
