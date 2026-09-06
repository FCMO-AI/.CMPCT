# ONE-G0.2 root-hash-charged writer coarse attribution — preregistration

Date: 2026-09-06
Branch: `research/cmpct1`
Experimental line: `ONE-G0.2`
Parent writer authority: `ONE_G02_ROOT_HASH_CHARGED_DIRECT_EMITTER_RESULT_2026-09-05.md`
Parent local-cost negatives: `ONE_G02_NATIVE_FUSED_NOMINATION_FP8_RESULT_2026-09-06.md`, `ONE_G02_NATIVE_FUSED_NOMINATION_LOCAL_SOA_RESULT_2026-09-06.md`

## Mission Lock / falsifiable hypothesis

Two independent integrated local-nomination experiments now show that operation-count-heavy local lookup is not a sufficiently large universal elapsed owner: mirrored-fp8 failed its whole-consumer gate and compact local SoA produced only ~1.24% mature-median improvement despite exact -512 B state. Witness proof-deferral similarly removed ~83% of relation-specific traffic without material elapsed gain. The next step must therefore measure where the clock actually lives rather than optimize another visible counter.

Hypothesis: inside the currently preferred **root-hash-charged direct-emitter adjacent-version research writer**, at least one coarse writer zone owns a stable material fraction of mature productive elapsed. A six-zone low-perturbation attribution should identify a zone with >=25% median share over mature productive rows while adding <=3% median elapsed overhead versus the identical uninstrumented direct writer. If no zone reaches that owner threshold, or instrumentation itself exceeds the overhead gate, this attribution is rejected and no optimization may be justified from its phase shares.

This is attribution, not a speed promotion and not a claim of full ingest. It intentionally preserves the existing boundary: SHA-256 roots, amortization-safe relation admission, native one-pass segment planning, bounded generic Program construction, full validation, and direct final-buffer canonical emission. Arbitrary/fused discovery, authenticated placement/durability, filesystem semantics, and product-native writer authority remain outside this gate.

## Frozen zones

The instrumented writer performs exactly the same work and returns exactly the same canonical bytes/stats/semantic observables as the uninstrumented direct writer. Only elapsed counters are added around these existing coarse boundaries:

1. `root_hash`: SHA-256 of previous + current version and Root construction inputs;
2. `admission`: amortization-safe relation gate;
3. `segment`: native one-pass segment-plan construction when relation is enabled (zero/near-zero otherwise);
4. `program`: bounded generic Law/Surprise Program construction from plan, or literal Program construction when admission rejects;
5. `validation`: `Program.validate_shape()` hard invariant;
6. `emission`: growable direct prevalidated canonical ONE wire emission.

No phase may be skipped, reordered, cached across calls, weakened, or moved outside timing. Timer calls themselves are charged by comparing the profiled writer against the uninstrumented direct writer.

## Frozen workload / timing law

Reuse the existing root-hash writer matrix and generators exactly: sizes 4/8/16/64/256 KiB; productive and control cases from `one_g02_end_to_end_direct_emitter_writer`; same exact-source native admission/segment kernels and same semantic/oracle checks. The attribution authority is based on mature rows >=16 KiB, while 4/8 KiB remain hostile diagnostics because timer overhead can be a larger fraction there.

For each row use alternating paired order between uninstrumented and profiled direct writer, GC disabled during timing, 31 rounds, medians per row. The profiled writer records phase elapsed with `time.perf_counter_ns()`; phase shares are computed from the sum of charged phase elapsed, and the paired profiled/uninstrumented whole-call ratio independently measures instrumentation perturbation.

## Frozen validity / owner gates

Attribution is valid only if all hold:

1. canonical wire and stats are exact between profiled and uninstrumented direct writer;
2. admission classification, best shift, exact-proof count, native plan, independent Python segment oracle where enabled, root hashes, decode/evaluate reconstruction and Program semantics are exact;
3. mature productive median profiled/uninstrumented whole-call ratio <=1.03x;
4. no mature productive row profiled/uninstrumented ratio >1.08x;
5. mature control median profiled/uninstrumented ratio <=1.05x;
6. every measured phase time is non-negative and the six phase shares sum to 1 within floating tolerance;
7. ONE semantic/hostile tests remain green in exact-source CI.

A **material owner** exists only if one frozen zone has >=25% median phase share across mature productive rows and >=20% median share in at least 2 of the 3 mature sizes (16/64/256 KiB). If multiple zones qualify, rank them by aggregate mature median share; this experiment identifies ownership only and does not pre-authorize an optimization.

If instrumentation gates fail, decision is `invalidate_root_hash_writer_attribution`. If semantics pass but no zone satisfies the owner law, decision is `diffuse_root_hash_writer_cost`; in that case the next experiment must broaden the boundary or use a lower-perturbation method rather than threshold-tune phase definitions. If a zone qualifies, decision is `localize_root_hash_writer_owner`.

## Hostile Reviewer pre-commit critique

The main risk is measurement perturbation: six Python timer boundaries can materially distort 4/8 KiB rows or change cache/interpreter behavior. This is why mature attribution begins at 16 KiB and why a separate whole-call overhead gate is authoritative. A second risk is mistaking Python orchestration overhead for product-native writer cost. Any owner found here is scoped to the current research writer and must later survive native-writer transfer; it cannot be promoted directly to product authority. A third risk is that productive temporal relations and controls may have different owners; control rows remain separately reported and cannot be hidden by aggregate productive medians.

No post-hoc phase merging, workload classifier, size threshold, or weakened owner percentage is permitted after results are visible.
