# J24P02 / J24P02b — kernel inode publication is possible, but source content is not automatically immutable

Status: DECISION-COMPLETE SCIENTIFIC RESULT; neither experiment is a CMPCT product patch.
Observed 2026-10-26 UTC. Canonical release v0.30.0 / format revision 24 remains unchanged.
PR: https://github.com/FCMO-AI/.CMPCT/pull/523
Parent negative source: O181 PR #514 at `8b0735912eb6c8062b483ac9279c956294fbac3b` (O179 Reader candidate, not released).

## Exact provenance and order

- J24P02 preregistration commit **before instrument**: `de4b96c218bce63eae338de8b80c165ceba5f46a`.
- J24P02 instrument blob: `c11a0366da889525446a253df6eeeafcba13730f` at `research/j24p02_fd_noclobber_oracle.py`.
- J24P02b separately preregistered **before hosted hostile instrument**: `45bf3caf8d6b63984b23c4c464fcaa636e43ae35`.
- J24P02b instrument blob: `6799dd42d055ff30e7b379d9491adb1887f53019` at `research/j24p02b_procfd_mutation.py`.
- **Result-bearing HEAD for both hosted courts:** `15964cf402ca8b098fd4c94ecaf7b2d827f7aefc`. The final documentary commit is NOT assumed to have passed these results until new exact-head CI is observed.
- An exploratory root O_TMPFILE/linkat success **preceded J24P02** and an exploratory same-UID cross-process procfd mutation **preceded J24P02b**; both were disclosed before the corresponding hosted courts. Do not relabel either as prospective discovery.

## Court A — atomic absent-name link, not overwrite

Hosted Ubuntu 24.04, Linux `6.17.0-1022-azure`, unprivileged `uid=1001`.
Source-bound GH Actions: https://github.com/FCMO-AI/.CMPCT/actions/runs/40351180726
Original raw artifact: https://github.com/FCMO-AI/.CMPCT/actions/runs/40351180726/artifacts/12662254542
Artifact zip digest SHA-256: `4a27ba653ab3d6301c2d08d68516ee5a9bd916ecd324f365eba8886cfa14d243`.

Outcome: **6/6 specified cases observed; hosted SUCCESS; independent audit PASS**.

| Case | Observation |
|---|---|
| absent output | Source `O_TMPFILE` inode linked directly to previously absent destination via `linkat(fd,"",dirfd,leaf,AT_EMPTY_PATH)`; exact `st_dev/st_ino`, valid whole ZIP + member CRC/payload |
| regular already exists | kernel `EEXIST`, original bytes and inode intact |
| symlink already exists | kernel `EEXIST`, link and unrelated victim intact |
| hardlink already exists | kernel `EEXIST`, alias and unrelated victim intact |
| independent same-UID child plants new destination immediately before link | kernel `EEXIST`, foreign ZIP intact; no success falsely attributed to export |
| parent directory renamed between opening `dirfd` and linkat | new link appears in renamed directory inode, **not** under original expected path; exact source inode remains bound |

Complete ZIP SHA in absent case: `cffcf8b88efff702f014cdff34f700db52690be12718f8b869727bbb46ea52f4`. Fixed 64-byte member SHA: `9762e891b75e17d42f53c6ebfa83e904f9dfab7687e525a2b41a323d013fc474`.

Kernel primitive proof: **a source file does not require a mutable stage pathname to be atomically added at an absent target name**. It establishes one useful *create-only* capability. It does NOT handle overwrite of an existing archive, the ordinary O149/O179 goal. No vendor/runtime benchmark or CMPCT Reader test was performed by this court.

## Court B — hostile same-UID process can mutate unnamed source through procfs

Hosted on same unprivileged Ubuntu 24.04 runner class, uid=1001.
Source-bound GH Actions: https://github.com/FCMO-AI/.CMPCT/actions/runs/40351180505
Raw artifact: https://github.com/FCMO-AI/.CMPCT/actions/runs/40351180505/artifacts/12662069422
Artifact zip digest SHA-256: `deb87d244d5c16fb900f6e3cf677e2e7556e60d6e64d55d07042fb977c941b1c`.

Outcome: **NEGATIVE SECURITY BOUNDARY REPRODUCED; hosted SUCCESS means the attack happened, not that the product is safe.** The child was a separate Python process with no inherited descriptor (`close_fds=True`), and opened `/proc/<parent-pid>/fd/<fd>` with the **same UID**, `O_WRONLY|O_TRUNC`. The actor did not edit any directory entry. The parent had already authenticated its original complete ZIP before child execution.

The child replaced it with a different, complete ZIP carrying the **same member name `raw.bin`**, a **same-length 64-byte logical payload**, and a valid ZIP CRC for the wrong bytes. Parent then linked the original fd to an absent destination; inode `8941108` matched before and after, and `linkat` returned success.

- Original ZIP SHA-256: `cffcf8b88efff702f014cdff34f700db52690be12718f8b869727bbb46ea52f4`.
- Published ZIP SHA-256: `fbe139a2ffc8e43ca26164d40b9a0c5c871224ff5f523e7ef55d9085f8e27ba5`.
- Original fd inode = published inode; ZIP remains independently valid; content authentication is **FALSE**.

**Decision:** fd ownership solves *stage pathname substitution*, but **does not prove source bytes immutable under a same-UID process with procfs fd access**. This is a stronger actor than O181's directory-only attacker; do not conflate threat models. Namespace protection, process isolation and content immutability are separate properties.

## Independent checks and counterfactual lesson

- Linux open/linkat reference law: https://man7.org/linux/man-pages/man2/open.2.html and https://man7.org/linux/man-pages/man2/linkat.2.html.
- Procfs fd access depends on Linux permission/ptrace policy. The hosted outcome proves existence on the observed Ubuntu runner, not universal accessibility.
- Source-inode identity and archived-content authentication must be checked separately; a test only comparing `st_dev/st_ino` would incorrectly declare success in Court B.
- The fastest prospective discriminator for a proposed pathless-stage security fix is a two-axis actor matrix: **directory entry mutation vs. descriptor content mutation**. It would have identified this threat-model fork before full product implementation.
- Even a repeated SHA readback before a later syscall can be defeated by a strong actor who can write after verification. Content seals/authority isolation would require separate evidence. No such solution is claimed here.
- Current file sealing on Linux is typically restricted to memfd-style volatile objects; this result does NOT presume such objects can be linked into an arbitrary persistent filesystem. See https://manpages.ubuntu.com/manpages/noble/man2/fcntl.2.html.

## Convergence, debt and next executable fork

O179/O181 owners should preserve their original negative and positive evidence. The physically unnamed source experiment **does not authorize replacement of the O179 Reader**. It might support an explicit Linux *no-clobber* API only after genuine Reader integration, source/content guards, portability/fallback controls, kernel/filesystem support decisions, exact reconstruction, fault-injection recovery and whole-system performance evidence.

The highest-leverage remaining architecture question is whether a **non-attacker-writable source namespace** or stronger process/content ownership can provide existing-output atomic replacement *and* defend against the threat model a CMPCT deployment actually promises. Prove actor capabilities and parent pathname custody explicitly; avoid merely adding another path check.

No product source, on-disk format, version, frozen historical benchmark, release threshold, Discovery Engine policy or canonical `docs/discovery/STATE.json` was modified. No merge/release credit; CI statuses for the later document-only HEAD require exact-head read.

**Final classification: scoped Linux no-clobber capability POSITIVE; same-UID procfd content integrity claim FALSIFIED; general safe ZIP replacement UNRESOLVED.**
