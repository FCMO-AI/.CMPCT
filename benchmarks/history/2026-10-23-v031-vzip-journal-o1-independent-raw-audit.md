# CMPCT VZIP journal O1 — independent artifact-level adversarial review

**Date:** 2026-10-23 UTC. **Source of raw evidence:** GitHub Actions [40027718949](https://github.com/FCMO-AI/.CMPCT/actions/runs/40027718949), exact source `e495117b729b5300f0ecdc68370af001e8bc863d`, [original artifact 12533376979](https://github.com/FCMO-AI/.CMPCT/actions/runs/40027718949/artifacts/12533376979). Retrieved artifact ZIP bytes were independently checked locally against GitHub-reported `SHA256 e9eaf2e5ed39aef72b48e9140ab31d59943fb3f7474507247181dc99d50733d7`. The ZIP contains `base-native.json` and `vzip-journal-o1.json` with **36 actual raw per-observation rows**; this review does not rewrite the original artifact or preregistration.

## ABBA pairing audit
Actual experiment is three independent A-B-B-A cycles for each synthetic ZIP-rich regime; the table shows **per-cycle means** of two observations per engine, in milliseconds, plus fractional candidate change. This exposes stability and time-order effects concealed by one pooled median.

| Regime | Cycle | A original | B journal | Δ candidate versus A |
|---|---:|---:|---:|---:|
| Late reject, 0 preexisting aliases | 0 | 20.653 | 11.814 | −42.80% |
| Late reject, 0 preexisting aliases | 1 | 20.728 | 11.986 | −42.17% |
| Late reject, 0 preexisting aliases | 2 | 20.522 | 11.803 | −42.49% |
| Late reject, 64 preexisting aliases | 0 | 22.625 | 17.126 | −24.31% |
| Late reject, 64 preexisting aliases | 1 | 22.686 | 17.352 | −23.51% |
| Late reject, 64 preexisting aliases | 2 | 22.567 | 17.098 | −24.24% |
| Successful VZIP, 64 aliases | 0 | 20.012 | 20.736 | **+3.62%** |
| Successful VZIP, 64 aliases | 1 | 20.394 | 20.709 | **+1.54%** |
| Successful VZIP, 64 aliases | 2 | 20.219 | 20.491 | **+1.34%** |

**Strengthening of the result:** the large **late-reject** improvement is consistent across all three local ABBA rounds, and complete archive bytes are deterministically smaller. This rules out one accidental favorable pooled median in the measured host and supports the causal unused-candidate encoding explanation. A separate input family, stronger compression/larger member sizes and independent host/platform reproduction are still necessary for generalization.

**Stronger self-critique:** the **successful VZIP** case does have a small positive cost in **all three** ABBA rounds. It was initially called ambiguous based only on +0.220ms pooled median; the raw pairing suggests a possible true ~1–4% journal bookkeeping penalty on this favorable-success workload. Do not call it neutral or regression-confirmed at product/release level; three rounds and one short synthetic input remain weak evidence for a 1–4% effect. If broader official benchmark indicates a similar cost, retain safety fix and seek amortization/skip-work changes only with unchanged semantic contracts.

## Research decision boundary
The journal owner #287 gains **genuine product-mechanism support** for rejected ZIPs (strict bytes + large CPU/wall savings at fixed complete semantics) but not universal compression superiority or zero-performance-debt. The lower-rung callback microresult is not incorrect—it measures bookkeeping—but is insufficient to predict net Builder cost. The appropriate counterfactual discriminator was an exact whole-archive byte comparison of a failed speculative probe versus forced opaque and actual end-to-end Builder measurement. Normal PR #288 full CI and official same-runner release parity remain separate authority. **No policy, comparator, format or promotion changes.**
