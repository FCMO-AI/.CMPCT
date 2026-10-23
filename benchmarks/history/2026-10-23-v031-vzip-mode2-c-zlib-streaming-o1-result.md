# VZIP Mode-2 streaming native libz O1/O1b — decisive result (2026-10-23)

## Decision, evidence class
**O1 result: 78/84 byte-identical with Python single-call; six byte-different.** All six failures are on Deflate level 0 with feed sizes 1 or 4096 bytes for three inputs >64 KiB. **O1b independent causal control: 84/84 byte-identical between C/libz and Python/libz when both receive the SAME input-feed segmentation; Python chunk-fed vs Python one-shot differs in exactly the same six coordinates.**

This proves the six failures are attributable to input feed boundaries **in the tested single zlib provider/version/runtime**, not to an independent C-vs-Python compressor implementation difference. **Neither conclusion establishes universally byte-exact streaming for arbitrary callers/versions/data.** C/libz is a credible bounded-memory *research candidate*, not a native CMPCT Reader capability. The original O0 rust_backend negative (26/28 differences) remains controlling for that separate provider.

## Frozen hypotheses and source identities
- PR #282 stacked on independent PR #278 `4a6755c407329467dd872416aae898757dcc0a69`; unchanged canonical development `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`.
- O1 prereg before implementation/outcomes: `benchmarks/history/2026-10-23-v031-vzip-mode2-c-zlib-streaming-o1-prereg.md`, initial commit `4f7101a848bbb5db826296802e2dd4f034a2895b`.
- After observing initial six mismatches, O1b feed-boundary causality prereg **before changing its experimental harness**: `benchmarks/history/2026-10-23-v031-vzip-mode2-libz-feed-boundary-o1b-prereg.md`, commit `2657e76ffc18587ca8c7cd5f2cbfe24629442599`.
- **O1 original exact-head hosted** `f945f5ae5e1162afe913b12450900c5ec4ef76eb`; [run 40018627548](https://github.com/FCMO-AI/.CMPCT/actions/runs/40018627548) SUCCESS; [artifact 12528599787](https://github.com/FCMO-AI/.CMPCT/actions/runs/40018627548/artifacts/12528599787). Confirms 78/84, six mismatches.
- **O1b exact-head hosted** `da8407bf8a3ac6fb1b58f974edc06a9a8e65c94a`; [run 40018780012](https://github.com/FCMO-AI/.CMPCT/actions/runs/40018780012) SUCCESS; [artifact 12530091149](https://github.com/FCMO-AI/.CMPCT/actions/runs/40018780012/artifacts/12530091149), downloaded ZIP sha256 `9e37af35124483bb67bd19b7a605241c8f72392cfb36d91ac520a826d2e0f682`.
- Artifact contains `o1-native-libz.json` **71,177 bytes** of raw per-case source hashes, native/Python stream lengths, digests, feed-matched comparison flags, first mismatches and diagnostic subprocess wall times, plus compiler/libz/linker and source blobs.
- Same Ubuntu 24.04 job: CPython **3.11.17**, Python zlib compiled/runtime **1.3**, C dynamic libz **1.3**; Linux 6.17 x86_64. Local preliminary 3-family C/Python3.13.5/libz1.3.1 smoke on a different host was positive but is not authority for the hosted result.
- Frozen independent 861-byte archive SHA-256 `febef1d1f1157066204c468d74e81e14c6f79d1490ab2e76e024beed3ce3fb81`; exact 75-byte member SHA `708bee4f14697a0938db8dffa4b2f2783db2b662bd279ea584e717daf70cb1fc`. Level-6 native streaming under all three feed chunks returned original exact 13-byte stream `4b4c4a4ec483929350105ec500`.

## Full nonidentical coordinates, unchanged by O1b
| Family | Deflate level | C chunk | C output | Python one-shot | First byte difference |
| --- | ---: | ---: | ---: | ---: | ---: |
| shifted_related_64k | 0 | 1 | 65,551 B | 65,546 B | 1 |
| shifted_related_64k | 0 | 4096 | 65,551 B | 65,546 B | 1 |
| structured_logs | 0 | 1 | 70,671 B | 70,666 B | 1 |
| structured_logs | 0 | 4096 | 70,671 B | 70,666 B | 1 |
| json_rows | 0 | 1 | 78,527 B | 78,522 B | 1 |
| json_rows | 0 | 4096 | 78,527 B | 78,522 B | 1 |

- **7 families × 4 levels × 3 feed sizes = 84** cases.
- **C vs Python-one-shot:** 78 identical, 6 different.
- **C vs Python-same-chunks:** 84 identical, 0 different.
- **Python-same-chunks vs Python-one-shot:** 78 identical, 6 different, exact same coordinates.
- Native output stable across two independent executions per tuple; all produced Deflate streams inflate to original source. Under same linked libz1.3/provider, input segmentation alone changes physical raw Deflate output on those level-0 cases.
- Cross-provider original rust_backend/miniz_oxide exactness remains decisively negative independently (PR #278).

## Cost, safety and portability
The native probe allocates two fixed 65,536-byte arrays and refuses >1 MiB source input. It writes incrementally to stdout; the **Python experimental controller** materializes synthetic test data and subprocess output, so this does **not** establish product-level bounded RSS for large archives or streaming integrated native Reader. The complete hosted Python oracle recorded peak 19,168 KiB for itself and children; diagnostic single-process median wall around 1.19 ms includes fork/exec/pipe overhead and has no same-semantics product comparator. Raw hashes/bytes are preserved; no claimed compression gain, extraction throughput, selective work, broad archive fidelity or platform certification. Different zlib versions, strategies, chunk scheduling, Windows/macOS/Android and malformed native reads remain untested.

## Counterfactual / next decision
The frozen 75-byte anchor could have ruled out the Rust backend cheaply, but **could not detect the level-0 segmentation-dependent counterexample**, because it fits in one input chunk. A stronger *prospectively recognizable* oracle compares both library/provider and exact feed schedule on a >64KiB level-0 member before claiming universal native bitstream identity. This is a local transferable test-design lesson, **not** sufficient evidence to change normative Discovery Engine policy.

Next executable fork: decide whether native mode-2 should (a) bind provider *and* feed schedule through explicit versioned semantics plus portability controls, or (b) refuse native Mode 2 / retain original Deflate stream in Mode 1. Do not threshold-garden chunk sizes from this small matrix. Any future native integration must pass exact Reader/ABI, hostile/conformance, SHA, full filesystem and complete performance/portability gates before release.

**No production code, canonical revision, frozen benchmark, evaluator, policy, state cache, merge or release changed.**

## Cross-version local corroboration — complete digest, not release parity

Independent **local**, NOT GitHub Actions product or exact-head CI: CPython 3.13.5 / libz 1.3.1 regenerated raw Deflate on all seven immutable O0 family seeds and four levels (28 streams), comparing **complete SHA-256 + encoded byte lengths + complete source SHA-256** with O0's actual hosted CPython 3.11.17 / libz 1.3 reference JSON from PR #278 [run 40014722192](https://github.com/FCMO-AI/.CMPCT/actions/runs/40014722192), artifact 12528086507 (source `262b368e9022cb79c3ec5b57c35347e2d32cfb90`). **28/28 complete stream digests and source digests matched** on the local host (original evidence ZIP SHA256 `60943abf511251cbcb949ab50476b05aa220cc3c4790e13dd4e8839c22d9fa77`; local comparison JSON SHA256 `79c29a034d38fd323b6eccef7c59d5136207be1d9f88be9a0dbce2cff8c36c9f`). This is limited evidence of cross-version equality on *those exact inputs with a single Python compress call*, not a claim of universal zlib parity, cross-platform parity, or parity across feed-boundary schedules. The original six O1 streaming negatives survive unchanged. Unlike the original 12-character prefix diagnostic, the subsequent check used the complete artifact digests.
