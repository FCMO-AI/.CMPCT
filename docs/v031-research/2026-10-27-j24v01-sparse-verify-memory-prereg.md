# J24V01 — bounded-memory S_SPARSE verification (prospective, 2026-10-27 UTC)

## Exact baseline and ownership

Released `main@80c358f8824ec1b20d349c92ed94c898090969b0`, Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`; v0.30.0/r24. `CMPCT.verify()` calls `read()` for every row; the `S_SPARSE` branch creates `bytearray(logical_size)`, materializes all holes, converts to `bytes`, then `verify()` hashes again. This makes a valid sparse archive with a large logical hole demand memory proportional to its declared logical size even when its stored physical extents are small. `codec._hash_sparse` already defines exact streaming zero-hole SHA semantics for Builder.

Neighboring #255/#571 own sparse **extraction integrity/publication**, #560/#569 own structural sparse admission, #610 owns hardlink alias sizes; this lane is limited to **regular `K_FILE/S_SPARSE` verification memory**. No changes to those owners or to `docs/discovery/STATE.json`.

## Primary falsifiable prediction (before implementation)

Under the same authenticated r24 sparse archive, the current Reader's `verify()` requires O(N) extra resident memory due to full logical allocation; a specialized streaming verifier can compute the same full logical SHA with O(1 MiB + max decoded physical chunk) auxiliary memory, without accepting changed bytes or size/extent contradictions, and without format/Builder/parser alteration.

Controls: genuine valid Builder sparse file; independently computed streamed SHA from `_hash_sparse`; deliberate physical content corruption rejected (CRC or full logical SHA); signed logical digest tamper rejected; non-sparse regular file unchanged; a bounded resident-memory court comparing old/new source on same archive (rather than comparing a token microbenchmark). Prefer a deterministic data-sparse file and bounded CPU/RSS/wall evidence. If local runtime cannot build genuine CMPCT because installed native Rust extension is unavailable, host on Ubuntu via source-locked GitHub Actions, marking any unexecuted court pending.

## Alternative mechanisms / cost

(1) `read_range()` in 1-MiB windows bounds output but rescans all sparse extents on every window (potential O(E*N/window)); reject absent a charged index. (2) Reuse Builder's `_hash_sparse` with reconstructed extent payload list would duplicate all extents in memory; reject for multi-GB physical sparse data. (3) Stream monotonically across authenticated extents, hashing zero blocks and `_blob` payload once: simplest O(logical-bytes hashed + E + physical-decode) and O(1MiB + decode unit) RSS. Zero hashing remains full logical SHA work, not a magical CPU optimization.

## Kill/narrow conditions

Reject if any valid sparse r24 corpus differs in SHA/read/verify result; if a corrupted physical or logical byte is newly accepted; if material CPU/wall regression occurs beyond extra verification cost already required; if extents can be overlapping, unbounded, or silently padded without a fail-closed check; if additional reconstruction helpers create worse maintenance than the memory improvement. An honest streaming microtest or mock-only test earns no product credit without an authentic installed-Reader court.

## Limits, promotion and independent review

No promise of global `verify()` streaming: hardlink aliases to sparse owners still recurse to `read()` in this narrow slice, and S_CHUNKS/S_CDC/direct/PACK/VZIP remain as-is. Existing full Reader release/parity/portable CI, recovery, concurrent mutability, and hardlink semantics still gate integration. Do not merge/release from focused correctness or RSS evidence alone. Code and bench results must remain on distinct evidence rungs.

Prospective hypothesis registered before any Reader patch.
