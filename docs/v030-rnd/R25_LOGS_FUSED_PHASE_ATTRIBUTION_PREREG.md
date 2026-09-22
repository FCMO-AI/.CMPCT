# Logs fused extraction phase attribution — preregistration

Status: **FROZEN FORGE D2 / NO RELEASE CREDIT**

## Question

After independent current-product revalidation established that the promoted one-session fused Logs extractor is materially faster than the mature pre-promotion ownership boundary, which still-required phase inside that exact fused extractor owns enough absolute wall time to plausibly cover the remaining strict Logs extraction gap without changing archive bytes or filesystem semantics?

This is attribution, not another fused-vs-baseline promotion test. `R25_LOGS_FUSED_REVALIDATION_RESULT.md` remains the authority for the local 23.33% fused win. The latest substantive complete-product receipt remains the authority for the strict row: Logs extraction was `1.3003232248x` v0.29 against the unchanged `<=1.25x` workload ceiling. On that receipt, roughly 2 ms of additional v0.30 extraction reduction would be needed to reach the row ceiling. Ratios from different runs are not multiplied or treated as release evidence.

## Frozen semantic owner and target

- target: `neutral_hostile_v1/05_logs_and_telemetry` from the deterministic neutral-hostile generator;
- product builder/verifier/tree identity: `experiments.entropygraph_v030_release_product_logs_candidate`;
- extractor under measurement: `experiments.entropygraph_v030_release_product_logs_runtime.extract`, which delegates the selected Logs representation to the promoted one-session fused owner;
- representation must remain `logs-inverse`;
- archive bytes/SHA and canonical user tree are fixed within the run;
- every measured extraction must reconstruct the exact source tree.

## Frozen instrumentation

The candidate extractor itself is unchanged. An instrumented arm temporarily wraps only three existing call boundaries and immediately calls the original implementation:

1. outermost calls to `LOGS.Archive._restore_session` — authenticated graph restore/decompression work, with recursive/nested calls charged only once at depth zero;
2. `FS.decode_manifest` — bounded authenticated filesystem-manifest decoding;
3. `_restore_filesystem_metadata` — directory/symlink/hardlink creation plus modes/timestamps/xattrs ownership restoration after content identity is already proven.

All other time remains explicit as `unattributed_remainder`: archive open/close, identity-map construction, path preparation, regular-file writes, temp-tree setup/cleanup, atomic publication and Python overhead. No part of that remainder is gifted away.

The experiment runs **11 paired rounds**, alternating control-first and instrumented-first. The control is the exact uninstrumented fused extractor. Before measurement both arms receive one untimed warm-up. Garbage collection occurs before each timed extraction, matching the existing Logs runtime oracle.

## Validity and overhead law

For a valid result:

- all 22 timed extractions reconstruct the exact source tree;
- the built archive strongly verifies and remains the selected `logs-inverse` representation;
- instrumented and control arms execute the same public fused extractor and differ only by timing wrappers;
- instrumented median total wall / control median total wall must be `<=1.10x`; larger instrumentation overhead invalidates phase shares;
- every phase median and the unattributed remainder must be non-negative; phase medians are diagnostic and are never treated as additive OS/runtime accounting beyond the instrumented call boundaries;
- no production source, archive bytes, grammar, locality, recovery/integrity or release threshold changes.

## Frozen material-headroom rule

A tracked phase is `material` only if its median instrumented time is both:

- `>=0.0020 s` absolute wall time; and
- `>=5%` of the median instrumented total extraction wall.

The 2 ms floor is intentionally tied to the scale of the current strict Logs row gap rather than to a percentage chosen to make a phase look important. Crossing it does **not** mean the phase can be eliminated; it only means that a causal optimization of that phase could be large enough to matter and deserves the next lowest-radicality A/B.

The largest tracked phase by median wall is reported. Terminal decisions are:

- invalid exactness/selection/instrumentation overhead -> **`INVALID_CORRECTNESS_OR_INSTRUMENTATION`**;
- one or more tracked phases meet the frozen material rule -> **`TRACKED_PHASE_MATERIAL_HEADROOM`**;
- none meet it -> **`TRACKED_PHASES_INSUFFICIENT_FOR_LOGS_GAP`**.

No threshold or phase boundary may be changed after result-bearing execution.

## Non-claims and next law

This experiment grants **zero release credit** and does not authorize deleting metadata work, weakening strong verification, skipping transactional publication, changing symlink/hardlink/xattr semantics, or treating the unattributed remainder as free. If a tracked phase is material, the next Forge action must attack that exact phase with a separate semantics-preserving A/B and explicit safety/carrying-cost review. If none is material, stop polishing those three call boundaries and attribute the residual path instead.
