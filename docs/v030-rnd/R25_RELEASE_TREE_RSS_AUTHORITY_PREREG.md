# v0.30 whole-process-tree RSS release authority — frozen custody preregistration

Status: **FROZEN CUSTODY / RELEASE-ACCOUNTING RATChet / ZERO RELEASE CREDIT BY ITSELF**

## Why this authority exists

The promoted v0.30 product now contains a bounded PrefixGraph helper-process path. The existing paired runtime authority records Linux `resource.getrusage(RUSAGE_SELF).ru_maxrss` inside the fresh operation worker. That metric remains valid for the worker process itself and its timing/size receipt remains durable, but `RUSAGE_SELF` cannot charge memory resident in a live descendant process.

Moving work into a child must never manufacture a release-memory improvement by moving bytes outside the accounting boundary. Resource safety is a hard release fact, not borrowable optimization debt. Therefore, once the product may create descendants, parent-only RSS is insufficient to satisfy the existing peak-memory release requirement.

This preregistration adds a **strictly stronger accounting authority**. It changes no workload, product, archive byte, timing boundary, ratio ceiling, comparator, locality/decode-unit rule, recovery/integrity condition, platform requirement, or release threshold. The old parent-only receipt remains historical evidence; it simply cannot by itself unlock the memory gate for a process-spawning product.

## Frozen target and comparator contract

Inherit exactly from `benchmarks/v030_release_performance.py` and the canonical v2 binding:

- targets:
  - `resemblance_hostile_v1 / 01_shifted_versions`;
  - `neutral_hostile_v1 / 05_logs_and_telemetry`;
  - `neutral_hostile_v1 / 09_ml_artifacts`;
- balanced repetition order: v0.29-first then v0.30-first, followed by v0.30-first then v0.29-first;
- v0.29 remains the accepted historical runtime baseline;
- v0.30 remains the promoted `experiments.entropygraph_v030_release_product` front door;
- the same deterministic corpus generators and accepted historical identities remain mandatory;
- zero archive-size regressions remain mandatory;
- timing ratios remain exactly:
  - median create `<=1.10x`;
  - every workload create `<=1.25x`;
  - median extract `<=1.10x`;
  - every workload extract `<=1.25x`;
- **peak RSS ratio remains exactly `<=1.25x`**.

Nothing in this authority permits a threshold change after observation.

## Frozen whole-process-tree RSS measurement

Each ordinary v2 performance worker remains a fresh subprocess and continues to own the operation timer and its parent-process `ru_maxrss` diagnostic.

The new harness samples the live Linux process tree rooted at that worker PID every **10 ms** using `/proc/<pid>/status` plus `/proc/<pid>/task/<pid>/children` recursively.

For every operation receipt:

1. `parent_peak_rss_kib` is the worker-reported `RUSAGE_SELF` high-water;
2. `sampled_tree_peak_rss_kib` is the maximum sampled sum of resident `VmRSS` for the worker plus every live descendant;
3. decisive `peak_rss_kib` is `max(parent_peak_rss_kib, sampled_tree_peak_rss_kib)` so sampling can never reduce the inherited parent high-water;
4. the receipt records sample count and maximum live process count;
5. a v0.30 pack that creates the PrefixGraph helper receives no exemption: helper RSS is charged while that process exists;
6. worker `wall_s` is retained unchanged, so the external sampler does not redefine the frozen operation timing boundary.

The sampler itself lives outside the measured worker process and its own RSS is not charged to either codec. Its CPU overhead is symmetric within the paired same-run comparison. The 10 ms interval matches the already reviewed S6 whole-tree ownership instrument.

This authority is Linux-hosted because `/proc` is the measurement substrate. Platform-specific product correctness and portability remain governed by the existing Windows/macOS/Android/native authorities; this benchmark does not replace them.

## Frozen identity and honesty gates

Before interpreting ratios, the instrument must prove:

- exact three-target contract;
- the same accepted v0.29 byte floors and source identities as the canonical runtime gate;
- v0.30 canonical user-tree identity for pack/verify/extract;
- `candidate_fingerprint` equals the exact release-lock fingerprint at invocation;
- every decisive tree peak is `>=` its worker-reported parent `ru_maxrss`;
- every measured worker has at least one tree sample;
- no size regression;
- no benchmark or release threshold changed;
- release credit remains false unless the full repository release chain independently passes.

## Interpretation

The previous parent-only runtime authority remains useful for timing, bytes and parent-process diagnostics. Its RSS column is scoped to parent-process high-water after process isolation entered the product and must not be called complete-product memory authority by itself.

The whole-tree result becomes the required resource-accounting companion for v0.30 while descendants are possible. If it is materially worse than parent-only RSS, preserve the exported child-memory debt and attack it. If it closely matches parent-only RSS, that is positive evidence that process isolation truly shortened overlapping lifetime rather than merely moving the allocation into another PID.

A green whole-tree RSS ratio still grants no standalone release credit: all existing create/extract, size, correctness, recovery, native/platform and final-release requirements remain unchanged.

## Release law

**v0.30 may not be unlocked on parent-only RSS evidence while the promoted product can spawn the PrefixGraph helper.**

This is a tightening of measurement completeness, not a relaxation of the memory gate.
