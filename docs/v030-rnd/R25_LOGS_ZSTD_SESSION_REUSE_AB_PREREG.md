# Logs operation-scoped Zstd decompressor reuse A/B — preregistration

Status: **FROZEN FORGE R1 REHABILITATION TEST / NO RELEASE CREDIT**

## Causal predecessor

`R25_LOGS_PACK_MATERIALIZATION_COMPONENT_ATTRIBUTION_RESULT.md` established, on the exact promoted Logs restore boundary, that Zstd materialization costs **3.463152 ms / 9.69057%** of total extraction while pack seek/read is only **0.264943 ms / 0.74136%**. The same receipt observed exactly **2 Zstd pack calls** per full extraction. SHA-256 and CRC32 are also material, but both are non-borrowable integrity work.

The current inherited `_read_pack` constructs `zstd.ZstdDecompressor()` independently for each compressed pack. This frozen R1 experiment asks whether reusing one ordinary decompressor object **inside one full authenticated Archive operation only** recovers enough total extraction wall time to matter, without changing any compressed bytes, decompression semantics or authentication facts.

## Frozen intervention

Control: exact promoted fused Logs extraction with inherited `_read_pack`.

Candidate: for one Archive instance/full extraction operation only, lazily construct one `zstd.ZstdDecompressor` and reuse it for every compressed pack read by that Archive. Everything else in `_read_pack` remains byte-for-byte semantically equivalent:

- same exact seek/read and short-read rejection;
- same `max_output_size=usize` bound;
- same exact raw length check;
- same CRC32 over the complete decompressed/raw pack;
- same SHA-256 over the complete decompressed/raw pack;
- same expected CRC/SHA comparisons and fail-closed behavior;
- same pack cache, inverse decode, logical-member SHA-256, filesystem publication, recovery and locality law.

The candidate may not persist the decompressor across Archive instances or operations. Cold selective reads and independent callers therefore remain independent. This is an experiment only; production code is unchanged.

## Frozen target and execution

- target: deterministic `neutral_hostile_v1/05_logs_and_telemetry`;
- exact promoted `logs-inverse` archive produced once before timing;
- exact selected archive bytes/SHA and canonical tree fixed across arms;
- complete promoted strong verification before timing;
- one untimed warm-up per arm;
- **21 paired rounds**, alternating control-first / candidate-first;
- `gc.collect()` immediately before each timed extraction;
- exact canonical tree after every extraction;
- candidate must record exactly one decompressor construction and exactly two compressed-pack decompressions per measured extraction;
- control must remain the inherited implementation.

## Frozen decision bands

The known product-level Logs gap is narrow: the latest substantive promoted receipt is approximately `1.3003x` v0.29 versus the unchanged `1.25x` release ceiling, corresponding to roughly **3.87%** candidate-time reduction from that exact product state. That cross-head number is context only, never release evidence.

For this A/B:

- candidate median total extraction reduction **>=4.0%**, candidate/control wall ratio `<=0.96x`, all exactness/lifecycle gates pass -> **`LOGS_ZSTD_SESSION_REUSE_SUPPORTED`**;
- reduction **<1.0%** -> **`LOGS_ZSTD_SESSION_REUSE_RETIRED`**;
- reduction from **1.0% to <4.0%** -> **`LOGS_ZSTD_SESSION_REUSE_AMBIGUOUS`**;
- any exactness, authentication, lifecycle or instrumentation failure -> **`INVALID_LOGS_ZSTD_SESSION_REUSE_AB`**.

No rerunning until noise crosses a band. A future retry requires a materially different Zstd binding/implementation, pack-count regime or decompressor construction path.

## Safety / release law

This experiment does not remove, combine, weaken or defer CRC32 or SHA-256. It does not alter archive grammar, pack bytes, compression level, selector, recovery, locality, decode-unit limits, competitor settings or release thresholds. It grants **zero release credit**.

If supported, the next step is the smallest production implementation of the same Archive-instance-scoped reuse followed by exact hostile-corruption/recovery tests and the normal promoted product runtime gate. If retired, move to the next material authenticated-byte-scan owner rather than I/O/remainder tuning.
