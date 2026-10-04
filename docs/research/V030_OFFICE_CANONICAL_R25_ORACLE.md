# v0.30 Office canonical-r25 oracle — exact negative

Status: **research/oracle evidence only; zero release credit**.

## Source / substrate

- Evidence source commit: `feff1477eecd15bb0fb4640abe12172997c0c3a2`.
- GitHub Actions run: `35306247190`, job `office-canonical-r25`.
- Frozen substrate: `neutral-hostile-determinism-repair-v6`.
- Office tree: `aac7de772b9fae0f9791a8f2884cebb29a2ba85df9e4db21ea78482afb378a57`.
- 20 files, 16,063,798 logical bytes.
- The run bound checkout to the exact PR head, strong-verified the emitted archive, checked semantic tree identity, measured per-member decoded-context amplification, and uploaded the JSON receipt.

## Direct result

The canonical-r25-only candidate set selected `geometry-g04`:

- canonical r25 archive: **11,633,031 B**;
- canonical-r25 build wall inside the oracle: **76.2873 s**;
- worst member decoded-context amplification: **1.0x**;
- strong verification: **PASS**;
- semantic tree identity: **PASS**;
- current same-tree inner v0.29 floor: **5,954,336 B**, selected as `v029-fallback`;
- current shipping-r24 control: **15,445,236 B**;
- Zstd-19 control: **8,312,879 B**;
- 7z control: **7,455,748 B**.

Deltas:

- saves **3,812,205 B** versus current shipping r24;
- regresses **5,678,695 B** versus the current same-tree v0.29 floor;
- loses **3,320,152 B** to Zstd-19;
- loses **4,177,283 B** to 7z.

Terminal oracle decision: `CANONICAL_R25_ESCAPE_INSUFFICIENT`.

## What this falsifies

The Office loss is **not** currently explained by a simple two-level selector bug hiding an already-good canonical r25 contender. On the accepted repair-v6 Office identity, the legal canonical-r25 portfolio is much larger than both the inherited v0.29 floor and the external solid-codec controls. Wiring the existing canonical-r25-only tournament directly into shipping would therefore violate the inherited byte floor and still lose to Zstd-19/7z.

The earlier ~7.61 MB PrefixGraph observation must not be substituted for this result without proving identical source/substrate/profile semantics. The accepted repair-v6 exact-head oracle selected G04 at 11.63 MB.

## Mechanism implication

Office remains a high-value representation problem. The neutral corpus intentionally contains DOCX/PPTX/XLSX families with independently zipped packages and shared assets/boilerplate. The older v0.25 family explicitly discovers profitable cross-container ZIP-stream graphs. The next decisive question is therefore whether that compact ~5.95 MB family survives the modern locality/integrity/product contract on the accepted repair-v6 tree, and, if so, how to carry its generic container-member graph semantics into a bounded canonical profile without importing research-only reader debt.

Do **not** productize the 11.63 MB canonical-r25 candidate as an Office fix. Do **not** weaken the v0.29 zero-regression floor. Preserve this negative and move to the compact-floor legality/materialization falsifier.
