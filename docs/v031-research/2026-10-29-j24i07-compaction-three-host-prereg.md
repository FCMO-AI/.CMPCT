# J24I07 — Three-host installed compaction portability court (preregistration)

Date: 2026-10-29 UTC. Status: **PREDICTION / NOT RESULT**. Exact source baseline: J24I06 PR #723 head `52d51b9446dc8876319f7bd1e6ca2b7f54681de8` stacked over J24I05 PR #720. No changes to CMPCT product source, format, public extraction policy, benchmark/release evaluators or thresholds.

## Primary question and why now
J24I06's exact-source Ubuntu installed court passed eight genuine r24 cases and independent physical audit; cross-host portability remains unmeasured. Can the **same installed candidate source** preserve archive-to-archive logical semantics for ordinary file, literal absolute symlink, parent-relative symlink, hardlink, and corrupt-source destination rollback under Ubuntu 24.04, macOS 14, Windows 2022? This is a productization falsifier, not compression research. It can veto promotion immediately.

## Competing approaches and BONK
A. Run existing J24I06 court unchanged on all hosts: simpler, but its Linux xattr admission is unconditional, so on hosts without `os.setxattr` it falsely reports absence of an optional facility as corruption; that is a harness defect.
B. This dedicated **portable invariant subset** with explicit platform capability proof, independent source/destination SHA, exact Reader indexed metadata, a sentinel outside the rebuild root, and public safe-extraction negative controls. It tests real interfaces and never edits the system under test. Chosen as the cheapest decisive portability gate.
C. Full crash/durability filesystem fault injection and resource profiling: important but costlier and orthogonal. They do not replace the three-host correctness falsifier.

## Prediction and disproof
Prediction: positive cases preserve full indexed metadata, file/link bytes, hardlink owner relationship, and verify; ordinary `extractall(safe_symlinks=True)` still rejects restricted symlinks; corrupt source cannot replace destination; external sentinel unchanged; same-source package is imported from the installed wheel on every host. Any exception, mutation, case omission, or unsupported symlink/hardlink capability is a **non-PASS**, with the underlying reason recorded. No silent skip or substituting an emulated path test. Control plain file must pass on each host. No cross-host binary archive identity is expected because OS metadata and path encoding differ; only before/after within each host are compared.

## Evidence and release law
Workflows pin source using exact checkout head, install the package into a clean Python 3.11 venv, compile/run the portable test, emit OS/Python/source SHA/physical file SHA and per-case receipts, upload evidence even after failure. Record full stdout and raw receipts. Existing Ubuntu J24I06 8-case court remains inherited and must not be weakened, renamed, or replaced.

PASS means bounded experimental cross-host correctness, not release readiness: source-independent parser validation, complete host-concurrent race/ACL cases, Windows and macOS filesystem semantics beyond these cases, crash durability, CPU/RSS/temp I/O, full general suite and official performance gate remain debt. A non-PASS is retained as a reproduction, not fixed by skipping a host. Do not update discovery STATE.json (PR #574 owner) or alter release fingerprints.