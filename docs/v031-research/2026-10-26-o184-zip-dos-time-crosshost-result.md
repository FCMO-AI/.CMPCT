# O184 — Authentic r24 signed timestamp to ZIP cross-host result

**Status:** decision-changing Windows product-negative, Linux positive; macOS receiver and broad CI pending at the initial evidence cutoff. **Source HEAD** `790ee1fc7a8c82d534668ecc4639740217e4bad7`, base `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, published CMPCT v0.30.0/r24. Original prereg at `467f409833377a7e055ef08b0686c3e65bdbc6d6`, before instrument and workflow.

## Actual product finding: Windows can verify the same Linux archive but cannot export it as ZIP

Hosted scientific Actions [40325877075](https://github.com/FCMO-AI/.CMPCT/actions/runs/40325877075), run started on 2026-10-26. Original archive built with genuine `Builder(root).build(archive)` on Ubuntu 24.04, source SHA authenticated, installed Reader outside source checkout on both consumers.

| Record | SHA-256 | Size | Signed mtime_ns |
|---|---|---:|---:|
| `old.cmpct`, old.txt 1960-01-01 UTC | `c7617ff817f8a9b8cde13ce6d1425e9f6c3166cca9070b57fd9dc07ad930154c` | 952 B | -315619200000000000 |
| `normal.cmpct`, modern.txt 2000-02-02 UTC | `ef33550d66ec22e16652bfbc78d96dc53b8f3f396e6aec871fa53bb55826f24c` | 945 B | 949449600000000000 |

All jobs examined independently compared checked-out `src/cmpct/reader.py` with installed Reader source; SHA-256 `83be3f08f7fafb1fd638fda6140bbe1af6676c261be10acc9ea8f8b633beefff`. Both archives passed CMPCT `verify()` and exact source file bytes and physical header/index timestamps were preserved.

### Host evidence (source-exact authentic Reader)

| Consumer | Normal ZIP | Old pre-1970 ZIP | Verdict |
|---|---|---|---|
| Ubuntu 24.04 / Python 3.12.15 | PASS; 165 B | PASS; 166 B, DOS date 1980-01-01 | POSIX control positive |
| Windows Server 2022 / Python 3.12.10 | PASS; 165 B, same ZIP SHA as Ubuntu | **FAIL; OSError Errno 22** | **Product-negative hypothesis CONFIRMED** |
| macOS 14 | PENDING at initial cutoff | PENDING | Not attributed yet |

**Windows exact exception:** `OSError: [Errno 22] Invalid argument`, raised inside `time.localtime(mtime_ns/1_000_000_000)` at `src/cmpct/reader.py::_zip_dos_time` line 494, called by `CMPCT.export_zip` line 533. Genuine valid r24 input, identical archive SHA, negative timestamp accepted by CMPCT `verify()`, ordinary contemporaneous control exports successfully. POSIX exports old signed timestamp as ZIP date 1980-01-01, preserving exact member bytes and ZIP CRC. This separates archive compatibility from ZIP DOS timestamp-conversion portability.

**ZIP successful control:** normal zip SHA-256 `e7a0b0f664b438b30c165b9f048800fce51843f89cda0e8c5593a52aa8243a56`, original old Linux ZIP `34af037723c987253510ff8d306e4c385976837e98d81fabd99afa5638518ad8`. Payload SHA-256 `old.txt=627630a4301d9386c072ddafbd15b79f8882af0f99ab02142e4c10654ee242f2` and `modern.txt=a37aeb9e2a79410196109a351ee7e8cdc51f62f11b934acee9ab36d9f94042e8`, independently checked with stdlib `zipfile.ZipFile.testzip` on successful cases.

### Raw custody
- [Hosted action #40325877075](https://github.com/FCMO-AI/.CMPCT/actions/runs/40325877075)
- [Original Linux binaries & receipt #12650898042](https://github.com/FCMO-AI/.CMPCT/actions/runs/40325877075/artifacts/12650898042)
- [Ubuntu consumer result #12650149587](https://github.com/FCMO-AI/.CMPCT/actions/runs/40325877075/artifacts/12650149587)
- [Windows consumer result #12651895033](https://github.com/FCMO-AI/.CMPCT/actions/runs/40325877075/artifacts/12651895033)

### Decision / alternative explanations / boundaries

**Decision changed:** `_zip_dos_time` does **not** preserve availability for every valid r24 signed timestamp on Windows. Its unconditional host `localtime` precedes DOS year clipping. The Windows negative comes from a real installed source/runtime, not a synthetic mock or SHA drift. Existing transactional ZIP publication owners #492/#512/#514 must not be overwritten; nearest Reader ZIP naming integration owner #499/#507 should preserve the recorded defect when designing a safe bounded full-date conversion. Python's `zipfile` public compatibility mode clips pre-1980 timestamps to *1980-01-01*; a future product conversion rule must explicitly specify date/time and timezone semantics before adoption, not only catch exceptions blindly.

**Strongest self-critique:** This is a small synthetic two-archive vector and a single Windows Server/Python runtime. It does not measure exploitation, all Win32 versions, older macOS runtime limits, ZIP64, archive byte economics, transient I/O, RSS, crash integrity, or output-publication safety. Source currently opens output path `wb` and known O143 stage failure is independent; no claim of atomic ZIP output. This branch modifies no Reader source. No release, merge, format/version change, official performance or discovery policy update. Subsequent hosted macOS/comprehensive CI must be inspected and the result appended without rewriting this negative.
