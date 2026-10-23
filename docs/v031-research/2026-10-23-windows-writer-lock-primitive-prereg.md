# Windows Writer Lock Primitive — Fresh-Process Decision Oracle O0 (PR #298)

**Preregistered 2026-10-23 UTC before Windows execution.** Research-only, separate from product Writer; does **not** modify POSIX PR #295. Linked preliminary candidate is exact-source PR #298. No release authority.

## Narrow portability question
Can Windows' standard-library `msvcrt.locking` coordinate cooperative writers over a *shared physical file* without making an ordinary concurrent CMPCT header read fail? Test two alternative lock positions: first byte (simple mandatory-range control) and an agreed far-out-of-file sentinel byte (proposal). Confirm that an open/lock operation does not change archive bytes or length.

## Predictions / falsifiers
- **P1:** Nonblocking exclusive lock on byte 0 prevents a second independent process from acquiring the same physical range via the same path or a hardlink. This is expected but not assumed.
- **P2:** A different process may be denied a header read of byte 0 when it is range-locked, making it a poor position for a Reader-compatible writer lease. A passing read would narrow, not invalidate the rest of the question.
- **P3 (decisive):** Lock at byte offset `1 << 60` (far past EOF) is accepted without file growth, still conflicts for different processes/hardlink aliases, yet ordinary byte-0 reads continue successfully. If unsupported or reads fail, retire this primitive/offset under current assumptions. Do not lower the success criterion.
- **P4:** After release, an independent process can acquire the lock and data hash/size are unchanged.

All subprocesses use the real Windows Python runtime, not mocked locking or thread-only serialization. Each result carries source SHA and GitHub Actions job identity, fresh-process return codes, actual conflict/error evidence, and exact file bytes. Control uses same sample file and same subprocess code with only lock position changed. Windows profile is not extrapolated to Linux/macOS, network shares, or malicious/noncooperative writers.

## Alternatives / BONK
- Blanket fail on Windows (current safe but compatibility regression).
- `LockFileEx` ctypes: more OS API complexity than needed to falsify standard-library approach; defer.
- Path-sidecar mutex: hardlink aliases can evade it; reject without identity coordination.
- `msvcrt.locking` at byte 0: cheapest control but might block Readers.
- Far-out-of-file sentinel with `msvcrt.locking`: chosen cheapest decisive experiment. A Windows success is only a feasibility proof; product port needs actual descriptor ownership, crash release, sharing modes, multiwriter append, no hidden open/read denial, timeout boundedness, local vs SMB, and full native tests.

## Guardrails
No changes to `transactions.py`, `reader.py`, on-disk format, benchmarks, thresholds, release lock or Discovery Engine. No product/performance credit from standalone API oracle. Negative findings stay visible. Do not claim portability from an unexecuted workflow or from green build/no substantive test.
