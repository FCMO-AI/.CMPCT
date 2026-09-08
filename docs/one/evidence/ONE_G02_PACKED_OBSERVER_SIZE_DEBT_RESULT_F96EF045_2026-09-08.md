# ONE-G0.2 packed observer dense-size debt — exact result at `f96ef045` — 2026-09-08

Status: **semantic exactness retained; previous 256 KiB compressed/long-run reds did not reproduce, but a stable tiny-output `near_repeats` regression was exposed. General packed promotion remains blocked.**

## Exact evidence authority

- exact source SHA: `f96ef04521d129df086bb4fd17d4332e4e8fc485`
- workflow run: `34220403805`
- job: `102041919409`
- artifact id: `10053618631`
- artifact name: `one-g02-packed-observer-size-debt-f96ef04521d129df086bb4fd17d4332e4e8fc485`
- artifact digest: `sha256:c36565eeeb9ef98561f744e3eeaec30c759d179215534b344215aada55f81d4b`
- exact checkout/binding, frozen diagnostic, semantic gates and artifact retention: passed

## Family classifications

- `structured`: `NO_256K_RED_ON_REPEAT`
- `compressed_like`: `NO_256K_RED_ON_REPEAT`
- `long_runs`: `NO_256K_RED_ON_REPEAT`
- `random`: `NO_256K_RED_ON_REPEAT`
- `near_repeats`: **`STABLE_ADJACENT_REGRESSION`**

The original rehabilitation's 256 KiB `compressed_like` 1.126x and `long_runs` 1.088x reds did not reproduce under the denser exact-source run. At 256 KiB they measured approximately 0.994x and 0.964x packed/eager wall respectively, with both immediate neighbors clear. Those old rows remain historical evidence, but the hypothesis of a stable 256 KiB cliff for those families is weakened substantially.

## Dense wall/CPU ratios

| KiB | structured | compressed_like | long_runs | random | near_repeats |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 128 | 0.393/0.394 | **1.051/1.050 RED** | 0.875/0.875 | 0.977/0.977 | 0.969/0.969 |
| 192 | 0.358/0.358 | 0.990/0.991 | 0.967/0.967 | 0.914/0.914 | 0.897/0.893 |
| 256 | 0.352/0.353 | 0.994/0.994 | 0.964/0.964 | 0.996/0.996 | **1.115/1.115 RED** |
| 384 | 0.351/0.351 | 0.998/0.998 | 0.966/0.967 | 1.001/1.000 | **1.114/1.114 RED** |
| 512 | 0.347/0.347 | 0.999/1.000 | 0.966/0.967 | 1.013/1.013 | **1.102/1.103 RED** |
| 768 | 0.346/0.346 | 0.996/0.996 | 0.964/0.964 | 0.992/0.992 | 1.039/1.039 |
| 1024 | 0.348/0.348 | 0.999/0.998 | 0.971/0.971 | 0.971/0.973 | **1.097/1.096 RED** |

Every semantic/wire/root check remained exact.

## Strongest causal interpretation

`near_repeats` emits exactly **one 24-byte run record and zero reuse records** across this matrix. That is an important regime distinction:

- zero-output cases can pack to empty bytes and are generally near parity;
- high-output structured cases avoid thousands of Python opportunity objects and win by ~65%;
- tiny nonzero output pays `ctypes.string_at`/packed-bytes construction and retention for essentially no materialization forest to avoid.

This makes a mechanism-level fixed-cost hypothesis more plausible than a raw size threshold. The likely problem is not “256 KiB is bad”; it is **packing a tiny useful prefix when eager materialization is itself tiny**.

That hypothesis is still not proven because the 192 KiB `near_repeats` row is strongly favorable (~0.897x), 768 KiB is clear (~1.039x), and the earlier exact 1 MiB rehabilitation row was ~1.004x rather than the new ~1.097x. Allocator/runtime context therefore still contributes materially.

## Scientific consequence

Do **not** create a hand-authored size cutoff. Also do not promote `observe_native_packed()` as the universal writer boundary yet.

The next falsifier should isolate the tiny-output regime in fresh processes and compare three mechanisms after the same native scan:

1. eager Python materialization;
2. exact-prefix packed bytes;
3. a bounded inline/small-output handoff that avoids both a Python opportunity forest and a `ctypes.string_at` allocation/copy for one/few native records.

The selection variable, if any, must be the already-known observer output cardinality/used bytes—not source size—and any break-even must be preregistered from measured component costs rather than tuned to this matrix.

## Campaign truth

This result changes writer implementation economics only. Stored bytes, reader semantics, selective-read amplification, reconstruction semantics, durability, recovery, portability and frozen v0.29/deferred-v0.30 authority are unchanged. The earlier `ADVANCE_PACKED_OBSERVER_REHABILITATION` remains a valid bounded exact-run result, but its universal no-regression implication is **not reproducible** on `near_repeats`; broader promotion is therefore blocked pending the small-output falsifier.
