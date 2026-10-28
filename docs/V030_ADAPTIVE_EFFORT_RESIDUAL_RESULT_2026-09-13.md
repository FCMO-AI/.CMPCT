# v0.30 adaptive-effort residual referee — 2026-09-13

Status: **research evidence; no release or R4 credit**

Measured branch: `agent/v030-authoritative-integration`
Exact measured head: `4537bb848824f87db7a0fd82e5663d727b67aa90`
Hosted run: `34773959099`
Historical policy source: `experiments/entropygraph_v030_federated_adaptive_effort_candidate_v8.py`
Historical policy git blob: `dc76dbfb17b8157cf453c2bb21c27459b34b1b7c`
Scientific verdict: `EFFORT_POLICY_INSUFFICIENT`

## Question

Can the already-existing generic C25EG08 adaptive-effort policy capture most of the fixed-geometry Zstd-19 headroom identified by H-EFFORT-1 without tuning or workload identity?

The policy was replayed exactly: keep current level-1 payload as incumbent; never recompress hot stream roots; try levels 3, 6, 12 and 19; continue after a strict win or tie; stop on the first strictly worse next effort. Levels 9 and 15 were observation-only and could not affect the selected artifact.

The referee froze the current Office/Analytics physical geometry and required exact level-1 physical reproduction before attribution. Policy and oracle therefore operate on identical raw physical units; neither counterfactual receives product/release credit.

## Result

| Surface | Policy share of L19 oracle | Policy CPU / L19 CPU | Residual vs L19 | Hot residual | Cold residual | Early-stop misses | Observation-only 9/15 recovered |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Office | **99.8%** | **72.1%** | **1,134 B** | **0 B** | **1,134 B** | **3 packs / 1,134 B** | **3 packs / 1,134 B** |
| Analytics | **56.9%** | **70.9%** | **414,213 B** | **0 B** | **414,213 B** | **20 packs / 414,213 B** | **21 packs / 222,490 B** |

Analytics fails the preregistered >=80% sufficiency floor, so the unchanged historical policy is retired as a complete answer to H-EFFORT-2.

The residual is not the result of preserving hot-stream latency. It is **100% cold** on both surfaces. In Analytics the five largest residual packs account for **96.2%** of the remaining bytes.

Most importantly, the early-stop diagnostic exactly accounts for the residual: every byte of residual is attached to packs where the historical policy stopped after the first strictly worse effort rung even though a later effort rung became better again. The observation-only levels 9/15 recover 222,490 B of the Analytics residual without touching hot roots, directly demonstrating non-monotonic compression-effort curves.

## Interpretation

The causal defect is therefore narrower than "adaptive compression is insufficient." The current C25EG08 stop law assumes that, once additional Zstd effort becomes strictly worse, still-higher effort is no longer worth evaluating. That monotonicity assumption is false on the measured cold packs.

This result does **not** authorize simply evaluating level 19 everywhere. H-EFFORT-1 already showed that global level 19 recovers the byte headroom but exports substantial creation CPU, especially on Analytics. The next question is whether an already-existing later generic policy, or a cheap pre-expensive observable, can recognize the small residual family without workload/path identity and without paying the full oracle cost on every pack.

No threshold may be derived from these two target workloads and promoted directly. Any new selector must be preregistered, preserve the fixed geometry/locality/integrity/recovery semantics, and transfer unchanged to held-out structured workloads.

## Score custody

Genesis remains unchanged: ONE-G0.2 `275,219,901 B`, frozen v0.29 `137,499,525 B`, frozen v0.30 `150,055,575 B`; Genesis creation CPU remains ONE `3.0791 s`, v0.29 `806.5369 s`, v0.30 `33.0603 s`. The previously adjudicated composed R4 remains `138,616,788 B`. This referee is attribution evidence only.
