# J24C15 result — held-out irregular and mixed-codec installed Reader court

**2026-10-28 UTC; research evidence only; NOT a release/promotion decision.**

## Exact source and prospective contract

This result applies to the unchanged research/product code at **`5921179c21aafd3847c3c3cc5c687e1de82ae553`**, PR #669, on top of PR #665 (the protected fused Reader itself is byte-identical to PR #662 `a66fd593a83cc4c71556d3d86d835c51abd20a96`). Preregistered test and limits: `docs/v031-research/2026-10-28-j24c15-heldout-irregular-prereg.md` at commit `4631c3c182f08ffaafe302259fc97110c05807dd`. No product, reader, format, frozen thresholds, comparator or release code changed in this result dossier.

Each of **two independent GitHub Actions executions** built three separately installed wheels from exact historical commits and processed the same revision-24 signed fixture bytes through 144 processes / 288 measured sessions. The six Q6/Q64 cells transferred the prior Reader advantage; Q1 early remains a clear **relative** regression and one execution crossed the **absolute** preregistered threshold. Preserve both verdicts: the extra security/admission scan and the released Reader's weaker hostile-input semantics cannot be erased to report a universal performance win.

| Job/artefact (same measured HEAD) | Source-exact hosted scientific verdict | Raw JSON SHA-256 |
| --- | --- | --- |
| [PR run 40675424786](https://github.com/FCMO-AI/.CMPCT/actions/runs/40675424786), [artifact 12811356183](https://github.com/FCMO-AI/.CMPCT/actions/runs/40675424786/artifacts/12811356183) | `HELDOUT_RELEASED_FLOOR_DEBT_REQUIRES_REHABILITATION` | `07b256a3fcf68927257736731b52ad79e09e382a79fad0d78d5e1e22c9c33946` |
| [Push run 40675417832](https://github.com/FCMO-AI/.CMPCT/actions/runs/40675417832), [artifact 12811450975](https://github.com/FCMO-AI/.CMPCT/actions/runs/40675417832/artifacts/12811450975) | `HELDOUT_SIX_OF_SIX_TRANSFER_RESEARCH` | `e42a1ae74d9b2a52c927c74423de028bd61a821010a8379f675260b42f4807d6` |

Both hosted independent referees reported PASS and their verdict files SHA-256 are respectively `39c78a2a67cac59a99398e9a0c1c01af4d04e00dc6c93074aa1a453a8844ef10` and `8facd48b2eb0607774526eceb5ad2d702cef218d9fd6a6315441dac172939157`. A third, separate no-CMPCT-import local auditor reconstructed 144 worker identities, 288 session observations, source SHAs, answer digests, exact phase sums, thresholds and medians for **each** run. The third audit agrees with both hosted verdicts. It explicitly did not merge or reinterpret their observations as same-host repeated samples.

## All measured cells — complete session wall medians (milliseconds)

Every triplet is **released / fused / released ÷ fused**. Independent runs used the same three source commits and identical signed archive content; different runners show roughly 2x timing scale differences, so do not pool absolute timing without host attribution.

| Family / regime | PR run #40675424786 | Push run #40675417832 |
| --- | --- | --- |
| Irregular RAW 65,536, Q1 early | 1.005 / 2.385 / **0.42x** | 0.547 / 1.223 / **0.45x** |
| Irregular RAW 65,536, Q1 tail | 4.925 / 2.376 / **2.07x** | 2.676 / 1.272 / **2.10x** |
| Irregular RAW 65,536, Q6 mixed | 12.559 / 2.497 / **5.03x** | 6.561 / 1.290 / **5.08x** |
| Irregular RAW 65,536, Q64 mixed | 122.262 / 3.111 / **39.31x** | 65.688 / 1.708 / **38.45x** |
| Irregular RAW 262,144, Q1 early | 3.660 / 8.847 / **0.41x** | 1.676 / 4.456 / **0.38x** |
| Irregular RAW 262,144, Q1 tail | 18.003 / 8.897 / **2.02x** | 9.660 / 4.472 / **2.16x** |
| Irregular RAW 262,144, Q6 mixed | 48.973 / 8.983 / **5.45x** | 26.280 / 4.509 / **5.83x** |
| Irregular RAW 262,144, Q64 mixed | 451.024 / 9.430 / **47.83x** | 246.277 / 5.014 / **49.11x** |
| Mixed RAW/Zstd 65,536, Q1 early | 1.032 / 2.449 / **0.42x** | 0.592 / 1.259 / **0.47x** |
| Mixed RAW/Zstd 65,536, Q1 tail | 4.868 / 2.456 / **1.98x** | 2.557 / 1.277 / **2.00x** |
| Mixed RAW/Zstd 65,536, Q6 mixed | 12.291 / 2.490 / **4.94x** | 6.737 / 1.348 / **5.00x** |
| Mixed RAW/Zstd 65,536, Q64 mixed | 123.005 / 3.143 / **39.13x** | 68.711 / 1.707 / **40.24x** |

**Strongest negative / nonpromotion law:** At 262,144 references, Q1 early is 2.42–2.66x slower than the published Reader by relative time. The PR-run absolute difference is **+5.186 ms wall / +5.205 ms CPU**, triggering both locked **≥5% AND ≥3ms** gates. The push-run absolute difference is **+2.780 ms wall / +2.785 ms CPU**, so the gate does **not** trigger in that run, despite an even larger relative slowdown. This is a material *cross-run decision boundary instability*, not grounds to overwrite or average away the negative. Q1 early at 65,536 references is 2.1–2.4x slower relatively but <3ms absolute on both runs. The secured #641 Reader has nearly identical early opening cost to fused, localizing the Q1 negative to the inherited full-list admission work rather than to fused checkpoint search. No semantic parity exists versus the released Reader's weaker admission contract for malformed archives.

**Positive:** In all 6/6 Q6/Q64 cells on both runs, CPU and wall exceed the preregistered ≥1.20x released/fused requirement, with no observed >8MiB high-water RSS delta. The mixed RAW/Zstd small-owner family and irregular including zero-length owners transfer the selective-read headroom. Q1 tail is ~2x faster but does not erase the early-Q1 cost. Native-only #641 remains a meaningful *security-equivalent* control; its read-range behavior is not accelerated by the index.

## Artifact/source integrity

All **four physical fixture SHA-256 values independently predicted before hosted measurement** match both archived ZIPs byte-for-byte:

| Fixture | Bytes | SHA-256 |
| --- | ---: | --- |
| irregular RAW 65,536 | 1,525 | `07874e348de6c676a44a958f5a02d186d3c3e5ef509f8d75df5536ef0b64063d` |
| irregular RAW 262,144 | 1,811 | `2b08ee4bbab0e564ee1fc1f5a312b43c205dd475ed0b1997b3a4689a1341efcd` |
| RAW/Zstd 65,536 | 1,890 | `ee4797a470dab665caf8af5089481f2cca10f198fe7c3cd59f358555363af45a` |
| Three-member synthetic cap | 759 | `db3e82960caf43a55d9c148029430186ecb1c7e616ae854e105ff32243deff57` |

144/144 unique workers, 288/288 correct answer hashes, 2 exact source-identical original receipts, all per-sample session CPU/wall equal the sums of open/range/close components, no proof calls in released and exactly one native probe in each native/fused worker. The synthetic reduced 4-mark budget admitted `alpha.bin` (4 marks) and correctly fell back for subsequent members; **not** evidence that natural 65,536-mark exhaustion has been benchmarked.

## Causal interpretation and decision

1. **Preserve the fused range-lookup mechanism as a promising seed**, with 6/6 Q6/Q64 held-out positives on each independently executed host and byte-exact signed files.
2. **Do not promote universal short-query performance.** Early Q1 is reproducibly worse by relative cost; one run materially violates the absolute released-floor gate and the two host executions disagree on that threshold while agreeing on the mechanism and direction.
3. **Keep released-vs-secured semantics separate.** Valid-input timing against a less guarded published Reader does not establish adversarial-security equivalence. Neither weaken validation nor relabel the absolute gate.
4. **Next cheapest decisive investigation:** isolate the inherited full-list admission cost vs checkpoint construction under Q1 from the actual installed Reader, include per-run host CPU signature/frequency/thermal context, and test whether a semantics-preserving architecture can amortize it without losing native admission. An option that only skips validation to win Q1 fails the security BONK. Then run a material 128KiB–2MiB owner/CDC+sparse/full decode-unit perturbation, and eventually the frozen product gate. No nearby stride tuning warranted until that fork changes.
5. **Process lesson:** the earlier J24C14 homogeneous Q6 win predicted Q6, but not Q1. Prospective Q1 regimes added here found an intrinsic admission-vs-lookup tradeoff; include one short/early query in future *released-floor* courts before generality claims. This local lesson is supported by two source-exact runs, but is **not** authority to rewrite Discovery policy. `docs/discovery/STATE.json` remains untouched under #574.

## Scope, losses and outstanding CI

Result-bearing J24C15 jobs **SUCCESS** for both exact measured-head runs; independent referees PASS, negative results retained. On the original research HEAD `5921179c`, Engineering Evidence, Version Discipline and CI Topology report SUCCESS. Generic CMPCT tests report **858 passed / 10 failed / 20 subtests** on inherited issues: missing ABI3 extension in generic test env, historical release fingerprint coverage and outdated surface-attribution assertions. The narrow research result is **not** a fully green product build, and the generic test run is not a reason to change historic expectations in this science PR.

**Not measured:** true realistic large compressed owners, CDC/sparse semantics, hostile signed-but-malformed repair, mutable in-memory metadata after open, default global-budget saturation, macOS/Windows, actual complete release product parity, process-start-inclusive speedup, compression quality and creation/recovery throughput. No core release, format change, merge, site claim or benchmark promotion.

**Handoff:** preserve original raw artifacts; coordinate with #662/#641 owners before modifying Reader code; next run may evaluate the admission-cost owner and a bounded semantically equivalent alternative. Do not repeat J24C15 exact held-out court merely to push the absolute threshold under 3ms.
