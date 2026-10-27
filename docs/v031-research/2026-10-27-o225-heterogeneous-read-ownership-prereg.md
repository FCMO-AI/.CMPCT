# O225 — Heterogeneous full-member read ownership falsifier

Date: 2026-10-27 UTC. **Prospectively fixed before code, results or workflow. Research-only; no Reader mutation.**

## Baseline and exact authority
- Public release `v0.30.0`, on-disk r24 remains untouched. Exact unmerged J24C02 Reader parent PR #569: `c5e13bb3fbb4cdade8b64246658ce7c7818de41f`, Reader blob `dbd4ac576a05a47eae97e1e40de89cf1de440516`.
- O223 PR #587, head `9a92c2846dbe1a8dddf6c7224b8f84cb7cfda5cf`, measured serial ~11–18x faster than `ThreadPoolExecutor.map` on **tiny one-byte RAW cached/repeated references**. O224 PR #590 independently corrected O223's inherited-child `ru_maxrss` misinterpretation; its 453–497 MiB peak is not a trustworthy per-child memory claim. Retain O223 wall, CPU, output hash evidence; do not repeat its old memory attribution.
- Adjacent owners: #569 owns product Reader; #583 owns random-range indexing; #577/#578 own native strict admission. This trial alters none of their source files, schemas or evaluators.

## Locked question
**Can the observed tiny-RAW serial superiority support a general full-member Reader concurrency policy once physical blobs are unique and genuinely decoded with Zstd/Deflate, or does it fail to transfer?**

The falsifiable primary hypothesis is **NO UNIVERSAL SERIAL**: serial advantage is amplified by the Python executor's scheduling over repeated tiny cached blobs and will not reliably dominate on distinct compressed blobs. The strongest simpler control is `serial`; the incumbent is untouched `CMPCT.read()` eager ordered map; `bounded64` is a third practical control rather than an assumed winner.

## Frozen design (source-exact, same archive bytes per arm)
- Use independent authenticated r24 head/index/footer/BHDR writer (not Builder) with real `CODEC_RAW`, `CODEC_ZSTD`, `CODEC_DEFLATE` stored frames, exact per-blob CRC and SHA, signed index digest, version 24.
- Two storage representations: `S_CHUNKS` and `S_CDC`; different-size coded payloads in the held-out variable-length control. Source metadata must survive preflight, full `Reader.verify()`, exact SHA and both near-boundary `read_range` controls **before** timing. All arms must reproduce the same logical bytes.
- Five deterministic workload families: `raw_repeat` (65,536 references / eight physical 1-byte RAW blobs), `zstd_distinct` (128 independent Zstd frames of 256 KiB), `deflate_distinct` (128 independent raw-Deflate frames of 256 KiB), `mixed_distinct` (96 distinct 256-KiB blobs across RAW, Zstd, Deflate), and `zstd_reuse` (2,048 references to eight decoded 32-KiB Zstd blobs). Compressible payloads are generated from seeded pseudorandom 4-KiB patterns repeated to the required size; all distinct-owner patterns differ and are deterministic. CPU/throughput interpretation is conditional on these regimes.
- Arms: `eager` unchanged `Reader.read()`, `serial` same Reader `_blob` sequential `b''.join`, `bounded64` same Reader `_blob` through at most 64 ordered futures at a time; all use identical admission and Reader object and full logical size/SHA verification.
- 3 independent process observations per arm/profile, randomized interleaving, 5 families x 2 representations x 3 arms x 3 repeats = **90 fresh-child samples**. Preserve sample order, PIDs, exact archive and Reader hashes, read/session CPU and wall (milliseconds), `/proc/self/status` VmHWM/VmRSS on Linux (or mark unavailable), archive stored bytes, index/decoded size and codec mix. Do not substitute `resource.getrusage(RUSAGE_SELF).ru_maxrss` for own VmHWM.
- Further byte-sensitive changed-length controls must check distinct references and whole-output SHA for all three arms; at least one authenticated but physically corrupt payload must fail the Reader rather than pass due to concurrency.

## Fixed decision criteria
1. **`UNIVERSAL_SERIAL_CANDIDATE`** only when serial is at least 1.20x faster (eager/serial median full open+read wall >=1.20) on the 65K tiny RAW case **and** serial/eager median full-session wall <=1.10 **for both distinct Zstd and distinct Deflate on both storage modes**. Also require all bytes exact, no false acceptance on the hostile control, and serial peak VmHWM <= eager +8 MiB on all decisive profiles.
2. Otherwise **`SERIAL_GENERALIZATION_NOT_EARNED`**. A positive result on only some families is a narrowed research seed, not permission to install unconditional serial execution.
3. Independently record whether `bounded64` improves complete wall time at least 1.20x against **both** eager and serial on any compressed distinct profile with no >8 MiB own VmHWM penalty; call this `BOUNDED_SUBSET_SEED` only for the actual modes where criteria hold. No averaging across modes to conceal losses.
4. If identity, admission, paired samples, CPU and own HWM attribution, source/head fingerprints, corruption refusal, or independent raw-audit invariants fail, decision is **`INVALID_SCIENCE`**, not a product loss/win. A negative scientific answer may still yield a green workflow.

## Strongest alternative explanation / uncertainty
- Linux hosted runner core count, native codec GIL behavior and OS scheduling could reverse results outside this environment. Small frames may be too cheap to benefit from threads. Real archives may have mixed decoded length, heavy dictionaries, Zstd seek/caching, I/O or memory dependencies. Benchmark includes complete Reader open and separate read-only cost so relative conclusions are bounded.
- The instrument is an oracle around a real installed Reader; it is **not** a product integration. It does not prove Windows/macOS parity, safe filesystem publication, 4GiB ZIP64, journal recovery, full parity, or format release. No `STATE.json` changes without a decision-changing measured result.
- Preserve the strongest inherited control, including the O223 serial positive and O224 memory correction. A source-valid negative beats an attractive story.

## Outcome
Land isolated instrument + independent second-root raw auditor + exact-source hosted workflow. Artifact must survive activation with workflow/run id, source HEAD and expected receipts. Report the actual results, negatives, cost and exact-head CI; notify Reader owner only after credible evidence. No merge, version, format, threshold or evaluator change.
