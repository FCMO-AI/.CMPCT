# J24K07b — held-out canonical Deflate mode0 signed suffix-coordinate court

Date: 2026-10-28 UTC. **Prospective independent third-representation discriminator.** Prior J24K07 STORED/mode1 result is frozen at experimental source `8b61002505c6567ecae5d2b02bac6af178a88379` and 3-host [run #40635350564](https://github.com/FCMO-AI/.CMPCT/actions/runs/40635350564); this extension does not rewrite those predictions, tests or receipts. No product, frozen fixture, format, version or evaluator changes.

## New question
Does the same signed skipped-payload offset issue occur with **canonical Deflate mode0**, where `reader._stream(0)` provides raw compressed bytes from a physical CODEC_DEFLATE blob rather than retained mode1 or STORED? It is the remaining representation branch of the three non-mode2 payload mechanisms.

## Prospective prediction and kill
Using immutable Builder-independent `tests/conformance/v24-virtual-zip-deflate-mode0.json` at Git blob `663b9fdb4df560fb9572fa14bf003928a2379e5e` and unchanged artifact SHA `9fa44e064af01a2fdc7402881bb89d9449cbc5de6a26563d05f71b812af0c224` (known 130 B, payload csize 14, literal sizes 39+77), change ONLY recipe compressed-size by +1/-1 and matching file/recipe total, recompute primary/tail compressed index SHA, retain physical content bytes, and execute current exact installed Reader. Predict at least one **correct-length but wrong-byte** suffix among all one-byte positions after the skipped payload within the common valid positional overlap, with strict preflight/full read/verify rejecting. Both +/-1 must succeed on all three hosts to claim supported third-branch transfer. The opposite result is a valid negative: preserve it without modifying the oracle or archive.

## Cheaper controls and alternatives
The existing source conditional says non-mode2 skipped streams advance `outpos += csize` with no physical proof, but code inspection alone does not demonstrate ordinary Reader behavior for canonical compressed blob owner. A pure mathematical offset model would underprove actual Reader behavior. Reuse the already present J24K07 Builder-independent archive mutator and its test mechanism, without creating product changes, broadening the corpus or adding a second CI fanout. Stronger control: `validation._validate_recipe` already validates canonical mode0 csize against blobs[stream_ref][2] and codec CODEC_DEFLATE; ordinary Reader does not invoke that recipe validator.

## Disposition
If observed, the same bounded metadata proof covers STORED, retained mode1 and canonical mode0; avoid per-suffix decompression for these modes. If unobserved, narrow J24K07 to STORED+retained and scrutinize canonical mode0's different stream mechanics. Do not credit a repaired Reader or general security claim, and never promote without full integration/size/create/extract/RSS proofs. No change to Discovery STATE owned by #574. Source SHA/CI and raw receipts must bind to the new exact final head.
