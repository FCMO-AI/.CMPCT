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

This experiment begins **after segmentation is already complete**. Segment plans are built outside every timed interval. It asks which of the two remaining Python research-harness stages owns post-plan control creation:

1. materializing the generic ONE `Program` graph from an already-known segment plan; or
2. canonical `encode_program()` serialization of an already-built Program.

This is causal diagnosis only. Python nanoseconds are not product-speed authority.

## Falsifiable hypothesis

**Hypothesis:** canonical wire serialization is the dominant post-plan owner for sufficiently large/structured generic relation programs. If serialization consumes at least 60% of measured `Program`-build + encode time in the median productive row and remains the majority owner across most frozen size classes, a byte-identical bulk/native canonical emitter is justified as the next Builder.

**Disproof:** if graph materialization owns at least 60%, attack graph construction instead. If neither stage reaches 60%, the boundary is jointly owned and a serializer-only Builder is not justified; investigate fused graph/control construction without resurrecting direct per-segment streaming.

The 60% boundary is frozen before result-bearing execution. It is an ownership threshold, not a speed-promotion threshold.

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
- 51 interleaved rounds per row.
- Segment discovery/build occurs outside all timed regions.
- `Program`-build timing starts from the frozen segment plan and ends with a complete immutable `Program` object.
- encode timing starts from a complete prebuilt `Program` and ends when `encode_program()` returns the canonical wire and stats.
- combined timing starts from the frozen segment plan and includes Program construction plus canonical encoding.
- medians are reported independently. Stage shares use the separate median build and encode measurements: `encode / (build + encode)` and `build / (build + encode)`.
- Python GC is disabled only inside each timed micro-loop and restored immediately after, to reduce non-causal collection noise while preserving ordinary allocations.

No result may be interpreted as native writer throughput.

## Frozen semantic and representation gates

Every row must satisfy all of the following:

1. generated canonical wire decodes and reconstructs both `previous` and `current` byte-exactly;
2. every operation belongs to the existing six-op ONE grammar;
3. every concat fanout is <= declared `Limits.max_nodes`;
4. total node count is <= declared `Limits.max_nodes`;
5. all productive rows use exactly the generic ranged-Ref + Surprise + concat structure; no relation opcode exists;
6. negative controls remain literal and are not granted generic relation structure;
7. repeated builds from the same frozen plan produce byte-identical canonical wire;
8. the hostile 256 KiB `fragmented_every96` row requires hierarchy and preserves the already-proven bounded form;
9. wire bytes, Surprise bytes, control/integrity bytes, node count, concat-reference count, hierarchy depth, segment count and modeled segment-plan bytes are reported.

Any semantic/canonical mismatch invalidates the profile.

## Frozen owner decision

Ownership is evaluated over the **21 productive rows** (three productive cases x seven sizes).

Let `E` be each row's median encode share and `G` its median Program-build share.

- **advance_bulk_canonical_emitter** iff median `E >= 0.60`, encode is the majority owner (`E > 0.50`) in at least 15/21 productive rows, and at least 5/7 size classes have median productive-row `E >= 0.55`.
- **advance_program_graph_builder** iff the symmetric graph conditions hold: median `G >= 0.60`, graph is majority owner in at least 15/21 rows, and at least 5/7 size classes have median productive-row `G >= 0.55`.
- otherwise: **hold_joint_post_segment_boundary**. Do not implement a serializer-only or graph-only optimization from this result.

Negative controls are reported but do not vote on owner selection because their two-literal-node shape is not representative of the generic relation compiler debt being diagnosed.

The combined timing is reported as a sanity check only. Separate-stage medians are the frozen ownership authority; no attempt will be made to make their sum exactly equal the separately measured combined median.

## Hostile reviewer requirements

A passing ownership result must not be overclaimed:

- It does not prove that the selected optimization will improve total writer time by the same fraction; Amdahl's law still applies.
- It does not establish native performance, arbitrary pair discovery, selective-read authentication, failure blast radius, or superiority over frozen v0.29/deferred-v0.30.
- A serializer result must preserve **byte-identical canonical wire**. A new compact relation opcode or alternate private format is outside this experiment.
- A graph-builder result must preserve the same Program semantics and bounded grammar.
- Direct per-segment control streaming remains retired in its tested form; this profile is not permission to retune or rename it.

## Next action by result

- Encoder-owned: preregister a byte-identical bulk/native canonical emitter from the frozen segment plan/Program semantics, with total writer A/B and memory traffic charged.
- Graph-owned: preregister compact/bulk Program graph materialization while retaining canonical encoding unchanged.
- Joint: profile allocation/copy/varint/control sub-costs or test a fused **bulk** plan-to-wire builder that emits canonical bytes from sized batches; do not use incremental per-segment streaming.
