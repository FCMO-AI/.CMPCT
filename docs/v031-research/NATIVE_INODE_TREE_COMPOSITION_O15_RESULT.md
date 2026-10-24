# O15 / O15b — Native public-C bounded inode-tree composition: definitive research result

Date: 2026-10-24 UTC. **SCOPED SCIENCE: POSITIVE. PRODUCT/RELEASE: NOT PROMOTED.** Canonical `FCMO-AI/.CMPCT` released v0.30.0 / on-disk r24 and separate `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b` remained unchanged at orientation.

## Original authorities, ownership and pre-result predictions

- Parent/ABI owner: [PR #349](https://github.com/FCMO-AI/.CMPCT/pull/349), native terminal hardlink owner ordinal source `611d0ea67a94f552f9ebca07ba747f191dee160e`. O13/O13b [PR #343](https://github.com/FCMO-AI/.CMPCT/pull/343), run `40086479175`, originally proved the old C ABI could not distinguish two otherwise observationally identical hardlink-owner graphs. [PR #337](https://github.com/FCMO-AI/.CMPCT/pull/337) independently owns bounded verified Zstd PACK batching and scalar streaming; no changes were made to either owner's product code.
- **O15 prediction frozen before implementation:** `docs/v031-research/NATIVE_INODE_TREE_COMPOSITION_O15_PREREG.md`, commit `3a47beb6ecdd06bd38d35da05cbffdfd9e4fad6f`.
- **O15b held-out prediction frozen before O15b code:** `docs/v031-research/NATIVE_INODE_TREE_COMPOSITION_O15B_PREREG.md`, commit `6791d06e308c35b5eaf311528e3ea893354a86ca`, after original O15 hosted PASS. Changes only the authenticated index-row enumeration, not source logical files or physical records.
- Isolated [PR #351](https://github.com/FCMO-AI/.CMPCT/pull/351) branch `agent/phased2-v031-native-inode-tree-compose-o15-20261024` stacks on the exact terminal-owner ABI. Added a test-only public-C client, independent Python POSIX oracle, two preregistrations and hosted workflow. **Product Rust/Reader/Python Builder/Writer/format/frozen benchmarks remain bit-identical to the parent.**

## Baseline and primary causal question

The O11 C client could reconstruct regular-file bytes but did not materialize source inode identity or literal symlink target relations; the historical pre-O14 ABI lacked terminal hardlink ownership. O14 exposed terminal regular-owner ordinals without guaranteeing client-side publication. **Can that new authenticated-index observable compose with operation-scoped verified shared PACK decoding and bounded streaming into source-exact flat POSIX file + inode + symlink reconstruction?**

A correct result requires a *filesystem structural* oracle (actual `lstat` device/inode equivalence classes + `readlink`) in addition to per-file SHA-256. A simpler byte-copy alias may pass SHA while losing hardlink identity, so it is not an adequate positive control.

## O15 initial hosted result (two genuine Builder trees)

- **Result-bearing commit:** `8a3d8c33e111ddb2490626a6f54c6eb6b8801b1d`.
- **Hosted run:** [GitHub Actions #40094327272](https://github.com/FCMO-AI/.CMPCT/actions/runs/40094327272), job `120873302568`: **SUCCESS**.
- **Raw artifact:** [#12559279789](https://github.com/FCMO-AI/.CMPCT/actions/runs/40094327272/artifacts/12559279789); ZIP SHA-256 `de72ad2233f1eabb989b90b52bc53f0be0de3ed323e165ac928a2d667ccab3cb`.
- Two authentic independently constructed Linux/POSIX source trees; each has **131 regular files, 2 source hardlink aliases and one symlink**. The linked owner varies between distinct-content `a.bin` and `b.bin`. Another same-content independent `a_copy.bin` must **not** collapse into the same inode class.
- Actual public-C output matches independent per-file SHA-256, every source `lstat` kind, exact source inode-equivalence classes and literal `readlink` bytes. **Each** tree executed one native SHA-authenticated Zstd physical-owner batch for **128 .txt members**, three scalar fallback reads, stage peak **98,304 B**, logical budget **102,509 B**. Not an oracle pretending a batch fired.
- Existing destination symlink pointing at external canary rejected **before** any source member was published; canary bytes unchanged and symlink entry retained. Cargo fmt/test, native release build, C `-Wall -Wextra -Werror` passed. No whole-tree atomicity or malicious concurrent destination protection claimed.

## O15b held-out, same-source signed alias-before-owner index

- **Source/preregistered test HEAD:** `1f9bcb72f5a948e495c07e1034be10dea398ac43`.
- **Hosted run:** [GitHub Actions #40094589404](https://github.com/FCMO-AI/.CMPCT/actions/runs/40094589404), job `120874142576`: **SUCCESS**.
- **Raw artifact:** [#12560521009](https://github.com/FCMO-AI/.CMPCT/actions/runs/40094589404/artifacts/12560521009); ZIP SHA-256 `9b931f0cc1d308a6a9ece2910d5d804d7c32fb6dcd023236d599b3b54a2d0b14`.
- Independent test reauthenticates both r24 header/footer compressed index copies and SHA-256 after swapping two **whole** index rows, placing `y_alias.bin` before `a.bin` in the native enumeration. Verifies physical records are *byte-exact unchanged*, all index rows form the same multiset, and signed archive digest differs. No source inode, logical data or fallback semantics are redefined.
- **All three** full native outputs (owner a, owner b, and alias-before-owner a-reordered) match independently constructed source bytes, literal symlink targets and the entire POSIX inode-equivalence partition, including the equal-content/different-inode control. Each executed **one actual Zstd batch / 128 grouped members**, **3 scalar fallbacks**, **98,304 B max staged output**; **131 regular, 2 hardlinks, 1 symlink**. The source index ordinal ordering did not impede this restricted C consumer.
- Hostile preexisting symlink/canary still **REJECTED before publication**. Original and held-out positive outcomes retain distinct preregistration times and source commits.

## Negative evidence, costs and adversarial self-critique

1. **No speedup claim.** This is correctness and actual batching applicability evidence. O7/O11 performance comparisons are separate, noninterchangeable measurements. Full process wall, CPU, RSS, physical disk I/O and official ABBA remain unmeasured for this new client. Max group-stage 98,304 B observed, cap 1 MiB; Rust's decoded/compressed buffers and runtime/index allocations increase total RSS beyond C stage.
2. **Not a production extractor.** Only strictly flat public ASCII-ish names, private empty root, Linux/POSIX, bounded member count/size and source totals. Existing leaves are rejected, but the client does not defend against a malicious concurrent process replacing the opened destination root or its intermediate descriptors, does not offer atomic publication or rollback, and a late I/O error can leave a partial result.
3. **Not a complete filesystem archive handler.** No nested trees, directory metadata, xattrs/ACL/UID/GID, special devices, sparse physical allocation fidelity, Windows/macOS path rules, large arbitrary files or source-mutation snapshot integrity. The native scalar RAW path's independent ranges do not alone authenticate an immutable logical source commitment.
4. **No external authenticity.** A SHA-authenticated CMPCT index is not a signed publisher identity.
5. **Inherited CI debt remains independent.** Original evidence-workflow fail due to PR dossier exact headings; corrected PR body without weakening evaluator, then an additional fail identified lowercase `disproof`/`quality-ratchet` markers; body was updated to restore both markers. Must observe new exact-head evidence status after this edit. General Tests historically include inherited source/fingerprint reds; do not treat a pending run or administratively successful but substantively SKIPPED official benchmark as a pass.

## Decision and next executable frontier

**SCOPED_O15_O15B_POSITIVE:** the information gap can be repaired by a minimal terminal-owner ordinal; in a controlled flat POSIX consumer, it composes with bounded, authenticated operation-scoped Zstd batching and scalar streaming to reconstruct byte-exact file trees with correct *inode identity*. The held-out preowner alias ordinal perturbation did **not** falsify the composability claim. This is a research capability / concrete productization seed, not a merged user feature.

The next high-leverage scientific/product step is **general safe destination publication and authenticated complete-file staging/recovery**, not additional PACK size or link-order variants. Reuse pre-existing Python descriptor-root/path-hardening owners instead of another unsafe independent general extractor. Compare a simpler control retaining Python's mature whole-tree semantics against any future native product architecture. No release, format, benchmark or Discovery-policy modification is earned.

### Evidence classification
- **Research / independent oracle:** O15 and O15b original hosted source-exact synthetic whole-tree cases, adversarial destination and index-order perturbation.
- **Product:** no product source changes or accepted mainline feature; terminal owner ABI remains draft parent PR.
- **Infrastructure:** exact-head specialized workflow cargo/Rust/C and raw artifact custody, pre-merge.
- **Unmeasured:** full product cost, cross-platform security, arbitrary-tree extraction, journal/recovery, official parity and numeric version promotion.

Counterfactual discriminator: Before writing a generalized native extractor, one *single* three-entry real inode-graph test plus a byte-equal independent inode control proves the ABI has sufficient topology information; and one authenticated alias-before-owner index-row permutation tests whether that information is usable independent of enumeration. This earlier prospective test transfers to other filesystem-native reconstruction clients. No evidence-backed Discovery-policy amendment is justified from this single composition success.
