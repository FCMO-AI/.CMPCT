# ONE-G0.2 compact validation certificate V3 — result

Date: 2026-09-09  
Decision: **ADVANCE_COMPACT_VALIDATION_CERTIFICATE**

## Exact evidence authority

- Evidence source: `0607fdff930b66eb9d92a097f304d8ca0b3e5a87`
- Workflow: `CMPCT1 ONE-G0.2 compact validation certificate`
- Run: `34394443280`
- Job: `102610538455`
- Artifact: `10120946840`
- Artifact digest: `sha256:ccf0ec40d59b248b006b21c7b27c28bb6559522f1f0c043f2cd26bf128c67290`

The exact-source lane installed the repository test dependency surface, passed all 46 validation/range semantic and hostile tests, ran the unchanged V1 falsifier, and retained the exact-source JSON artifact.

## Result

V3 keeps complete ordinary Program validation as the authority. It may replace the retained node-length tuple with an immutable dense uint64 proof only when:

1. every proven logical length fits the optional uint64 optimization domain; and
2. the honestly measured retained Python state of the compact proof is strictly smaller than the ordinary proof.

Otherwise the already-valid ordinary proof remains in place. There is no workload-name or node-count threshold.

All frozen V1 gates passed:

| Gate | V3 result |
| --- | ---: |
| exact semantic parity | PASS |
| 4,096-unrelated-node retained state <= 0.40x ordinary | PASS — **0.224264x** |
| absolute retained-size law | PASS |
| median repeated-read CPU <= 1.15x | PASS — **1.004517x** |
| worst repeated-read CPU <= 1.30x | PASS — **1.027290x** |
| median one-time open CPU <= 1.25x | PASS — **1.142040x** |

At 4,099 preflight entries, retained proof state is **33,113 B versus 147,652 B** ordinary for both add8 and XOR families. The dense proof therefore removes roughly **77.6%** of retained Python preflight state on the large graph while keeping repeated reads essentially CPU-neutral.

The V1 pathological three-node add8 row is repaired causally. V1 forced the packed representation there and measured `1.7944x` repeated-read CPU. V3 recognizes that the compact representation has no retained-state advantage at that scale and leaves the ordinary proof in place; the same row measures **1.0041x** repeated-read CPU. Tiny XOR similarly remains ordinary at **1.0001x**.

The large rows use the compact proof. Their repeated-read CPU remains near incumbent: approximately 0.992-1.027x across the frozen matrix.

## Negative lineage retained

- V1 (`e6d4ade453745f7336cc771f23a08fa1a54ec5c3`) remains **HOLD** because one tiny add8 row reached 1.7944x CPU despite the strong memory result.
- V2 (`18c3d2d5a1c9c3883ff3ac3b55c0c6da804d7eb6`) remains **REJECTED BEFORE FALSIFIER** because a read-only memoryview made a tiny proof larger than ordinary retained state. That fixed metadata is still charged in V3.

No threshold was weakened to promote V3.

## Interpretation

This closes the immediate reusable-validation proof-state problem for ONE-G0.2: full graph validity can be proven once, retained as a sealed immutable authority, and represented densely when doing so is actually economical. Repeated selective reads therefore need not redo O(graph) validation, nor must large graphs retain thousands of Python integer objects merely to remember proven node lengths.

The promotion is an in-memory reader optimization only. It changes no ONE wire, Law, Surprise semantics, resource policy, integrity rule, or accepted logical-length domain. Valid >uint64 logical graphs retain the ordinary authority rather than being rejected or truncated.

## Next decisive work

The next systems test should charge the complete lifecycle rather than benchmark this component indefinitely:

`open/authenticate -> complete validation once -> retained validation authority -> repeated authenticated selective cone reads`

It should vary request count, graph size, requested cone size and cheap-control topology, preserve all existing integrity/resource failures, and measure when the one-time open proof amortizes. Native cone admission must remain economic: cheap Literal/Fill/Concat requests should retain the simpler reader path when native planning/proof overhead cannot repay itself.
