# O26b preregistration — Sealed-source mapping and critical verification window

Date: 2026-10-24 UTC. O26 original hosted first at source `f7ec477ab5ba48e5d76753e547b79fe604dadf7e`, run `40129952439`, artifact `12574523297`, specialized SUCCESS. Original positive 4/4 corpus cases and 60 process observations must remain immutable evidence; modifying the old script changes only a successor, not retroactively the original.

## Narrow new question
Does Linux `F_SEAL_WRITE` also reject writable **shared mmap** of the sealed archive FD, and does attempted same-UID mutation specifically **after CMPCT.verify() but before CMPCT.extractall()** leave the resulting filesystem bytes identical to the authenticated snapshot? Distinguish `MAP_SHARED` from `MAP_PRIVATE`: private writable mappings may succeed but changes must remain private and must not alter the underlying sealed archive.

## Prediction and fixed oracle
On each O26 authentic RAW/S_PACK 128B/4MiB source, seal the full copied archive as before. Check attempts to create `mmap.MAP_SHARED` with `PROT_READ|PROT_WRITE`: require denial (EPERM/EACCES) by Linux. If `MAP_PRIVATE` is accepted, write a byte to that mapping and independently prove the FD content hash is unchanged. After successful `CMPCT.verify()`, repeat the ordinary FD write/size-change denial and shared-mmap denial *before* extraction; verify output SHA remains the original. Preserve original outcome and cost protocol unchanged. Direct source path mutation remains independent in-place identical-inode/size + CRC repaired, physical SHA stale and rejected by fresh verifier.

## Disproof and limits
Any permitted MAP_SHARED write changing the sealed archive, MAP_PRIVATE write changing the shared archive, successful pwrite/truncate after verify, or changed extraction output defeats O26b. A memory-map syscall denied for unrelated environment reasons is inconclusive: require a writable shared-mmap **positive control** on an unsealed memfd in the same process, and ensure seal bitmask is present. Only one Linux host, ordinary same-UID write syscalls, not hostile process control/ptrace or OS administrator adversaries. No consistency cut during original copying, no protected output file, no portability or release performance credit. No product/format/benchmark/validator changes.

## Cost
The successor may incur test-only extra kernel mappings and hashes; no new product performance claim. Fresh-process ABBA time results of O26 remain classified as same-semantics scientific control only; RAM-backed archive pages count against the resource budget even when `ru_maxrss` is constant.
