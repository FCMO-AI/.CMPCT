# ONE-G0.2 — compact rescue queue result

**Status:** result-bearing native encoder-discovery evidence; advances to integration review only  
**Exact source:** `7fe2f7f2c034c680842e8897579f4c617527262d`  
**Workflow:** `33945883605`  
**Job:** `101251764097`  
**Artifact:** `9963308247`  
**Artifact digest:** `sha256:92e1746831b5d6baddfbf295e9d8a00ad3c554ca28a4dd9bbbf5f03c52e92c42`  
**Experiment:** `ONE-G0.2`

## Referee freeze

The preceding linear activation-time rescue queue preserved the full 4,096-position rightmost-min opportunity but reserved 71,680 B because each possible queue slot carried a 64-bit value and a 64-bit absolute position.

The tested representation keeps every one of the 4,096 queue slots and every 64-bit value, but stores positions modulo 8,192 in `uint16_t`. Because every live entry is younger than 4,096 positions, `current_position mod 8192` and the stored modular position uniquely determine the live age. No queue-capacity reduction or opportunity threshold is used.

Frozen promotion required:

- exact nomination trace and accounting equality on every case;
- candidate reserved state <= 0.70x the linear baseline;
- median compact/linear elapsed <= 1.03x on both entropy controls and the shifted large case;
- no tested median > 1.10x;
- hostile shifted vectors crossing the 8,192- and 16,384-position modulo epochs.

Failure was defined to retire this compact-position implementation without threshold tuning.

## Result

**Decision:** `advance_compact_queue_for_integration_review`.

All eight cases preserved exact trace and accounting semantics. Reserved state was **47,104 B vs 71,680 B**, or **0.657143x**: a **34.29% reduction** while retaining all 4,096 queue slots.

| Case | Input bytes | Median compact / linear | p90 | Peak live queue | Emitted |
|---|---:|---:|---:|---:|---:|
| random_1mib | 1,048,576 | 0.993489x | 0.995688x | 18 | 22 |
| zlib_random_1mib | 1,048,902 | 0.990753x | 0.994801x | 18 | 23 |
| repeat_64k_basis_1mib | 1,048,576 | 0.932571x | 0.947677x | 15 | 32 |
| shifted_512k_insert1 | 1,048,577 | 0.995113x | 0.999920x | 22 | 26 |
| boundary_random_4160 | 4,160 | 1.023553x | 1.030842x | 0 | 0 |
| transfer_starved_seed10_insert1 | 8,193 | 0.929357x | 0.986811x | 21 | 3 |
| wrap_shifted_20000 | 40,001 | 0.967922x | 1.032904x | 15 | 4 |
| wrap_shifted_40000 | 80,001 | 0.971498x | 1.015278x | 17 | 8 |

The critical entropy and shifted-large medians all remained below the frozen 1.03x ceiling. The only median slowdown was the just-enabled 4,160-byte boundary at **1.023553x**, still inside the frozen gate. Both explicit wrap controls preserved exact semantics across multiple modulo epochs.

## Mechanism-level interpretation

The state reduction is not a capacity or benchmark-specific threshold trick. It follows from a bounded-age invariant: an exact sliding queue whose maximum live age is 4,095 does not need an unbounded absolute position per live entry. The chosen 8,192 modulus is strictly larger than twice the maximum live age and therefore leaves the live-age mapping unambiguous.

This result closes the largest remaining **state representation** debt in the deferred rescue prototype, but it does **not** establish that deferred rescue is globally worth carrying. The promoted ordinary discovery baseline remains the 8 KiB tail-return counter/offset dispatcher at 41,056 B on its offset path. Compact rescue still reserves 47,104 B and performs starvation tracking/history work even where its extra opportunity may have no value.

## Hostile review / claim boundary

This is **native encoder-discovery A/B evidence only**. It grants no product speed, stored-byte, reader, v0.29/v0.30 comparator, release, access, integrity, recovery or portability authority.

The strongest surviving criticism is opportunity economics, not queue representation: a correct and reasonably compact rescue path can still be a bad global mechanism if its always-paid observation/history cost exceeds the value of the shifted/starved opportunities it uniquely recovers.

## Next decisive experiment

Run an end-to-end charged comparison between:

1. the promoted 8 KiB tail-return selector baseline; and
2. the compact starvation-rescue path with all required signal/history/queue work and reserved state charged.

The comparison must retain the hard shifted/starvation opportunities, include ordinary random/compressed/repeated controls, and report elapsed + retained state + unique opportunity recovered. The rescue mechanism advances toward integration only if the extra opportunity earns its global carrying cost rather than merely passing an internal queue-vs-queue microbenchmark.
