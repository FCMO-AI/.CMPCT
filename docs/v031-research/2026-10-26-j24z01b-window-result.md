# J24Z01b — bounded output-buffer amortization falsified; smaller window dominates tested streaming policies

Date: 2026-10-26 UTC. **Decision: BUFFER_AMORTIZATION_WEAK — retire output-window tuning as next solution.** This is only native-library research, not shipping Reader code or release credit.

## Prospective source / hosted receipts
- Distinct prereg before implementation: `docs/v031-research/2026-10-26-j24z01b-window-prereg.md`, commit `2d39627ed3a522ca0896cb8a49979bf1c7320d04`; original J24Z01 result and immutable prereg preserved separately.
- Follow-up instrument `research/j24z01b_window_court.py`, prospective implementation commit `66bcf99b732e9d8f8a3d667c18cbd9f93792e55e`; parent full-auth decoder reused unmodified, varying ONLY `WINDOW` across 64KiB, 256KiB and 1MiB in separate fresh processes.
- [Hosted workflow #40420706050](https://github.com/FCMO-AI/.CMPCT/actions/runs/40420706050) **SUCCESS** at exact source HEAD `ea86d0511059bacb4172acb1bf218edb919258c8`; retained original [raw artifact #12696498366](https://github.com/FCMO-AI/.CMPCT/actions/runs/40420706050/artifacts/12696498366); archive ZIP SHA-256 `7d14624418c5abf42a50ff09655502d2f0cff4520110ef2cb27924863bd38c1e`. The ZIP was downloaded and **both** `oracle.json` and `window-result.json` inspected directly, not inferred from CI status.
- All arms used one identical original authenticated 7,612-byte CMPCT archive, physical SHA-256 `cff0cf0bb0c77eabf07b46292ef8dcc7189107a2814080ae92326ce097a02061`, same 64MiB logical source, same exact 1MiB selected output SHA. Parent ordinary Reader SHA blob `d2e7ed7863d9a9c598d225ca1f77e53d94c6bf44`.

## Measured five rotating fresh-process repetitions per arm

| Arm | Native decode calls | Median fresh-process VmHWM increment KiB | Median CPU ms | Median wall ms |
|---|---:|---:|---:|---:|
| Original CMPCT Reader A | not applicable, whole-frame decode | 131,464 | 60.428309 | 60.426108 |
| Streaming B64 output 64 KiB | 1,024 | **17,092** | **85.456589** | **86.236801** |
| Streaming B256 output 256 KiB | 256 | 51,272 | 94.362830 | 95.219785 |
| Streaming B1024 output 1 MiB | 64 | 71,172 | 96.768370 | 97.637999 |

B1024 versus B64: **CPU became 13.23687399% slower, wall became 13.22080349% slower**, and process VmHWM increment rose from 17,092 KiB to 71,172 KiB. B1024 still has a 58.87890625 MiB RSS margin versus Reader A but this is **smaller** than the B64 margin 111.69140625 MiB. All B arms fully decompressed and authenticated all 64 MiB of source bytes (CRC32/SHA256) while retaining exactly 1MiB of selected output. No decoder result or file SHA differences.

Original J24Z01 primary result [run #40420064445](https://github.com/FCMO-AI/.CMPCT/actions/runs/40420064445) remains binding: B64 margin 111.68359375 MiB but 2.3482x CPU and 2.3746x wall. In the second fresh hosted run, B64 was only 1.4104x CPU and 1.4260x wall A, demonstrating substantial cross-run timing variation. **Do not silently select the more favorable run or treat the >2x condition as permanently passed.** The same-run follow-up result falsifies the specific call-count hypothesis: 16x fewer C-boundary crossings did not speed decoding.

## Decision / counterfactual / scope
- **Hypothesis retired:** Python↔C decoder call frequency **is not the dominant overhead under tested input and instrumentation**, since eliminating 960 of 1,024 calls made end-to-end slower. Greater decoder-buffer allocation/copy/GC and Python checksum throughput remain possible, **unproven** explanations; require attribution before any new expensive product change.
- **Candidate retained as conditional research seed:** same archive, no chunked +69,894-byte physical overhead, material memory savings under full SHA/CRC; absent a stable whole-system CPU/wall win, no product or release promotion.
- Stronger next architecture candidate is **package-owned Rust native streaming integrity+selective output** rather than external system libzstd with Python ctypes loop; a staged micro-court profiling each subcomponent or a Rust local fused experiment is required before coding shipping API. Do not garden output-window size.
- **Scope restrictions:** Ubuntu-only, one repetitive 64MiB physically small frame, warm system cache, fresh child runs, original Reader vs independent native library not native shipping ABI. No Windows/macOS, full ZIP64 export, source mutation adversary, metadata integrity beyond original source, recovery/publication guarantees or official parity evidence. All bytes decoded, no claim of selective physical decoded-work saving.
- **Policy:** no change to `docs/discovery/STATE.json` or normative discovery policy; result is one prospective counterfactual lesson (same-container streaming can avoid physical-chunking bytes, while larger output windows cannot be assumed to amortize overhead).
