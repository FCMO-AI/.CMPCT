# Office v0.25 ZIP-stream causal ablation — accepted research evidence

**Status:** completed research-only causal evidence; no release credit by itself.

## Exact evidence

- Workflow: `CMPCT v0.30 Office v0.25 ZIP-stream ablation`
- Run: `35332507781`
- Evidence source: `55b7e66f8afa6c23a91f457063a420b4d061dc6a`
- Artifact: `10542321093`
- Artifact upload digest: `sha256:5734c8d0870cf9f2f9522d7630cce2764025719cdfc3cd7e1d637885c8eeddb8`
- Substrate: accepted `neutral-hostile-determinism-repair-v6` Office tree
- Tree SHA-256: `aac7de772b9fae0f9791a8f2884cebb29a2ba85df9e4db21ea78482afb378a57`
- Files: `20`
- Logical bytes: `16,063,798`
- Receipt schema: `cmpct-v030-office-v025-zipstreams-ablation-v1`
- Decision emitted by the instrument: `ZIPSTREAMS_CAUSALLY_MATERIAL`
- Both control and ablated archives passed strong exact-tree verification on the same tree.

## Direct measurements

| Variant | Complete archive bytes | Create CPU seconds | Packs | Derived | Special | Stream pool bytes | Stream slabs | Hot stream slabs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v0.25 control | 5,954,026 | 0.464764575 | 21 | 8 | 5 | 3,791,492 | 12 | 10 |
| v0.25 with ZIP-stream admission disabled | 15,308,746 | 1.318202476 | 38 | 0 | 0 | 0 | 0 | 0 |

Disabling only v0.25 ZIP-stream admission increased the complete archive by **9,354,720 bytes**. The ablated artifact is about **2.571x** the control size; equivalently the lost ZIP-stream mechanism value is **157.116% of the control artifact size**. Create CPU also rose by about **2.836x** (`1.3182 / 0.4648`), so on this exact Office tree the mechanism is not trading size for extra creator work: it is simultaneously avoiding substantial bytes and work.

## Cross-evidence: locality is not the explanation

The accepted earlier compact-floor locality falsifier on this same repair-v6 Office identity (`4082c08f4d98f3e4bd8af4becf9e0ceb38eb4762`, run `35306897195`, artifact `10531781945`) measured the same **5,954,026 B** v0.25-style artifact with exact-tree verification and found:

- maximum selected-member physical amplification **4.001128526645768x**;
- weighted member amplification **1.0258147543936995x**;
- members over the current `<=8x` law: **0**.

Therefore the old compact floor is not merely buying its size by violating the current selected-member locality ceiling. Combined with this ablation, the evidence is stronger: ZIP-stream representation owns material Office bytes, and the resulting compact-floor artifact already survived the existing locality falsifier on this tree. That still does not make the old grammar a product candidate.

## What this proves

The large inherited v0.25 Office advantage is causally dominated by the ZIP-stream representation family on this accepted Office substrate. This is not a small threshold effect: removing that family destroys 9.35 MB of complete-artifact value, eliminates all 8 derived objects and all stream slabs, and expands the pack count from 21 to 38 while preserving exact reconstruction.

The result therefore changes the next question. The useful frontier is no longer “does ZIP-stream virtualization matter?” It does, decisively on this tree. The useful question is why the current canonical r25 product cannot retain enough of this value while satisfying the rest of its bounded product semantics.

## Claim boundary / strongest negative

This is **research/oracle evidence**, not a release result. It does not prove that the exact current canonical r25 product can legally carry the same representation, does not prove transfer outside the accepted Office tree, and does not price r25 filesystem framing, generic admission, native-reader/recovery parity, hostile-input safety, current runtime, or maintenance cost. The v0.25 control itself is not the release candidate.

The ablation disables the ZIP-stream admission family as a whole. It therefore establishes family-level causal ownership, but it does not yet separate which subcomponent supplies the 9.35 MB: local duplicate compressed members, cross-container shared compressed streams, exact matches to loose assets, representation inversion, or downstream interactions enabled by stream virtualization.

## Next highest-leverage executable target

Do **not** repeat broad Office mechanism search or continue treating the ZIP-stream ablation as pending. Build the smallest charged r25-compatible rehabilitation experiment that preserves the current product contract while selectively reintroducing the proven stream-virtualization value.

The first instrument should separate remaining semantic taxes from representation value: price the proven v0.25 stream family behind current r25 filesystem framing, then decompose the admitted ZIP-stream value into decoder-carrying subcomponents. Charge stored bytes, metadata, exact reconstruction, largest-member physical/logical read amplification, decoded context, creator/extractor work, recovery/native-reader burden, and generic admission. Prefer the smallest submechanism with the largest charged recoverable value. A candidate dies or narrows if its fully charged r25-compatible artifact cannot beat the current r25 Office floor without violating exact filesystem semantics or the inherited `<=8x` selective-read law.

This evidence supersedes any coordination text that still says the ZIP-stream ablation itself is awaiting execution. Preserve the older text as chronology; do not rewrite the run or its measurements.