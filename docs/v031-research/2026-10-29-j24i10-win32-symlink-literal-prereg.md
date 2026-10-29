# J24I10 — Win32 symlink literal source-of-truth falsifier (PREREGISTRATION)

**Date:** 2026-10-29 UTC. **Evidence class:** prospective, source-installed portability/representation research; not a format or release change. **Owner:** independent adjacent test lane; no code edits to #723/#724/#725 or #726. **Base:** J24I08 [#725](https://github.com/FCMO-AI/.CMPCT/pull/725), exact commit `96989c923ed8a01f6cd6a6ca8bf69002a2409685`, stacked on J24I07 #724 / J24I06 #723. Released `main@80c358f8824ec1b20d349c92ed94c898090969b0` remains v0.30.0/r24.

## Observed baseline / why this is decision-changing

J24I07's installed three-host court records Ubuntu/macOS 4/4 logical fidelity, but on Windows fails **before creating the symlink archive** because its fixture demands `os.readlink(link) == target_argument` immediately after `os.symlink(target_argument,link)`. J24I08 fixed two independently observed Windows blockers (non-following mtime, staging fsync) and obtained exact 1,159-byte byte-identical plain compaction; its [host run #40809483598](https://github.com/FCMO-AI/.CMPCT/actions/runs/40809483598) still fails on that fixture. The failure might indicate a Windows pathname representation transformation, not loss of a CMPCT-authenticated literal. No captured requested/observed byte pair currently decides it.

## Primary scientific question

When Win32 exposes a symlink's **actual stored/read-back literal** through `os.readlink`, can the exact installed J24I08 Builder, Reader and private compactor preserve that observed literal, complete revision-24 indexed semantics and external-sentinel integrity? Does asking Windows to recreate that returned literal yield the same read-back literal?

**Hypothesis H1:** `os.symlink` may normalize an absolute target, and `os.readlink` is the authoritative *observed filesystem* literal for Builder. The pre-archive fixture equality to the caller's requested spelling is not a valid cross-platform invariant. After replacing this fixture-only assertion with a **stronger three-boundary byte-exact chain**—source `readlink` -> original archive `reader.read` -> rebuilt archive `reader.read`—compaction is expected to preserve source logical metadata and not touch any outside sentinel. No silent string normalization is allowed inside CMPCT.

**Strong simpler control:** on each host, create a second symlink with the *observed* target literal from the first, record both `os.readlink` outputs as byte strings, and compare without CMPCT. This directly distinguishes OS normalization/idempotence from archive product loss.

**Plausible alternative:** Win32 changes `os.readlink` again when re-creating a symlink from the already normalized string; or the installed Builder/Reader/compactor changes literal bytes or indexed metadata even if the OS readback is stable. Any of these is a real portability defect or a narrower unresolved contract, not a successful compaction.

## Preregistered experiment (no result at writing)

On Ubuntu 24.04, macOS 14 and Windows 2022, build the **exact installed #725 source** as a wheel and run one reproducible source-to-product test. Source SHA, installed module, OS/Python version, requested target bytes and observed target bytes will be recorded. Controls: a literal **relative** target to an in-root regular file; a parent-relative target to an outside sentinel; and an **absolute** target to that sentinel. For every case, archive source and destination hashes, physical bytes, `reader.verify()`, complete indexed rows, `_compaction_source_metadata`, source and rebuilt `reader.read('link')`, and outside sentinel integrity. A conventional public `extractall` must continue to reject unsafe absolute and parent-relative targets. Records shall survive failure, with physical archive witnesses when produced.

**Predicted if H1:** observed target may differ from caller-requested spelling on Windows absolute paths; source archive literal equals observed UTF-8 bytes; second filesystem link's readback equals observed; built-vs-compact archive target bytes and all authenticated metadata remain exactly equal; outside sentinel remains unchanged; safe extraction still rejects unsafe links.

**Kill/narrow:** any byte difference in source-observed -> source archive -> compact archive, any changed indexed metadata, sentinel mutation or unsafe default extraction acceptance fails; re-materialized observed literal mismatch narrows H1 and opens a platform representation issue even if archive source==output. The requested/observed difference alone does **not** fail, because that is the exact alternative to discriminate. Unsupported symlink privilege on a host is a host failure, not product success. No results are counted from source inspection or synthetic testing alone.

**Evidence tier:** hosted, genuinely installed three-OS product experiment (stronger than Python-only oracle); independently inspect original platform receipts and physical archives if provider artifacts are accessible. No full release benchmark, crash recovery, cold-open, true race or cross-OS interchange is claimed.

## BONK / convergence alternatives

- Change the original J24I07 assertion to ignore target mismatch: **rejected**, because it would erase real literal fidelity requirements without measuring archive semantics.
- Implement a new Windows symlink normalization helper in Reader/Builder: **premature**, because source truth and idempotence are unmeasured.
- Add a bounded independent test on #725 and then route the result to its current owner: **selected**; no duplicated product implementation.
- Work on J24I09 stage-name custody: **not selected**; #726 owns that narrower critical security question.

**Cost/debt:** constant-size three-link fixture, archive-create/compact per host, one extra re-materialization, no large data or new format. Existing scratch-tree materialization overhead, destination pathname races, crash/recovery and metadata portability remain separate debts. Any CI check that merely classifies or skips the court is not evidence.

**Decision unlocked:** distinguish a mistaken cross-platform fixture oracle from an archive representation defect; prescribe the smallest safe parent-test correction or a specific product repair, without weakening release/format/safety laws. No discovery-policy edit unless durable repeated evidence supports one.
