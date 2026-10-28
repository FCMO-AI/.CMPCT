# v0.30 Office external gap — first causal read

Status: **DIAGNOSTIC EVIDENCE — NEXT ORACLE NARROWED**

Parent receipt: `docs/v030-rnd/V030_EXACT_HEAD_EXTERNAL_FRONTIER_B2260DB.md`.

## Observation from the exact-head artifact

The Office row in exact-head run `35285383961`, job `105417365534`, is not merely a 15.45 MB opaque loss. The uploaded candidate profile exposes the internal tournament:

- canonical published CMPCT: **15,445,236 B**, selected `r24-fallback`;
- canonical outer create: **39.8801 s**;
- canonical r24 build: **15,445,236 B**, **0.1418 s** internal build time;
- nested r25/G0-G4 tournament reported `g04_selected = v029-fallback`;
- nested G0-G4 `v029_bytes`: **5,954,226 B**;
- G0-G4 pre-overlay graph: **11,632,757 B**;
- G0-G4 overlay: **11,632,888 B**;
- PrefixGraph candidate: **7,607,844 B**, contract-eligible but rejected because it was not smaller than the G0-G4/v0.29 floor;
- G0-G4 portfolio create: **29.4955 s**;
- shared candidate build: **12.5859 s**;
- v0.28 child: **11.9339 s**;
- attempt5 child: **12.4496 s**;
- r25 tournament total: **39.8297 s**;
- ZIP/Deflate-9: **15,493,019 B**, **0.3910 s** create;
- solid Zstd-19: **8,312,879 B**, **1.3749 s** create;
- 7z solid: **7,455,748 B**, **1.0621 s** create;
- ZPAQ method 5: **7,238,801 B**, **38.2281 s** create.

This is a much sharper diagnosis than “invent a better Office codec.” An already-built internal floor is only **5.95 MB**, materially smaller than Zstd-19, 7z and ZPAQ, yet the canonical product publishes the **15.45 MB** r24 artifact instead.

## Why the 5.95 MB number is not yet a product win

Do **not** promote or directly publish the 5.95 MB candidate from this observation. The outer canonical selector deliberately requires the r25 candidate to parse as canonical revision 25, beat the v0.29 floor, and beat canonical r24. The nested tournament selected its `v029-fallback`; the artifact profile then reports `r25_product_bytes = null`, so the outer selector correctly refuses to call those bytes canonical r25 and falls back to the genuine r24 product.

There is also a known reason to distrust a historical compact r24/v0.29 byte floor as a release substitute: the current release r24 path retains exact Deflate streams to obey the <=8x selected-member locality law. The 5.95 MB floor must therefore be tested for locality, exact product semantics, integrity/recovery and canonical-reader compatibility before it receives any product credit.

The current evidence proves **headroom exists inside the already-computed portfolio**; it does not yet prove that headroom is legally materializable.

## New falsifiable mechanism hypothesis

**H-Office-ownership:** most of the 7.13 MB Office loss to Zstd-19 is not an entropy-coding floor. It is an ownership/compatibility gap between a compact already-computed v0.29-style representation and the stricter canonical r24/r25 product contract. If the compact floor can be re-expressed under canonical r25 semantics with <=8x locality and exact reconstruction at modest overhead, Office can cross the Zstd/7z frontier without inventing a new compressor.

Strong simpler control: canonical PrefixGraph already measures **7,607,844 B**, which is also below Zstd-19 and only ~152 KB above 7z. It was rejected only because the nested v0.29 floor was smaller. A diagnostic arm that compares *legal canonical materialization*, not merely nested byte minimum, can determine whether PrefixGraph is already the cheapest shippable Office route.

Disproof conditions:

1. the 5.95 MB floor violates locality or cannot be represented canonically without >~2.36 MB overhead (enough to lose Zstd-19);
2. PrefixGraph cannot preserve exact filesystem/product semantics or <=8x locality on the real Office tree;
3. legal materialization remains >= Zstd-19 after full manifest/integrity/recovery charge;
4. create-time cost remains so large that the strict size+create contract cannot plausibly be rehabilitated.

## Next decisive instrument

Build an Office-only **legal-materialization oracle** on the exact frozen tree. It should emit, side by side:

1. shipping r24 bytes/time/locality;
2. raw nested v0.29 floor bytes plus explicit locality verdict — research bound only;
3. PrefixGraph complete bytes plus manifest/product charge, exact tree verification and max selected-member amplification;
4. the cheapest canonical-r25 encoding of the nested floor if such a representation already exists, with every required decoder fact charged;
5. Zstd-19 and 7z same-input controls;
6. per-arm create CPU/wall and candidate-build ownership.

Do not run the full 15-workload matrix to answer this first question. The purpose is to determine whether Office is a **representation legality/ownership problem** or a true missing-compression problem. Only after a legal arm survives should it return to the full matrix.

## Efficiency consequence

The timing profile independently exposes massive losing-search work: the final r24 product is built in ~0.14 s while the overall CMPCT Office create takes ~39.88 s, almost all of it spent in an r25 tournament that is discarded. Even if no compact representation can be legalized, Office therefore contains a separate high-headroom admission/search problem. A proof-directed early rejection that safely predicts “r24 will win” could remove tens of seconds on this row; conversely, if PrefixGraph/legalized compact bytes can win, the same evidence should be used to avoid building dominated candidates.

This makes Office unusually valuable: one focused oracle can attack both the largest external byte loss and one of the clearest create-time waste owners without changing benchmark semantics.
