# CMPCT v0.31 — Windows cooperative Writer contention O4 preregistration
Date: 2026-10-23
Status: RESEARCH / NO PRODUCT OR RELEASE PROMOTION

## Source and ownership
- Exact tested product parent: PR #304 `fdb752b9e9ac72af74a44575b926e24ecacd812e`, stacked upon Reader×POSIX Writer PR #298 `2c8329276d875e0940db98551c70f329d7cecd57`.
- This branch owns only a separately runnable Windows contention court, its CI and evidence. It does not modify either owner implementation.
- Known tests: PR #304 Windows O3 8/8 PASS; Linux general 843 PASS, 8 SKIPPED; prior official r24/ZIP workflow skipped substantive ABBA because the final parent commit affected CI only. These are inherited results, not new findings.

## Primary falsifiable question
Under independent real Windows processes sharing one CMPCT archive, does the existing CRT `LK_LOCK` lease show quantized waiting and a finite retry ceiling when the owned sentinel is held for 0.3, 2.2, and >10 seconds? Does the blocked public Writer either commit exactly once after a released lease or fail explicitly without altering committed logical state? Crucially, a research PASS means the witness executed, **not** that contention latency is acceptable.

## Mechanism and predictions
- Parent obtains actual `_cooperative_writer_lease()` over a real revision-24 archive.
- Child process invokes public `append_rename()` and instruments the actual `msvcrt.locking(LK_LOCK)` duration without replacing its behavior.
- Parent releases after a measured interval counted from child's actual lock-attempt signal.
- Expect around one-second retry granularity for short holds, longer wall times for longer holds, and possibly an explicit acquisition failure before a >10-second held lease ends.
- After success, verify exact logical rename, original payload, and `CMPCT.verify()`; after an acquisition exception, assert original archive bytes untouched, then retry after release and verify.
- Preserve measured raw times, result/error type, Windows and Python details, process exit, archive SHA-256 and source custody.

## Alternative explanations and controls
- Startup process time is outside the measured CRT interval; use child instrumented call timing.
- A direct 0.3-second lock hold with and without cross-process contention separates startup and lock semantics.
- Existing O3 is stronger for multiprocess transaction correctness and remains in force.
- Do not treat 8/8 O3 green or same-source Linux suite as direct latency evidence.
- On release timing uncertainty (queue/scheduler), preserve measured actual times and classify ambiguous rather than threshold-garden.

## ABBA custody opportunity
- Open a stacked PR **against PR #298** (not #304), while branching from exact #304 and changing only tests/CI/docs. The existing official `.github/workflows/zip-parity.yml` classifies a latest-commit `tests/` change as in-scope. If run, the true GitHub PR base is PR #298 and the candidate's product code is byte-identical to PR #304.
- Require checkout HEAD, explicit base SHA, one immutable corpus, ABBA actual execution, and compare actual package/core source bytes. A green workflow whose performance job is skipped earns **no** ABBA evidence.
- The resulting new-HEAD performance receipt applies to the new source identity and to PR #304 *only by demonstrated product source equivalence*, never by treating hashes as equal.
- Do not modify benchmark thresholds, comparator or frozen historical releases to trigger a run.

## Kill/narrow/release boundary
- A lost rename, wrong filesystem state, format change, unhandled corruption or test harness false green is a correctness red.
- Quantized waits or finite explicit failure are performance/product-liveness debt; never present as acceptable unqualified concurrency.
- No Windows SMB/network or hostile non-cooperating Writer claims, no crash/power-loss extrapolation, no compression win.
- If hosted Windows execution cannot materialize, preserve the blocked question and strongest local/static checks, with no invented timing evidence.
- Release credit: zero. No merge; PR stays draft.
