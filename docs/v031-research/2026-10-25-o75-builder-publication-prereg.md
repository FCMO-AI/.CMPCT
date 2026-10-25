# O75 — Builder publication failure-atomicity (preregistration)

Date: 2026-10-25 UTC. Status: frozen **before** implementation and result-bearing CI.

## Authority and baseline
Canonical development: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; Builder Git blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`. Released CMPCT is v0.30.0, revision 24. Builder currently ends in `out.write_bytes(header+ic+data+ic+footer)`, which opens the existing destination for truncation. Existing PRs #402/#420 test *pre-write rejection*; O75 concerns **failure during final publication**, a separate narrow ownership surface. No overlapping active Builder-output publication branch found in 2026-10-25 PR/issue search. No shared Discovery cache mutation.

## Primary falsifiable question
Does an injected partial write during final `Builder.build(out)` destroy a previously valid archive, even when the method returns an error? The independent negative control is an ordinary successful build on a fresh path; the historical Builder must be reproduced exactly, not mocked as a replacement algorithm.

## Prediction
A legitimate pre-existing r24 archive A at `out` will be irreversibly truncated when the current `Path.write_bytes` writes a short prefix of candidate B and raises `OSError`. A smallest same-directory temporary-file + atomic `os.replace` publication mechanism will preserve A and leave no temporary file under injected pre-publish write or replace failure, while successful B is byte-identical to the original Builder and reads/verifies exactly.

## Simpler alternative and controls
Keep direct overwrite and document that callers must stage externally: zero added product complexity, but a failed build can destroy recoverable prior data. Caller-managed staging remains an option; a one-copy internal publication boundary would offer a stronger default. Compare both on the *same input bytes* and include: fresh-path success, overwrite success, failure before bytes, partial temporary write, replace failure, old-archive SHA and exact Reader reconstruction, temp cleanup, file mode/permissions. Neither a compiler-made mock archive nor `verify()` alone substitutes for a full original archive.

## Cost and falsification
Measure complete artifact bytes, create wall/CPU (raw repeated measurements, no release claims), extra temporary physical footprint, number of payload writes and creation permissions. The candidate fails productization if it changes r24 output bytes, exposes a half-written replacement, leaves a partial temp after injected exceptions, regresses legitimate public file permissions unexpectedly, or incurs unacceptable create/runtime debt. A same-process microbenchmark is research-only. Durability across sudden system power loss is **not** established by `os.replace` alone; fsync/dir-sync would require an explicit additional cost/guarantee decision. The failure injection is a process-level controlled `OSError`, not a claim of physical power-loss testing.

## Evidence levels and scope
Use genuine installed CMPCT Builder/Reader, standard filesystem primitives and a host-bound GitHub Actions court. Preserve raw negative, positive, SHA, mode, temp listing and exact source identity. Running on Linux alone cannot prove Win32 replacement semantics; extend to macOS and Windows for functionality, without pretending equivalence to all filesystems/network shares. Frozen benchmark thresholds, format, historical release lock, native ABI and current Reader/Writer stay untouched.

## Decision
If source-exact partial-write destruction is confirmed, implement the smallest reversible atomic-publication candidate on an isolated branch and subject it to POSIX/Windows and full-product costs. A clean focused CI is not release proof; promotion needs owner review, general tests, official direct-base release parity, portability and proven runtime economics. This preregistration must not be edited to rescue an outcome.
