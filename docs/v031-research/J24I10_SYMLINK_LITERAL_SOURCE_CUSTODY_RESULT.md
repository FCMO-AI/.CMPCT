# J24I10 — three-host symlink literal custody result

Date: 2026-10-29 UTC. Status: DECISIVE HOSTED SCIENCE ONLY; no release credit. Preregistered at commit 8d825a2f5cb3b6527e0e43d8b38a33269d38cb93 before implementation. Tested the exact installed source 88dc72bb136be13bead8b7c02f1d487b64d3364e, based on PR #725 at 96989c923ed8a01f6cd6a6ca8bf69002a2409685. Three-host provider run: https://github.com/FCMO-AI/.CMPCT/actions/runs/40814303898 — three jobs SUCCESS.

## Primary question and decision

**OS_REQUESTED_DIFFERS_FROM_OS_OBSERVED_ON_WINDOWS_ABSOLUTE; SOURCE_TO_COMPACT_TARGET_EXACT_THREE_HOST.**

On Windows 2022, the absolute symlink target argument was a conventional C: drive path. The actual os.readlink spelling gained the extended namespace prefix consisting of two backslashes, question mark, and backslash (commonly described as the Win32 extended-length path prefix). It was not lexically equal to the original argument, but was idempotent when used to create a second symlink. Ubuntu and macOS returned exactly the caller's spelling on all three controls.

This **falsifies the universal requested-vs-readback equality assumption in the J24I07 fixture**, not CMPCT's archive integrity. The actual OS-observed target bytes survived source Builder/Reader and private compaction exactly, without modifying any source or external sentinel. Distinguish observed filesystem representation from the original API input and require strict exactness thereafter. Do not normalize away a source/compacted-archive mismatch.

## Fixed three-host matrix

| Host | Relative | Parent-relative | Absolute | Requested/observed mismatch | Source/output physically identical |
| --- | --- | --- | --- | --- | --- |
| Ubuntu 24.04 | PASS | PASS | PASS | 0/3 | 3/3 |
| macOS 14 | PASS | PASS | PASS | 0/3 | 3/3 |
| Windows 2022 | PASS | PASS | PASS | 1/3, absolute target | 3/3 |

Every host checked raw target readback and second-symlink idempotence, exact target bytes in both authenticated archives, complete indexed entries and metadata, strong verification, existing-destination replacement, source/sentinel integrity and default rejection of unsafe absolute/parent-relative links. Single small synthetic examples; recorded CPU/wall timings are not comparative performance claims.

## Independent artifact audit

All three original hosted artifact ZIPs were downloaded. A separate physical revision-24 parser (Python struct, MessagePack, system libzstd, zlib, SHA-256, CRC32; no CMPCT imports) authenticated both indexes, all physical blobs, complete logical entries, content and raw symlink bytes. **18/18 archives passed; nine source/output pairs physically identical; zero discrepancies.** Offline parsing cannot independently recreate host filesystem behavior or sentinel checks, which remain direct original-host receipts.

- Ubuntu artifact 12871338938, ZIP SHA-256 7834c4c77990626c8b6fad433eee7a46366063357737f0ce55db51926d1b3e13.
- macOS artifact 12872125367, ZIP SHA-256 d522646a6e8944a56cde51fabf439741bdfbc366f6ec0c88b8668b722a47d4c1.
- Windows artifact 12872235106, ZIP SHA-256 919719528521379b41a9fe94267dc24ca6aa797cda8cf9ddf4e2904b3d3382d0.
- Independent audit JSON SHA-256 06a50958880e13135dc2d1ac8da7f474770b1f26c8f949ad28f5b897dda3a082.

## Counterfactual, limitations and recommended next action

An os.readlink capture before archive creation could have identified the misplaced fixture assumption much earlier; source-to-archive-to-archive verification is still needed and independently decisive. No general discovery-policy edit is earned.

**Next experiment:** modify only the J24I07 test on a child branch to record requested and OS-observed targets separately and require exact equality of the **observed** target with both source and compacted CMPCT. Keep all security, metadata and default extraction checks. Re-run its four-case real installed three-platform court, including hardlinks, corruption denial, destination symlink and in-place compaction.

Unaddressed: J24I09 #726 stage-name race, true cross-OS re-materialization, recovery, hostile concurrency, full memory/I/O and release parity. This result creates no permission for merge, version bump or publication.
