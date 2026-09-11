# ONE-G0.2 — packed quaternary descriptor-proof rehabilitation — 2026-09-05

## Mission lock

The exact quaternary structural A/B advanced arity 4, but the first CPython/hashlib compute A/B found V=8 reference verification about 15.9% slower than binary despite fewer SHA calls and slightly fewer SHA input bytes. Inspection identified proof metadata that carried no authenticated information: `(level, slot, child_count, sibling-slot integers)` were stored as Python objects although all are deterministic from `(descriptor index, version count, current tree width)`.

The frozen Builder therefore changed only the in-memory proof shape. Each quaternary proof level now carries the same sibling digests concatenated in canonical child order with the current child omitted. The verifier derives geometry and inserts the running digest at the derived slot. Hash domains, descriptor controls, Surprise bytes, tree root, proof digest bytes and corruption semantics are unchanged.

Frozen V=8 gate required zero exact/corruption/proof-byte failures, median packed/old quaternary verification `<=0.92x`, median packed/binary `<=1.05x`, and no V=4 row above `1.05x` old quaternary.

## Exact execution identity

- experimental version: `ONE-G0.2`
- exact source: `aa427e7031e6b02d440ea382869be32e2838af65`
- workflow run: `33954740296`
- result-bearing job: `101275884654`
- artifact: `9965990357`
- artifact ZIP SHA-256: `55a79fa3845edf8066f401c095e2ef08995b6b45d256e2ff13266b57172f7118`
- ONE semantic boundary: **76/76 passed**
- exact failures: **0**
- corruption-rejection failures: **0**
- proof-byte mismatches: **0**
- decision: **`advance_packed_quaternary_proof`**

## Result

| versions | median packed / old q4 | median packed / binary | max packed / old q4 | max packed / binary |
| ---: | ---: | ---: | ---: | ---: |
| 4 | **0.967119x** | **0.951794x** | 0.976579x | 0.960130x |
| 8 | **0.844739x** | **0.969695x** | 0.847541x | 0.973600x |

At V=8 the packed representation removes about **15.53%** of the old quaternary reference-verification elapsed and ends about **3.03% faster than the exact binary reference verifier**. Every V=8 row independently agrees:

- 64 KiB base 0: packed/old `0.843692x`, packed/binary `0.955594x`;
- 64 KiB base 1: `0.843005x`, `0.970753x`;
- 64 KiB base 2: `0.841483x`, `0.972308x`;
- 256 KiB base 0: `0.845786x`, `0.968636x`;
- 256 KiB base 1: `0.847541x`, `0.973600x`;
- 256 KiB base 2: `0.846205x`, `0.967245x`.

At V=4 the same representation is modestly faster than the old quaternary verifier on every row and is also faster than binary at the median. The V=4 proof remains **96 B** and the V=8 proof remains **128 B**; no authentication byte was deleted or gifted away.

## Causal interpretation

The previous V=8 quaternary slowdown was not evidence that higher-arity authentication intrinsically costs more execution time. The decisive difference was redundant reference proof structure: Python tuples/lists and explicit slot/control integers that the reader could derive without storing or transferring them.

This rehabilitation preserves the structural q4 result:

- V=8 persisted descriptor hashes: **448 B binary -> 320 B quaternary**;
- selected 80-byte basis-leaf worst-family complete stored fraction: **0.90183258x independent literals**;
- worst-row median authenticated 4 KiB touch: **1.18603516x**;
- V=8 q4 build already used fewer SHA calls and was about 4.7% faster than binary in the prior reference A/B.

The combined evidence now supports q4 as the current generic descriptor-authentication research shape, with canonical geometry derived at read time rather than redundantly serialized into proof objects.

## Hostile review / remaining debt

This is still CPython/hashlib reference evidence. It does not prove native/product verification throughput. A separately frozen C/OpenSSL binary-vs-quaternary discriminator is already queued and independently checks both native roots against Python before accepting timing. Its result remains necessary to distinguish interpreter rehabilitation from native execution economics.

The basis AuthTree creation cost also remains real: prior native C/OpenSSL evidence still charges roughly 4.1–4.2x whole-SHA creation around the structurally interesting 96/112-byte leaf region, and the selected 80-byte basis point is costlier. Packing descriptor proofs does not erase that separate basis-authentication bill.

## Claim boundary

Reference descriptor-authentication execution rehabilitation only. No canonical wire mutation, end-to-end archive creation speed, peak-memory, full 15-workload, v0.29/v0.30 supremacy, portability or release authority is claimed.
