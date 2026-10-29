# J24G43 — native and Python strong-verify accept an undecodable compressed empty physical record

**Evidence boundary:** 2026-10-29 UTC; read exact source before any promotion. This is a **NEGATIVE PRODUCT-INTEGRITY RESULT**, proved in an unmerged research/test branch, not a product repair or release.

## Prediction, contradiction and method
Original immutable [preregistration](2026-10-29-j24g43-zero-compressed-verify-prereg.md) at `632c237b9e5e0b7602e0a7d31b9312f674e92012` predicted compiled native would skip zero-logical-byte encoded Zstd frames while Python `CMPCT.verify` would reject. Initial exact-head [Actions #40882402234](https://github.com/FCMO-AI/.CMPCT/actions/runs/40882402234) at `c01c5b3a7c3b986f07afb0d1b1e6cfcabcdc4e28` **failed in Ubuntu and macOS**: Python unexpectedly *also accepted* malformed encoded input, `verify()==1`. The independent source-derived root cause and **chronological prospective clarification** are frozen in [J24G43a addendum](2026-10-29-j24g43a-python-zero-decode-negative-addendum.md), committed `d0fb313557a8f23b10b3489418f3b9631174a6ee` before changing instrument expectations. The original prediction was not silently edited or declared correct.

## Exact hosted proof after transparent instrument adjustment
The two-host source-exact [Actions #40882912289](https://github.com/FCMO-AI/.CMPCT/actions/runs/40882912289) at `92627f9861d2cb6e7e41392c752928cbc33a3e6e`: **Ubuntu 24.04 SUCCESS, macOS 14 SUCCESS**. Specialized SUCCESS means it reproduced the **negative acceptance**.

Every host produced exactly the same original bytes:
- Authentic Builder source, one empty regular file: **856 B**, SHA-256 `cd7f9a85dd380f6da8c6e3b9c13dce4981e0cf8f92bfdc08ed96908c1bbbe008`. Python and native each verified 1.
- Independently derived fully signed-valid r24 direct Zstd-compressed empty file: **875 B**, SHA-256 `2fc6b8f12941b0257e071e0187f8923303a279d4a21a0b1716642dc67e0e75bc`. Independent Zstd decoded zero bytes; Python and native each verified 1.
- Same valid frame with **one byte XOR 1** at physical payload offset **465** (its Zstd frame magic), SHA-256 `bc5a8e7b2e4af9bc16b67bfe90f24da94ea44d5f0ea2e21d3a37dc76850e381c`: independent Zstd decoder rejects; the physical CMA4 header SHA-256(empty), CRC32=0, both authenticated indexes, footer, declared sizes, file row and codec remain **unchanged**. **Python `CMPCT.verify()==1`; compiled Rust `Archive::verify_complete()==Ok(1)`.**

The detached `research/j24g43/audit_zero_encoded_payload.py` imports no CMPCT code, parses authentic r24 wire, validates MessagePack/Zstd index, two identical compressed index copies, SHA-256/CRC32 and footer, asserts the exact one-byte physical mutation, and independently proves the corrupted frame is **undecodable**. Its audit passed on both hosts.

Original first successful evidence artifacts:
- [Ubuntu raw archive/receipt #12901237458](https://github.com/FCMO-AI/.CMPCT/actions/runs/40882912289/artifacts/12901237458).
- [macOS raw archive/receipt #12900728475](https://github.com/FCMO-AI/.CMPCT/actions/runs/40882912289/artifacts/12900728475).

A separately executed command-line Zstd decoder on Linux also rejected a one-byte corrupted authentic 13-byte empty frame, but that independent lower-rung check **does not** earn product credit or replace the hosted real r24 verifier.

## Causal mechanism / published Python reach
- Exact `main` `src/cmpct/native_codec.py` Git blob `c928e69e1513fa1f7898e4016cbccd8bda3dfbec` is **identical** to the unmerged candidate: `decompress(data,usize)` returns `b''` immediately when `usize==0`, even for nonempty undecodable `data`. The dictionary one-shot/cached decoders contain corresponding early exits (not physically tested here).
- The complete `_blob()` method in the published Reader Git blob `e716233403dabd0966863c45635e18fa5ac6afb8` is **byte-identical** to the candidate's `_blob()` in Reader blob `29ffd0e94b7baa82bfded6f060c88a4fd44c19f8`. It calls `zd(comp,rus)`, then verifies empty decoded bytes against CRC(empty), but the codec never inspected the compressed frame.
- The unmerged Rust #759 native `verify_complete()` reads through `while offset < entry.size`. At zero logical size it never runs the decoder. `complete_member_identity()` checks indexes, header and decoded SHA(empty), not physical encoded Zstd frame validity.

This is **strong evidence of a shared logic bug in published Python and an unmerged native repair**, but the hosted compiled binary was built at the candidate source, **not as a separate published-release build**. The output logical bytes remain the correct empty stream. There is **no defeat of SHA-256, no demonstrated data loss, no key-authentication claim and no remote exploit demonstrated**. This is a malformed physical-encoding acceptance in explicit strong verification of an adversarial r24 record.

## Controls, tradeoffs, negative and uncertainty
A genuine original and a valid Zstd-empty derived control both pass. Only one encoded byte changes between valid and corrupt cases; the independent decoder rejects invalid magic; two different host OSes observe identical wire SHA. Frozen historical archives are not rewritten. The originally anticipated Python rejection **failed** and must remain recorded.

This case is synthetically re-encoded, not a Builder-emitted compressed empty frame: current Builder normally stores empty content as direct RAW (zero encoded bytes). Do not infer frequency in ordinary workloads or arbitrary codec exposure. A proper fix must inspect a nonempty compressed physical payload even when the decoded size is zero, while continuing to accept historical valid RAW empty records and any legitimately valid Zstd-empty frame under unchanged r24 grammar. A stronger global mechanism could require CRC and exact compressed stream validity in one bounded pass, but CRC of decoded empty bytes alone cannot detect a malformed compressed frame. Full end-to-end overhead, recovery, selective reads, ZIP export, Windows, other codecs, native ABI and all-archive integrity are **unmeasured**.

## Decision / coordination / next action
Primary scientific question **resolved negatively**: both installed Python and native complete verification accept a declared zero-logical-size Zstd member with invalid encoded payload, whereas independent Zstd rejects it. This changes the product correctness backlog; notify native #759/#755, Python direct-SHA #750 and CRC research #762, but avoid duplicating their implementation branches. Next cheapest unclaimed executable: existing owners implement a narrowly scoped fail-closed full-frame check for empty compressed members and run original exact hostile and historical controls plus nonempty codec cases. Consider codecs with zero-size early exits after owner decision.

No change to `main`, product source, frozen comparators, release conditions, format revision, version, Discovery policy or `docs/discovery/STATE.json`. Discovery Engine selected a low-cost falsifier and yielded a decision, **not** a new generalized policy lesson. No conflict with existing mutation owner; this is an explicitly independent replication/falsification lane. Release credit **0**.
