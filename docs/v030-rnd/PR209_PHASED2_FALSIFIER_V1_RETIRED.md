# PR #209 Phased2 falsifier v1 — RETIRED / DO NOT EXECUTE FOR CREDIT

**Date:** 2026-09-27  
**Applies to:** `benchmarks/v030_pr209_nested_child_binding_falsifier.py` as landed at commit
`1b1e2e11bc0766e452b2bc0274af49c13b90004f`.

A later adversarial self-review found that v1 is not an admissible three-arm comparator.

The module imports `entropygraph_v030_release_product_compact_r24` before its nominal
`genuine_r24` arm runs. Importing that candidate mutates preserved release Builder policy in the
same interpreter. The nominal genuine control therefore cannot be assumed to represent an untouched
genuine-r24 Builder state. This is exactly the kind of process-boundary contamination the experiment
was intended to detect.

**Decision:** v1 is retired and receives zero scientific/product credit. Do not use a result from it,
even if it appears to reproduce the expected byte deltas.

A valid replacement must run every byte-owning arm in an independent fresh interpreter, or otherwise
prove that candidate side effects cannot contaminate the genuine control. No such replacement is
claimed landed on this branch.

The strongest existing next owner is still
`agent/v030-r24-compact-source-replication@9014cfa5d2b854299670a213f2386fe469d9a312`,
whose candidate-specific child worker and structural byte-owner test avoid the parent-only rebinding
error. That branch is implemented but unexecuted as of this reconciliation.

Cheapest decisive route:
1. execute the source-replication structural child-custody test;
2. if green, run unchanged global compression parity once with the correctly bound candidate;
3. a genuine red retires the compact-r24 family; a green advances only to inherited gates.

This retirement changes no product source, threshold, comparator, workload, or release authority.
