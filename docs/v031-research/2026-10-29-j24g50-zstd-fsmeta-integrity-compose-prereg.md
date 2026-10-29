# J24G50 — prospective independent integration of signed fsmeta identity and zero-output Zstd integrity

**PRE-REGISTERED BEFORE COMPOSITION SOURCE MUTATION.** Date: 2026-10-29 UTC. Research-only stacked integration, no promotion/release authority.

## Authority, source and ownership

- Parent: #773 `agent/phased2-v031-j24g47-positional-fsmeta-rekey-20261029@893aac3f6b7b54e89d71af6970405ff5fc71aef7` owns signed journal positional `fsmeta` path identity and depth-64 Writer checkpoints. Preserve that code byte-for-byte.
- Donor: #767 `agent/phased2-v031-j24g44-zstd-zero-coded-physical-auth-20261029@be6d66ec86fd95942662e98902a72852c8510742` owns Python `native_codec.py` zero-output Zstd frame validation and borrowed input ownership, measured on three hosts. Transplant donor source verbatim; do not reimplement its mechanism.
- Their changed product-file sets do not overlap: #773 changes Reader/transactions; #767 changes `native_codec.py`. Reader uses `zd` which delegates to the donated native codec. This shared runtime dependency is the integration boundary.
- No changes to format r24, native ABI, thresholds, historical corpora, release locks, Discovery STATE, old tests or existing parent branches. Existing #777 (100k fsmeta replay), #775 (Reader rekey economics), #574 (Discovery allocator) remain separate owners.

## Primary question and mechanism

Can a single installed revision-24 CMPCT package preserve both independently observed fixes, without importing an incompatible codec and without reintroducing the signed metadata misbinding or zero-output corrupt-frame acceptance? The first credible control is the exact original source of each owner independently; a union candidate is meaningful only if both independent acceptance suites and a cross-boundary probe pass on one installed package and one exact Git head.

The cheapest *decision-changing* rung is a three-platform installed-package court with source blob identity, deterministic signed input, old suite controls, and independent on-disk audit for the Zstd frame. No full-product benchmark or version bump until that narrow composability question has survived.

## Prospective evidence / kill

1. Exact donor `src/cmpct/native_codec.py` Git blob must be `1dd853c111410726e051adc48ee59392a4cbd5fb`; parent Reader blob must remain `84f1c0602c7a9679cd79a0a5de984b169a467903`; parent Writer blob `3eef7fdc3f6deca5ddd6d9edf1292c7e2c864f11`. Any mismatch kills source-equivalent attribution.
2. The real installed Python+Rust package must have identical Python bytes to the exact branch checkout.
3. The unchanged donor `tests/test_j24g44_zero_encoded_python_codec.py` must accept valid empty RAW and encoded Zstd while rejecting both magic corruption and wrong decoded size, including dictionary paths. Exact signed physical archive cases must be independently audited by the donor auditor.
4. The unchanged parent `tests/test_v031_j24g47_journal_fsmeta_identity.py` must pass the file/transaction/checkpoint/malformed-ordinal state machine and genuine host xattr restoration where available; Windows is content-only for native xattrs.
5. A new integration-specific test must build one real archive with an ordinary xattr-bearing file plus empty content, cause an ordered journal insertion and ensure metadata ownership plus empty-file `verify()` and post-compaction exact content. This does NOT prove that the Builder emits a compressed zero-byte frame, which requires the donor's separately signed fixture.
6. Include frozen direct-codec and dictionary conformance vectors. A red is preserved; no test deletion, skip concealment, comparator semantics change, or host-failure-as-product-failure.
7. Source-exact CI runs on Ubuntu 24.04, macOS 14, Windows 2022 and preserves raw JUnit, SHA, package provenance and signed wire specimen on success/failure. Hosted CI is pending until actually executed; green is specialized integration evidence, not release promotion.

## Alternatives

- Merge either owner into `main` first: rejected, release checks incomplete.
- Implement another Zstd path or Reader remapper: rejected, duplicates two proven owners.
- Add tests only without combining runtime: cannot verify their interaction.
- Run the full parity matrix now: expensive and a weak discriminator of two specific hard correctness invariants.

## Losses and cost accounting

The donor byte-exact Python module is approximately 7 KB versus the inherited 5.8 KB; this is *source* size, not archive cost. Zero-output decoder obtains a 1-byte destination and borrowed encoded input, but complete process RSS and CPU remain unmeasured on the union. Parent rekey has inherited +0.50–0.77 ms (2,048 files in a separate research court) with different-source comparator; no new claim of product speedup. The union may expose unexpected ABI, dictionary, platform or reader dependency failures. Release target v0.31 and published v0.30.0 remain distinct. Original owners should decide promotion after exact-head full gates and peer review.

## Concurrency and handoff

One integration branch, no writes to owners, no overwrite of shared Discovery STATE. The parent head and donor blob will be reread before late writes. Notify both owners with exact HEAD and meaningful results. A failed court keeps draft unmerged with actionable failure artifacts.
