# O8 result — fresh-interpreter Reader journal source-exact cold performance

**Date:** 2026-10-24 UTC. **Decision:** `LARGE_COLD_WIN_WITH_BOUNDED_MEASURED_RSS_DEBT; SMALL_CASE_NEAR_NEUTRAL`.
**Evidence source:** [hosted Actions run 40105733426](https://github.com/FCMO-AI/.CMPCT/actions/runs/40105733426), job 120906920830, exact measurement HEAD `71d79615f7472f19bc7f07b5ab628b1aa0189997`, [raw artifact 12564058258](https://github.com/FCMO-AI/.CMPCT/actions/runs/40105733426/artifacts/12564058258). Raw JSON SHA-256 **`ffab08c98e46102d6eb3ba6d2618ad64be01470b3fd5d76369c28b8b5b805143`**; independently retrieved the artifact, extracted `reader-cold-start-rss-o8.json`, recomputed its SHA, and inspected the stored observations. PR #362 owns **research/evidence only**; no product or official gate change.

## Exact sources, control and execution
- Historical Reader from source commit `5f6c1462e30686687ea13cc2507c9702f13df116`, Git blob `604f6a81bf03bd97a4defb4ad7a1393d01ed491f`.
- Candidate Reader unmodified O7 exact Git blob `6de2edcf5b804e224a1c651ca77361af5667dc2e` inherited from PR #358.
- Real CMPCT Builder produced revision-24 authenticated physical payloads. O0 `make_case` generated **one** journal and identical logical checkpoint per N; all preflight and Reader index/payload equality checks passed.
- Full stored archives: N=512 journal **2,739 B**, checkpoint **2,191 B**; N=4,096 journal **12,046 B**, checkpoint **4,601 B**. Bytes are *not equal between journal and checkpoint*; final logical index and payload are equal by construction and Reader verification.
- Ubuntu, CPython 3.11. **10 fresh independent interpreters per source/variant/count** (two observations per ABBA/BAAB round × five rounds); all raw wall, CPU, Linux VmHWM/VmRSS and parent subprocess timings preserved in the JSON.

## Median outcomes — actual cold-process product research, not release gate

| Input | Historical import+construct | O7 import+construct | Ratio | Historical full process | O7 full process | Ratio |
|---|---:|---:|---:|---:|---:|---:|
| 512 authenticated renames | 30.734 ms | 29.248 ms | **1.051×** | 81.941 ms | 80.382 ms | **1.019×** |
| 4,096 authenticated renames | 286.388 ms | 39.800 ms | **7.196×** | 343.044 ms | 94.447 ms | **3.632×** |

**Controls:** for the logically identical final checkpoint, N=512 historical/candidate import+construct **26.667 / 26.629 ms**, full subprocess **77.498 / 77.705 ms**; N=4096 **31.539 / 31.588 ms**, subprocess **85.541 / 85.497 ms**. No checkpoint slowdown clears the preregistered both-5%-and-3ms research threshold. The 512 journal result fails the prospective >=1.5x cold-win threshold: do **not** claim benefit for every workload.

## Causal decomposition

| 4,096 renames | Historical | Candidate |
|---|---:|---:|
| Module import median | 25.288 ms | 25.055 ms |
| Reader constructor median | 261.186 ms | 14.695 ms |
| Import + constructor | 286.388 ms | 39.800 ms |

The mechanism is in **journal replay**, not a favorable shift in module import. O7 prior *warm* 33.42x constructor ratio is not a cold-process speedup: startup/import consume real time. Fresh-process measured product benefit is bounded to **7.196x** in-process import+construct and **3.632x** inclusive subprocess wall at N=4096. These numbers do not need cross-runner comparison.

## Measured resident memory and negative evidence

| N=4,096 journal | Historical | Candidate |
|---|---:|---:|
| Linux VmHWM median before constructor | 23,362 KiB | 23,400 KiB |
| Linux VmHWM median after constructor | **26,648 KiB** | **27,738 KiB** |
| Linux VmRSS median before constructor | 23,360 KiB | 23,396 KiB |
| Linux VmRSS median after constructor | 26,646 KiB | 27,666 KiB |

Measured **candidate HWM +1,090 KiB / +4.09%** versus historical; measured resident memory is **not free**. Both versions' post-constructor HWM exceed their respective pre-constructor HWM, so the primary O4/O5 saturation issue does **not** apply at this O8 scope. The preregistered **>10 MiB AND >10%** material-debt condition did not fire. This is still *not* a proof of maximum transient allocations beyond Linux kernel sampling or of behavior at sizes above 4,096.

At N=512 journal HWM was **24,306 KiB** historical versus **24,546 KiB** candidate. Windows/macOS memory, unusual generated histories, full package-install startup, process-native packaging and release parity were not measured.

## Hostile review and decision
- The historical source was dynamically imported under a private qualified module name while candidate used normal module import. This potentially biases import-only overhead. Observed 4,096 import medians differ by merely **0.233 ms**, while constructor difference is **246.491 ms**, strongly limiting that explanation for the large-case result; tiny differences remain ambiguous.
- The journal contains extra authenticated index bytes vs checkpoint. The comparison is **same actual journal file between Reader versions**, not a false same-bytes assertion between journal/checkpoint; checkpoint isolates final-state overhead.
- Comparison uses one GitHub runner and repeated medians, not an official cross-platform performance guarantee or frozen candidate/base release corpus.
- Predicted large-case cold win **survived**; small-case win **did not**; resident cost **exists** but remains below prospective materiality. No product optimization should be launched solely to shave ~1 MiB on this bounded case.

## Counterfactual and next executable action
The cheapest transferable prospective discriminator was to include **fresh-interpreter plus gross subprocess wall** and **kernel RSS before/after constructor** alongside warm ABBA from the first Reader replay result. This would have immediately exposed startup dilution and bounded residency without a third replay-index implementation. It is a *measurement lesson*, not grounds to mutate Discovery Engine policy from one episode.

**Stop local replay threshold gardening.** Next valuable task is composing the already validated O7 shared replay with the independently owned Reader signed-symlink prewrite guard and installed-wheel hostile tests, preserving their exact source identities and the full official release-parity gate. PRs #356/#361 own those protection/publishing surfaces; coordinate before implementation. Do **not** merge/release this science-only PR as though it were a product change.

## Exact-head statement
All measured claims above belong to source/code HEAD `71d79615f7472f19bc7f07b5ab628b1aa0189997`. Subsequent result documentation, if committed, changes Git HEAD but does not retroactively produce new exact-head hosted measurements. Neither source Reader/validator nor the O8 script changed after this measured source.
