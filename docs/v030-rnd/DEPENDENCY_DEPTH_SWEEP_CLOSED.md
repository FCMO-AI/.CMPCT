# Dependency-depth sweep — CLOSED one-off evidence

Status: **CLOSED / ONE-OFF / NOT AN ACTIVE RESEARCH FRONT**

This record preserves the lesson from a deliberately disposable research-only experiment. It is **not** a Foundry thesis, Forge campaign, roadmap item, candidate feature, promotion prerequisite, or invitation to continue tuning dependency depth. The runnable branch/instrument was intentionally treated as temporary after the result was captured.

**Canonical CMPCT policy is unchanged: resemblance dependencies remain maximum depth 1.** Nothing in this experiment authorizes a reader-visible depth increase or weakens locality, recovery, integrity, decode-unit, native/platform, or release requirements.

## Question tested

Instead of assuming that recursive delta chains are harmful, measure what actually changes if the EntropyGraph-II resemblance mechanism is allowed maximum dependency depths 1, 2, 3, 4, 5, and 6 while keeping candidate discovery/admission semantics fixed.

The sweep used the repository's deterministic resemblance-hostile workloads and independently materialized/reconstructed each tested depth. The experiment was intentionally isolated from canonical encoder/reader policy.

## Measured result

### Shifted versions

| Maximum depth | Research artifact bytes |
|---:|---:|
| 1 | 1,762,898 |
| 2 | 1,760,021 |
| 3 | 1,757,602 |
| 4 | 1,757,714 |
| 5 | 1,757,455 |
| 6 | 1,756,950 |

Depth 6 saved **5,948 B (0.337%)** relative to depth 1.

### Repeated boundary churn

| Maximum depth | Research artifact bytes |
|---:|---:|
| 1 | 90,091 |
| 2 | 89,961 |
| 3 | 89,896 |
| 4 | 89,816 |
| 5 | 89,711 |
| 6 | 89,617 |

Depth 6 saved **474 B (0.526%)** relative to depth 1.

### Hostile controls

The false-neighbor, related-DEFLATE-family, and incompressible controls admitted **no useful depth-dependent delta edges**. Raising the depth limit therefore provided no representation opportunity on those workloads.

## Causal interpretation

The important observation is that deeper chains did not unlock a large new population of delta-compressible objects. On the two workloads where depth mattered, depth 1 had already represented almost every eligible node as a delta. Additional depth mostly changed **which already-delta node served as another delta's parent**.

That explains the small byte gains and the rapid diminishing returns: deeper graphs were mostly re-parenting existing relationships, not exposing a new class of redundancy.

Creation cost was essentially unchanged in this bounded sweep because resemblance discovery and concrete delta audition were held constant and shared across depth choices. Full strong-verification time was likewise approximately flat because reconstructed ancestors were cached during whole-archive traversal.

Cold/selective reads exposed the real cost. Median cold-node latency at depth 6 was approximately **13% slower** than depth 1 on shifted versions and approximately **24.9% slower** on boundary churn. Decoded-byte amplification barely moved, showing that dependency depth can add a **serial reconstruction-latency tax** even when byte-read amplification looks nearly unchanged.

The sweep did not price the full recovery blast radius. A deeper chain also makes descendants depend on successful reconstruction of more ancestors, so the system-level case for depth >1 is weaker than the size-only numbers above suggest.

## Durable lesson

Depth 1 captured nearly all measured resemblance benefit in the tested regime. Depths 2–6 produced only **sub-percent additional size reduction** while increasing cold-read serial dependency cost and making recovery/failure reasoning less local.

Therefore this experiment **strengthens the existing depth-1 decision rather than opening a deeper-graph research front**.

This result belongs with the repository's rejected/superseded/deferred experimental evidence. Future agents must not infer an active workstream merely because historical commits or a branch name mention a dependency-depth sweep.

## Reopening predicate

Do **not** rerun or extend this family merely to try depth 7+, tune chain selection, or obtain another small scalar byte gain.

Reopen only if genuinely new causal evidence shows a **material representation opportunity unavailable at depth 1** and the proposed mechanism can plausibly pay its complete random-access, recovery/failure-domain, integrity, locality, decoder-resource, native/platform, and global carrying costs. Any reopening must be a new explicitly preregistered experiment; this closed record remains immutable evidence.
