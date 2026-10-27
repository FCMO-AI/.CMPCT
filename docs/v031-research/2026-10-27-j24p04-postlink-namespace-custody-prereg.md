# J24P04 preregistration — FD-authentic fresh-leaf publication versus post-link pathname custody

Date: 2026-10-27 UTC. Status: prospective scientific falsifier, **before new instrument**. This is a continuation of issue #528 / J24P03 #566's namespace-ownership inquiry, not an overwrite implementation or a second policy authority.

## Exact inherited control / scope
- Current source-exact parent #566 at `cba3636f7cbc28562908ef02cedb69ba11f98afa`, stacked on J24F12 #559 `dd723d128b5a020f154b4c9f7d37c6eedc929f24`; Reader blob `83c6600fa6cc951c1e6a136d239a39bb2c5d836b`.
- Inherited J24F11 #557 asserts fresh Linux `O_TMPFILE` plus direct `linkat(AT_EMPTY_PATH)` publishes the originally authenticated inode; it explicitly disclaims **after-syscall namespace mutation**. Preserve that positive property. Existing-leaf overwrite was falsified separately in J24P03.
- Only installed Python CMPCT r24 S_CHUNKS and S_CDC fresh-file extraction on Linux, with 0700 and 0300 output directories. All tests use independent Builder-free r24 archive construction and a separate same-UID process.

## One falsifiable question
Does *successful return of `extractall(metadata=False)`* imply that the destination pathname still resolves to the authenticated physical inode when an equally authorized directory writer changes the name **after** the kernel direct-fd link syscall but **before** the extraction method returns?

**Prediction:** absent actor, output's (dev,ino) and SHA equal the authenticated fd and indexed logical commitment. With an actor synchronized just *after real `_publish_unnamed_chunk_fd` returns*, but before the extract call returns, the actor can rename the just-linked inode to quarantine and create a separate same-length foreign inode at the destination name. `extractall` will return successfully because publication itself did no wrong; the final pathname will resolve to foreign bytes. The original authenticated inode and fd remain correct. This is a **temporal/authority boundary**, not a bypass of `linkat`'s source-inode authenticity at its linearization point.

## Independent controls, alternatives, and kill/narrow conditions
1. Source-identical package installed outside checkout; its Reader Git blob must exactly match the original fixed hash. Use the original J24F11 independent r24 chunk/CDC fixture construction, not a weakened local format.
2. Four no-actor controls (two storage kinds × two permissions) must reconstruct exact bytes and require final (dev,ino) == the inode observed inside actual publisher.
3. Four actor cases must use the unmodified real kernel publication first, then a **different PID**, same UID, to move the published inode and exclusively create a same-length foreign one at that name. Require quarantine still hashes to indexed SHA, original descriptor unchanged, and final path's SHA + inode differ. Assert method returned success.
4. The control uses an explicit synchronization point *only after* the real syscall, rather than asserting an uncontrolled exploit frequency. No `linkat`, `os.rename`, `extractall`, cryptographic or comparator monkeypatch replaces real behavior; a Python wrapper around the publisher schedules the actor after the actual syscall.
5. If any positive control fails, the actor cannot mutate as specified, or the genuine Reader checks/refuses publication after the actor, report the contradiction rather than claiming the prediction true. A genuine failure to keep the authenticated inode at syscall linearization would invalidate J24F11 and demand escalation instead.
6. Optional separated different-UID/sticky-parent exploration **not included**; cannot infer it from same-UID evidence.

## Decision scope and whole-system debt
A positive result would **narrow** the promise, not condemn anonymous-fd publication: the directly linked inode is guaranteed at the syscall's linearization instant, whereas a pathname subject to concurrent peers' write authority cannot be promised immutable through later observation or return without a stronger ownership/security boundary. Avoid labeling this as a novel remote exploit, byte corruption in the CMPCT archive, or a product improvement. No format, release, evaluator, workload, timing boundary or threshold may be changed.

Research evidence rung: authentic installed-Reader mechanism/hostile kernel test. Not a complete hostile-directory security proof; performance and cross-platform effects are not measured. A precise acceptance contract matters before engineering the still-open existing-target operation. Preserve raw negative/positive receipts on an exact Git SHA; no release or merge.
