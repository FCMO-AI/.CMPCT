# O226 — full-reader decoder-unit ownership beyond the 2 MiB cache ceiling (prospective)

2026-10-27 UTC. Research-only. **Immutable before new instrument/workflow or new results.**

## Provenance and owner contract
Released CMPCT v0.30.0/r24 unchanged. Reader source comes from J24C02 owner PR #569 exact commit `c5e13bb3fbb4cdade8b64246658ce7c7818de41f`, blob `dbd4ac576a05a47eae97e1e40de89cf1de440516`. This O226 independent science stacks on completed O225 PR #592 `c2751715edca996019e7ea680d9e9203d40c06b7`. O225 showed 10–16× serial advantage on tiny RAW and ~4–8% for distinct 256 KiB Zstd/Deflate, but those units were all below the Reader's 2 MiB cache threshold. O169/O173 own cache-product policy; #569 owns the Reader; O226 edits neither.

## Frame review and primary question
Two prior activations explored futures/serial. Do not resume threshold gardening. This is **one bounded final transfer/falsification** changing the physical ownership and decoded-unit scale: when verified 3 MiB decoded blobs cannot enter `CMPCT._blob`'s <=2 MiB cache, does unconditional serial stay within the O225 <10% full-session penalty envelope under truly unique and repeated heavy units? If this court produces no decision-changing evidence, retire nearby scheduling micro-variants and defer product implementation to #569.

## Baseline, controls and alternatives
Use the *same exact installed J24C02 Reader* and same physical authenticated r24 bytes per alternative: original eager `reader.read()`, simple serial complete-member concatenation, bounded64 chunk executor. Reader source and preflight unchanged. Controls include pre-existing O225 256 KiB transfer evidence, actual SHA of all logical outputs, authentic Zstd-7 and Deflate-6 physical frames, independent original r24 headers/index and signed SHA, held-out mixed codec/range tests and authenticated-index/invalid-referenced-physical CRC rejection for all alternatives.

Freeze six regimes, for both S_CHUNKS/S_CDC: Zstd/Deflate × (high-entropy 3 MiB decoded owners once, high-entropy owners reused twice, compressible patterned owners reused twice). Twelve source-distinct owners per regime; 3 MiB each; twice means 24 refs / 72 MiB reconstructed. Each arm gets 3 fresh separate PIDs in counterbalanced order. 6×2×3×3=108 child observations. Include full open + read + shutdown wall/CPU and own-process Linux VmHWM; process-launch time separate; complete archive bytes and decoded logical bytes. Verify every read against independent SHA. No synthetic first-level compression gain claim.

## Frozen decisions and falsifiers
The key scientific result is **cache-boundary generalization** rather than a mandatory positive. Reject unconditional serial as a generic current Reader policy if any of twelve regimes shows >1.10× median serial/eager *complete session* wall, or serial's own VmHWM > eager by 8 MiB. Report stronger `EAGER_PARALLEL_COUNTEREXAMPLE` only if eager is >=1.20× faster than serial in **read-only** and complete-session medians on at least one of the four high-entropy regimes; otherwise label `BOUNDED_SERIAL_TRANSFER` when all full-session ratios <=1.10 and memory bound holds; otherwise `SERIAL_TRANSFER_VETO`. Report bounded64 separately; it earns headroom only if >=1.20× both alternatives on the same profile with no >8 MiB RSS penalty.

Wrong logical byte/hash, missing/corrupt parent or receipt, source drift, stale/missing samples, nonfinite time, unsafe exception, corrupted referenced CRC accepted, mismatched archive/input across alternatives or wrong CPU/RSS accounting **invalidates the scientific conclusion**, not the threshold. A green workflow may report a negative decision.

## Product/evidence boundary and externalities
No production Reader change, no on-disk format, ABI, codec default, validator, release gate, benchmark, workflow threshold, public headline, license, or `docs/discovery/STATE.json` mutation. Experimental reader.read alternatives are adapters, not product. One Ubuntu/Python 3.12 host cannot grant cross-platform, integrated Reader/ZIP64/recovery/sparse publication or release authority. Record source/binary sizes, false-positive rejection, decode work, CPU/wall, memory, and archived raw observations. Final policy requires larger held-out sources and native/Windows/macOS/read-range oracles.

## PARETOBONK competing routes
Exploit existing J24C02 open-cost owner (already claimed by #569); rehabilitate O225 serial (selected bounded transfer court); native O218 admission (different owner/evidence); cheap source-level cache-ownership boundary (this transfer) versus another full release parity (premature). **Kill condition:** if no >10% difference at 3 MiB and no new CPU/memory insight, do not continue near-variant exploration; hand off O225's cheaper serial control for prospective product testing and switch to independent integrity/productization debt.
