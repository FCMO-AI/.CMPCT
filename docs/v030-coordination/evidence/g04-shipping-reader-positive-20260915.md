# v0.30 G04 shipping-reader positive — 2026-09-15

Corrected exact-ML A/B exact head: `c962ce7dee8311e621f399a2bdeb5e6c2e75eae2`.
Workflow run: `35038850772`.
Artifact: `v030-g04-delimiter-inverse-ab-c962ce7dee8311e621f399a2bdeb5e6c2e75eae2` (artifact id `10424721247`, digest `sha256:2031abee9956b01607c7c864bedf802b1ed543d1c7a3dbe63b9d920a458dfd69`).

This run fixes the custody defect in the earlier A/B by patching the **private isolated canonical reader** used by the release product (`PRODUCT.C.SHARED.G.O` plus canonical policy G04), not the public historical research module.

Target: `neutral_hostile_v1/09_ml_artifacts`, exact canonical archive, nine alternating extractions per arm, exact source-tree identity after every extraction, six differently shaped property controls.

Direct result:

- control: reviewed bulk rectangular-prefix v1;
- candidate: currently installed `release_single_buffer_delimiter_inverse`;
- control median: `0.19451258499999824 s`;
- shipping candidate median: `0.13288730599998644 s`;
- candidate/control: `0.6831810188527783x`;
- measured whole-extraction speedup: `31.681898114722173%`;
- inherited minimum mechanism speedup: `15%`;
- promotion signal: `true`;
- release credit: `false` (mechanism attribution only).

Raw control seconds:
`[0.19408409600001164, 0.19451258499999824, 0.19396751900001163, 0.1945733759999939, 0.19217218100000366, 0.19414327500000184, 0.19656372900000463, 0.19560031100000685, 0.1954476490000019]`

Raw shipping-candidate seconds:
`[0.13095260699999756, 0.13321752499999207, 0.13288730599998644, 0.13063464599999008, 0.13329690499999458, 0.13380130899999187, 0.1323610590000044, 0.13515158300000962, 0.1327533120000055]`

Decision: **retain the shipping single-buffer inverse.** The corrected causal instrument shows a large, stable exact-product extraction win over the reviewed bulk predecessor. The earlier ~1.50x “banded negative” is custody-confounded and must not be used to retire this shipping mechanism.

This does **not** prove the v0.30 ML runtime gate is green versus v0.29. The prior product-level runtime debt was much larger than one local inverse mechanism; this result only establishes that reverting the shipping inverse would be a substantial regression. The next product action remains fresh exact-head authority-v2/runtime measurement followed by attribution of the residual gap.
