# ONE-G0.2 growable direct emitter — repeatability classification

Date: 2026-09-05
Experimental line: ONE-G0.2
Authoritative branch: `research/cmpct1`

## Authorities

- Parent preregistration: `docs/one/evidence/ONE_G02_GROWABLE_DIRECT_CANONICAL_EMITTER_PREREG_2026-09-05.md`.
- First failed gate: `docs/one/evidence/ONE_G02_GROWABLE_DIRECT_CANONICAL_EMITTER_RESULT_2026-09-05.md`.
- Boundary diagnostic: `docs/one/evidence/ONE_G02_GROWABLE_EMITTER_BOUNDARY_DIAGNOSTIC_RESULT_2026-09-05.md`.

## First parent-gate run

- source: `8017e8c5f4d1bf616d0b1e971eae7523a979d5f9`
- workflow: `33992597245`
- job: `101377359758`
- artifact: `9977073178`
- artifact SHA-256: `c822bd712cd363716503d09e7b728f216a599b80f65496e861c89751cae0f500`
- tests: **93 passed**
- semantic gate: pass
- formal decision: `retire_growable_direct_canonical_emitter`

It produced a very strong broad signal but one absolute-gate failure: productive median **0.369928x**, 20/21 productive rows <=0.95x, every control size median below baseline, but 256 KiB `shift_plus1` measured **2.752696x**.

## Frozen boundary diagnostic

The preregistered dense size sweep then falsified a stable 256 KiB `bytearray` growth cliff. On exact source `433937e49c08106210e78957e0ce056f4f6af19a`, 13 exact-shift sizes from 96–320 KiB were all <=1.03x and the exact 256 KiB row measured **0.547454x**. No isolated blob-append row reached 1.20x.

Frozen decision: `classify_parent_outlier_nonrepeatable`, which authorized only an unchanged repeatability run of the parent gate.

## Unchanged parent-gate repeatability run

- branch source included by PR merge: `48c720a72137672b30a7e5242ae24d407c12ec65`
- PR merge SHA / benchmark `EVIDENCE_HEAD`: `433937e49c08106210e78957e0ce056f4f6af19a`
- workflow: `33992721970`
- job: `101377693939`
- artifact: `9977123811`
- artifact SHA-256: `4a6f69fdaf1b6c251e6becd17a9cd249a25df60ce79138e653acf5d0d5afe244`
- tests: **93 passed**
- semantic gate: pass
- formal decision: `retire_growable_direct_canonical_emitter`

The broad result reproduced strongly:

- productive median: **0.432190x**;
- productive rows <=0.95x: **20/21**;
- productive size medians: **0.417–0.458x**;
- control size medians: **0.566–0.625x**;
- 256 KiB quarter-damage: **0.419266x**;
- 256 KiB fragmented/96: **0.399695x**;
- 256 KiB controls: **0.619334x / 0.630834x**.

But the same single 256 KiB exact-shift row failed again, now even more strongly:

- baseline: **41,892 ns**;
- candidate: **127,428 ns**;
- candidate / baseline: **3.041822x**.

The unchanged broad gate therefore remains failed. The dense size diagnostic and the mixed-envelope parent gate disagree on the same exact-shift size despite identical implementation/semantic bytes. This is now repeatable evidence of **benchmark-context / runtime-state sensitivity**, not evidence for a simple size threshold.

## Hostile-review classification

Do not promote this Python emitter and do not erase the 256 KiB row. Do not add a `size != 256 KiB`, workload-name, node-count or other corpus-derived dispatch to make the matrix green.

The useful mechanism-level fact survives: eliminating helper-produced temporary uvarint/ref/node bytearrays while keeping one growable output buffer gives large gains over almost the entire frozen envelope. The unstable row shows that CPython allocation/timing context can dominate a very small three-node Program and makes this research implementation unsuitable as stable product-speed authority.

The repository native frontier is still the r24/r25 product reader/portable layer; ONE does not yet have a canonical native product writer. Therefore spending many more activations micro-tuning CPython allocator behavior has low marginal product value.

## Decision

**`hold_python_growable_emitter_context_instability`**.

Preserve `growable_wire.py` as research evidence/reference, but do not promote it into the canonical ONE writer yet. The next product-relevant use of this mechanism should be transferred into the future native/shared ONE canonical-emission boundary, where direct writes into an owned output buffer can be measured without CPython temporary-object/allocation behavior.

At most one future Python experiment is justified before that transition: a cheap preregistered context/order falsifier that can directly distinguish heap/order history from runner noise. Do not continue a sequence of threshold or allocator micro-tunings.

## Claim boundary

This classification changes no ONE wire bytes, operations, validation contract, reader semantics, product writer, version or comparator authority. Frozen v0.29 and deferred v0.30 remain untouched.