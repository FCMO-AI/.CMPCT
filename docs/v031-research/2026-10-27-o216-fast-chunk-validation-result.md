# O216 — exception-only S_CHUNKS validation: 4x faster, still fails early-admission economics

**2026-10-27 UTC** · Research-only / not a product patch · PR #570 stacked on J24C02 #569. **Decision:** `LOCAL_FASTPATH_INSUFFICIENT_FOR_PROMOTION`.

## Exact provenance and prospective contract
- Published v0.30.0 and r24 unchanged.
- Parent four-way correctness candidate #569 exact `c5e13bb3fbb4cdade8b64246658ce7c7818de41f`, installed Reader Git blob `dbd4ac576a05a47eae97e1e40de89cf1de4405166`, validator blob `51c2849061f99a4afeddb7666956b24566ce7de0`.
- Pre-observation prereg `3d28e4187d5e4ff89a2d1ea024e626fc1d2a153d`, [contract](2026-10-27-o216-fast-chunk-validation-prereg.md).
- First result-bearing script/workflow HEAD `dd994fa61c110cb046f5302c2d757f4cd0ac04b2`. [GitHub Actions #40451829700](https://github.com/FCMO-AI/.CMPCT/actions/runs/40451829700) **SUCCESS**; original artifact [12709899044](https://github.com/FCMO-AI/.CMPCT/actions/runs/40451829700/artifacts/12709899044), provider ZIP SHA-256 `7b09d81e747d920027412255c151146d4565367031d7913b609ae41535f648ea`.
- Zero product-source/format/threshold/benchmark changes. All three variants are **runtime-injected science** in the same unchanged Reader and validator installation. `unguarded` is deliberately unsafe and has *no* product correctness credit.

## Falsifiable mechanism
Original strict S_CHUNKS validation calls `_ref` and constructs a formatted diagnostic label for every accepted chunk reference. An exception-only path checks the exact accepted built-in int range inline, falling back to the identical `_ref` on invalid/unusual types and preserving the original total-of-blob-lengths invariant.

The independent program first required **identical class/message/acceptance** across 19 deterministic valid and malformed cases, including bool, float, negative, absent, repeated and out-of-range refs, invalid descriptor shape and declared-size mismatch. 12 original O215 tests passed against unchanged source. Historical valid/hostile parent behavior was **not** rewritten to make the oracle green.

## Complete installed-Reader cold-open result (Ubuntu 24.04)

Each fixture is one independently serialized, root-versioned, SHA-authenticated r24 CMPCT archive with one four-byte RAW blob and a list of repeated references. Same physical archive bytes for all arms. Original = unchanged strict J24C02 admission; fast = exception-only substitute; unguarded = unsafe no-S_CHUNKS-admission timing lower bound. Timed `CMPCT(path)` constructor + close after imports/warmup; **72 independent process observations**, **360** raw wall samples over three randomized paired cycles (six observations/arm/shape), all kept in artifact.

| Refs | CMPCT bytes | Original strict wall median | Exception-only strict median | Unsafe unguarded oracle | Strict speedup | Fast overhead vs unsafe |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 452 B | 0.1126 ms | 0.1110 ms | 0.1085 ms | 1.015x | +0.0024 ms |
| 4,096 | 474 B | 1.7528 ms | 0.4958 ms | 0.1527 ms | 3.535x | +0.3431 ms |
| 65,536 | 482 B | 25.6817 ms | **6.3633 ms** | 1.0211 ms | **4.036x** | **+5.3421 ms / 6.232x** |
| 262,144 | 516 B | 102.7494 ms | **25.1282 ms** | 3.7712 ms | **4.089x** | **+21.3570 ms / 6.663x** |

**Mechanism: supported. Material cold-open regression: STILL PRESENT.** The preregistered 65,536 (+5ms and >2x) and 262,144 (+20ms and >2x) blockers both fire. No relaxation of the threshold. The candidate is **not an adequate complete product repair** despite ~4x reduction versus original.

## Independent artifact replay
Downloaded the provider ZIP and verified ZIP CRC, exact HEAD, inherited test log, unchanged validator/source blobs, 19 hard-case outcomes, 72 process observations, five CPU and five wall times per worker, ABBA/pair ordering and all median-of-worker-median arithmetic. Replayed per-row ratios and debt predicates from raw observations. **PASS**. Independent audit and executable replay are preserved as conversation-side attached artifacts; GitHub artifact retains the original run evidence.

A separately executed local **micro-only** synthetic kernel and 5,000 deterministic adversarial value combinations showed no outcome mismatches and ~2.3–3x baseline/fast savings. This is subordinate to the authentic hosted Reader evidence; no product credit from it.

## Adversarial self-critique and proof frame
- The research controls do not establish a general cold-tree filesystem cost: the 262,144 repeated refs are a deliberately extreme but valid r24 index, not proven typical Builder output.
- A direct runtime monkeypatch is **not** a packaged product alternative. It bounds the loop mechanism and cannot be merged as-is. Full Python/Rust/Windows/macOS/ZIP64/parity/recovery integration is unmeasured for any optimized implementation.
- The unsafe unguarded arm supplies a lower-bound time control only. It accepts malformed descriptors and is never proposed as a safe replacement for strict same-index admission.
- No exact all-references check can skip an arbitrary unvisited reference: an adversary can change that entry to an invalid ID or to a valid ID with another length while leaving all inspected entries unchanged and re-authenticating the r24 index. Without independent authenticated geometry proof, worst-case **Ω(number of referenced chunks)** observations are necessary to reject every such file at open. This does **not** prove an unavoidable *100ms* cost; it identifies a lower bound on work, not CPU constant factors.
- For a strong next candidate, reduce **interpreter boundary cost** (native/vectorized batch verification with explicit type/bounds and bounded allocation) or change **representation/proof ownership**. Measuring yet another local branch threshold is lower-value after decisive high-N debt.
- An alternative delayed check on `read_range` alone can avoid the open cost but would **weaken the established early malformed-index rejection guarantee**, and cannot be promoted as equivalent simply because it detects some short reads.

## Decision / handoff
This closes the narrow exception-only Python loop proposal as an **insufficient full-product solution**, preserves a true 4x mechanism-level improvement, and satisfies the mandatory repeated-family frame review: move to bounded/native admission or new authenticated representation/proof architecture. Keep J24C02 #569 and O215 #568 source ownership. No changes to Discovery Engine policy or `docs/discovery/STATE.json` (stale cache); detailed durable evidence lives here and in the GitHub Actions raw receipt. **No merge / release / version / format promotion.**
