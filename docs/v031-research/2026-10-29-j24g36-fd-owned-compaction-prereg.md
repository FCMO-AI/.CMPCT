# J24G36 — source-FD compaction publication research candidate

Date: 2026-10-29 UTC  
Status: **PROSPECTIVE PRODUCT CANDIDATE TEST, NOT A RELEASE.**  
Exact source parent: [#738](https://github.com/FCMO-AI/.CMPCT/pull/738), `ec112a87ea34349b63885f3f0bea4689f192bd2f`; source `transactions.py` `8d1e46e1fdf408c1d95ce9091e25fa159f0e6264`. It already carries sparse-owner and hardlink-alias verification via #620. Baseline released main v0.30.0/r24 `80c358f8824ec1b20d349c92ed94c898090969b0`.

## Primary question and known negative

Can the product compactor preserve the **same opened archive inode** through Builder write, Reader verification, fsync and publish, even if an actor renames/rebinds the private staging-directory entry within the destination parent? [#726](https://github.com/FCMO-AI/.CMPCT/pull/726) established the failure of sibling mkstemp-close/path reopen. [#740](https://github.com/FCMO-AI/.CMPCT/pull/740) established at a **local OS-only rung**, before this file, that a mode-0700 subdirectory alone does not protect a mutable parent namespace; pinned source/destination directory descriptors survived that one Linux rebind. These are known facts, not fresh prospective evidence for J24G36.

## Falsifiable proposed mechanism

On POSIX only, open destination parent directory once; create an exclusive mode-0700 child there, pin that child's directory fd, and create an exclusive O_NOFOLLOW regular staging fd relative to it. Make the Builder write its complete archive to a *duplicate of that same staging fd* rather than opening `Path.write_bytes`; verify through Reader opened from a duplicate of that FD; fsync that FD; publish by `os.replace('payload', dst.name, src_dir_fd=stage_dirfd, dst_dir_fd=parent_dirfd)`. This isolates the physical source identity from any ancestor directory-entry replacement. Keep existing Windows behavior explicitly **unfixed** until a genuine handle-based design exists. Do not silently make Windows protection claims.

Strong simpler control: no-interposition compaction via unchanged inherited #738, exact before/after member hashes, modes, xattrs and recovery. Hostile control: same source with one deterministic rename+symlink interposition on the private directory entry immediately before Builder creation, then compare outside sentinel, expected destination inode/data and original CMPCT. Distinguish path-rebound failure from source archive corruption. Test ordinary POSIX, symlink-rich and sparse+hardlink cases to ensure inherited protections survive. Preserve failure outputs.

## Kills and limits

Any outside write, wrong destination inode/content, missing committed transaction, metadata or hash mismatch, loss of sparse alias bound, or failure to reject hostile source is a decisive red. A no-race positive is necessary but not sufficient. One deterministic interposition is not a general TOCTOU proof; directory creation/open race before the first FD and another actor with the same UID who may enter mode-0700 are explicit residual boundaries. POSIX-only code cannot earn release while Windows and full portability are unmeasured. No format change, benchmark law modification, frozen test weakening, threshold adjustment or release/version bump is authorized.

This is adjacent to but **does not edit** #726/#738 or `docs/discovery/STATE.json`; the possible source changes are `src/cmpct/builder.py`, `reader.py` and `transactions.py` on an isolated child branch. If an existing owner starts the identical repair, retire the duplicate child in favor of coordinated integration.
