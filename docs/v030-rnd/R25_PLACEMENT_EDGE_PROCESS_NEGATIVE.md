# R25 Placement exact-edge process-cache negative

Status: **TERMINAL SCOPED NEGATIVE — DO NOT REOPEN WITHOUT THE PREDICATE BELOW**

Date: 2026-09-03

## Authority and claim boundary

This record preserves the result-bearing `CMPCT v0.30 Placement edge process oracle` execution from GitHub Actions run `33781561229`, substantive job `100736514785`.

The PR workflow checked out merge SHA `49ca94f496a6fbca8f07b05f3ffa47f68d590226`, the merge of authoritative PR #56 head `5c7459ca52ce212021fbf5c860a32708fad00459` into base `dd0c12cd6ee2dbb859464ea5c6be221ad34b9fdf`. Evidence artifact ID: `9904320029`; artifact ZIP SHA-256: `6607b77a568562bd1e7583ea371ea93e20822132b03a5c97388f5ff5bd024f6b`.

This is research/Forge evidence only. It grants **zero release credit** and changes no release, benchmark, locality, integrity, recovery, or product threshold.

## Worldview tested

The tested R2/R3 hypothesis was deliberately narrow: Placement's expensive exact delta-edge auditions on the pathological `10_large_mixed_binary` target might contain enough independent work that precomputing those exact edges with a four-process cache materially reduces total canonical graph creation time **without changing the compiler decision or bytes**.

The oracle required exact graph/archive bytes, strong verification, the intended nested-spawn topology, and a non-empty edge cache. The frozen promotion hurdle was intentionally large: at least **30%** total-create improvement **and** at least **120 seconds saved**. Ties and marginal speedups lose.

## Exact result

| Metric | Baseline | Process-edge-cache candidate |
| --- | ---: | ---: |
| total create | 380.107782927 s | 377.867059816 s |
| archive bytes | 12,609,503 B | 12,609,503 B |
| archive SHA-256 | `fdc83c9ebae0a29798fd8d949c8eab77b253e1ffa3f63d6c34f0d57b37b95537` | identical |
| tree SHA-256 | `9373f96626c7f463b4112bf138ac5db766e7e71def9b209c7ba28fe44f0878d3` | identical |
| Mosaic nodes | 1 | 1 |
| single-delta nodes | 3 | 3 |
| residual-pack records | 0 | 0 |

Candidate cache facts:

- 105 nodes;
- 95 exact edges;
- 4 workers;
- cache precompute: **7.171163603 s**.

Observed net saving: **2.240723111 s**.

Observed improvement: **0.589496772%**.

Frozen hurdle: **>=30% AND >=120 s**.

The exact-target-shape, byte-identity, tree-identity and non-empty-cache invariants all passed. The material-speed gate failed decisively.

## Decision

`PLACEMENT_EXACT_EDGE_PROCESS_CACHE_NOT_SUPPORTED`

The process-cache family is retired for this exact Placement / large-mixed-binary / exact-edge-audition regime. A 0.59% net gain is not a productization candidate and does not justify global process topology, cache lifecycle, memory, platform, parser, recovery, or portfolio carrying cost.

This is not evidence that Placement is universally impossible to accelerate. It is evidence against **parallel precomputation of this exact independent edge set as the dominant remedy**.

## Causal interpretation

The candidate did compute 95 edges with four workers and preserved byte-identical output, so the failure is not attributable to a dead code path or semantic mismatch. The mechanism simply attacks too little of the 380 s end-to-end critical path and pays 7.17 s of precompute overhead. Therefore process fan-out of the currently identified edge work cannot explain or retire the dominant Placement construction debt.

The useful constraint is architectural: future Placement speed work must eliminate or avoid a much larger category of end-to-end work (for example by proving candidates futile earlier, reducing candidate construction itself, or changing the information/search abstraction) rather than merely scheduling this already-defined edge set in parallel.

## Reopening predicate

Do not repeat worker-count, executor, batching, or nearby cache-topology sweeps for this family.

Reopen only if new causal evidence establishes at least one of:

1. a materially larger exact-edge-owned fraction of the end-to-end critical path than this oracle exposed;
2. an exact proof/admission method that removes a substantial share of candidate construction before edge work is performed;
3. a new representation/search abstraction whose required edge set is materially smaller while preserving exact selected bytes; or
4. a measured implementation change that removes most of the 7.17 s precompute/export cost **and** makes the unchanged frozen >=30% + >=120 s product-level hurdle plausibly reachable.

Without one of those predicates, further work in this local process-cache parameter family is sunk-cost repetition.
