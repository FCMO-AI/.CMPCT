# J24K11b — Pay per-query VZIP signed-index projection before native BHDR batch

Date: 2026-10-28 UTC. **PREREGISTERED BEFORE IMPLEMENTATION / UNMEASURED.** Follow-up to J24K11 first hosted evidence #40654643276; its raw component result >20x excludes actual signed-index-to-7-tuple materialization. This test must not inherit uncharged tuples as "free".

## Primary falsifiable question
For the same immutable synthetic physical r24 BHDR source and signed in-memory `blobs`/VZIP `payloads` representation, does a **newly materialized 7-field native batch on each read** still win against a **strong one-loop Python validation that directly consumes the signed structures without projection**? No caching, no source copy, no fixture identity shortcuts; include acquisition/bridge/selection/indexing work for both. This is still a modeled component, not installed Reader evidence.

## Frozen comparison and kill
- Exactly identical physical source bytes and nonmode2 signed descriptor values. Model three modes: STORED physical RAW, canonical mode0 DEFLATE, retained mode1 opaque physical Zstd-like owner. C source unchanged and Python direct validates the same physical BHDR invariants (record magic, codec, flags, reserved, all sizes, record bounds, stream coordinate and compressed Deflate codec).
- 64, 512, 4,096 signed payload entries; two owner arrangements: sequential and random-permuted physical refs, same signed rows. At least 12 ABBA-balanced wall/CPU samples for each arm and cell. Arms: direct unprojected Python; projected direct Python; **new projection+native**. Retain complete raw observations and source hashes.
- Demand **>=1.5× in both wall AND CPU versus direct unprojected Python** at 4,096 for each mode/owner arrangement. If any cell fails, classification **PROJECTION_BRIDGE_HEADROOM_NOT_PROVEN**, no tuning or retrospective exclusions. Negative adversarial signed csize and physical BHDR mutants must reject in candidate and direct control, using fresh projection.
- Report Python allocation footprint of created tuples and list object each call, plus compiled helper size/time separately. Startup/ABI import and full installed Reader excluded and explicitly labeled.
- Retain the stronger original J24K11 prebuilt tuples numbers as historic micro evidence only; do not treat them as product speedup.
- Only if this cheap bridge assay is favorable may the following experiment compose installed J24K09 Reader with real signed r24 archives and multi-query read_range / published baseline. A failure means bridge economics have already killed this route at the modeled rung.

## Concurrency and authority
#653 owns the actual VZIP product fix, #657 owns copy economics; #641 owns unrelated S_CHUNKS native validation. Work only in this isolated science PR; `src/`, `native/`, all old tests, existing evaluators, format/version/release, and discovery STATE remain untouched. No full SHA verification of selected range is provided. Record negative/raw evidence even when the result fails.
