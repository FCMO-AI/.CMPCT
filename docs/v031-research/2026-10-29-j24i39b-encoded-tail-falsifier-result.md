# J24I39b — compiled Claxon does NOT accept the three basic invalid FLAC suffix families

**Observed 2026-10-29 UTC / scientific negative for one specific failure mechanism / no product fix, merge or release.** Based on prospective preregistration commit `c48fa97a73140b08558edb0945ddfb7d263fd1fa`, original actual source `55d672272a48413a9ef9dd97eadb3ee5b71cebe5`. The hypothesis that an extra arbitrary 21-byte FLAC trailer could pass the existing `Claxon::samples()` digest loop was **NOT supported**. Do not retrofit the scientific question to claim a broad codec validation proof.

## Actual hosted execution

[GitHub Actions J24I39b #40934324693](https://github.com/FCMO-AI/.CMPCT/actions/runs/40934324693), job `123660723525`, Ubuntu 24.04, **SUCCESS** with real instrument compilation, original Builder fixture and detached source auditor, and four cases executed. Genuine 8-MiB+44B Builder WAV's original physical archive SHA-256 `9250964815f67891c3e106c9d87aadc67d4f2c3dce8b3e4e1873813a13a6fac7`; original split FLAC SHA-256 `d2126c870dcba10ad7f9d7b6caf83ca0c0df2815b9e47be343f3ed3b3b1355e8`. No source/index/CMA4 mutation was needed for this independent *encoded-stream* falsifier.

| FLAC input | Encoded bytes | Reference `flac -t` exit | Actual compiled Claxon logical-digest oracle exit |
|---|---:|---:|---:|
| Genuine original | 3,982,561 | 0 | 0 |
| +21 bytes invalid trailer | 3,982,582 | 1 | 101 |
| Final 64 bytes removed | 3,982,497 | 1 | 101 |
| Full second FLAC appended | 7,965,122 | 1 | 101 |

Raw host log reports `TRAILER_GAP_NOT_DEMONSTRATED`; exact SHA-256 fingerprints for each mutation and source-bound outcomes are preserved in [research/j24i39/hosted_tail_result.json](../../research/j24i39/hosted_tail_result.json). The logged Claxon **exit 101 is an uncaught Rust panic on the research probe's error path**, not a successful logical verification. No claim that the parser itself emitted a specific class of error until per-case logs are recovered.

**Evidence infrastructure negative discovered:** `actions/upload-artifact` completed as a warning stating that no files were found under the paths, so the original hosted artifact was NOT preserved. The executed job log and its exact source HEAD remain durable on GitHub, and the condensed result/identifiers are committed in this repository. We must repair artifact custody before claiming a reproducible full physical specimen bundle. CI success in this case proves the custom scientific court completed and classified outcomes; it did not prove artifact delivery.

## Interpretation and next discriminator

J24I39a's 5.746× faster and 56,296KiB-lower-RSS *standalone file-backed digest* remains a valid lower-rung logical reconstruction oracle, but is not an archive-integrity-equal product benchmark. Three simple appended/truncated/concatenated cases do not demonstrate a Claxon tail *acceptance* defect, and do not prove universal strict frame consumption, metadata admission, corrupt CRC inside frames, source-inode custody, or adverse resource limits.

The next useful narrow experiment is to reproduce the four cases with explicit Claxon error classification **and** guaranteed persistent evidence artifact, plus a physically reassembled revision-24 CMA4 hostile case only when Native Core owner requires it. Do not change archive evaluator, source, version or thresholds to rescue a hypothesis. No Discovery Engine policy change warranted.
