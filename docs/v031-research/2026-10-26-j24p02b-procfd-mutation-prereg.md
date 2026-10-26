# J24P02b — same-UID /proc FD mutation boundary: prospective hostile court

Date: 2026-10-26 UTC. Additive hostile test after J24P02's original prospective no-clobber result. J24P02 base/result criteria are frozen and not rewritten.

## Pre-observed exploratory signal (not a prospective result)

After the J24P02 source was created, a local separate-process microprobe on Debian Linux 6.18.55 overlayfs showed that an unrelated Python child (no fd inherited, launched with close_fds=True) with the **same UID** could open `/proc/<parent-pid>/fd/<unnamed-O_TMPFILE-fd>` with `O_RDWR` and overwrite original bytes; this occurred under uid=0 and uid=65534. The unpublished file had `st_nlink=0` and the original parent descriptor remained open. This preliminary observation MUST NOT be misreported as prospectively validated hosted evidence.

## New narrowed question and prospective prediction

Can an independent **same-UID** Linux child on unprivileged Ubuntu 24.04 deliberately replace an entire ZIP's bytes through the parent process's procfs fd path after the parent has validated its O_TMPFILE data, yet before the parent calls J24P02's inode-bound `linkat`, such that:
- `linkat` correctly publishes **the original inode** at a previously absent name;
- the published bytes are nevertheless a *different valid ZIP* with the same member name `raw.bin`, same logical length, and independently correct CRC for attacker bytes;
- before/after `st_dev/st_ino` stay equal, so inode identity alone cannot prove content authenticity across this actor capability?

This is a **stronger actor** than O181's directory-entry-only adversary. It needs procfs access to the process FD under same-UID permissions, which may be denied by host ptrace/dumpability or procfs hardening. Do not infer that directory-only attackers have this capability, or that every Linux host allows it.

## Frozen negative/positive acceptance

1. Parent creates complete deterministic valid ZIP in O_TMPFILE, reads it via descriptor and checks expected member+SHA; records initial FD `dev/ino`, ZIP SHA.
2. Child launched with `close_fds=True` and explicit parent PID+fd path attempts `os.open(..., O_WRONLY|O_TRUNC)`, writes a **different complete valid ZIP**, closes fd, exits successfully.
3. Parent checks same original inode, confirms FD bytes now match attacker ZIP, and executes `linkat` to previously absent output; target must match same source inode.
4. Independent `zipfile` check shows a valid `raw.bin` whose logical bytes are NOT the authenticated original, despite identical logical length and valid CRC.
5. Assert original foreign-victim archive was never present or changed; test works with a private temporary directory and no external data.
6. If procfs access is denied, record clear **UNAVAILABLE_ON_HOST** and do not claim either universal security or a reproduced attack. Do not weaken the actor or exploit a local inherited fd to obtain green.

Prospectively expected hosted outcome: same-UID attack is reproducible. Its falsifier is denial of procfd open or inability to change the original unnamed inode. One observed host does not prove all Linux configurations.

## Product/architecture implication

J24P02's fd-to-name kernel operation addresses the *source pathname substitution* race for **absent destination**; it does not create an immutable source. A true same-principal adversary who can access and mutate open process fds can change the bytes while `st_dev/st_ino` remains stable. Fixing this threat model may require process/principal isolation, kernel file seals where suitable, or an enforceably narrower adversary model; a final readback hash without an atomic immobilization guarantee is still TOCTOU.

No CMPCT product code, release, source identity, historical results, comparators or Discovery Engine policy may be changed by this research episode.
