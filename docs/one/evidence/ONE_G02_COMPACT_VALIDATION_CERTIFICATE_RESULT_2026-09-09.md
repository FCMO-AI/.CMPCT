# ONE-G0.2 compact validation certificate — result

Date: 2026-09-09  
Decision: **HOLD_COMPACT_VALIDATION_CERTIFICATE**

## Exact evidence authority

- Evidence source: `e6d4ade453745f7336cc771f23a08fa1a54ec5c3`
- Workflow: `CMPCT1 ONE-G0.2 compact validation certificate`
- Run: `34393672217`
- Job: `102607955100`
- Artifact: `10120658158`
- Artifact digest: `sha256:6e37194a51fcc9a12a76d463a241a625378d2195f875d636b335052ae99c32b8`

The exact-source lane passed all 45 validation/range semantic and hostile tests and reached the frozen falsifier. The benchmark exit was a scientific HOLD, not infrastructure failure.

## Frozen-gate result

The candidate retained validated node lengths as one immutable packed little-endian uint64 table after full ordinary validation. Valid logical lengths outside uint64 continue to fall back to the ordinary certificate, so the optimization does not narrow ONE semantics.

| Gate | Result |
| --- | ---: |
| semantic parity | PASS |
| compact absolute retained size | PASS |
| retained memory at 4,096 unrelated nodes <= 0.40x incumbent | PASS — **0.222963x** |
| median one-time open CPU <= 1.25x | PASS — **1.029997x** |
| median repeated-read CPU <= 1.15x | PASS — **1.006769x** |
| worst repeated-read CPU <= 1.30x | **FAIL — 1.794376x** |

At 4,099 total preflight entries, retained Python preflight state fell from **147,652 B to 32,921 B** for both add8 and XOR families. The compact representation therefore delivered the intended large-graph memory reduction without material median CPU cost.

The sole frozen promotion failure was the tiny three-entry add8 row: ordinary request CPU was about **1.449 ms**, compact request CPU about **2.601 ms**, or **1.7944x**. The corresponding three-entry XOR row was essentially neutral (**0.9998x**). Larger add8 rows were about 0.999-1.046x, and larger XOR rows about 1.003-1.035x.

## Causal interpretation

This result does **not** reject compact retained validation state. It rejects the current per-index decoding implementation as a universally safe replacement. `_PackedLengths.__getitem__` currently calls `struct.Struct('<Q').unpack_from(...)[0]` on every length lookup. For a tiny graph, the resident-memory saving is negligible in absolute terms while Python unpack/tuple-return overhead can sit directly on the hot range-evaluation path.

Because the large-graph rows already satisfy both memory and CPU gates, changing graph-validation policy or relaxing thresholds would be benchmark gardening. The rehabilitation target is the lookup mechanism itself.

## Reopening condition

A new candidate may reopen this line only if it preserves the exact same validation semantics and frozen V1 memory/CPU gates while causally reducing packed-index lookup overhead. A native-endian read-only `memoryview.cast('Q')` over the already-immutable bytes is the first bounded hypothesis on little-endian platforms; big-endian platforms must retain explicit little-endian decoding so portability is unchanged.

No threshold may be weakened to turn this HOLD into an ADVANCE.
