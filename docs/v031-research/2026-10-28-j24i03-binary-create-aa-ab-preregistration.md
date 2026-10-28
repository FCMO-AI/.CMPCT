# J24I03 — source-locked binary-create A/A vs A/B attribution (preregistered)

**Status:** PROSPECTIVE / not yet measured. **Date:** 2026-10-28 UTC. Research-only; no product, archive format, release gate, benchmark threshold or test change. This file was committed before the diagnostic instrument and workflow.

## Exact-source question

Why does the official r24/ZIP parity gate reject otherwise-green composition PR #704? On identical parity trees and unchanged scoring, the first hosted ABBA reports binary/library/create base 139.4093305 ms, candidate 171.2223795 ms (+22.8199%, +31.813049 ms); attempt 2 on the **same source head** reports base 168.996 ms, candidate 199.053 ms (+17.79%). Both authentic release-gate negatives remain authoritative. Other same-tree rows and binary/CLI control do not explain the specific library-create anomaly. A control on older unrelated source pair #238 demonstrated A/A and A/B ~neutral, but cannot be inherited as a #704 attribution verdict.

- Exact candidate product source: `#704@293aa161a4a13b4c1f4fd0f5089aa62e4dbeedef`.
- Exact comparator product source: `#699@4de43609046ceaba93902e6680af3b4059aee49f`.
- Reader constructor is the only modified **product** function; `src/cmpct/builder.py` and `src/cmpct/codec.py` are unchanged.
- `benchmarks/zip_parity_bench.py` times `Builder(src).build(out)` for binary/library/create; it imports Reader but does not call `CMPCT.__init__` in its timed create closure.
- Existing #238 owns historical #234→#235 sham, not this exact #699→#704 comparison. This J24I03 is an explicitly preregistered independent exact-source replication of the *different* and currently release-blocking question; it does not edit #238 or #704.

## Mechanism, controls and alternative explanation

**Hypothesis H1 (source-attributable):** in a fixed process/time/CPU environment, candidate #704 consistently slows native binary create relative to #699 by more than both +5% AND +3 ms in the same-input library operation even after excluding process startup, while base/base A/A is neutral. This would indicate previously unobserved process-level coupling despite apparent static callgraph nonintersection.

**H0 (environment/order artifact):** +17–23% official reds reflect runner chronology, CPU contention/import/memory state or other uncontrolled full-matrix effects. On individually warmed, independently sourced *interleaved* subprocess creation with the exact same binary tree, A/A and A/B ratios are indistinguishable, or A/A sham itself crosses gate-scale margin.

**Stronger simpler control:** exact-base `#699` loaded under two different experiment labels A and A2. A/A sham repeated in reversed order alongside source-paired A/B. The same canonical files and metadata, complete archive SHA, native payload custody and imported module paths must agree. Unlike a full benchmark rerun, this isolates just the decisive operation and excludes process startup from each timed sample.

## Frozen experimental design

1. Derive one deterministic binary parity input from the unchanged `benchmarks/universal_bench.py`, with fixed nanosecond mtimes, on Ubuntu 24.04/Python 3.11; record SHA-256 of each file and executable provenance.
2. Check out #699 **exact** as a separate engine, retain #704 **exact** as candidate product code in a child science branch, and bind both SHA trees plus installed native ownership. No mutable `main`/development assumptions.
3. Execute source-independent separately spawned/warmed subprocess samples in A/A and A/B ABBA orders; 8 groups per court × 7 samples per group (at least 28 timed samples/side/court); preserve individual wall and process CPU, per-group medians, complete deterministic archive SHA/bytes, RSS and module-source identity.
4. An independent evaluator must recompute medians from raw samples and reject altered totals/source identities/expected archive hashes. The control is `A` versus `A2` with the same base code. A full-matrix official red is never treated as green on the strength of this exploratory court.
5. Test a chronology-balanced alternate order (BAAB or a rotated sequence) when feasible. Preserve negative results, even if the new court fails to explain the original official gate.

## Prospective discriminators

- **Credible candidate regression:** A/A wall delta below 5% and 3 ms; A/B wall **and** process-CPU both exceed 5% AND 3 ms, with the same sign across at least three of four matched paired groups and no archive identity drift. This diagnoses a repeatable in-process difference, not the cause in source.
- **No candidate attribution at this rung:** A/A is stable while A/B fails the above prospective materiality, or A/A itself crosses a gate-scale margin. Record separately whether null results are precision limited.
- **Invalid court:** any cross-source archive bytes or semantics differ; missing native provenance, source/wheel/module identity, corpus hash or raw process samples. Do not infer timing economics from invalid evidence.

## Promotion and product boundary

The official first and second ABBA **FAILURE** remain publication vetoes regardless of court result. No changes to the zero-byte floor, timing thresholds, comparator, test semantics, release, historical records or frozen experiments are authorized by this diagnostic. A possible next action is a controlled same-source full-matrix repeat/true double-blind runner experiment, chosen only when the cheap court changes that decision.

**Decision-contingent next:** if source-attributable, profile package startup/global import and Builder binary path with verified deterministic inputs; if not replicated, investigate full-matrix runner chronology/scheduler and A/A sham before changing product code. Only update discovery state after decision-changing durable result, and coordinate with #704 and #238 owners.
