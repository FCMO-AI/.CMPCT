# v0.31 Windows cooperative Writer lease: O3 product preregistration

Date: 2026-10-23 UTC. Status: PREREGISTERED; no product or release credit.
Base: exact Reader x POSIX Writer composition `2c8329276d875e0940db98551c70f329d7cecd57` (PR #298); original POSIX lease source PR #295, writer blob `8fa50d50fe186195e60d2e7db51f17cd3125b1e0`. Historical loss witness PR #289 / run 40027763420; issue #290. Windows primitives O0/O1/O2 in runs 40040076203, 40040286618, 40040511901 and owner #295 handoffs.

## Narrow primary question
Can an opt-in, same-archive-inode *cooperative Windows Writer lease* extend the existing POSIX transaction-wide snapshot-to-footer exclusion without breaking unchanged Readers, hardlink aliases, append offsets, valid archive bytes, or fatal-error cleanup? The selected primitive is a one-byte `msvcrt.locking` range far above physical EOF (position 2^60), with the existing `O_RDWR|O_APPEND` held descriptor used for `dup`-based writes and `fstat` offsets. This does NOT claim hostile/noncooperative Win32 `FILE_SHARE_DELETE` resistance, remote share semantics, or power-loss durability.

## Predictions and disproof
1. Fresh Windows Server 2022/Python 3.11 installed-CMPCT court: two cooperating independent `spawn` processes rename disjoint entries and return success, both names survive and `verify()` passes. The second writer must not snapshot an obsolete footer while the first owns the lease. A hardlink alias must serialize too. A deliberately held lease must not prevent read-only CMPCT operations.
2. Multiple sequential single-writer mutations (rename, update, delete), failure-path lock release, no new holes or misplaced blob/footer offsets, and byte-identical unchanged parent archive after rejected mutation. Exact index/fs semantics preserved.
3. The POSIX lease and all Reader integrated behaviors must remain unchanged; Linux focused and general tests cannot regress.
4. A Windows lease on byte 0 is the *rejected control*: it blocks ordinary header readers (O0). Sidecar-by-path is rejected because hardlinks escape one owner; appender-only lock is rejected by the independent stale-footer negative. O2 showed ordinary Python held handle itself denies `os.replace` locally, so an O3 rejection MUST NOT claim this is caused by the lock.
5. Fail closed if `msvcrt` lease acquisition fails; release only on successful lock acquisition; preserve primary exception. No negative may be erased or relabeled as a release pass.

## Explicit cost and limits
This extension pays one exclusive range lock for every mutating operation, holds it for compression/source reading and two footer fsyncs, and may wait under contention. No size/compression win predicted. No full create/extract ABBA, RSS, macOS, remote filesystems, malicious uncooperative writers, or Windows version matrix credit unless separately measured. Numerical version, r24 wire format, frozen v0.30 source-lock, CI thresholds/comparators, and discovery-state cache must not change.

## Proof path
Implement the smallest independent Windows backend and a Windows-only real package workflow (not a primitive-only oracle). Upload exact `github.sha` and pytest JSON/log artifacts, retain failures. Keep the PR DRAFT stacked on PR #298 and send the upstream owner a bounded technical handoff. If Windows errors or test cannot execute, classify as infrastructure/portability pending; do not claim product support.

## Concurrency
Existing PR #295 owns the POSIX Writer, PR #298 owns the Reader/Writer composition; PR #299/#300 own Windows O1/O2 primitive results. This O3 branch is an explicit *dependent Windows extension*, not a replacement; preserve all POSIX blocks and Reader owner bytes. Discovery `docs/discovery/STATE.json` left unchanged, owned by PR #240.
