# J24K12 — installed Reader, authentic signed VZIP native-batch transfer (preregistration)

Date: 2026-10-28 UTC. **Prediction recorded before test/instrument implementation.**

## Ownership / actual authority

- Scientific base: #660 `fed0ac7fff533dc66b56f5e39f7c6f64c4ee6d7a`, which already carries #653's guarded installed Reader source `e77578505985dd264d69425e3bc816c421ae3cdc` and codec `fe692c4595c1303dbc89b7d660501e4ef0f223c3`. Both sources are immutable controls for this experiment.
- #660 owns the standalone/charged-component scanner; this is a distinct **authentic installed Reader** transfer question, on a separate branch/PR. No edits to #660, #653, #662, #574 or their claims; no shared Discovery STATE mutations.
- Current released baseline is v0.30.0/r24 on main. This study does not grant product or release credit.

## Primary falsifiable scientific question

Can #660's exact positive-only C/BHDR scanner, including a newly charged per-query projection from genuine signed revision-24 recipe and owner descriptors, improve complete `CMPCT.read_range` sessions on **real Builder-produced, signed, readable Virtual ZIP files** compared with #653's safe per-stream BHDR witness, without changing any requested byte, decoder, source-fd ownership or error rejection?

**Prediction:** for a source with >=512 physically describable STORED streams, Q=64 suffix-heavy queries, median charged open+range wall and CPU should improve >=1.20x versus the original safe Reader, on each hosted OS. For Q=1 early and mid queries the original Reader is expected to win or tie because a native projection/scan has fixed costs. We do not retrospectively turn a favorable Q into the frozen primary question. A Q=1 loss >=5% **and** >=2ms absolute, or increased peak RSS >8 MiB on a comparable measured host, prevents product promotion even if Q64 improves.

## Controls / design / evidence hierarchy

1. Strong baseline: unmodified installed #653 Reader `CMPCT.read_range`, with signed index and same-mmap physical BHDR checks, not an optimistic no-proof shortcut.
2. Candidate: call exactly #660 C scanner on the already-open Reader mmap for the **same skipped physical streams** that define the requested range. Rebuild/check exact-integer descriptors and projection for each request; on any unsupported/negative C proof defer to unmodified `CMPCT.read_range`. After a positive proof, use the untouched `range_vzip` and decoder with temporary per-request witnessed length values. No cross-call cache.
3. Independent byte oracle: full original ZIP source bytes plus Reader `read`, `verify`, `preflight_archive`; identical unsigned-byte sequence and per-query SHA under both strategies. Preserving the full ZIP byte identity is mandatory.
4. Authentic Builder-generated signed r24 archives, not modeled 64-byte BHDR records; STORED first, with a held-out DEFLATE physical-mode cohort when supported by exact Builder output. Query early/mid/late and a mixed sequence; source SHA and exact commit/blob lineage in receipts.
5. Balanced fresh subprocess A/B on the same host, with Reader constructor, projection/C calls, range read, process start tracked separately, raw CPU/wall repetitions; architecture-specific peak RSS only where supported. Include native compile/import and wheel/source packaging as separately disclosed costs, not magically zero.
6. Malformed yet reauthenticated length lie, exact boolean owner and overflow refs, corrupted physical header, and source/receipt tampering. A negative result is valid scientific output; no test loosening.

## Kill/narrow conditions / alternative explanation

If speedups vanish after Reader open, per-query descriptor projection, source-byte verification and process startup are charged, the standalone C scanner's 2.8x+ model improvement cannot earn product credit. If the C proof accepts any signed or physical contradiction that #653 rejects, terminate the positive path rather than weakening safety. If the only win is a special repeated identical owner, retain as a bounded seed and demand permuted/mixed-owner generality. If CI cannot obtain authentic native builds, classify it as infrastructure, not a performance loss. If early range loses, adaptive/non-native baseline is a legitimate winner. No architecture, format, frozen comparator, release gate or safety threshold may be weakened.

## Prospective handoff

Keep the original raw receipts, CI SHA, exact reconstructed source and output hashes, CI failures and contradictions. Do not merge/release from science. Return to the mission frontier after this fork; #662 owns S_CHUNKS native indexing, not VZIP BHDR. Next action is the cheapest genuine installed Reader A/B, not another isolated BHDR microbenchmark.
