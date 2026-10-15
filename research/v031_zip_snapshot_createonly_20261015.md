# v0.31 ZIP verified-new publication: source-snapshot research (2026-10-15)

**Status: research only; not merged or a release.** Base: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; Python Reader Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`. No r24 format or frozen evaluator changes.

## Hypothesis and control

The original direct raw-DEFLATE ZIP exporter reads bytes from an mmap and writes an output without checking the stream's actual logical size/SHA/CRC. Prior bounded prevalidation can race source mutations between proof and copy. Prior staged ZIP revalidation protects the destination but entails a separate post-write ZIP read. A materially different option captures **one owned compressed byte snapshot**, verifies its bounded decode against physical and logical metadata, and writes **exactly that snapshot** to a private ZIP. An exclusive hardlink publishes only a **previously absent pathname**: preexisting files, symlinks and hardlinks are never replaced. This is NOT an update-in-place API, full trusted-source authentication, or cross-platform durability claim.

## Independent local results (not hosted CI)

Research-only Python subclass and create-new staging wrapper, using unchanged source-exact reference ZIP writer. 33 focused tests pass, including valid ZIP byte parity, non-direct rows, intentional source mutation before/after snapshot capture, destination name aliases, late failure, ENOSPC simulation, and publication syscall failures. The independently seeded 5,000-case r24 raw-DEFLATE mutation court has **1,711 accepted, 3,289 rejected, zero oracle disagreements**. Accepted ZIPs decoded exactly. A real Builder-derived 18-row archive produces the same 133,834-byte ZIP as baseline. All emitted valid controls tested with Python zipfile; selected controls also pass external unzip.

Five fresh-process repetitions per arm, startup excluded, fsync disabled; complete-operation median wall milliseconds:

| Scenario | Unsafe direct | Prior staged postvalidation | Snapshot + create-only |
|---|---:|---:|---:|
| 128 B | 0.0955 | 0.5642 | 0.2795 |
| 1 MiB zeros | 0.1113 | 3.3905 | 3.2960 |
| 128 members | 0.5314 | 4.0395 | 2.2929 |
| 8 MiB highly compressible | 0.1068 | 12.6460 | 11.3047 |
| 8 MiB incompressible | 3.8958 | 14.4926 | 12.8479 |
| 18 mixed rows | 3.7597 | 4.7199 | 3.9819 |

**Negatives/limits:** verification still pays O(decoded bytes): the fast unverified path remains up to ~106x faster on a repetitive 8 MiB control. Source mmap truncation/SIGBUS, untrusted-writable stage directory, directory-fsync failure *after* publication, non-direct codec resource bounds, default output mode (0600 versus typical 0644), Windows portability, arbitrary archive sizes and same-source canonical CI are not proved. The new API refuses overwrites, deliberately differing from the original API. These are local oracle results, not product or release evidence.

## Decision

Keep snapshot-linked publication as a separate experimental contract, not a default replacement for `CMPCT.export_zip()`. Evidence favors binding the bytes proved to the bytes published; it does **not** eliminate the decompression cost required to validate self-described untrusted DEFLATE without stronger authenticated proof. Compare with the simpler staged postvalidation and retain the faster baseline only behind an explicit trust contract. Global CMPCT priority remains the exact frozen bounded-drift court; this work does not supersede Issue #194/#206.
