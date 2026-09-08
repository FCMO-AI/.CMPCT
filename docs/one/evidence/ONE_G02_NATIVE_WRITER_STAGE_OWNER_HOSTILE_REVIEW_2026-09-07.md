# ONE-G0.2 native writer stage-owner hostile review

Date: 2026-09-07
Branch: `research/cmpct1`
Experimental version: `ONE-G0.2`
Profiler head entering this receipt: `8186675d05f646a27dfa6460d8cdf34e6b312671`

## Mission / decision boundary

This experiment moves the ONE speed campaign upward from the demoted positional Python fused-observation cache. Its purpose is descriptive: identify the dominant cost owner in the current native adjacent-version research-writer envelope before optimizing another stage.

The charged envelope is:

`root SHA-256 -> native fresh observation -> relation admission -> native one-pass segmentation -> generic Program construction -> validation -> direct canonical emission`

No reader-visible operation, ONE grammar, admission threshold, benchmark comparator, or archive semantic is changed.

The preregistered owner rule is unchanged:

- a single stage owns the next optimization budget only if its median wall share is at least 20% on at least two distinct 1 MiB rows;
- an adjacent two-stage cluster may own the boundary if its combined wall share is at least 40% on at least two distinct 1 MiB rows while no stable individual stage qualifies;
- otherwise the verdict is `NO_STABLE_OWNER_FUSE_BOUNDARY`;
- any semantic/oracle mismatch invalidates the profile.

## Hostile-review finding: the first implementation could not possibly find an owner

Before consuming a scientific result, hostile review found that the first profiler revision imported `SIZES` from the existing direct-emitter writer benchmark. That inherited matrix stops at 256 KiB. The new owner adjudicator, however, deliberately votes only on 1 MiB rows.

Therefore the initial implementation was logically incapable of satisfying its own owner rule: the 1 MiB voting set would always be empty and the profiler would mechanically return `NO_STABLE_OWNER_FUSE_BOUNDARY` regardless of measured timing.

This was a falsifier bug, not a scientific negative. No owner result from that implementation is admissible evidence.

The fix was made before a profiler result was consumed:

- replace inherited `SIZES` with an explicit `PROFILE_SIZES = (4 KiB, 256 KiB, 1 MiB)`;
- add a hostile unit test requiring all three scales, including the 1 MiB decision scale;
- retain the existing rule that 256 KiB rows alone cannot authorize an owner decision.

No performance threshold or owner threshold changed.

## Adjudicator hardening

Synthetic tests now prove the decision logic itself can express the preregistered outcomes:

- repeated 1 MiB evidence can identify one stable stage owner;
- alternating individual ownership can identify an adjacent co-dominant boundary;
- uniformly sub-threshold rows return `NO_STABLE_OWNER_FUSE_BOUNDARY`;
- 256 KiB evidence alone cannot manufacture a 1 MiB owner;
- the measurement matrix cannot silently lose its tiny, 256 KiB, or 1 MiB rows.

## Instrumentation-overhead audit

Stage medians are diagnostic measurements, not a literal production wall-clock decomposition. The profiler therefore now also times a separately composed writer path with the same semantics and canonical output. Instrumented-first and composed-first order alternates across repetitions to reduce drift bias.

For every row the result reports:

- median per-stage wall and process CPU;
- summed stage medians;
- median composed wall and CPU;
- `stage_sum_over_composed_wall` and `stage_sum_over_composed_cpu`.

The composed and instrumented paths must emit the same canonical bytes and statistics. This prevents timing probes from silently changing the writer being measured and exposes how much isolated-stage instrumentation inflates or perturbs the envelope.

## Semantic and independent-oracle gates

The profile requires:

- exact current and previous SHA-256 roots checked independently with `hashlib.sha256`;
- native segmentation equal to the independent Python segmentation oracle whenever relation admission enables the temporal path;
- canonical wire decoded by the ordinary ONE decoder/evaluator;
- exact reconstructed `previous` and `current` roots;
- composed and instrumented canonical outputs identical.

The native observer remains writer-side discovery state only. Reader execution remains discovery-free.

## Important interpretation caveats

1. `observe_native` currently enters through a Python/ctypes wrapper whose buffer setup includes a copy. If native observation becomes the owner, wrapper/buffer cost must be separated from C-kernel cost before deciding that the native kernel itself is the optimization target.

2. The root-hash stage currently charges SHA-256 for both previous and current roots. In a durable versioned writer the previous root may already be known. If root hashing becomes the owner, the next experiment must distinguish unavoidable current authentication from gratuitous previous-root revalidation before proposing authentication/observation fusion.

3. Native fresh observation is deliberately charged even though the current relation gate does not consume its Observation object directly. This is a conservative generic writer envelope: it prevents the broader ONE discovery path from looking artificially cheap by omitting the observation work that the promoted speed baseline requires. It is not a claim that the current research writer has already fused all discovery consumers into one literal production dependency graph.

4. A stage-owner verdict selects only the next research target. It does not establish product writer speed, durability/placement economics, v0.29 superiority, deferred-v0.30 superiority, or September-11 Genesis promotion.

## CI / evidence truth at receipt time

The corrected profiler, exact-head workflow, semantic tests, adjudicator tests, composed-path audit, and 1 MiB matrix are durable on `research/cmpct1` through `8186675d05f646a27dfa6460d8cdf34e6b312671`.

GitHub Actions had spawned runs for earlier profiler revisions while the falsifier was still being hardened. At receipt time a completed exact-head hosted JSON result for the corrected `8186675...` matrix had not been positively resolved through the available Actions query surface. Therefore this receipt claims no stage owner, no new stage timing ratio, no RSS result, and no CI-green scientific verdict.

The correct next action is to consume only a completed exact-SHA result from the corrected matrix. If none is available, rerun/obtain that evidence rather than interpreting an earlier pre-fix workflow.

## Next decision

- `OWNER_NATIVE_OBSERVE`: first split wrapper/buffer-copy cost from native C-kernel cost; then test source-pass fusion only if authentication is also material.
- `OWNER_ROOT_HASH`: distinguish current-root authentication from already-known previous-root work before any fusion claim.
- another `OWNER_*`: move optimization upward to that measured owner rather than returning to the demoted cache.
- `NO_STABLE_OWNER_FUSE_BOUNDARY`: prefer broader pass/boundary fusion over isolated micro-tuning.
- `INVALIDATE_PROFILE`: repair semantic/oracle disagreement before any speed interpretation.

The positional fused-observation cache remains demoted as the general ONE speed path. This experiment does not reopen it.