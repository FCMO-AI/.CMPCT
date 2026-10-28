# v0.30 implicit-v4 hardlink metadata parity mission lock — 2026-09-13

Status: **frozen D5/native semantic-parity falsifier; no release credit until independently executed**.

## Trigger

The canonical Python implicit-v4 decoder treats hardlink metadata as inode-owned state. When an explicit hardlink row resolves to a regular owner, Python reconstructs the hardlink metadata and rejects the control if that metadata differs from the owner's metadata.

The portable Rust manifest parser currently resolves hardlinks to a regular owner but, by direct source inspection, does not visibly perform the same owner-metadata equality check in `FsManifest::from_entries`.

Source inspection is not sufficient evidence of a product defect. This lock therefore freezes one independent cross-language falsifier before any Rust fix is allowed to claim parity.

## Hypothesis

`H-IV4-HL-META`: the current portable Rust implicit-v4 parser accepts an authenticated hardlink control whose inode-owned metadata diverges from its regular owner, while the canonical Python reference rejects the same semantic state.

If the Rust parser already rejects the divergent control for the same invariant, the hypothesis is falsified and no fix is justified.

## Frozen test

Use the already-committed independent Python-generated implicit-v4 vector in `native/cmpct-portable/src/implicit_v4_vector_tests.rs` and mutate only the hardlink row's metadata override:

- keep version, default metadata, regular-owner index, path encoding, authenticated regular-file identities, and every other explicit row unchanged;
- replace the hardlink's empty metadata override `[0]` with `[MODE, +1]`, making only its mode diverge from the owner;
- keep the same authenticated owner index.

Call the Rust `FsManifest::parse_with_identities` path used by the native reader.

## Frozen adjudication

### `NATIVE_HARDLINK_METADATA_PARITY_PRESENT`

If the current Rust parser rejects the mutated control specifically because hardlink metadata does not match owner metadata. No source fix is warranted from this hypothesis.

### `NATIVE_HARDLINK_METADATA_PARITY_DEFECT`

If the current Rust parser accepts the mutated control and reconstructs the divergent hardlink. This is a real semantic-parity defect because the canonical Python reference rejects that state.

### `NATIVE_HARDLINK_METADATA_PARITY_INCONCLUSIVE`

If the test cannot execute, the vector/provenance is invalid, or the parser rejects for an unrelated malformed-control reason that does not establish the inode-metadata invariant.

Do not call CI infrastructure failure a parser result.

## Fix boundary if defect is confirmed

The smallest acceptable repair is shared manifest validation, not an implicit-v4-only special case:

1. make filesystem metadata structurally comparable in Rust;
2. after resolving a hardlink to its regular owner in `FsManifest::from_entries`, reject if hardlink metadata differs from owner metadata;
3. use an error message identifying the hardlink/owner metadata invariant;
4. preserve all previously valid implicit-v4 and legacy filesystem-v1 vectors;
5. rerun the independent positive implicit-v4 vector, the new hostile divergence vector, native tests, and the existing Python/native reader bridge gates.

Shared validation is preferred because inode-owned hardlink metadata is a filesystem semantic invariant independent of which control encoding produced the entries.

## Promotion boundary

A green targeted test after the fix is necessary but not sufficient for release/native parity. Exact-head native CI and applicable reader/bridge/conformance gates must also remain green. This change must not alter archive bytes, reader grammar accepted for valid archives, format revision, compression policy, locality, recovery, or performance claims.