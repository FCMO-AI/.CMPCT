# O56 — Confirmed silent NTFS named-stream loss on authentic O50 Builder

Date: 2026-10-25 UTC. **Research conclusion: SOURCE_INVENTORY_LOSS_CONFIRMED_WINDOWS_NTFS.** Preregistered [before experiment](2026-10-25-o56-ntfs-ads-source-completeness-prereg.md) at commit `1fa1854f3d51ec514f7af9660cd3ca17b321d3b3`. This file records observed outcomes rather than modifying the scientific prediction.

## Source, host and measurement custody

Original product: O50 [#405](https://github.com/FCMO-AI/.CMPCT/pull/405) exact base commit `17c96603e33b02b3f2f9e0079eec2b128f293be8`, actual installed Builder Git blob `21a9ec696df13961c25301654feb607a7e161a4c`. Tested with source-bound research HEAD `4a5c5c10c33c5886b8af66f23bd6a7f8cac5742a`, which changed **no product file** from original O50. CPython 3.11.9 installed outside checkout on GitHub `windows-2025`.

[Real exact-source Actions run #40164441760](https://github.com/FCMO-AI/.CMPCT/actions/runs/40164441760), [unaltered JUnit/log/JSON artifact #12587393904](https://github.com/FCMO-AI/.CMPCT/actions/runs/40164441760/artifacts/12587393904). JUnit **3 tests, 0 failures, 0 errors, 0 skips**. Tests executed with the real Python Builder/Reader, output revision-24 physical archives and independent Win32 `FindFirstStreamW/FindNextStreamW` enumeration; source byte content remained stable.

| Actual scenario | Source physical data streams | Restored physical data streams | Physical reconstruction | Archive |
| --- | --- | --- | --- | --- |
| Ordinary regular | `::$DATA` 4096 B; `:cmpct_o56:$DATA` 331 B | `::$DATA` 4096 B only | Named stream **missing** | 1235 B, emitted and Reader-verified |
| Regular + NTFS hardlink | `::$DATA` 4096 B; `:cmpct_o56:$DATA` 331 B | `::$DATA` 4096 B only | Hardlink alias **preserved**, named stream **missing** | 1267 B, emitted and Reader-verified |
| Unnamed-stream-only control | `::$DATA` 4096 B | `::$DATA` 4096 B | Exact regular success | 1239 B, emitted and Reader-verified |

Original default-stream SHA-256 in both ADS scenarios: `bc3eb3ed30d4e2dff2069c0c59e51cd14c9e09efb571c2ec1a1a0b771c2b8316`. Named-stream SHA-256: `5daeea8a47886e5d6ef1cee451ed9762098622321a4c99692b684095f7d07833`.

Actual regular ADS archive SHA-256: `42b803c754ff20a1bade37a2e8b3f8703d3e716161182187ce6c984022c7373f`. Actual hardlink ADS archive SHA-256: `49b55c1c5401d3290ae4853bd93108cd008ca5046a8f0f90ddddd3dc84e0393b`. These are fixture-specific evidence identities, **not** an admission heuristic or general product benchmark.

## Falsification and interpretation

The preregistered prediction was confirmed: an authenticated archive can encode *all default-stream bytes* and remain cryptographically valid while losing nonempty named NTFS data outside the format's captured model. This is **not an SHA-256 collision, a corrupt r24 file or a loss of source hardlink ownership**. It is absence from source inventory. Named NTFS streams are not distinct `scandir` entries. `Builder._capture_fs_meta` handles portable POSIX xattrs but does not enumerate Win32 named $DATA streams.

The strongest alternative explanation is a deliberately restricted v0.30/r24 metadata contract. That may be legitimate for a format **if unsupported inputs are observably rejected or the excluded guarantee is explicit**, but the tested end-user success path did neither. The result does not claim r24 must retroactively gain full NTFS stream semantics; the lower-cost initial product response is fail-closed admission.

## Boundary and negative self-critique

Only the actual hosted Windows NTFS regular-file paths were examined. Directory-level streams, symlink/reparse points, legacy NTFS variants, ReFS, remote shares, ACLs, EFS, volume capability errors and concurrent source mutation remain untested; **no** immutable filesystem snapshot is implied. O52/O54 investigate different source-time races. There is no CPU/wall/RSS, enumeration-syscall cost, all-platform installed product-release or frozen ZIP/Deflate performance evidence in O56. A green JUnit proves the *source defect*, not a corrected product.

## Durable disposition and coordination

- [Issue #412](https://github.com/FCMO-AI/.CMPCT/issues/412) records the product contract choice and acceptance criteria, distinct from [#408](https://github.com/FCMO-AI/.CMPCT/issues/408) live-source custody.
- Notified original O50 owner [#405](https://github.com/FCMO-AI/.CMPCT/pull/405), preserving their branch and controls.
- Independent reversible [O57 candidate #413](https://github.com/FCMO-AI/.CMPCT/pull/413) explores a **Win32 regular-file fail-closed admission**, not a new format or release.
- No Discovery Engine or state-policy edit. No universal search-policy lesson has earned repeated-evidence promotion.

## Counterfactual prospective lesson

An inexpensive physical named-stream enumeration check **before** treating ordinary Win32 `stat`/read as a complete source-object description would have decided this fork sooner. The decisive discriminator is the *inventory of all source-held data streams*, not a stronger digest of the unnamed stream. Transfer cautiously: filesystem-specific metadata must be counted at the admission boundary before claiming tree completeness.

**Research conclusion: confirmed / decision-changing. Product repair: not provided by O56. Release credit: zero.**
