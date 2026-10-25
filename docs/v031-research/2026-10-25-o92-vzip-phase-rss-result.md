# O92 — Phase-attributed memory high-water witness: result

Date: 2026-10-25 UTC
Source-bound product observation: **CONFIRMED**. Research inference: **Reader-lift hypothesis falsified**.

## Sources and custody

- Exact preregistration: `43ccdf653140531c694f558925d5d894a20d5e99`.
- Measured O92 instrument+workflow HEAD: `604d33f69d75160d53ba6e22773da76f7865a005`.
- Genuine Ubuntu 24.04 GitHub Actions [run #40210177911](https://github.com/FCMO-AI/.CMPCT/actions/runs/40210177911): **SUCCESS**, all actual hosted steps executed, `O92_ACTUAL_EXECUTED_INSTALLED_PROCESSES=6`, zero skipped or invalid runs.
- Raw original [artifact #12605840118](https://github.com/FCMO-AI/.CMPCT/actions/runs/40210177911/artifacts/12605840118) (digest recorded by GitHub as `sha256:973f21766f27241fcd1ebc335af6841793700bc7e0eeff3bc4128f95b0cc4b5a`).
- Historical original O63 `18e32cae012f5dca9fc47f10d194f8b81005c85c`, candidate O86 `6225e30f3e21c0783aa56726b52a3a3583540f99`. Workflow confirms original Builder/codec Git blobs and independently installed packages. Full O88 fixture and instrument are **unchanged**.
- All six observations use the same physical shared-over cohort: three real ZIPs, 65 MiB declared uncompressed member each, exactly re-read/reconstructed. Full CMPCT sizes reproduce historical O88: O63 **664,428 B**, O86 **52,641 B**. All three archive hashes within each engine match.

## Direct measurement (medians of 3 independent children per arm)

Linux `resource.getrusage(RUSAGE_SELF).ru_maxrss` is process peak high-water KiB, **not** a snapshot of live heap or Builder-only allocations.

| Product phase | O63 KiB | O86 KiB |
| --- | ---: | ---: |
| After importing installed CMPCT modules, **before Builder exists** | **300,348** | **300,348** |
| After `Builder.build()` | **304,716** | **300,348** |
| After `Reader.verify()` | **304,716** | **300,348** |
| After 3 `Reader.read()` calls | **304,716** | **300,348** |
| After `Reader.extractall(metadata=False)` | **304,716** | **300,348** |

O63 post-build minus O86 post-build: **+4,368 KiB**. Reader-phase increase in reported process peak: **0 KiB for both**.

## Decision / hypothesis dispositions

**Primary prospective Reader-lift explanation is FALSIFIED.** This run reached its ~300 MiB process high-water mark **before** constructing the Builder. Reader verification/reads/extraction added no *new high-water mark*; this does **not** establish zero Reader allocations or no transient memory use hidden below the already-reached peak.

The finding corrects the source of the apparently identical O88 300 MiB whole-process memory numbers: it is **not** attributable from these observations to either the Builder or the Reader. The earliest measured phase is already high. O63 caused a further +4,368 KiB peak relative to O86 in this one cohort. The dominant residual is **pre-build/import/startup memory attribution**, a new fork requiring a cheaper isolated import-stage discriminator. This may also reflect native/library loading or another startup effect, not necessarily a Python package leak.

O88 remains truthful for full-process peak, full archive bytes, CPU and reconstruction. O92 does not revise its measurements and does not prove O86 reduces 300 MiB of Builder RSS. The 64 MiB budget is not a universal memory ceiling.

## Negative / limitations / self-critique

The preregistered prediction that subsequent Reader phases would lift the common peak failed. All actual RSS stage readings are **peak-to-date**, monotonic, so memory freed between stages is not identified and the values do not measure current committed/unique memory. Three child repetitions on one Ubuntu host and one synthetic same-source family are not a portable or workload-general RSS profile. Even a real import-stage cost may be environment-dependent or library initialization rather than CMPCT-specific retained memory. No direct attribution to any particular import was measured. Do not upgrade this experiment into product-release/performance-gate evidence.

## Counterfactual and next executable action

A cheapest prospective discriminator would have captured Linux `ru_maxrss` **before package import**, then separately after imports of (a) standard-library and existing benchmark harness, (b) `cmpct` package initialization, (c) Builder, (d) Reader/native library. That would have avoided testing the weaker speculative Reader attribution first. The reusable lesson is to establish a *pre-operation resource floor* before assigning a resource peak to a codec/Builder/Reader.

Next: one isolated import-order stage-oracle (research, not product credit); stop if the 300 MiB floor belongs to a broad hosting/import layer beyond CMPCT or if timing/memory confounds prevent a causal conclusion. No change to discovery policy based on one result; no additional VZIP parameter gardening.

## Quality gates

Product correctness for the six source-exact children PASS. Scientific court SUCCESS. This is **research evidence**, not a shipping change. Official r24/ZIP parity comparison and full cross-platform/corpus memory economics remain unexecuted by O92. Do not merge/release on this basis.
