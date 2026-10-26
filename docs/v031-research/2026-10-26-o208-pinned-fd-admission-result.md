# O208 scientific result — genuine CMPCT preflight/Reader source identity versus source immutability

**Date:** 2026-10-26 UTC  
**Decision:** `PINNED_INODE_BINDS_TWO_READS_BUT_NOT_SOURCE_IMMUTABILITY`  
**Evidence class:** Linux-only, genuine installed-source scientific verification; *no product repair or promotion*.  
**Parent:** O193 #521, `392112ce859db5a7f85be593c82d1cabc1f5131f`.  
**Preregistration:** `e8697fcfc0a9391069214dc53f37bd478a194689` (before instrument or workflow).  
**Product code:** unchanged relative to parent.  
**Result-bearing source HEAD:** `9892d8601937caa7241de8a3bc37aab4ba788c6d`.  
**Hosted court:** [GitHub Actions #40408031501](https://github.com/FCMO-AI/.CMPCT/actions/runs/40408031501) — one Ubuntu scientific job SUCCESS.  
**Original receipt:** [artifact #12690488507](https://github.com/FCMO-AI/.CMPCT/actions/runs/40408031501/artifacts/12690488507).  
**Research owner:** O208 PR #546. Existing preflight economics O205 #542, inconsistent sparse geometry #533, Reader implementation O193 #521 and mmap lifetime #460 remain independent authorities.

## Genuine experiment and independent controls

The instrument `research/o208_pinned_fd_admission_court.py` used the actual `Builder` to construct two distinct valid revision-24 archives, A and B. Both held one `payload.bin` member, of identical logical length but deliberately different bytes. For **both** archives it required successful unmodified `preflight_archive`, `CMPCT.verify`, full `read`, selected `read_range`, and differing archive SHA-256. It installed the actual package independently of source checkout and compared normalized installed Reader and validation bytes to the exact source Git blobs. All these assertions passed in the result-bearing workflow.

The experiment then executed three deliberately different source-custody conditions:

| Arm | Before mutation | Adversarial operation | Actual reader result | Conclusion |
| --- | --- | --- | --- | --- |
| Ordinary pathname | Strict preflight validates A | Atomic rename replaces pathname A with already-valid B | Reopened ordinary `CMPCT(path)` reads B; reader inode and archive SHA differ from preflight A | Two independent pathname opens **do not bind a single source identity** |
| Held-fd pathname alias | Original A opened with `O_RDONLY\|O_NOFOLLOW\|O_CLOEXEC`; both consumers use `/proc/self/fd/N` | External pathname replaced by B | Reader inode remains original A, full/read-range/verify return A; fresh pathname refers to B | Holding the descriptor **does** bind the original inode in this Linux scenario |
| Same-inode negative | Pinned Reader has loaded and verified A | Separate writable descriptor to *old A inode* modifies one header-magic byte via `pwrite` | Old inode unchanged but its SHA changes; fresh strict preflight rejects; already-open Reader still reconstructs A from cached index/unmodified blobs | **Inode identity is not byte immutability** |

The hosted job printed `O208_DECISION=PINNED_INODE_BINDS_TWO_READS_BUT_NOT_SOURCE_IMMUTABILITY`; an independently coded result-receipt step checked all required inequalities, inode equalities, negative outcomes, unchanged product source, and exact Git reader/validation identities. No evaluator was weakened.

## Why this is a decision-changing result

O205 established that performing strict preflight before opening a Reader is a plausible-cost approach on one genuine high-extent sparse archive, but identified a generic POSIX pathname replacement problem. O208 upgraded that warning to a **real CMPCT preflight-and-Reader source-identity differential** using Builder-authenticated archives, without editing product code.

The evidence separates two required protections:

1. **Same-source admission:** validating and then reading the *same effective bytes/index* without a pathname rebind. The Linux held descriptor experiment provides narrow evidence that inode pinning is feasible.
2. **Source-byte ownership:** preventing or detecting same-inode external modification of an already-open mmap-backed archive, and preserving recovery/extraction integrity under hostile mutation. The negative arm explicitly shows the held descriptor alone cannot provide this stronger guarantee.

Consequently neither `preflight_archive(path); CMPCT(path)` nor a portable-unproven raw descriptor façade is sufficient as a complete product security fix. For product convergence, apply existing strict geometry validation against the Reader's same admitted effective index/source, and separately define/defend the byte-mutation threat model with verified immutable ownership or appropriate fail-closed mechanisms. Costs must include any copied archive bytes, memory, I/O and recovery boundaries.

## Negative evidence, alternatives and scope

The replacement B in the ordinary-path arm was **valid** and passed the strict preflight; the experiment does not establish remote code execution, malicious sparse parser acceptance, or a CVE. It establishes mismatch between the source certified by a prior check and the source later consumed.

The pinned original A remained open while its header bytes were modified; the already-loaded Reader's successful logical `verify()` after that edit is not a claim that the complete physical archive remains valid. The strict preflight correctly rejected the changed header. This is a *different* notion of verification scope.

`/proc/self/fd` is Linux-specific. Not tested: Windows, macOS, hostile same-UID directory or file ownership beyond this bounded operation, actual sparse 4 GiB archive, full extraction/ZIP64, repeated latency, peak RSS, stage publication, same-inode truncation/SIGBUS, malicious recovery histories, full parser resource limits, and release gates. The scientific outcome is no license to add a Linux-only product implementation or skip future independent native validation.

The strongest simpler control (generic POSIX file replacement) had already been established by O205. A new nontrivial observation required running the actual Builder, strict parser and Reader together. A full private immutable copy is a credible alternative but exports full archive I/O/space and was not constructed or measured. Two path opens with a stat comparison alone are vulnerable to further races; not selected.

## Counterfactual and continuity

The cheapest earlier discriminators are (a) whether the preflight file description and Reader file description have identical `st_dev/st_ino`, and (b) whether archive bytes remain stable after that comparison. Only checking (a) would have missed the intentionally observed same-inode mutation. This is a transferable **experiment design** lesson; one activation does not justify changing normative discovery policy.

Owner follow-up: design a cross-platform same-effective-source validation and mutation/immutability contract within one Reader implementation, preserving historical recovery semantics; run the versioned adverse O198/O202 sparse vectors and genuine 4 GiB O196/O197 ZIP64 positives; compare true open/list/extract CPU/wall/RSS, failure atomicity, and hostile same-inode changes before any release promotion.

**No source code, version, format, frozen comparator, baseline, validator, Discovery cache, merge or release was changed by O208.**
