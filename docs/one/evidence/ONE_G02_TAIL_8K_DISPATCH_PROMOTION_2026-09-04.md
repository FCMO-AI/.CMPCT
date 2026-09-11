# ONE-G0.2 — Tail-return 8 KiB dispatcher promotion

**Branch:** `research/cmpct1`  
**Exact result-bearing source:** `dbf5a940ce22c058567dcd4889c13e64200cc741`  
**Workflow run:** `33941920994`  
**Result-bearing job:** `101240914393`  
**Artifact:** `9962132188`  
**Artifact ZIP SHA-256:** `52444fe65ff6db0eccc8b9306d68977223adc21f5076fddcd7ea6fa96128ef6a`  
**Experimental version:** `ONE-G0.2`

## Mission lock

The earlier paired crossover map selected 8,192 input bytes as the first frozen size at which the 41,056-byte offset-only representation was consistently favorable across the tested regimes, but the first ordinary wrapper dispatcher failed to convert that kernel-level advantage into a material end-to-end win. This experiment tests a causal rehabilitation only: whether expressing the dispatch as a tail-return boundary removes wrapper/call/layout debt while preserving the already-frozen 8,192-byte decision law.

The promotion gate, size ladder, regimes, 13-round timing protocol and comparison against the promoted counter baseline are unchanged from `one_g02_minimizer_size_dispatch_ab.py`. No threshold was chosen after seeing these results.

## Static shape

The same-compiler diagnostic supports the intended integration cause:

- dispatcher body: **25 decoded instructions**;
- call instructions: **0**;
- jump instructions: **4**;
- relocations retain one reference to each of the counter and offset-only kernels.

This is code-shape evidence only, not dynamic speed authority.

## Dynamic result

**Frozen decision: `promote_tail_8k_size_dispatch`.**

The exact-head run passed all **50 ONE semantic tests** before measurement and preserved the independent selector/oracle boundary. Source-byte rescans remain **zero**.

The tail-return dispatcher converts the previously inconclusive wrapper into a material large-case win:

- cross-large median dispatch/counter: **0.900864x** — about **9.91% lower elapsed**;
- enabled reserved discovery state: **41,056 B vs 49,248 B**, a **16.63% reduction** on the offset-only path;
- below 8,192 B the counter path remains selected, so the prior tiny-boundary offset regression is not exported.

At the exact 8,192-byte boundary the selected offset path is already favorable across the frozen regimes:

- random: median **0.946528x**, p90 **0.958496x**;
- repeated 4 KiB basis: median **0.936286x**, p90 **0.956490x**;
- zlib-random-like (8,203 actual bytes): median **0.913483x**, p90 **0.935492x**.

Large examples remain favorable:

- 256 KiB random: **0.900279x**;
- 256 KiB repeated: **0.895999x**;
- 256 KiB zlib-random-like: **0.895487x**;
- 1 MiB random: **0.906862x**;
- 1 MiB repeated: **0.901449x**;
- 1 MiB zlib-random-like: **0.906472x**.

The frozen promotion step in CI executed; rejection and inconclusive steps were skipped.

## Causal interpretation

The offset-only kernel already had evidence of lower state and lower mature-input elapsed cost. The first dispatcher failed because integration shape exported enough wrapper/layout overhead to erase that gain. Tail-return dispatch changes the integration boundary rather than the selector semantics, threshold, data regimes or representation. The material recovery under the unchanged gate therefore supports **wrapper/control-flow debt** as the causal blocker of the first dispatcher.

This is a useful ONE pattern: do not tune away a strong lower-state kernel merely because a naive integration wrapper loses. Rehabilitate the exported integration debt, then retest under the original gate.

## Promotion boundary

The encoder-discovery baseline may now use:

- counter-based tail-aware four-segment minimizer below **8,192 input bytes**;
- offset-only minimizer at/above **8,192 input bytes**;
- tail-return dispatch so the gate itself does not erase the mature-path win.

This promotion changes encoder discovery only. It creates **no reader-visible opcode**, no new Law relation, no wire/stored-byte authority, no product-speed authority, and no v0.29/v0.30 superiority claim. The full Genesis comparison remains due at/after the first activation on 2026-09-11 America/Mexico_City.

## Strongest surviving criticism

The result is still hosted C/Python research evidence on a synthetic/frozen selector workload set. The approximately 9.9% cross-large gain is real under this instrument, but it does not establish that minimizer discovery has positive marginal information yield in the eventual fused observer or across the 15 product workloads. Integration into normal observation still requires charged opportunity-value evidence.
