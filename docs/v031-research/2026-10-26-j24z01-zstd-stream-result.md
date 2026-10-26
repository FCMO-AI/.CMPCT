# J24Z01 — fully charged bounded Zstd physical-frame streaming result

Date: 2026-10-26 UTC. **Decision: MEMORY_SEED_WITH_THROUGHPUT_DEBT; do not promote.** This is Linux-only independent native-ABI science, not a CMPCT Reader/product fix.

## Source / prereg / hosted custody
- Preregistered unchanged hypothesis **before instrument**: commit `466518562708081c8143068fb055c4dff1dc9fc0`, `2026-10-26-j24z01-zstd-stream-bound-prereg.md`.
- Exact result-bearing HEAD `b40efa926d55515bd4b4af0edcc451007d0e9398`; original authentic Reader Git blob `d2e7ed7863d9a9c598d225ca1f77e53d94c6bf44`; new oracle blob `33472d79e7225d1a6eebb27cf3bf1505cf411f42`; inherited unchanged O209 original oracle blob `0371095ee4830b5e74793577083a147946ae9d91`.
- [Hosted Actions #40420064445](https://github.com/FCMO-AI/.CMPCT/actions/runs/40420064445) SUCCESS, exact checkout, Python 3.11, original CMPCT installed, Ubuntu 24.04. [Raw artifact #12696652594](https://github.com/FCMO-AI/.CMPCT/actions/runs/40420064445/artifacts/12696652594) ZIP SHA-256 `6e04f6c9ffb28059b9b19a69e622dc5d7a3a385532b2e8f008b12d6b5baf3c68`. Raw `oracle.json` downloaded and inspected, not inferred from CI label.
- Serialized direct S_BLOB archive: **7,612 B**; compressed physical payload **7,180 B**; exact container SHA-256 `cff0cf0bb0c77eabf07b46292ef8dcc7189107a2814080ae92326ce097a02061`; full source **67,108,864 B**; original logical SHA-256 `e2cb9873a8fbf8708fd5137ad2737bc1da5dfafcaff139a057b989e6c4cc16ec`. Same physical archive for Reader and streaming oracle. Inherited 64x1MiB chunked archive **77,506 B**, explicitly +69,894 B; not used as a same-bytes timing comparator.

## Predeclared decision and actual results
Preregistered P1 required >=32 MiB lower fresh-process kernel VmHWM for streaming; P2 required exact selected 1 MiB, full 64 MiB physical CRC32+SHA256 and authenticated source; P3 required <=64 KiB output buffering; P4 required both CPU and wall <=2x control for favorable full-product candidate economics.

| Metric — five alternating fresh independent child processes | Original Reader A | Bounded streaming oracle B |
|---|---:|---:|
| Kernel VmHWM increment median | **131,500 KiB** | **17,136 KiB** |
| Kernel VmHWM increments KiB | 131452, 131536, 131512, 131440, 131500 | 17152, 17228, 17128, 17136, 17128 |
| Complete open+range wall ms | 22.25, 22.43, 21.96, 22.07, 22.41 | 53.19, 52.41, 52.84, 52.83, 54.96 |
| Complete open+range CPU ms | 22.26, 22.42, 21.94, 22.08, 22.41 | 52.57, 51.84, 52.26, 52.23, 54.27 |
| Logical selected bytes | 1,048,576 | 1,048,576 |
| Physical decoded bytes | 67,108,864 | 67,108,864 |

- **Memory margin: 111.68359375 MiB lower** for streaming (P1 PASS, genuine different ownership with same container bytes).
- **CPU ratio B/A: 2.348212187x; wall ratio: 2.374640491x** (P4 FAIL). This is confirmed added complete decode/verification work in the experimental Python/C ABI route, not noise or permitted release economics.
- B streamed using **1,024** output iterations, max compressed input block **7,180 B**, max decoded output buffer **65,536 B**, selected output **1,048,576 B**. Full CRC32 and SHA-256 validated; exact sample SHA-256 `77a780026c6c37dae50fd91c470440b0feb7d76a35c644478a50f59b451dcf0d` (P2/P3 PASS).
- C ABI: system libzstd **1.5.5**, intentionally experimental; CMPCT's package-owned Rust Zstd remains authoritative.
- Negative controls *separately executed* on the authentic archive's decoder-visible compressed bytes: corrupt middle -> `Data corruption detected`; truncate last byte -> `truncated or non-progressing Zstd frame`; append after authenticated frame -> `trailing compressed data after first frame`. All rejected.

## Causal and counterfactual analysis
O209's 125.765625 MiB advantage from physically chunked storage was not necessary to achieve large RSS reduction: **the same 7,612-byte archive** can be processed with bounded streaming by an independent decoder. This uncouples physical storage-byte overhead from decoded-memory ownership for the tested case. However this initial solution pays about 2.35x CPU and wall, likely including 1,024 ctypes transitions and repeated Python-side integrity accounting. Attribution to those sources is *hypothesis*, not yet measurement. Next cheap falsifier: change only fully bounded output-decode granularity, preserve exact physical bytes/source and entire SHA/CRC checks; if wall and CPU cannot approach original, retire Python-callback streaming as product path and evaluate package-native Rust streaming separately.

Prospective lesson: before changing chunk layout to bound RSS, compare a **same-container streaming decoder oracle** with full integrity charges; storage fragmentation is not the only option. Evidence-backed architecture lesson, not an automatic change to Discovery Engine policy.

## Limits, non-credit and next owner
- Linux, one highly repetitive synthetic 64 MiB frame; no broad corpus, cold-device I/O, concurrency, source-race handling, dictionary codecs, full ZIP64 file, Windows/macOS ABI or general installation behavior.
- Complete **64 MiB decoded work remains mandatory in this oracle** to validate full CRC/SHA; output buffer alone does not imply selective physical I/O or decoder CPU savings.
- No product code, release benchmark, format, frozen comparator, Discovery policy, version or source owner modified.
- O193 Reader owner #521 and O209 parent #548 should evaluate a package-native bounded decoder only if both **peak RSS and CPU/wall debt** can be paid under real Reader/full ZIP64 semantics. **No merge or release credit.**
