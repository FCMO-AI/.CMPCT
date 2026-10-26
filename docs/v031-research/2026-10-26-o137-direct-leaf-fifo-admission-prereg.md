# O137 — Static direct-output leaf type admission (preregistration)

Date: 2026-10-26 UTC. Status: PREDICTION FROZEN BEFORE SOURCE PATCH.
Owner: independent Phased3 narrow safety/convergence lane, stacked on O136 PR #485 at `44ccdc03f12538691f9df3465d5166a3cdc2ec19`; shipping CMPCT v0.30.0 / on-disk r24 unchanged. No canonical merge/release authority.

## Source-bound baseline and primary question

O106/O108/O121 established direct `S_BLOB/S_SPARSE/S_PACK/S_VZIP` Reader extraction hangs in a write-only open on a preexisting POSIX FIFO with no reader, genuine installed experiments on Ubuntu/macOS. O131/O136 inherit #269's static `_preflight_existing_destination_links()` before any member writes when `safe_symlinks=True`; its `direct_truncate` path rejects symlinks and multiply-linked regular leaves but **does not reject a preexisting FIFO**. Current Reader blob `5ce013f80c0220c7e7771041c60740a7111fff8a`.

Question: Can a single static nonregular-leaf rejection inside the **existing** prewrite preflight eliminate the preexisting-FIFO hang across authentic direct storage types without changing the safe atomic `S_CHUNKS/S_CDC` replacement contract, hardlink rejection, normal regular reuse, or `safe_symlinks=False` opt-out semantics?

## Predictions (prior to patch)

P1: Installed genuine `S_PACK` and `S_VZIP` originals, each with a regular reuse/fresh positive control, complete exact reconstruction; an existing FIFO is rejected promptly (within 5s) **before any archived member is written** while the FIFO inode/type and source archive SHA remain unchanged.
P2: Existing symlink-to-FIFO is still rejected in safe mode, and existing multiply-linked regular leaf continues to be rejected before writing an outside sentinel. No weakening.
P3: Atomic `S_CHUNKS/S_CDC` publication retains its existing FIFO leaf-replacement capability; the fix must apply only to direct-truncate `K_FILE` rows. No false refusal of existing regular destination leaves.
P4: A deliberately preexisting nonregular leaf in a **later** member causes a prewrite rejection that leaves an earlier sentinel unchanged; no partial extraction. All tests must be genuine installed product, killable child processes, with raw counts/identity.
P5: Canonical content/format, release gates, public benchmarks, historical lock and comparator thresholds remain untouched. Preliminary local tests are lower-rung until independent hosted Linux/macOS installed evidence lands.

## Mechanism / simpler controls / alternatives / kill

The existing `os.lstat` on all selected destination components already pays to reveal the leaf mode. For `direct_truncate`, reject `not stat.S_ISREG(mode)` before any `O_WRONLY|O_TRUNC` open; preserve current symlink/hardlink checks and atomic-output exception. Additional `stat()` syscalls should be **zero**; one branch per existing checked direct leaf.

Alternatives:
1. Write with `O_NONBLOCK` plus `fstat` after opening: more portability hazards, creation effects, and possible wrong-object races; static admission is narrower, not a TOCTOU solution.
2. Force `S_PACK/S_VZIP/S_SPARSE` into atomic staging: O75/O78 inode/xattr/hardlink semantics differ; higher carrying cost, needs separately owned architecture.
3. New independent preflight scan: duplicates existing #269 owner logic, unnecessary complexity.
4. Leave existing FIFO as explicit `safe_symlinks=False` opt-out: opt-out remains intentionally unsafe and cannot be misrepresented as protected.

Disproof: Any authentic direct-mode FIFO still hangs, any ordinary regular output is rejected, any `S_CHUNKS/S_CDC` unchanged positive is rejected, any outside sentinel mutated, any inherited test fails, or any additional silent semantic loosening. Do not rescue by altering original O121 negative court (which should still observe a hang on **its original Reader**).

## Concurrency, evidence, and costs

#269 owns original static symlink protection; #479/#482/#485 own composite Reader/evidence. This is an isolated additive stacked experiment with a preregistered distinct narrow invariant. Notify owner rather than touching other branches. `docs/discovery/STATE.json` is a staleable index owned by PR #440: do not race it. No discovery-policy revision, version bump, format rewrite, merge or release. Product gain is bounded to **static safe-mode** nonregular leaf refusal; post-lstat swaps and concurrent namespace races remain unresolved. Measure exact-head focused native-host courts first, then general CI and original r24 performance on same input before any promotion.
