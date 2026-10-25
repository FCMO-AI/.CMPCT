# O103 — Reader mapped-source lifetime after same-inode truncation (preregistered, 2026-10-25 UTC)

**Status:** prospective science-only falsification, NOT a product fix, release or vulnerability severity assessment. Source authority: `FCMO-AI/.CMPCT` canonical v0.31 development `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, shipping v0.30.0/r24 unchanged. Original `src/cmpct/reader.py` Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`. This test must run the installed real Reader/Builder, not a mock mmap.

## Question and baseline
The Reader opens a file descriptor, recovers the index, then `mmap(MAP_SHARED, ACCESS_READ)` the archive; subsequent `BHDR.unpack_from(self.mm,pos)` and slicing are performed without pinning an immutable backing file. `mmap` protects the relationship to an inode across atomic pathname replacement but not necessarily a concurrent in-place truncation of that same inode. The process could receive SIGBUS rather than a catchable Python validation error if the source file shrinks under a mapped page.

## Preregistered prediction (before implementation/result)
On Linux and macOS: build a genuine r24 archive containing a regular BLOB sufficiently large to place payload past page 1; in a disposable child with a freshly installed Reader, (1) stable file reads and verifies; (2) rename-replacing the *pathname* with a second regular archive after Reader open leaves the original descriptor/mapping valid and reading the old member exact; (3) truncating the *same open inode* to zero immediately after Reader open then reading the member terminates the child with a SIGBUS/similar host fatal mapping-fault signal, not a managed IOError. A Linux SIGBUS child exit establishes the narrow fault; a handled exception, normal return, or inability to establish the source identity kills/narrows that hypothesis. macOS may legitimately signal differently; report honestly. Windows has different handle-sharing rules, so no Windows claim or runner required.

## Strong controls and evidence
Child isolation and timeout: a crashing child cannot crash the CI runner or agent. Fresh temporary fixtures; source bytes and member SHA-256 recorded before mutation; confirm the archive Reader was already open before each mutation; use `os.ftruncate(reader.f.fileno(),0)` to ensure same physical descriptor/inode, not a pathname race; record child return code and signal; normal Reader first read and `verify()` pass; on renamed original, old mapped bytes remain readable, new pathname has different inode. A separately executed POSIX raw mmap control establishes underlying OS behavior but receives no CMPCT product credit.

## Interpretation and alternatives
A SIGBUS would demonstrate a **source-lifetime/process-availability** defect *under concurrent hostile or accidental mutation of the archive inode*, not malformed immutable-archive parsing, content-authentication bypass or exploitable remote crash. Solutions differ: a semantic immutability contract, snapshot/copy source, descriptor-based size detection (cannot eliminate race), platform-specific in-memory/guarded reads or no mmap. Each carries read-CPU/RSS/I/O/portability cost; do not implement an unmeasured fallback or downgrade strong verification.

## Coordination and kill
Owner search through GitHub 2026-10-25 found adjacent PR #286 for a separate stale-mmap Deflate **export** mutation, Writer update races #289/#295/#311, and Reader snapshot issues, but no currently owned same-inode external truncation during ordinary Reader `read()`. This research alters no owner implementation, Discovery State, release thresholds, historical comparisons or source files. Productization requires owner coordination, exact semantics, resource accounting, and a full release gate. Negative test success is not secure-product success.

## Planned lowest decisive court
A single source-pinned installed Linux wheel test plus separate macOS job if available: stable, atomic pathname replacement, same-open-inode truncate. Preserve stdout/JSON before child exits and report exit signals, unlike tests which equate a successful scientific falsifier with safe production behavior.
