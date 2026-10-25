# O52b — hosted ancestor-symlink vs final-only O_NOFOLLOW primitive result (2026-10-25 UTC)

**Decision:** `FINAL_COMPONENT_NOFOLLOW_INSUFFICIENT_FOR_ANCESTOR_CONTAINMENT`. This is a *lower-rung POSIX kernel/Python primitive oracle*, **not** a CMPCT Builder source/product patch or a security guarantee about a complete extraction/creation implementation. The original O52 O50 genuine Builder findings are separately documented in [the primary O52 result](2026-10-25-o52-builder-poststat-source-pivot-result.md) and remain unchanged.

## Evidence and chronology
- A preliminary local Linux exploratory script (described openly in [O52b prereg](2026-10-25-o52b-parent-directory-fd-prereg.md)) had shown the general mechanism **before** formal hosted preregistration; do not treat that local sighting as prospective prediction.
- Cross-host replication question/disproof was recorded **before** hosted experiment source and workflow edits, in commit `87fdc2df2f608fc67e836de9b72efe4677943330`.
- Actual Python POSIX primitive test file: `tests/test_v031_builder_parent_fd_o52b.py`, source Git blob `e069fedd92df2d2ad904bfa85503333009008aaf`.
- Hosted replication: [GitHub Actions #40161280822](https://github.com/FCMO-AI/.CMPCT/actions/runs/40161280822), tested workflow/source exact HEAD `11cc7c33897207c8df4ac06bf60faa0fb317316a`, original source-exact O50 Builder remains `21a9ec696df13961c25301654feb607a7e161a4c`.
- Dedicated O52b JUnit checked separately from the original O52 four-case JUnit: original cases still **Ubuntu 4 pass; macOS 4 pass; Windows 1 pass / 3 skip** on this same run. The O52b primitive case is **Ubuntu 1 pass; macOS 1 pass; Windows 1 explicit POSIX skip**, no failed/error/skipped-as-pass misrepresentation.
- Original O52 + O52b combined on this exact head: **11 actual passing cases / 4 classified skips, zero failures/errors**, across all three hosts; **only two hosts executed the added POSIX primitive**.

## Direct distinct controls
Create trusted `source/child/data.bin` with `INSIDE_ROOT_REFERENCE_BYTES` and disjoint `outside/data.bin` with `OUTSIDE_ROOT_REFERENCE_BYTES`. Capture source root and child directory file descriptors with `os.open(O_RDONLY|O_DIRECTORY|O_NOFOLLOW)`. Rename the actual child directory out of the way, replacing its original pathname by a symlink to the outside directory. All file and directory operations use genuine Python `os.open`/POSIX syscalls; no CMPCT code or monkeypatch.

**Both Ubuntu 24.04 and macOS 14 observed all four:**

1. Stable, unsubstituted file opening with `O_NOFOLLOW`: `INSIDE`.
2. After parent replacement, opening the **final** `data.bin` component by absolute/pathname, even with `O_NOFOLLOW`: **`OUTSIDE`**; the final component itself was not a symlink.
3. Opening `child` relative to a trusted source-root FD with `O_DIRECTORY|O_NOFOLLOW`: **rejected**, `errno=20 (ENOTDIR)` in both hosts.
4. Opening `data.bin` relative to an already-pinned original child-directory FD: **`INSIDE`**, despite external pathname replacement.

Retained raw reports:
- Ubuntu job `121073275776`, [artifact #12585948772](https://github.com/FCMO-AI/.CMPCT/actions/runs/40161280822/artifacts/12585948772): 1 O52b PASS / 0 SKIP.
- macOS job `121073275838`, [artifact #12586157257](https://github.com/FCMO-AI/.CMPCT/actions/runs/40161280822/artifacts/12586157257): 1 O52b PASS / 0 SKIP.
- Windows job `121073275671`, [artifact #12585928972](https://github.com/FCMO-AI/.CMPCT/actions/runs/40161280822/artifacts/12585928972): 0 O52b PASS / 1 POSIX-only SKIP.

## Adversarial interpretation
A tempting **final-component** `O_NOFOLLOW` fix for the O52 Builder poststat symlink problem **does not provide containment against switched parent directories**. The strongest directly supported **kernel primitive** is descriptor-relative traversal with `O_DIRECTORY|O_NOFOLLOW` at each ancestor and stable held fd for final read. This does not solve in-place mutation of an already opened regular inode, hardlink rebinding, write concurrency, source root opened via untrusted ancestors, metadata/xattrs and deferred file reopening, or cross-platform Windows equivalence. It also does not show whether the proposed architecture is economically acceptable on complete CMPCT create workloads.

**Cheapest next owner-controlled product question:** Can O50 Builder scan once through a pinned trusted directory descriptor and read all r24 content paths (including sparse/CDC, nested ZIP/WHL, xattrs, symlinks, hardlinks, metadata) without reopening mutable untrusted parent paths, while preserving exact archive bytes for stable trees and keeping creation costs within the release gate? Split the multi-dimensional obligations into focused pre-registered unit demonstrations before broad product admission.

## Negative knowledge / Discovery Engine
The positive primitive result *rejects the simpler proposed final-only nofollow architecture* for a strong source-root containment contract. It does not change the Discovery Engine policy, state cache, release facts, or shared source. This can prospectively save an incorrect narrow product patch but earns no product correctness, performance, security-release or portability credit.
