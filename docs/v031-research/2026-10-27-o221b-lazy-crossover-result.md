# O221b — Lazy short-session crossover: preregistered threshold NOT MET

Date: 2026-10-27 UTC. **Separate science rung; no product or release credit.** This is a new follow-up to the completed O221 [result](2026-10-27-o221-chunk-range-stride-result.md), not a change to its success criterion.

## Frozen provenance and exact-run truth

- O221b prospective preregistration commit `748d0dc9ad36c3dad791a1f1fed5084904aad897` precedes implementation `4be81555088e255b20f276464af17014c7150c57`.
- Exact hosted code HEAD: `283cc1f0f3c0fbf7fc5c4a1aad421dbd3de959b5`, unchanged Reader parent `c5e13bb3fbb4cdade8b64246658ce7c7818de41f` / blob `dbd4ac576a05a47eae97e1e40de89cf1de440516`. Original O221 adapter unchanged, blob `d5b97d8a75707243e49d79c4561ad9e40072939d`.
- [Hosted genuine-reader trial #40476030566](https://github.com/FCMO-AI/.CMPCT/actions/runs/40476030566): **SUCCESS**; [original artifact #12721121437](https://github.com/FCMO-AI/.CMPCT/actions/runs/40476030566/artifacts/12721121437), ZIP SHA-256 `a5758a89b85e7695f469cccfe3e40eb5a77141fce686a6a9c9f3317a796cc7fd`.
- Hosted independent receipt auditor **PASS**. Separately authored third-root audit of the original raw ZIP also **PASS**: CRC, exact source blobs, prereg identity, 108 raw independent process observations / 36 aligned baseline/eager/lazy triplets, identical query positions and output digests, 12 independently recomputed median groups, complete reproduction of decision. The third-root audit verifies receipts, not a second source-installed product run.

## Real installed Reader open + query costs

Same authenticated revision-24 archives with 262,144 repeated physical one-byte RAW refs, independently installed Reader, three fresh trials per arm, both `S_CHUNKS` and `S_CDC`. All arms include genuine Reader constructor/admission; eager builds the index before Q1; lazy builds it **once** immediately before Q2 and never for Q1. Process startup is recorded but excluded from the separately measured Reader session; candidate build time **included**. All medians below are complete-session wall speedups relative to original Reader:

| Q | Fixed eager | Fixed lazy | CDC eager | CDC lazy |
|---:|---:|---:|---:|---:|
| 1 | **0.915x (loss)** | 1.003x | **0.950x (loss)** | 1.005x |
| 2 | 1.012x | **0.962x (loss)** | 1.003x | **0.982x (loss)** |
| 3 | 1.015x | **0.934x (loss)** | 1.031x | **0.986x (loss)** |
| 4 | 1.149x | **1.043x** | 1.098x | **1.068x** |
| 8 | 1.453x | **1.382x** | 1.213x | **1.191x** |
| 16 | 2.327x | **2.210x** | 1.467x | **1.408x** |

**Prospective O221b decision: `LAZY_SHORT_SESSION_NOT_PROVEN`.** Lazy matched one-query original Reader within the preregistered 5% bound, but its Q=4 wall gain was only **4.30% fixed** and **6.82% CDC**, short of the required **>=10% gain in both wall and CPU**. The result stays negative even though Q=8 and Q=16 earn meaningful scientific headroom. **No threshold or evaluator changed.**

## Causal interpretation / counterfactual

The eager checkpoint’s Q=1 construction debt is real, and lazy successfully avoids that debt for Q=1. But with Q=2/3, lazy pays both a first linear scan and index construction, so it often loses. For the tested workload, sustained repeated seeks can amortize this (Q>=8), but a general one-query vs repeated-query policy is not established. Interpolating a crossover from Q1 and Q64 was insufficient; directly testing Q2/3/4 produced decision-changing negative evidence earlier than an implementation attempt.

## Debt and next frontier

Scientific scope: one Ubuntu Python 3.12 host, one extremely compressible RAW byte repeated 262,144 times, fixed/CDC selection only. Archive stored bytes/correctness, matched range digests and coarse Linux high-water RSS were charged and observed; more representative heterogeneous 1–4KiB physical blobs, native vs Python, journal/source mutation, platform portability and full official performance parity remain **unmeasured**. No claim of general workload savings or improved released product.

**Recommendation:** do not prioritize a lazy on-second-query product policy yet. The previous Q=64 checkpoint option remains a high-upside research seed for repeated-seek workloads; first test physical decoder and archive-profile generality with a stronger simple control (original Reader or ordered cursor) and full absolute CPU/RSS. Coordinate any product integration with existing J24C02 Reader owner [#569](https://github.com/FCMO-AI/.CMPCT/pull/569); do not fork another Reader. The cold-open O(N) admission and sparse/physical publication safety owners remain independent higher-priority product debt. Discovery policy changes are not earned.

**No Reader source, formatter, ABI, version, release, frozen benchmark or comparator modifications. No merge.**
