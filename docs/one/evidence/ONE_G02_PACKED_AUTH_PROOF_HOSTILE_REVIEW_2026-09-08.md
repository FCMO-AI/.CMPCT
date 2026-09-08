# ONE-G0.2 packed authenticated-range proof — pre-result hostile review

Date: 2026-09-08
Status: pre-result review; thresholds frozen before consuming the dedicated benchmark
Experimental version: `ONE-G0.2`

## Mission / falsifier

The candidate keeps the newly advanced native AuthTree in one packed digest arena and generates the existing generic `RangeProof` directly from derived level geometry. The experiment asks whether this avoids full-tree re-materialization without changing proof semantics or exporting a material proof-generation latency regression.

## Builder review

The candidate deliberately does not read selected leaf hashes from the sidecar: proof verification recomputes those hashes from the returned leaf payload bytes. Only missing sibling hashes are read from `packed_nodes`, one 32-byte digest per emitted sibling. Level widths and prefix node offsets are derived once at tree creation; there is no per-proof full-level scan.

The public/reference `levels()` expansion remains for oracle/debug use only. A dedicated unit test makes the packed proof path fail if it tries to invoke that expansion.

## Hostile findings

### 1. A speedup is not the primary requirement

The Python reference receives a fully materialized `AuthTree` for free before proof timing. That is a strong control for proof generation itself. The packed candidate should therefore be judged primarily on preserving compact state without a material latency tax. The frozen 1 MiB hard ceiling is 1.15x wall/CPU, with at least 12/16 rows required to be non-regressing on both dimensions.

Do not reinterpret a green result as proof that packed extraction is intrinsically faster than every materialized representation.

### 2. Tree creation is excluded symmetrically

Both trees are built before timing. The preceding native-tree creation experiment already owns construction-speed evidence. Charging creation here would mix two questions and let the large creation win hide a proof-generation loss.

### 3. Previous-result destruction is excluded from the next arm

The paired loop drops the prior proof before either wall or CPU clock starts, and retains the current proof until both clocks stop. This prevents tuple/payload destruction from being charged to the opposite arm.

### 4. Proof traffic accounting is bounded but narrow

`tree_digest_bytes_read` records one 32-byte packed digest per emitted sibling, matching `RangeProof.touched_proof_bytes`. Coordinates are not counted as stored proof bytes because the current generic proof model derives them from tree geometry/request; this matches existing `auth_tree.py` semantics rather than changing accounting for the candidate.

This does not measure cache-line traffic, OS page traffic, remote ranges, or metadata/index lookup outside the packed arena. A green result cannot claim those dimensions.

### 5. Packed tree bytes are not yet canonical on-disk bytes

The candidate demonstrates a research sidecar shape. There is no format revision, canonical placement rule, crash/recovery contract, or portable crypto backend decision in this experiment.

### 6. Verification remains Python reference work

`verify_range()` is exercised for semantic exactness before timing, but verification throughput is outside the timed boundary. If packed proof generation advances, proof verification remains a separate owner candidate for native/bulk work.

### 7. Odd tree widths and boundary requests need exact coverage

Unit semantics include tiny and odd-width trees; the benchmark matrix exercises first/middle/final ranges and 64 KiB multi-leaf requests across leaf sizes 80/96/112/192. Any byte mismatch invalidates rather than becoming regression debt.

## Frozen interpretation

- `ADVANCE_PACKED_AUTH_PROOF`: the packed native tree can remain packed through selective proof construction under the frozen latency and exactness gates; advance it as the preferred research sidecar shape and next measure verification + process/RSS/product placement.
- `HOLD_PACKED_AUTH_PROOF`: keep the native creation result, but do not promote packed selective access yet; isolate proof-generation overhead or choose another in-memory index shape.
- `INVALIDATE_PACKED_AUTH_PROOF`: semantic or traffic-accounting failure; candidate does not advance.

No result may alter the frozen tree grammar, authentication domains, leaf-size matrix, or comparator semantics.