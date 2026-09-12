# v0.30 R4 composed Mode2 + Office federation result — 2026-09-11

Status: **SUPPORTED FOR LOCALITY / PHYSICAL-HARDENING; NOT RELEASE CREDIT**

Exact evidence authority:
- branch: `agent/v030-authoritative-integration`
- source commit: `99e7926fbdfdbb3358d6faa317261f8084b26ff1`
- workflow run: `34664041006`
- job: `103472239441`
- artifact: `10288730465` (`v030-r4-composed-mode2-office-99e7926fbdfdbb3358d6faa317261f8084b26ff1`)
- artifact ZIP SHA-256: `c8441ede7a9338ead5c8250a4ce4190c1b906cccc583cff265063b4885d5add3`
- benchmark: `benchmarks/v030_r4_composed_mode2_office_full_matrix.py`
- schema: `cmpct-v030-r4-composed-mode2-office-full-matrix-v1`

This receipt is diagnostic/research evidence only. It changes neither the canonical shipping format nor the production selector and consumes no numeric release version.

## Mission lock

Falsifiable hypothesis before the run: two already-isolated structural mechanisms should compose without post-hoc selection or collateral regressions:

1. Analytics exact structural relation -> `analytics-mode2`;
2. Office exact compressed-stream identity -> `office-exact-stream-federation-v2`;
3. every other Genesis workload -> exact ordinary v0.30 fallback.

Disproof conditions included any extra admission, any byte regression in a fallback workload, semantic-tree mismatch, either mechanism failing to save bytes, or aggregate candidate bytes not improving the same-run v0.30 baseline. Beating v0.29 aggregate was recorded but deliberately was **not** required to call the composition scientifically useful.

## Exact 15-workload result

Logical bytes: `265,969,714 B`.

| Metric | Same-run v0.30 | Composed candidate | Delta |
|---|---:|---:|---:|
| authenticated stored bytes | 150,059,822 B | **138,616,788 B** | **-11,443,034 B** |
| creation tree CPU (sum) | 851.796104 s | **529.902021 s** | **-321.894083 s** |
| creation wall (sum) | 366.668473 s | **254.993343 s** | **-111.675130 s** |

Frozen Genesis references:
- v0.30: `150,055,575 B`;
- v0.29: `137,499,525 B`.

The composed candidate is `11,438,787 B` smaller than frozen Genesis v0.30 and remains **`1,117,263 B` larger than frozen v0.29** (~0.813%). It therefore closes about 91% of the aggregate Genesis v0.30 -> v0.29 byte deficit without buying the recovery through more creation compute.

### Office

- same-run v0.30: `15,445,448 B`;
- exact-stream-federation-v2: **`10,197,268 B`**;
- saving: **`5,248,180 B`**;
- creation tree CPU delta: **`-63.486546 s`**;
- creation wall delta: **`-26.647523 s`**.

### Analytics

- same-run v0.30: `10,392,494 B`;
- analytics-mode2: **`4,197,640 B`**;
- saving: **`6,194,854 B`**;
- accepted frozen/source-sealed v0.29 Analytics floor: `6,135,172 B`;
- margin below that v0.29 floor: **`1,937,532 B`**;
- creation tree CPU delta: **`-260.776125 s`**;
- creation wall delta: **`-86.302282 s`**.

Admissions were exactly the preregistered two. The remaining **13/15** workloads were exact v0.30 fallback and the receipt reports **zero byte regressions**.

## Interpretation

This is mechanism-level evidence that the dominant v0.30 Genesis density debt was not a need for globally higher compression effort. Two sparse structural opportunities recover `11.443 MB` while also eliminating large amounts of creation work:

- Office: duplicate exact compressed streams across ZIP-like containers can be physically federated;
- Analytics: complementary exact tabular and NPY/NPZ relationships permit one representation to own information that ordinary v0.30 stores redundantly.

The creation-compute improvement is strategically important. It is consistent with the ONE Genesis lesson that cheap opportunity gating plus elimination of redundant discovery/work is preferable to reviving v0.29-style global search cost.

## Regression debt / hostile review

This result is **not promotable** yet.

1. **Analytics Mode2 locality remains open and severe.** The retained density result has previously shown a worst selective reconstruction case around `937.53x` for a 4 KiB read because the exact DEFLATE stream can require regeneration from its beginning. The inherited product target is <=8x. This debt is not averaged away by the aggregate size win.
2. **Office locality is still an ideal/model result, not final physical I/O authority.** Exact file-backed range reads must include authenticated index/proof bytes, recovery semantics and reader complexity.
3. **Integrity/recovery packaging is still a research wrapper.** The final product representation must price authenticated metadata, corruption isolation, recovery blast radius and bounded hostile-input behavior.
4. **The aggregate still loses to v0.29 by 1,117,263 B.** No claim that v0.30 has beaten the frozen mature density authority is permitted.
5. No format/release/version credit is earned by this diagnostic composition.

## Decision

`ADVANCE_LOCALITY_REHABILITATION`.

The next decisive question is no longer whether the two density mechanisms compose; they do. The next question is whether their gains survive real product locality/integrity semantics.

For Analytics, first falsify the cheapest representation-boundary repair: retain the ordinary localized NPY owner while paying only the minimum exact physical view necessary to make NPZ reads independently addressable/authenticated. The experiment must charge every added byte and reject the repair if it spends the `1,937,532 B` Analytics margin versus v0.29 or fails <=8x selective work.

Conventional restart-window checkpoints are not to be revived merely to obtain a green result: prior budgeting showed their state/windows consume more than the available density margin. If the minimal dual-view repair also fails, escalate to a genuinely smaller restart-state/chunk ownership representation rather than weakening locality.

For Office, convert the current ideal touch model into authenticated file-backed selective I/O measurement before any release design.

## Frozen ONE context

This result does not alter the 2026-09-11 ONE Genesis verdict. v0.30 remains the primary near-term research line; ONE remains durable secondary evidence and its compute-efficiency mechanisms remain valid inputs. No ONE score or frozen contender result is rewritten by this R4 work.
