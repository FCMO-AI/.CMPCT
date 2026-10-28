# J24H07 — Linux descriptor-owned hardlink source, prospective product court

**UTC preregistration 2026-10-28; status: BEFORE PRODUCT CODE; draft source-bound experiment, no release authority.**

## Authority, ownership, exact starting state
- CMPCT canonical published base `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0 / revision 24.
- Stacked implementation owner: #629 HEAD `22fb832777211a5aa19ccb1c9df54fa4714ff22f`, Reader Git blob `931545520b5a649903a8bdac4e9a1806bc38d58d`.
- #633 / science #632 J24H06 demonstrates a real Linux/macOS signed hardlink owner-path late substitution; Linux alias became a symlink with foreign bytes; macOS regular hardlink to foreign inode.
- Existing #557 Linux O_TMPFILE absent-leaf *destination* protection, #566 named-stage overwrite negative, #262 owner-first materialization, #401 Windows physical hardlink discovery, #504 Windows timestamp semantics remain authoritative and unchanged.
- This child branch claims only **Linux alias source inode binding**. #569/#609/#630/#634 Reader composition and performance, #574 discovery state, and #629 owning general Reader remain independent. Do not merge or update their branches.

## Prospectively falsifiable primary question
Can the real CMPCT Reader preserve the **created owner file descriptor** until each dependent hardlink is physically published, then use Linux `linkat(source_fd, "", parent_dirfd, alias, AT_EMPTY_PATH)` to avoid the J24H06 source-path substitution without changing signed archive bytes or existing normal hardlink/read/mtime behavior?

**Prediction:** under deterministic injection immediately before the real descriptor-bound `linkat`, replacing the owner **pathname** with a symlink to a distinct external canary after moving the original inode aside will leave the new alias linked to the original verified inode (same device/inode, original SHA), not the injected symlink or the external inode. The default `metadata=True` flow should still preserve valid original content, alias equivalence and mtime. The direct frozen #629 source-path control remains vulnerable (do not weaken/replace that negative).

## Stronger simpler controls and alternatives
1. Leave #629 unchanged: expected J24H06 negative. A second `lstat` is rejected because it cannot close inter-syscall substitution.
2. Re-open owner pathname just before alias: rejected because the attacker controls that lookup.
3. Keep an **fd from creation to aliasing**, using one owner at a time: avoid descriptor exhaustion, avoid source-name TOCTOU, and bind alias source to a pre-existing inode. Linux-only `AT_EMPTY_PATH` is genuinely kernel-bound, without assuming portability to macOS. Windows handle path is untested.
4. Delete/recreate from bytes instead of hardlink: forfeits hardlink physical identity; not a valid substitute.

## Cheapest decisive evidence ladder
- Local Linux kernel oracle as UID 65534: source swap; occupied alias EEXIST; root parent path swap with prior directory fd; unlink last source name => safe ENOENT; oracle evidence only.
- Host Ubuntu true installed Reader r24 archive Builder→Writer append_rename→Reader, unmodified signed bytes. Compare current #629 negative and candidate late source-path swap; assert whole output SHA, hardlink identity, external canary untouched and true Linux syscall. Test direct/S_BLOB, CDC/fixed chunk, sparse, alias chain and many independent hardlink owners where feasible.
- Host macOS/Windows original unchanged acceptance; candidate must not claim Linux mechanism is portable. General CI and full release parity remain separate.
- Charge complete bytes, CPU/wall, peak RSS, temporary I/O, open FD count and unsupported-filesystem behavior before promotion. No speed/ratio credit from narrow court.

## Kill and rollback conditions
- Any replay yields an alias to the foreign inode, a silently wrong inode, incorrect signed bytes, or unsafe fallback.
- File-descriptor exhaustion scales with number of hardlink owners rather than current owner; refused/original-consistent semantics required.
- Unexpected mutation to r24, Builder/Writer, Windows metadata, existing Reader source beyond owner linking; ordinary hardlink or chained alias failure.
- If `linkat` yields ENOENT when the owner's final name is removed, **fail closed**; do not fall back to source pathname. For unsupported Linux filesystems/kernel, fail closed with a capability diagnosis, not silent incorrect output.
- **Threat boundary:** correct bound source inode at alias publication under a name-only attacker. Does not protect against attacker who can write the owner inode itself or race final output after publication; nor does it solve mutable destination parents/overwrite, crash durability or unprivileged cross-OS portability.
- Preserve failures, opposite platform evidence, frozen controls, exact source SHA and no merge/release claims.

## Completion expectations
Create a narrowly scoped experiment with real source changes only if the above syscall controls pass, test the Builder/Writer/Reader on the same r24 source and run exact-head CI. Keep Discovery state unchanged unless decision-changing shared authority evolves; preserve original evidence and owner coordination. No feature/version bump.
