# O30 — Sealed source copy with ABA mutation: result and decision

**Date:** 2026-10-24  
**Status:** HOSTED SCIENTIFIC RESULT / NO PRODUCT PROMOTION  
**Repository:** FCMO-AI/.CMPCT  
**Preregistration:** [2026-10-24-copytime-source-aba-o30-prereg.md](2026-10-24-copytime-source-aba-o30-prereg.md), commit 6bda85f5791dbfe9a9b204cf5cbd266451ebe419 BEFORE experiment implementation.  
**Inherited exact parent:** PR #379, 5994dca7d4d9255a2ed7c6edf1669acf2422e2f1 (O26 sealed-source ownership).  
**Source-only experiment:** benchmarks/v031_copytime_source_aba_o30.py, Git blob 10ad731e4ae9ab695f68330ac059299079ef1435.  
**Initial hosted exact-source result:** Actions run 40134244226, SHA bb650e1c22320034bcb7d8ef0095824d3fb6c645, SUCCESS; original artifact ID 12576062481, ZIP SHA-256 00c30525d3a6ce604fba4b2768d3b985a182a7f6f166677b2959a036c6430fea.  
**Final documentation HEAD exact-run:** PENDING on this documentation commit; do not relabel earlier CI as final exact-head evidence until confirmed.

## Question, simpler control, and disproof

Can a Linux sealed memfd constructed by copying blocks from a mutable source be called an atomic image of that source merely because the source SHA-256 is identical before and after copying?

**Answer in this tested source model: NO.** The stronger simpler control remains an original whose bytes are trustworthy and immutable during the whole read/copy interval. Sealing a copied inode prevents later changes; it does not make earlier reads atomic.

Prospective falsification required two independently SHA-valid A/B revision-24 sources, identical length and physical CRC32, true separate-process interleaving, source A recovered on completion, H unequal to A and B, ordinary H CRC-tier decode succeeding, and explicit H verification rejecting for exact physical SHA rather than a parser/CRC error. Failing a control would not earn scientific credit.

## Method / independently inspectable controls

- Generate a 4 MiB deterministic RAW payload A and B containing a one-byte mutation at logical offset 1,400,000 plus four CRC-compensation bytes starting at 1,400,064. A 32-bit GF(2) elimination finds a correction that keeps B's CRC32 identical to A's, while SHA-256 differs.
- Construct two individually valid revision-24 archive sources from the independent physical generator v031_pack_physical_sha_court.archive_bytes, with original and materialized arguments matching separately for A and B. The logical index is the same; the physical blob header SHA commits to each complete payload.
- Copy A's first 1 MiB into a new memfd; a separate writer child rewrites the same-inode source to B. Copy its second 1 MiB; another writer child restores the source to complete A. Copy remaining blocks and apply F_SEAL_WRITE, F_SEAL_GROW, F_SEAL_SHRINK, F_SEAL_SEAL.
- Verify A/B complete controls, complete before/after-source SHA and inode/size, sealed copy exact bytes/fingerprint, ordinary Reader data, SHA verification error and before-publication refusal.

**Scope:** explicitly forced interleaving demonstrates an existence counterexample, not an exploitability or race frequency claim.

## Direct hosted observations

| Metric or decision property | Direct observation |
| --- | --- |
| A original archive SHA-256 | 45456c53be5b3379b5ec3cf7cd49f42d65fb302b53534ccb37c7b4ceae815f8d |
| B independent archive SHA-256 | dcb8d61ac00d2d086aaf2bfe3938bbf3054bd8f20e933b88ec28ae285befa8de |
| Sealed H hybrid archive SHA-256 | f474e3d4776c1b26754a2112015352997f492ebc4b9d58066ad140dec8d630fa |
| Source before and after | EXACT SAME SHA-256, matching original A |
| Source dev/inode/size | SAME |
| Source ctime before and after | CHANGED (no stat-based invariance claim) |
| A and B strong verify + extraction controls | BOTH PASS |
| Physical content CRC32 of A and B | 2,237,313,281 (identical) |
| SHA-256 logical A vs B | DIFFERENT, both precisely reconstructed |
| Ordinary H read | PASS; B logical bytes observed |
| H strong verify | REJECTED on physical SHA-256, NOT CRC/structure |
| H verified publication | REFUSED BEFORE DESTINATION CREATION |
| Source after ABA | VERIFIED AND RECONSTRUCTED as original A |
| H memfd post-seal write | REJECTED, errno 1 (EPERM) |
| Archive bytes | 4,194,760 |
| Copy bytes read and written | 4,194,760 + 4,194,760 |
| Minimum sealed memfd page charge | 4,198,400 |
| Writers | Two separate child PIDs, captured in artifact |
| Read chunks | Five: four full 1 MiB plus 456 bytes |
| Product source modification | NONE |

The independently downloaded ZIP SHA-256 matched GitHub's artifact digest. The archived o30-result.json contains both child PIDs, per-block SHA-256 digests, full source/archive hashes, CRC compensation and successful no-publication assertion.

H is neither of the valid A/B archive images. Its physical SHA header comes from A, but a portion of its payload comes from B. Its CRC32 remains consistent because A and B were deliberately constructed as same-CRC payloads. The genuine Reader's strong SHA verification catches the mismatch. **This does not show a verifier bypass.**

## Product/science separation and external control

**Product:** unchanged; no safe general extractor, whole-tree transaction, compression gain, bounded-memory advantage or release established.

**Science:** equal source SHA before/after plus unchanged inode/length cannot prove a multi-read copy represents one source generation in this mutable-source ABA model. A strong SHA on the actual copied content detects the tested inconsistent hybrid before extraction publication.

**Infrastructure/evidence:** hosted code installs the authentic CMPCT Reader and pins inherited Reader, physical generator, O23, O24, O26 and O30 Git blobs. No historical benchmark, format or evaluator changed.

Primary Linux semantics: [memfd_create(2)](https://man7.org/linux/man-pages/man2/memfd_create.2.html) describes the anonymous file that can later be sealed. [F_GET_SEALS(2const)](https://man7.org/linux/man-pages/man2/F_GET_SEALS.2const.html) specifies constraints on that inode AFTER seal installation, not atomicity of previously performed cross-inode reads.

## Strongest negative, alternative explanations, and accounting

**Source ctime changed.** A source-ctime-before/after preflight could reject this exact controlled run. Therefore O30 does not claim that all inexpensive source-change detectors are defeated. The falsified shortcut is specifically source-hash-equality (plus inode/length) interpreted as proof of atomic copy. A trusted immutable source remains cheaper and stronger under its trust assumptions.

An actor capable of rewriting both physical payload and its authenticated commitments can supply a different valid generation. The internal SHA is not a provenance signature. This one Linux/direct RAW test does not establish arbitrary race probability, cross-platform support, filesystem tree reconstruction, crash recovery, nor a broadly bounded storage model. The charged full memfd archive copy remains N bytes read, N bytes written, plus at least N page-rounded bytes memory-backed.

## Discovery decision, counterfactual and handoff

**Primary question:** DECIDED; the implicit atomicity claim is FALSIFIED by authentic revision-24 counterexample.  
**Concurrency collision:** NONE FOUND. #379 owns original post-copy sealing; #377 owns disk snapshot; #381/#383 independently own hardlink safety and are untouched.  
**Discovery policy:** NO CHANGE EARNED.  
**Shared state:** docs/discovery/STATE.json deliberately unchanged; staleable cache is not a lock.

**Prospectively recognizable counterfactual:** before promoting a complete-source snapshot, distinguish byte immutability during capture from byte immutability after sealing. A hash outside the interval cannot replace a true atomic source-ownership mechanism. O26 already warned about copy-time mutation; O30 adds a causal CRC-equal, SHA-exact witness rather than merely restating the warning.

**Next highest-value action:** choose product trust assumptions (immutable source throughout capture vs dynamically mutable adversarial source). If mutable input must be supported, compare bounded physical-owner verified staging against whole disk/memfd copies, accounting for source lifetime, complete I/O/memory cost, destination publication, recovery and metadata. A complete RAM-backed clone is not scalable to arbitrary archive sizes. Do not extend the same narrow ABA family without new decision-changing evidence.

**Disposition:** durable scientific negative, no product integration, no merge, no release; pivot to nonoverlapping product convergence or a genuinely different representation/information question.
