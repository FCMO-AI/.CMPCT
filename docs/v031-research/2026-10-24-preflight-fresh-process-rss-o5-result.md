# O5 — higher-N source-exact signed replay RSS falsifier: decision

**2026-10-24 UTC — signed-product scientific evidence only.** O5 was preregistered before the larger-N observation at `d9640ccd65f70987bb3609737044d4ef38d194ce`; it follows O4's bounded high-water-memory ambiguity without modifying any product file.

## Exact sources and immutable evidence

- O5 measurement source HEAD: `870647a3650c4806290a73a0b4565b23b49fc0d9`; combined validator *unchanged* `validation.py` blob `1e085db992add64118a9488790096c574fff154d`, inherited [PR #348](https://github.com/FCMO-AI/.CMPCT/pull/348) `0062961be78cd4d28231a9acaf37a4d9cf43920c`.
- Historical exact comparator: `_apply_delta` from frozen Git blob `51c2849061f99a4afeddb7666956b24566ce7de0`, injected only inside the comparator child.
- [Result-bearing Linux GitHub Actions run #40093015164](https://github.com/FCMO-AI/.CMPCT/actions/runs/40093015164): **SUCCESS** for both O4 repeat and independently preregistered O5 (all script assertions and package setup passed).
- [O5 raw samples artifact #12560240092](https://github.com/FCMO-AI/.CMPCT/actions/runs/40093015164/artifacts/12560240092): ZIP SHA-256 `12a13ca9527d039491fb8dd81581b5a0795cc0a2718d8f67a0d78fd9cb3a5276`; inner JSON `fresh-process-rss-o4.json` SHA-256 `8e9077f9f0485b8dc80313fa8fd3d584a5eca5c89f4ed003119537c9bc4bde8f`.
- Five **independent fresh child processes per historical/combined arm**, alternating arm order; identical fully SHA-authenticated Builder-derived r24 archives for each arm, with signed 16,384 rename generation versus exact-final-index checkpoint. Combined 40,423 stored archive bytes (journal), equivalent checkpoint 16,429 bytes. Open/read/preflight identity guarantees and three sample content controls inherited from unchanged corpus generator.

## O5 measured medians

| Case (16,384 files) | Historical preflight | Combined preflight | Historical / combined `ru_maxrss` | Historical / combined post-minus-pre `VmRSS` |
|---|---:|---:|---:|---:|
| Signed 16,384-renames journal | **5,710.192 ms** | **83.642 ms** | **51,732 / 51,732 KiB** | **+4,700 / +5,888 KiB** |
| Equivalent signed checkpoint | 53.392 ms | 53.702 ms | 51,732 / 51,732 KiB | +4,652 / +4,768 KiB |

The signed journal's observed **68.27× speedup** is a strong additional large-N CPU result on authentic source-bound installed product semantics, not a claim about whole-product create/extract throughput. The checkpoint shows no meaningful preflight time change.

**High-water caveat remains:** `ru_maxrss` was already at 51,732 KiB in *every* child **before** measured preflight, so equal post-call values do **not** establish equality of intermediate peak RSS. Linux live VmRSS measured immediately after the call shows **+1,188 KiB** additional median candidate growth (5,888–4,700 KiB) and **+116 KiB** additional checkpoint growth (4,768–4,652 KiB). The control-adjusted difference-of-differences is **+1,072 KiB**, around **3.8%** of the 28,348 KiB historical post-call resident memory. The O4 negative at N4,096 was of similar size (about +1,140 KiB checkpoint-adjusted). Neither test finds the preregistered **>=8 MiB absolute or >=10% overall-resident** signal. No evidence supports calling the optimization memory-free.

## Decision and counterfactual

**Reject immediate memory-structure redesign as the highest-value action for N<=16,384.** Despite +42.77% relative `tracemalloc` allocation in the earlier 4k experiment, this independently hosted source-exact 16k product archive court did not find material persistent resident-memory debt; the existing 68.27× CPU gain and no changed checkpoint result justify *preserving* the combined candidate pending broader integration. The size scaling result narrows the material-resident-memory concern without proving product-wide Pareto dominance or bounding transient in-call peaks.

If future priority warrants, monitor in-function VmRSS/USS over time or run a true separated peak sampler; do **not** infer the intermediate maximum from saturated `ru_maxrss`. Any such extension must itself earn its cost with a decision that can affect actual admission. This repeated family has now met the prospective bounded final-attempt law: no further threshold/range gardening without a fundamentally different information/ownership question.

**No discovery-policy change earned**; one transferable prospective lesson is to pair trace allocation with independent live resident-memory measurement *and* explicitly inspect whether pre-call high-water is saturated. All release/CI/platform/performance parity gates remain separate, and no published product is changed.
