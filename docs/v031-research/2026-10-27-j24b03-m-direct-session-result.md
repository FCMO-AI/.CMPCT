# J24B03-M — full direct-owner Reader session: measured CPU/wall debt below preregistered absolute veto

**Date:** 2026-10-27 UTC. **Status:** hosted science/result only, not product or release permission.

## Authority and prospective protocol
[Original, preceding J24B03-M preregistration](2026-10-27-j24b03-m-direct-session-prereg.md) commit `2462534c2c4e18d3a9b86dcd80ad4111da1430aa` precedes instrument, independent referee, and result. No evaluator, threshold, input workload or comparator was changed after observation.

- Source-exact hosted [GitHub Actions run #40582356902](https://github.com/FCMO-AI/.CMPCT/actions/runs/40582356902), **SUCCESS**, source checkout `acf7f10de21ae1c4e1afa594adc26f5257f4b418`, Ubuntu 24.04 / CPython 3.11.
- Original [artifact #12770117656](https://github.com/FCMO-AI/.CMPCT/actions/runs/40582356902/artifacts/12770117656), upload ZIP SHA-256 **`9f003ea396ccab1ff5ec910a3b8e081ac3bdf9ac2178d69c6b694e83e9de86c5`**. Raw results, 36 fresh worker-process rows, exact archive-input SHA identities and independent referee JSON are in this artifact; not copied into Markdown.
- Historical reader: frozen `main@80c358f8824ec1b20d349c92ed94c898090969b0`. Candidate: J24B03 #609 Reader blob `33deb74e196f7e40aa8351b6ec426a24255d5eec`, validator blob `74a907253c8e9719ec972aa7a8d7bae9d7a27124`. Both true package-native-installed sources. Runner checks live paths, source SHA-256 and the identical binary archive for each arm.
- Three legitimate revision-24 archive images, N=1 / 4,096 / 65,536 distinct logical S_BLOB files referencing one exact 128-byte physical RAW block. Full duplicated authenticated index and physical frame charged. Three ABBA rounds per N with order released/candidate/candidate/released, 36 separate processes, process startup excluded; per-arm open, selective read, close, full session, separate strict preflight, CPU, wall and own `/proc/self/status VmHWM` observed. Exact content/selective checks and worker checksums pass.

## Largest profile: original measured medians (N=65,536)

| Metric | Released v0.30.0 | Guarded J24B03 | Candidate/base | Delta |
|---|---:|---:|---:|---:|
| Cold open wall | 100.831 ms | 103.375 ms | 1.0252× | +2.544 ms |
| 65,536 selective range reads wall | 80.488 ms | 100.070 ms | **1.2433×** | **+19.582 ms** |
| Complete open→read→close wall | 181.106 ms | 203.815 ms | **1.1254×** | **+22.709 ms** |
| Complete session CPU | 181.093 ms | 203.791 ms | **1.1253×** | **+22.698 ms** |
| Strict preflight wall | 225.868 ms | 227.896 ms | 1.0090× | +2.028 ms |
| Process VmHWM after session | 50,288 KiB | 50,266 KiB | 0.9996× | −22 KiB |

These are 6 worker medians per arm, **not** official product release timings. Other N=1 and N=4096 raw observations are preserved in the artifact and independently checked, rather than replaced with inferred numbers.

## Result and strongest negative

**Recorded decision: `NO_PREREGISTERED_MACRO_DEBT_SIGNAL`; independent stdlib referee `PASS`, 36/36 processes, **3/3 forged receipts rejected**.** The preregistered full-session wall AND CPU relative veto (>=1.10×) actually fires on the 65,536 profile, **but the corresponding >=25 ms absolute additions do not** (+22.709ms wall / +22.698ms CPU); no >=8MiB session VmHWM condition fires. The strict preflight clause does not fire. This is near the absolute boundary and not evidence of parity.

**Scientific interpretation:** the safety check is economically visible at high cardinality: 65,536 tiny direct range reads cost +24.33% and add 19.58 ms; complete session +12.54% / +22.71 ms. The immutable earlier tiny-call J24B03-P measured +135.467ns (+37.94%) per RAW call. Those observations are directionally consistent. Unlike the previously falsified J24B03-H prediction, the current macro conclusion was not retroactively adjusted. Neither instrument proves full reconstruction, arbitrary data, other codecs, hostile destination, cross-host timing parity or no cumulative cost at larger scale.

## PARETOBONK / counterfactual and next decision

The cheapest transferable discriminator was a single high-cardinality full-session A/B on a legitimate authenticated deduplicated archive. It exposed a nontrivial whole-session penalty that a 128-byte microbenchmark could not quantify. No policy-level discovery change is earned by one observation; `docs/discovery/STATE.json` remains untouched under #574 owner.

**Next:** do **not** remove direct size/BHDR guards or relax tests. Supply source-exact measurements to #569's Reader owner and integrate only after conflict-reconciled full Reader geometry + recovery/performance acceptance. #569's independently measured 27–28× chunk cold-open debt remains a separate hard blocker. Hardlink alias length #615, forward hardlink publication #618/#619, mutable mmap data and transactional extraction remain separate. J24B03-H's historical falsified test stays red and preserved as scientific evidence. No merge, no release, no format change.
