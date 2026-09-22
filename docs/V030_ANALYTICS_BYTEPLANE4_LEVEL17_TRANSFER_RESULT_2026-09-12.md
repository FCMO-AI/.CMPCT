# v0.30 Analytics BytePlane4 + level-17 transfer result — 2026-09-12

Status: **positive research seed; not product/release authority**.

Source head: `673f65c74bd016fb589d23cdc75ac8b62dff78e6`
Hosted run: `34731374179`
Schema: `cmpct-v030-analytics-byteplane4-level17-transfer-v1`

## Frozen hypothesis

The prior effort frontier identified level 17 as the unique non-dominated lower-effort global point near the accepted v0.29 Analytics byte floor. The already-frozen width-4 BytePlane transform had earned 71,951 B against direct level 19. Before measuring this transfer, the arithmetic gap was only 3,836 B: direct level 17 needed 75,787 B to reach accepted v0.29.

The test therefore froze level 17, width 4, and the prior path-blind level-1 exact-framed audition. It did not sweep levels, widths or thresholds. Three modes were measured on the same normalized source with rotated order across three rounds: direct L17, BytePlane4+L17, and direct L19.

## Exact hosted result

| mode | archive bytes | median complete verified create | median process CPU | peak RSS |
|---|---:|---:|---:|---:|
| direct L17 | **6,210,959 B** | **2.530269465 s** | 2.636076556 s | 473,912 KiB |
| BytePlane4 + L17 | **6,134,444 B** | **2.723128948 s** | 2.828180556 s | 473,912 KiB |
| direct L19 | **6,135,703 B** | **6.120821358 s** | 6.226820995 s | 473,912 KiB |

Accepted v0.29 Analytics remains **6,135,172 B**.

The fixed candidate therefore:

- saves **76,515 B** versus direct L17;
- finishes **728 B smaller than accepted v0.29**;
- finishes **1,259 B smaller than the same-run direct L19 control**;
- is **55.5104% faster** in complete verified creation than direct L19;
- adds only **0.192859483 s** versus direct L17;
- preserves the same canonical user tree, deterministic archive size and unchanged measured peak RSS.

The transform stayed sparse and structural:

- 52 compression calls total;
- 50 cheap level-1 auditions;
- only **2** cheap winners;
- only **2** strong transform auditions;
- both strong transforms selected;
- transformed raw bytes: **700,416 B**;
- direct-L17 bytes for those selected payloads: **157,189 B**;
- transformed framed bytes: **80,674 B**;
- net payload saving: **76,515 B**;
- median cheap-gate CPU: **0.117276099 s**;
- median strong-transform CPU: **0.064725557 s**.

Verdict: **`LEVEL17_STRUCTURAL_CROSSOVER`**. Every preregistered gate passed.

## Interpretation

This is the first result in the current Analytics rehabilitation line that simultaneously beats the accepted v0.29 byte floor and removes a material majority of the direct-L19 creation cost without using workload identity, path/extension dispatch, a level sweep or a weaker comparator.

The causal mechanism is not “level 17 happens to be faster.” Direct L17 is too large by 75,787 B. The crossover comes from a sparse reversible representation transform that changes the entropy geometry of only two content-selected packs enough to make the lower-effort global regime competitive.

This also explains why the earlier skip-only line was boxed in. Instead of using earned margin to throw away expensive L19 work after the fact, BytePlane4 changes the representation so the whole ordinary-pack baseline can move to L17.

## Strongest self-critique / regression debt

The byte margin is only **728 B** against accepted v0.29. That is far too small to absorb casual metadata, proof, recovery or portability overhead. The result also inherits the CMPNX5 research representation; it does not by itself satisfy r25 canonical/native/recovery integration.

No release credit is granted for:

- canonical r25 serialization;
- authenticated product metadata/proof traffic beyond the research container;
- native reader/writer parity;
- hostile-resource bounds beyond the inherited research mechanism;
- cross-workload generalization;
- product-side opportunity selection or fallback economics.

A 728-byte lead should be treated as a scientific crossover, not a victory lap.

## Next decisive action

Freeze this exact mechanism and run a generator-distinct hostile transfer. The transfer must include structured fixed-width positives and false friends (random/incompressible and misleading 4-byte structure), preserve width=4 and level=17, and report both transformation-selection behavior and complete archive bytes/time against direct L17/L19 controls.

Do not test adjacent levels or BytePlane widths. If the fixed mechanism generalizes, the next step is a productization/economic gate that charges r25 metadata, integrity/recovery and reader/native work. If it does not generalize, preserve the Analytics seed as workload evidence and do not promote a corpus-specific selector.

The frozen ONE Genesis result and `research/cmpct1` remain unchanged.
