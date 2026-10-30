# J24G85 — Cooperative per-append lease + size-validated owned Writer state (preregistration)

**Status: PROSPECTIVE / RESEARCH-ONLY / NOT A SHIPPING MUTATION.** Frozen before implementation and before observing the J24G85 hosted result. Source parent: PR #833 exact `bcbb377dffdcc1ccae1c8510b3abb8bc89233098`; inherited J24G83 three-way physical science only. Published main v0.30.0 / format revision 24 remains unchanged. Do not claim product, security, cross-platform, or release credit.

## Baseline and material problem

J24G83 measured two 63-delete families: fresh optimized Reader-per-append was ~5.1x faster than unchanged public Writer, while a private 63-commit state owner was another ~5.79–6.66x faster. The private oracle assumes no other Writer changes the archive between commits. #290 proves successful overlapping public commits can silently lose logical updates. #295/#304/#409 already own full-transaction Writer lock implementations; this branch must not duplicate or overwrite them.

**Question:** Under a deliberately cooperative, local POSIX file-inode locking discipline, can an owned state survive release/reacquisition of the lock between independent commits while detecting external successful appenders from an independent process, refreshing state only upon visible physical change, and still materially outperforming the public per-append Writer?

The proposed research instrument does **not** implement portable or non-cooperative product locking. It exercises the immutable public mutation primitives under an external test-only advisory `flock` held before opening/validating until after original footer `fsync`.

## Competing mechanisms / BONK

1. A — original `transactions.append_delete()` for each mutation; each call wrapped in the same external POSIX transaction-wide lock. Best conservative control. External Writer uses the same lock and unchanged public `append_rename()`.
2. B — research-only owner retains an in-memory logical index, predecessor footer and delta depth; **reacquires** the same per-call lock, then admits the cached state only if `fstat` identity and file length exactly match the last completed operation. Otherwise it discards all cached state and reloads from a fresh real `CMPCT` under the lock. B calls unchanged `_index_after_op`, `_reject_hardlink_owner_mutation`, and `_append_generation` (including both `fsync` barriers).
3. Strongest alternative C — #829 full-session exclusive owner, much faster when quiescent, but it either holds a lease across the whole session or fails to observe intervening independent commits. No new global cache, speculative tail metadata, format index, or new lock protocol here.

A/B use **identical initial Builder bytes and deterministic mutation order**, 8,192/middle and 32,768/tail member families, 64 deletes each, plus two disjoint renames by a separately spawned cooperating writer after delete #17 and #44. Each external actor must be seen blocked while the parent actually holds its lock, then finish successfully after release. Both A/B must produce the same complete file bytes/SHA-256 after **every** mutation, including external commits; no uncharged metadata, skipped operations, or relaxed recovery.

## Frozen decision and controls

- Correctness hard gate: all intermediate complete physical archives byte-identical, exact index/content, 64th physical update checkpoint, complete strong verification + strict preflight, and final corrupt-tail recovery. A single inconsistency blocks the result regardless of speed.
- Concurrency scope hard gate: an independent process actually waits for a live lock **twice per trial**, succeeds after unlock, and the cached owner detects exactly two external changes and refreshes from real Reader under the lock. A successful external rename must remain in the final logical view. If the check only tests the parent's own writes, reject the claim.
- Performance H1 prediction: at **both** 8,192 and 32,768 initial members, balanced A/B/B/A medians for the 64 locally performed deletes (including B's initial load, lock acquisition and both reopens after external interference) show **>=6x** lower wall time for B than A. The independent external writer's wall/CPU is separately recorded, not charged to either local timing (same controlled external work on both arms). Each local call includes original `fsync`; SHA auditing is equally outside timing.
- If exact parity fails, outcome `UNSAFE/FAILED`; if the hard correctness/concurrency gates pass but either speed ratio is <6x, outcome `BELOW_MATERIALITY`; otherwise `COOPERATIVE_LEASE_REVALIDATION_SEED_SURVIVES`. No retuning after observation.
- Distinguish library hot path from process startup. Collect per-append wall/CPU, cache miss/refresh count, independent child wall, final archive bytes, index hash, intermediate complete SHA receipts, host/platform, exact Git head/blob checks, and raw failing receipt before any assertion.
- Host: Ubuntu 24.04 Python 3.11. This is one Linux host, with no Windows `msvcrt`, macOS, NFS/SMB, competing non-cooperators, inode replacement/ABA, in-place same-length mutation, journal hardlink/xattr mix, or power-loss crash guarantee.
- Obvious adversarial alternative: a malicious or noncooperating actor may mutate the archive under the test lock, or pathname-to-inode may change between the guard and the unchanged pathname-open writer. The size check is **only** a cooperative append-only proof condition; no general product safety assertion follows.

## Constraints / falsification / handoff

Do not modify `src/`, `native/`, Builder/Reader/Writer shipping APIs, `docs/discovery/STATE.json` (owned by #574), frozen benchmarks, release lock, historical receipts, version or on-disk revision. No retrospective performance benchmark claim. No automatic merge. Preserve original negative results #290, #826 and #833.

A positive result only warrants a narrowly scoped next owner-reviewed integration experiment with the **actual** #295/#304 per-transaction lease implementations, fd-bound append and adversarial inode replacement; it cannot promote a Python test-only flock wrapper. A negative that survives exact physical controls should retire or narrow this per-call lease/cache family before adding more complexity.

The transferable discriminator to evaluate after the run: whether `same identity + unchanged length under an actually cooperative exclusively held transaction lease` is sufficient for quiescent cache reuse, and whether revalidation+refresh retains material leverage at realistic independent-writer interference rates. Do not generalize beyond this bounded condition.