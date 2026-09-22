# v0.30 promoted-product runtime authority — fcb05 result

Status: **ACCEPTED EXACT-HEAD PRODUCT AUTHORITY / RELEASE RED / NO RELEASE CREDIT**

This record preserves the fresh-process promoted-product runtime/RSS authority completed on the exact source fingerprint below. It supersedes older product-runtime numbers for current Forge gap accounting, but it does **not** supersede any frozen threshold, corpus, competitor, locality, recovery, integrity, native/platform, or release requirement.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`
- exact source: `fcb05acfa7cf9d18ef02336c6056fc244e985071`
- workflow: `CMPCT v0.30 authoritative v2`
- workflow run: `33699066911`
- substantive runtime job: `100474225800` (`authority-runtime`)
- runtime artifact id: `9872999103`
- runtime artifact digest: `sha256:08d10e4e6c472e52224fb6247bfd3231d1e0e20d2c678936ca6f001963242953`
- candidate fingerprint: `82bd9009cb4c4fc344169ee04d7e4df3d311af7ecc1f5e9a6ec057321769f574`
- exact three-target contract: pass
- no size regressions: pass
- release credit: **false**

The sibling 15-workload authority-generalization job on the same source completed successfully. The runtime job failed exactly because the frozen runtime/RSS gates remained red; the failure is therefore substantive product evidence, not an infrastructure or classifier-only failure.

## Frozen runtime gates

The unchanged product limits are:

- median create ratio `<= 1.10x` genuine r24;
- every workload create ratio `<= 1.25x`;
- median extract ratio `<= 1.10x`;
- every workload extract ratio `<= 1.25x`;
- maximum peak-RSS ratio `<= 1.25x`.

No threshold is changed or reinterpreted by this result.

## Exact target rows

| target | r24 bytes | promoted r25 bytes | byte saving | create ratio | verify ratio | extract ratio | peak RSS ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| `resemblance_hostile_v1 / 01_shifted_versions` | 30,146,189 | **29,973,276** | **172,913 B** | **1.406733078x** | 0.713295374x | 0.923276886x | **2.089966178x** |
| `resemblance_hostile_v1 / 05_logs_and_telemetry` | 207,745 | **206,017** | **1,728 B** | 0.033049284x | 1.080979363x | **1.374227492x** | 1.006276432x |
| `neutral_hostile_v1 / 09_ml_artifacts` | 12,692,256 | **12,624,320** | **67,936 B** | **1.352523310x** | **1.743058850x** | **2.448729934x** | **1.607660873x** |

Aggregate saving across these frozen runtime targets is **242,577 B**. Aggregate saving does not hide any required losing runtime row.

Shifted repetition detail:

| repetition | create | verify | extract | peak RSS |
|---|---:|---:|---:|---:|
| 0 | 1.404183489x | 0.719700759x | 0.953954991x | 2.084059701x |
| 1 | 1.409282667x | 0.706889990x | 0.892598781x | 2.089966178x |

Logs repetition detail:

| repetition | create | verify | extract | peak RSS |
|---|---:|---:|---:|---:|
| 0 | 0.033640641x | 1.063190x | 1.361599x | 1.006276x |
| 1 | 0.032457927x | 1.098767x | 1.386856x | 1.001061x |

## Exact aggregate runtime result

- median create ratio: **1.352523310x** -> red;
- maximum workload create ratio: **1.406733078x** -> red;
- median extract ratio: **1.374227492x** -> red;
- maximum workload extract ratio: **2.448729934x** -> red;
- maximum peak-RSS ratio: **2.089966178x** -> red;
- runtime gate: **fail**.

Starting from this exact measured product state, the minimum ratio reductions required merely to reach the frozen ceilings are approximately:

- median create: **18.6705%**;
- maximum workload create: **11.1402%**;
- median extract: **19.9549%**;
- maximum workload extract: **48.9531%**;
- maximum peak RSS: **40.1904%**.

These are gap-accounting figures, not permission to weaken a workload, omit a row, or trade correctness for performance.

## Cross-fingerprint progress versus the previous product authority

The prior Shifted RSS gap ledger was anchored to source `292b64664b38ee79cba75968a86a2386a7b28544`, where the substantive promoted-product maximum peak-RSS ratio was **2.960331653x**. The present exact product authority measures **2.089966178x**.

That is an absolute ratio reduction of **0.870365475x**, or about **29.4009% lower** than the earlier product ratio. Correspondingly, the same-semantics reduction still needed to reach `1.25x` falls from about **57.7750%** on the old receipt to about **40.1904%** on this receipt.

This comparison is deliberately **not** causal attribution. The receipts are on different exact source fingerprints and may include multiple repository changes. In particular, the current-head `CMPCT v0.30 PrefixGraph isolation Builder hostile review` was classifier-only on `fcb05...`; its substantive Hostile Reviewer job was skipped. Therefore this result does **not** prove that the integrated PrefixGraph process isolation alone caused the 29.4009% cross-fingerprint improvement. The frozen S6 A/B remains the authority for that causal transfer question.

## Forge diagnosis and terminal allocation

### Shifted

Shifted remains the strict memory owner and also owns the worst create ratio. The new product receipt materially narrows the scale of the RSS problem but does not close it: **2.089966178x -> 1.25x** still requires about **40.19%** reduction from this exact state.

The next decisive causal authority remains the frozen canonical-Builder PrefixGraph isolation Hostile Reviewer in `R25_PREFIXGRAPH_ISOLATION_PRODUCTIZATION_PREREG.md`. Do not infer S6 support from this cross-fingerprint product improvement. If S6 passes, preserve the process-isolation mechanism and evaluate whether the separately evidenced r24 streaming-finalize mechanism compounds at the promoted-product boundary strongly enough to attack the remaining release-scale gap.

### ML artifacts

ML is now the dominant decode-side product red: **1.7431x verify** and **2.4487x extract**, with **1.6077x RSS**. The frozen G0-G4 operation-record-cache experiment remains the relevant low-radicality lane. Partial/interrupted receipts receive no win or loss credit; do not retune its grammar or thresholds after observing checkpoints.

### Logs

Logs create/RSS are comfortably below the frozen ceilings, while extraction remains **1.3742x**. The active full-pack member identity-proof-reuse experiment may remove only redundant logical SHA work when the logical member is exactly the already-authenticated complete pack. Pack CRC32/SHA-256, derived/partial-member SHA, cold selective reads and hostile mismatch rejection remain mandatory. If that mechanism loses, preserve the negative and move to another authenticated traversal/decompression implementation rather than weakening identity checks.

## Strongest surviving critique

The current product is measurably closer to the RSS gate than the previous authoritative product, but release convergence is still not near enough to justify saturation theater. Shifted still requires a large second-order memory win, while ML extraction needs nearly half of its current ratio removed to reach the hard per-workload ceiling. A few-percent optimization in the wrong lane cannot unlock v0.30.

The repository should therefore continue allocating Forge effort by exact product gap scale: causal-transfer proof and compounding RSS mechanisms for Shifted; reconstruction/decode ownership for ML; bounded authenticated proof reuse or traversal improvements for Logs.

## Release state

This exact product authority is **red**. It does not authorize merge, tag, numeric version bump or publication.

**v0.30 remains MERGE / TAG / VERSION / PUBLISH LOCKED.**
