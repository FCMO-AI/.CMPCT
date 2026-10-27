# O229 — bounded prefix-only CDC admission: hosted falsification

**Date:** 2026-10-27 UTC. **Status:** scientific negative, not product evidence. **Decision:** `PREFIX_PREDICTOR_FALSIFIED`. Released `main@80c358f8824ec1b20d349c92ed94c898090969b0` remains v0.30.0/r24; no Builder, Reader, encoder policy, format or gate changes.

## Source, preregistration and evidence custody

[O229 preregistration](2026-10-27-o229-prefix-chunker-admission-prereg.md) was committed **first** at `752ddc4d421a9248163173c3a5457c5446d04e05`, before the instrument, audit, CI and output. Criteria were frozen: sample first 4 MiB with genuine native/fixed Builder, choose native for full 16-MiB source only when complete native-prefix archive ≤80% of complete fixed-prefix archive; count both sample encodes and one selected full encode, preserve SHA/verify/read/range, compare against strong full fixed, full native and gifted after-the-fact smaller full archive.

A complete original hosted [O229 court run #40540215769](https://github.com/FCMO-AI/.CMPCT/actions/runs/40540215769) **SUCCESS** on branch source `6e403acc4cbb33f1eaab526845b900be2d4eb418`, PR merge checkout artifact ref `2ea8fd7ed16e2207607c1246fd3955215ebcf24b`, Ubuntu 24.04 / Python 3.12. Its independent referee **PASS**: 13 profiles × 3 strategies × 3 separate child processes = **117** observations, deterministic archive SHA identity within each strategy, exact logical reconstruction and selective range checks. Hosted raw artifact [#12750926204](https://github.com/FCMO-AI/.CMPCT/actions/runs/40540215769/artifacts/12750926204), ZIP digest reported by GitHub Actions **SHA-256 `90315b8af38761b3efdf77836751d3b3ece2b89851047a7e40e553b32d625a8e`**. This digest is a GitHub Actions upload receipt; not an independent container download/ZIP verification. The original work produced a correct raw negative on an earlier run but its initial referee incorrectly expected nonexistent `input_bytes` fields. The referee was corrected to audit actual raw fields, with no change to the frozen selector, main instrument or outcome. A later reviewer enhancement additionally checks cross-strategy identical input SHA and native C-source digest.

**Exact-head note:** the result-bearing run is on the cited earlier source branch head, not automatically equivalent to every later documentation/audit commit. Subsequent exact-head workflow must be read independently; do not relabel pending checks as passed.

## Held-out whole archive bytes (not projections)

Seven held-out sources were locked before output. The following are complete authentic revision-24 archive sizes in bytes; the `admitted` column is the prefix-only policy result. The gifted comparator can choose after observing both complete encodes, and is **not** a candidate deployment policy.

| Held-out source | Fixed full | Native full | Prefix-admitted full | Decision |
|---|---:|---:|---:|---|
| 768-KiB repeating high entropy | 787,592 | 3,409,240 | 787,592 | fixed, correct |
| Two alternating 768-KiB periods | 1,574,270 | 3,567,483 | 1,574,270 | fixed, correct |
| Seed-shifted repeating source | 16,782,978 | 1,809,336 | 1,809,336 | native, correct |
| Repeated source with inserted boundary bytes | 16,782,978 | 1,983,750 | 1,983,750 | native, correct |
| Mixed periodic/random/shifted | 9,440,846 | 7,589,202 | 9,440,846 | fixed, missed native |
| Independent random | 16,782,976 | 16,780,642 | 16,782,976 | fixed, negligible miss |
| **Late shift after 4-MiB random prefix** | **16,782,974** | **5,441,896** | **16,782,974** | **fixed, decisive miss** |

Held-out aggregate: always-fixed **78,934,614 B**, sampled policy **49,161,744 B**, gifted best of two genuine builds **35,966,688 B**. The gifted possible improvement against fixed is **42,967,926 B**; the prefix policy captures **69.290917%**, below the prospective **≥75%** threshold. The worst per-file relative regret is **208.403%** (late shift), above the **≤25%** veto. It is not enough to win on the two friendly shifted patterns.

Three-process median charged Builder totals in the successful hosted court gave CPU ratio **1.237539x**, wall ratio **1.237512x** compared with single full fixed Builder, and maximum extra own-process Linux VmHWM **7,692 KiB**. Those stay below the prospective 1.50x time/CPU and 10-MiB memory vetoes. **The byte predictor, not the measured execution ceiling, fails this experiment.** These costs cover Builder creation; they do not establish a deployed streaming selector, extractor throughput, cross-platform size/performance or a release-ready format.

## Causal explanation, negatives and counterfactual

A finite prefix is blind to potentially decisive later physical ownership. The late-shift hostile presents independent random data in the first 4 MiB, causing conservative fixed selection while the remaining repeated/shifted region strongly favors native CDC. This is a structural information limitation: two sources with identical first 4 MiB must receive the same decision from any deterministic prefix-only rule even if their later optimal physical partitions differ. No amount of threshold gardening at 0.80 can make **prefix-only** admission universally aware of unseen suffix structure. The experiment does not prove that native CDC is universally superior, nor that a different full-stream bounded predictor is impossible.

**Scientific disposition:** retire this *specific bounded prefix-only policy* without promotion. Preserve O228c's native/fallback physical-ownership crossover and O228/O228b/O228c's virtual-run-index negatives separately. Future continuation, if justified against higher-priority product debt, should change the information boundary: e.g. stream-aware ownership evidence with explicitly charged scan/hash/compression work and adversarial phase changes, not another adjacent prefix fraction or threshold. Otherwise prioritize strict Reader admission/open-time regression [PR #569](https://github.com/FCMO-AI/.CMPCT/pull/569), extraction recovery integrity and native CDC extreme bounds [issue #606](https://github.com/FCMO-AI/.CMPCT/issues/606).

## Truth boundaries and coordination

No new storage tags, Builder/Reader mutations, decoder compatibility claims, format revision, benchmark manipulation, version, merge or release. The original O228 line stays owned by [PR #600](https://github.com/FCMO-AI/.CMPCT/pull/600); O229 stays isolated in [PR #607](https://github.com/FCMO-AI/.CMPCT/pull/607). Discovery `STATE.json` remains unmodified because [PR #574](https://github.com/FCMO-AI/.CMPCT/pull/574) owns current reconciliation. No general Discovery Engine policy change is earned from a single isolated negative.
