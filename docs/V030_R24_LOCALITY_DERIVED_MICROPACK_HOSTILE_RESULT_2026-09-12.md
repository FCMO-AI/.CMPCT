# v0.30 r24 locality-derived micro-pack hostile transfer result — 2026-09-12

Status: **research evidence; no release credit**

Exact measured head: `66558bf938938630e04124751bf8e60030ae4ee0`
Hosted run: `34737316493`
Receipt artifact: `v030-hostile-generalizes-bal-7684fok-skew-14097fok-noise-8581fok-dup-4137fok-single-60fok-66558bf938938630e04124751bf8e60030ae4ee0`
Scientific verdict: `LOCALITY_DERIVED_MICROPACK_GENERALIZES`

The older hostile red at `508236fa...` is not product evidence: it failed inside the benchmark before emitting a receipt and was followed by `fix(v030): restore earned micropack eligibility mechanism`. This document records the corrected exact-head rerun.

All five hostile families preserved strong-tree identity, physical payload identity, tail recovery where applicable, and the fixed 8x locality contract. All five were strict stored-byte wins versus the same-grammar independent control:

| Family | Independent | Candidate | Delta | Groups | Members | Max amp | Max decode |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| balanced structured text | 162,154 B | 154,470 B | **-7,684 B** | 15 | 96 | 8.0x | 9,544 B |
| skewed structured text | 125,144 B | 111,047 B | **-14,097 B** | 12 | 61 | 7.9962x | 50,776 B |
| incompressible text-labeled | 839,959 B | 831,378 B | **-8,581 B** | 4 | 32 | 8.0x | 196,608 B |
| duplicate forest | 44,434 B | 40,297 B | **-4,137 B** | 5 | 40 | 4.0x | 20,480 B |
| singleton buckets | 18,410 B | 18,350 B | **-60 B** | 2 | 5 | 2.9917x | 2,379 B |

No hostile family showed an economic or invariant loss. This materially strengthens the mechanism beyond Developer/Tiny origin evidence, including an adversarial incompressible-text-labeled case and duplicate-heavy input.

Promotion is still blocked by policy dependence: current eligibility and grouping use mature text-extension hints. The hostile corpus demonstrates that the mechanism survives adverse bytes under those hints; it does not prove that filename-derived policy is necessary or acceptable. That question is separated into explicit ablation/path-blind admission work rather than hidden inside this verdict.
