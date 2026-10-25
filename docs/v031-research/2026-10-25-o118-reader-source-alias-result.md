# O118 — Reader self-archive inode alias: original-source destruction and static-guard repair

Date: 2026-10-25  
Status: **SCIENTIFIC RESULT — original baseline defect and candidate static protection CONFIRMED; product promotion NOT EARNED**  
Prospective preregistration: `docs/v031-research/2026-10-25-o118-reader-source-alias-prereg.md`, committed at `c78a8c3da6c23070f3204be833c0caabe6d6a5fe` **before** the candidate or court.  
Released v0.30.0 / physical r24 and canonical v0.31 integration branch remain unchanged.

## Source and question

- Canonical comparison base: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`.
- Original `src/cmpct/reader.py` blob: `e716233403dabd0966863c45635e18fa5ac6afb8`.
- Candidate `src/cmpct/reader.py` blob: `729ddc263f8d2d5ce2bbab7162461d19b0b2768c`, candidate code commit `559c306a1629cf0bb5bb02837a1511ef176597bd`.
- Full experiment-and-workflow HEAD: `b27f8c9dec2c07501067a58b60de824079fea871`.
- Test script: `tools/research/o118_reader_source_alias_court.py`.
- Hosted exact-head workflow: [Actions #40234346308](https://github.com/FCMO-AI/.CMPCT/actions/runs/40234346308), Ubuntu 24.04 **SUCCESS**, macOS 14 **SUCCESS**.
- Raw artifact Ubuntu: [#12614257339](https://github.com/FCMO-AI/.CMPCT/actions/runs/40234346308/artifacts/12614257339), SHA-256 digest `42b7830f6c15fb5e4010f95be2f2b19eadfaebfed80152845fb440cfbdb9a35e`.
- Raw artifact macOS: [#12614132455](https://github.com/FCMO-AI/.CMPCT/actions/runs/40234346308/artifacts/12614132455), SHA-256 digest `9b6738ec72f49a6a914daaed603da34dca1308935449cad29fa4779ae8117cd4`.

## Direct authenticated observations

One real `Builder(..., reproducible=True)` builds a single CMPCT archive from a deterministic 262,144-byte regular file. Each variant receives an identical independent copy of the archive and a separate disposable Reader process. Parent measures the **complete source archive SHA-256 after child termination**, independently of whether child returns success. A positive clean control proves content reconstruction; adversarial static output aliases are the exact same source path, a hardlink to the source archive, or a symlink pointing to the source archive.

Pre-extraction original whole archive SHA-256: `75ecb8ba31580d84971bd615c303813e6dfcbeb1674c16829c457e6d5b3b7958`.

When baseline regular extraction writes the payload through the archive alias, the source archive SHA-256 instead becomes `3c7aa75ecc04fc17ca6b5f4997b75f495de3f95eb8fc484c157296917b217a2a`.

| Engine | Input output leaf | Ubuntu behavior | macOS behavior |
| --- | --- | --- | --- |
| Original | Disjoint fresh path | Exit 0; archive unchanged; exact member output | Same |
| Original | Same archive pathname | Exit 0; **source archive overwritten** | Same |
| Original | Hardlink to archive | Exit 0; **source archive overwritten** | Same |
| Original | Symlink to archive | Exit 0; **source archive overwritten** | Same |
| Candidate | Disjoint fresh path | Exit 0; archive unchanged; exact member output | Same |
| Candidate | Same archive pathname | Explicit managed refusal, exit 47; original archive unchanged | Same |
| Candidate | Hardlink to archive | Explicit managed refusal, exit 47; original archive unchanged | Same |
| Candidate | Symlink to archive | Explicit managed refusal, exit 47; original archive unchanged | Same |

**16 independent process/case observations; original baseline 6/6 source-destruction negatives on aliased source, candidate 6/6 fail-closed and source-preservation positives, 4/4 disjoint reconstruction positives.** Both OS independent auditors accepted all eight required cells. The original source *reported success while destroying its own archive* for three alias kinds, so this is silent source integrity loss, not merely an availability edge case. No unsupported speculation about eventual mmap SIGBUS is necessary for the decisive result.

## Mechanism and alternatives

`CMPCT.extractall` previously used path-based `O_TRUNC` writes after only lexical logical path checks. Path names cannot establish physical inode identity, so a perfectly valid original CMPCT can be targeted for extraction by the same pathname, hardlink or symlink. The candidate checks the archive's actual **open descriptor** with `os.fstat` and checks every existing non-directory output leaf with `os.stat` (following symlinks) before constructing output directories or truncating/unlinking any leaf. If `(st_dev, st_ino)` agrees, it refuses.

A naive string-comparison rule fails hardlink and symlink controls. Snapshot-copying the archive would cost full-archive additional I/O/storage. Moving the check after `O_TRUNC` would be too late. An inode-bound output-opening architecture may be stronger and cheaper than repeated preflight checks but has not been proven.

## Strongest limitations, contradictions and debts

- **Static destination only.** An active attacker can replace an output leaf after preflight. This result does not establish race-free publication, safe handling of mutable ancestor directories, static symlink pivot coverage in general, or secure extraction of arbitrary untrusted trees. Separate PRs #269/#294/#297 and #459 retain their distinct questions.
- Original and candidate Readers are tested on real filesystem aliases in hosted Linux/macOS. Windows/NTFS, case-folded namespaces, network filesystems and mutated output ancestors are **unmeasured**.
- This is one authentic archive using the ordinary file storage selected by the Builder; the guard is syntactically located before any storage branch, but actual sparse/chunked/virtual ZIP/metadata interaction is **unmeasured**.
- New work costs **one `fstat` per extraction plus one `stat` per existing/non-existing non-directory leaf**. The full product wall/CPU, I/O, RSS and large-tree syscall inflation remain **unmeasured**. Eight focused subprocess durations (~0.06–0.08 s) are end-to-end test overhead and cannot establish performance superiority.
- The source/archive-loss defect is proven on the base Reader even though its child returned exit 0. The candidate prevents precisely these static aliases; it is not a general archive snapshot/failure-atomic repair.
- No numeric version, format mutation, merge, parity benchmark win or release credit was earned. General CI and official substantial performance gate are independent obligations.

## Concurrency and transferable observation

Search found no existing narrow owner specifically for **Reader output alias of its own still-open archive**. Existing work on external hardlinked leaf safety, Reader mmap external inode truncation and static symlink pivots remains orthogonal. No shared Discovery `STATE.json` was changed: its reconciliation owner is PR #440.

A generalizable prospective test: **any parser/extractor that writes destination files while maintaining a mapped or open source must first examine whether source and output can be the same physical object**, not just whether their pathnames look different. A complete input hash checked *after* apparently successful extraction is a cheap independent discriminator that would have exposed this case without waiting for SIGBUS.

## Decision and next executable frontier

**Candidate static guard: supported as a draft mechanism; NOT PROMOTABLE YET.** Next evaluate source-inode preservation under all relevant storage modes and destination publication policies, quantify added `stat` overhead on realistic large trees, and compare descriptor-bound output publication (including active namespace mutation) against this cheap static guard. Preserve exact old-archive read semantics, authentic recovery, direct competitor/parity controls and Windows portability. Promotion requires current final-head CI and relevant release evidence.
