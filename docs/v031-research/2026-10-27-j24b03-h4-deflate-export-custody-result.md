# J24B03-H4 — direct-Deflate ZIP export custody: result and integration boundary

Date: 2026-10-27 UTC. Research/product-code evidence on existing Reader protection owner [PR #609](https://github.com/FCMO-AI/.CMPCT/pull/609), **not a merge/release authorization**.

## Authority and prospective freeze

- Published v0.30.0/r24: `main@80c358f8824ec1b20d349c92ed94c898090969b0`.
- Pre-H4 candidate (H3) was frozen at `068f24af02ef422d9c71e7cfd81ed4e81b032fa6`, Reader Git blob `0aa5ef60e8dacde07226062b476bc819698807ef`.
- H4 preregistration **landed alone first** at `d992f578e5583527937c9644f8f3a964304533cd`; no test, evaluator, or Reader source H4 changes preceded its question/kill conditions.
- Minimal Reader implementation at `b4f09e4032461990560d94d60a889a793ea1d497`, Reader blob `72a1fd0acda62e518d53594c521391d42a9190e4`. Same format, unchanged Builder, codec choices, native ABI, ZIP wire generation on valid inputs, and #569/#615 ownership.

## Primary question and discovered product path

`CMPCT.export_zip` can emit direct stored Deflate byte streams from `_direct_deflate_stream` without invoking `_blob()`. H3 made ordinary `read/read_range/verify` reject unsupported physical BHDR control bits, but that export fast path still trusted physical fields without checking their agreement with the signed logical owner. A valid ZIP could therefore be produced from a **malformed CMPCT archive rejected by strict preflight and ordinary read**. This is an operation-level safety-bypass, not a compression invention.

H4 adds **constant-time** checks before zero-recompression Deflate reuse: directly declared row size must equal the indexed physical owner size; physical BHDR magic, codec, flags/reserved, compressed/uncompressed/meta lengths must agree with the index; record and compressed stream span must fit inside mmap. No per-read whole SHA or index-wide scan was added.

## Source-exact hosted result

Original [GitHub Actions #40604548602](https://github.com/FCMO-AI/.CMPCT/actions/runs/40604548602), PR HEAD `aae734f2d5dca1bdc2ac5aace9596594739a378e`: **paired signed-wire H3-vs-H4 courts and independent referee completed on Ubuntu 24.04, macOS 14, Windows 2022**. On *each* host:

- 2/2 authentic Builder-independent direct-Deflate regular/symlink controls: preflight, read, verify and fast ZIP export accepted. Original complete ZIP bytes preserved between H3 and H4, and exported compressed-stream SHA-256 equals the original physical Deflate stream.
- 8/8 unsupported physical `flags`/`reserved` bit mutations plus 2/2 independent index-re-signed logical 136/physical 128 contradictions: H3 `export_zip` **accepted all 10** while strict preflight rejected; H4 `export_zip` **rejected all 10**.
- The separate stdlib referee independently checked the unchanged compressed streams, one-field physical changes, signed-index size variant, same input digests, source separation and complete ZIP identities; terminal decision `H4_DIRECT_DEFLATE_EXPORT_CUSTODY_CONFIRMED`. In total **30/30 rejected H4 adversarial exports across hosts**; 6/6 controls preserved across hosts.

Original workflow overall outcome differed by host: **Ubuntu SUCCESS including 12 targeted pytest tests**. **macOS/Windows job FAILURE at targeted pytest collection**, *after* paired court/referee PASS, because unrelated legacy `tests/conftest.py` imports historical `experiments/entropygraph_v025.py` which requires ambient `libzstd.so` unavailable on those runners. This is not a failure of the H4 paired scientific claims but is still a real failed CI job. Original raw receipts are in artifact IDs: Ubuntu `12780870349` (provider ZIP SHA-256 `7e75f3a96bda4983ebeda8ed170e177edb0e274cee1293d56d4fdd303e323eba`), macOS `12779902223` (`9cf3a55c7f4a7c556df31b6910c2137bed2c7207962989247c7d0a294c590a70`), Windows `12780930230` (`225129b6e4e22bbec09953cec541bc744fff191f1744d5dff39fa8321114272c`). Digests are hosted provider metadata, not an independent local re-download audit.

A narrow workflow fix at `0d77b54e618e1b1eb93a2095183bb815357717a2` invokes **only the newly added standalone 12-test module** with `pytest --noconftest`. The tests depend solely on `tmp_path`, not the legacy broad suite fixtures. Tests/assertions, Reader source and frozen H3 control are unchanged. [Exact-head rerun #40605130372](https://github.com/FCMO-AI/.CMPCT/actions/runs/40605130372) was queued at the time of this note; a successful rerun must be observed before changing the full-host CI verdict.

## Interpretation, negatives and exported costs

**Product-code evidence:** an O(1) physical framing/owner guard is implemented. **Scientific/product-path evidence:** its rejection of these ten classes and preservation of original direct-Deflate ZIP bytes is source-exact and confirmed on three platforms. **Evidence-enablement:** the macOS/Windows first-run failure belongs to unrelated legacy pytest setup, not the scientific referee. **Unmeasured:** whole-system ZIP export wall/CPU/RSS, huge member counts, mutable-inode time-of-check/time-of-use races, ZIP64 fallback, full extract/recovery, atomic ZIP output, tampered compressed payload SHA authenticity, full v0.31 composed Reader or official release-parity.

In particular, H4 checks header/geometry but does **not** authenticate a reused compressed stream cryptographically as a full content read would. A malicious physical payload altered without changing the indexed fields may still produce a broken/inconsistent ZIP. No claim of full archive integrity or zero-overhead export is earned here. The already measured J24B03-M/M2 direct RAW read latency debt remains separate, as does #569's approximately 27–28x chunked cold-open regression.

## Scientific disposition and next action

The narrowly preregistered H4 static hypothesis is **CONFIRMED** at the paired-court evidence rung; CI full-host acceptance and general product parity remain separate gates. Three adjacent direct header-family activations now support a **frame review**, rather than indefinitely gardening another header field: compose the smallest proven physical-ownership guards with the existing #569 Reader owner, then attack measured global Reader open/reader architecture and existing hardlink/recovery debts. Never weaken exact semantics/evaluators to pay timing debt. PR #615 owns hardlink alias size; PR #574 owns Discovery state, left untouched. No merge, release, format change or Discovery policy promotion.
