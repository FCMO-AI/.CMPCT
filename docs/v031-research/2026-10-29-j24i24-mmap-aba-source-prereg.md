# J24I24 — shared-mmap ABA source witness for bounded r24 relay (prospective)
Date: 2026-10-29 UTC. Source: #746 exact `ef83fe091509b07908646cd048278def715200b2` (J24I22). Public main v0.30.0/r24 unchanged.

**Research-only; no product, format, reader, builder, comparator, or release edit.**

## Primary question / decision
Does J24I22's two full-file SHA-256 observations plus pre/post fstat(dev,ino,size,mtime_ns,ctime_ns), combined with per-record CRC/SHA, imply that the emitted archive is semantically identical to one authenticated source state when a same-permission writer can mutate physical content through a pre-dirtied MAP_SHARED mapping?

**Predicted causal counterexample (not yet tested against installed CMPCT):** pre-dirty writable mmap before baseline fstat, read initial A index and whole-source SHA, temporarily replace one direct RAW blob header+payload with an independently self-authenticated equal-length B, have unmodified relay read/copy B, and restore A before the final fstat+SHA. Linux mmap writes after initial dirtying may not change mtime/ctime (a *local OS-only pilot* already observed unchanged stats across repeated A/B writes). If the relay succeeds, input pre/post SHA and file-stat witnesses equal while output carries B payload but index file-row signed logical SHA remains A. Require independent CMPCT verify() to reject output. This would falsify the *strong* immutable-source/snapshot inference, not the relay's narrower already-declared safety scope.

## Controls
1. Clean A, no attacker: relay succeeds, exact original physical wire on a single-blob full checkpoint, Reader.verify succeeds.
2. Persistent mmap B without restore: full-source end SHA differs and relay rejects, no destination published.
3. ABA mmap B during physical read, restored to A after unmodified verify_record: potential false acceptance with unchanged stat and source hash, destination published with file-row logical SHA mismatch.
4. Stronger conventional pwrite A→B→A, if platform ctime changes: fstat should reject. Observe but do not force environment-dependent outcome.
5. Independent physical parser validates the B blob's CRC32 and SHA-256 and detects row-hash mismatch; do not call malformed compressed bytes a successful attack.

Test uses *exact installed #746 research helper*, temporary single-file r24 RAW archive built independently of Builder, and deterministic nonconcurrent hooks placed only at source mutation timing. Do not patch production or test algorithm; the hooks only orchestrate an adversarial writer's scheduling. The source path remains regular; no privileged timestamp manipulation. Pre/post source bytes and SHA must be identical, and output B must differ from original A.

## Disproof / scope
If the relay rejects ABA, if source timestamps change, if output does not contain a complete valid B blob, if the final SHA changed, or if source bytes are not restored: mark the strong hypothesis unsupported/invalid on that host. Linux is initial scope; MAC/Windows not assumed. Same-process mmap test models a writer with write permission; not remote exploit or real-world race probability. Fingerprint pre/post equality is not a transactional snapshot unless proved. Reader/Builder product integration and collision with #741/#745 remain out of scope.

## Evidence and economics
Begin with exact fstat/data invariants and independent fixed-vector parse, then hosted Ubuntu 24.04 installed-source test. No whole-product timing, storage or promotion credit. Expected maximum <64 KiB record and small test RSS. Store raw case identities/results and git source identity in workflow artifact. Repeat without weakening the oracle if the first run conflicts with the prediction.

## Concurrency
#746 owns streaming FD relay implementation. #741/#745 own publication. This branch modifies only separate test, prereg, CI, and result notes. Report negative to #746 without overwriting its code. Discovery STATE.json and frozen benchmarks stay untouched.