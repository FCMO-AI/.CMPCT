# v0.30 Shifted bounded-drift R4 strict candidate win

Status: **PROMOTE_NEXT_PREREQUISITE** as research evidence only. This is not release credit and does not change canonical r25 grammar or production selection.

## Exact evidence

Source commit: `65f0fa9d20c9db99ef972c216c9ba4d849810be4`

Workflow: `CMPCT v0.30 Shifted bounded-drift edit R4 floor`

Run: `33456109759`

Job: `99696281794`

Frozen Shifted tree: `d9106dcdc8f965d45236c241d6c45f773e10b84ac204acc3c3521d889cd3a8fd`

The candidate chooses one complete base solely by logical-content SHA-256, represents siblings with bounded sequential copy/replace/insert/delete programs, compresses all edit programs in one shared context, keeps reconstruction depth 1, and prices edit search, both compression contexts, durable candidate publication and SHA-256 binding inside candidate creation time.

Measured result:

- complete candidate: **1,687,692 B**
- candidate creation: **0.360600381 s**
- solid Zstd-19: **1,694,672 B / 0.762426491 s**
- ZIP/Deflate-9: **30,283,112 B / 0.753036434 s**
- complete size margin versus Zstd-19: **6,980 B smaller**
- payload floor margin versus Zstd-19: **8,034 B smaller**
- candidate speed margin versus Zstd-19: about **2.11x faster**
- candidate speed margin versus ZIP: about **2.09x faster**
- shared raw edit bytes: `22,764`
- shared stored edit bytes: `8,679`
- copied logical bytes: `33,506,538`
- edit records: `867`
- max decode unit: `1,862,620 B`
- max member read amplification: about `2.0123x`
- exact tree verification: PASS
- benchmark identity in representation: false
- artifact SHA-256: `518957399a1f37e6bf8e1bd36196d513d22e2fbcb34a68866f2fd349627bd70f`

## Domination audit

- strict target: 15/15 workloads strictly smaller and faster than ZIP/Deflate and solid Zstd-19; ties fail
- diagnosis: `D4`
- radicality: `R4`
- inherited saturation: `S1`, `S3`, `S4`
- RPS: `100`
- measured gap change: from the retired latent patch-pack at `+12,303 B` versus Zstd to this candidate at `-6,980 B`, while creation falls from ~11.708 s to ~0.361 s
- strongest surviving self-critique: this exact win is on one frozen structural red; generic admission, canonical semantics, recovery, native/Android parity, accepted-v0.29 no-regression and the exact common 15-workload authority are still unproven
- terminal decision: **PROMOTE_NEXT_PREREQUISITE**

## Next prerequisite

The representation must now prove it is a generic mechanism rather than a benchmark trick. The first productization seam is a workload-blind bounded-drift primitive with:

1. content-only base selection;
2. deterministic encode/decode independent of paths and member ordering;
3. hostile corruption/resource fail-closed behavior;
4. bounded depth/decode units and explicit locality accounting;
5. structural admission based on actual priced benefit, never benchmark names/hashes;
6. only after that, canonical writer/reader/recovery semantics and native/Android parity.

A later productization gate may still reject the mechanism. The strict candidate win does not authorize shipping by itself.
