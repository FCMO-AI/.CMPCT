# O24 RESULT — private complete archive snapshot under post-copy source mutation

**Date:** 2026-10-24 UTC. **Scientific status:** `CONTROL_CONFIRMED_IN_TESTED_SCOPE`; not product/release credit. Preserved preregistration: `f8f4c0a21efaaf5080328f31c26f2ac1f792ebe6` (committed BEFORE instrument and workflow). Current released v0.30.0 / revision-24 unchanged.

## Exact authority and host receipt

- Parent O23 source: #376 `3493f4e3cfbad6c295161f63ec163a6b78d60692`; Reader blob `60f52328467ca509bb410abe6a34810c50917cb5`; independent fixture generator blob `2383bf9a8f7ce8a9a01028ccf1072169897df3f1`.
- O24 research workflow and script source HEAD: `b80df5fd24b54429f90fa0c0460dc0820651ab69`, [hosted scientific run 40127113318](https://github.com/FCMO-AI/.CMPCT/actions/runs/40127113318) **SUCCESS**, Ubuntu 24.04 / CPython 3.11 with actual CMPCT package installed.
- GitHub artifact ID `12573623251`; downloaded ZIP SHA-256 `806160e404c949161a1baa071f2d4f3f93be0abe3aa29646fa1f1ef1b4f6b209`. Inner unmodified `o24-original-data.json` SHA-256 `cb85624739a360934a13888d1514ec0310716007b10eb8c9d6917f8254f435f7`. The original JSON, subprocess stdout, exact checkout SHA, source Git blobs and four-line commit history are included. Audited medians independently from all raw observations, NOT only the summary values printed by the test. A later docs-only HEAD must obtain its own checks to claim full new-HEAD CI.
- Workflow verified original Reader source and O23 experiment/fixture Git blobs before running. PR #377 changes no product source, format, comparisons, official thresholds or installed application behavior.

## Decision: post-copy mutation

The full authenticated revision-24 archive was copied into a private 0600 file before modifying the source path's *same inode*, preserving the original size and authenticated index/physical SHA while repairing the modified physical CRC. Reopening the original corrupted file and copying it *after* mutation independently failed at physical-SHA verification.

All four crossed cases succeeded: 128-B direct RAW, 128-B S_PACK, 4-MiB direct RAW, 4-MiB S_PACK. For each, the private snapshot's strong `verify()` passed, the same snapshot Reader's `extractall()` published the exact pre-mutation content, and the ordinary live source's SHA-inconsistent bytes were independently recognized as mutated. **4/4 semantic cases passed; source inode+length identity preserved; 0 unverified snapshot publications.**

This outcome does **not** solve concurrent modifications during the snapshot copy, an attacker capable of rewriting internal commitments, destination symlink races, or atomic whole-tree publication. Nor is it an independent claim of cryptographically signed origin.

## Fresh child processes: charged economic control (5 A/B blocks per case; 40 observations)

The **operation** timer includes private copy + Reader strong verify + full extraction for B, and same-Reader strong verify + full extraction without copy for A; excludes fixture generation, Python process startup, independent output hash oracle and cleanup on both sides. Complete fresh-process wall was also retained separately. Medians below recomputed from the original JSON.

| Case | Archive B | A op wall ms | B op wall ms | B/A | B minus A ms | A CPU ms | B CPU ms | Fresh-process A/B ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| RAW 128 B | 586 | 0.266 | 0.827 | 3.110× | +0.561 | 0.263 | 0.452 | 50.444 / 51.268 |
| RAW 4 MiB | 4,194,760 | 5.675 | 14.324 | 2.524× | +8.649 | 5.670 | 8.401 | 67.463 / 76.759 |
| S_PACK 128 B | 628 | 0.319 | 0.835 | 2.618× | +0.516 | 0.316 | 0.488 | 49.128 / 50.000 |
| S_PACK 4 MiB | 4,194,820 | 16.884 | 30.020 | 1.778× | +13.136 | 16.879 | 19.817 | 79.699 / 93.952 |

Each of the five paired blocks per case had a **positive snapshot penalty**, not an isolated adverse sample: RAW 128 B +0.493/+0.675/+0.540/+0.542/+0.599 ms; RAW 4 MiB +19.704/+8.690/+7.411/+6.177/+8.737 ms; S_PACK 128 B +0.520/+0.514/+0.528/+0.601/+0.497 ms; S_PACK 4 MiB +22.864/+13.105/+12.135/+12.421/+13.423 ms. The first block of each 4-MiB case has a larger cold-file effect; median is not extrapolated to production.

Linux `ru_maxrss` observed exactly equal medians on both arms within each case (30,420 KiB tiny, 62,956 KiB large). This coarse lifetime peak **does not** establish zero heap overhead or bound peak copy buffers beyond the 1 MiB Python copy block and ordinary subprocess runtime.

**Exported physical charge:** a complete additional `archive_bytes` temporary disk file per extraction, at least that many source bytes read and written during snapshot creation; the subsequent verify/extract must read this copy as well. Snapshot files were fsync'ed (durability instrumentation cost included). The 4-MiB cases remained under the prospectively selected `>3×` operation-wall / `>10 MiB` RSS cost label; tiny RAW exceeds 3× but that label was expressly scoped to 4 MiB. This is not an optimization or release gate, only a bounded safe-control cost.

## Counterfactual and next decision

The earlier O23 small-vs-large crossing isolated Reader **cache size**, not a PACK-vs-RAW format semantic difference. A private archive byte copy makes the verified content independent of subsequent rewrites to the original path; it costs actual I/O and scratch storage. A pair of deterministic 4-MiB cases plus original/mutant SHA controls would have been sufficient to decide this basic snapshot question; the small cases constrain the structural generality and calibration.

**Scientifically confirmed, economically non-free.** Keep this isolated research PR draft; do not quietly turn `verify(); extractall()` into a strong immutable-source promise. The next significant product question is whether a **one-pass, per-physical-owner verified staging + publication boundary** can preserve the safe copy's exactness without retaining N bytes of *complete archive* and with robust guard against mutation between verification and materialization. Another cheap alternative is a narrow trust-model contract requiring a stable, private source path; it must be explicit, not implied. Test source rewrite **during** a snapshot copy before any broad safety claim. Re-check hostile paths/hardlinks/metadata, temp/read amplification, create/extract/verify wall+CPU, RSS, Windows/macOS/native capability, and official parity separately before promotion.

No canonical merge, format or release change; the scientific outcome is scoped to one Linux host and controlled after-copy mutation.


## Structural cost frontier (no product measurement)

Let `A` be complete stored archive bytes and `L` be the logical materialized tree's bytes, with sparse filesystem holes treated as sparse logical extents rather than necessarily allocated disk. The complete-source private snapshot copies `A` bytes to scratch and must subsequently strongly verify/decode/extract; its scratch footprint is `A`. An alternative whole-tree output staging architecture may require scratch proportional to *materialized* `L` (or allocated sparse extents), plus per-owner integrity metadata, and it must preserve inode topology, symlinks, xattrs, ownership and failure atomicity. **One-pass staging does not automatically dominate snapshot copying in stored bytes**: for `A << L`, a compact archive snapshot may consume far less temporary space. Conversely when `A ≈ L`, an authenticated staged decoded-owner pipeline could avoid copying original archive bytes while paying staging/output costs. No cost saving is asserted until a real product A/B charges the actual physical bytes, CPU, RSS, read/write amplification, verified source lifetime, selective access and recovery.

The cheapest next oracle is a generic `(A, L, sparse-allocated-bytes)` projection on identical authentic archives, compared against the strongest simple copy; kill any proposed universal ownership path whose optimistic scratch/I/O bound already loses across its intended domain. Preserve a Pareto choice rather than a single scalar/fixture-specific threshold.
