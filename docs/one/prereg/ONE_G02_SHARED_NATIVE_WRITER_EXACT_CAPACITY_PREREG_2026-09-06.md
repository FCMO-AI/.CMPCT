# ONE-G0.2 shared native writer exact-capacity preregistration — 2026-09-06

## Mission Lock / Referee

Repository authority: `research/cmpct1`. This lane is writer-only and representation-neutral. It MUST NOT alter ONE0 wire bytes, node ordering, refs, roots, Surprise bytes, hierarchy decisions, limits, reader behavior, or discovery semantics.

Current relevant seed is `benchmarks/one/native/one_g02_shared_native_writer_ref_fused.c`. The seed validates the complete Segment buffer before allocation, but `checked_cap()` then reserves a deliberately loose upper bound:

`4096 + 64*segment_count + 64*intermediate_nodes + source_len + target_len`.

The emitted wire is normally much smaller than that reservation. The hypothesis is that the already-required validation/metadata walk contains enough information to count the exact canonical ONE0 wire length without rereading source/target payload bytes. Exact pre-sizing can therefore remove allocator slack without introducing a second payload pass or a new representation mechanism.

## Falsifiable hypothesis

An exact-size prepass fused into the existing semantic validation can allocate exactly the number of bytes subsequently emitted while preserving byte-for-byte canonical output and hostile-input rejection. The bookkeeping cost must be negligible at full-writer scale; otherwise the lane is rejected even if capacity falls.

This is primarily a resource hypothesis, not a claim that `malloc(cap)` bytes equal physical RSS. The benchmark MUST distinguish:

- requested/reserved output capacity;
- bytes actually emitted/touched;
- peak resident memory when the runner can measure it reliably;
- full-writer elapsed.

No RSS win may be inferred merely from a smaller `malloc` request.

## Builder constraints

1. Keep the existing complete bounds/resource validation.
2. During that existing metadata walk, accumulate the exact encoded byte count using overflow-checked uvarint/blob/ref/concat size arithmetic.
3. Counting MUST NOT reread source or target payload bytes. Payload lengths are sufficient.
4. Account exactly for magic, resource limits, node count, source Surprise, target/segment Surprise nodes, concat hierarchy, roots, names, refs and 32-byte digests.
5. Allocate once at the computed canonical length; emission remains bounded and must finish with `out_len == allocated_bytes`.
6. Preserve the generic hierarchy path for `segment_count > ONE_MAX_NODES`; do not introduce workload/size/density dispatch.
7. No reader-visible change, no new opcode, no threshold tuning.

## Independent correctness oracle

For every accepted input, compare candidate output byte-for-byte with the current ref-fused seed and independently evaluate the resulting ONE0 artifact through the existing evaluator/oracle. Required identity includes output length, hashes, roots, reconstructed `previous` and `current`, node count, hierarchy depth and Surprise accounting.

Hostile native buffers MUST retain the seed's rejection behavior: zero-length segments, source/target spans outside bounds, unknown kinds, incomplete/excess target coverage, invalid enabled/disabled combinations, segment/resource overflow, node/depth overflow and allocation-size overflow.

## Benchmark matrix

Use the current frozen shared-native-writer matrix and seeds, including tiny inputs, productive structured/resemblance cases, random/incompressible controls, already-compressed/media-like controls, fragmented/false-pattern cases and hierarchy/resource edges. Do not remove a row because exact sizing is unfavorable.

Run A/B and B/A order with identical process/CPU controls used by the current native writer lanes. Report per-row seed-capacity bytes, candidate-capacity bytes, emitted bytes, capacity/emitted amplification, elapsed ratio, semantic identity and, where robustly available, peak RSS.

## Promotion / rejection gates

Semantic gate is absolute: zero byte/semantic/rejection mismatches.

Resource gate:

- candidate requested capacity MUST equal emitted canonical length on every accepted row;
- median requested-capacity reduction across mature productive rows MUST be at least 20% relative to the seed; otherwise the complexity is not worth carrying as a resource optimization;
- report controls and hostile rows without post-hoc exclusions.

Speed non-regression gate:

- mature productive full-writer median candidate/baseline MUST be <= 1.02x;
- no mature productive row may exceed 1.05x;
- control/hostile median MUST be <= 1.03x and no row may exceed 1.08x unless the row is explicitly a resource-limit rejection rather than a timed accepted workload.

A speed promotion requires independent evidence beyond this resource gate; exact sizing is NOT to be called a speed win merely for passing non-regression.

## Disproof / hostile review

Reject or preserve as negative if exact counting requires an additional payload pass, changes canonical bytes, weakens validation, causes material elapsed regressions, or produces little real capacity reduction. If requested capacity drops but measured RSS does not, record that distinction rather than upgrading the claim.

Forbidden rescue after seeing results: size thresholds, compressibility classifiers, segment-density dispatch, special-casing benchmark families, weakened hostile rows, or silently reverting to the loose seed allocation for inconvenient inputs.

## Causal question

If the lane succeeds, the mechanism is not a new compressor: it proves that canonical wire sizing is derived information already available in the writer's validated ONE state, so reserving speculative slack is avoidable work/state. If it fails on elapsed, keep the negative and seek a larger owner of writer time/memory traffic rather than tuning this allocator lane.
