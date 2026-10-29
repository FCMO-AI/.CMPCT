# J24I34 preregistration — native complete verification must authenticate symlink payloads

**Frozen before product edits, 2026-10-29 UTC.** Candidate product change on isolated branch stacked from [J24I30 #754](https://github.com/FCMO-AI/.CMPCT/pull/754) exact `0c99eca3890b7fb4a7625d9f11152fac5cf34a61`. Baseline native `vzip_dispatch.rs` blob `60e53b1e85c30d413e379052bb288ed3b51ec30d`; `lib.rs` blob `463c50633be74423e92a074b7d7577db6a4b0cf9`. Released `main@80c358f8824ec1b20d349c92ed94c898090969b0` v0.30.0/r24 is unchanged. Issue #755 is the native verification owner; #751 owns hardlink alias SHA.

## Baseline and causal mechanism

The frozen J24I30b [installed Ubuntu + macOS court #40862020614](https://github.com/FCMO-AI/.CMPCT/actions/runs/40862020614) definitively found native `Archive::verify_complete` checks **zero** members in a one-symlink archive, accepting both rehashed contradictory present 32-byte logical SHA and a physically corrupted RAW symlink payload, whereas installed Python `CMPCT.verify` rejects both. Code path: `vzip_dispatch.rs` `if entry.kind != 0 { continue; }` skips `kind=2`. `complete_member_identity`, `checked_blob_layout` and `read_range` already support direct payloads without extracting to a filesystem.

**Prediction:** including symlink-kind entries in the existing bounded full-member hash-verification loop (not a parallel verifier) makes genuine and correct-present revision-24 symlinks return `Ok(1)` and makes contradictory-present/physical-corrupt variants return `MemberHash`, while regular-file exact conformance stays unchanged. A present zero-length optional digest still fails native `Archive::open`, preserving the independently observed #755 admission discrepancy, not silently expanding grammar.

**Kill/narrow:** any false acceptance of bad symlink bytes or contradictory logical SHA; failure to open genuine symlink; regression in valid regular file, directory, hardlink/alias, direct-compressed/virtual paths; increased peak buffer cap; arbitrary materialization or directory traversal; weakening historical J24I30 research testimony. If the real native kernel cannot reuse the same range/hash machinery for links, stop and consider separate bounded proof; do not waive coverage.

## Strong controls and alternatives

- **Old unchanged source:** J24I30 is the frozen scientific red (do not edit its expected-negative Rust test or original artifacts).
- **New product court:** reuse J24I30 generator to produce four admissible authentic/re-signed/corrupted symlink files, plus the known empty-SHA parser refusal as a *separate unresolved negative*. Execute the actual compiled native `Archive` on Ubuntu and macOS. Make the test explicitly ignored in ordinary Cargo and explicitly run by dedicated CI. Require `verify_complete` to reject corrupt/contradictory cases; green means fixed behavior, unlike J24I30 scientific court.
- **Simpler control:** continue using existing `complete_member_identity` and `read_range`; a separate symlink decoder introduces duplicate code, new attack surface and incompatible resource budgets.
- **Independent referee:** reuse J24I30 detached physical auditor to certify both indexes, frame, CRC, SHA and expected corruption. Do not turn invalid archives into a release claim.

## Whole-system and promotion debt

The additional work is proportional to symlink payload bytes; the verifier already allocates a single reusable bounded buffer up to `VERIFY_CHUNK_BYTES=8 MiB`, hashes each member once, and does not materialize a filesystem. For archives without symlinks, the loop remains behaviorally identical. CPU/read bytes of symlinks increase from **zero to full symlink target length** in complete verification, necessary to support the semantic claim; full create/extract/RSS/portability performance and adversarial path races are not established and still block release credit. Native parser parity for optional `b''`, hardlinks, journal recovery, Windows and all native ABI consumers remain separate owners/debt.

## Scientific taxonomy

J24I30 is decisive negative product evidence. J24I34 tests a candidate implementation repair using independent installed evidence. If fixed, do not rewrite J24I30 expectations; retain the frozen original source and invert only a new product test. The cheapest disproof is a genuine signed-index contradictory digest that the repaired native API still accepts. No format/release/policy/Discovery STATE/frozen benchmark edits.
