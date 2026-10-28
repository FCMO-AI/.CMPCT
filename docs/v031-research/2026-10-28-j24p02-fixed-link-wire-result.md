# J24P02 — fixed-wire link-tree cross-platform conformance: result

Date: 2026-10-28 UTC. Status: SCIENTIFIC PASS FOR TESTED SOURCE / NO PRODUCT PROMOTION.

## Decision and source boundaries

**Question:** Can real installed revision-24 CMPCT Readers reconstruct Builder-independent immutable bytes representing a regular owner, hardlink alias, relative symlink and parent directory on Ubuntu, macOS and Windows, with an independently decoded physical proof?

**Answer:** **YES**, for the two frozen 4-row, 2-physical-blob RAW and Zstd archives defined here. The exact test-producing HEAD is `fcbe50c67b90ae1fabbbe5a7dd1be1768076082f`, on branch `agent/phased1-v031-j24p02-fixed-links-wire-20261028`, with released product `main@80c358f8824ec1b20d349c92ed94c898090969b0` unchanged. Scientific run [#40778244608](https://github.com/FCMO-AI/.CMPCT/actions/runs/40778244608) completed **SUCCESS on all three hosts**.

The preregistration was committed before code at `e9d9f0a0ea56a3ebd5f0a33d8973e8cbe742de37`. The independent local generator used `struct`, `msgpack`, and system libzstd and never imported CMPCT Builder/Reader. The separate exact-wire physical referee also never imports CMPCT.

## Immutable physical source evidence

| Vector | Complete archive bytes | Archive SHA-256 | Index plain bytes | Record span |
|---|---:|---|---:|---:|
| RAW links | 934 | `1d1e102349095151312cc3efa49a8da7848453d1a322c95a537e3d0307c0e03c` | 300 | 240 |
| Zstd links | 952 | `afaea969c1cd1bf185c730adfd1d1d31e36449dbc2c1f3a5f45b1ac5d7a96b1f` | 300 | 258 |

Each includes 4 signed-index filesystem rows: directory `tree`; owner `tree/00-owner.bin` (100 bytes; SHA `dac9ce2fa2b337b37cdc94b14500528b82e56f2d1f738ad82e71b6bd9c45c265`); hardlink alias `tree/10-alias.bin`; symlink `tree/20-link` with relative 12-byte destination `00-owner.bin` (SHA `e846ad6295578f80eeae3b449aeac5888e099814c1e654438f1ad4012bc43e44`). Both physical records are verified by SHA-256 and CRC32; metadata is duplicated in primary/tail index with footer. These SHA checks are unkeyed integrity commitments, not digital signatures.

## Hosted exact-code-head evidence

| Host | Installed Reader + strict preflight + real filesystem identity + signed structural negatives | Independent referee |
|---|---|---|
| Ubuntu 24.04 | **8/8 PASS**, no skip; frozen regeneration PASS | PASS |
| macOS 14 | **8/8 PASS**, no skip | PASS |
| Windows 2022 | **8/8 PASS**, no skip, including actual symlink and inode alias | PASS |

Totals: 24/24 installed tests, both source-independent physical variants on three hosts, 12 signed structural-negative test cases rejected across hosts, 12 altered physical evidence cases rejected by the independent hosted referee (4/host), and 6 forged-receipt checks rejected (2/host). The referee asserts exact file/member bytes, two authenticated indexes and two physical records for each archive. Each installed Reader `reader.py` was compared to checkout source (Windows CRLF normalized) from an out-of-worktree wheel installation.

**Original artifacts, not reconstructed logs:**
- Ubuntu [#12856230552](https://github.com/FCMO-AI/.CMPCT/actions/runs/40778244608/artifacts/12856230552)
- macOS [#12856221469](https://github.com/FCMO-AI/.CMPCT/actions/runs/40778244608/artifacts/12856221469)
- Windows [#12855073589](https://github.com/FCMO-AI/.CMPCT/actions/runs/40778244608/artifacts/12855073589)

An additional local independent `ctypes/libzstd` wire auditor (separate from the hosted `zstandard` referee) reconstructed both original archives and rejected 10 altered archive/record bytes. Its scope is **local physical/oracle evidence** rather than installed-product evidence; source and receipt remain preserved in the run evidence package.

## Negative and repair history

The **first** upload of `v24-link-tree.json` at commit `090f02fe65046e1bf46ae9fc0aa70e95641ae3af` accidentally shortened the manually transcribed base64 strings: 1224 versus required 1248 characters for RAW, 1248 versus required 1272 for Zstd. That commit did **not** hold valid claimed frozen physical bytes. It remains in Git history as a custody negative. A direct cross-check against the unchanged, independently generated local frozen source found the mismatch **before scientific product results were promoted**. Exact original base64 was restored in `fcbe50c67b90ae1fabbbe5a7dd1be1768076082f`, with both archive SHA-256 values, vector meaning, parser, test criteria, and referees unchanged. The original triggered workflow was queued and was never used as product evidence. The corrected exact-source run cited above is the sole successful scientific attribution.

Engineering Evidence initially failed solely because the PR description omitted required literal headings; the dossier was completed without weakening tests or source. Engineering Evidence on corrected source HEAD `fcbe50c67b90ae1fabbbe5a7dd1be1768076082f` subsequently returned SUCCESS. No discovery policy changed.

## Correct classification, limitations and future work

This is **conformance/evidence enablement**, not a new codec, format, compression gain, generalized hostile-input seal, native/Rust ABI guarantee, or release candidate. Because the fixture places owner before hardlink alias, it does not resolve the separately owned forward-hardlink ordering defect (#262/#621). It also does not resolve known signed hardlink-size contradictions (#610/#693), quota bypass (#690/#697/#700), sparse publication (#255/#573), unsafe targets, race-resistant extraction, xattrs, ACLs, Unix raw byte pathnames or transaction recovery. No native link topology conformance was run; the native Reader currently parses kinds but its hardlink storage is `Unsupported` by source inspection, **not** a measured failure on these new goldens.

The next cheapest decision-changing action, if not already claimed, is a *source-bound* native C ABI conformance test reusing these exact bytes with an explicit expected unsupported hardlink result (not silently weakening successful Python semantics). Product promotion still requires general exact-head tests, portability, semantic safety and official parity/release law. No merge/version/format change is claimed. Discovery Engine `STATE.json` was intentionally untouched under #574 ownership.


## Detached original-hosted ZIP audit: three-root custody confirmation

After the hosted green decision, all three **original GitHub Actions artifact ZIPs** listed above were downloaded (not recreated from logs) and independently read by an offline stdlib ZIP/JSON/hash auditor. Every ZIP passed its entry CRC; each carried the *same exact* source HEAD `fcbe50c67b90ae1fabbbe5a7dd1be1768076082f`, Reader Git blob `e716233403dabd0966863c45635e18fa5ac6afb8` and frozen-wire Git blob `7b0743274987b904d695d9e280883ed66b930519`. Their parsed referee JSONs were exactly equal semantically, each with two correct physical archive identities and two decoded logical byte identities, and each native pytest log contained 8 `PASSED`, zero `SKIPPED`.

| Artifact | Downloaded ZIP SHA-256 | Local checkout manifest SHA-256 |
|---|---|---|
| Ubuntu #12856230552 | `1919aeead4d0d7a6ad882dd81277ac41cdfa8f0ce02609769e0adc5be60856d2` | `736dd65237a4bfccae3aea387fb0e31b56dfd48e734a0b5789ca5d1be7c7ae5b` |
| macOS #12856221469 | `de2768dda70301db87fc201a69075dddf933673145533bf7441de69bc29ed422` | `736dd65237a4bfccae3aea387fb0e31b56dfd48e734a0b5789ca5d1be7c7ae5b` |
| Windows #12855073589 | `393c1549603fb4a27f6db65eb4ebb8c735a7d5e3208acaf3dbd128da53c56ea2` | `f93ad8c7e8fa96a764c516dfee8ff7ce6517fb2e3414b5b761c60691db55f919` |

**A genuine intermediate negative was preserved:** the first offline audit incorrectly demanded byte-identical on-disk manifest SHA across hosts and failed on Windows. Inspecting the complete artifact isolated the difference to checked-out text-file line endings. Reconstructing the exact GitHub manifest yielded LF file hash `736dd652...` and CRLF-transformed hash `f93ad8c7...`, precisely matching the original receipts; the immutable Git blob ID, all archives, source HEAD and semantic JSON referee were unchanged. The independent auditor was then amended to require exactly those two derived SHA-256 values per host, not weakened to ignore hashes. This is a **portable evidence-harness correction**, not a changed product, trial, comparator, frozen vector or promotion threshold.

The complete three-host ZIP auditor and its PASS receipt were preserved separately as local forensic evidence. The evidence-backed process lesson is narrowly prospective: distinguish Git blob identity from checkout byte identity when cross-platform line endings can change. One observation is insufficient to change the Discovery Engine policy.

