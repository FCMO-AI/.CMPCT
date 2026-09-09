# ONE-G0.2 Sparse Native Seed Transfer — Result (2026-09-09)

## Decision

**ADVANCE_SPARSE_NATIVE_SEED_TRANSFER**

The exact-source fail-closed hosted falsifier advanced. V4 removes V3's full Python actionable-witness scan from the positive relation path and replaces it with a second zero-copy sparse native triplet pass that emits bounded aligned seed offsets for exact span proof.

This is a writer-side research promotion only. It changes no reader-visible opcode, wire grammar, integrity rule, or canonical version, and it does not substitute for the September 11 Genesis comparator gate.

## Exact authority

- branch: `research/cmpct1`
- experimental version: `ONE-G0.2`
- source SHA: `5baa2d3d7ba364ef0f6976c81457f357ec70e155`
- workflow: `cmpct1-one-g02-sparse-native-seed-transfer`
- run: `34349663837`
- job: `102459544371`
- artifact: `10103211650`
- artifact digest: `sha256:141feceedbdfc1725d63685e6bc32ae62c750bb1170e4c4904a4db0e325f0e88`

Exact checkout/frozen-law binding passed, inherited semantic adversaries passed, the sparse native seed-transfer falsifier passed, and the row-level JSON artifact was uploaded successfully.

## Headline measurements

Across the frozen 27-row V3 matrix:

- decision: `ADVANCE_SPARSE_NATIVE_SEED_TRANSFER`;
- median novel marginal yield: **86.9878 Mbit eliminated / additional CPU-second**;
- median V4/V3 novel CPU ratio: **0.672991x**;
- worst V4/V3 novel CPU ratio: **0.692954x**;
- median control V4/incumbent CPU ratio: **1.139057x**;
- worst control V4/incumbent CPU ratio: **1.185945x**.

Thus the causal target cleared materially rather than barely: the novel positive path is about **32.7% faster than V3 at median**, every novel row is faster than V3, and controls remain comfortably inside V3's frozen 1.35x median / 1.75x individual CPU limits.

## Representation parity

V4 reproduced V3's final canonical wire byte-for-byte on every row and preserved V3 final selection and accepted relation coverage.

At 1 MiB combined input (512 KiB per version):

- exact add8: incumbent **1,048,697 B**, generic **524,430 B**, saving **49.9922%**;
- exact XOR: incumbent **1,048,697 B**, generic **524,430 B**, saving **49.9922%**;
- add8 sparse cracks: incumbent **1,048,697 B**, generic **524,656 B**, saving **49.9707%**;
- XOR sparse cracks: incumbent **1,048,697 B**, generic **524,656 B**, saving **49.9707%**.

Accepted relation coverage was identical to V3:

- exact relations: **524,288 B** accepted;
- sparse-crack relations: **524,280 B** accepted.

All roots reconstructed exactly.

## Traffic and state

The first V3 gate still reads exactly three source/target pairs per aligned 64-byte block: **0.046875x combined-input source traffic**.

On positive rows only, V4 performs one second pass with the same sparse triplet geometry to emit seed offsets. Total relation-nomination source traffic is therefore exactly **0.09375x combined input** on positives.

Controls rejected by the first gate never enter seed transfer and remain exactly **0.046875x** relation-probe traffic.

At 1 MiB combined input the exact relation rows emitted 8,192 aligned seeds. The modeled relation-state ratio was **0.06640625x**. This is an algorithmic payload model, not Python RSS.

## Stage-level positive cost ownership

Representative 1 MiB exact rows show where time now goes:

### add8 exact

- V3/V4 gate: **83.604 us CPU**;
- sparse seed transfer: **1.029 ms**;
- exact span proof: **48.924 ms**;
- Program construction/emission: **0.141 ms**;
- V4/V3 total CPU ratio: **0.6635x**;
- marginal yield: **83.36 Mbit/s**.

### XOR exact

- gate: **82.583 us**;
- sparse seed transfer: **1.026 ms**;
- exact span proof: **45.340 ms**;
- Program construction/emission: **0.143 ms**;
- V4/V3 total CPU ratio: **0.6465x**;
- marginal yield: **89.87 Mbit/s**.

The dominant remaining positive-path cost is now unambiguous: **exact relation proof**, not nomination, seed transfer, or canonical emission.

This is a healthy boundary. Exact proof is the safety/truth boundary and cannot simply be removed. Future optimization must reduce redundant proof work or move it into a faster bulk/native implementation while preserving exact semantics.

## Strongest criticism

V4 still performs **two sparse source-probe passes** on positive rows. The second pass exists only because V3's first pass discards per-block relation signatures after tallying its histogram. That is now avoidable duplication.

A stronger fused observer should retain a compact per-block candidate signature during the first already-paid sparse pass, select the global winner, then derive seed offsets from that compact record without rereading source bytes. This could reduce positive nomination traffic from 0.09375x back to 0.046875x while preserving V4's exact seed geometry.

Also, exact proof still dominates positive CPU by roughly two orders of magnitude over the gate itself. Native/SIMD exact span verification is now a higher-value optimization target than further micro-optimizing the gate.

Reader/access debt remains unchanged. At 1 MiB exact relations the generic candidate modeled **1,572,864 B materialized** and **5,242,880 B reconstruction work**; sparse cracks modeled **2,097,152 B materialized** and **6,291,432 B work**. Better stored density therefore still exports extra reconstruction work compared with the incumbent.

## Causal conclusion

V2's control failure and V3/V4 together establish a coherent principle:

1. always-on rich discovery is economically unacceptable;
2. a tiny native opportunity gate protects no-op inputs;
3. once an opportunity is real, sparse native geometry transfer is substantially cheaper than a full Python witness scan;
4. the remaining expensive work is exact proof, which is semantically necessary but implementation-optimizable.

This is materially closer to ONE's intended `observe once -> think selectively -> prove exactly -> emit one generic Law` writer architecture.

## Next decisive actions

Two next experiments are justified, in this order:

1. **single-pass signature retention**: retain compact per-block relation signatures from the first sparse gate and derive seeds without the second source pass. Require exact V4 wire/coverage parity and a material further positive CPU/traffic reduction without worsening controls;
2. **native bulk exact proof**: after semantic vectors are frozen, replace Python byte-by-byte `grow_relation_spans()` inner verification with a bounded native bulk verifier that identifies the exact first mismatch and preserves no-reread accepted-span semantics. Charge wall/CPU, source traffic, failure work, and sparse-crack recovery.

Do not weaken exact proof or V4's frozen economic gates.

## Campaign boundary

Frozen Genesis comparators remain:

- v0.29: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- deferred v0.30: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

No ordinary v0.30 development resumes from this result. At/after the first activation on 2026-09-11 America/Mexico_City, run the required full 15-workload same-input/same-semantics Genesis comparison.
