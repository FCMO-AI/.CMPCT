# v0.30 implicit-v4 hardlink metadata parity result — 2026-09-13

Status: **confirmed native semantic defect repaired; D5 evidence only; no performance, release, or version credit.**

Authority chain:

- preregistration: `docs/V030_IMPLICIT_V4_HARDLINK_METADATA_PARITY_MISSION_LOCK_2026-09-13.md`;
- frozen independent vector: `native/cmpct-portable/src/implicit_v4_vector_tests.rs`;
- repaired implementation: `native/cmpct-portable/src/manifest.rs`;
- product repair commit: `6fa444f54351301b31e8ee0c97129cfd667c8422`.

## Result

The preregistered hypothesis was confirmed after separating an initial harness/integration defect from product semantics.

The first hosted court was **inconclusive** because `cmpct-portable` did not compile: an earlier test-wiring commit had accidentally replaced a large part of the public portable-reader dispatch with an incompatible `ArchiveReader` surface. That was D0 evidence/integration debt, not a product loss. The coherent reader baseline was restored at `8011f15c8a16b831641c6161cccb43618d01ba09` without changing the hardlink semantic under test.

With the baseline compiling again, hosted run `34785633776`, job `103800485711`, executed the frozen adversarial vector. The vector changed only the authenticated hardlink entry's POSIX mode while leaving its regular-file owner unchanged. The owner mode was `416`; the hardlink mode was `417`. Rust returned `Ok(FsManifest)` where the frozen test required rejection. That cleanly confirmed the preregistered semantic defect: the Rust manifest accepted authenticated hardlink metadata divergence that canonical Python semantics reject.

Root cause was `FsManifest::from_entries`: it already resolved each hardlink to an ultimate regular-file owner and rejected non-file owners, but it did not enforce that the hardlink's inode-owned metadata matched that owner.

## Repair

The shared manifest validation now:

1. derives `PartialEq, Eq` for `FsMetadata`; and
2. rejects a hardlink when `entry.metadata != owner.metadata`, with the explicit format error `r25 hardlink metadata must match regular-file owner`.

This is intentionally a shared manifest invariant rather than an implicit-v4-only patch. It preserves the existing reader grammar and archive bytes; it tightens acceptance of authenticated filesystem manifests whose hardlink inode metadata is internally contradictory.

## Hosted proof

The repair was applied in a temporary CI workspace before persistence, while the frozen independent parity module was wired only into that workspace. Hosted run `34786051253`, job `103801613828`, then proved the complete portable-reader test surface and persisted only `native/cmpct-portable/src/manifest.rs`.

Observed proof surface:

- `cargo test --release --no-run`: PASS;
- portable library unit tests: **24 passed, 0 failed**;
- frozen adversarial hardlink-divergence test: PASS after repair;
- independent valid Python -> Rust implicit-v4 reconstruction vector: PASS;
- compact-control preparity integration tests: **3 passed, 0 failed**;
- ZIP preparity integration tests: **2 passed, 0 failed**;
- logs filesystem materialization, hardlink owner-byte resolution, metadata-copy recovery, gzip/zstd inverse-edge locality, and existing implicit-v4 manifest controls: PASS.

The workflow asserted before commit that `manifest.rs` was the only product file changed. The persisted product diff is 6 insertions / 1 deletion in `manifest.rs`.

## Negative / self-critique

The initial court infrastructure was materially flawed. The original test-wiring change broke the portable public API, and the temporary repair court required two D0 environment corrections before its whole-suite proof was valid: first `msgpack`, then the full editable Python test environment. None of those failed runs are product evidence. They are retained as evidence that test/harness failure must not be narrated as algorithmic failure.

A separate `G04 ML native FFI reader oracle v2` red observed during this campaign is also not product evidence: its patch input is malformed before compilation. It remains independent evidence debt and must not be folded into this result.

## Claim boundary

This result supplies **native semantic parity / hardening evidence only**. It changes no stored-byte score, creation CPU/wall, RSS, selective-read amplification, locality budget, release version, or competitor result. No performance or release credit is claimed.

The next authority step is exact-head revalidation of the persisted product repair through the independent hardlink court and the repository's current native/recovery/platform authority, followed by whichever remaining D5 blocker current repository truth identifies.