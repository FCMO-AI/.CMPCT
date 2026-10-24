# CMPCT v0.31 — Independent revision-24 S_PACK fixed-byte conformance court

Date: 2026-10-24
Status: **prospective; no product, format or release authority**.
Base: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`.
Ownership: independent fixed-byte conformance only; PR #258 owns physical PACK SHA verification, PR #257 owns its scientific falsifier, PR #270 owns Reader composition. Do not edit those owners or their code.

## Falsifiable primary question
Can the actual Python Reader and the native r24 archive ABI read identical S_PACK content and selective byte ranges from **independently authored immutable physical CMPCT archives**, without relying on a Builder-produced pack corpus or a shared parser/encoder bug?

Prediction: two exact revision-24 physical archives (one RAW physical pack blob, one Zstd physical pack blob) built with only documented magic/structs, MessagePack and system libzstd—not CMPCT Builder—preserve three different logical file slices sharing one blob, including a nonzero-offset slice, a boundary-crossing range, and a duplicate-slice alias. Complete reads, slices, index preflight and native reads must match independent stored digests. Re-opening original fixed archive bytes must not require re-encoding.

## Controls / alternatives
- Current `tests/native_pack_abi.py` Builder-derived native test is the simpler product regression control, but cannot supply encoder-independent provenance.
- Existing independently frozen chunk/sparse/VZIP vectors do **not** exercise S_PACK. Neither validates this gap by proxy.
- Random synthetic packet-only test is cheaper but shares a parser-side assumption and cannot hold a stable cross-implementation byte oracle.
- Selected route: construct and freeze raw base64 archives in `tests/conformance/v24-pack.json`, record full archive SHA and logical/range identities, and add one Python installed-product court plus optional explicit native ABI court.
- Add corrupted authenticated metadata/framing adversarial cases without rewriting the official vectors; refusal must not depend on relaxing verifier criteria.

## Kill/narrow conditions
Reject the proposed vector if either physical archive fails independent offline structural decoding or authentic installed Reader, if its on-disk records differ from revision-24 encoder grammar, if the native core gives a different answer, if an invalid packed slice is accepted, or if byte/range SHA does not match. Any currently unsupported platform is **UNMEASURED**, not green. Do not change the binary format to make the vector pass.

## Cost and source truth
Tiny permanent vector payload (expected < 4 KiB total) and a short reader/native gate; no archive encoder changes, no mandatory third-party runtime dependency, no changed release/performance comparator. Fixture creation uses Python stdlib struct/hashlib and installed msgpack/system libzstd via ctypes, outside the CMPCT Builder. The fixed byte identity and generator source will be independently checked, then immutable.

## Decision
If accepted, this promotes evidence coverage—not a runtime win or release—and closes the inherited independently-authored PACK conformance gap. If falsified, preserve the offending archive, actual Reader behavior, and the narrowest reason. Always report exact-head CI status and do not infer a native pass from Python green.
