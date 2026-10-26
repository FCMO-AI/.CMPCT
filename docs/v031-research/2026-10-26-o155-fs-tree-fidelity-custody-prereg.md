# O155 — strict static filesystem topology oracle (preregistration)
Date: 2026-10-26 UTC
Source: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, `src/cmpct/transactions.py` Git blob `964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c`.
Owner issue: #312. Scope: independent evidence helper, not a new storage format, product patch, or mutation of frozen historical benchmarks.

## Primary scientific question
Can a deterministic source/extract tree witness distinguish different physical trees which the original `transactions.tree_digest` declares equal, while remaining independent of absolute inode numbers and root pathname for genuinely equivalent static trees?

## Baseline / hypotheses / controls
The inherited helper tests `Path.is_file/is_dir` before `is_symlink`, following link referents, and never encodes hardlink equivalence classes. Issue #312 preregistered local false-equality examples. **Prediction:** a new separate static-tree oracle using `lstat` and raw `os.fsencode` names/link targets yields distinct tree identity for (A) symlink vs regular copy, (B) directory symlink vs ordinary directory, and (C) hardlink alias vs independent content-identical copy. Independently cloned exact tree with different inode numbers should yield equal witness. Payload byte flip should change the witness. Single unique hardlinked file without an in-tree peer should not leak numeric inode into the digest.

**Stronger simpler control:** compare `os.lstat` kind and `os.path.samefile` of controlled pairs directly; this already decides individual cases but cannot create a durable deterministic multi-tree proof. An independent manifest/partition representation is an orthogonal verifier of the digest's classification.

**Alternative explanation:** historical digest is intentionally logical-byte-only; its collisions do not automatically prove CMPCT Reader/Builder output corruption or invalidate historical size/time benchmarks. A 'strict tree' identity needs clearly bounded metadata scope and may still omit ACL/xattr, uid/gid, timestamps or race-free inode custody.

## Design constraint and falsifiers
Portable staged evidence helper only: walk without following symlinks, use `lstat`, raw path/target bytes, SHA-256 regular content, deterministic classes for regular files with >1 in-tree names sharing (st_dev,st_ino), optional permission bits marked in exact scope, canonical JSON serialization of typed rows and relative equivalence partition. Absolute paths, inode integers, changing directory iteration order, process start and host metadata must not affect logically equivalent static-tree digests. No hashes of outbound symlink referents; no circular traversal. File-content work is O(total regular payload bytes) with hardlinks read once when possible; memory O(paths+max file I/O buffer), avoid read_bytes. Root itself is a directory and must be verified. Fail closed on unsupported types, invalid type changes, or duplicate raw names; don't claim race-safe snapshot. Runs on Ubuntu/macOS; Windows support only when host supports the exact cases.

**Kill/narrow:** if the new oracle conflates any preregistered pair, changes under equivalent inode renumbering, follows a symlink, or silently ignores a file type, the proposed helper is not usable as a full-topology witness. A test harness/import failure is not a scientific product loss. Raw individual observations + manifests required.

## Evidence ladder and cost
First inspect source and derive counterexamples; run tiny, synthetic static-tree POSIX microcourt (3 adversarial pairs + identical copies/renumbering + payload perturbation + unsupported-type case); then hosted installed Ubuntu/macOS same-source court. This evidence hardens verification only: no new CMPCT product/release credit and no downstream promotion without exercising real Reader/Writer conformance. Preserve original digest and any historical result.

## Ownership / concurrency
No modifications to transactions.py, any frozen benchmark, historical receipts, source fingerprint or `docs/discovery/STATE.json` (owner #440). Research helper and workflow live on a dedicated draft branch; issue #312 remains causal source of prior finding. Avoid reconstructing already-owned Reader/ZIP/Builder mechanisms. CI code and test cannot change the preregistered acceptance criteria.
