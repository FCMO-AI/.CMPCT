# J24G63 prospective protocol — public Writer put/delete one-op chains

Status: PREREGISTERED, NOT A MEASUREMENT. Frozen before any J24G63 instrument or hosted job. Research-only, no product/release/format modification.

## Current authority, provenance, distinct ownership
Canonical published main is v0.30.0 / r24 at `80c358f8824ec1b20d349c92ed94c898090969b0`. Experimental same-source parent is J24G60 PR #800 `fb5d96cdb8855fe3e01868792e65b79d3d61661d`, containing the fail-closed J24G57 #795 source. J24G61 #801 attributes the 63-one-op *rename* chain penalty to repeated replay (positive Ubuntu/Windows, macOS ambiguous). Independent active J24G62 #804 owns **rename-only cross-generation factoring** and is not to be modified or duplicated. #797 owns wide-single-generation optimization. This activation owns ONLY a different question: public Writer **put and delete** cold-open applicability/economics. `docs/discovery/STATE.json` is stale and #574 owns reconciliation; do not write it.

## Primary falsifiable question
When Writer emits one `put` or `del` per durable generation, is the actual Reader-open penalty relative to a physically stored, same-effective-index private checkpoint material at N=2048 and d=63, and is it of comparable magnitude to the inherited 63-rename case?

Prediction: each class incurs >=3.0 ms and >=10% of chain-open wall at N2048/d63 on at least two hosted OSes; if either class fails, narrow cross-generation generality to the surviving classes, not reinterpret the threshold. This is a **pre-registered hypothesis**, NOT a claim. Never claim representative real-user operation frequencies; artificial equal-frequency classes are just causal controls.

## Physical construction and exact semantics
Pin five parent Python product blobs to J24G60's source SHA. For each N=512 and 2048 and d=1/16/32/63:
- **put:** Builder creates N ordinary regular files; use public `append_update` to replace d distinct existing names with different exact 64-byte deterministic contents. Final N remains N. New blobs, generation widths, mode/mtime and physical archive bytes are accounted, not assumed zero.
- **delete:** Builder creates N+63 files; use public `append_delete` on d early sorted names. At d63 final N; at smaller d final N+63-d. This counts as a distinct physical baseline, never an identical-input cross-class A/B.
- Immediately copy authentic chain and append ONE private full checkpoint on a separate identical copy, with identical index/blobs and no intermediate mutations. The checkpoint is an oracle/control, **not** reachable from the public Writer at that depth; charge its additional bytes.
- Audit real r24 footer chain offsets, SHA-256, opcode lists, widths, and index identity; independently strong-verify both archives and preflight; preserve all counterexamples. No xattrs, hardlink perturbations, crash/recovery, ZIP/Zstd, native ABI or installed release parity asserted.

## Execution and statistical controls
Use unchanged inherited `research/j24g60_single_delta_chain_court.py --probe` in fresh child processes so imports/startup remain outside its wall/CPU timer (not cold disk). Pre-bias-paired ABBA/BAAB four blocks per case and retain **every** raw reading: 2 classes * 2 N * 4 depths * 4 blocks * 4 samples = 256 observations, 8 chain + 8 checkpoint per cell. Capture process CPU + wall and Linux VmHWM when available; do not treat that as full peak RSS. Report medians separately with signed absolute delta and fraction. At N2048,d63, >=3ms and >=10% chain fraction means `MATERIAL`; all other outcomes are `NOT_MATERIAL`, not missing data. If a hosted OS fails or source does not match, classify host `UNMEASURED`.

## Stronger controls, alternatives and kill/narrow conditions
Counter-explanations: footer SHA/MessagePack/zstd overhead, OS cache noise, archive size/more physical blobs, initial index size differences, and transient import/runner effects. Rename-only results from #800/#801 are inherited historical controls, **never same-runner numerical A/B** with new classes. A measured put-or-delete result cannot validate an optimization not implemented in Reader. Any difference in logical index, bytes, SHA/footer chain, opcode width, source identity, installed Python source, parsing or recovery is an invalid experiment. No product code, frozen baseline, fixture, historical evidence, comparator, admission gate or threshold may change.

## Discrimination / completion
Evidence should show whether to invest engineering in a generic mixed-operation across-generation replay, or preserve J24G62's rename-only lane while the cheap `put` path stays the simpler control. Audit original raw receipts independently, including hostile receipt corruption. Preserve negative/noisy results and physical 2048/d63 archives. A positive result is **research headroom only**; full Reader/Writer CPU/wall/RSS, temporary I/O, cold opening, selective read, extraction, recovery, metadata, portability and release parity remain mandatory for any future product promotion.

## BONK and resource budget
Baseline #801 already answers rename; #804 actively tests rename factoring. Do not repeat them. This new oracle tests two different public operation families with existing source exact physical court, avoiding product implementation and benchmark cost. No archive-size savings are predicted. A negative for either family can retire its priority for crossgen optimization. A follow-up implementation should preserve the strongest simpler zero-code baseline and consider memory/no-bytes cost, portability, recovery and generality before any product claim.
