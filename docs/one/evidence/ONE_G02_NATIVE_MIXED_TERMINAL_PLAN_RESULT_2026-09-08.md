# ONE-G0.2 Native Mixed Terminal Plan — exact result

Status: **HOLD_NATIVE_MIXED_TERMINAL_PLAN**

## Authority
- source SHA: `5cd4c07ac77afaad91ed0bc4adc31106bdc13d4f`
- workflow run: `34285229444`
- job: `102259141951`
- artifact: `10079198122`
- artifact digest: `sha256:eb7a76d4628c300ce043494e1fb6ada98b7001570b277b615c468dcca0942357`

Exact branch-head checkout/binding passed; the environment installed and all 18 semantic/decision-law tests passed. The benchmark's non-zero exit is the scientific HOLD. An earlier attempt lacking pytest / exact PR-head binding is inadmissible; thresholds, matrix, candidate and interpretation were unchanged by the CI repair.

## Result
The same validated terminal `Surprise` / `Fill` / `Concat` Program was lowered into one destination-ordered native COPY/FILL schedule per root. Preparation was measured separately; root allocation, full SHA-256 authentication and output freezing remained charged.

At 1 MiB:

| family | wire/literal | mixed/literal wall | mixed/literal CPU | mixed/prepared wall | mixed/prepared CPU |
|---|---:|---:|---:|---:|---:|
| structured | 0.875018x | 1.481859x | 1.481554x | 1.201788x | 1.201790x |
| compressed_like | 1.000000x | 1.481402x | 1.480873x | 1.519366x | 1.518852x |
| long_runs | 0.501019x | 1.510496x | 1.510516x | 1.219072x | 1.218779x |
| random | 1.000000x | 1.887482x | 1.886785x | 1.923682x | 1.922886x |
| near_repeats | 1.000000x | 1.521801x | 1.521176x | 1.540563x | 1.539911x |

`long_runs` retains ~0.501x literal wire and 0.90x modeled traffic, but mixed replay is ~2.646 ms wall versus ~1.752 ms literal and ~2.171 ms prepared. `structured` retains ~0.875x wire and 0.975x traffic but is ~1.482x literal and ~1.202x prepared. The negative persists below 1 MiB: 64 KiB long-runs is ~1.474x literal / ~1.296x prepared; at 256 KiB Law-bearing rows are ~1.54–1.55x literal / ~1.22–1.25x prepared. Incremental break-even is infinite on decisive rows because the hot mixed path itself is slower.

## Causal interpretation / stop condition
This falsifies the hypothesis that Python Surprise scatter plus separate Surprise/Fill execution boundaries were the remaining material cost after prepared-plan compilation. One terminal-specific native mixed boundary makes the path materially worse, despite exact semantics and unchanged density/traffic.

The preregistered stop condition is therefore reached. Do not relax the 1.05x literal gate, add a run-only dispatcher, gift more terminal prepacking outside the timer, or invent a reader-visible run mechanism. Terminal-specific micro-optimization stops here.

The useful result survives at the representation level: automatic observation found a strong generic ONE Law (~0.501x wire on long-runs) with lower modeled traffic. Reader work now moves upward to a **general reconstruction-plan/native execution model** spanning multiple Law shapes, with preparation, memory, selective-access, integrity and portability costs measured explicitly.

## Claim boundary
No stored grammar, Surprise semantics, integrity requirement or reader-visible mechanism changed. No Genesis comparator point is earned. Frozen v0.29 and deferred v0.30 remain the authorities in `docs/CMPCT1_GENESIS.md`. This is full-root execution evidence only; it makes no selective-range, RSS, recovery, or canonical-native-backend claim.
