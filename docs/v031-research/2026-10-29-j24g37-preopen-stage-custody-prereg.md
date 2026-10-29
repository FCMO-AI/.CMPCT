# J24G37 — Pre-open POSIX compaction staging-name interposition

Date: 2026-10-29 UTC. Status: **PREREGISTERED CANDIDATE SCIENCE; NO PRODUCT CHANGE, MERGE OR RELEASE**.

## Exact authority and inherited evidence

Parent: #741, product-candidate HEAD `a2f4804c203caeb5d4b81c24456517fa2f398349`. The released `main` remains v0.30.0/revision-24; this experiment does not promote the candidate. #726 proved the closed stage-name overwrite; #740 proved a mode-0700 private directory can be renamed from an untrusted parent; #741 uses a pinned stage dirfd and a pinned archive fd and proved an **after-open** ancestor rename in two POSIX hosts.

Do not duplicate or edit the implementing #741/#738 branches. This child changes only its own research test, court workflow and dated result. `docs/discovery/STATE.json` is a stale cache belonging to other concurrent work.

## Question and prospective product-level prediction

Between `os.mkdir(candidate,0700,dir_fd=parent_fd)` and `os.open(candidate,O_RDONLY|O_DIRECTORY|O_NOFOLLOW,dir_fd=parent_fd)`, an actor with write permission to the destination parent can rename/rebind the candidate name. Does the **installed actual Builder→Reader→compact_archive** fail closed without modifying source, destination or an outside sentinel?

Four deterministic interventions, all under an isolated temporary directory:
1. Replace candidate with symlink to outside directory: `O_NOFOLLOW|O_DIRECTORY` should reject before payload creation.
2. Replace candidate with a fresh same-UID directory of mode 0755: opened but `fstat` mode must reject.
3. Replace candidate with a fresh same-UID directory of mode 0700: the *current candidate cannot distinguish its identity* from the original directory, so the operation may succeed. This is **negative scope evidence** (same-UID impersonation), not a proven secure ownership contract.
4. Replace candidate with a fresh mode-0700 directory containing `payload.cmpct`: exclusive `O_CREAT|O_EXCL|O_NOFOLLOW` must reject, leaving destination and outside unchanged.

Strong control: identical input without interposition, with authentic revision-24 Builder, Reader verify, physical SHA and logical/table comparison. Repeat on Ubuntu 24.04 and macOS 14 without rewriting any inherited evaluator.

## Prior knowledge and honest prediction freeze

A **local OS-primitive-only unblinded pilot** already observed fail-closed for symlink and bad mode, successful substitution for same-UID 0700 directory, and rejection of a pre-planted payload name on Linux. It is NOT product evidence and must not be described as prospectively unobserved science. This registration is prospective specifically for transfer into installed real CMPCT archive compaction and macOS behavior.

## Killer / alternative explanation / cost

Any outside sentinel mutation, source archive mutation, unexpected destination change after a rejected operation, unverified compacted output, or swallowed error is a hard falsifier of the relevant claimed containment. A same-UID 0700 directory that succeeds is NOT a universal security PASS, because the original inode identity is not proven; it narrows the candidate's threat model. A failure to interpose at the intended `os.open` boundary invalidates the instrument (no product conclusion).

The alternative is an actor-created 0700 directory with matching uid/mode, which the current checks cannot distinguish. Merely adding more mode/UID checks cannot prove freshness against same-UID parent writers. Fully closing that threat may require an unnamed inode, a trusted parent, an OS-specific handle/path publication primitive or an explicit trust boundary; do not implement a platform claim without evidence. A writer capable of changing destination after publication also limits the meaningful guarantee. No compression, speed, peak-memory, cross-platform Windows or power-loss gains are anticipated.

## Decision unlocked

Determine the exact pre-open attack boundary and whether #741 can honestly claim safety against **different-UID** writable-parent rebinding (subject to separately verified owner control), while marking same-UID impersonation as an unsatisfied invariant. If product transfer contradicts the OS pilot, keep it red and notify #741. If confirmed, preserve concise result and recommend a constrained threat-model statement rather than proliferating overlapping pathname fixes.
