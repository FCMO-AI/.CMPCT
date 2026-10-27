# J24B04 — Authenticated hardlink-alias logical-size contradiction: three-host result

Date: 2026-10-27 UTC
Status: **SCIENCE CONFIRMED / PRODUCT UNCHANGED / DRAFT PR #610**
Original prospective protocol: [J24B04 preregistration](2026-10-27-j24b04-hardlink-alias-size-prereg.md), commit `bbe49d530a6a78298a69fbfe613a5c3e59634884`, before all code and outcome.
Released source: `main@80c358f8824ec1b20d349c92ed94c898090969b0`, CMPCT v0.30.0, physical revision 24; `reader.py` blob `e716233403dabd0966863c45635e18fa5ac6afb8`, `validation.py` blob `51c2849061f99a4afeddb7666956b24566ce7de0`.
Scientific implementation-only head: `8ab8107ae3ad5123938489e3c06603b803a3f090`; **neither product source is modified on the PR**.

## Scientific question and actual decision

Can a fully reauthenticated r24 `K_HARDLINK` alias declare a size different from its terminal owner's verified physical size, while normal strict preflight, read, verify and selected range continue accepting contradictory semantics? **YES**, on the unchanged installed CMPCT Reader in Linux, macOS and Windows. This finding is distinct from owner `S_BLOB` direct geometry #605/#609 and distinct from external-archive disclosure.

The r24 Builder normally writes the alias's real inode `st_size`; `K_HARDLINK` is a second path to the *same inode*. Keeping an independently false logical length is not exact filesystem reconstruction.

## Hosted evidence and reproducible wire

Three-platform prospective run: [GitHub Actions #40548523651](https://github.com/FCMO-AI/.CMPCT/actions/runs/40548523651) — **SUCCESS for each of Ubuntu 24.04 / macOS 14 / Windows 2022**, Python 3.11. Exact-head archived artifacts:
- Ubuntu: [#12753343153](https://github.com/FCMO-AI/.CMPCT/actions/runs/40548523651/artifacts/12753343153).
- macOS: [#12754955702](https://github.com/FCMO-AI/.CMPCT/actions/runs/40548523651/artifacts/12754955702).
- Windows: [#12753174189](https://github.com/FCMO-AI/.CMPCT/actions/runs/40548523651/artifacts/12753174189).

[Original research court](../../research/j24b04_hardlink_alias_size_court.py) builds complete archives independent of the Builder: RAW and Zstd owners of exactly 128 physical bytes; valid alias size 128 and hostile alias sizes 136/120/0; authentically recomputed primary/tail index, footer, SHA-256, CRC32 and physical frame, with no physical owner/payload mutation. For all **8 actual wire images per host**, the published `preflight_archive`, `CMPCT.read(owner)`, `read(alias)`, and `verify()` succeed. For the **6 contradictory alias-size images per host**, `read(alias)` returns the underlying owner's 128 bytes regardless of its alias metadata. A query beginning at an alias-declared end below 128 also returns one byte from its ultimate physical owner's content, even though it exceeds the alias's recorded logical EOF. Positive 128/128 controls return exact expected bytes; owner physical EOF still rejects an out-of-owner request. An actual missing hardlink target is rejected by strict preflight.

The [detached stdlib/msgpack/python-zstandard referee](../../research/j24b04_hardlink_alias_referee.py) imports **no CMPCT module** and independently decodes/rechecks entire original wire byte images, primary/tail indexes, physical CRC/SHA, and alias-only metadata delta. It confirms all eight images and rejects **8/8 deliberately tampered receipts per host**. Totals are 24 authenticated original cases (18 malformed alias rows), **24/24 tampered evidence receipts rejected**, 3/3 host SUCCESS. This is independent *wire/receipt verification*, not a second complete Reader implementation.

## Causal attribution and strongest negative

Source-exact r24 `validation._validate_storage` checks only `K_HARDLINK` target shape. The hardlink post-pass checks existence and absence of cycles; it has no `alias.size == terminal_owner.size` invariant. The public `CMPCT.read(alias)`, `file_sha256(alias)` and `read_range(alias,...)` delegate to the referenced owner without comparing the alias's declared size first; `verify()` consequently hashes the delegated bytes and accepts the false alias size. The failure is a **logical metadata/inode ownership discrepancy**, not data escaping the target's actual physical blob. Unlike J24B01, the prospective prediction was confirmed, not retrofitted. No hostile filesystem extracts, NTFS ACL/meta parity, source mutation, chain-depth benchmark or resource/RSS performance has been measured.

The negative controls show that missing-target rejection continues working and that an out-of-**owner** range still fails. A positive product repair must not broaden this into a fabricated physical leakage claim. Existing #342 proves that per-alias terminal-owner walk can exhibit quadratic work on valid chains: at N=4096 chain preflight baseline ~684 ms and memoized ~16 ms, but memoization also incurred ~7% star overhead. So a naïve recursion-based repair is **not** automatically promotable.

## Smallest productizable invariant / next executable action

On one pinned authenticated effective index, resolve terminal owner identities using bounded memoization or another charged O(N) approach (reuse #342 ownership); enforce `K_HARDLINK.alias.logical_size == terminal_regular_owner.logical_size` for every alias, rejecting malformed declarations before list/read/extract publication. Preserve valid chains and acyclic graph behavior of existing v0.30 archives unless current normative format explicitly limits them. Retain direct-file/symlink guard already separately owned by #609; compose both through current Reader owner #569. For product promotion independently test Builder-created hardlinks, signed alias-only adversarial rows, ranges including zero, chain and star topologies, 3-host semantic parity, cold-open wall/CPU/RSS, extraction inode/mode/xattr/mtime semantics, exact revisions, and full release gates. Guard needs no on-disk format change in principle, but **no such repair is present in this PR**.

### Discovery/counterfactual
One prospective discriminator could have decided this cheaply without broad empirical benchmark: compare the alias's declared size with the terminal regular owner in the authenticated effective index. It was recognizable from unchanged source and r25's existing inode-metadata invariant; hosted genuine-Reader plus wire-independent audit was nevertheless necessary to establish actual r24 behavior. There is no basis for editing normative Discovery Engine policy from this single result. Shared `docs/discovery/STATE.json` remains under owner #574; no collision or shared mutation.

### Exact-head CI and promotion boundary
The scientific court passed on `8ab8107` and all three hosts; Engineering Evidence was initially red because PR dossier lacked three required named sections, then a corrected PR description triggered a **SUCCESS** on the same source head. Version Discipline and CI Topology also returned SUCCESS. General Tests and other release gates are independent and are not claimed green by the scientific court. No product code, benchmark comparator, evaluator, format, version, merge or release was changed by this research.