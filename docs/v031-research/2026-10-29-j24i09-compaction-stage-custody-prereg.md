# J24I09 — private compaction staged-name custody under adversarial rebind (frozen prediction)

Date: 2026-10-29 UTC  
Status: PREREGISTERED BEFORE INSTRUMENT / RESULT. SCIENCE ONLY.  
Exact product parent: PR #723 `52d51b9446dc8876319f7bd1e6ca2b7f54681de8`; released reference: `main@80c358f8824ec1b20d349c92ed94c898090969b0` (v0.30.0/r24).

## Primary question

Does J24I06's freshly created sibling stage actually prevent an untrusted actor with write access to the *destination directory* from re-binding the stage pathname between `mkstemp` + `close` and `Builder.build(stage)`, even while the in-memory writer retains proper archive/metadata verification?

The source shows `tempfile.mkstemp()`, immediate `os.close(fd)`, and a subsequent `Builder.build(stage)` that uses `Path.write_bytes` at the same pathname. A subsequent `CMPCT(stage)` verification and `os.replace(stage,dst)` would then operate on whichever filesystem object the stage name resolves to. That is a **time-of-check/time-of-use boundary**, not another sparse/symlink metadata mismatch.

## Hypothesis and strongest simpler control

H1 (unsafe): in a temporary, wholly synthetic test namespace, a deterministic single interposition **at the existing Builder entry boundary** (no product source edit) removes the closed stage file, replaces its name with a symlink to an outside sentinel, and then resumes the unmodified installed `Builder.build`. The compaction writer follows the symlink, overwrites the sentinel with genuine CMPCT bytes, validates through that symlink, and eventually makes `dst` a symlink rather than a regular archive. The ordinary no-interposition control must produce a regular exact archive with an unchanged sentinel.

Stronger simple control: a *pre-existing destination symlink* is known to be replaced by `os.replace` rather than followed; this is **not** equivalent to a re-bound stage name, so the court must distinguish them. The relevant control is same original CMPCT input and code, with only interposition removed. The independent operating-system fact `Path.write_bytes` follows a symbolic link is an initial lower-rung observation, not evidence about installed CMPCT until hosted.

Alternative explanations to falsify: initial materialization fails; Builder does not write to the supplied stage pathname; `CMPCT(stage)` refuses a stage symlink; `os.replace` itself protects a directory previously written through another name; or the first control already damages the sentinel. Any of these narrows/refutes H1.

## Frozen disproof criteria and evidence

A valid installed-source court must (1) fix a SHA exact head and tree, (2) build a genuine r24 source archive, (3) prove normal compaction exact and source/sentinel immutable, (4) perform only one constrained stage-name substitution after `mkstemp`, (5) separately inspect outside sentinel contents, destination lstat/symlink type and target, and source archive SHA, and (6) preserve raw machine-readable observations and actual output physical samples. The court must never touch paths outside its own `TemporaryDirectory`.

H1 **CONFIRMED** only if: no-interposition PASS; intervened path produces a verified CMPCT archive via the outside sentinel; outside sentinel SHA changes; and the resulting destination is the substituted symlink. If the candidate refuses without modifying sentinel and destination, H1 is **FALSIFIED FOR THIS SOURCE**. Anything else is AMBIGUOUS/SEPARATE FAILURE. Do not call a green scientific CI product success.

## Limits and consequences

This is a deterministic adversarial boundary probe, not a measured spontaneous scheduler race, an external attacker privilege demonstration, a public Reader issue, or a claim that an untrusted user can replace `mkstemp` names in a sticky protected directory. Attack precondition is effective ability to replace entries under the selected destination directory (including another cooperating same-UID actor). That precondition must remain prominent.

No Reader/Builder/transactions source edits, benchmarks, format, version, released `main`, frozen tests, policies or Discovery STATE edits. J24I06/#723 remains product owner, J24I07/#724 and J24I08/#725 own platform work; this is an **independent same-source fault injection** focused only on staged name custody. If confirmed, hand source SHA/physical receipt to #723; prefer maintaining an open staging file descriptor and nonfollowing/inode-bound writes or equivalent verified private staging rather than duplicating compaction implementation.

Research classification only. Product promotion remains subject to the entire inherited correctness, portability, performance, resource, recovery and release contract.
