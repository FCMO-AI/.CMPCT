# J24I05 — authentic revision-24 compaction symlink policy: confirmed capability gap

**Disposition: `COMPACTION_POLICY_INCOMPLETENESS_CONFIRMED` (scientific/product-defect reproduction, NOT a fix or a release).**

## Preregistered question and exact source

- [Source-derived issue #718](https://github.com/FCMO-AI/.CMPCT/issues/718) was unconfirmed when prospectively registered at commit `5c0a635e0ecf5ba08226e3bc4260a83d786dff6b`.
- Published base `main@80c358f8824ec1b20d349c92ed94c898090969b0` (v0.30.0, r24). The original, unedited product blobs on the research branch are `builder.py 663ef0922992b1fbb8f19e6eea88d55c10a56044`, `reader.py e716233403dabd0966863c45635e18fa5ac6afb8`, `transactions.py 964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c`.
- Research script `research/j24i05_compaction_link_policy.py`; source-bound hosted [run #40796428224](https://github.com/FCMO-AI/.CMPCT/actions/runs/40796428224) on experimental HEAD `f7bfb96fd84851e3f69510e81c61ce8fea0af057`, **SUCCESS**, genuine pip-installed Builder/Reader/native package on Ubuntu 24.04/Python 3.11, no product `src/` or `native/` changes.
- Original evidence [GitHub artifact #12863419130](https://github.com/FCMO-AI/.CMPCT/actions/runs/40796428224/artifacts/12863419130), ZIP **6,961 B**, SHA-256 `f0eb4c0017c8bc2cf85af9d6f6d5e945c345f4e71d1fb8ec8d157025a7fbf412`, contains full six genuine CMPCT input/output files, source Git-blob identities, raw case JSON and stdout.
- First installed hosted run [#40796196429](https://github.com/FCMO-AI/.CMPCT/actions/runs/40796196429) on prior source `277ac570` also passed all four cases, but preserved only JSON/hash receipts. Later source added **physical artifact retention** and repeated all four cases rather than claiming byte-level independent audit from the first run.

## Direct hosted observation

The test created four distinct Builder archives, each opened by the original Reader. It verified the full regular owner bytes and, where applicable, the literal symlink target bytes; the original `verify()` reported one or two valid members. After each attempt it rehashed the original archive and a separate external sentinel.

| Input | Original r24 SHA-256 | Ordinary compaction result | New output |
| --- | --- | --- | --- |
| Owner-only regular file | `5eb4e616a270b58853da8d8f59832056c53d8e95a737e5e2546563ee18f6858b` | PASS, exact data | 913 B valid r24 |
| Safe relative target `owner.bin` | `ab1c1471c633ad174f1e2e19fc055faf3b96858825e2531ac40fbcb24af2e058` | PASS, exact owner and symlink | 1,030 B valid r24 |
| Absolute target inside test scratch root | `456f97219e772cba9d56791dab3d63bf459a3daaa18abdedafec0af2220839e0` | **FAIL** `OSError: unsafe symlink target in 'link'` | None |
| Parent-relative `../external/sentinel.txt` | `9bb6ae5e77d3d00886f51bb8158153b6fa58b30ea6ef116f2fb2e5b8f573c16b` | **FAIL** same extractor policy | None |

All source archives remained bit-identical; both rejected cases left no final compacted archive and the external sentinel remained unchanged. The test proves that **some genuine, readable, authenticated-by-index r24 archives cannot be compacted through the current default pipeline**. Calling this an extractor security defect would be inaccurate: default extraction appropriately rejects the two targets for caller-selected destinations.

## Detached physical audit from a different code root

A separate local Python auditor imported **no CMPCT package code or experiment functions**. It used `struct`, `hashlib`, `zlib`, system `libzstd` through `ctypes`, and MessagePack to read all **six retained real r24 archives** directly from the downloaded GitHub ZIP. It verified revision-24 headers and footers, two compressed index copies, SHA-256 over decoded index, every physical RAW blob frame's geometry/CRC32/SHA-256, member kind and storage references, literal symlink target bytes, complete archive SHA-256 vs the hosted case receipts, and valid compacted outputs for both controls. **Result: PASS, zero differences.** Independent audit receipt JSON SHA-256: `93e8a90dd335ff7871fe3a7b3d3c19b0bd8864a313368c0a17b41a934e393fbf`. Standalone audit program SHA-256: `cad7d78b3f08f2a2643086793b46138da1cfca194f681fe2ed84c74591e85fef`. The downloaded artifact's outer ZIP SHA is preserved above.

This second parser provides **physical-format evidence** and detects an internally inconsistent hosted receipt. It is **not** a second independent OS/Reader execution and cannot validate the test's temporary sentinel after the work directory is removed. The positive installed-run assertions provide that narrower claim.

## Causal finding and next engineering fork

Published `compact_archive` first calls `ar.extractall(root, metadata=True)` in a temporary tree, implicitly inheriting `safe_symlinks=True`. That guard rejects absolute/parent-relative target bytes, despite Builder and Reader being able to represent and read them exactly. Both positive controls surviving discriminates this from a general compaction malfunction.

The cheapest **product** route is not `safe_symlinks=False` globally. A credible fix should separate *inert archive representation* from *user-destination materialization policy*: a typed manifest/physical-owner route is safer long-term; a narrowly capability-isolated scratch extractor requires explicit no-parent-symlink, safe hardlink-owner and namespace proof before lifting the target guard. Preserve contents, link target bytes, hardlink equivalence, sparse/integrity, crash/atomic publication and all extractall security defaults. Existing destination-symlink and forward-hardlink issues #265/#619 are independent hazards; coordinate rather than implementing parallel Reader guards.

**Negative / limitation:** this court measured a tiny synthetic Builder-generated file tree, only Ubuntu (not Windows/macOS), one original revision, no update/delta generations, no concurrent source mutation, no ACL/xattr/hostile namespace transfer and no full-system CPU/RSS/storage economics. The fact that the failed source archives pass `verify()` does **not** make them safe to materialize with a relaxed policy. Zero product files changed, zero merge/release/format/policy modifications.

## Discovery and continuity

This was a *frame change*: after saturating full-matrix A/A attribution in J24I04, a cheap actual installed semantic counterexample answered the previously source-only #718 question. No other active PR owned the same compaction-specific hypothesis at preregistration. The earliest decisive observable was the **source-controlled Builder/read/verify versus compact** comparison on one actual unsafe-target archive; the second negative target and two positives prevent a narrower accidental explanation. This is a local scientific method lesson, not enough repeated causal evidence to change `docs/discovery/DISCOVERY_ENGINE.md` or the claimed `STATE.json` (#574 owner).

**Next practical owner action:** decide whether `compact_archive` promises all r24 encoded paths/links, then implement a single consistent compaction-specific representation transfer or private proven-safe extraction path, and challenge full filesystem/integrity/atomicity before merge. This experiment remains research/bug proof, **not release credit**.
