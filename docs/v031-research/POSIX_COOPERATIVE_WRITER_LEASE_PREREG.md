# v0.31 POSIX inode-lease experiment — prospective protocol (2026-10-23)

Status: **PREREGISTERED / experimental / NO release credit**. Base `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`. Existing `src/cmpct/transactions.py` Git blob `964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c`. Source-exact negative court PR #289 and Issue #290: two successful disjoint `append_rename` calls sharing a predecessor, with serialized entire physical generation writes, can silently discard one logical operation; separate-process run 40027763420 establishes the same outcome without threads.

## Primary question
Does a POSIX advisory exclusive `flock` on the **existing archive inode** held from **before Reader snapshot** through **after committed-footer fsync** prevent stale-parent silent lost updates across cooperating independent processes, including hardlink aliases, without changing wire revision 24 or normal Reader operations?

### Falsifiable prediction
Under controlled A/B scheduling, a first cooperating writer paused after snapshot prevents a second cooperating writer from reaching its snapshot until the first commits. After both successful returns, BOTH disjoint names survive and `CMPCT.verify()` succeeds. The original unguarded Writer is the stronger simpler negative control and will enter both mutation callbacks before release. The lock must release on exceptions, allow sequential subsequent writes, and serialize aliases to the same inode.

### Alternative explanations and kill/narrow conditions
- A lock only around `_append_generation` already fails the original falsifier; do not use it.
- A sidecar keyed to the pathname can disagree across hardlinks; do not substitute for inode identity without testing.
- Advisory locks do **not** stop non-cooperating processes; do not claim general adversarial serializability.
- `stat`/inode checks are not a race-proof containment architecture against hostile pathname replacement and do not pin path-based Reader/Writer opens. If a rename/replace during the operation is admitted silently in a dedicated adversary, keep product promotion blocked. An independent fd-pinned transaction architecture would be needed for stronger guarantees.
- If Linux-specific `flock` is unavailable, fail closed in this candidate; explicitly record Windows/macOS behavior and portability debt before merging. Do not silently fall back to unlocked writes.
- If ordinary single-threaded updates, deletes, renames, checkpoint/recovery semantics, valid symlink/hardlink paths, source permissions or existing reader access regress, **candidate not promotable**.
- No release or format bump, no changes to frozen evaluation semantics or historical fingerprint.
- Measure at least targeted wait/order, exact logical tree, exit statuses, execution overhead on uncontended and contended cases; reserve full r24/ZIP same-runner ABBA, crash, RSS/temporary I/O and cross-platform gates for a future promotion decision.

## Pareto selection
A) Implement inode-wide cooperative lease (this bounded R2 correctness question).
B) Fail-closed reject all Writer mutations (stronger safety but major functionality loss).
C) Pathname sidecar (fails hardlink alias without stable global naming).
D) Extra stale-footer compare after snapshot without atomic exclusion (racy, reject).
E) Broader descriptor-root transaction rewrite (stronger hostile-replacement containment, but adjacent API architecture, higher implementation/review cost). This candidate tests A without marketing A as E.

## Evidence and ownership
Issue #290 owns the gap; PR #289 owns original negative. The dormant `agent/phased1-v031-transaction-multiwriter-ownership` and `agent/phased3-v031-transaction-inode-lock-20261013-run29` branches both equal the development SHA at orientation; no active overlapping implementation was found. This experiment is a distinct bounded candidate under the issue; it must remain DRAFT. Discovery `STATE.json` is staleable, owned by PR #240, and will not be overwritten.

## Decision boundary
Focused installed-package positive proves only **cooperating POSIX writer serialization and preserved archive semantics on measured cases**. It is not proof of arbitrary untrusted concurrent filesystem safety, Windows parity, durability under power loss, or product release readiness. Keep raw negative observations, regardless of whether this hypothesis passes.
