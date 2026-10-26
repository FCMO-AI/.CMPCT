# J24F08 — Linux kernel VmHWM for exact J24F04/J24F05 RAW Reader extraction

2026-10-26 UTC. Status: **PREREGISTERED BEFORE J24F08 EXPERIMENT CODE OR RUN**. Research/evidence repair only, no product, format, evaluation threshold or release change.

## Authority and original controls

Released v0.30.0/r24 unchanged. Continue J24F06 owner PR #543 at exact source `dd01be99ec33e820517f7e54b9beead416b20e19` and parent J24F05 #540 `1885cb0658cacd34a50d05e45b541ecb76fc8497`. Strong control J24F04 #537 `d5aa5cbc1ef1e00b6e3c8c72cdd1598192d563a3`. Exact product Reader Git blob IDs: whole `8b5910725260e7b4db155ee0b393eb48a42f7efa`, window `41efeb9d3301fc06b1df56ab6bd42d9ee91f6d5e`. Preserve original J24F06 A/B experiment and all negative result rows; do not rewrite it. J24F06 reported macOS lower RSS, Linux equal ru_maxrss; independent R637 audit showed Linux inherited peak contamination; historical O92c #450/O95 #453 already derived a child /proc VmHWM remedy.

## Primary question / prediction

With authentic source-exact r24 extraction, does Linux's **child-kernel `/proc/self/status:VmHWM`** separate the whole-RAW-copy J24F04 from the 64 KiB window J24F05 while `resource.ru_maxrss` remains potentially polluted by inherited high-water history? Hypothesis: for 64MiB primary RAW, the **median** kernel VmHWM candidate is at least **32 MiB lower** than whole-snapshot baseline in both S_CHUNKS and S_CDC, while full reconstructed SHA/length remain identical. Prediction is falsified when actual fresh child VmHWM fails to separate by >=32 MiB, reverses, lacks provenance, or displays excessive variability; this is evidence, not a safety or performance gate.

## Minimal decisive mechanism and controls

- Only Linux Ubuntu 24.04, installed CMPCT candidate source, actual unmodified historical vs candidate Readers against one identical independent physical archive. Reuse J24F06 fixture constructor and same 16/64MiB + 1KiB per S_CHUNKS/S_CDC cases and ABBA×2 (8 observations/case, 32 total). Each measured worker is a separate `subprocess.run` Python program; controller's fixture allocation is excluded.
- Child measures `VmHWM` directly by parsing `/proc/self/status`, at pre-open, post-open, post-extract, post-close, and **before independent output digest**. Also `VmRSS`, `RssAnon` where available, and `getrusage(...).ru_maxrss` as an explicitly nonauthoritative diagnostic. No `tracemalloc`, Python `os.write` monkeypatch or costly sampling during timed arms. CPU/wall bound Reader open+extract+close only.
- Validity checks: authenticated exact J24F06/prereg ancestry, both actual Reader blobs, physical archive SHA and indexed whole-file SHA, output SHA and size, same input SHA across arms, positive increasing VmHWM stages, nonzero VmHWM, complete repeated samples/fresh PIDs, correct A/B ordering, no weakening of inherited hostile or release tests. Include a separate cheap Linux process probe that faults physical anonymous pages and checks VmHWM grows, independently from extraction.
- Report raw individual metrics and median **absolute child VmHWM** in bytes, plus baseline-to-after-extract HWM growth; distinguish absolute RSS process peak from an allocation-attribution claim. Keep original J24F06 high-water numbers and contradictory timing unchanged.
- Stop/mark `INVALID` on source drift, wrong bytes, missing kernel counters, impossible monotonic VmHWM, incomplete samples or runner failure. `NO_CONFIRMED_MEMORY_WIN` if prediction fails. No post-hoc change of threshold.

## Costs, alternatives, boundaries

Simpler source inspection and macOS evidence already support bounded Python windows but cannot resolve Linux maximum. Running another identical `ru_maxrss` court repeats an invalid metric; directly measure kernel child VmHWM. Separate shell `/usr/bin/time` may measure different startup/process boundaries; use in-child phase snapshots. Larger corpus/full release ABBA is premature to answer this binary metric question. Charge complete stage-write syscall amplification from J24F06 separately: 2 calls original versus 257/1025 window; this experiment does NOT demonstrate universal CPU/wall advantage. Linux only. No source mutation race injection here: inherit J24F04/J24F05 scientific hostile evidence; no new guarantee on stage inode substitution #528, SIGBUS #460 or Windows #535. No format or release promotion.

## Concurrency, interpretation and handoff

Existing #543 owns original economic comparison; this **stacked research-only measurement repair** does not edit that owner's instrument, and will return exact result and artifact to #543/#540. `docs/discovery/STATE.json` is a stale cache and shall not be edited for a metric-only result. Counterfactual: if O95 VmHWM methodology had been reused from the beginning, J24F06's Linux memory ambiguity could have been decided in the first hosted run. Only a prospective reusable observation, not an authorized Discovery Engine policy change.
