# O22 — shared resource policy cold Reader result (measured, not promoted)

**Date:** 2026-10-24 UTC. **Pre-registered before implementation:** `5fbe2a8eb08e5a26c76289d387a7aa971563587d`. **Exact product/instrument observation head:** `fe898359db2d36e9001a516994f4ff51ba4c7b0e`. **Source parent:** O10R #365 `54c998200b1908b696ade049fe94df71a736c284`. Current v0.30.0/r24 released product unchanged.

## Source-exact hosted outcome
[Actions run 40124440059](https://github.com/FCMO-AI/.CMPCT/actions/runs/40124440059) completed **SUCCESS**. Raw 80 child-process measurements retained in [artifact 12572023815](https://github.com/FCMO-AI/.CMPCT/actions/runs/40124440059/artifacts/12572023815); JSON result receipt SHA-256:
`a972f7e67edd938d0d06bb3521e34f3445c0e7a60ff2e81b86fbcda059959fbb`.
Observed artifact ZIP transport SHA-256 from GitHub Actions upload:
`c51ea971665d202e0219b2f08b08eed3a286f2a539952d69c536fcdb1820adda`.

The hosted job installed the actual O22 candidate and validated exact Git blobs of the O10R historical Reader (`2402721258531a56cfa2a53dcbd81874fd6c1f76`), O22 candidate Reader (`2ee41b4b51bac88cfb815c6d0532be97d13fa823`), new shared policy (`dda379de094cbe6e0d4ecdffb97cb0be9cba0e36`), validation (`4059443d447f1bb95175841c558b58a3bfee1c33`), and authentic source fixture (`02c5f506c9294130db6b0eb9c36c0a61460c3b35`). Source-only historical Reader substitution uses the same installed O22 dependency closure; this is **NOT** a two-wheel or official release A/B.

The unchanged O10R hostile authenticated-generation/depth tests plus the new shared-identity/actual-signed-checkpoint subprocess tests: **4/4 PASS**. The new checkpoint test explicitly proved strict `cmpct.validation` was *not imported* when opening a genuine signed checkpoint with O22, whereas the signed journal still caused the indexed validation replay to load. Both environments read exact original payload.

## Fresh-process A/B median import + Reader-construction (Ubuntu CPython 3.11)
| Authenticated members | O10R historical journal | O22 journal | O10R checkpoint | O22 checkpoint |
| --- | ---: | ---: | ---: | ---: |
| 512 | 23.210 ms | 23.088 ms | 22.657 ms | 21.822 ms |
| 4096 | 32.007 ms | 31.993 ms | 26.321 ms | 25.804 ms |

Journal ratios: 1.0053× at 512, 1.0004× at 4096 (essentially neutral). Checkpoint changes: **−0.835 ms / −3.68%** at 512, **−0.517 ms / −1.96%** at 4096. No result exceeds the O13 prospective materiality threshold of 5% AND 3 ms. The Linux lifetime journal VmHWM after construction changed from 24,756 to 24,708 KiB (512) and 27,800 to 27,886 KiB (4096); these HWM differences are not an instantaneous heap comparator or significant economic win. Full-child-process wall/CPU observations are preserved in artifact but are NOT asserted here until independently summarized and audited.

**Scientific decision: `ISOLATION_MECHANISM_CONFIRMED__LATENCY_WIN_NONMATERIAL`.** The proposed causal import boundary exists and can be removed while preserving focused safety semantics, but the wall improvement is below material threshold and might partially be noise. **Do not claim that isolating the strict validator solves O13's observed 3–6 ms gross checkpoint debt.** Different hosted runs cannot be subtracted to attribute that debt, and original O13 used different controls. There is no demonstrated substantial product speedup and no reason to prioritize a new resource-policy module purely on performance grounds.

## Strong negative, counterfactual and cost
The original hypothesis that heavy structural validator import owns most checkpoint cold debt is **narrowed**: module admission disappears, but observed cold latency changes by <1 ms. Other fixed Python/package/CLI startup, actual filesystem/mmap/init, runner variance, and `dataclasses` import are competing owners; do not guess which without profiling. Prospective class introspection/`__module__` and old Python pickle compatibility require explicit review because classes moved from `cmpct.validation` to `cmpct.resource_limits`; alias identity alone does not guarantee all import/reflection use cases. Two source files edited plus one added module and tests/workflow constitute ongoing carrying cost. Preserve source as unmerged reversible draft, or retire it if no non-performance advantage offsets complexity.

## Credit and continuation
**Product security:** 4 focused tests green on tested Ubuntu; the inherited O10R 3-OS negatives/positives are separate-source evidence. **Engineering:** one small candidate refactor landed on draft. **Scientific:** decisively narrower than proposed performance win. **Release/benchmark:** ZERO; no compression ratio, create/extract, portability or official parity improvement established by this O22 court. Later broader CI statuses must be checked at exact source; administrative success/skips are not product proof. Avoid further threshold gardening. Next highest-value path: product convergence (O10R security, O9 replay, prewrite safety) or a genuinely different cold-process ownership model, not iterative lightweight-import variants.

**No merge, numeric bump, format change, release, benchmark threshold or evaluator relaxation authorized.**
