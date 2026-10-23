# VZIP mode-2 native backend parity — result (2026-10-23)

## Decision

**CURRENT_RUST_BACKEND_NOT_DROPIN_BYTE_EXACT_MODE2** — 26/28 same-input, same-level raw-Deflate streams differed, even though both independently inflated exactly and native emission was repeatable. This definitively rejects using the **current flate2 rust_backend/miniz_oxide** as a byte-exact replacement for Python zlib in revision-24 VZIP stream mode 2. It is NOT a failure of Deflate losslessness, proof of other Rust/zlib backends failing, or a shipping product regression.

Research episode VZIP-M2-BACKEND-001 was committed *before implementation or result* in [prereg](./2026-10-23-v031-vzip-mode2-native-backend-parity-prereg.md) at commit `386f2d2b8b88a7f71aa644b8cd2cb3dead42fa73`.

## Exact-source hosted evidence

- Exact research HEAD: `262b368e9022cb79c3ec5b57c35347e2d32cfb90`, continuing PR #278; initial development source `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`.
- GitHub Actions workflow: [run 40014722192](https://github.com/FCMO-AI/.CMPCT/actions/runs/40014722192), step `Execute same-input exact-byte and independent inflate court` **SUCCESS**.
- Raw artifacts: [artifact 12528086507](https://github.com/FCMO-AI/.CMPCT/actions/runs/40014722192/artifacts/12528086507), downloadable ZIP SHA-256 `60943abf511251cbcb949ab50476b05aa220cc3c4790e13dd4e8839c22d9fa77`. Contains `mode2-native-backend-court.json` with complete 28 per-case SHA-256/length/equality/first-mismatch receipts and golden stream hex, plus source-head/blob and runtime identity.
- Probe source: `native/cmpct-core/src/bin/vzip_mode2_backend_probe.rs` and `benchmarks/v031_vzip_mode2_native_backend_probe.py`. No production Reader/Builder source or VZIP recipe altered.
- Runtime: ubuntu-24.04 Linux 6.17 x86_64; Rust `rustc 1.99.1`; `flate2 1.1.10` with `miniz_oxide 0.9.1` (`rust_backend`); CPython 3.11.17 linked against zlib 1.3.
- Families: immutable 75-byte independently generated VZIP mode-2 member, 8192 zero bytes, 32768 seeded random bytes, alternating pattern, 65536 shifted related bytes, structured synthetic log text and synthetic structured JSON rows.
- Levels: 0, 1, 6, 9; 7 families × 4 levels = **28**.
- **2 byte-identical; 26 nonidentical.** Both identity cases were the 75-byte golden and zeros at level 0. Every stream decompressed to source data exactly with zlib; native repeated-run determinism held in all cases.
- Independent frozen anchor: Python zlib level 6 reproduced immutable 13-byte RFC-1951 stream `4b4c4a4ec483929350105ec500`. Current Rust backend yielded **23 bytes** `7dca310d000000c230ad30ff1eb87996f46c4a043d9a07` for the identical 75-byte content and requested level. Both independently decompress to the exact same 75-byte content SHA-256 `708bee4f14697a0938db8dffa4b2f2783db2b662bd279ea584e717daf70cb1fc`.

## Mechanism and claim boundary

Revision-24 VZIP mode 2 regenerates an exact nested ZIP stream from content bytes and a declared zlib compression level. A standards-compliant but byte-different Deflate bitstream changes the exact nested ZIP representation and invalidates its SHA-256. This probe isolated input, compression level, raw-Deflate framing and full-stream finish on the same host; the backend implementation is the material remaining difference. It does **not** prove which block-selection heuristic caused the divergence.

The native `Unsupported` status in production remains correct. Revision-24 mode 1, which stores the exact Deflate stream, remains the stronger simpler control for byte identity. Do NOT flip native mode-2 support using only `flate2::write::DeflateEncoder` / rust_backend.

## Cost/uncertainty and recommended next fork

The test materialized <=1 MiB per input, executed detached binaries and **did not** measure product archive bytes, resident memory, cold open, native integrated selective reads, CPU, throughput or multi-OS portability. Version-specific parity with another backend is unmeasured.

**Cheapest decisive next unclaimed action:** test a *detached* package-native zlib backend with an exact version/provider fingerprint against the frozen 75-byte anchor and held-out matrix; do not change the shipping codec feature set just for this oracle. If fixed-source parity is established, price explicit dependency/version/portability and complete-member integrity before extending native VZIP representation/dispatch. Otherwise preserve typed Unsupported or retained-exact mode 1. Do not treat a friendly vector as universal parity.

## Counterfactual and policy

A single 75-byte level-6 source-locked anchor would have rejected this backend **before** a full native-dispatch implementation: 23 B vs 13 B. It was prospectively accessible from PR #278. This is a transferable probe-selection lesson, **not** enough evidence to mutate the Discovery Engine's normative policy or release thresholds.

**Classification:** decisive O0 backend compatibility negative. **Format change: NONE. Native product support: NONE. Release credit: NONE.**

## Compact 28-case exact-stream matrix (hosted evidence)

The two 12-character SHA-256 prefixes below are **diagnostic abbreviations only**, not authentication receipts; full SHA-256 and per-case source IDs remain in the source-bound JSON artifact. Identical compressed sizes do **not** imply identical streams (e.g., zeros at level 6 or structured logs at level 9).

| Family | Level | Python zlib bytes | Rust native bytes | Byte-equal | First differing offset | zlib SHA prefix | native SHA prefix |
|---|---:|---:|---:|:---:|---:|---|---|
| golden_75 | 0 | 80 | 80 | YES | - | 9e1ab83d0b3c | 9e1ab83d0b3c |
| golden_75 | 1 | 16 | 23 | NO | 0 | 0ce199fccb92 | 81900be84eed |
| golden_75 | 6 | 13 | 23 | NO | 0 | 803f9173e4fd | a1ec3339f9a2 |
| golden_75 | 9 | 13 | 23 | NO | 0 | 803f9173e4fd | a1ec3339f9a2 |
| zeros_8k | 0 | 8197 | 8197 | YES | - | eed86045d2f8 | eed86045d2f8 |
| zeros_8k | 1 | 53 | 54 | NO | 7 | 13d937c82e1d | 0e4a77f28e99 |
| zeros_8k | 6 | 25 | 25 | NO | 1 | f2535cbe7473 | 6fc25a7a6c54 |
| zeros_8k | 9 | 25 | 25 | NO | 1 | f2535cbe7473 | 6fc25a7a6c54 |
| high_entropy_32k | 0 | 32778 | 32778 | NO | 1 | 627e3f61213c | 6c5923184843 |
| high_entropy_32k | 1 | 32778 | 32773 | NO | 0 | a0a5d81c0ec2 | 6b741168ff92 |
| high_entropy_32k | 6 | 32778 | 32778 | NO | 2 | 2026faf41621 | 6c5923184843 |
| high_entropy_32k | 9 | 32778 | 32778 | NO | 2 | 2026faf41621 | 6c5923184843 |
| alternating_pattern_32k | 0 | 32778 | 32778 | NO | 1 | 9492c6ab044e | f34ab0bf400b |
| alternating_pattern_32k | 1 | 181 | 189 | NO | 5 | 7b15237c12db | 9191f7d1b8c4 |
| alternating_pattern_32k | 6 | 52 | 52 | NO | 2 | 830f08af7efb | 36e98da1f44c |
| alternating_pattern_32k | 9 | 52 | 52 | NO | 2 | 830f08af7efb | 36e98da1f44c |
| shifted_related_64k | 0 | 65546 | 65551 | NO | 1 | bd0244c3eff9 | 858a2f1dca4f |
| shifted_related_64k | 1 | 65556 | 65595 | NO | 0 | 6914af154cad | 54cfdbbb9d46 |
| shifted_related_64k | 6 | 65556 | 65551 | NO | 2 | e157931f3fa4 | 858a2f1dca4f |
| shifted_related_64k | 9 | 65556 | 65551 | NO | 2 | e157931f3fa4 | 858a2f1dca4f |
| structured_logs | 0 | 70666 | 70671 | NO | 1 | 2dfb098bfb02 | e7b760844ee2 |
| structured_logs | 1 | 8480 | 9279 | NO | 1 | 1728cb69e502 | 5ab2e1debaed |
| structured_logs | 6 | 7227 | 6561 | NO | 2 | 1178768fabd5 | bf4ca1a553b4 |
| structured_logs | 9 | 6508 | 6508 | NO | 2 | 55b1b6f15b97 | 1eb987a2bf3d |
| json_rows | 0 | 78522 | 78527 | NO | 1 | 6bda52599957 | 10b23c9326f3 |
| json_rows | 1 | 10832 | 10553 | NO | 2 | 6d8b7e023719 | 5644fef62cf0 |
| json_rows | 6 | 8382 | 8080 | NO | 2 | c51bfa53fa26 | 034e890414b5 |
| json_rows | 9 | 8019 | 8067 | NO | 4 | fc46d2a24dc6 | 0e414824009f |

**Sanity:** 28 cases, 26 differences; identical level-0 streams appear only in the golden-75 and zeros-8k rows. All other rows have fully decodable streams yet cannot substitute for the frozen output. This result provides an inexpensive falsifier for future native codec integration; it is not a compression-performance ranking.
