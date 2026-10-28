# r25 Shifted shared-child early-bound observability — Forge diagnosis

Status: **D2/D3 STATIC CAUSAL DIAGNOSIS / OUTER-POLLING FAMILY RETIRED / NO PRODUCT OR RELEASE CREDIT**

Decision: `SHIFTED_SHARED_OUTER_BOUND_STRUCTURALLY_TOO_LATE`

This record narrows the repository-defined successor to `SHIFTED_G04_SHARED_MIXED_OWNERSHIP`. It is code-path diagnosis, not benchmark evidence. It changes no product code, experiment grammar, archive bytes, threshold, corpus, selector, locality rule, integrity/recovery law or release authority.

## Question

Can the already-evidenced ~31 s post-PrefixGraph G0-G4 debt be removed by a cheap fail-open proof implemented *outside* the two inherited v0.28/attempt-5 builders, for example by polling partial candidate artifacts or waiting for one child and then bounding the other?

## Exact shipping path inspected

`experiments/entropygraph_v030_shared_portfolio.py::_build_shared_candidates` starts two spawned workers:

- accepted v0.28 candidate;
- attempt-5 pre-fallback graph candidate.

The parent then blocks on one terminal queue result per child, joins both processes, and only afterward reads `v028.cmpct` and `attempt5-prefallback.cmpct` sizes. There is no progress receipt, monotone forced-byte counter, or partial-artifact contract exposed to the parent.

The same module applies G0-G4 only *after* both candidate artifacts exist. Prior causal evidence measures the parallel child pair at ~29.68 s, with attempt-5 consuming ~99.69% of that makespan and v0.28 ~79.55%.

## Why outer polling is not a legal proof

A temporary output file's current length is not a lower bound on the final candidate unless the writer's publication protocol explicitly makes it monotone forced state. Neither inherited worker exports such a contract. Treating an observed temporary size, path existence, elapsed time, corpus identity, or historical winner as a pruning signal could terminate a future winner and would violate exact tournament semantics.

Waiting until the completed attempt-5 graph exists is also too late for the primary opportunity: G0-G4 overlay work occurs after the ~29.6 s child owner has already finished. A sound lower bound applied only while overlay records are auditioned can save overlay work, but cannot recover the dominant inherited-child wall.

## Attempt-5 internal seam

Inspection of `entropygraph_v029_mosaic_placement.py::_build_graph` shows that complete serialized bytes are decided only after substantial upstream work:

1. read/chunk/deduplicate source nodes;
2. construct similarity sketches and broad candidate pairs;
3. run exact delta auditions over candidate edges;
4. choose central bases and physical pack groups;
5. run mosaic subset/placement trials;
6. finally assemble the graph representation.

A PrefixGraph-style terminal law — `strict forced complete-artifact lower bound > incumbent bytes` with unseen payload and metadata optimistically priced at zero — is sound only when the counted bytes are already unavoidable under every continuation. In attempt-5, many payload/placement choices remain replaceable until after the expensive edge/mosaic decisions. Therefore simply transplanting the existing PrefixGraph lower-bound check at serialization time is causally too late.

## Forge consequence

The following nearby intervention families are retired as the *primary* Shifted fix under the tested regime:

- parent-side partial-file-size polling;
- post-child G0-G4 overlay-only lower bounds;
- elapsed-time or workload-identity cancellation;
- attempt-5-only cancellation that ignores the concurrently live v0.28 floor;
- equality pruning or any heuristic estimate that can remove a possible strict winner.

The next justified intervention must operate inside, or before, the dominant shared-child work. Two viable classes remain:

1. **early exact forced-state checkpoints inside both builders**: expose only bytes/properties that are mathematically unavoidable under every continuation and cancel each child only on strict `lower_bound > PrefixGraph incumbent`;
2. **a cheaper candidate-specific admission proof before expensive graph auditions**: prove from exact source/grammar invariants that neither inherited candidate can beat the incumbent, failing open whenever the proof is unavailable.

If neither class can produce a proof before a material fraction of the ~23.6 s v0.28 and ~29.6 s attempt-5 work has elapsed, the stopping-proof family should be retired for this Shifted regime and Forge should escalate rather than hiding the debt behind a heuristic.

## Carrying-cost rule

Any deployable proof must account for its own global nomination/probe cost on non-Shifted workloads and false neighbors. Persistent side metadata or a new parser-visible proof format is not free; prefer an in-memory admission/checkpoint proof that changes no archive grammar if it can be made exact.

## Reopening predicate

Reopen an outer/post-child stopping strategy only if the builders gain a durable monotone progress contract whose reported state is itself a proven lower bound on final complete bytes, or if new timing evidence shows the dominant child work has moved after that observable checkpoint.

## Strongest self-critique

This diagnosis proves where an outer proof cannot legally act; it does not yet prove that an early internal bound exists or that it fires soon enough. The next result-bearing experiment must measure **proof firing time and avoided child work**, preserve exact winner identity, and fail open on every case where the bound is not decisive.
