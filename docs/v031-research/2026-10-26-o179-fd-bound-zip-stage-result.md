# O179 — fd-bound ZIP staged writing, result and integration debt

Date: 2026-10-26 UTC. Decision-bearing scientific/product-candidate code at `09d423c23c1124e1569c96f91fcb5421711cf73c`; this note is a later documentation-only commit. Published release remains v0.30.0, archive format revision 24. PR #512 remains Draft; no merge/release credit.

## Pre-result prediction and provenance
Preregistration **before implementation** `5672cf11faf9430eef6fa70d39c56ac16be0b71c`. O149 donor `ca01d885fedc8ffc343b9c3c624eddd134158452`, original Reader blob `496e70bdc06ddc17aa90e4fc0e9f10a6bc5c5332`, repair Reader Git blob `9e399aa9cbc25c3d7b7c8663f5a039ade9d80aa7`, original independent r24 fixture Git blob `d10b7dab9126d39e819a74279c186363a163f2ef`. The exact source was installed outside the checkout and source Git identity was authenticated on all three hosts.

Question: Can O149 retain the original exclusively created ZIP stage fd during both direct Deflate and stdlib/fallback writing, so an attacker with directory mutation rights replacing the pathname before writer startup cannot overwrite an unrelated regular victim? Compare to O157/O157b negative original at PR #497. Preserve O143/O149 prior-output bytes and original O140 destination guards.

## Decisive hosted result
[Run 40316492157](https://github.com/FCMO-AI/.CMPCT/actions/runs/40316492157) at result-bearing exact HEAD `09d423c23c1124e1569c96f91fcb5421711cf73c`:

| Host | O179 + inherited O149 | Original O140 | Outcome |
| --- | --- | --- | --- |
| Ubuntu 24.04 | **9 PASS** | **24 PASS** | SUCCESS |
| macOS 14 | **9 PASS** | **24 PASS** | SUCCESS |
| Windows 2022 | **7 PASS, 2 POSIX-only SKIP** | Not run (POSIX-only) | SUCCESS |
| **Total** | **25 PASS, 2 SKIP** | **48 PASS** | **73 PASS, 2 SKIP, 0 FAIL** |

Four O179 cases on each POSIX host cover successful canonical fast ZIP, successful stdlib ZIP, adversarial symlink pivot and adversarial hardlink pivot *after exclusive creation but before stream writing*. The two pivots leave unrelated victim bytes/SHA untouched and the previously valid ZIP bytes/SHA intact, detect replaced stage identity, and remove the stage entry. Windows executes both successful ZIP routes and five O149 semantic cases; the two POSIX pivot injections are explicitly skipped, not credited on Windows.

Five inherited O149 acceptance scenarios per host include early RAW CRC failure, late second-member corruption, injected partial-write ENOSPC, successful fast ZIP + old hardlink preservation, and successful stdlib ZIP + old hardlink preservation. **Important transparent test-port:** original O149 fault-injection monkeypatch accepted pathname; the O179 stack changed the *private writer* interface to an fd-bound file object. On O179 HEAD, the single monkeypatch now calls `stage.write(...); stage.flush()` instead of `Path(stage).write_bytes(...)`; error type/predicate, partial bytes, destination SHA/inode and cleanup assertions are identical. Frozen parent original test blob `d394c1dd66eb229f5b24ccbd3713825f5e95cd89` is untouched; O179 ported test blob `13a0f79ca6a1a802a70bfd96cffe8b59d4b294ae`. First hosted [run 40315896117](https://github.com/FCMO-AI/.CMPCT/actions/runs/40315896117) recorded TypeError in the original monkeypatch, not an observed product regression. This failure remains historical evidence.

## Engineering mechanism and limits
The writer now uses `os.fdopen(original_exclusive_fd, 'wb', closefd=False)` and passes the file stream into either direct ZIP writer or `zipfile.ZipFile`. It holds the fd through close of the Python stream and checks `fstat(fd)` against `stat(stage, follow_symlinks=False)` before replacement. No ZIP archive/format or codec rules change, and no additional full-ZIP in-memory copy was introduced. This directly addresses **write-ownership** if the sibling entry is replaced before writing; it does **not** provide atomic identity binding at rename. A replacement **after** the final check still races with `os.replace`. On Windows the original stage descriptor is closed before rename due platform file-sharing constraints. Directory ancestor swaps, same-UID adversaries, remote filesystems, crash durability, owner/xattrs, transient ZIP-sized I/O and whole product economics remain unproven. Initial success is a scoped candidate, not complete data preservation under a hostile concurrent namespace.

## Exact-head CI, as-of 2026-10-26 11:40 UTC
At `09d423c2...`: O179 specialized three-host SUCCESS; Engineering Evidence [40316702604](https://github.com/FCMO-AI/.CMPCT/actions/runs/40316702604) SUCCESS; CI Topology [40316499085](https://github.com/FCMO-AI/.CMPCT/actions/runs/40316499085) SUCCESS; Version Discipline SUCCESS; R36 classification SUCCESS. Legacy O140/O149 workflows mark **FAILURE** solely due intentional historical Reader source blob pin mismatch against O179; the **authentic original functional controls** instead ran inside the new source-bound O179 court with 48+15 passes. General Tests, Native Core and Continuous Fuzzing were still running at this evidence cut; no conclusion is claimed. Performance workflow administrative SUCCESS but substantively SKIPPED; no RSS/wall/CPU/temp-I/O comparison or release credit. Re-query live exact-head CI before promotion.

## Decision, counterfactual and next target
**Decision-changing:** O157-class *pre-write stage-path swap* no longer changes an unrelated victim in the observed real installed Reader on Ubuntu and macOS while retaining O149 ordinary failure-atomicity in the three tested OS. Baseline and original O157 negatives remain valid for their source identities. The cheapest decisive prior discriminator was not adding `O_NOFOLLOW` (hardlink bypasses it) but recognizing the close/reopen of a uniquely created inode and adversarially swapping its pathname before write. This is a transferable design diagnostic; no normative Discovery Engine policy modification is earned.

**Next executable frontier:** reconcile full exact-head general/native/portability CI; target a **genuinely fd-bound or safely restricted publication primitive** that closes the residual compare-and-rename gap, or explicitly narrow the adversary/contract and demonstrate that constraint at API boundary. Then quantify cost, metadata and cross-platform behavior; retain surviving strong alternatives and avoid redundant implementation in O149/O150 owner branches. PR #512 is isolated and owner #492/#497 have a result link; no shared Discovery STATE.json write.
