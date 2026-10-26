# O188 — deterministic scan-admission oracle: scoped positive, non-dominant

Date: 2026-10-26 UTC. **O0/O1 offline research evidence only. NOT Reader-product, CPU, RSS or release credit.**

## Identity / prospective boundary
Preregistration: `docs/v031-research/2026-10-26-o188-scan-admission-prereg.md` committed on branch at `dbdc627b42267f42ae9e564dae564f5853588103`, before research instrument `research/o188_cache_admission_oracle.py` was committed as `b07eea21e9fdf76ceee58c80bbc8388fff54bfca`. Original research owner #510 O175 and cache product owner #506 are not changed. Published CMPCT v0.30.0/r24 remains unchanged.

Local deterministic execution of the research instrument on 2026-10-26: `python3 research/o188_cache_admission_oracle.py` emitted all seven trace families, passed bounded-byte/count invariants and the frozen scan/warm control assertions. Raw local script SHA-256 `01c97b1e083e257f8d98bb1c0cce7c6e275c82223788303de3e4f237dad5e85b` applies to a locally equivalent script with longer introductory comment; **do not identify that checksum as the committed Git blob**. Local full JSON SHA-256 `668e310035cd30c7f8db6b91e8f79a0ed3a0b69a17f4e7842a557e10ddfdddd4` likewise is not a hosted exact-head artifact. A source-authenticated hosted workflow is declared separately; **treat hosted execution as pending until the job and raw artifact are inspected.**

## Outcomes — all counts are simulated requests, not physical Reader timings

| Frozen trace | O169 LRU hits | Simple fixed-pin hits | Exploratory guarded 48/16 hits | Strong negative / interpretation |
|---|---:|---:|---:|---|
| 96 × 1MiB, 3 forward passes (288 reads) | **0** | **128** | **96** | second pass 0 vs 64 vs 48 hits; offline maximum second-pass hits is 64 |
| 48 × 1MiB, 3 passes (144 reads) | **96** | **96** | **96** | no warm-fit regression in this exact synthetic control |
| 16 hot + repeated one-pass 96-cold scans (352 reads) | **16** | **48** | **48** | both simple/guard outperform LRU on this access order |
| A 96 × 2 then disjoint B 96 × 4 (576 reads) | **0** | **64** | **161** | fixed-pin never adapts: 0 B4 hits; guard B2=17, B3=48, B4=48, one reset |
| Streaming 512 unique 1MiB (512 reads) | **0** | **0** | **0** | no reuse: guard performed 4 resets with no benefit |
| Repeated 8 hot 4MiB synthetic VZIP + fresh 96 RAW 1MiB (416 reads) | **0** | **24** | **24** | synthetic refetch-work units: LRU 1408 vs both alternatives 640, NOT measured time |
| 40,000 distinct zero-byte keys (40000 reads) | **0** | **0** | **0** | all kept <=32,768 keys; guard incurred 312 resets without any reuse |

All strategies respected <=64 MiB retained bytes and <=32,768 entries in the local execution, with periodic full-accounting checks. These are model invariants, not verified physical process limits. No algorithm was allowed to look at future accesses or phase labels; the output categories are for the auditor only.

## Scientific disposition

**Primary hypothesis NARROWLY ADVANCED:** The pathological 0-hit repeated-scan behavior of bounded O169 LRU is not an inevitability of a 64MiB residency cap. Even a simple online admission rule can retain reusable decoded objects and stay inside the same budget. A guarded choice can recover after a phase shift while a permanently pinned cache cannot.

**Novel policy NOT PRODUCT-READY:** The stronger simpler fixed-pin control outperforms guard on unchanged repeated scans (64 vs 48 hits per postwarm pass) and ties it on the tested hot/VZIP-proxy traces. Guard's claimed advantage arises only after a temporal phase shift and costs reset logic, metadata churn and a completely unmeasured impact on real decode cycles, contention and process RSS. Ratio/reset constants 48/16/128 are exploratory frozen choices, not validated generic admissions. Synthetic VZIP work units are arbitrary weights and are not CMPCT VZIP reconstruction timings.

**Causal next discriminator:** Replay the same authentic O175 revision-24 physical archive, then an independent authenticated heterogeneous VZIP + RAW corpus, using exact product Reader implementations of **plain bounded LRU vs the strongest simple admission control** before constructing a complex adaptive guard. Measure repeated-read wall/CPU/RSS, retained bytes, complete exact SHA verification, concurrency and byte/entry accounting. Phase-shift traces must be predeclared and resistant to cache poisoning by stale first objects. If a simpler control matches or beats a guarded policy in real read economics, retire guard. If the absolute O175 ~37ms second-pass debt is small relative to implementation/metadata costs, leave LRU as product candidate.

## Counterfactual and process learning
A simple upper bound (64 second-pass hits at 64/96 capacity) and fixed-pin falsifier would have exposed *admission choice* as a possible cause of O175 scan-thrash before a product implementation. But fixed-pin's phase-shift failure was prospectively recognizable by its non-eviction semantics. This is one scoped useful discriminating recipe, **not repeated evidence justifying a normative discovery-policy change**. No change to `docs/discovery/STATE.json` or frozen benchmarks.

## Concurrency, safety and limits
No code under `src/`, `native/`, release gates or historical controls changed. #506 owns cache product, #509 source custody, #510 physical RSS evidence and #516 CDC×cache integration. This is independent lower-rung policy science with no claim of generic speedup, hardening, cross-platform behavior, acceptance or release. All original negatives survive.
