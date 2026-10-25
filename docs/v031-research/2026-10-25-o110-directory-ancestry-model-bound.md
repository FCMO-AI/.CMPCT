# O110 — directory identity is not stable exclusion from the source tree

**Status:** lower-rung architectural bound, **not a CMPCT product change**, **not a release gate**, and **not a new format claim**. 2026-10-25 UTC. Independent source-exact product context: O96 [#454](https://github.com/FCMO-AI/.CMPCT/pull/454) and O101 [#456](https://github.com/FCMO-AI/.CMPCT/pull/456). The latter already proved the same-inode reparenting defect in an installed Builder on Ubuntu/macOS. This note investigates the stronger *Linux openat2* idea without duplicating another Builder patch.

## Narrow question and frame review

Can replacing O99's dirfd-relative creation with Linux `openat2(RESOLVE_BENEATH | RESOLVE_NO_SYMLINKS)` guarantee that a physically pinned, initially external output directory **never becomes a descendant of the source tree** when another actor can rename/reparent directories concurrently?

**Exploratory answer: no, under that explicitly adversarial threat model.** The flags constrain traversal *relative to the pinned directory descriptor*, not the descriptor's ancestry in the wider namespace. A directory's identity survives rename. A kernel containment proof relative to `dirfd` must not be presented as a proof of separation from a different, independently movable source-root object.

**Why this question matters:** O91→O93→O96→O99→O101 repeatedly improves final-leaf, parent-fd and inode controls but cannot resolve a guarantee whose predicate depends on a namespace relation that an independent writer can change. This is a **frame-level boundary** rather than an invitation to add another `stat()` check. Stop iterating small ancestry guards without an explicitly changed threat model or a new atomic, OS-enforced exclusion mechanism.

## Mechanism and controlled witness

The script `tools/research/o110_parent_mobility_oracle.py` is an isolated research oracle: it creates only temporary synthetic directories. It opens a file descriptor to an initially external output directory, moves that **same directory inode** into the source tree, then creates a leaf relative to the held descriptor. A Linux x86-64/aarch64 arm uses kernel `openat2` with `RESOLVE_BENEATH|RESOLVE_NO_SYMLINKS` for the leaf and separately requires `../escape` to be rejected.

**Locally observed on Linux 6.18.55 x86-64** (exploratory prototype, source SHA256 `55d06240a07a5d8365dee272b67a4c86f66e840cd275879efe6f84f86ac856d9`, JSON receipt SHA256 `a67d735b865626edd604c2768354d41ad17ab386f9c9ee816096b7fdf4d849b3`):

- `fstat(dirfd)` retained the identical `(st_dev, st_ino)` across rename.
- `openat(dirfd, leaf, O_EXCL)` successfully created a file now physically under `source/moved/`.
- `openat2(dirfd, leaf, RESOLVE_BENEATH|RESOLVE_NO_SYMLINKS)` **also succeeded under the now-in-source directory**.
- `openat2` did reject a relative `../escape` attempt; **this positive kernel control must be retained**. It demonstrates that the resolution restriction works as specified, not that it enforces CMPCT's distinct source/output exclusion predicate.
- Synthetic source payload SHA256 remained `26b7e40be0bcf3e6667020b3acf6e07faa17585b21b2936305dd6c9ad3860b15` and was never overwritten.

The committed script is a cleaned-up reproduction route for this local finding; **it has not earned a hosted exact-head test or installed CMPCT product credit here**. Cross-platform actual Builder evidence comes from O101, not this kernel primitive. This is **post-observation explanation**, not fictitious prospective preregistration.

## Scoped reasoning (not a universal impossibility claim)

Assume A owns valid file descriptors to source/output and may run a finite sequence of path checks; B has legitimate rights to atomically rename/reparent the output directory between those operations or immediately after them. Suppose A promises both (i) successful publication via the pinned physical dirfd and (ii) that the resulting directory remains outside the source tree *regardless of B's concurrent renames*. B can reparent the exact inode after the last ancestry check, before publication, and can reparent it after publication as well. Descriptor identity is unchanged. Hence no **finite check-then-use-only** strategy establishes the stated continuous global-ancestry guarantee under B's powers. This says nothing about designs with stronger enforced permissions/ownership, mount isolation, adversary cooperation, or purpose-built atomic OS primitives; it also does not negate the useful O99 leaf/dirfd identity improvements.

Primary syscall behavior: Linux [rename(2)](https://man7.org/linux/man-pages/man2/rename.2.html), [open(2)](https://man7.org/linux/man-pages/man2/open.2.html), [openat2(2)](https://man7.org/linux/man-pages/man2/openat2.2.html).

## Decision and product architecture options

1. **Honest bounded contract:** guarantee non-destructive output-leaf publication relative to the physically pinned directory, and source exclusion at a specified initial/commit checkpoint under a **stable-ancestor or nonadversarial/cooperative rename assumption**. State this condition explicitly; do not silently claim global namespace immutability. Keep O91 FIFO/source clobber and O96/O101 counterexamples in the threat matrix.
2. **Stronger environment:** if arbitrary hostile concurrent directory reparenting really must be excluded, first design an enforceable capability/ownership/permission or mount-namespace boundary preventing B from moving the authorized root; then test that actual OS guarantee. Do not merely reread paths or substitute `openat2`.
3. **Re-evaluate necessary property:** distinguish original source bytes, output physical-object identity, original namespace placement, visible requested path, and exact archive reconstruction. These are separate invariants with different ownership and costs. Cross-filesystem Windows behavior, power-loss semantics and transaction durability remain unmeasured here.

## Falsification / next useful action

This conclusion must be narrowed if a supported OS primitive is shown to **atomically** bind *not-in-source* ancestry to publication despite an unrelated process with rename rights, or if the intended product contract no longer includes global namespace exclusion. The cheapest decisive future work is an explicit owner decision on which property needs continuous enforcement, followed by one integration court preserving all known O75/O78/O84/O91/O96/O101 safety semantics; not another stat/dirfd microvariant.

**Promotion:** none. No Builder/Reader code, codec, format, historical benchmark, evaluator, tolerance or threshold is changed by this note/script. Original O101 host evidence (Ubuntu/macOS) remains the product negative and O99 different-inode rejection remains a valuable positive.
