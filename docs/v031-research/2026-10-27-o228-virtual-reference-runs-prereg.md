# O228 preregistration — virtual reference-run index (research only)

**Frozen before instrument/results:** 2026-10-27 UTC. Owner branch `agent/phased3-v031-o228-virtual-reference-runs-20261027`, based on released `main@80c358f8824ec1b20d349c92ed94c898090969b0`. Product remains **v0.30.0, revision 24**. No code, format, validator, published benchmark, threshold or release changes.

## Primary scientific question and landscape BONK

Can a *lossless virtual logical-index representation* replace repeated per-reference Python objects with run segments, while carrying **all physical owner IDs, chunk lengths and multiplicities** needed for exact reconstruction and random range selection? Existing #569 owns real Reader correctness and #570/#577/#578 own per-reference validation execution. #583 owns checkpoint lookup; #587/#590 own memory attribution; #597 retires physical-owner scatter. This study is a different **information-representation** layer, not another Reader implementation or timing-optimization reskin.

Compare three genuinely different routes: (A) keep shipping explicit MessagePack references + compressed index; (B) new run-bearing index with every repeated fact charged, with full-index compressed bytes measured; (C) no new grammar, simply compress current explicit bytes (strong simplest control). A fourth portfolio oracle chooses cheaper *complete* index only after paying candidate encoding and two-index duplication. An oracle is not automatic runtime product admission.

## Baseline and hypothesis

Release r24 stores an S_CDC member as `[S_CDC, [[len, blob_id], ...]]`; S_CHUNKS stores `[S_CHUNKS, [blob_id,...]]`. Physical blobs are separately indexed, complete file length and SHA remain outside the storage field. Ordinary MessagePack unpack materializes O(N) reference objects even when compressed index bytes are tiny. Repetition may permit a virtual run `[count, logical_chunk_length, blob_id]` (CDC) / `[count, blob_id]` (fixed), with an explicit new **research-only** storage tag; decoded run counts are bounded and never expanded before a selective query. Exact file hash, physical blob table, metadata and index hash costs are common/charged, not gifted.

**Prospective prediction:** on 262,144 adjacent identical owner-length references, full decoded MessagePack peak-heap cost is at least 4x less for run representation, while compressed complete index bytes do not increase. At least one intermediate deterministic held-out shape (runs of 8/128) should also preserve >=2x heap benefit and avoid >1% physical+dual-index archive-size regression. This is a *research* hurdle, not a product release criterion.

**Falsifier/kill:** if native compressed index already dominates both memory and bytes, or if contiguous repeat structure is too narrow to survive held-out runs 8/128 and high-diversity negative controls, retire unconditional run replacement. Even success requires later source-exact Reader proof, bounded hostile-input admission, versioned format law, query/extract semantics, update/journal semantics, broad corpora, create CPU, memory, portability and archived parity before product credit.

## Frozen experiment and controls

- No fixture identity as predictor. Deterministic seeded synthetic, structurally valid **r24-shaped** indexes with identical logical metadata and blob objects. Not Builder-produced archives; do not call them genuine CMPCT wire.
- Cases: 262144 references with contiguous run lengths 1,2,8,128,262144; alternating two owners; seeded random owners drawn from 32 owners; distinct references (unique owner indices) as hostile negative. Both fixed-S_CHUNKS and length-bearing S_CDC forms; where feasible, perturb chunk lengths and owner IDs together rather than claiming every duplicate-content pattern is realistic.
- Serialization: `msgpack.packb(use_bin_type=True)` and **libzstd level 12** compression for both on exactly the same host; library dependency/version recorded. Full top-level index charged, not just isolated storage. Primary and tail duplicate compressed index counted. New run tag/count/length/owner is fully encoded. Same index root `sha256` for each version protects its own metadata.
- Compare compressed-index bytes, raw-index bytes, encode wall/CPU, unpack wall/CPU, Python tracemalloc peak on fresh decode, estimated full archive bytes with unchanged physical records, run/expanded logical count, selected decoded-reference work. Distinguish streaming grammar *oracle* from an implemented parser.
- Create independent interpreter process for each variant and shape; >=3 repeats for key cases; audit exact reconstruction identity through multiple random boundaries, last byte and full logical length, reject zero/negative/excess count, invalid owner, bad length, and declared logical size mismatch. For each case compare entire expanded (length,owner) *semantic sequence* using a deterministic rolling SHA-256, not a merely equal sum.
- Independently recompute all summary ratios from raw JSON observations, verify exact source SHA and results. Keep negatives, no tuning thresholds after results.

## Scope and ownership

Research-only PR, no changes to Reader/Builder/native codec/format/release law/benchmarks, no merge on green science. Coordinate findings with #569 and #590 *after evidence*. No `docs/discovery/STATE.json` edits: #574 already owns stale state reconciliation. No concurrent claim on source files. Evidence from local environment is labeled local; hosted GitHub Actions required for independent execution/CI claim.

## Principal alternative explanation

A zstd-compressed explicit index is already tiny and can be decoded rapidly; run semantics may save only Python heap on highly repetitive artificial refs, with extra CPU complexity and no meaningful complete-archive win. Comparisons to one reference string or microbench must not be presented as full product improvements. Even a generous oracle win could be killed by update cost, format incompatibility, hostile run-count denial of service or lack of structurally general repeated runs.
