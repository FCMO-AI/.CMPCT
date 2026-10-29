# J24G27 preregistration — public tree digest must not erase filesystem topology

**Source-bound before mutation:** canonical `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; published `main@80c358f8824ec1b20d349c92ed94c898090969b0`; `src/cmpct/transactions.py` Git blob `964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c`. Released format r24/v0.30.0. Local baseline witness run before this preregistration.

## Problem, invariant and baseline

The public compatibility facade exports `tree_digest` as a filesystem-tree fingerprint. Its current implementation calls `Path.is_file()` and `Path.is_dir()` **before** `Path.is_symlink()`: following links makes a symlink to a file indistinguishable from an independent copy with identical bytes. It also has no representation of hardlink identity: a hardlink and a distinct copy receive the same digest. Linux local witness: all three distinct trees returned `4a0ec1aaba71d5c2abd6cb9c8d6b54e7601c582b35a1c4f98c0d3bd67ba85b24`. This is an evidence/semantic-fidelity problem in a public helper, not demonstrated byte loss in the archive Reader or Writer.

The invariant is **topology-aware equality**: matching path/kind/content/within-tree hardlink classes/lexical symlink targets yields the same digest regardless of inode numbers; changing one of these must change the hash in practical controls. Unsupported special nodes must not be silently accepted as a type-free path. This helper is not a complete metadata fingerprint: file mode, times, xattrs, ACLs, sparse physical allocation, concurrent namespace mutation and crash atomicity are outside this bounded change.

## Mechanism and falsifiable prediction

Use `lstat` rather than following links for kind discrimination. Encode directory, regular file, symlink target and repeated hardlink identity with explicit path and target lengths plus a new digest domain prefix. Stable first-seen path is the hardlink owner; identify only when `st_nlink > 1` and `st_ino` is meaningful; never persist physical inode numbers. Use `os.fsencode` for filenames and symlink targets, preserving POSIX non-UTF8 byte names. A new digest domain intentionally changes the prior output; do not pass it off as the old hash algorithm. This does not modify the archive on-disk format.

**P1:** symlink-to-file vs ordinary copy vs hardlink vs dangling symlink vs directory produce pairwise different digests. **P2:** equivalent hardlink tree freshly built under different root/inodes yields identical digest. **P3:** changing link target changes digest without reading target contents, including dangling links. **P4:** independent file contents remain bound by SHA-256 and explicit lengths, no unknown node silently hashes as an empty type. **P5:** ordinary repository CI, exact source audit and portability checks do not regress from this compatibility-facade change.

**Kill/narrow:** any same-topology different-root disagreement, false equality for test cases, high file-count/byte cost outside existing `O(files+logical bytes)`, unsupported platform failure, or documented consumer requirement for the historical raw digest mandates rework or scoping to an opt-in versioned function. No broad filesystem-exactness credit from the narrow helper.

## Alternatives and opportunity cost

- Keep old hash for historical comparability: preserves known false equalities; not acceptable as topology evidence.
- Mark function content-only: avoids mutation but perpetuates ambiguous exported name; viable fallback if compatibility obligation emerges.
- Rewrite whole format/extraction model: unnecessary, high cost, collides with active owners of r24 link semantics.
- Add source-independent topology-aware digest with explicit domain and regression test: chosen smallest bounded falsifier.

Primary scientific question is the reliability of this currently exported tree-fingerprint abstraction, not another variant of ZIP, MessagePack or extraction size budget. Existing owners #709/#716 cover frozen r24 link conformance; this change does not touch their source/tests or claim their product gates. `docs/discovery/STATE.json` is a staleable shared cache and remains untouched.

## Evidence requirements and no-credit rule

Keep the before/after independent tree fixtures, run focused tests and normal CI, record exact HEAD and all red checks. Validate both symlink and hardlink controls on POSIX; Windows must run or explicitly remain unmeasured. No version, release, compression, general Reader/Writer, full extraction or benchmark credit for this helper change.