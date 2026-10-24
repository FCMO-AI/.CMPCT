# CMPCT v0.31 Windows wait-capable lock O5 — prospective preregistration
Date: 2026-10-23
Status: independent research primitive / no product implementation or release credit.

## Exact source and negative trigger
Product source PR #304 fdb752b9e9ac72af74a44575b926e24ecacd812e. Writer blob fd8d922ae5a6e77ab7e01bf599da16a14aca1cff; Reader c548a2ae4d650e928eb46ed1c2431423e49765b5.
PR #309 hosted O4 run 40050047296/12542908507 found CRT LK_LOCK waited 1004.117 ms when hold=302.547ms and 3019.061 ms when hold=2193.715ms, and failed explicitly Errno 36 after 9089.882ms for parent hold=11300.517ms (zero data corruption, successful post-release retry).
Windows LockFileEx official synchronous contract: https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-lockfileex. Omitting FAIL_IMMEDIATELY on synchronous handle should wait for lock or error. Far-offset locking beyond EOF permitted.

## Primary falsifiable question
Can kernel32.LockFileEx acquire the exact 2^60 far-range byte on an independent Windows process after the existing CRT LK_LOCK holder releases, with accurate (non-quantized) wait and without the inherited 9s retry ceiling, preserving ordinary CMPCT Reader access and physically unchanged archive?

## Cheapest decisive experiment
Use a real installed CMPCT revision-24 Builder archive. Parent holds product _cooperative_writer_lease (genuine CRT), child opens separate fd and uses ctypes LockFileEx on that fd with initialized OVERLAPPED offset 2^60 and size one byte, no FAIL_IMMEDIATELY. Child timestamps call entry/completion, parent holds 0.3s or 11.3s starting only after entry, records pre-release time, then unlocks. Exclusion: success must follow parent release. Reader verify during parent lease; bytes/size SHA must remain identical. Child unlocks exactly once and closes fd.

## Kill / stronger controls
Kill or narrow if attempted lock succeeds before parent release, fails after release, hangs after bounded parent release, blocks Reader, changes bytes/EOF, violates source identity, or cannot execute on hosted Windows. An actual observation is not a production guarantee. Existing CRT O4 is the incumbent; LockFileEx result is primitive evidence only and cannot itself earn performance/release credit. Distinguish child spawn time from kernel lock time.

## Alternatives and costs
LockFile with immediate failure does not solve liveness; pathname sidecars fail hardlink identity; altering PR #304 before proving a primitive would duplicate owner work. Focus on exact kernel interoperation, report negative as-is. No new codec, archive representation, product ABI, benchmark comparator or release metadata. No SMB, reparse, uncooperative writer, Windows variants, power-loss claims.

## Coordination
PR #304 owns Windows Writer, PR #309 owns independent O4 and ABBA custody, PR #240 owns discovery state. This branch modifies only its own research test, workflow and preregistration. Preserve scientific/prospective evidence in GitHub for later zero-history agents.
