# O13 result — O10R signed-generation resource ceilings versus O9 Reader cold economics

**Observation date:** 2026-10-24 UTC. **Decision:** no preregistered material checkpoint/journal cold gate triggered; a repeatable smaller checkpoint cold cost remains. **Research only, not a release.**

## Source/custody boundary
- Preregistered **before** implementation at `dfdfb02d84a86589b17509671ae5f8f130a09d0f`.
- Corrected final test source HEAD: `9a659f50c517da1602f182a0ee01311b66bc6946`. Hosted experiment [Actions 40118135703](https://github.com/FCMO-AI/.CMPCT/actions/runs/40118135703): **SUCCESS**; source-bound artifact `12570297707`, original ZIP SHA-256 `5f935cade39f1954cb0986270b10fb4d0b43af333547153242453f68633f1b76`, raw JSON SHA-256 `3f6fce02c8bc52e6c3b6793af52b9a49ef29cee1481be7a33df40f2b5b548ac0`.
- Exact O9 source control: `1d8701588bdb8ece69749149a60d4b70a643e12f` / Reader Git blob `bd1df6091c952e74c8690cf2ba0764747e6db815`.
- O10R installed candidate: `54c998200b1908b696ade049fe94df71a736c284` / Reader Git blob `2402721258531a56cfa2a53dcbd81874fd6c1f76`.
- 80 fresh-process raw observations in total, 10 per source/archive cell; 5 alternating blocks; 512 and 4,096 genuine signed renames; authentic Builder-generated same-input r24 journal/checkpoint; independent index SHA/payload equality and same complete-archive SHA/bytes across both Reader variants; Python 3.11.17 on Ubuntu Linux. The historical O9 Reader is dynamically source-loaded into **O10R's installed non-Reader dependency closure**, not a separately installed O9 wheel.
- First attempt source HEAD `50802d93fbbefe982eb5d1e6eb47d84329c569a4`, [run 40117887191](https://github.com/FCMO-AI/.CMPCT/actions/runs/40117887191), independently audited. Its JSON had a **misleading `credit` string** calling both arms O9 despite correct SHA/source comparisons; this was corrected with a code-only receipt-label edit before the second complete hosted run. Preserve both original artifacts; use the corrected final record for claims.

## Source-exact result (median of 10 subprocess observations per cell, milliseconds)

| Signed archive | O9 import+Reader | O10R import+Reader | O10R minus O9 | Relative | Complete child process O9→O10R | Linux VmHWM O10R−O9 |
|---|---:|---:|---:|---:|---:|---:|
| 512 journal | 33.153 | 32.330 | −0.823 | −2.48% | 93.333→92.589 | +10 KiB |
| 512 checkpoint | 29.294 | 32.090 | **+2.796** | **+9.55%** | 86.638→92.439 | +182 KiB |
| 4096 journal | 44.119 | 43.872 | −0.247 | −0.56% | 106.612→105.477 | −92 KiB |
| 4096 checkpoint | 34.757 | 36.486 | **+1.728** | **+4.97%** | 96.097→99.149 | +200 KiB |

The five checkpoint **paired block** extra costs are all positive: 512: `+2.075,+2.569,+2.151,+2.192,+3.430ms`; 4096: `+2.004,+1.949,+1.752,+1.430,+2.147ms`. Signed-journal results are much closer and direction-sensitive to noisy host start/run ordering; one 512-journal block showed a −24ms transient. Raw samples, not headline medians, remain authoritative.

## Prospective decision / counterfactual
**No condition simultaneously exceeded +5% AND +3ms import+constructor**, for either checkpoint or journal at either preregistered size. No condition increased Linux lifetime HWM simultaneously by >10 MiB AND >10%. Thus **O10R does not erase the O9 journal gain within this scoped O13 court** and the preregistered material regression criterion was not met. **But checkpoint cold opens reproducibly pay ~1.7–2.8ms**, which is a real smaller exported cost, not zero. A lighter shared `ParserLimits` import boundary is a possible product simplification only if a stronger measured workload values the saving enough to justify a new module and maintaining exact policy authority.

What earlier observable could have decided this sooner? A single authentic checkpoint cold-open A/B with the resource patch, retaining both process wall and CPU, would have exposed the likely import-owner cost. To establish a *nonmateriality* decision across journal/checkpoint and source identities, the additional ABBA/BAAB repeated court was still warranted. No discovery-policy modification is earned from a single case.

## Adversarial limitations
- One Ubuntu CPython 3.11 run and dynamic Reader-module substitution, not both independently installed wheel lineages or Windows/macOS latency.
- `VmHWM` is process lifetime high water; cannot attribute tiny differences solely to Reader allocations.
- The builder output is the same across arms; no archive-size improvement is claimed. The official parity court measures create/extract, not the cold-open boundary.
- This research does not replace [O10R hosted authentic resource-red→green](https://github.com/FCMO-AI/.CMPCT/actions/runs/40110160739) or resolve symlink TOCTOU, crash-atomic extraction, all MessagePack nested-collection resource limits.
- No regression hidden by changing timing thresholds, repeats, corpus identity or semantic contracts.

## Next action
Retain #365's authenticated generation size/depth protection with the measured checkpoint cost. When advancing O9→O10R product convergence, preserve the 4096-journal performance advantage and rerun the final installed three-OS safety and parity gates. Only investigate a lightweight limit-policy import split if actual cold-start product economics justify its extra complexity; an unmeasured optimization is not warranted. The O13 branch owns only this research court, no independent Reader implementation. Do not touch shared `docs/discovery/STATE.json`.
