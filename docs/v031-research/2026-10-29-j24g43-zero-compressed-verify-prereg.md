# J24G43 — zero-logical-size compressed direct-member verification: prospective falsifier

Date: 2026-10-29 UTC. Status: **PREREGISTERED BEFORE INSTRUMENT AND OBSERVATION**. Independent research / no product modification.

## Exact baseline and authority

Published `main@80c358f8824ec1b20d349c92ed94c898090969b0` remains v0.30.0 / revision 24. The experiment is based on #759 HEAD `e67ed337e78e021ba91f7bc6bdc271ae0ddd6b51` and **unchanged** native `vzip_dispatch.rs`, which hashes a stream only in `while offset < entry.size`. The direct-member identity procedure compares authenticated index/header sizes and SHA but never reads compressed payload for logical size zero. This is a different skip condition from #762's physical CRC-field mismatch: corruption here targets **actual encoded compressed bytes**, not a CRC-only field. Check current PR/issue claims before developing this question; no duplicate implementation is intended.

## Locked primary question and prediction

Starting with a real one-file empty-regular-member revision-24 archive built by the installed first-party Builder, construct a derived, structurally self-consistent and authenticated-index **Zstd-compressed empty logical member**: physical CMA4 codec=Zstd, usize=0, csize=actual valid Zstd empty-frame length, CRC32=0, SHA256=SHA256(empty); update the indexed blob tuple, *both* compressed index copies and footer. Positive control is a valid encoded empty Zstd frame.

Change exactly one byte **inside the Zstd frame** while keeping the signed index, physical CMA4 header, declared sizes and logical SHA untouched. Predict:

1. Python `CMPCT.verify()` accepts the positive derived frame and rejects the corrupted frame during physical decode, or the question must be narrowed if that oracle does not reject.
2. Compiled native `Archive::verify_complete()` accepts **both** positive and corrupted zero-length members as `Ok(1)` without reading encoded bytes; this is a **negative integrity result** for the native candidate, not a product success.
3. A nonempty Zstd control with one-byte payload corruption is rejected by native; otherwise the instrument is not discriminating.
4. Independent physical wire referee confirms both primary/tail index SHA, footer, header/index agreement, expected empty SHA/CRC and exact mutated payload byte; corruption must be detected as an invalid Zstd frame by an external decoder.

## Strongest alternatives and kill criteria

If native `verify_complete` rejects the derived corrupted frame, the predicted skip is falsified (possibly earlier validation). If the valid empty Zstd frame fails Python or native, classify the derived archive as unsuitable rather than inventing a product bug. If the corrupted frame still decodes to empty, choose a guaranteed invalid magic byte mutation *before* execution. No product release credit for this research. An unkeyed SHA is not provenance/authenticity. Invalid codec metadata, CRC-only mismatch and S_PACK composite semantics are outside this test.

## Cost and next decision

Cheapest rung: source derivation and exact hosted genuine-to-derived oracle, then compiled native court on Ubuntu; optionally macOS. A zero-size fixed logical payload makes current implementation perform zero physical read/decoder work, rather than SHA work over the encoded Zstd bytes; a repair needs to decide whether every empty compressed physical record must be decoded at least once during strong verify. Account for codec start-up cost and bounded metadata/physical reads if promoted. Reuse existing #759/#762 native owner; this research-only branch changes no product code, format, frozen suite, gate, release or Discovery STATE.

## Explicit promotion boundary

Even a positive falsifier is only a narrow native strong-verification inconsistency. It cannot establish arbitrary payload loss, exploitability, a general codec defect, performance impact or release readiness. The next owner action, if positive, is a bounded empty-compressed-source admission/verification fix plus independent nonempty/empty/historical cross-codec controls.