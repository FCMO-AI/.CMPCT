# ONE-G0.2 numeric morphology gate preregistration — 2026-09-07

## Mission lock

Repository authority identifies deployed ASCII-numeric roots as a measured red for generic fused observation: the generic fused observer can add writer cost where the older path already avoids the redundant stride scan. This experiment attacks that red without adding any reader-visible mechanism.

Activation T0 was recorded as 2026-09-07T17:09:12-06:00.

## Hypothesis

A bounded, content-derived morphology gate can skip reuse-fingerprint discovery on sufficiently large, strongly numeric ASCII roots **only when bounded evidence distributed across the root is also highly diverse**, reducing observation wall/CPU time while preserving run opportunities and avoiding numeric regions where repetitive material contains useful reuse Laws.

The candidate is writer-side discovery policy. ONE bytes, Law + Surprise semantics, reader execution, locality, integrity and recovery contracts are unchanged.

## Builder

`experiments/one/morphology_gate.py` adds:

- a classifier reading at most 4096 bytes total, distributed across eight deterministic windows of the root;
- a minimum input size of 16 KiB so tiny roots do not pay a hard-to-amortize gate;
- >=98.5% membership in a deliberately narrow numeric/delimiter alphabet;
- >=35% ASCII digit density;
- >=90% exact uniqueness across sampled 64-byte chunks;
- a run-only one-pass observer when all gates pass;
- exact delegation to the existing generic observer when any gate fails.

The distributed sample reads are charged as source traffic. Gated observation retains run discovery but intentionally emits no reuse opportunities.

## Hostile reviewer corrections before result authority

The first candidate gated on numeric morphology alone. Review rejected it before benchmarking: repetitive numeric tables can be highly compressible by reuse, so morphology alone could destroy valuable discovery while appearing fast. The gate was tightened to require high sampled chunk diversity.

A second review found that a contiguous prefix remained too easy to fool: a diverse numeric header followed by a large repetitive numeric body would satisfy a prefix-only gate while hiding substantial reuse. Before any completed scientific workflow result, the classifier was changed to stratify the same 4096-byte budget across eight deterministic root windows. A hostile phase-shift root now requires fall-through and exact equality with generic observation.

This is still sampling, not a proof of global absence of reuse; adversarial structure can evade deterministic windows. The full generic reuse-opportunity fraction on the benchmarked gated roots therefore remains an independent disproof criterion, and any production promotion must measure final stored bytes rather than treating the heuristic as density-safe by construction.

## Frozen falsifier

`benchmarks/one/one_g02_numeric_morphology_gate.py` uses 256 KiB and 1 MiB roots, 15 paired alternating repetitions, and four families:

1. diverse numeric ASCII — must gate;
2. repetitive numeric ASCII — must not gate;
3. diverse-prefix / repetitive-tail numeric phase shift — must not gate;
4. binary control — must not gate.

Promotion gates are frozen before hosted result authority:

- diverse numeric wall ratio <= 0.90 versus generic observe;
- diverse numeric process-CPU ratio <= 0.90;
- generic observer reuse opportunity bytes on a gated root must be <=2% of source bytes, otherwise the morphology heuristic is discarding too much potential Law evidence and fails regardless of speed;
- fall-through families must remain <=1.08 wall and CPU;
- all run opportunities must match generic observe exactly;
- every ungated observation must equal generic observe exactly.

No threshold may move after observing CI output to manufacture a pass.

## Disproof / retirement conditions

Reform or retire this gate if any of the following occurs:

- diverse numeric roots fail to achieve the preregistered 10% wall and CPU reduction;
- a gated root hides >2% source bytes of generic reuse opportunity;
- repetitive numeric, phase-shift numeric, or binary controls false-gate;
- fall-through overhead exceeds 8%;
- run opportunities diverge;
- the bounded classifier becomes a material extra memory/source-traffic owner in whole-writer profiling;
- end-to-end density later regresses materially even when observation-level skipped reuse remains below 2%.

A component pass is not a Genesis scoreboard win. If positive, this gate still has to earn value in the complete writer envelope and at the 2026-09-11 same-input comparator gate.
