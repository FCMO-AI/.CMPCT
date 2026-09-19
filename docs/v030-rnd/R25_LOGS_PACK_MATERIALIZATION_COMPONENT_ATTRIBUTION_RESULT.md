# Logs authenticated-pack materialization component attribution — result

Status: **ACCEPTED EXACT-HEAD FORGE D2 CAUSAL EVIDENCE / THREE MATERIAL OWNERS / PACK I/O RETIRED / NO RELEASE CREDIT**

This record closes the frozen follow-up in `R25_LOGS_PACK_MATERIALIZATION_COMPONENT_ATTRIBUTION_PREREG.md`. It changes no production source, archive bytes, pack framing, codec, integrity/recovery rule, locality/decode-unit bound, benchmark threshold or release state.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`
- exact source: `d0620d80d06288bdc2c28c019c8661ce8a5ab4d8`
- workflow: `CMPCT v0.30 Logs restore attribution`
- workflow run: `33696691763`
- substantive job: `100466974259` (`pack-components`)
- artifact id: `9872080048`
- artifact: `v030-logs-pack-components-d0620d80d06288bdc2c28c019c8661ce8a5ab4d8`
- artifact ZIP digest: `sha256:62179752b25867a09e342b5d51875ce598f7120e25adc02a5f9421087e48194d`
- schema: `cmpct-v030-logs-pack-materialization-component-attribution-v1`
- target: `neutral_hostile_v1/05_logs_and_telemetry`
- rounds: **11 paired alternating control/instrumented rounds** after one warm-up per arm
- release credit: **false**

The substantive measurement, frozen contract ratchet, CI-topology self-check, public-surface guard and artifact upload all completed successfully. This is result-bearing evidence, not a classifier-only green.

## Exactness and instrumentation validity

The measured archive remained the promoted `logs-inverse` representation and was strongly verified before timing. Every instrumented extraction executed the same authenticated `_read_pack` semantics: exact seek/read, any required Zstd decompression, CRC32 over the complete raw pack, SHA-256 over the complete raw pack, bounds/length checks and exact logical-tree reconstruction. No authentication work was disabled or gifted away.

- control median total extraction: **0.035676437000006445 s**
- instrumented median total extraction: **0.03573732600000312 s**
- instrumentation wall ratio: **1.0017067006998672x**
- frozen maximum: **1.10x**
- median authenticated `_read_pack` total: **0.011354929000049196 s**
- stable pack calls: **7**
- stable raw-pack calls: **5**
- stable Zstd-pack calls: **2**
- call counts stable: **true**

The instrumentation therefore perturbed total extraction by only about **0.171%**, far below the frozen 10% validity ceiling.

## Exact component result

| Existing authenticated-pack component | Median time | Share of total extraction | Frozen material floor | Decision |
|---|---:|---:|---|---|
| seek + exact payload read | **0.00026494300027479767 s** | **0.74136%** | >=2 ms and >=5% | not material |
| Zstd materialization | **0.003463151999994807 s** | **9.69057%** | >=2 ms and >=5% | **material** |
| CRC32 authentication | **0.0022630109999681736 s** | **6.33235%** | >=2 ms and >=5% | **material** |
| SHA-256 authentication | **0.005339030000072853 s** | **14.93965%** | >=2 ms and >=5% | **material** |
| explicit remainder | **0.00001334899991434213 s** | ~0.037% | diagnostic | negligible |

Frozen terminal decision:

**`PACK_SHA256_HEADROOM+PACK_ZSTD_HEADROOM+PACK_CRC32_HEADROOM`**

## Causal interpretation

The predecessor restore-inner result showed authenticated pack materialization at roughly **31.7%** of complete promoted Logs extraction. This follow-up explains almost all of that pack cost. Under the exact warm-cache hosted-runner regime, seek/read itself is tiny; the actionable cost is CPU work performed after the payload arrives.

The largest tracked owner is SHA-256 authentication, followed by Zstd materialization and then CRC32 authentication. The explicit remainder is only tens of microseconds, so another Python dispatch/bounds micro-optimization inside `_read_pack` is not a serious Forge target.

The result is especially useful because the Logs release red is narrow rather than catastrophic: the last substantive promoted Logs extraction ratio was about **1.3003x** against a hard **1.25x** ceiling, requiring approximately **3.87%** reduction in candidate extraction time from that exact product regime. Zstd materialization alone is about **9.69%** of the measured total here; SHA-256 plus CRC32 together are about **21.27%**. There is therefore plausible release-scale headroom, but none of those percentages can be mechanically subtracted from another exact-head receipt.

## Negative constraint: pack I/O retired under this regime

`PACK_IO_HEADROOM` did not cross either materiality threshold. Do not spend v0.30 Forge activations on seek coalescing, path-layout changes, buffered-read tuning or similar pack-I/O work for this exact warm-cache seven-pack Logs regime without a reopening predicate.

Reopen pack I/O only if at least one of the following changes materially:

1. evidence is explicitly about a cold-storage / high-latency device regime rather than the frozen hosted-runner product gate;
2. archive layout or pack count changes enough to alter syscall/read behavior materially;
3. a new trace proves I/O itself crosses the same millisecond-scale materiality floor.

## Non-borrowable integrity boundary

CRC32 and SHA-256 are material costs, but correctness/integrity are not borrowable debt. This result does **not** authorize removing either check, hashing fewer bytes, trusting metadata without recomputation, reusing a verification result across operation boundaries, or weakening corruption rejection/recovery guarantees.

A future implementation may attack duplicate memory passes or use a different implementation route only if the exact same authenticated facts remain established before publication. Any such change requires explicit hostile-corruption evidence in addition to performance evidence.

## Forge decision and next lowest-sufficient intervention

The lowest-risk next intervention is the **Zstd implementation/lifetime seam**, because it is material and does not require redesigning the integrity contract. The current inherited `_read_pack` constructs a fresh `zstd.ZstdDecompressor()` for each compressed pack; this exact workload performs two compressed-pack materializations per extraction.

Freeze an operation-scoped reusable-decompressor A/B before product modification:

- reuse one ordinary `ZstdDecompressor` only within one full authenticated restore operation;
- keep cold selective-read semantics unchanged;
- preserve exact archive/tree bytes, CRC32, SHA-256, bounds, hostile-corruption rejection, recovery and locality;
- alternate enough paired rounds to resolve the narrow product gap;
- require a material total-extraction improvement rather than merely proving constructor reuse occurs.

If reusable decompression cannot recover meaningful total wall time, retire that family and move to a security-preserving way of reducing duplicate authenticated byte scans, with CRC32 and SHA-256 still both established. Do not optimize the retired I/O/remainder components first.

This result grants **zero release credit**. Only a promoted-product runtime receipt on the resulting exact implementation can alter the v0.30 release state.
