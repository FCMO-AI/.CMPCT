# J24H07 — Descriptor-owned Linux hardlink source: result and open gates

**UTC 2026-10-28; DRAFT PRODUCT CANDIDATE / NOT A RELEASE.** Immutable parent #629 `22fb832777211a5aa19ccb1c9df54fa4714ff22f`, published v0.30.0 / on-disk r24. Prospective hypothesis first committed at `05d227a32684e69d750c2758e24e2b870e5532c5` before any product code. No source owner branches modified.

## Primary question and causal baseline

[Original J24H06 #632 and issue #633](https://github.com/FCMO-AI/.CMPCT/issues/633) established that #629 validates a regular owner by pathname, then `os.link(owner_path,alias_path)` can bind the alias to a foreign inode after an attacker swaps the owner name. The authentic archive remains signed and verifies successfully. Linux published a foreign symlink; macOS published a regular hardlink to the foreign inode. That result is **unchanged scientific negative**, not evidence of any release defect in uncontended directories.

J24H07 tests a different ownership boundary: keep the file descriptor from the original materialization until the aliases of *that owner* have been linked using `linkat(AT_EMPTY_PATH)`. Restore basic owner metadata via descriptor; if the owner's public pathname is observably changed after linking, fail rather than return success. One owner at a time avoids holding thousands of owner descriptors.

## First hosted product result — exact old candidate, source-bound

[GitHub Actions #40621449216](https://github.com/FCMO-AI/.CMPCT/actions/runs/40621449216): **SUCCESS** on exact HEAD `af2164a3a9d221ab0b54bc37ff4efd6c67f44c52`, Reader Git blob `3abf6ff694b6d771da853b6d17f7180dc35b7772`, authentic installed wheel on Ubuntu 24.04 / Python 3.11. Original `Builder→Writer.append_rename→Reader` produced signed 1,095 B r24 archive; original unperturbed `verify/read/read_range/extractall(metadata=True)` succeeded, ordinary owner and alias shared inode and exact 5,080-byte SHA `a69bfe17aa9fa686e152e3fb6b344cb2236b5b434972b3fe5edd50eefdd1c23e`.

A deterministic hook immediately before the **genuine Linux fd-bound syscall** renamed the existing owner inode aside and replaced the public owner path with an external symlink. The alias was linked to the original displaced owner (identical device/inode and SHA), NOT the external 5,289-byte sentinel; the Reader **raised** `OSError: hardlink owner path rebound during materialization: 'b-owner'`. It did **not** report successful completion. The original signed archive and external sentinel SHA remained unchanged. Independent receipt referee passed. This supports *fd-bound alias source ownership plus observed fail-closed rebind in the bounded court*, **not** full hostile destination atomicity.

Same hosted run executed an independent synthetic broadness court: 26 physical owner+alias pairs (52 entries), including a genuine **S_CDC** 1,200,000 B dense payload and **S_SPARSE** 2,000,012 B sparse payload, all actual `linkat` calls, every owner/alias SHA/inode exact. Archive bytes: 1,204,908; first-court create wall: 0.014725208 s, extract wall: 0.006622051 s (single small trial, **not** comparative benchmark), fd baseline 8 / peak during link 9 (one additional descriptor, **not** a general peak RSS result). Result: 26/26 links and 26/26 physical hardlink-pair checks PASS.

## Linux micro economics — O0 only, unprivileged UID 65534

Separate local syscall ABBA on Linux kernel 6.18.55, N=200 links/method × 8 paired-order repetitions, reports **medians, not product speed claims**:

| Actual operation | Median µs per hardlink, local |
|---|---:|
| `os.link` path source | 10.03 |
| `linkat(fd, "", stable parentfd, alias, AT_EMPTY_PATH)` cached libc/parentfd | 9.92 |
| Same `linkat`, new parent fd each alias | 12.98 |
| Reconstruct ctypes/CDLL + open parent fd each alias | 30.00 |

These values are noisy and filesystem-/machine-specific. They do not prove product-level CPU or wall savings. They **do** identify an avoidable implementation cost: repeated `ctypes.CDLL(None)` construction and parent-dir fd opening dominate the initial helper in this micro. The candidate therefore added a lazy cached libc symbol and one current alias-parent fd (bounded 1), using fd-relative unlink and no-follow parent access; never an unbounded directory-fd cache.

The unprivileged kernel oracle also independently confirmed: a substituted source **pathname** cannot redirect an already-bound source fd; an occupied alias fails EEXIST without overwriting; an owner inode whose last named link has been removed fails ENOENT instead of unsafe fallback; a previously opened parent directory fd remains anchored after an ancestor path swap. These are narrow kernel facts, not Reader security claims.

## Latest candidate state and pending evidence

Optimized source Reader blob `fe0706ce00a425edb6572ff6cd2032f9be413468` was committed after the successful first court, followed by updated court signature and exact workflow source pin. HEAD **at this document's creation**: `3f63622e7844389b43c3b02f75d8d1a4e68074c3`. **A successful previous HEAD does not automatically approve this optimized HEAD.** Its hosted exact-head court, inherited General Tests, three-host Windows/macOS controls, user-visible installed extraction, CI topology and release parity must be checked separately. All fail labels / historical checks remain as returned; no fixed test source identity is silently rewritten.

## Losses and scope

**Still not solved:** arbitrary concurrent modification of destination ancestors/leaf after return, same-user attacker writing directly into owner inode, safe existing-target replacement, all POSIX filesystems (ENOSYS/EOPNOTSUPP/ENOENT policy must fail closed), Windows user-mode handle publication, macOS equivalent supported source-fd hardlink API (Apple DTS: not available), crash recovery, late-stage metadata races, native ABI/product release and complete CPU/wall/RSS/temp-I/O economics. In this current hostile test the extraction can leave **partial output** after it raises; no guarantee of cleanup was established. The normal uncontended three-host #629 court remains separate; its historical failure source fingerprints are not softened. A post-publication second path check does not make an adversary-controlled directory safe forever.

## Decision, counterfactual and next action

The decisive discriminator was **owner inode source** rather than another pathname check. The earlier evidence from #557 proved fd-bound *destination* publication and #566 retired named-stage overwrite; neither answered hardlink source binding. The new Linux implementation solves a narrow observable without claiming the whole tree. No evidence-backed process policy change is earned; `docs/discovery/STATE.json` is unchanged.

If optimized exact-head CI survives, carry source-bound hardlink owner mechanism to #629/#569 review; next cheap disproof is an independent process mutating the destination namespace while many sibling aliases are being published, plus actual test of parent-ancestor and owner-inode mutation, with conservative failure/rollback. Before promotion, measure worst-case memory, fd count, syscall/CPU wall and full r24 parity, and preserve exact signed-file semantics. Do not merge on this scientific court alone.
