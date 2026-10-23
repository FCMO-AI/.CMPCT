# CMPCT v0.31 — O4 verifier-fed wire identity vs mutable-source copy (preregistration)

Date: 2026-10-23
Status: **PREDICTION FROZEN BEFORE O4 CODE AND RESULTS**.
Starting research HEAD: `7c072494ea923d3f27deb83c3775a211cc24898f`. Production parent: PR #284 original Reader blob `b0c8eb5eddd5591524b3e9c9a640d9266ccbbbdb`. No product source edits authorized here.
Episode: `v031-direct-deflate-verifier-fed-wire-sha-o4`.
Scientific tier: bounded byte-custody mechanism oracle, below full product integration.

## Fork opened by O2 and O3

O2 proved a live source can mutate after the parent's logically correct preflight and be copied into a successful but invalid ZIP. O3 independently demonstrated a valid stage-and-verify-before-publish architecture, but requires an extra logical inflate/SHA pass **per exported member** after copy; an alias-heavy/high-ratio archive could export major CPU.

New question: can we bind **the exact compressed bytes consumed during an already-required logical SHA/CRC/inflate proof** to the exact compressed bytes emitted, by using a SHA-256 wire digest on each set of immutable bytes, without inflating each later alias?

## Predictions

1. Single-pass bounded verifier feeds the same immutable <=64KiB compressed chunk to both SHA256(wire) and its raw-Deflate inflater, validating original logical CRC32/SHA-256/size against the original revision-24 blob header. If source is corrupt *before* validation, it rejects.
2. Direct emitter copies <=256B chunks to private staging and hashes **the exact Python bytes object it writes**. For immutable input, wire SHA matches preflight, raw Deflate identity and exact logical decompression hold.
3. If another writable file handle mutates the live source **after successful validation, before the first copied byte**, copied wire SHA differs and the stage is not published; pre-existing user target remains intact.
4. If the source changes **during the chunked copy**, specifically at a future byte after the first chunk, copied wire SHA differs and stage is not published.
5. If the source changes after validation and is restored to its original bytes before the copy completes, the copy is rejected when it saw altered bytes; a simple final-state source checksum could miss this event. Record both copied and final source digests.

Disproof: any mismatched copied byte reaching public target; false acceptance of corrupt source; valid immutable stream rejected; wire digest calculated by re-reading source in a separate post-validation epoch; incomplete chunk coverage; unbounded allocation per input size. Keep all negative results, not only positive controls.

## Alternatives and exported costs

- O3 postcopy logical verification: stronger simplest full-output control already proven, but repeats inflate/hash per exported member and rereads ZIP.
- Wire SHA bound during original verification: avoids re-inflation per copy; adds SHA-256(compressed bytes) during unique-blob verify and copy. Cost: compressed-size SHA pass on each alias; stage requires output-sized disk and private temp ownership. Cryptographic collision assumptions remain.
- Recompute wire SHA from source after original preflight: **rejected a priori**, same TOCTOU.
- Copy entire compressed member to immutable bytes: avoid time gap but exports compressed-sized RSS; reject as general unbounded solution.
- File metadata timestamps: not a completeness guarantee.

Implementation is a detached research proof on a fully authentic r24 source for logical commitments but emits **raw Deflate staged bytes**, not a complete ZIP. O3 already covers real ZIP stage/publish. Therefore O4 does not earn full ZIP product credit. Test on Linux Python 3.11 with explicitly reversible in-place mutation; check source mmap visibility. No code outside `benchmarks/` or a focused workflow; no changes to source production owner, publication gates, format, tests, release version, or shared discovery state.

The practical next step if O4 succeeds is an owner trade study: add wire digest to the genuine preflight's input loop, retain it for each physical blob, wire-hash exact buffered bytes while emitting ZIP, reject before atomic rename, and prove the entire ZIP output/metadata/reader behavior with complete cost and hostile cross-platform tests.
