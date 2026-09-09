# ONE-G0.2 validated authenticated selective lifecycle — result

Date: 2026-09-09  
Decision: **ADVANCE_VALIDATED_AUTHENTICATED_LIFECYCLE**

## Exact evidence authority

- result-bearing source: `69320eef76fa1c0d9597d1c001f040e191eee5df`
- workflow: `CMPCT1 ONE-G0.2 validated authenticated selective lifecycle`
- run: `34396871356`
- job: `102618658156`
- artifact: `10121897100`
- artifact SHA-256: `60718f0036cb7dbb8e527a7e0eb3462363430ebaacd6e15ef185e781817fddfc`
- inherited validation/authentication/cone tests: **83 passed**

The source SHA was checked out exactly and exported as `EVIDENCE_HEAD` before the frozen falsifier ran.

## Mission outcome

The complete repeated selective-read lifecycle crossed the preregistered systems gate:

`open once -> complete Program validation -> retain sealed validation authority -> repeated authenticated native selective cone reads`

beats the promoted raw-Program path that repeats complete preflight on every request, while preserving exact returned bytes, authentication, cone geometry, and modeled per-request movement.

No format, Law, Surprise, integrity, recovery, portability or resource rule changed.

## Frozen gate results

| Gate | Frozen limit | Result | Verdict |
|---|---:|---:|---|
| semantic parity | exact | exact | PASS |
| raw/validated cone movement | identical | identical | PASS |
| retained proof @ 4096 nodes | <= 0.40x | **0.224265x** worst | PASS |
| median lifecycle CPU, >=4 reads | <= 0.75x | **0.299564x** | PASS |
| median lifecycle CPU, >=16 reads | <= 0.50x | **0.126187x** | PASS |
| worst one-shot lifecycle CPU | <= 1.30x | **1.248532x** | PASS |
| every 4096-node >=4-read row | <1.0x | **0.291896x** worst | PASS |

All result gates passed.

## Mechanism-level evidence

The result is strongly graph-size dependent in exactly the direction predicted by the preflight cost-owner experiment.

For a 4,096-node add8 Program with a 128 KiB root:

- 1 request: `8.499 ms / 7.530 ms = 1.1286x` — the one-time open proof is visible and slightly loses;
- 4 requests: `8.815 ms / 30.383 ms = 0.2901x`;
- 16 requests: `9.904 ms / 121.325 ms = 0.08163x`;
- 64 requests: `14.713 ms / 500.650 ms = 0.02939x`.

The corresponding XOR 4,096-node rows were `1.1267x`, `0.2900x`, `0.08136x`, and `0.02886x` for 1/4/16/64 requests.

The same pattern held for crack Laws and the literal/fill/concat controls once unrelated valid graph state was large enough. This is important: the win belongs to eliminating repeated global validation, not to special-casing add8/XOR.

At 4,096 nodes the economically admitted compact certificate retained **33,089 B** versus **147,544 B** for the ordinary Python preflight state (`0.224265x`). Small Programs correctly retained the ordinary certificate when packing would not save honest resident state.

## Data locality / integrity truth

Candidate and comparator had byte-identical requested outputs for every row, and per-request authenticated cone movement remained identical. For the common beginning request the cone stayed 4 KiB; a middle-crossing request used 8 KiB. Validation amortization therefore removed control-plane CPU only—it did not manufacture a win by changing the reconstructed/authenticated data plane.

The shared AuthTree index remained visible at 1,988 B for this 128 KiB / 4 KiB-leaf matrix and was not credited away as candidate work.

## Strongest negative result / boundary

Open-once validation is **not** universally free. The worst one-shot row was `1.248532x` the raw path, and small 3–6-node Law Programs remained around `1.08–1.19x` for one request. Even 64 repeated reads on tiny graphs only reached roughly `0.69–0.76x` for the Law cases because raw preflight is already cheap there.

Therefore this result does **not** authorize blindly replacing every one-shot raw selective read with an eager reusable-open path. The correct systems interpretation is:

- shared/repeated opens: reusable sealed validation authority is now the preferred research path;
- genuinely one-shot/tiny graphs: retain an economic route choice rather than imposing open-state machinery unconditionally.

## Architecture consequence

ONE now has evidence for both locality planes:

1. **data plane:** authenticated native Reconstruction Cones avoid unrelated root-byte work;
2. **control plane:** sealed complete validation avoids re-proving unrelated graph validity per request.

The reader shape is now credibly:

`authenticate/open immutable representation -> prove complete bounded validity once -> retain compact proof when economically smaller -> execute repeated authenticated reconstruction cones locally`.

This keeps the reader mechanical. It adds no discovery and no Law-family codec path.

## Next decisive action

Do not continue isolated compact-certificate benchmarking. The next reader experiment should preregister a **generic economic route admission** across one-shot versus shared-open usage, using only already-known structural facts (graph size, request count/intent where available, topology support, cone geometry/cost) and never workload labels. It must choose between the simple raw path and the reusable validated/native-cone path without making either class materially worse.

The September 11 Genesis gate remains separate and embargoed until the first qualifying activation on/after 2026-09-11 America/Mexico_City. This result is mechanism/system evidence, not a supersession declaration.
