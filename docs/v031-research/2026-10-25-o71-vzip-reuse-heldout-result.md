# O71 — Actual held-out cross-object VZIP admission decision

Date: 2026-10-25 UTC. Scope: **research oracle only**, not a shipped CMPCT improvement or release result.

## Source and prospective custody

- Preregistration committed first: `98c32b5e955a57f4143a886cdf4e8f1be134b059`.
- Exact **result-bearing** instrument/workflow HEAD: `795458dffc2c6da4b3cde91b92ce769292c6cf88`; authentic O63 parent: `18e32cae012f5dca9fc47f10d194f8b81005c85c`.
- Actual installed Builder Git blob: `382e60983bf1e8e7595ea7112f3a5553dc33dcc0`; codec: `dc3446b0eed82edfba9380e3885a20aa45577899`; instrument: `7ada94bcf1259865201901ef4cf6dc13348cdfc2`.
- Hosted result: [source-exact GitHub Actions #40179516645](https://github.com/FCMO-AI/.CMPCT/actions/runs/40179516645), SUCCESS. [Raw artifact #12593755705](https://github.com/FCMO-AI/.CMPCT/actions/runs/40179516645/artifacts/12593755705).
- Downloaded independent ZIP SHA-256: `24ba7b6019cbf7968ec94269ca6347e1362181b39f51e3348ce39c93e5601c8f`. Independently parsed full raw JSON SHA-256: `5c9678ec84abffc6b16fa97fc1cc1fcd466e73593d17177ba17d6a53ef62043b`.
- Independently checked original 42/42 per-process observations, 7/7 paired source hash sets, 3 observations per mode/case, deterministic within-arm final archive SHA, stored-byte arithmetic, source blobs. Original artifact preserved; subsequent commits must not reattribute its result to a new HEAD.

## Direct complete-product observation (medians within each matched three-process arm)

| Family (each 1 MiB logical member) | Lowest ZIP logical/physical ratio | Original O63 VZIP .cmpct bytes | Opaque oracle .cmpct bytes | Virtual − opaque B | Create CPU VZIP ms | Opaque CPU ms | Actual S_VZIP members |
|---|---:|---:|---:|---:|---:|---:|---:|
| Singleton repeated | 905.51× | 1,245 | **990** | +255 | 10.190 | 0.439 | 1/1 |
| Shared repeated, Deflate 1/6/9 | 222.39× | 1,840 | **1,442** | +398 | 20.642 | 0.658 | 3/3 |
| Shared textual, Deflate 1/6/9 | 152.74× | 1,965 | **1,851** | +114 | 16.721 | 0.693 | 3/3 |
| **Shared mixed-entropy, Deflate 1/6/9** | **44.96×** | **18,334** | 53,113 | **−34,779** | 18.735 | **1.228** | 3/3 |
| Independent repeated, Deflate 1/6/9 | 222.39× | 2,103 | **1,441** | +662 | 20.071 | 0.649 | 3/3 |
| Shared repeated, same level, different ZIP metadata | 905.51× | 1,809 | **1,410** | +399 | 23.532 | 0.542 | 3/3 |
| Shared incompressible random, levels 1/6/9 | 0.9996× | **2,099,685** | 3,148,132 | **−1,048,447** | 123.123 | **11.798** | 3/3 |

All original ZIP files were checked with stdlib; genuine r24 archive `CMPCT.read()`, `verify()`, and full `extractall()` succeeded in both arms, on the same source SHA sets. Process CPU excludes Python startup, whereas the fresh process itself includes interpreter and imported packages in its RSS observation. Artifact reproducibility was checked within each arm. Verification/extraction wall medians were recorded separately in raw JSON, not charged to creation.

**Prospectively specified decision: `COUNTEREXAMPLE_OBSERVED`.** High-ratio mixed-content ZIP siblings sharing exact decompressed data saved **34,779 complete bytes (65.48% relative to opaque)** even though the least-compressible member still represented a **44.96×** logical/physical expansion. A blanket skip-VZIP rule based on expansion ratio alone would reject this real r24 byte winner. VZIP paid **~15.25× creation CPU** and **~10× verify/read/extract wall** in this particular matched case. The gain must not be described as joint Pareto product domination.

Another positive exists at the opposite entropy extreme: unrelated physical Deflate streams for the same incompressible expanded payload, ratio ~1×, save **1,048,447 B**, but incur **~10.44×** create CPU. This establishes the independence of expansion ratio and cross-object reuse benefit; it does not establish an acceptable shipping heuristic.

## Strongest negative and causal self-review

The three other high-ratio shared-identity families (pure repetition, textual repetition, same Deflate level/different metadata) **lose complete bytes as well as CPU**. Mere raw-content equality does not guarantee a VZIP win: opaque compression can encode the physical streams more cheaply than a decomposed recipe. The mixed family’s advantage is *consistent* with exact logical-owner reuse in the presence of byte-distinct Deflate streams, but the currently matched **unrelated-repeat control does not have the same entropy profile**. A stronger independent **unrelated-mixed** contrast must be run prospectively before claiming that exact source identity, rather than simply material entropy and encoder packaging, caused the 34,779 B advantage.

Memory: per-process peak RSS medians were observed, but allocator and peak virtual-memory economics were not isolated. Results are Ubuntu installed CPython 3.11 synthetic workloads, not independently ported Windows/macOS data nor broad mixed real-world corpora; changed physical container origin is not tested. Frozen 15-row performance or external ZIP/Zstd gate did not execute from this research result. Broad release-readiness remains unmeasured.

## Decision and handoff

- **Rejected:** any global rule that simply refuses VZIP whenever ZIP logical/physical expansion is above 32×, 44× or 50×. That rule loses the demonstrated exact 44.96×, 34,779-B gain.
- **Supported:** distinguish `reconstruction headroom from cross-container ownership` from `inflation/cost to discover it`. A bounded early signal must account for both expected reuse (before full inflation) and CPU/RSS/reader cost, and must compete with the existing opaque fallback on full output bytes. No safe cheap predictor has been demonstrated.
- **Immediate next cheap falsifier:** same 1 MiB mixed-entropy, three Deflate levels, exact ZIP/container semantics, but **distinct** expanded member payloads sharing local entropy statistics. Does the 34,779-B virtual byte win disappear without exact raw identity? Preregister separately as O71b; preserve this source/receipt unchanged.
- **Concurrency:** O63 #418 product owner, O68 #424 single-member cost owner, O70 #426 eight-member cohort owner; no implementation overlaps, no forced shared-state update, no policy self-modification earned.
