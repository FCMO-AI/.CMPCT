# O19b — Hosted Linux anonymous-stage ownership falsifier

Date: 2026-10-24 UTC. **Decision:** `ANONYMOUS_PATHLESS_BUT_SAME_UID_MUTABLE` under one Ubuntu Actions kernel. Independent scientific **host/infrastructure** result, NOT an integrated CMPCT product-extractor test and NOT an externally exploitable-vulnerability claim.

## Preregistration and temporal provenance
After the O19 stage-readback experiment, an unprivileged local Linux feasibility exercise revealed that a child under the same UID could reopen an anonymous `O_TMPFILE` inode through procfs and alter it. That local outcome was already known; O19b's [preregistration](NATIVE_ANONYMOUS_STAGE_O19B_HOST_PREREG.md), committed at `463e76096fcdd94d0255ad11caa8aad326efd960`, openly records it and prospectively predicts **independent Ubuntu-hosted replication only**. Do not call O19b a blind pre-result discovery.

Hosted source HEAD `109a133c6543fa7082840c708464afa06ff963be`. Dedicated [GitHub Actions run 40112069741](https://github.com/FCMO-AI/.CMPCT/actions/runs/40112069741) **SUCCESS**; artifact [12567151587](https://github.com/FCMO-AI/.CMPCT/actions/runs/40112069741/artifacts/12567151587), ZIP SHA-256 `1d0c796d1e3adc423b69df5f312066c1518d82cdb75d87577819a2c84948e897`. Independent download + archive SHA + raw receipt/byte assertion audit passed; `anonymous-stage.json` SHA-256 `3968932c6d0dd3ee472e471f079c606af2bb9a384cc42b2b79c2cacc2e87fdc5`.

## Actual host facts
- Kernel/host: `Linux-6.17.0-1022-azure-x86_64-with-glibc2.39` (GitHub runner), executing UID **1001**. This is a single kernel/mount/procfs configuration, not portability evidence.
- A parent process opened an `O_TMPFILE|O_RDWR|O_CLOEXEC` inode mode 0600 inside a private temporary directory, wrote `ABCDEFGH`, and called `fsync`. Directory contents before publication: **0 entries**.
- A **separate same-UID subprocess**, given the parent process's `/proc/<parent pid>/fd/<fd>` path, succeeded in `os.open(...,O_RDWR)`, wrote `Z` at offset zero, fsynced and closed; child exit **0** with marker `REOPEN_MUTATION_OK`. The parent's own FD then read back `ZBCDEFGH` (hex `5a42434445464748`).
- The parent called `linkat(...,AT_EMPTY_PATH)` on the anonymous inode. Return code **0**. Independently read final published bytes: `ZBCDEFGH`. **No stage pathname existed before publication**, yet the inode had been modified.
- The host workflow also reproduced the earlier O19 exact-real-CDC result in the same execution: two true Builder corpora × two clients × three fault positions = 12/12 preregistered decisions; 4 exact controls, 2 readback catches, 6 known injected corrupted publications. These are separate tests, not 12 O_TMPFILE cases.

## Scientific decision and strongest caveat
**Narrow negative confirmed:** pathname anonymity alone does not make an `O_TMPFILE` inode immutable to a separate process that already has **the same host UID and procfs access to the parent FD**. Merely substituting `O_TMPFILE` for a predictable named temporary file is not a full same-UID concurrent-mutator security guarantee.

This deliberately cooperative same-UID process received enough information to locate an open FD. It is not evidence that an unrelated, different-UID attacker can get into a properly permissioned private directory or procfs, nor that a normal disk spontaneously mutates committed data. Host security policy, restricted `/proc`, privilege boundaries, lack of FD exposure, mount capabilities, and platform differences may prevent it elsewhere. Conversely, an operator promising same-UID adversary isolation must explicitly establish that boundary or use a stronger ownership/publication model.

## Generalization and future action
The useful portable lesson is **separate name hiding from inode authority**. O18/O19's SHA barrier checks content at a particular time; a name-less inode narrows name-based attacks but does not automatically revoke same-UID FD/procfs access. In a general extractor, first define allowed concurrent principals, protect the source/archive FD identity, private work directory and output final namespace, then choose staging/publication primitives matched to that threat model and test the last mutation-capable boundary. Additional full readback adds `+1×` logical file I/O and one SHA pass, yet cannot by itself close O19's demonstrated `linkat` race.

Do not promote, merge, alter format/release/Discovery Engine policy, or claim any real CMPCT product performance/security win from this isolated host test. Leave shared `docs/discovery/STATE.json` untouched. This separate result is an infrastructure/proof-boundary input to future extractor architecture, not a new code path in released CMPCT.
