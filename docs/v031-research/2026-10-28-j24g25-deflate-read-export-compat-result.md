# J24G25 — Physical Deflate Reader/export acceptance incompatibility

Date: 2026-10-28 UTC  
Status: **DECISION COMPLETE — VALID COMPATIBILITY COUNTEREXAMPLE; DRAFT SCIENCE ONLY**  
Original prospective prediction: [prereg](2026-10-28-j24g25-deflate-read-export-compat-prereg.md), immutable commit `dccad9404e78c0aedd3a9f6b72390bef564307b0`.  
Original product owner: [PR #284](https://github.com/FCMO-AI/.CMPCT/pull/284), exact source `2e493d2d941f9c144c0c5050b41c88dc7c6e57dd`, Reader blob `b0c8eb5eddd5591524b3e9c9a640d9266ccbbbdb`.  
Original released source: `main@80c358f8824ec1b20d349c92ed94c898090969b0`, version v0.30.0 / revision 24.

## Executive decision

**Falsified as transparent promotion:** PR #284's bounded physical raw-Deflate validator preserves its positive CRC corruption repair but rejects legitimate signed-index revision-24 archives whose exact physical compressed bytes contain unused trailing RFC1951 data. The **same exact installed Reader**, on the **same exact physical archive bytes**, accepts `read` and `verify`, yet `export_zip` rejects solely because `inflater.unused_data` is nonempty. This is a compatibility rule divergence, not an integrity win, and must be reconciled before product promotion. The independent [PR #707](https://github.com/FCMO-AI/.CMPCT/pull/707) provides an alternative trailer-tolerant candidate; it must not become a second competing owner without coordination.

## Frozen physical experiment

Five genuine revision-24 one-physical-owner files were assembled with separate first/tail Zstandard-compressed MessagePack indexes, authenticated identical SHA-256, physical `S_BLOB/CODEC_DEFLATE` geometry and SHA/CRC in the header. The source generation tool is `tests/research_j24g25_deflate_read_export_compat.py`. A separate raw RFC1951 ZIP constructor and Python's `zipfile` provide the stronger non-CMPCT output consumer control. On clean source, the same Reader exports exactly recoverable ZIP. Corrupting one physical CRC bit makes all Reader operations reject. Existing destination bytes survive rejected exports in this *single-owner prevalidation case*, **not** the general multi-owner failure-atomicity contract [#492](https://github.com/FCMO-AI/.CMPCT/pull/492).

| Physical Deflate variant | Same installed Reader `read` | `verify` | `export_zip` | Independent stdlib ZIP |
| --- | --- | --- | --- | --- |
| No trailer | ACCEPT | ACCEPT | ACCEPT | Exact bytes |
| One unused byte | ACCEPT | ACCEPT | **REJECT** | Exact bytes |
| Two unused bytes | ACCEPT | ACCEPT | **REJECT** | Exact bytes |
| Second complete stream after first EOF | ACCEPT | ACCEPT | **REJECT** | Exact bytes |
| Physical CRC-only corruption | REJECT | REJECT | REJECT | Independently constructed control still valid |

The three rejected trailer cases yield `OSError: trailing data in retained Deflate stream`. All file records and indexes remain consistent with the compressed-byte size, and every independent ZIP consumer reads the exact original 32,768 bytes in all five cases.

## Hosted evidence and custody

**Final result-bearing installed exact-HEAD scientific workflow:** [Actions #40780525585](https://github.com/FCMO-AI/.CMPCT/actions/runs/40780525585), source `ddc5e636376d7147a6229a4f5128840bb0ed9eaa`, three jobs **SUCCESS** on Ubuntu 24.04, macOS 14 and Windows 2022. It runs source-locked actual `read`/`verify`/`export_zip` cases plus independent physical/index/ZIP referee; on Linux it additionally reruns the **unchanged** inherited PR #284 pytest suite. Windows/macOS inherited pytest collection is not credited because its unrelated historical `tests/conftest.py` imports an experimental `libzstd.so` Linux library; skipping that ancillary suite is explicitly limited to non-Linux hosts. No evaluator assertion or physical-Reader comparator was altered.

Original GitHub artifacts, downloaded and separately audited **as ZIP bytes**:

- Ubuntu: artifact `12857610788`, artifact-ZIP SHA-256 `213babff04590eab257a294d9b4cc138e6e4a49d20d7d3f81f3891911b2c8ea3`
- macOS: artifact `12856363440`, artifact-ZIP SHA-256 `d90f657f74c3df4f90ca969e0998a3615d0b3ffb7a341e2e4f064b9040c5c7f5`
- Windows: artifact `12856548041`, artifact-ZIP SHA-256 `e9702e459dd99ddd20c6f7134feaf180b7f33cd9b5539d9f4cd07c743789ab90`

The in-repository independent physical referee completed **174 successful checks per host**. A second, completely external Python/ctypes/libzstd and Python-stdlib referee, which imports **no CMPCT code or in-repo referee**, read each actual GitHub ZIP and completed **158 checks per host**; it verified primary/tail index parity, SHA-256, MessagePack controls, raw RFC1951 remainder, physical CRC/SHA, ZIP compressed bytes and recorded Reader accept/reject verdicts. All **five complete physical CMPCT archives were byte-for-byte identical across the three operating systems** (identical SHA-256 per case). The independent external auditor correctly rejected eight deliberately mutated artifact variants: physical magic, index, footer, stream bytes, ZIP header, ZIP member, fake accept/reject report, and fake Reader source fingerprint.

Scope caveat: the external referee authenticates physical archives, ZIPs and recorded outcomes, **not** a second independent implementation of the full CMPCT Reader. The actual installed Reader verdicts originate from the three-host exact-source court.

The first hosted run [#40780177385](https://github.com/FCMO-AI/.CMPCT/actions/runs/40780177385) already obtained the same result on all three hosts. The macOS job eventually failed **after** both physical scientific steps passed because the unrelated inherited full-suite conftest `ctypes.CDLL("libzstd.so")` cannot load the Linux-named library there; a concurrent re-dispatch canceled Windows's final ancillary step. The subsequent exact-head run adjusted only the workflow's scope of the unchanged inherited pytest suite to Linux, **without changing the scientific test, physical referee or acceptance expectations**. Earlier mixed-status run is preserved as a genuine infrastructure negative.

## Decision and constrained next action

1. **Keep** the original #284 direct-Deflate physical CRC/SHA repair hypothesis; its current CRC-bit protection is supported by real Reader evidence. **Do not** promote its trailing-byte rejection as transparent.
2. Preserve historical Reader acceptance unless the owner explicitly secures an intentional, separately approved compatibility-policy change. Compare the existing #707 trailer-tolerant candidate as an *alternative implementation* on the same physical source, with correct geometry, source-byte identity, and complete CRC/SHA/error semantics.
3. Keep archived exact-Deflate output identity, true I/O, full product CPU/wall/RSS, ZIP output publication, ZIP64 and cross-platform tests as release blockers. The separate output atomicity owner is PR #492; the ZIP64 count owner is #260. No attempt was made to merge or overwrite their work.
4. Reconcile **one** product integration owner. The first prospectively recognizable cheap discriminator would have been to cross #284's original `trailing` negative test against `read()`/`verify()` on one real signed revision-24 file before implementing more candidate variants. This is a transferable local-method lesson, **not** authorization to edit Discovery Engine doctrine.
5. No format, Reader/Writer/Builder, benchmark, release gate or `docs/discovery/STATE.json` changes. No performance/product credit, no merge, no release. The PR remains draft with a separate exact-head CI evidence basis.


## Exact published-source inheritance control

A separate direct GitHub source-content comparison retrieved `src/cmpct/reader.py` from released `main@80c358f8824ec1b20d349c92ed94c898090969b0`, original PR #284 `2e493d2d941f9c144c0c5050b41c88dc7c6e57dd`, and alternative #707 `5f66db11dfef60b9d0162e8e04596b142db2570d`, and compared the complete source bodies of `_inflate`, `_blob`, `read` and `verify` for exact literal equality. **All four methods were byte-identical in all three sources.** The original PR #284's `_direct_deflate_stream` remains byte-identical to published main, but its `export_zip` wrapper adds the strict preverification step. Conversely #707 modifies `_direct_deflate_stream` but leaves `export_zip` itself byte-identical to published main. This independently localizes the acceptance fork to export verification rather than read/verify being subtly modified in the source controls.

The scientific court executed actual PR #284 Reader, **not** a reinstalled released-main Reader; any assertion about shipped behavior rests on the exact inherited bodies and published full source, not a fictional second hosted baseline. This strengthens attribution without changing any original prediction, gate or measurement.