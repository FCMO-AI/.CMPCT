# O71b — entropy-matched independent-content falsifier: original causal story insufficient

Date: 2026-10-25 UTC. **Research evidence only — O71b prospective prediction falsified.** Original O71 record and its raw artifact remain frozen/unaltered.

## Prospective source and evidence custody

- O71 baseline prereg `98c32b5e955a57f4143a886cdf4e8f1be134b059`, O71b prospective extension prereg **`83fc27518f45663c399d1f16809b9601880a9fec` before code edits**.
- Actual O71b result-bearing product+instrument HEAD **`f69bde769c58dc30ab9b9f60787d662db1098fec`**. Product unchanged from O63 `18e32cae012f5dca9fc47f10d194f8b81005c85c`, Builder blob `382e60983bf1e8e7595ea7112f3a5553dc33dcc0`, codec blob `dc3446b0eed82edfba9380e3885a20aa45577899`.
- Hosted [source-exact O71b run #40179991667](https://github.com/FCMO-AI/.CMPCT/actions/runs/40179991667) SUCCESS; exact-head additional run #40179993606 also SUCCESS. [Raw artifact #12594216707](https://github.com/FCMO-AI/.CMPCT/actions/runs/40179991667/artifacts/12594216707); archive SHA-256 `682d10dbf1e1fe7de398fcfcf2fde2422a481184dfcefdd658c388ababd39156`, `o71-raw.json` SHA-256 **`453e3d9232ba5afab6092250f1dfaf84ec76b3b85e72511870753739e59882c0`**.
- Independent ZIP extraction/parser validated **48/48 original individual records**, eight cohorts, three actual separate-process observations per arm, all matched within-arm physical ZIP source hashes, original/opaque archive SHA determinism, complete archive-byte arithmetic and original source SHA. Includes 42 O71 replication measurements and **six new O71b observations**. The original O71 source/receipt (42 observations, artifact #12593755705, SHA `24ba7b6019cbf7968ec94269ca6347e1362181b39f51e3348ce39c93e5601c8f`) remains independently available.

## Controlled prospective comparison (complete genuine r24 archive bytes)

| Cohort | Same expanded raw SHA among all three? | Least source inflation ratio | VZIP archive bytes | Same-input opaque bytes | VZIP minus opaque | Median Builder CPU VZIP / opaque |
|---|---|---:|---:|---:|---:|---:|
| O71 shared mixed, Deflate levels 1/6/9 | **Yes (1 SHA)** | 44.96× | **18,334** | 53,113 | **−34,779 B** | 32.039 / 2.023 ms |
| **O71b independent mixed**, same Deflate levels 1/6/9, changed 1-MiB raw identities | **No (3 different SHAs)** | **46.98×** | **51,579** | 53,119 | **−1,540 B** | 32.840 / 2.341 ms |

Both use same original O63 Builder and codec, same type/count of ZIP files, same timestamps/Deflate levels and same within-family physical source tree for VZIP and opaque. Both produce S_VZIP for **3/3** real members and pass original ZIP authenticity, Reader read/verify/extract.

**Prospective O71b hypothesis falsified.** Despite eliminating whole-raw exact SHA identity, VZIP still saves **1,540 B complete (2.90% against opaque)** in the independent-content matched-entropy cohort. O71b exact classification is `INDEPENDENT_MIXED_STILL_WINS_CAUSAL_STORY_INSUFFICIENT`. Thus **exact whole-content identity was NOT necessary for any complete byte gain in this mixed-entropy structure**. The associated gain in the shared case is much larger: 34,779 B vs 1,540 B, a 33,239-B difference between independently paired cohorts. This contrast is *consistent* with additional reuse benefits from exact identity, but cross-input differences in physical ZIP contents and transform overhead mean it is **not** an isolated same-input causal delta, nor a proof of full-byte ownership attribution.

The prospective primary O71 counterexample to an inflation-only admission cutoff survives: each source ZIP above 44× inflation can be a genuine VZIP bytes winner, even with enormous creation CPU debt. The new independent-content winner further **strengthens** the rejection of expansion-ratio-only rules as general admission. In contrast, repeated/text/high-inflation cases in both O71 runs are genuine VZIP bytes **losers**, making unconditional VZIP equally unjustified.

## CPU / memory / read debt and key negative

New O71b independent-mixed median Builder CPU **32.840 ms** vs opaque **2.341 ms** (14.03× worse) for only **1,540 B** complete byte gain. Median verify/read/extract wall **14.405 ms** vs opaque **0.999 ms** (14.41× worse). Peak process RSS median **33,672 KiB** VZIP vs **29,340 KiB** opaque (+4,332 KiB), but process-wide peak RSS is not a fine-grained memory allocator profile. This is a **productically dominated or tradeoff-heavy** scenario for ordinary latency-sensitive use, not an engineering win to promote.

O71 first real result had lower absolute CPU due to hosted runner noise; the unchanged seven families' **archive bytes and classification replicated exactly** in O71b's second run, while CPU/wall shifted. Therefore emphasize within-run matched comparisons and source-exact complete bytes rather than portability claims for absolute timings. The 42+48 observations are not 90 wholly independent scenario families: second run repeats first cases.

## Scientific consequence / next decision

Reject as false the overly narrow mechanism claim that cross-object raw SHA equality is **required** for a high-inflation VZIP archive-byte win. Instead a **two-part model** survives:
1. Information yield of decomposing compressed representation versus directly compressing physical ZIP bytes can produce material wins even with independent raw payload identities in this mixed-entropy family;
2. exact whole-content reuse can amplify that benefit greatly, but is neither necessary nor sufficient (shared repetition loses complete bytes).

A cheap pre-admission signal must estimate **structural compression headroom**, not just raw identity or physical inflation ratio. The marginal decision-relevant next cheap probe is a fully charged *raw Deflate work versus opaque envelope* using ZIP central-directory sizes and a fixed bounded sample, keeping fallback-safe, with enough negative counterexamples to prevent over-admission. No predictor has been earned, no revision-24 product implementation or decoder change authorized. Full true process-start/RSS/sparse/platform economics, arbitrary real files, release ABBA and external comparators remain unmeasured.

**Counterfactual discriminator:** the preregistered independently mixed source was the cheapest stronger causal control to falsify the original narrative; it did so, yielding a legitimately transferable lesson about overattributing VZIP byte gains to whole-content SHA reuse. Single scientific episode is **not sufficient** for discovery-policy edits; leave `docs/discovery/STATE.json` unchanged. O63 #418, O68 #424, O70 #426 continue as independent owners. No merge/release.
