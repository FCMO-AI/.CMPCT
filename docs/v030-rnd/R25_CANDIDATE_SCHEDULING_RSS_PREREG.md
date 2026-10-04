# r25 candidate scheduling RSS A/B — frozen Forge preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION / Forge diagnostic / no release credit**.

## Causal predecessor

`docs/v030-rnd/R25_SEMANTIC_OWNER_RSS_V2_RESULT.md` established on exact source `60543bcbb1779ecbfe1e1807b725709f8ec3d57e` that neither exact canonical candidate family reproduces the shifted-version shipping peak in isolation:

- shipping product: **400,000 KiB** median total fresh-process peak RSS;
- exact G0-G4: **180,654 KiB** (**0.451635x shipping**);
- exact PrefixGraph: **200,670 KiB** (**0.501675x shipping**).

The shipping release-candidate tournament explicitly builds G0-G4 and PrefixGraph concurrently with a two-worker `ThreadPoolExecutor` whenever PrefixGraph is eligible. That creates a falsifiable product-level hypothesis: simultaneous candidate lifetimes, rather than either representation alone, may own the shifted RSS peak.

The code path makes the hypothesis plausible; it does not prove it. This A/B is required before any production scheduler change.

## Frozen question

> On the deterministic shifted-version workload, does forcing the exact canonical G0-G4 and PrefixGraph contenders to execute serially materially reduce total fresh-process shipping peak RSS while leaving the selected complete product artifact byte-identical and tree-identical to inherited concurrent scheduling?

## Arms

Both arms execute the same canonical `release_product.build` surface in fresh processes after importing the same canonical/private graph before the RSS baseline.

### A — inherited concurrent shipping

Unmodified canonical tournament behavior: when PrefixGraph is eligible, `canonical.RC.build` uses its inherited two-worker `ThreadPoolExecutor` to overlap exact G0-G4 and exact PrefixGraph construction.

### B — exact serialized scheduling override

Before invoking the same `release_product.build`, replace **only** `canonical.RC.ThreadPoolExecutor` with an inline executor implementing the context-manager / `submit(...).result()` contract. `submit` executes the requested builder synchronously, so the existing release-candidate source naturally executes G0-G4 to completion before beginning PrefixGraph.

The override may not modify:

- `canonical.RC.G04`, `canonical.RC.PG`, `canonical.RC.READER` or their identities;
- PrefixGraph eligibility;
- candidate bytes or builder arguments;
- candidate admission, locality accounting or exact size comparison;
- strong verification or final r24/r25 product selection;
- archive grammar, integrity, recovery, decode-unit/locality bounds;
- corpus identity or benchmark thresholds.

## Workload and repetitions

Target: `resemblance_hostile_v1 / 01_shifted_versions` from the same deterministic corpus generator used by the v2 semantic-owner result.

Run two independent fresh-process repetitions per arm in alternating order:

1. concurrent -> serialized;
2. serialized -> concurrent.

The parent oracle builds the corpus once and supplies that immutable source tree to every worker.

## Validity conditions

The experiment is invalid unless all conditions hold:

1. every worker proves `canonical.RC.PG`, `canonical.RC.G04`, and `canonical.RC.READER` exact private semantic-owner identity;
2. every worker strongly verifies the final product tree;
3. every worker reports the same source tree identity;
4. both arms select the same representation;
5. serialized and concurrent final products have **identical complete byte count and physical SHA-256** in every paired repetition;
6. serialization reports that the inline executor actually accepted exactly the expected two candidate submissions on this PrefixGraph-eligible workload;
7. total fresh-process peak RSS, not baseline-subtracted `ru_maxrss`, is the causal ownership metric;
8. baseline-subtracted `ru_maxrss` remains diagnostic only;
9. no production source is modified to obtain the result.

Any byte/tree/selection mismatch invalidates causal interpretation. A faster/smaller artifact under one arm is not accepted as evidence here because the question is scheduling only.

## Decision thresholds

### Supports concurrency/lifetime ownership

The hypothesis is supported if serialized scheduling:

- preserves exact physical product identity and exact verified tree; and
- lowers median total fresh-process peak RSS by **>=20%** relative to inherited concurrent shipping.

The 20% threshold is deliberately material: v0.30's frozen release ceiling is 1.25x r24, so a tiny high-water change is not enough to justify product scheduling work.

If supported, the next Builder unit may evaluate serialized/adaptive scheduling as an R1/R2 rehabilitation candidate, but promotion still requires the full authoritative runtime/memory/selective-read gate because serialization may export creation latency.

### Retires concurrency as primary explanation

If exact serialization lowers median total peak RSS by **<10%**, retire candidate concurrency as the primary shifted-memory explanation under this regime. Escalate to other product-level retained-state/lifetime boundaries rather than repeatedly tuning worker policy.

### Ambiguous

A 10–20% reduction is diagnostic but insufficient for product intervention. Repeat only with stronger measurement quality or a narrower lifetime oracle; do not change release behavior from an ambiguous result.

## Runtime accounting

Record wall time for both arms. A memory win is not a free product win. Even if serialization clears the causal RSS threshold, any material creation slowdown becomes explicit rehabilitation debt and must pass the unchanged authoritative runtime gate before release.

## Evidence custody

The result-bearing worker/oracle/workflow are immutable once a substantive run begins. If implementation identity, archive identity, or the executor override is later found defective, preserve the old result and supersede it with a new freeze rather than editing the old grammar after seeing numbers.

This experiment grants **no release credit** by itself.
