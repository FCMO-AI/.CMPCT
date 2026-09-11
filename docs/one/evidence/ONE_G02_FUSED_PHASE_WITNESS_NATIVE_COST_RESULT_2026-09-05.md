# ONE-G0.2 — fused phase-witness native carrying-cost result

Date: 2026-09-05
Experimental line: ONE-G0.2
Decision: **retire unconditional fused phase witness**

## Exact evidence

- source: `df083da415fb8aa426c3f6a1ed84cd6d25f5e32d`
- workflow: `33973449301`
- job: `101325924360`
- artifact: `9971607895`
- artifact digest: `sha256:d98b9c280c557b19b8c523bff5daccbca3e8d8965e10fa7840beba44a2b5bf80`
- pre-result ONE semantic/hostile tests: **pass**
- native witness/reference mismatches: **0**
- modeled incremental retained discovery state: **248 B**

## Referee question

Can the already-validated five-phase, bottom-4 relation certificate be carried unconditionally inside the already-required byte observation pass cheaply enough to eliminate its standalone payload rescan?

Frozen large-gate requirement: median fused/baseline <=1.12x; random and compressed-like <=1.15x; every ~1 MiB control <=1.18x; 4 KiB <=1.30x; 64 B <=1.50x.

## Result

The semantic fusion is exact, but the compute economics fail by a wide margin.

| control | fused / baseline |
|---|---:|
| random 1 MiB | 2.7044x |
| compressed-like ~1 MiB | 2.9138x |
| repeated 1 MiB | 2.8829x |
| shifted/versioned 1 MiB | 2.4762x |
| zeros 1 MiB | 2.7600x |
| alternating hostile 1 MiB | 2.9077x |
| random 4 KiB | 3.2088x |
| random 64 B | 3.0203x |

Five-large-control median: **2.7600x**.

The result is not a near miss and must not be rehabilitated by relaxing the gate or reducing the frozen phase/witness settings on this same cohort.

## Strongest causal observations

The failure cannot be blamed on witness semantics or state size: exact tuples match the independent reference and the retained state is only 248 B. It is a hot-loop compute/exported-work problem.

The full 16-repetition ~1 MiB rows sampled about 2.62 million phase windows. Bottom-K replacement counts were tiny by comparison (0–3,168 across those repetitions), so replacement frequency alone is not evidence that heap maintenance owns the bill. Conversely, that sparsity does not prove hashing owns it because phase testing, raw-word maintenance, branches, and top-K admission checks still execute frequently.

The parent preregistration therefore requires a measured decomposition before attempting a repair.

## Hostile Reviewer

This experiment proves only that **this unconditional native carrying shape is uneconomic**. It does not falsify the structural relation certificate, the shared-observer + cold-fallback complementarity evidence, or the ONE Law representation that consumes surviving exact relations.

The tempting but invalid response would be to choose fewer phases/witnesses after seeing these timing rows. That would mix structural coverage and timing thresholds post hoc and could silently reintroduce the hostile misses that forced the richer certificate.

## Next decisive action

Run the frozen native owner decomposition in `ONE_G02_FUSED_PHASE_WITNESS_OWNER_DECOMPOSITION_PREREG_2026-09-05.md`, separating:

1. 8-byte raw-window maintenance;
2. phase scheduling + frozen hash;
3. bottom-K witness maintenance.

Only after the stable owner (or co-dominant cluster) is measured should the next Builder change mechanism shape.

No density, reader-speed, format, product, v0.29, or deferred-v0.30 claim follows from this result.