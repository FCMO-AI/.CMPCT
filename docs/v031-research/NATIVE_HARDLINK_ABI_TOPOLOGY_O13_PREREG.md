# O13 — Native C ABI hardlink-topology distinguishability (frozen preregistration)

Date: 2026-10-24 UTC. Status: **PREDICTION FROZEN BEFORE TEST IMPLEMENTATION**. Scientific falsifier only; no product/release claim.

## Authority and ownership

Canonical `FCMO-AI/.CMPCT` development: `agent/v031-development`; released checkpoint v0.30.0/r24. This independent research branch starts on exact native parser/batching union PR #326 `43ba79f9b9395af22a0f408de565704c268a4758`. PRs #327/#335/#337 own experimental C extraction and PR #340 owns a separate optional logical SHA query. PRs #339/#342 own Python strict-tree/hardlink preflight. No overlap: O13 changes only a new stand-alone test, its workflow, and research evidence, never native ABI or extraction implementation. Discovery `STATE.json` is staleable; do not edit it. `docs/discovery/CONCURRENCY_PROTOCOL.md` absent at orientation on canonical default branch.

## Primary question / bounded claim

Is the complete documented *public read-only native C API* information-complete enough to reconstruct hardlink **inode equivalence classes**, even when every regular file's bytes and metadata are recoverable? Specifically, can two genuinely different valid r24 hardlink graphs have identical values for all public entry enumeration and supported entry-read observables?

A positive indistinguishability witness means a correct general-purpose native-only extractor **cannot** infer the hardlink target/ownership graph from this ABI. It does not imply the on-disk revision-24 format lacks that information, or that the Python extractor cannot reconstruct the graph. Adding a new signed index-backed hardlink-target query (or a higher-level native tree API) may be necessary for native-only complete filesystem semantics; no ABI addition is authorized by this O13 alone.

## Frozen experiment

Create *two* independent real Builder-produced r24 archives (POSIX runner), each containing `a.bin`, `b.bin`, and `z_alias.bin`. The two regular files have **identical exact bytes, size, permission, and normalized timestamp** but are distinct inodes. In archive A the alias is an `os.link` of `a.bin`; in archive B it is an `os.link` of `b.bin`. Verify source `st_dev/st_ino` partitions, immutable original-source SHA-256, and authenticated Python Reader index rows, including respective hardlink storage owner paths, before comparing native observables. Archives should differ in bytes because their authenticated hardlink target paths differ.

Read the archive through the actual compiled public native C ABI (not a private Rust field or index decoder): revision, entry count, each entry's `path`, `CmpctEntryInfo` kind/mode/size/mtime, public `cmpct_entry_read_range` status and returned bytes for every entry (including the hardlink alias), plus the PACK owner admission status. Demand semantic observation equality across the two archives while Python indexed hardlink targets differ. The alias read should be UNSUPPORTED, **not** silently reclassified as a regular file; both ordinary-file bytes remain independently readable and exact.

Distinct control: create two real archives with symlink `z_symbolic.bin` pointing to `a.bin` or `b.bin`; verify the ordinary native entry-range API *can* distinguish the link-target payload (when implemented for direct symlink storage). This prevents overclaiming that all link types are unobservable. If that positive control cannot execute, report why rather than weakening hardlink disproof criteria.

## Disproof / kill / external costs

**Disproof:** if any documented public ABI observable differs on the hardlink pair, or the archive's actual hardlink target cannot be verified independently, or the source byte/metadata parity fails, the indistinguishability claim fails. Do not delete the differing observable. Also fail if real Builder collapses the two distinct inode partitions, if archive byte differences can be explained solely by inconsistent source timestamp/metadata, or if the new test requires altered native code/harness comparator.

**Positive scope:** one constructed structural pair establishes an ABI *incompleteness counterexample*, not generalized safety/performance measurement, cross-platform behavior, or a production API design. Inherited native tests remain independent; no write/release/format policy changes. The source tree must not rely on private datasets or hidden format shortcuts.

**Alternative considered:** a full native extractor could parse the archive index itself, but that would duplicate the canonical native parser's trust boundary. The simpler product design might be an opt-in metadata query or a portable native extraction API; this experiment determines whether an actual information gap exists before paying for either.

## Cheapest decisive rung and next decision

The initial code-level derivation says native `Entry` keeps only path/kind/mode/mtime/size/storage and `Storage::Unsupported` for authenticated hardlink owner-string references; public info/path/range/owner APIs do not export the owner path. The hosted real Builder + ABI differential witness is the cheapest differently rooted decisive rung to falsify this inference. If positive, hand off to O11 owner #337 and consider the **minimal** bounded ABI design only after comparing with other missing filesystem-semantic metadata (symlink, uid/gid/xattr, sparse, hardlink). If negative, retire this route and record the distinguishing observable. Never grant product or release credit from a research-only oracle.

**Release law:** r24 and v0.30 history unchanged; standard exactness, safety, resource, portability, official benchmark, and release gates remain intact.
