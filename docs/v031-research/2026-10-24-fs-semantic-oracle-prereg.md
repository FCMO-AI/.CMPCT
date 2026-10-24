# v0.31 — filesystem semantic digest source-exact falsifier (Issue #312)

**Date:** 2026-10-24 UTC. **Status:** research/conformance instrument, not product promotion. **Authority:** `AGENTS.md`, `docs/AGI_ENGINEERING_STANDARD.md`, `docs/PRE1_RELEASE_POLICY.md`, `docs/discovery/DISCOVERY_ENGINE.md`.

## Pre-hosted-court question and claim

The three existing tree digest helpers used in the Writer/evidence line conflate physically different structures: a symlink to a file versus a separate file of identical bytes; a directory symlink versus an actual directory; and an in-tree hardlink alias versus an independent file copy. The current `transactions.tree_digest` has `is_file`, `is_dir`, `is_symlink` in that order; the historic C25CC01 helpers check `is_dir` before `is_symlink`. These tests are evidence integrity, **not proof of a Reader or Builder reconstruction defect**. Old recorded results and source identities remain frozen.

**Hypothesis:** an opt-in digest independent of the product/evidence helpers can distinguish these three cases while remaining invariant under changes to the numeric inode identifiers and root directory, preserving raw POSIX symlink/name bytes, avoiding symlink traversal, and failing closed on unsupported special files and resource limits.

**Stronger control:** compare with an independently constructed typed filesystem manifest (separate `pathlib` traversal, `lstat`, physical inode-equivalence partition, and SHA-256 file content). Use a seeded 90-case structural perturbation suite. No fixture identities or heuristic thresholds are used to determine equivalence.

**Disproof:** any false equality on the three controls, any different digest for equivalent hardlink graphs across separately constructed roots, symlink traversal, raw-name collision, a held-out typed-manifest disagreement, a silent special-file omission, or an assertion of metadata/snapshot fidelity outside the documented scope defeats the claim. Native/platform failures must remain visible as platform-specific `UNSUPPORTED`, not silently labeled pass.

## Exact-source and concurrency

Target the exact PR #311 source stack and operate only in new, isolated tool/test/research/workflow paths. Do not edit `src/cmpct/transactions.py`, `src/cmpct/reader.py`, `src/cmpct/cli.py`, `benchmarks/v030_c25cc01_{direct,mmap}_extract_oracle.py`, the discovery index, benchmark history or v0.30 release custody. The original helpers run via AST extraction of their **actual source function**, not rewritten approximations. Concurrency/source locks belong to the GitHub branch/PR and exact-head workflow; this experiment does not modify shared locks.

## What v1 actually certifies

The digest domain-separates and length-prefixes raw relative path components, entry types, symlink targets and regular-file contents; within-tree `(device, inode)` equivalence is canonicalized into path-order group identifiers so inode numbers themselves are not exported into the digest. It hashes files incrementally in 1 MiB chunks and limits entries/depth/path bytes. A missing/nontrustworthy file ID fails closed; unavailable symlink/hardlink operations are reported explicitly.

This **does not** commit permission bits, ownership, xattrs, ACLs, mtimes, sparse physical extent structure, special devices, directory hardlinks, or physical storage costs. It does not provide a filesystem snapshot or race-resistant directory confinement. Its recursive traversal materializes and sorts each directory's immediate child list (bounded by the global entry budget, but not constant-space with respect to a single wide directory). It is appropriate for quiescent-trees conformance, not a security sandbox.

## Evidence ladder / promotion

1. Locally run strong negative, positive and held-out tests. Local green is diagnostic only.
2. On GitHub Actions, pin the exact source HEAD; execute tests and source-faithful three-case court on Linux, with a second Windows platform control when supported; preserve machine-readable JSON evidence even on failure.
3. Decide only the scoped scientific question. A product integration requires an explicitly reviewed API contract and separate full regression, source fingerprint, performance, portability and release gates. No format/version change here. Do not rewrite old benchmark receipts.

**BONK alternatives considered:** modifying `transactions.tree_digest` would collide with active Writer/Reader ownership in PR #311; rewriting historical C25CC01 digests would destroy lineage; merely renaming the old hash would not fix false equivalence; depending on `rglob()+is_file` would reproduce the original defect. The isolated typed semantic oracle is the cheapest decisive action with future reuse.
