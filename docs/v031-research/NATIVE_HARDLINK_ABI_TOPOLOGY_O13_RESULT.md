# O13 / O13b — Native C hardlink topology information boundary (result)

Date: 2026-10-24 UTC. Status: **DECISIVE NARROW SCIENTIFIC RESULT / RESEARCH ONLY**. No CMPCT Reader, Builder, Writer, format, benchmark threshold, release version or existing ABI altered.

## Source and authority

- Canonical release: v0.30.0/r24; development `agent/v031-development`. Independent test-only draft [PR #343](https://github.com/FCMO-AI/.CMPCT/pull/343) starts from exact [PR #326](https://github.com/FCMO-AI/.CMPCT/pull/326) source SHA `43ba79f9b9395af22a0f408de565704c268a4758`.
- Frozen O13 prediction: `docs/v031-research/NATIVE_HARDLINK_ABI_TOPOLOGY_O13_PREREG.md`, committed **before O13 tests** at `0b05ff7eb706482b20fb505280dbfdae160b5852`.
- Frozen held-out O13b prediction: `docs/v031-research/NATIVE_HARDLINK_ABI_TOPOLOGY_O13B_PREREG.md`, committed at `00f2ff21914c6682ae1371a578fd529a24045fbd` **before O13b test implementation**.
- All synthetic public test source and inspected ABI are in the PR; full test output is retained in hosted artifacts (GitHub artifacts may expire after retention).

## Primary mechanism and exact observations

The r24 file index stores a hardlink as a logical `K_HARDLINK` row carrying an owner **path string** in the storage tuple. The native Rust parser exposes its generic entry `kind`, `path`, `mode`, `mtime_ns` and `size`, but its `Storage::Unsupported` representation neither resolves the hardlink owner nor exposes it through the public C ABI. Public C enumeration and range/owner admission therefore cannot reconstruct that relation.

**O13 frozen original:** On two real POSIX source trees, `a.bin` and `b.bin` are separate inodes with identical bytes and metadata. `z_alias.bin` is hardlinked to `a.bin` in tree A, to `b.bin` in tree B. Actual source `(st_dev,st_ino)` partitions differ. Real Builder r24 archive SHA-256 **differs**:
- Alias-to-a: `3b93791bce71e433ed1b725993d64788b5f73e111d68ff32a6bba63ce1b3b587`.
- Alias-to-b: `9eae13e1646e0497a9333771e61b5550757b6b9c0d4b6a6ac113fa6b8347c666`.

The independent Python Reader's indexed hardlink owner target distinguishes the trees and reconstructs correct bytes. Conversely the compiled public C ABI returns **identical** revision, count, pathname, entry kind/mode/mtime/size, full per-entry range status/bytes and PACK-owner admission results. Both `z_alias.bin` read requests return `CMPCT_ERR_UNSUPPORTED (-7)`. The complete public C-observation JSON SHA-256 for either archive is `3127a69928db2504f4847df713918d53744db026939bb3de1cc4d544271d90c4`. Held-out positive control: symlink `z_symbolic.bin` target `a.bin` vs `b.bin` **is** distinguishable by public C range output, so not all link payloads are inherently hidden.

**O13b, stronger held-out perturbation:** Now `a.bin` and `b.bin` are equal-sized but deliberately **different bytes**; across the two archives each root file remains identical to its counterpart, and modes/timestamps/paths are controlled. Alias-to-a vs alias-to-b yields **different independently verified logical bytes**, different owner paths, different archive SHA-256, yet still **identical C observations** and `CMPCT_ERR_UNSUPPORTED` for the alias. Archive hashes: `27d17a40f7cae377dd73a3134fcbd98ff46c63735aca46f43101261f940c267e` vs `efda0af7cddaa1278dccfb1440c4b04915b4758207939295cccd0c82a923562e`. Public C-observation digest for either is `8aabc826e2dd6daf7dec6c3ffbb286efa14fba6f10bfa4bf69cf86610330ea6f`. Independently reconstructed alias logical SHA-256 differs: `a0e7a3477db21f5900baecd29aa33bfcfa240ca753064745db2002fa2734e98b` vs `6d95fe30ecdb10acb5d5088c0a7617be83af17a67c0764c03e66f2ca0c9ad34a`.

**Decision:** `HARDLINK_GRAPH_UNOBSERVABLE_OVER_DOCUMENTED_NATIVE_ABI` and `DISTINCT_SOURCE_CONTENT_STILL_NATIVE_UNOBSERVABLE`. The second test defeats the tempting alternative explanation that O13 appeared ambiguous merely because the two roots had identical contents.

## Hosted source-bound evidence

- Original O13 code HEAD **`e702764a2b83f6ff791efa482187ffebd5efa917`**, [workflow 40086106599](https://github.com/FCMO-AI/.CMPCT/actions/runs/40086106599) **SUCCESS**, artifact **12556114825**, ZIP SHA-256 recorded by GitHub: `3c9f6e2e03856c866c52d28b7b79645b9614942b99d566fdca26dce35494af4d`.
- Combined O13 + O13b code HEAD **`4f8503e62034b35bb2b2021018e04eea219f78ad`**, [workflow 40086479175](https://github.com/FCMO-AI/.CMPCT/actions/runs/40086479175) **SUCCESS**, artifact **12557456507**, ZIP SHA-256 `6535805afb3b8b9e46b7787be4166700acc46aad0262fa3a87d8deda55f83390`. Both original and held-out controls passed on the **same exact source**.
- [Engineering Evidence 40086276024](https://github.com/FCMO-AI/.CMPCT/actions/runs/40086276024) passed original HEAD after PR dossier corrected an initial missing literal `disproof` marker; neither evaluator nor product source changed.
- Combined-head general native/release status is independent of this specialist O13 court; do not infer full General Tests or non-skipped release parity from the two successful specialist runs. Any post-result docs commit also requires its own exact-head check when relevant.

## What the result proves (and what it does not)

It proves a **non-injective public ABI mapping** from two valid r24 archive filesystem graphs to the same output transcript. A deterministic C consumer restricted to those documented APIs cannot reconstruct both originals correctly: the two source trees require distinct inode partitions and, in O13b, different alias content, while all allowed observations are equal. For `k` independently aliasable paths with two candidate roots each, the underlying relation can encode `k` bits of information not surfaced by this ABI (conditional on otherwise equal visible entry metadata); this is a derivation, **not** a separately hosted `2^k` corpus result.

The on-disk r24 index and Python Reader **do retain the owner path**, so no format-information loss is claimed. Index SHA-256 is internal integrity checking, not an external digital signature/authentication credential. The experiment does not prove a vulnerability in all APIs or that arbitrary hostile archives are safe to parse, and only confirms POSIX hosted synthetic trees. It measures neither product compression, full extraction performance, RSS, recovery, Windows/APFS correctness nor release-worthiness.

## Next decision-complete action

Compare **minimal index-backed hardlink-target path query** against **native owner ordinal/graph API** and a **higher-level native extractor** before adding ABI surface. For path query, prefer an explicitly bounded size-query/copy, no borrowed C pointers; reject non-hardlinks, missing/cyclic/invalid target and bad output buffers; preserve exact opaque UTF-8 path bytes where existing native grammar allows. Owner-index query may need index-time O(N) mapping/cycle guard, which must charge memory/CPU and not enable algorithmic complexity attacks. A high-level extractor has larger ownership/security obligations but may avoid piecemeal metadata APIs; don't invent an entire new parser in each consumer. Need independently authored hostile target/cycle cases plus real Builder ordinary trees, exact-head parity, source mutation, portable filesystem constraints and known O11 resource bounds.

The existing C extractor owner is [PR #337](https://github.com/FCMO-AI/.CMPCT/pull/337); hand off the information limit there rather than editing its source. No canonical merge, version bump or Discovery policy change from this research.
