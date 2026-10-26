# J24F02 prospective falsifier — verified chunk extraction postcheck namespace custody

Date: 2026-10-26
Status: **PREREGISTERED BEFORE INSTRUMENT OR RESULT**. Scientific, not product code.

## Repository/ownership
Canonical `FCMO-AI/.CMPCT`; frozen base `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; authentic Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`. Independently authored revision-24 S_CHUNKS/S_CDC archive vectors: `tests/conformance/v24-chunk-maps.json` blob `91141405bb10b2e1226b0652e3aa0a13ba41846c`. Current shipping checkpoint v0.30.0, r24. J24F01 PR #486 independently established 28 static publication/corruption positives; it explicitly did **not** test concurrent directory swapping. O181 PR #514 established an analogous but separate ZIP-export final-name vulnerability. No active PR found owning the narrow **verified chunked extraction final-stage swap** question. This is a distinct independent negative/conformance court, not a competing patch.

## Primary question
Does the actual installed r24 Reader's `_extract_chunked_verified` successfully return while publishing an object *different from the staged, SHA-verified inode* if a directory writer substitutes its `mkstemp` name after full hash verification and before final `os.replace`?

## Baseline/mechanism and disproof
The real method writes and hashes into `mkstemp` fd, verifies indexed SHA, **closes fd**, then publishes by mutable stage *pathname*. A fully synchronized second process allowed to write the same extraction directory can rebind that pathname between close and replace. Hypothesis: destination becomes a valid regular file with **same length but different SHA**, `extractall(metadata=False)` returns success; the pristine archive and any preexisting destination not targeted are unchanged. Strong simple control: identical archive/Reader without substitution must extract exact bytes and SHA. Different plausible cause: injection harness might intercept the wrong `os.replace`, or fail due to OS path/permission differences; fail or classify inconclusive rather than claim vulnerability.

## Cheapest decisive court / prospective acceptance
Use both frozen Builder-independent S_CHUNKS and S_CDC archives on Ubuntu 24.04 and macOS 14 (separate jobs). Independently verify fixture archive SHA, installed Reader blob, authentic member logical SHA, source unmodified, regular baseline output exact. Deterministic rendezvous at the **real** `os.replace` boundary (instrument observes call, does not rewrite Reader), with a distinct child process replacing only the disposable private-stage directory entry with a same-length altered regular file. Before trigger confirm original stage inode and its byte SHA equals indexed member digest. Then allow the **unmodified** real `os.replace` to execute. Require apparent success plus destination wrong SHA and correct length to falsify final-publication authenticity. Preserve child exit code, actor UID, staged inode before/after and both hashes. Control any unexpected failure explicitly as `NOT_REPRODUCED`; never treat an infrastructure/test failure as an observed vulnerability. Optional symlink/foreign-inode attack only after primary case, never substitute for same-length case.

## Scientific decision
- `VULNERABILITY_REPRODUCED` only when both members on both POSIX hosts exhibit the exact successful-wrong-content signature and independent provenance checks pass.
- `HOST_SCOPED` if only one platform reproduces.
- `NO_REPRO` when unmodified Reader rejects or correct content survives with valid injection.
- `INCONCLUSIVE` for fixture/source mismatch or instrumentation failure.
No promotion or general exploitability claim. Other actors require write permission to the private stage directory and scheduling near final publication. Does not establish attacks without those capabilities or ZIP export publication behavior.

## Anti-self-deception / costs
This is a crafted deterministic race and not an estimate of spontaneous exploit probability. Byte/authenticity evidence, not performance. Current Reader may be vulnerable to preexisting destination symlinks and hardlinks through other paths; those independent owners are not part of this question. No release source, frozen benchmark, comparator, format, namespace policy or CI threshold changes. A positive result should hand off to extraction/path-safety owners, preserve existing static J24F01 positives, and require a physical namespace-ownership/publication architecture rather than another pathname check.

## Candidate selection / BONK
Exploit: real extraction physical integrity regression (chosen, high consequence, cheap two-host falsifier). Alternative proven-seed productization: J24S01 sparse-hole DEFLATE oracle is owned by #525; exact ZIP64 work by #521/#526; avoid duplicate. Worldview: kernel fd-vs-name publication ownership already demonstrated for ZIP; transfer same falsifier to **data extraction**, not implementation duplication. Baseline: preexisting J24F01 proves static only. Control: regular same-input extraction. Cost: negligible synthetic vectors and bounded subprocess; no 4GiB matrix. Next action if negative: retire narrow suspicion and return to another dependency-safe frontier.
