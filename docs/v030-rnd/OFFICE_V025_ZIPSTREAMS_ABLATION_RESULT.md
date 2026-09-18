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

## What this proves

The large inherited v0.25 Office advantage is causally dominated by the ZIP-stream representation family on this accepted Office substrate. This is not a small threshold effect: removing that family destroys 9.35 MB of complete-artifact value, eliminates all 8 derived objects and all stream slabs, and expands the pack count from 21 to 38 while preserving exact reconstruction.

The result therefore changes the next question. The useful frontier is no longer “does ZIP-stream virtualization matter?” It does, decisively on this tree. The useful question is why the current canonical r25 product cannot retain enough of this value while satisfying its bounded selective-read / locality / product semantics.

## Claim boundary / strongest negative

This is **research/oracle evidence**, not a release result. It does not prove that the exact current canonical r25 product can legally carry the same representation, does not prove transfer outside the accepted Office tree, and does not price r25 filesystem framing, generic admission, selective-read amplification, current runtime, or maintenance cost. The v0.25 control itself is not the release candidate.

The ablation disables the ZIP-stream admission family as a whole. It therefore establishes family-level causal ownership, but it does not yet separate which subcomponent supplies the 9.35 MB: local duplicate compressed members, cross-container shared compressed streams, exact matches to loose assets, representation inversion, or downstream interactions enabled by stream virtualization.

## Next highest-leverage executable target

Do **not** repeat broad Office mechanism search or continue treating the ZIP-stream ablation as pending. Build the smallest charged r25-compatible rehabilitation experiment that preserves the current product contract while selectively reintroducing the proven stream-virtualization value.

The first instrument should decompose the v0.25 control's admitted ZIP-stream value into decoder-carrying subcomponents and price each against the current r25 constraints: stored bytes, metadata, exact reconstruction, largest-member physical/logical read amplification, decoded context, and creator/extractor work. Prefer the smallest submechanism with the largest charged recoverable value. A candidate dies or narrows if its fully charged r25-compatible artifact cannot beat the current r25 Office floor without violating the inherited `<=8x` selective-read law or exact filesystem semantics.

This evidence supersedes any coordination text that still says the ZIP-stream ablation itself is awaiting execution. Preserve the older text as chronology; do not rewrite the run or its measurements.