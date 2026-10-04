# r25 candidate scheduling RSS v2 — invalid result record

Status: **preserved invalid diagnostic / zero causal credit / zero release credit**.

## Authority

- source commit: `198e7e124b5b56be29d21a94ecc2a8896d156478`;
- workflow run: `33598181893`;
- substantive job: `100146095315` (`candidate-scheduling-rss-v2`);
- artifact id: `9834409346`;
- uploaded artifact digest: `sha256:5f3d5b743cd1e02498cefe17c3bee19195c049bfc91ec22555a157c8f285ed9f`;
- schema: `cmpct-v030-r25-candidate-scheduling-rss-v2`;
- `experiment_valid`: `false`;
- release credit: `false`.

V2 successfully repaired V1's identity-domain category error. Every worker reported the same research-content tree and the same canonical filesystem/user-tree verification identity; every final product strongly verified, selected PrefixGraph, and paired concurrent/serialized artifacts were byte-, SHA-, and tree-identical.

## Defect

The serialized arm did **not** intercept the shipping candidate scheduler. Both serialized repetitions reported `inline_executor_submissions = 0`, violating the frozen requirement of exactly two submissions.

The reason is architectural: the canonical final wrapper executes the implementation in its own module namespace and replaces `RC.build` with `_overlapped_release_candidate_build`. That function resolves `ThreadPoolExecutor` from the **canonical final module's globals**, not from `canonical.RC.ThreadPoolExecutor`. V2 patched the latter, so the shipping candidate overlap remained unchanged in both arms.

This is an instrumentation defect, not evidence that candidate serialization is ineffective.

## Observed but inadmissible numbers

The invalid artifact reported:

- concurrent median total peak RSS: `400210 KiB`;
- nominal serialized median total peak RSS: `400108 KiB`;
- nominal reduction: `0.00025486619524749506` (~0.0255%);
- concurrent median wall time: `41.78999190649998 s`;
- nominal serialized median wall time: `40.40092055300002 s`;
- nominal threshold decision: `retires-concurrency-primary-explanation`.

These values receive **zero causal decision credit** because the serialized intervention never executed. They may be used only as a debugging witness. Candidate concurrency is not retired by V2.

## Superseding requirement

A V3 freeze may repair only the intervention seam while retaining V2's corrected dual identity proof, workload, fresh-process alternating order, exact complete-artifact identity requirement, total RSS metric, and unchanged 20% / 10% thresholds.

Because canonical final also uses its module-global `ThreadPoolExecutor` for internal G0-G4 overlay work, V3 must **not** blindly replace the global executor with a serial executor. It must use a routing factory that intercepts only the scheduler call whose `thread_name_prefix` is `cmpct-v030-prefixgraph` and delegates every other executor construction to the original implementation. The serialized arm must prove exactly one intercepted PrefixGraph submission and preserve all internal G0-G4 scheduling semantics.

## Scoped negative constraint

Do not use V1 or V2 nominal near-zero deltas to retire concurrency. Reopen interpretation only from a valid superseding run that proves the intended shipping scheduler was actually changed while product bytes and all hard semantics remain identical.
