# A14-O1a — naturally occurring Linux/OS byte-window admission test

Date: 2026-10-28 UTC  
Status: **ZERO ADMISSIONS ON TESTED CORPUS; EXTERNAL-GENERALITY NOT PROVEN**. Post-O0 held-out falsifier (research only), preregistered before observations at [A14-O1a freeze](2026-10-28-a14-heldout-os-prereg.md). Original A14-O0 prediction and verdict remain unchanged.

## Direct result
The exact unchanged `research/a14_derived_crc_o0.py` candidate detector (SHA-256 `f6f5fb61afb4549f6f1afc248b1418a396bc6756676a44b039791ad9ed289262`) was applied locally to **224 naturally occurring public OS files** (not synthetic records). Four source categories were fixed prospectively. From each selected file, three independent **4 KiB** windows (start/middle/end) were inspected.

| Kind | Files | 4 KiB windows | Candidate geometries evaluated | Admitted CRC geometries |
|---|---:|---:|---:|---:|
| ELF executables | 64 | 192 | 5,760 | 0 |
| Python standard-library source | 64 | 192 | 5,760 | 0 |
| Shared-object binaries | 64 | 192 | 5,760 | 0 |
| JSON schemas/resources | 32 | 96 | 2,880 | 0 |
| **Total** | **224** | **672** | **20,160** | **0** |

The detector made **20,160 CRC comparisons** in total: each sampled candidate was rejected after the first mismatch. No candidate reached the full-regime admission phase. Total local scan wall ~830.403 ms for input enumeration + reading + SHA manifest + scan. This is a *single unreplicated local instrument observation*, not a throughput claim or cross-host measurement.

The selector scans regular nonsymlink files of size 8 KiB–2 MiB, using sorted public OS file paths. Publication contains **no raw file content or individual names/hashes**; reproducibility is tied to a source-corpus manifest SHA-256 `e8007065ba050b010ec9815f0ccc615255e3685adc9d89264eff8cc6c965afc2` and source-selection instrument `research/a14_heldout_os_court.py`. Environment: Linux 6.18.55 x86_64/glibc 2.41, Python 3.13.5. Full raw aggregate [JSON observation](../../research/evidence/a14_heldout_os_o1a_20261028.json) (the relative repository path can be resolved as `research/evidence/a14_heldout_os_o1a_20261028.json`).

## Negative knowledge / self-critique
This **does not support a claim of common applicability**. Precisely zero of 672 tested byte-windows used a detectable regular CRC32 field in the narrow fixed record grammar. It also does *not* prove false-admission probability is zero, since no legitimate CRC-bearing record was discovered here. Arbitrary 4KiB cuts may destroy original record alignment, and the sample heavily favors OS executables/text rather than known telemetry/protocol/checksum-framed data. Source installation is environmental, not permanently frozen public test fixtures.

The result appropriately lowers broad-priority confidence: a derived CRC representation is a conditional specialized capability, not a universal compressor. A product addition that scans every arbitrary file would pay admission cost on data like this without any storage gain. Such a selector must be cheap, gated by content-only evidence, and preserve direct fallback; the unchanged sampling scan alone does not show an economic case.

## Next discriminator
If future broader addressability is claimed, choose **naturally occurring checksum-framed records with fixed public provenance and a held-out sibling control**, apply the same search grammar unchanged, and compare complete archive bytes and create/selective-read work against direct + transpose + strong conventional codecs. Do not use more friendly planted CRC rows to inflate apparent prevalence. Until that evidence, **PARK product integration** while preserving this O0 seed and the negative O1a result.

## Concurrency and promotion
Isolated research branch/PR #670, no changes to Builder, Reader, native, CI thresholds or `docs/discovery/STATE.json` (separate owner #574). No claim of release, merge, changed revision or product conformance.
