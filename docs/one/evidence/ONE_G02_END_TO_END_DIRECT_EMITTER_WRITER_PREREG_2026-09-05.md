# ONE-G0.2 end-to-end direct-emitter writer — preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2
Authoritative branch: `research/cmpct1`

## Mission Lock / observed opportunity

The post-segment cost-owner experiment identified canonical byte emission as the dominant post-segment Python cost. A growable one-pass direct emitter then reproduced a large broad speed signal while preserving byte-identical ONE0 output, but one 256 KiB exact-shift row showed benchmark-context/runtime-state instability and blocked promotion of that isolated Python microbenchmark.

The next product-relevant question is not whether CPython's allocator can be tuned. It is whether the **direct-write principle still removes meaningful charged writer work after the currently advanced relation-admission, one-pass segmentation, bounded generic graph construction and validation costs are charged together**.

## Accounting boundary

This is an adjacent-version writer A/B **after root identities are already available**. Source/target SHA-256 construction and broader fused observation/authentication work are not timed here because they are identical context supplied to both arms and are not changed by the emitter hypothesis. They remain non-borrowable product cost for a later full ingest/writer benchmark. Therefore this experiment may establish survival of the emitter gain through the charged relation-to-wire path, but it may not be described as total product ingest cost.

## Baseline

Both arms receive identical deterministic `(previous, current)` version pairs and use the same:

- amortization-safe +1 relation admission/proof path;
- native one-pass maximal Ref/Surprise segment-plan construction when a +1 Law is accepted;
- bounded generic `surprise` + ranged `Ref` + `concat` graph construction, including hierarchy under the unchanged fanout/resource cap;
- `Program.validate_shape()` safety boundary;
- canonical ONE0 semantics, root hashes, limits and decoder/evaluator.

The **baseline** emits the validated Program with ordinary `encode_program()`.

The **candidate** emits the same validated Program with `_encode_program_growable_prevalidated()`, which writes uvarints/refs/nodes/blobs directly into one growable output buffer and performs no sizing pass.

The experiment deliberately does **not** compare different relation-discovery or segmentation algorithms. Those are common charged writer work so the emitter's end-to-end contribution can be identified.

## Falsifiable hypothesis

If helper-produced temporary uvarint/ref/node byte strings are a material avoidable cost rather than merely a microbenchmark artifact, direct canonical emission should remain measurably faster after admission, native segmentation, Program construction and validation are all included in each timed writer call.

## Disproof / hold conditions

Hold the mechanism at the Python research boundary if any of these occur:

1. baseline and candidate canonical wires/stats differ on any row;
2. either path fails byte-exact decode/reconstruction;
3. the candidate changes Law vocabulary, limits, root identity, stored bytes or reader work;
4. median candidate/baseline elapsed over productive rows exceeds **0.92x**;
5. fewer than **18/21** productive rows are at or below **0.98x**;
6. any productive size-class median exceeds **1.00x**;
7. any individual productive row exceeds **1.10x**;
8. any control size-class median exceeds **1.03x**.

These thresholds are frozen before result-bearing execution. They are not release gates and do not authorize a product-speed claim.

## Frozen envelope

Sizes:

- 4, 8, 16, 32, 64, 128 and 256 KiB.

Productive generic-relation cases:

- exact `shift_plus1`;
- `shift_plus1_damage_quarter`;
- `fragmented_every96`.

Controls:

- `fragmented_every32` false-pattern/dense-damage control;
- independent random next version.

Timing uses **31 repetitions** with alternating A/B-B/A order. Program/wire correctness checks are outside the timed loops, but every timed writer call includes admission, native segment-plan construction when enabled, bounded Program construction, full shape validation and canonical emission.

## Cost model

Charge in the timed writer call:

- relation admission/proof;
- target/source traffic performed by that relation path;
- native one-pass segment-plan construction and transient segment state when enabled;
- Python Program/node/ref allocation;
- `Program.validate_shape()`;
- canonical byte emission.

Record outside the timing boundary but preserve as result dimensions:

- canonical wire bytes;
- Surprise bytes and control/integrity bytes;
- Program nodes / concat refs / hierarchy depth;
- modeled transient segment-plan bytes (`sizeof(Segment)` from the native kernel);
- reader reconstruction work/materialization;
- exact classification/shift truth;
- exact wire equality.

Explicitly uncharged in this A/B but retained as later product debt:

- initial source/target root hashing;
- broader object-discovery / fused-observation work not changed by the candidate;
- authenticated container/index placement and durability work.

## Independent evidence plan

- The candidate wire must equal ordinary `encode_program()` byte-for-byte.
- Candidate output is decoded with the ordinary decoder and reconstructed through the existing reference evaluator.
- Native segment plans are compared to the existing Python maximal +1 segmentation oracle before timing authority is accepted.
- Existing ONE semantic/hostile tests run before the benchmark in CI.

## Hostile Reviewer

This experiment is intentionally allowed to fail if the previous 256 KiB exact-shift instability survives the larger timed boundary. A broad aggregate gain does not erase that row.

A pass would establish only that the direct-write **principle survives charged relation-to-wire research-writer work on this temporal envelope**. It would not establish total ingest cost, native/product writer throughput, arbitrary relation discovery, authenticated selective reads, recovery, portability or supremacy over v0.29/v0.30.

If the Python context instability remains the only red while the broad mechanism survives, do not tune a size/workload exception. Preserve the debt and transfer the direct-write idea to a native/shared ONE writer experiment when that boundary is justified.

## Terminal decisions

- `advance_end_to_end_direct_emitter_writer` — all frozen semantic and performance conditions pass.
- `hold_end_to_end_direct_emitter_writer` — semantics remain exact but one or more frozen performance conditions fail.
- `invalidate_end_to_end_direct_emitter_writer` — semantic/wire/oracle invariants fail.
