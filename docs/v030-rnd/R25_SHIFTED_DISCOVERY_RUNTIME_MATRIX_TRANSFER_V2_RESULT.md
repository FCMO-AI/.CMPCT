# r25 position-independent discovery source — runtime-matrix transfer v2 result

Status: **INVALID / ZERO TRANSFER, PRODUCT OR RELEASE CREDIT**

Frozen preregistration: `R25_SHIFTED_DISCOVERY_RUNTIME_MATRIX_TRANSFER_V2_PREREG.md`  
Exact source: `863027917b254a58b703bb8d4dadee92fa5974d5`  
Workflow run: `33811958273`  
Substantive job: `100835613765`  
Artifact: `9915412137`  
Artifact ZIP SHA-256: `c4e339104a76309fd2b9caa1fd8b48eb307287adaaaf21379eef1bf755227fd4`

## Terminal result

The v2 serialization repair worked: the experiment emitted a complete exact-head receipt instead of crashing. The inherited validity grammar nevertheless returned `INVALID` because it required positive delta timing and positive delta-call counts for every arm, including workloads/arms where the measured mechanism legitimately made zero delta calls.

No row receives transfer-decision credit from this invalid execution.

Observed diagnostic rows, preserved only to motivate the superseding validity model:

| target | byte delta | discovery/delta-call reduction | child-wall ratio | delta-wall ratio |
|---|---:|---:|---:|---:|
| shifted versions | 0 B | 28.9993% | 0.762538x | 0.708118x |
| logs/telemetry | 0 B | 100% | 0.997449x | 0.0x |
| ML artifacts | 0 B | 0% | 1.000246x | null |

The invalid reasons were exactly zero delta timing/calls in the Logs inherited-only arm and zero delta timing/calls in both ML arms. Those facts are structurally different from a missing or failed timer: a mechanism can be inapplicable on a workload and still be a valid byte-transfer observation.

## Causal interpretation

V2 falsified the assumption embedded in the v1/v2 validity grammar that every transfer target necessarily exercises the delta path in every arm. That assumption is not required by the scientific question, which asks whether removing the position-independent discovery source changes selected bytes and, where it is exercised, runtime work.

The diagnostic evidence is consistent with all three selected archives being byte-identical after ablation, but because the frozen validity law declared the run invalid, this document does **not** promote that consistency into the global byte-dead decision.

## Reopening / supersession requirement

A v3 freeze is justified by new causal evidence. It must preserve the same corpus, two alternating pairs, single ablation, archive/tree/integrity requirements and terminal scientific question, but replace the false universal positive-delta precondition with applicability-aware validity:

- positive finite complete child wall remains mandatory in every arm;
- if both arms have zero delta calls, the row is valid as `delta_path_not_exercised` and receives byte-identity evidence but no delta-speed evidence;
- if baseline has positive calls and the ablated arm reaches zero calls, zero candidate delta wall is valid and represents complete removal of measured delta work;
- any negative/non-finite timing, candidate increase in delta calls, inconsistent zero/nonzero timer/call state, archive/tree drift or verification failure remains invalid;
- global byte-dead promotion still requires exact byte/SHA identity on every target and a real call reduction on at least one exercised target.

V1 and v2 remain immutable historical evidence.
