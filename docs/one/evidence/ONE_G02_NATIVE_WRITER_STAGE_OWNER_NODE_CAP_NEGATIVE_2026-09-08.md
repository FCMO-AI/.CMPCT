# ONE-G0.2 — native writer stage-owner hard-node-cap negative

Date: 2026-09-08
Result-bearing source: `b5fafaf54e24bcfd357aac1871a8b27855d9e6fd`
Workflow run: `34199286795`
Job: `101974122342`
Experimental line: `ONE-G0.2`

## Referee result

The repaired native-writer stage-owner lane reached the scientific workload. Exact checkout/SHA binding, environment provisioning and reachability checks passed. Its semantic/adjudication gate then passed **32 tests in 0.88 seconds**.

The subsequent stage-owner benchmark did **not** produce a stage-ownership result. On the 1 MiB profiling matrix, `Program.validate_shape()` raised:

`OneError: node count exceeds declared limit`

No benchmark JSON was produced. The always-run artifact step therefore preserved only the evidence-lane shell rather than a scientific result. The red workflow is a representation/resource negative, not an `OWNER_*` verdict and not `NO_STABLE_OWNER_FUSE_BOUNDARY`.

## Causal finding

The existing plan compiler creates one generic `surprise` Program node for each Surprise fragment emitted by segmentation. In highly fragmented temporal plans, reader-visible node count therefore scales with fragment count. The 1 MiB hostile family can exceed the unchanged `Limits.max_nodes = 4096` hard cap even though the underlying representation principle remains simply ranged reuse plus explicit Surprise.

This is distinct from the two earlier evidence-path failures around the same profiler (missing test path and missing 1 MiB decision scale): the lane now reached the intended scientific input and the Program itself violated a declared resource limit.

## Prohibited response

Do **not**:

- raise `max_nodes` to make the benchmark pass;
- drop or shrink the 1 MiB hostile row;
- skip `Program.validate_shape()`;
- weaken reconstruction/resource/access requirements; or
- call the crash a stage-owner result.

Those changes would remove the falsifier rather than repair the representation.

## Builder hypothesis opened by this negative

The next bounded hypothesis is output-local Surprise pooling using only the existing generic grammar:

- keep temporal/source structure as ranged `Ref`s;
- pool explicit Surprise bytes inside bounded contiguous output-local groups;
- point ordinary ranged `Ref`s into those pooled Surprise nodes;
- compose groups with ordinary `concat`;
- derive group span from declared `max_output_bytes` and `max_nodes`, not corpus identity.

The preregistered falsifier is `ONE_G02_BOUNDED_SURPRISE_POOLING_PREREG_2026-09-08.md`. It must reproduce this legacy overflow, validate the pooled 1 MiB Program under the unchanged cap, preserve total Surprise payload and exact semantics, and retain bounded generic 4 KiB unauthenticated range-cone work before the stage-owner profiler is allowed to consume the pooled graph.

## Claim boundary

This negative says only that the then-current per-fragment Program graph cannot represent the required hostile 1 MiB temporal plan under ONE's own hard node cap. It does not invalidate Law + Surprise as a representation principle, does not authorize a new opcode, and says nothing about v0.29/v0.30 superiority or product writer performance.