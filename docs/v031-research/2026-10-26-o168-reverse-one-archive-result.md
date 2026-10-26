# O168 — Authentic macOS→Linux one-archive POSIX tree transfer (2026-10-26 UTC)

**Decision: NARROW POSITIVE — REVERSE-DIRECTION PORTABLE TOPOLOGY VERIFIED; STRICT CROSS-HOST PHYSICAL IDENTITY FALSE.** Research and independently installed product evidence only. No product code, format, release, benchmark or discovery-policy change. Prospective hypothesis committed before any implementation at `c3b20a5b7c3b0f0b694b939dc5a95d9852a729a5`.

## Primary question, source custody and original raw artifacts

Can one original macOS-built genuine CMPCT r24 binary be verified and extracted unchanged on Linux with the original O155 strict physical-tree oracle and O165 narrow portable projection preserving all fields except the physical mode of symlinks? **YES for the synthetic 10-entry supported POSIX fixture and exact tested source.**

- Base owner: [O165 PR #503](https://github.com/FCMO-AI/.CMPCT/pull/503) `9e9bb88e7a2c96749fbd27880f72517d9e975e67`. O168 [draft PR #505](https://github.com/FCMO-AI/.CMPCT/pull/505), [source-exact result-bearing hosted run 40296197914](https://github.com/FCMO-AI/.CMPCT/actions/runs/40296197914), code/workflow HEAD `faebb5865f9093dd1bd62c2feb3fa58d89a6257a`.
- macOS producer job `121482755904` **SUCCESS**. [Original macOS archive and source strict receipt artifact 12639230219](https://github.com/FCMO-AI/.CMPCT/actions/runs/40296197914/artifacts/12639230219).
- Linux receiver job `121485273352` **SUCCESS**. [Independent receiver full strict/result JSON artifact 12638417685](https://github.com/FCMO-AI/.CMPCT/actions/runs/40296197914/artifacts/12638417685).
- Original binary extracted from actual downloaded GitHub artifact ZIP independently: `original.cmpct`, **1,963 bytes**, SHA-256 `78b09deb2938a378a3e0dbcca74a2400be021695c1fae0c9a3d42ef780874580`, genuine magic `CMPCT24\0`. Exactly the same binary SHA and size were recorded by both independent host jobs; Linux original archive remained unchanged through verify/extract.
- Both jobs bind original unchanged Builder, Reader, original O155 strict witness, O162 fixture, and O165 projection. O168 requires original O165 instrument Git blob `2fb9cf5c9ecc072a0e692a64f21b6273f0b28fd6`; neither original research harness nor product changed.

## Actual observed physical and portable reconstruction

- macOS original strict digest: `2610ed72a12d168e46326a55273dd60fe532d90f616b0e025cbb02e2a3e6845b`.
- Linux extracted strict digest: `8e72d2b9273fe50b30a6bf84ee275d9250c339c48f26e17180d13f619ef60e94`.
- **Strict cross-host physical identity is FALSE**, as predicted. The *only* three actual strict entry-field deltas are physical symlink `mode`: `ln-dir`, `ln-file`, `nested/ln-nested`, all macOS `0755` to Linux `0777`. No changes in other entry fields, names, file/dir modes, content SHA, types, symlink targets, or hardlink equivalence partition.
- The original O165 portable projection discards **only symlink physical mode**, not link targets or any other field. Full source/receiver projected manifests and independently recomputed SHA-256 agree exactly: `0292ffc4d4e40d43c1d6e0cbd06616e5024b44403d6705fb9f4cadac50faeaa0`.
- Actual Linux restored owner/alias `os.path.samefile` hardlink test **PASS**. In the independent altered extracted tree, severing the hardlink while preserving member bytes/mode changes portable digest; after rejoining it, changing only a relative in-tree symlink target also changes portable digest. Both adversarial signals **PASS**.
- Linux `cmpct verify` and `cmpct extract` exit successfully against the authenticated transported artifact. macOS local same-archive strict source/roundtrip **PASS** before transfer.
- Independently downloaded both raw artifact ZIPs; rehashed physical original archive bytes and recomputed portable digests directly from source/receiver JSON; confirmed all three raw field-diff exceptions, identical semantic projected manifests and both hostile outcomes. A green workflow flag alone was **not** used as evidence.

## Disposition, negative boundary, inherited controls

The original [O165 Linux→macOS run](https://github.com/FCMO-AI/.CMPCT/actions/runs/40288932352) and this separate macOS→Linux result establish **two directional** examples of authentic same-binary cross-host topology portability in supported POSIX trees. They do NOT prove that strict physical symlink modes are identical, that the exact same archive is produced independently on different hosts, or that arbitrary filesystems, xattrs/ACL, owners, mtimes, sparse allocation, raw non-UTF8 names, NTFS, concurrency, crash durability, full product read economics, or v0.31 promotion are solved.

Both O165 original archive run-size observations (1,939 versus 1,935 bytes) are separately explained by a source-time/index delta in [independent forensic evidence on O165 #503](https://github.com/FCMO-AI/.CMPCT/pull/503#issuecomment-6412198564): all ten `mtime_ns` metadata values differed, physical 719-byte stored blob-data region was byte-identical, compressed primary index 542→540 B duplicated in tail explained exact 4 B archive delta. That is not a same-input compression-regression result and must not be conflated with O168.

Historical v0.30 custody/surface assertions in general CI were already red on [O165 final HEAD tests 40290142456](https://github.com/FCMO-AI/.CMPCT/actions/runs/40290142456) (4 failures). Do not weaken or silently green them. For O168 new final documentation HEAD, CI must be independently re-checked: this result-bearing hosted run applies to exact original code/workflow HEAD `faebb5865f9093dd1bd62c2feb3fa58d89a6257a`, **not automatically the later documentation commit**. No numerical r24/ZIP benchmark or CPU/RSS claim is earned.

## Decision, coordination and counterfactual

**H1 advanced for bounded POSIX source-exact installed-product reverse transfer.** Strict physical equality across operating systems is refuted. No concurrency collision or duplicate implementation: existing O155/O162/O165 owner code and branches unchanged; this work is an isolated child experiment. State cache `docs/discovery/STATE.json` remains owned by PR #440; no policy change earned.

Cheapest prospectively recognizable discriminator was to invert the *same binary transport* of O165 and preserve its two evidence tiers. It exposed no additional asymmetric defect in the tested scope; more repeats of the same toy tree are now lower value than generic held-out filesystem, source-custody, security, portability and actual product promotion work.

**NO FORMAT CHANGE. NO SOURCE PRODUCT CHANGE. NO MERGE. NO RELEASE.**
