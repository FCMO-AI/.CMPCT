# ONE-G0.2 Native Exact Relation Proof — Result (2026-09-09)

## Decision

**ADVANCE_NATIVE_EXACT_RELATION_PROOF**

A bounded zero-copy native verifier reproduces the authoritative Python `grow_relation_spans()` proof semantics exactly while reducing exact-proof CPU by roughly twenty-fold on the frozen hosted matrix. This is an implementation-level writer-side advance only: it performs no discovery, adds no reader-visible operation, and does not weaken exact proof.

## Exact authority

- branch: `research/cmpct1`
- experimental version: `ONE-G0.2`
- exact source SHA: `c9b56705acf7d6aa3a8b24024c02d4503d6e5849`
- workflow: `cmpct1-one-g02-native-exact-relation-proof`
- run: `34352861084`
- job: `102470152848`
- artifact: `10104620808`
- uploaded artifact ZIP SHA-256: `c1a4885d84f6bb9ba346ab69d9be69165970f95b45d72d81ca5dbb52db3ee177`

Exact checkout/frozen-law binding passed, the semantic oracle/native parity suite passed (`11 passed`), the complete frozen falsifier returned `ADVANCE_NATIVE_EXACT_RELATION_PROOF`, and the artifact uploaded successfully.

## Frozen-gate result

Hosted aggregate CPU ratios:

- median productive native/Python: **0.0510023x**;
- worst productive: **0.0546354x**;
- median hostile native/Python: **0.0506674x**;
- worst hostile: **0.0546276x**.

Frozen requirements were <=0.25x median / <=0.50x every productive row and <=1.00x median / <=1.50x every hostile row. The result clears them by a wide margin without moving thresholds.

Equivalent speedup is roughly **19.6x median** on productive proof and **19.7x median** on hostile proof.

## Representative hosted measurements

At 1 MiB per relation input:

### add8 exact

- Python proof CPU: **112.140 ms**;
- native proof CPU: **5.600 ms**;
- ratio: **0.04994x**;
- accepted bytes: **1,048,576**;
- semantic compared bytes: **1,048,576**;
- native bytes loaded per input: **1,048,576**;
- aggregate parent+child proof load: **2,097,152 B**.

### XOR exact

- Python proof CPU: **100.783 ms**;
- native proof CPU: **5.506 ms**;
- ratio: **0.05464x**;
- accepted bytes: **1,048,576**;
- semantic compared bytes: **1,048,576**;
- native bytes loaded per input: **1,048,576**.

### add8 sparse cracks

- Python proof CPU: **115.339 ms**;
- native proof CPU: **5.583 ms**;
- ratio: **0.04840x**;
- accepted bytes: **1,048,456**;
- semantic compared bytes: **1,048,471**;
- native loaded bytes per input: **1,048,576**;
- physical load amplification: **1.0001001x**.

### XOR sparse cracks

- Python proof CPU: **104.582 ms**;
- native proof CPU: **5.511 ms**;
- ratio: **0.05270x**;
- same accepted/semantic/load geometry as add8 sparse cracks.

## Semantic and hostile parity

Every row matched the Python oracle exactly for:

- plain `(start, length)` run tuples;
- `compared_bytes` including the exact mismatching-byte frontier;
- `accepted_bytes`;
- `rejected_seeds`;
- sparse-crack recovery/coalescing behavior.

The parity tests additionally cover duplicate, negative, larger-than-uint64 and enormous Python nomination integers, oversized seed geometry, enormous extension sizes, random cracks, and finite zero/small inputs. Python's unbounded integers are normalized before the bounded native ABI without changing oracle behavior.

This result supersedes the earlier flawed native-proof repair lineage through `dfb7a4a2298da92dfff545a6ac5cf221cbb65db4`, which is explicitly inadmissible because it invented a nonexistent `RelationSpan` oracle type.

## Physical memory-traffic truth

The SIMD kernel reports physical source load separately from semantic proof comparisons. This closes the preregistered accounting requirement that a 16-byte vector load may inspect lanes beyond the first semantic mismatch.

Worst hosted load amplification over semantic `compared_bytes` was **1.0004582x**, on the 64 KiB early-mismatch rows. At 1 MiB the largest observed amplification was roughly **1.0002243x** on multi-region cases. Exact and late-mismatch rows were exactly **1.0x**.

Thus the speedup is not purchased by an unreported bulk over-read. The kernel may read up to the remainder of one SIMD vector at an individual failed frontier, but the retained evidence exposes that traffic explicitly.

## Causal conclusion

V4 established that gate/seed-transfer work is already cheap and Python exact proof dominates positive relation CPU. This experiment isolates that owner and shows it was implementation cost, not an inherent consequence of exact ONE proof semantics.

The productive proof boundary can therefore remain strict and byte-exact while becoming a native bulk operation. This is consistent with ONE's intended architecture: cheap observation, selective reasoning, exact proof, then ordinary generic Law emission.

## Strongest criticism

This result proves the verifier in isolation. It does **not** yet prove the complete V4 writer improves by the same ~20x, because incumbent writing, sparse gate, seed transfer, Program construction, canonical emission, validation, Python/ctypes boundary cost, and reader-side reconstruction economics still exist.

Reader debt is untouched: generic relation Programs still materialize/reconstruct more bytes than the mature temporal incumbent in current V4 evidence. Native proof is a writer-speed advance, not a reader/access solution.

## Next decisive action

Consume the preregistered full-writer `ONE_G02_NATIVE_PROOF_WRITER_INTEGRATION` lane. It may promote only with byte-identical V4 wire/coverage, unchanged no-op control behavior, complete writer CPU improvement, and <=1.01x physical proof-load amplification. Do not infer the full-writer verdict from this isolated proof result.

## Campaign boundary

Frozen Genesis comparators remain:

- v0.29: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- deferred v0.30: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

No ordinary v0.30 development resumes from this result. The required full 15-workload same-input/same-semantics Genesis decision remains due at/after the first activation on 2026-09-11 America/Mexico_City.