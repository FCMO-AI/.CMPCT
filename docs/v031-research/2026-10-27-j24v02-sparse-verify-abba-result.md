# J24V02 — source-exact sparse verification ABBA, hosted result

Date: **2026-10-27 UTC**. Decision: **RSS_PASS_NO_MATERIAL_CPU_WALL_VETO**, bounded to Linux/CPython 3.11, one synthetic sparse-family and the exact historical/candidate Reader sources.

## Authority and original evidence
- Preregistration **before instrument**: `75a8408d5afd2fe7c000e3832a02795e926fd793`, with the unchanged >=128 MiB saved and candidate <128 MiB peak predicate at 256 MiB; CPU/wall veto >=1.15x **and** +0.20s.
- Product comparator: released `main@80c358f8824ec1b20d349c92ed94c898090969b0`, Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`.
- Candidate product source: J24V01 #613 `3b2bf3c2e033fa27d77b2355821dc0087aa46873`, Reader blob `b2b7774c13a5c8235ff89786d171b7ea3ff20710`.
- Hosted trial: [GitHub Actions #40576885545](https://github.com/FCMO-AI/.CMPCT/actions/runs/40576885545), experiment HEAD `0d18ecba76c859d4cfb639d82ce797e826d65f58`, **SUCCESS**, [original raw ZIP artifact #12768175815](https://github.com/FCMO-AI/.CMPCT/actions/runs/40576885545/artifacts/12768175815), 332,278 ZIP bytes as reported by runner. Raw `abba-raw.json` is retained in that artifact.
- A first run [#40576439510](https://github.com/FCMO-AI/.CMPCT/actions/runs/40576439510) **FAIL** at an infrastructure-only `git merge-base` check because checkout depth 1 omitted the exact J24V01 ancestor. The subsequent workflow uses complete fetched candidate ancestry, preserves both source SHA and logical gates unchanged, and succeeds. Original failure remains reachable.
- Exact diff relative to owner #613 consists of **four added science-only files**, zero changes to `src/`, formats or validators. Source history and original artifact, not this note, remain authority.

## Same-wire CPU, wall and *own-process* RSS medians

Each geometry uses one genuine Builder-produced `K_FILE/S_SPARSE` revision-24 archive, three independent extents, same immutable archive SHA for both Readers, **3 ABBA cycles × 4 fresh workers = 12 workers per geometry**, 24 total. Timed calls include Reader open/verify/close, exclude Python process start/import. Peak memory comes from **current worker's own** Linux `/proc/self/status VmHWM`, not inherited-child `ru_maxrss`. Native dependencies installed under the same Python environment; exact reader source paths and file SHA recorded per worker.

| Source logical size | Metric | Published baseline | J24V01 candidate | Outcome |
|---|---|---:|---:|---|
| 256 MiB | Median full verification wall | **487.376 ms** | **171.416 ms** | **2.843× faster**, 315.960 ms saved |
| 256 MiB | Median full verification CPU | **487.314 ms** | **171.330 ms** | **2.844× less CPU**, 315.984 ms saved |
| 256 MiB | Median own VmHWM | **547,824 KiB** (534.984 MiB) | **25,478 KiB** (24.881 MiB) | **522,346 KiB / 510.104 MiB saved** |
| 64 MiB | Median full verification wall | **124.312 ms** | **44.196 ms** | **2.813× faster**, 80.116 ms saved |
| 64 MiB | Median full verification CPU | **124.304 ms** | **44.190 ms** | **2.813× less CPU**, 80.114 ms saved |
| 64 MiB | Median own VmHWM | **154,612 KiB** (150.988 MiB) | **25,592 KiB** (24.992 MiB) | **129,020 KiB / 125.996 MiB saved** |

The source code already predicts the mechanism: historical `verify()` calls `read()`, materializes a logical-size `bytearray`, copies it into `bytes`, and hashes it; J24V01 hashes existing sparse holes incrementally with a 1-MiB zero buffer and physical extents without retaining decoded blobs. The data establish one concrete full-Reader cost difference; they do not establish all filesystem or OS behavior.

## Independent court and unchanged decision

The hosted separate stdlib `j24v02_sparse_verify_referee.py` (no CMPCT import) rechecked **all 24 raw samples**, two SHA-bound original archive files, Reader source paths/hashes, ABBA order, unique cells, all paired medians and exact success count. **Five deliberately altered copies of the raw evidence were rejected.** The referee's runner stdout concluded:

```json
{"decision": "RSS_PASS_NO_MATERIAL_CPU_WALL_VETO", "saved_peak_kib": 522346.0, "tamper_rejected": 5}
```

This is an **independent receipt audit executed in the hosted workflow**, not a second independent CMPCT decoder or a separate manually downloaded ZIP replay. Do not claim that wider proof. The 256MiB 128MiB-saved and <128MiB candidate absolute memory predictions both pass; neither CPU nor wall veto fires (candidate is materially faster). 64MiB is a corroborating same-mechanism measurement, not proof of generality.

## Negative / self-critique and product boundary

- Source runs are exact but only **one Ubuntu 24.04/Python 3.11 runner**, one hole-heavy synthetic Builder archive per size, one user-space unpack/verify library execution. No Windows/macOS, hardlink sparse alias, gigantic 4GiB sparse, many-extents hostile workload, ZIP64, multi-file materialization, native portable packaging or full external-release benchmark.
- Independent referee verifies recorded file digest and receipt integrity, but the instrument's positive outcome still trusts the installed CMPCT reader and Builder for decoding; it is not an independent implementation of r24.
- The measured speedup partly comes from avoiding two large allocated logical buffers and their memory traffic. Never extrapolate the exact ratios to compressed physical extents, tiny sparse files, multiple users, cold cache, metadata or release-wide workloads.
- The J24V01 owner branch is **not merged or released**. `CMPCT.read()` still must fully materialize bytes by API design, and hardlink aliases to sparse owners remain outside the streamed verify path. Sparse `extractall` corruption-and-destination defects (#572), namespace publication #528, hardlink alias #615 and composed Reader #569's 27–28× cold-open regression remain separate blockers.
- A green CI workflow with a performance job **SKIPPED** elsewhere cannot be represented as official parity. This result is independent bounded product-economics evidence, not release authority.

## Decision and next executable target
**Meaningful product lever confirmed for this workload: full-Reader sparse verification can be bounded in memory *and* avoid costly full logical materialization, with no measured CPU/wall debt on these two geometries.** Owner #613 should decide whether this independently measured economics justifies composing J24V01 with #569's active Reader, after screening sparse-hardlink semantics. Run same-image three-host correctness, independent 4GiB and many-extents hostile cases, real extraction/salvage correctness and complete numeric performance/recovery parity on the actually composed source before merge/release. Don't fork J24V01 implementation or relax historical tests.

Discovery Engine: primary question decided positively at this rung, no concurrency collision (this science-only stack is explicitly preregistered as an independent performance replication and the #613 owner was notified before code), no policy modification or `STATE.json` write because #574 owns coordination and repeated evidence has not earned policy change. Counterfactual lesson: use own process `VmHWM`, explicit same-wire historical control, and an independent median/identity referee rather than mistaking a one-arm RSS ceiling for a baseline delta.
