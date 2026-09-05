# ONE-G0.2 — post-segment control cost-owner preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2

## Mission lock / referee

The current ONE evidence has removed several previously entangled costs from the temporal/versioned writer path:

- amortization-safe relation admission preserves the isolated lower-level dispatch gain;
- native one-pass `Segment[]` planning eliminates the redundant second target scan and halves logical target-byte traffic;
- direct generic-control streaming was falsified twice as slower than retaining the compact transient segment plan;
- bounded hierarchical `concat` expresses hostile fragmented relations without relaxing reader caps; and
- generic concat-cone fusion removes the hierarchy's intermediate materialization tax.

The corrected temporal-writer v2 result cannot identify the remaining creation-time owner because its Python relation compiler still scans target bytes while constructing `Program` objects. That scan is obsolete relative to the promoted native one-pass segment-plan path. Optimizing `encode_program()` from that mixed timing would therefore be premature.

This experiment begins **after segmentation is already complete**. Segment plans are built outside every timed interval. It first asks whether post-plan control creation is owned by:

1. materializing the generic ONE `Program` graph from an already-known segment plan; or
2. the canonical encode boundary of an already-built Program.

Hostile review before result-bearing execution found an important ambiguity: `encode_program()` itself begins with full `Program.validate_shape()`. Therefore an encoder-owned result is decomposed further into:

2a. shape-validation work; and
2b. byte-identical canonical emission of a Program that has already passed the same validation.

The prevalidated-emission measurement does **not** remove validation from semantics or from any proposed product path. It is a diagnostic measurement only: the exact same Program is validated before the timed emission loop, `Program.validate_shape` is temporarily replaced by a no-op only while timing the otherwise unchanged `encode_program()` implementation, and the resulting wire must remain byte-identical to normal validated encoding. The method is restored immediately afterward.

This is causal diagnosis only. Python nanoseconds are not product-speed authority.

## Falsifiable hypothesis

**Primary hypothesis:** the canonical encode boundary is the dominant post-plan owner for sufficiently large/structured generic relation programs. If it consumes at least 60% of measured `Program`-build + full-encode time in the median productive row and remains the majority owner across most frozen size classes, graph materialization is not the next target.

**Primary disproof:** if graph materialization owns at least 60%, attack graph construction instead. If neither side reaches 60%, the boundary is jointly owned and a single-stage Builder is not justified.

**Encoder sub-hypothesis:** if the encode boundary wins, prevalidated byte emission—not repeated shape validation—must independently own at least 60% of validation + prevalidated-emission time under the same majority rules before a bulk/native canonical emitter is justified. If validation owns that envelope, the next research question is safe validation amortization/certification, not faster varints. If neither owns it, retain the encode boundary as joint debt and decompose allocation/copy/varint costs before implementation.

The 60% boundaries are frozen before result-bearing execution. They are ownership thresholds, not speed-promotion thresholds.

## Frozen corpus

Deterministic sizes: **4, 8, 16, 32, 64, 128, 256 KiB**.

Productive generic relation cases inherited unchanged from the exact relation-transfer generator:

- `shift_plus1`
- `shift_plus1_damage_quarter`
- `fragmented_every96`

Negative/control shapes:

- `fragmented_every32`
- `independent_random`

For the three productive cases, the profiler constructs the exact +1 Ref/Surprise segmentation once, outside all timed regions, then compiles it through the already-proven bounded hierarchical concat rule. For negative controls, the writer shape is the ordinary two-Surprise literal program; no relation structure is gifted to them.

The 256 KiB `fragmented_every96` case must retain the known hostile shape where the ideal flat relation exceeds the 4,096-ref cap and therefore requires bounded hierarchy.

## Frozen timing method

- Python 3.11 research harness.
- 51 rounds per row.
- Segment discovery/build occurs outside all timed regions.
- `Program`-build timing starts from the frozen segment plan and ends with a complete immutable `Program` object.
- full-encode timing starts from a complete prebuilt `Program` and ends when ordinary `encode_program()` returns canonical wire and stats, including its normal `validate_shape()` call.
- validation timing runs `prebuilt.validate_shape()` alone.
- prevalidated-emission timing first validates the Program outside the timing loop, temporarily suppresses only the duplicate `validate_shape()` call inside otherwise unchanged `encode_program()`, then measures canonical emission. The original method is restored before any other operation.
- combined timing starts from the frozen segment plan and includes Program construction plus ordinary validated canonical encoding.
- medians are reported independently.
- primary stage shares use `full_encode / (build + full_encode)` and `build / (build + full_encode)`.
- encoder-internal diagnostic shares use `prevalidated_emit / (validation + prevalidated_emit)` and `validation / (validation + prevalidated_emit)`. No claim is made that separate medians add exactly to full-encode timing.
- Python GC is disabled only inside each timed micro-loop and restored immediately after.

No result may be interpreted as native writer throughput.

## Frozen semantic and representation gates

Every row must satisfy all of the following:

1. generated canonical wire decodes and reconstructs both `previous` and `current` byte-exactly;
2. every operation belongs to the existing six-op ONE grammar;
3. every concat fanout is <= declared `Limits.max_nodes`;
4. total node count is <= declared `Limits.max_nodes`;
5. all productive rows use exactly the generic ranged-Ref + Surprise + concat structure; no relation opcode exists;
6. negative controls remain literal and are not granted generic relation structure;
7. normal full encoding, repeated builds, and prevalidated-emission diagnostic produce byte-identical canonical wire and identical wire stats;
8. the hostile 256 KiB `fragmented_every96` row requires hierarchy and preserves the already-proven bounded form;
9. wire bytes, Surprise bytes, control/integrity bytes, node count, concat-reference count, hierarchy depth, segment count and modeled segment-plan bytes are reported.

Any semantic/canonical mismatch invalidates the profile.

## Frozen owner decision

Ownership is evaluated over the **21 productive rows** (three productive cases x seven sizes).

Let `E` be each row's full-encode share and `G` its Program-build share. For the encode sub-boundary let `R` be prevalidated-emission share and `V` validation share.

Primary owner conditions use all three gates: median share >=0.60, majority share >0.50 in at least 15/21 productive rows, and at least 5/7 size classes with median productive-row share >=0.55.

- If graph satisfies the primary conditions and encode does not: **advance_program_graph_builder**.
- If neither primary side uniquely satisfies them: **hold_joint_post_segment_boundary**.
- If encode uniquely satisfies them, apply the same three conditions to the encoder sub-boundary:
  - prevalidated emission wins: **advance_bulk_canonical_emitter**;
  - validation wins: **advance_validation_amortization_falsifier**;
  - neither wins: **hold_joint_encode_boundary**.

Negative controls are reported but do not vote on owner selection because their two-literal-node shape is not representative of the generic relation compiler debt being diagnosed.

The combined timing is reported as a sanity check only. Separate-stage medians are the frozen ownership authority.

## Hostile reviewer requirements

A passing ownership result must not be overclaimed:

- It does not prove that the selected optimization will improve total writer time by the same fraction; Amdahl's law still applies.
- It does not establish native performance, arbitrary pair discovery, selective-read authentication, failure blast radius, or superiority over frozen v0.29/deferred-v0.30.
- A serializer result must preserve **byte-identical canonical wire** and all existing validation obligations. A new compact relation opcode or alternate private format is outside this experiment.
- A validation result is not permission to delete checks. Any later optimization must prove equivalent validation from trusted builder invariants or amortize repeated work without weakening hostile-input rejection.
- A graph-builder result must preserve the same Program semantics and bounded grammar.
- Direct per-segment control streaming remains retired in its tested form; this profile is not permission to retune or rename it.

## Next action by result

- Emission-owned: preregister a byte-identical bulk/native canonical emitter, retaining equivalent validation and charging total writer A/B plus memory traffic.
- Validation-owned: preregister a safe validation-amortization/certified-builder falsifier that proves no hostile acceptance regression before claiming speed.
- Graph-owned: preregister compact/bulk Program graph materialization while retaining canonical encoding unchanged.
- Joint primary/encode boundary: profile allocation/copy/varint/control sub-costs or test a fused **bulk** plan-to-wire builder that emits canonical bytes from sized batches; do not use incremental per-segment streaming.
