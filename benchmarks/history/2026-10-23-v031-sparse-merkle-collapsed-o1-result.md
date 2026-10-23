# v0.31 — Collapsed Sparse Merkle O1: exact-head scientific result

**Date:** 2026-10-23 UTC. **Disposition:** `O1_COLLAPSED_MEMORY_HEADROOM_CONFIRMED`, **research-only / product credit 0**.

## Source, preregistration, immutable result

- Preregistered before the primary result at commit `37e7a7d984f4f16ab614295a8c6cc17927367699` (frozen blob `e461d74805358bdcf9729ec7863afcaf77cf8ca5`).
- Inherited O0 scientific owner PR #276, base exact source `5f7ed18e900240ca7f288c962066ad32f92c44da`.
- Exact resulting test source HEAD: `715474112a961cd82fea2abdaa6dd8a108f80372`; model blob `6e4ae0e5e04a741d7cfdc6b43d0cac5abc9ed5b0`; prereg and original O0 independent control source unchanged.
- Hosted O1 workflow [run 40009625388](https://github.com/FCMO-AI/.CMPCT/actions/runs/40009625388), job 120606342969, **SUCCESS**; [artifact 12525113449](https://github.com/FCMO-AI/.CMPCT/actions/runs/40009625388/artifacts/12525113449), artifact ZIP SHA-256 `8409214027c5f9b6a99a81a6952ec9d868fad8a248e004b15d56cddfbb9a3803`.
- Raw model result SHA-256 `760160aa92b6d4ad398b544bc672cc92eecc43bf0f80266829bb3f9d638e2d31`.
- Raw dyadic independent result SHA-256 `6ced448cc4c90b295ecd603f2cb303c7a90a5104997da18c5458ceb63c79d821`.

## Measurements actually obtained

Primary 640/640 full-array independent cross-checks passed (320 diverse files × leaf dimensions 4096/65536 bytes). The cold 1 TiB *logical* model with two data-touching 64KiB leaves produced the exact same root on creation and cold re-open of a **128-byte** hypothetical descriptor (48+40×2), used **263,396 bytes tracemalloc peak** during the isolated measurement region, visited **95 creator** and **111 cold** subtree nodes, and completed the scientific create+reopen timing scope in **0.001032464 seconds** on the hosted Python 3.11 process. This is *not* file creation or extraction time.

Independent posthoc dyadic run-fold replication was coded after the local candidate existed, so it is **not represented as a preregistered independent prediction**. Nevertheless, exact-head hosted reproduction independently folded sorted dyadic zero runs and 513/513 random/boundary/power-of-two differentials agreed with the recursive/cached model. Its 1TiB case needed **48 dyadic block pushes** and a **23-level cached-zero-subtree table**, also matching root identity.

Mutated raw leaf, proof sibling, trusted-root field, descriptor order/duplicate, index bounds and truncation were rejected by the specific controls. No full 1 TiB data buffer or full Merkle leaf array was constructed.

## Strongest negative and limitation

The same hypothetical 1 TiB file with every 64KiB leaf data-bearing would require `48 + 40 × 16,777,216 = 671,088,688 bytes` in digest-index rows alone, before payload, physical source extents, proofs, recovery, filesystem semantics or maintenance cost. Distributed/dense regimes remain hostile as in O0; collapsing zero subtrees does **not** solve general admission. A stand-alone remote selected-leaf proof may also require up to 32×height bytes of sibling witnesses: on the 1TiB example, 24×32=**768 bytes** per independently transmitted proof; the 128-byte index charge presupposes the verifier has the cold descriptor.

**Immutable r24 flat SHA-256 differs from the O1 Merkle root.** Source byte offsets and extents were gifted in a Python model. The resulting root/rows are only mutually consistent without an external trusted root; origin authentication is not provided. No Builder, Reader, CMPCT archive, full stored bytes, filesystem reconstruction, selection admission, memory RSS, hostile real archive, recovery, native/portable parity or product benchmark was measured.

A separate local Linux-only illustrative control found two 8MiB files with the *same bytewise SHA-256* while one occupied 8 filesystem 512-byte blocks and the other 16,384 blocks. This establishes that logical-content commitments alone do not prove physical allocation/hole structure. Source host filesystem and allocation behavior limit generality; it is not a hosted CMPCT product test. Linux fs-verity's authoritative documentation independently emphasizes checking hole-backed pages and binding file descriptors/root for verity: https://kernel.googlesource.com/pub/scm/linux/kernel/git/stable/linux-stable/+/refs/heads/master/Documentation/filesystems/fsverity.rst. Do not interpret this as identical root encoding to our candidate.

## Decision and next cheapest action

**O1 memory and exact-root hypothesis advanced; no product promotion.** The expensive full array was unnecessary on the 1TiB two-leaf example, and separately rooted small/large differential tests reduce but cannot eliminate model risk.

Next highest-value unclaimed fork is an **O2 charged physical-index/Reader design**: prove that generic source extent discovery, immutable hole positions, index serialization, cold verifier trust, selected physical byte work, RSS, temporary allocation and reconstruction semantics can be achieved under honest bounded economics. Start with a compact representation/ownership bound on mixed sparse and allocated-zero extents, before editing revision-24 code. Avoid another same-family synthetic speed benchmark unless the O2 fork cannot yet be decided.

No discovery-policy change is earned. No `docs/discovery/STATE.json` mutation due stale shared cache and concurrent agents. Full release/provenance gates remain independent.
