# ONE-G0.2 — unmixed Gear-difference native carrying-cost result

Date: 2026-09-05
Experimental line: ONE-G0.2
Decision: **retire unmixed native repair; retire unconditional rich-certificate carrying as the immediate path**

## Exact evidence

- source: `1b5b349b1fec8f93b82cb6020badf53dae0cb8ef`
- workflow: `33974743723`
- artifact: `9972004214`
- artifact digest: `sha256:dfe0c2582a58393c302059cc78100ec1ff081dda74eec8251cdcd66bf0fd62d2`
- pre-result ONE semantic/hostile tests: pass
- mixed witness mismatches: 0
- unmixed witness mismatches: 0
- modeled state: 280 B

## Result

Removing `_mix64` preserved exact candidate-reference witnesses but did not meet the frozen 10% native stage gate.

Five-large-control medians:

- unmixed / mixed Gear-difference: **0.9735479914x**
- unmixed / promoted observer baseline: **2.5907659685x**
- original product-facing <=1.12x gate recovered: **false**

Per control:

| case | unmixed/mixed | unmixed/raw | unmixed/baseline |
|---|---:|---:|---:|
| random 1 MiB | 0.97355x | 0.93123x | 2.59564x |
| compressed-like ~1 MiB | 0.95998x | 0.92068x | 2.54687x |
| repeated 1 MiB | 0.97637x | 0.93404x | 2.59334x |
| shifted/versioned 1 MiB | 0.97453x | 0.93058x | 2.59077x |
| zeros 1 MiB | 0.94860x | 0.79954x | 2.20230x |
| alternating hostile 1 MiB | 0.97905x | 0.94466x | 2.65576x |
| random 4 KiB | 0.96264x | 0.92780x | 2.84760x |
| random 64 B | 1.08101x | 1.06359x | 2.91961x |

## Causal conclusion

The hot-loop debt is no longer plausibly recoverable by another local certificate spelling. Three increasingly mechanism-level attempts are now exact negatives for unconditional carrying:

1. selector-only sorted-4: five-large median 1.0124x vs heap control;
2. prefix-Gear difference: 0.9671x vs rejected raw certificate, still 2.6594x baseline;
3. unmixed prefix-Gear difference: 0.9735x vs mixed Gear difference, still 2.5908x baseline.

Together with the original 2.7600x raw-fused result, this is strong evidence that **paying rich relation-certificate work on every observed root is the wrong compute architecture**. The structural certificate remains useful, but it should become cold/opportunity-gated discovery rather than permanent hot-loop state.

## Hostile Reviewer

The unmixed result is not useless: relative to the original raw certificate it reaches roughly 0.92–0.94x on ordinary large controls and 0.80x on zeros. But the absolute baseline authority dominates. A writer path at ~2.59x the promoted observer cannot be promoted by celebrating its improvement over another rejected path.

Do not reduce phase count/K on this frozen cohort. Do not try another selector micro-spelling. Those routes are now explicitly retired unless new causal evidence changes the work architecture.

## Next decisive action

Move to **opportunity-gated relation discovery**. First consume/replay the already-frozen sparse exact-shift gate, which tests whether a candidate pair can be cheaply falsified before full proof. If that gate is viable, combine it with pair contexts that are already known cheaply (especially temporal/version adjacency), reserving the rich content-local certificate for cases where cheap pair context/shared observer evidence is absent or demonstrably insufficient.

The rich certificate can still teach ONE what predictive relation exists; it simply must not tax every byte unconditionally.

No density, reader-speed, format, product, v0.29, or deferred-v0.30 claim follows.