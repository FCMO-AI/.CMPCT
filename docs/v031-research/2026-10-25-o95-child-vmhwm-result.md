# O95 — Authentic child-local VmHWM O63/O86 memory attribution: result

**Date:** 2026-10-25 UTC. **Scientific decision:** `MATERIAL_O63_CHILD_VMHWM_DIFFERENCE_ON_TESTED_FAMILY` — preregistered positive hypothesis **CONFIRMED** on both tested 65 MiB-expanded ZIP families. This is Linux/installed-product research, not product release authority.

## Prospective identity and original result-bearing evidence

- Immutable preregistration at `3ce0088132bdc001458f6864a64670936c322864` preceded O95 instrument/workflow and outcomes.
- Original O95 genuine CI [Actions #40214780817](https://github.com/FCMO-AI/.CMPCT/actions/runs/40214780817), source-exact research HEAD `dc9b90d3e654fd56c2a0ed8723506690e78f8275`, **SUCCESS**, 18/18 installed-original Builder+Reader child process observations on Ubuntu 24.04, zero failed or skipped scientific children.
- Original raw [artifact #12607490284](https://github.com/FCMO-AI/.CMPCT/actions/runs/40214780817/artifacts/12607490284), SHA-256 `5ec8165b1cbd6d644f46dca31a3edee154c35b58a47b2c430283484d1dce4526`; includes all raw observations, per-stage Linux kernel status, stdout, exact Git identities, source SHA-256 and archive SHA-256.
- Historical original O63 `18e32cae012f5dca9fc47f10d194f8b81005c85c`; historical original O86 `6225e30f3e21c0783aa56726b52a3a3583540f99`. Exact installed Builder and codec blobs verified. Unchanged O88 generator blob `2acd2d9ea862b9f018bf1838f89dd2efa3807971`. The source ZIP bytes were identical between engines on every case.
- Original measurement came **before this result document was committed**; this document contains no redefinition of the original hypothesis or results. A later exact-head reexecution is separately necessary to claim independent replication of any final-document head.

## Median genuine observations (three independent child executions per arm / family)

All `VmHWM` and `ru_maxrss` values below are KiB. The `VmHWM` values come from each benchmark child `/proc/self/status` rather than the parent-inheritable `resource.ru_maxrss` metric.

| Same-source cohort | O63 child VmHWM after Builder | O86 child VmHWM after Builder | O63 − O86 (KiB) | O63 archive bytes | O86 archive bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| shared_low / 1 MiB | 30,272 | 30,168 | +104 | 18,344 | 18,344 |
| **shared_over / 65 MiB** | **304,756** | **32,120** | **+272,636** | 664,428 | 52,641 |
| **independent_over / 65 MiB** | **371,456** | **32,000** | **+339,456** | 913,287 | 52,567 |

The pre-import `VmHWM` for all six arm/cohort groups was approximately **19 MiB**. Importing CMPCT alone reached approximately 23 MiB. The new high-water in O63 arose during Builder creation. O86 maintained approximately 32 MiB on the above-budget cohorts.

For the same source cases, O63/O86 *pre-import* `ru_maxrss` were identical at **300,696 KiB** on shared_over and **301,544 KiB** on independent_over — despite independently measured pre-import child `VmHWM` being approximately 19 MiB. This directly connects the O92c inherited-accounting mechanism to the authentic original product comparison.

O63 `VmHWM` after Reader verify, selected reads and extraction **did not exceed** the post-Builder high-water on these cases. O86 likewise stayed at its post-Builder high-water.

## CPU and other independent costs

| Cohort | O63 create CPU (median) | O86 create CPU (median) | O63 create wall (median) | O86 create wall (median) |
| --- | ---: | ---: | ---: | ---: |
| shared_low | 31.102 ms | 31.756 ms | 31.110 ms | 31.757 ms |
| shared_over | 1,323.357 ms | 8.683 ms | 1,323.596 ms | 8.684 ms |
| independent_over | 1,379.635 ms | 8.697 ms | 1,379.898 ms | 8.698 ms |

Exact source SHA-256, archive SHA-256 determinism, representation admission, Builder, Reader `verify()`, individual read and `extractall(metadata=False)` all passed. O86 used `S_BLOB` above budget; O63 used `S_VZIP`. Under budget archive SHA-256 matched exactly. These are authentic source-exact product results **only on three synthetic O88 structural families**.

## Falsification, mechanism and counterfactual

**Primary preregistered memory-discriminator result: confirmed.** The 8 MiB threshold was exceeded by a very wide margin in both above-budget structures, while the low case is essentially tied. `ru_maxrss` was visibly inherited and could mask the O86 low true peak. The corrected child `VmHWM` mechanism changed a material scientific decision: **O86 is not merely avoiding CPU and stored bytes; in these cases its speculative-VZIP avoidance also removes approximately 266 and 332 MiB of child peak resident memory relative to original O63**. This is a measured cohort-specific inference, not a guarantee of all ZIPs.

**Strongest negative/self-critique:** `VmHWM` represents whole-process peak, not isolated codec allocations. Linux kernel watermarks and Python allocator retention do not give a function-level attribution. Synthetic 65 MiB expanded members, one runner family and just three repetitions per arm are not a held-out population sample; O86 may lose legitimate large positive-VZIP opportunities on other inputs. O63/O86 have different algorithmic paths intentionally. No separate memory profiler, temporary I/O, random-access amplification, portable Windows/macOS RSS, official release performance gate or integration with all Builder branches was measured. The apparent under-budget memory tie is not a global performance parity claim.

**Counterfactual discriminator:** sampling both `ru_maxrss` and child-local `VmHWM` *at the first line of the child benchmark* would have invalidated the old ~300 MiB O86-memory claim immediately. Future Linux child-process benchmarks should prospectively capture kernel high-water alongside other process metrics. No change to discovery-policy law is earned from a single family of experiments; the lesson belongs in this local case until broader repeated process failures warrant policy mutation.

## Concurrency, next action, release boundary

O95 is a science-only branch stacked on #450. It does not modify #444 O86, #447 O88, #450 O92 or current canon; concurrent O94 framed-PACK ownership and O90/O93 Builder safety remain independently owned. Inform those owners of corrected memory attribution with this exact-head artifact. The next product-facing decision is to evaluate O86's effect on held-out ZIP structures and integration economics; do not tune its 64 MiB budget to these fixtures or translate a resource-bound mechanism into an unearned release claim.

**Product change: none. Format change: none. Public release credit: zero.**
