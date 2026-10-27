# J24Z02 — pooled 64-KiB Zstd streaming dominates reference streaming on tested host, but misses continuation threshold

**Result date:** 2026-10-26 America/Mexico_City (hosted 2026-10-27 UTC). **Research decision:** `POOLED_PYTHON_NOT_PRODUCT_PRIORITY`. No Reader, format, comparator, product version or release modification.

## Frozen hypothesis / evidence custody

The preregistration was committed **before** implementation at `6e5b4e70b6f1fc402e829c3d1f4cc86a741e4385`: eliminate repeated Python output-byte allocations at fixed 64KiB, preserve full CRC32/SHA256 and select exact 1MiB. Prospective success required **both** >=15% same-host median CPU and >=15% wall improvement over the untouched original 64KiB streamer and <=4MiB kernel VmHWM regression. Parent #550 J24Z01 and #548 O209 are the inherited controls.

- Original exact-HEAD specialized GitHub Actions [run #40426455674](https://github.com/FCMO-AI/.CMPCT/actions/runs/40426455674): **SUCCESS**, source HEAD `8ce7e7a4be2df5e61e18914a0c979bb3d6b9ba93`.
- Original [raw artifact #12699657959](https://github.com/FCMO-AI/.CMPCT/actions/runs/40426455674/artifacts/12699657959), ZIP SHA-256 `0cfbd2ff4b39a9adac50d3ac21423532d5224968a4575fbc9eaa71cddf1ea8d5`. The ZIP's `court.json` was independently downloaded and inspected, not inferred from workflow SUCCESS.
- Source identity: Reader Git blob `d2e7ed7863d9a9c598d225ca1f77e53d94c6bf44`; candidate instrument blob `9522f2b71115eb40c9c34df49e3218a4225088a5`; exact r24 archive **7,612 bytes**, SHA-256 `cff0cf0bb0c77eabf07b46292ef8dcc7189107a2814080ae92326ce097a02061`; logical member 67,108,864 B, requested range 1,048,576 B.
- Linux Ubuntu 24.04 Python 3.11 genuine CMPCT installation, 5 rotating *fresh child* process rounds per arm. Archive bytes and content identical in every A/B/C arm. Initial [run #40426344559](https://github.com/FCMO-AI/.CMPCT/actions/runs/40426344559) failed solely because default shallow checkout did not contain prereg commit for the ancestry proof. Workflow fetch-depth corrected; historical infrastructure FAILURE retained.

## Three-way raw-run medians — same source / same host

| Exact arm | CPU median (ms) | Wall median (ms) | Fresh-child VmHWM increment (KiB) |
|---|---:|---:|---:|
| Authentic CMPCT `read_range` | 23.089271 | 23.087224 | 131,464 |
| Untouched J24Z01 64KiB streamer | 55.471685 | 56.086871 | 16,976 |
| New pooled fixed-64KiB streamer | **47.563273** | **48.222993** | **3,772** |

**Direct prospective comparison:** pooled CPU improved **14.25666446%** and wall **14.02088913%** over original streaming: **both below 15% predeclared continuation threshold**. VmHWM decreased an additional **12.89453125 MiB** relative to J24Z01 and **124.69921875 MiB** relative to full-frame Reader control. Pooled remained **2.060x CPU / 2.089x wall slower** than the authentic Reader, despite lower memory and unchanged archive size. Different GitHub run timing regimes previously varied materially; do not compare these absolute times with different-host O209/J24Z01b runs as one A/B.

**Raw per-arm CPU ms (cycle order retained in original JSON):**
- Reader: 23.6023, 23.1140, 22.1035, 22.8649, 23.0893.
- Original streamer: 55.4965, 54.8563, 55.3320, 55.6452, 55.4717.
- Pooled streamer: 47.5633, 47.2020, 47.5935, 48.3212, 47.1515.

**Raw per-arm VmHWM increments KiB:**
- Reader: 131408, 131464, 131356, 131488, 131508.
- Original streamer: 16976, 16880, 16900, 17036, 17068.
- Pooled streamer: 3756, 3856, 3656, 3772, 3828.

All six deliberate hostile-frame cases rejected: **corruption / truncated frame / trailing byte** × original-streaming and pooled-streaming. Both arms authenticated the full 64MiB with CRC32/SHA256 and returned the same selected output with independently asserted SHA256. Output block capped at 65536 B, no full decoded Python bytes piece in pooled loop. No false product success from the scientific workflow.

## Interpretation / falsification / costs

**Positive research fact:** 64KiB output buffer reuse and synchronous direct memoryview hashing removed repeated decoded Python-byte materialization and yielded a nondominated bounded-memory oracle on this source versus the prior reference streamer: **both lower CPU/wall and lower RSS**. No extra stored bytes, no codec or format changes.

**Negative decisive fact:** the *prospectively* required 15% CPU and wall thresholds were each missed. The pooled Python strategy is therefore **not** the next shipping product priority. Importantly, the 14% improvement and ~13MiB further RSS reduction are preserved as mechanism evidence, not rounded up or interpreted as satisfying the frozen continuation rule. Existing native whole-decode retains substantially lower CPU.

**Different-rooted cheap local micro-check:** a separate non-CMPCT 64MiB Zstd frame generated from a repeated 256-byte pattern measured medians ~155.78ms with copied output versus ~122.59ms with pooled output across nine interleaved repetitions, maintaining SHA256/CRC32. This *local synthetic micro* exaggerates the hosted whole-Reader research gain (~21% local vs ~14% hosted). It has neither authentic archive semantics nor hosted provenance; it is explicitly not product evidence. The gap is a caution against committing based on free-standing kernel improvements.

**Safety:** original archive remains read-only; the pooled ctypes output is only reused after its synchronous CRC32/SHA256 update and selected-range copy. The experiment does *not* prove arbitrary source-writer safety or stage publication identity. Full 64MiB decoded work is not avoided and there is no selective decompression claim.

**Portability / external controls:** one Linux x86_64 host with system libzstd and repetitive compressible source; no Windows/macOS, package-owned Rust ABI, dictionaries, random incompressible data, complete ZIP64 export, update/recovery, independent ZIP reader or whole-product release gates. The original archive-size delta to physically chunked O209 control remains +69,894 B, not erased by this oracle.

## Counterfactual / decision-complete handoff

The earlier cheap discriminator was recognizable in source: J24Z01 materialized `out_raw.raw[:n]` once per 64KiB output and allocated ctypes buffers per call. A focused pooled-memoryview micro could have tested this before any package-native interface. It predicted a directionally useful improvement, but not enough to pass the prospective full-operation threshold; in this case it would not have justified shipping work. **No evidence-backed discovery-policy change earned from one episode.**

**Next unclaimed high-leverage frame:** if the ~125MiB same-file memory headroom matters for genuine multi-gigabyte logical sparse/ZIP64 flows, build a *package-owned native fused Zstd streaming + integrity + selected-output* mechanism, not another Python buffer/window variant. First classify native decode/hash/ffi/IO work on held-out structures, then assess full product CPU/RSS/bytes/recovery and portability against exact current Reader and physically chunked alternative. This result should inform #550 and ZIP64 owner #521; do not duplicate their implementation. Pooled strategy is retained as research evidence only, not promoted.

## Independent paired-cycle check (original artifact, no changed evaluator)

A second examination of the original `court.json` uses the five recorded rotation cycles as **paired observations**, rather than relying only on ratios of arm medians. Original streaming versus pooled streaming improvements per cycle were:

| Rotation cycle | CPU saved | Wall saved |
|---:|---:|---:|
| 0 | 14.2951% | 14.0747% |
| 1 | 13.9534% | 13.7642% |
| 2 | 13.9855% | 13.6676% |
| 3 | 13.1620% | 12.9634% |
| 4 | 14.9990% | 14.7811% |

**All five paired CPU and all five paired wall observations remain below 15%.** No selection of favorable individual rounds within the captured result meets the prospective strict target in both metrics. This is an additional decision check derived from immutable hosted raw evidence, **not** a separate independent run, confidence interval, or proof of universal slowdown. The shared kernel and source can have correlated variability; no statistical significance claim is made from five cycles. This favors preserving the original negative decision and moving to a materially different execution architecture rather than more pooled Python tuning.
