# O42 — Prospective release-corpus semantic custody witness
Date: 2026-10-25 UTC
Status: PREREGISTERED BEFORE IMPLEMENTATION; source head 36c5c737c2896b9ad9ee68c491ff921fbd36aaa4 (PR #328), unchanged comparator and frozen matrix.

## Current decision and problem
The official r24/ZIP same-runner gate has a single input corpus, but its current `tree_sha256` hashes paths, lstat modes/mtime and bytes **without** the in-tree hardlink equivalence partition or extended attributes. Issue #312 preserves distinct independent false-equality counterexamples: a hardlink vs byte-identical copy and a file with vs without an xattr. The existing root-dependent inode numbers are not appropriate for a portable proof. PR #313 already owns an opt-in typed filesystem oracle but explicitly excludes mode/mtime/xattrs and does not integrate with release-corpus custody. PR #328 owns the fail-closed official comparator; this O42 does not modify its decision rules.

## One primary scientific question
Can an **additive, root-independent, strongly typed** corpus witness distinguish both omitted metadata classes, preserve equality for genuinely equivalent trees residing on different inode numbers, and fail closed when the physical corpus changes during the actual ABBA benchmark, without changing the original immutable release comparators, corpus producer, input, historical `tree_sha256` or threshold?

## Hypothesis, strong controls, and falsification
Create a POSIX-targeted, bounded SHA-256 transcript over exact relative path bytes, lstat kind/mode/mtime, symlink target bytes, regular content bytes, raw xattr names/values and canonical **within-tree** hardlink group ordinals (not absolute inode identifiers). Compare:
1. same relative paths, bytes, mode, mtime: shared inode vs independent copy -> old digest equal, new digest unequal;
2. identical file before vs after add/remove/change xattr -> old digest equal, new digest unequal;
3. two separately created trees with same hardlink partitions and xattr values -> new digest equal;
4. actual before/after release-corpus observation -> new value must remain equal; mutate a recorded metadata witness in a controlled negative test -> fail.
Include directory/symlink distinctions and special-file fail-closed controls. Reject unsupported xattr enumeration, unstable file identity or unreadable source, rather than claiming equivalent inputs. Keep the original manifest fields intact.

**Kill** if any of 1–4 fails, if a third-party xattr is silently skipped, if unchanged controls differ by inode/root location, if official existing `tree_sha256` fields change or if the official comparator, zero-byte gate, ABBA timing boundaries, frozen corpus generator, semantic contract or source identifiers must be weakened for a green result. A narrow scientific success is not a complete snapshot/race guarantee, and does not earn product/release approval.

## Alternatives PARETOBONKed
- Ignore the omitted metadata because one physical directory is reused: insufficient custody if a benchmark changes the root between A/B.
- Replace the historical digest: destroys evidence lineage and unrelated downstream assumptions.
- Import the PR #313 oracle as a release gate unchanged: excludes mode/mtime/xattrs and lacks the strict same-input witness.
- Rehash every input file inside each timing interval: contaminates measured create/extract.
Selected: additive pre/post physical witness, **outside all measured timing intervals**, in a separate stacked PR, with independent specialized CI and hostile unit tests; keep the historical digest and its provenance unmodified.

## Boundaries / concurrent ownership
Branch isolated from PR #328. No writes to #328/#313/#394 or Discovery STATE. No r24 format, Reader/Writer/codec/native changes. Stronger source custody does not grant release authority by itself. If hosted CI fails, separate checker/source evidence from underlying product failure, preserve the negative and the run ID. Reconcile newest heads before late shared mutation. Stop rather than merge while owner conformance/official gate is pending.
