# O26 / O26b RESULT — kernel-sealed complete archive source under post-copy mutation

**2026-10-24 UTC. Scientific decision:** `LINUX_SEALED_COMPLETE_SOURCE_CONFIRMED_IN_TESTED_SCOPE`; **no product or release promotion**. Released v0.30.0/on-disk r24 unchanged. O26 preregistration at `187591928e683952f3f9b5146b1a79680d7b5125`, before its instrument; O26b independently preregistered at `3c9ecb0e8cb0527a34eaae0132139b2bb0a2ccb8` before its additional mmap/critical-window code.

## Exact source, origin and custody

O26 research PR #379 is stacked on O24 #377 parent `73120e0fd4ac4d01fc2526f3fb59b6ce30417d4e`, whose base is O23 #376. Inherited product Reader blob `60f52328467ca509bb410abe6a34810c50917cb5`; authentic synthetic r24 fixture generator `2383bf9a8f7ce8a9a01028ccf1072169897df3f1`; O23 source `134085f99b92764a79899e4cbf5f6c5b3b7b01cf`; O24 disk-copy control `a454ee5ab2920be28c56b3a7fcafd8b0ae99547d`. The CI workflow checks these four exact blob identities and the parent ancestry before running tests on a source-exact checkout.

- **Original O26:** [GitHub Actions run 40129952439](https://github.com/FCMO-AI/.CMPCT/actions/runs/40129952439), source/workflow HEAD `f7ec477ab5ba48e5d76753e547b79fe604dadf7e`, **SUCCESS**; artifact ID `12574523297`, ZIP SHA-256 `cfbe23f4e6f2501c5b2e6b2e2befff5cd8529a04b1ad20d70142cb12623081df`.
- **Prospectively added O26b:** [GitHub Actions run 40130260182](https://github.com/FCMO-AI/.CMPCT/actions/runs/40130260182), source/workflow HEAD `3b5e25b15bfab4d639b292c76c7b219dcbfb4eef`, **SUCCESS**; artifact ID `12574288929`, ZIP SHA-256 `f088ecb3c37acafde99f3bc6558a8aaf8b52e7312a6ed7b3744e875f6f0410c9`.
- Environment: Ubuntu 24.04 GitHub-hosted runner, Linux kernel `6.17.0-1022-azure`, CPython 3.11.17, 4-KiB page size. Raw per-child CPU/wall/RSS and per-case SHA/errno data retained in both original ZIP artifacts; the record is *not* reconstructed solely from workflow summary.
- Exact-head science above pertains to the two *measured source HEADs*. This subsequently added result document is not a claim of new-HEAD overall CI success.

## What was actually falsified and proved

The experiment creates four **real revision-24** archives: RAW/S_PACK × 128 B/4 MiB logical members. Each archive is copied completely into a newly created Linux `memfd_create(MFD_ALLOW_SEALING)` descriptor, using ≤1 MiB copying blocks; the kernel then accepts all four seals `F_SEAL_WRITE|F_SEAL_GROW|F_SEAL_SHRINK|F_SEAL_SEAL` (bitmask `0xf`). Existing `CMPCT('/proc/self/fd/<fd>')` successfully opens, strongly `verify()`s and `extractall()`s the sealed archive. After copy, the original source is overwritten on the *same inode*, with identical stored archive length and repaired CRC, but its unchanged physical SHA commitment makes fresh strong verification fail for the specific expected SHA reason. A sealed copy created **after** that mutation fails the same strong verification. A snapshot copied before mutation retains its original physical SHA and publishes the exact original logical bytes.

All **4/4 cases in each hosted run** passed complete reconstructed-content SHA, source inode/size identity, actual mutation and physical-SHA rejection controls. Ordinary same-user `pwrite`/truncate on the sealed FD, inherited child `pwrite`, and separate child `/proc/<parent_pid>/fd/<fd>` reopen/write were denied with **errno 1 / EPERM**; content hash was independently unchanged. This is a source **write boundary**, not a statement about output publication.

O26b added a different syscall root at the most critical point — **after `verify()` before `extractall()`**. It reruns all four write attempts there, asserts the source SHA remains unchanged, and tests memory mappings. A positive control demonstrates an *unsealed* memfd's writable `MAP_SHARED` mapping really can mutate its bytes. A sealed memfd's writable `MAP_SHARED` mapping is denied (`EPERM`). A writable `MAP_PRIVATE` mapping is allowed to change its **private** page but cannot alter the underlying sealed FD (SHA retained). All 4/4 hosted O26b cases passed this held-out syscall test. Thus the apparent absence of a write race is not inferred merely from a hidden temporary filename, which O19b already falsified; it is enforced by the Linux inode seal in the tested threat model.

**Scientific decision:** A complete kernel-sealed archive snapshot can bind an ordinary CMPCT Reader's verify/extract to the same copied r24 source incarnation against the specific tested **post-copy** original source mutations and ordinary same-UID inode-write/mmap attempts. This is a credible bounded scientific control, **not** a generalized production extractor.

## Fully charged same-source economic control — measurements, not release benchmark

Five interleaved fresh-process blocks per case, three strategies per block: (A) directly `verify();extractall()` on an unchanged trusted source, (B) O24 full private **disk** archive copy with `fsync` then verify/extract, (C) full **sealed memfd** archive copy then verify/extract. 15 per corpus and 60 direct observations per original hosted run; **120** across O26/O26b. Child-operation wall excludes Python startup but *includes snapshot creation and full extraction*; separate fresh-process wall, CPU and ru_maxrss are retained in raw JSON. No timing comparison changes contents, verification strength or logical extraction. The disk arm incurs `fsync` and memfd is volatile, so they do **not** provide identical crash-durability semantics.

| Case | Archived bytes | O26 direct / disk / memfd wall (ms) | O26b direct / disk / memfd wall (ms) | Minimum memfd page charge |
|---|---:|---:|---:|---:|
| S_PACK 128 B | 628 | 0.337 / 0.923 / 0.471 | 0.391 / 0.933 / 0.525 | 4,096 B |
| RAW 128 B | 586 | 0.315 / 0.840 / 0.422 | 0.319 / 0.925 / 0.455 | 4,096 B |
| S_PACK 4 MiB | 4,194,820 | 16.611 / 39.730 / 19.991 | 21.922 / 40.169 / 26.267 | 4,198,400 B |
| RAW 4 MiB | 4,194,760 | 5.476 / 12.635 / 9.571 | 7.004 / 29.358 / 11.866 | 4,198,400 B |

All 5/5 paired blocks per corpus/run had a larger disk-snapshot operation wall than memfd; **direct unchanged-source is still faster**. The memfd ratio to direct was ~1.20–1.75× in O26 and ~1.20–1.69× in O26b, but there is **no product speedup**. The disk differences include a durable `fsync`; the memfd alternative requires real tmpfs-backed memory with page rounding (and can spill to swap). Constant observed Python `ru_maxrss` across arms is a coarse process high-water **not evidence of zero system memory/storage charge**. Both copy solutions require N extra source bytes read and N bytes of copy-write work, on top of verification and extraction. Page-backed memfd bytes are not a general purpose bounded-storage answer for arbitrarily large archives.

## Negative knowledge, strongest self-critique, and admission rule

This falsifier **does not prevent mutation of the original inode DURING snapshot construction**: reading inconsistent pieces could create a torn private copy. Strong SHA verification should reject a torn sample with stale commitments but atomic consistent-source snapshot provenance is not established. Attacker control over reauthenticating all index and blob SHA commits, OS privilege/ptrace/process-control capability, or filesystem/kernel compromise remain outside this trust contract.

Source sealing has **no influence over destination** inode publication, name/symlink races, already-writable staging files, crash durability, Windows/macOS behavior, recovery, or complete metadata/hardlink/sparse-filesystem fidelity. Linux `/proc/self/fd` is not a cross-platform ABI. `MAP_PRIVATE` permits private shadow copies; they were shown not to rewrite the common sealed inode. A memory-backed full archive snapshot can exhaust RAM/storage for large inputs despite small Python buffers. The O26b code reports the minimum page-rounded logical charge, not measured kernel allocator overhead or cgroup memory high-water.

**Simpler surviving control:** a clear contract requiring an immutable trusted input source can avoid all N-byte snapshot costs; O24's private disk copy remains a viable fallback when same-UID immutability is not required and disk scratch is available. Neither must be described as universally safe under adversarial concurrent writes. Do not claim a product win from the favorable Linux memfd vs disk operation wall.

## Discovery Engine / concurrency decision

PARETOBONK alternatives were: stable-source contract (simplest), O24 disk snapshot (proven), sealed Linux memfd (new ownership frame), reflink (environment-specific and not an inode-write seal) and a new fully authenticated per-physical-owner pipeline (high implementation cost). A cheap pre-implementation Linux memfd syscall check indicated feasibility; **hosted r24 reproduction** was required and obtained. O26b attacked a different mutation API and the exact verify→extract window after the original O26 result, preserving the first artifact. No overlap was found with the O25 ordinary hardlink graph owner (#378), Reader startup and CI fingerprint owners, or other product source mutations. This PR remains stacked on #377; O24 original code remains unchanged. Shared `docs/discovery/STATE.json` not overwritten because it is staleable and owned by concurrent reconciliation (#240). No discovery-policy self-modification: two scientific runs do not establish a process failure requiring a constitutional amendment.

## Exact next decision / handoff

Keep #379 DRAFT. Before any product charter, cheaply falsify **copy-time** source mutation and compare a stable trusted-source contract plus Linux sealed memfd versus Windows/macOS-compatible physical-owner staging under honest RAM/scratch/I/O and whole-tree publication costs. Explore one-pass per-physical-owner verified staging only with an explicit release-compatible and bounded architecture; require hostile destination, whole-tree metadata/inode classes, recovery, official r24 parity, and installed ABI/OS evidence before merge or core-release credit. No project code, archive format, benchmark comparator, release version or frozen evaluator changed by O26/O26b.
