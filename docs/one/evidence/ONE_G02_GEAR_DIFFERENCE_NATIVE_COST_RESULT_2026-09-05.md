# ONE-G0.2 — Gear-difference fused native carrying-cost result

Date: 2026-09-05
Experimental line: ONE-G0.2
Decision: **retire Gear-difference as a direct unconditional compute repair**

## Exact evidence

- source: `fd763e0167708ab79e16d30c44627b9c3689b2f3`
- workflow: `33974574487`
- artifact: `9971962441`
- artifact digest: `sha256:5519ba0602fd68b22bde137557600dbbaacd33759d2c70df722aea0ce623a915`
- pre-result ONE semantic/hostile tests: pass
- raw-control witness mismatches: 0
- Gear-difference witness mismatches: 0
- modeled candidate discovery state: 280 B

## Result

The algebraic prefix-Gear difference is exact, but it does **not** remove enough native writer work to rehabilitate unconditional certificate carrying.

Five-large-control medians:

- Gear-difference / raw-word certificate: **0.9670513450x**
- Gear-difference / promoted observer baseline: **2.6594389275x**
- original product-facing <=1.12x gate recovered: **false**

The preregistered direct-repair stage required Gear/raw <=0.85x. It failed by a wide margin.

Per control:

| case | Gear/raw | Gear/baseline |
|---|---:|---:|
| random 1 MiB | 0.96705x | 2.65926x |
| compressed-like ~1 MiB | 0.97109x | 2.66724x |
| repeated 1 MiB | 0.97146x | 2.65944x |
| shifted/versioned 1 MiB | 0.96670x | 2.66455x |
| zeros 1 MiB | 0.84788x | 2.33609x |
| alternating hostile 1 MiB | 0.98167x | 2.71232x |
| random 4 KiB | 0.96752x | 2.94208x |
| random 64 B | 1.03125x | 2.08466x |

## Causal interpretation

This falsifies the attractive idea that removing the independent rolling raw-byte word would remove a major fraction of the exported native bill. On ordinary large data, the saving is only about 3% versus the already-rejected raw-word certificate.

Combined with the owner decomposition and the failed sorted-4 rehabilitation, the evidence is now stronger: **unconditional certificate construction is itself the wrong compute shape**. Its cost is distributed across phase event handling, token formation, and online witness maintenance; eliminating one local representation stage does not approach the required economics.

The zero-data row benefits more strongly (Gear/raw 0.8479x), but post-hoc weighting of that isolated case cannot rescue the general writer path.

## Hostile Reviewer

The Gear-difference algebra remains useful discovery knowledge: it proves a content-local witness can be derived exactly from observer state. This result only rejects using that algebra as a direct unconditional carrying-cost repair.

Do not respond by reducing phases/K on the same cohort. The structural phase geometry was frozen to cover hostile misses. Weakening it to make timing green would manufacture a win by spending coverage debt.

The independently preregistered unmixed Gear-difference native test remains valid because it removes another whole stage (`_mix64`) without changing phase/K geometry. However, even a local unmixed speedup must still face the original <=1.12x candidate/baseline authority.

## Next decisive action

Consume the unmixed native A/B. If it still remains materially above the original baseline gate, retire **unconditional rich-certificate carrying** as the immediate path and move to opportunity-gated activation / shared cheap falsification, where the rich certificate is built only after already-available observer evidence proves the cheaper shared-observer signal is insufficient.

No density, reader-speed, format, product, v0.29, or deferred-v0.30 claim follows.