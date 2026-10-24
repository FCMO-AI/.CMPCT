# POSIX byte-namespace O1 — local materialized-tree result and decisive negatives

**Scope:** 2026-10-24, synthetic Linux/POSIX detached research only; [preregistration](2026-10-24-posix-byte-manifest-o1-prereg.md) before implementation; PR #329 stacked exclusively on O0 PR #254 exact parent `2f256fe79785803a58c62e3422b226c4a747b888`. No revision 24/25 implementation, Reader change or product/release claim. GitHub-hosted result is not recorded as green here until exact-head court is inspected.

## Primary question and outcome
Can candidate versioned byte-aware name grammars reconstruct more than individual strings — a *real filesystem tree* — without silently changing POSIX identities? **Bounded positive in small synthetic trees, not a generic safe decoder.** The independent oracle compares raw byte relative paths, regular file bytes, modes, symlink targets, hardlink inode-equivalence classes, and xattr raw key/value pairs after materialization. Both typed-key and escaped-string representations pass the positive trees locally under UTF-8 and actual ASCII filesystem encoding. A separate held-out path-length court demonstrates a fundamental materialization limit of absolute path joining.

The key **negative** is that the initial detached reference's target-aware admission is incomplete. Exactly authenticated metadata can still describe (1) a symbolic link whose *target* is not portable to an announced casefolding destination, and (2) a hardlink alias with xattrs contradictory to the same underlying inode's owner. The reference preflight admits both. They are research-model faults, **not evidence of an unobserved CMPCT shipping defect**. Both are preserved explicitly as falsifiers rather than changing the evaluator to get a green result. The new reference model is therefore **not promotion-eligible**.

## Direct local observations (not hosted/head-qualified product evidence)

Same-content and same-tree detached MessagePack+zlib-9 packets; each result includes the 32-byte detached commitment, compressed metadata **and all source payload bytes**. The compressor's global payload context makes this a *standalone surrogate archive*, not CMPCT storage.

| Source cohort | Physical entries | Typed complete detached bytes | Escaped complete detached bytes | Decision |
| --- | ---: | ---: | ---: | --- |
| Mixed raw names / xattrs / links / Unicode aliases | 14 | 805 | 853 | Typed saves 48 B (5.63%) in this tiny model; not a product win |
| UTF-8-valid but host-normalization-colliding names | 11 | 586 | 586 | Both match; strict casefold target must refuse |
| Casefold-safe names / links / xattrs | 9 | 486 | 486 | Both reconstruct under declared toy casefold policy |

Positive reconstruction included one physical hardlink group, symlink target bytes and xattrs. For the mixed cohort the typed raw MessagePack packet was 2,321 B versus escaped 2,357 B; compressed packet 773 versus 821 B. Local scripts print raw repeated wall and `tracemalloc` values, **not complete RSS, stable hardware measurements or product comparisons**. Five unpaired micro-runs were recorded; do not infer speed superiority.

**Hostile shape court:** 13 authenticated, structurally changed attacks per grammar (duplicate byte path, `..`, slash, NUL, boolean mode, unknown kind, bad blob digest, missing blob, duplicate xattr key, nonexistent hardlink owner, symlink escape, noncanonical tag, unrepresentable casefold target) rejected at *preflight* before output writes. The initially developed hostile test mistakenly used a destination sentinel **inside** the output directory, which could cause trivial destination-not-empty rejection and yield false green. This was caught during local adversarial review and corrected: structural preflight now must fail independently, then destination remains empty and a separate sentinel outside remains unchanged. Keep this methodological error visible: false-positive test oracle was the strongest alternative explanation for the original green.

## Independent counterexamples

1. **PATH_MAX:** real POSIX directory descriptors create sixteen nested 255-byte components (4,095 raw relative path bytes), and can create a file under the final descriptor. A root-prefixed absolute `stat` fails with `ENAMETOOLONG` (local root-prefixed path 4,112 B). This proves an exact byte grammar alone does not grant a decoder full-name coverage: descriptor-root relative traversal with its own concurrency policy is a prerequisite for the near-limit tail. No CMPCT Reader tested.
2. **Symlink target portability:** on a portable *entry-name* fixture, the same signed metadata is accepted by O1's toy `casefold` validator even if its relative symlink target contains invalid UTF-8, reserved device name, a backslash or a trailing dot. Both grammars reproduce all four signed negative examples. Rejecting just output entry-name aliases is not enough.
3. **Inode-owned xattrs:** after replacing one signed hardlink alias's `user.more` value with `CONFLICT`, O1's structural preflight accepts; materialization preserves file bytes and hardlink groups, but also overwrites the owner's xattr via the alias. Both grammars reproduce this signed contradiction. Metadata cannot be independently owned by two names that designate one inode.

The last two failures show that byte-accurate segment encoding is **necessary but insufficient** to provide exact filesystem reconstruction. A future decoder must define metadata authority at the inode/owner boundary and validate normalized symlink target strings as well as entry paths. Bad structures must fail *before* publishing files.

## PARETOBONK / decision / cheapest next action

The strongest immediate alternative was to retrofit escaped names into revision 24. It is inferior under O0's wire inflation and cross-platform alias counterexamples and would change native grammar; **not authorized**. O1 adds the cheaper actual filesystem falsifiers before any full decoder implementation. The signed hardlink contradiction and long-path counterexample also falsify the assumption that name-codec bijection alone solves filesystem fidelity.

**Decision: PRESERVE DETACHED POSITIVE SEED; NARROW CLAIM TO SMALL VALID POSIX TREES; REJECT CURRENT GENERAL/PORTABLE DECODER ADMISSION.** Next unclaimed decisive action: specify independent byte-namespace + per-inode metadata authority; strict target-specific symlink/casefold semantics; descriptor-root POSIX extraction for long names, with ownership and concurrent mutation rules. Cross-check using independent Python/Rust grammar under an explicitly versioned representation before touching the real Builder.

No discovery-policy self-modification is earned. The prospective lesson is narrowly causal: **an object-key codec can be injective while the object graph's physical ownership and output path semantics remain inconsistent**. Similar future research should test these invariants before full end-to-end implementation.

## Completion limitations
No native ABI, revision-24/25 product, Windows/macOS target, secure concurrent directory traversal, all metadata fields (ACL, UID/GID, timestamps), updates, recovery, sparse semantics, selective read, actual SSD bytes or release ABBA. Python `tracemalloc` omits native allocations and system RSS. No actual CMPCT format byte or benchmark credit. Source branch remains draft; no merge, no release. Independent hosted jobs must be inspected at the exact final SHA before assigning any hosted success.
