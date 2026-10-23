# Follow-up falsifier — archive pathname replacement inside an active POSIX lease

Date: 2026-10-23. **Preregistered before the adversarial test and mitigation.**
Parent question: `docs/v031-research/POSIX_COOPERATIVE_WRITER_LEASE_PREREG.md`.
Initial candidate code: `src/cmpct/transactions.py@99cccf3d7d31e7c3d1b40f65767f24ffb492e692`; initial hosted pass: workflow run 40033382928, six focused tests.

## Hypothesis / control
Even with a valid `flock` on the original inode, `os.replace` can make the public pathname point at another existing valid archive before `_append_generation` calls `open(path, 'ab')`. An exception from the post-commit identity check comes **too late** to prevent writes to the replacement. The replacement archive's bytes, inode and SHA-256 must remain unchanged when any such transaction is rejected.

A deterministic patch at the narrow generation-call seam will simulate pathname replacement after authenticated snapshot but before append. The strong simpler control is SHA-256 on the independent replacement archive before and after the operation, not merely whether an exception was raised. Original candidate is predicted to raise but still mutate replacement (negative); the stronger mitigation should raise *before writing* and retain the replacement exactly.

## Candidate mitigation
Bind each append descriptor via its `fstat` identity to the locked descriptor *before first write*, without using path-only checks as authority. Check Reader's opened descriptor against the locked identity before trusting its snapshot. Preserve old append-only footer/fsync semantics. Full fd-pinned access across arbitrary hostile namespace swaps remains separate work; ordinary OS advisory locks cannot prevent noncooperating writers or mutations to existing inode content.

## Disproof / costs / scope
A rejected operation that alters the replacement SHA or inode is a real safety regression. Rejecting legitimate hardlink/symlink alias writes also defeats the candidate. No assumptions about Windows/macOS/NFS, arbitrary ABA path attacks, invalid/stale journal tails, or uncooperating processes are added. Measure source/runtime overhead after the structural test; do not change archive format, CRC/SHA, historical release or promotion gates.
