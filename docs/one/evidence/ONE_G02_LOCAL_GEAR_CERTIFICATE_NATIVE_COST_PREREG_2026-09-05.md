# ONE-G0.2 — local Gear certificate native carrying-cost preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2
Mission lock: measure whether the structurally successful 136-byte content-local Gear certificate earns its unconditional native carrying cost when fused into the existing Gear observation loop.

## Repository state entering the experiment

The structural validation on source `0b5b60a651a909fa9bdc3aff90dbfdd45073ed23` advanced the hybrid shared-observer + local Gear certificate: 105/105 frozen rows preserved every required relation opportunity with zero false nominations. That result is nomination evidence only. It explicitly did not establish product-speed authority.

The candidate therefore remains unpromoted until native cost is paid.

## Falsifiable hypothesis

A 32-byte rolling content-local Gear certificate can be maintained in the same forward observation pass at acceptable marginal cost by reusing the prefix observer's incoming Gear-table lookup. The only unavoidable extra per-byte Gear traffic after warmup is the outgoing-byte lookup needed to remove the 32-byte-old contribution, plus rolling-state and bounded bottom-8 witness maintenance.

## Referee / disproof test

The A/B compares the same native fused observation loop in four modes:

1. `baseline`: run + prefix Gear observation only;
2. `rolling`: baseline + content-local 32-byte rolling Gear hash, with incoming Gear lookup reused;
3. `certificate`: rolling + exact bounded bottom-8 `(hash, position)` witness maintenance;
4. `certificate_no_reuse`: diagnostic only, deliberately reloads the incoming Gear value so the value of fusion itself is measurable.

The native certificate output must exactly match the Python reference `_source_certificate()` on frozen semantic vectors before timing is considered.

Frozen workload families include:

- random/incompressible 1 MiB;
- entropy-dense compressed-like 1 MiB control;
- repeated 1 MiB;
- shifted/version-like 1 MiB;
- zero/run-dominated 1 MiB;
- hostile alternating 1 MiB;
- 4 KiB and 64-byte tiny controls.

The benchmark uses repeated in-native loops so Python/FFI overhead is outside the timed work. Every mode returns a live checksum so the compiler cannot delete the observation path.

## Frozen promotion gate

The certificate advances from structural-only evidence to native-carrying-cost viability only if all of the following hold:

- native bottom-8 witnesses exactly equal the Python reference on every frozen semantic vector;
- incremental retained state remains exactly **136 bytes** under the already-frozen model;
- median `certificate / baseline` elapsed ratio across the five 1 MiB non-tiny controls is **<= 1.20x**;
- neither random/incompressible nor compressed-like 1 MiB exceeds **1.25x**;
- no 1 MiB case exceeds **1.35x**;
- the fused certificate is not slower than `certificate_no_reuse` by more than 3% median on large controls (a larger loss would indicate that the alleged lookup fusion is not actually realized);
- all pre-existing ONE semantic/hostile tests pass before the benchmark.

This is deliberately a viability gate, not a final writer-promotion gate. Even a pass only licenses the next end-to-end nomination/proof A/B where recovered useful relation bytes must repay this carrying cost.

## Mandatory accounting

Report, per workload:

- baseline, rolling, certificate, and no-reuse median native nanoseconds;
- elapsed ratios;
- bytes scanned;
- modeled extra outgoing-byte reads;
- baseline and extra Gear-table lookups;
- bottom-8 replacement count;
- retained-state delta;
- exact witness equality.

## Hostile Reviewer boundary

A failure retires **unconditional maintenance of this exact 32-byte/bottom-8 certificate shape**. It does not erase the structural result. Do not tune the window, witness count, or thresholds after seeing the result. A failed cost gate should instead ask whether the complementary content-local evidence can be made sparse or derived from already-sampled observer states while preserving the established hostile coverage.

No reader-visible ONE operation changes in this experiment. The reader performs no discovery. No v0.30 mechanism development is resumed.