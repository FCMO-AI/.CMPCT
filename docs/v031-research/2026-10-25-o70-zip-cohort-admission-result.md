# O70 — Source-exact eight-ZIP admission cost result (research, not release)

Date: 2026-10-25 UTC. Preregistered before execution: [O70 prereg](2026-10-25-o70-zip-cohort-admission-prereg.md), commit `76087081b84b07b50816a0da1b16d9976c213fa3`. Original product code unchanged.

## Exact science and direct measurements

Original v0.31 development Builder blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`, source at `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; O70 installed run [40178001005](https://github.com/FCMO-AI/.CMPCT/actions/runs/40178001005), evaluated instrument HEAD `b461b4852a30038de48b6bc5c19d02590043405d`, **SUCCESS (1/1 exact-source test)**. Direct raw artifact [12592398418](https://github.com/FCMO-AI/.CMPCT/actions/runs/40178001005/artifacts/12592398418), artifact ZIP SHA-256 `83786b0bfbed6b031c439cee82dbb1391941e0c661155e3c1f19c7147939c250`. Source full-text SHA-256 `875c24aea7fefdec19de9f10ccb2930e56fbd9633a09fbbdc64acea7592836e7`, one-expression counterfactual SHA-256 `fc5216c7285549c13cd7d2ceb8f74ca82fc067eaac9468c2be8ad740071bae82`.

Same deterministic **eight-file** physical ZIP source tree (six ~131,236 B and two ~1,153 B sources), unchanged filenames, timestamps, contents and original SHA hashes. ABBA four complete real archives, strong `CMPCT.verify`, per-member SHA, complete extraction identity, repeated source-policy deterministic archive bytes; ten fresh `CMPCT.read_range` observations per policy of 64 B from `m07.zip`.

| Metric | Current whole-cohort S_PACK | One-condition no-cohort oracle | Scope |
|---|---:|---:|---|
| Complete CMPCT archive bytes | **790,524** | 792,646 | Noncohort costs **+2,122 B (+0.268%)** |
| Complete create median wall | **12.323 ms** | 46.213 ms | Oracle costs **+33.890 ms (~3.75x)** |
| 64-B selected cold-Reader read wall median | 355.184 µs | **38.306 µs** | Oracle **~9.27x faster** observed |
| Selected-read physically decoded blob work | **687.911x oracle** | reference 1x | Real `_blob` invocations, not disk I/O |
| Exact reconstruction / integrity | PASS | PASS | All eight archive members |

Both controls used the same product and format; only the creator's eight-member packing policy differed in an in-memory, non-shippable Python module. A selection over a **tiny selected member** exported an entire multi-member group to the read path. **Prediction >20x decoded-work difference survived**, but the pure no-cohort oracle paid materially more create CPU/wall. This is a tradeoff, not Pareto domination.

## Strongest negative / adverse interpretation

The apparent locality gain is not free: +0.268% complete stored bytes and ~3.75x complete creation time on this one synthetic regime. The experiment did **not** measure full extraction throughput, real physical disk bytes, portability, memory peak, random selection distributions, or held-out corpora; fresh Reader objects do not guarantee cold OS page-cache. Therefore no global creator policy or v0.31 release change is earned. A blanket 'disable eight ZIP packing' is **not supported** by the measured evidence.

## Infrastructure evidence and original failed run

First hosted O70 run [40177901567](https://github.com/FCMO-AI/.CMPCT/actions/runs/40177901567) FAIL before science because the dynamically compiled `@dataclass` used postponed annotation lookup but had no `sys.modules` registration. Fixed only that isolated science-module registration at `b461b4852a30038de48b6bc5c19d02590043405d`; the input, source expression replacement, same-input oracle, scientific acceptance, sample count and product SHA remained unchanged. Original setup negative is preserved, not relabeled as a CMPCT loss.

## Disposition and next discriminator

**ADVANCED/NARROWED SCIENCE:** Eight-member cohort admission has a measured creator-vs-selected-read conflict on an authenticated same-input tree. No product credit and no policy mutation.

The cheapest next *structurally different* discriminator is a **charged split-owner oracle**: retain a large-file shared S_PACK (and its create advantage) while giving small ZIPs independent, bounded owners; require real complete archive bytes, create CPU/wall, cold selected read, exact identity, and a held-out distribution. It is only an investigation hypothesis, not authorized product promotion. If a split owner cannot preserve the creator benefit, this family may be a Pareto tradeoff to document rather than productize.

**Counterfactual prospective lesson:** The code's `len(deferred)>=8` discontinuity and the complete cohort byte sum (~789,722 source B against a ~1,153 B selected member) would have revealed the likely selective-read *work* hazard before hosted CI. It could not predict full archive size or 3.75× creator cost, so the paired same-input complete-Builder oracle was decision-changing. The existing Discovery Engine policy does not require modification.

## Authority and release boundary

Research only. Released CMPCT v0.30.0/r24 unchanged. No product source, format, frozen evaluator, benchmark, comparator, threshold, CI safety check, discovery state, version, merge, or release was changed. Full promotion gates are unmeasured.


## Reproduction on the first result-document HEAD

Independent GitHub-hosted run [40178208888](https://github.com/FCMO-AI/.CMPCT/actions/runs/40178208888), exact HEAD `6b3fac994bcb4af4be4085e9d9adce0b4d334dbf`, **SUCCESS (1/1)**, with its own raw [artifact 12592769212](https://github.com/FCMO-AI/.CMPCT/actions/runs/40178208888/artifacts/12592769212), artifact SHA-256 `bcdff0fc306e7c1e6452829bc9bc23e3cf3e1cfbb6ced2b1118c39bd787bac68`.

The original input hashes, installed Builder blob and isolated one-expression oracle source SHA are identical to the original hosted run. Result:

| Metric | S_PACK shipping | Noncohort oracle | Claim |
|---|---:|---:|---|
| Full archive bytes | 790,524 | 792,646 | **Exactly reproduced** |
| Full create median wall | 9.747 ms | 53.087 ms | Creator benefit replicated; absolute times vary |
| 64-B selected read median wall | 404.632 µs | 44.539 µs | ~9.09× faster on oracle in this run |
| Selected-read decoded bytes | 687.911× oracle | baseline | **Exactly reproduced** |
| Full integrity and reconstruction | PASS | PASS | Exactly reconstructed |

**Joint interpretation:** the fixed output-byte delta and fixed decoded-work ratio are robust in two actual same-input source-bound hosted invocations, while clock timings vary. The creator-vs-reader tension is real for this one synthetic tree. Any estimate of how many lifetime reads could repay the oracle's one-time slower creation must be scoped to workload access frequency, caching, and the measured process boundary; no single universal break-even is claimed.

The original first-science-run setup FAIL remains available. Subsequent generic CI and official performance checks are separate workflows and must never be inferred from the focused result.
