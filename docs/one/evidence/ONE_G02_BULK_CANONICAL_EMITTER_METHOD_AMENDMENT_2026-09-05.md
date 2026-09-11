# ONE-G0.2 bulk canonical emitter — timing-method amendment

Date: 2026-09-05
Experimental line: ONE-G0.2
Parent preregistration: `docs/one/evidence/ONE_G02_BULK_CANONICAL_EMITTER_PREREG_2026-09-05.md`

## Hostile-review finding before result authority

Before consuming any result-bearing bulk-emitter timing as authority, hostile review identified one avoidable measurement asymmetry in the first benchmark implementation: each row measured the baseline path first and the candidate path second. Repeated medians reduce noise, but fixed ordering can still export warm-cache, interpreter, frequency or thermal effects systematically into one side.

## Frozen correction

Only the timing schedule changes. Each row still uses the exact same Program, corpus, 51 rounds, semantics, byte equality checks, controls and promotion thresholds frozen in the parent preregistration. Timed calls are now paired with alternating order:

- even pair: baseline A, candidate B;
- odd pair: candidate B, baseline A.

Both paths execute while the duplicate validation call is suppressed for the pair, exactly as in the parent cost-owner experiment, so the measurement remains prevalidated canonical emission versus prevalidated canonical emission. The public bulk-emitter entrypoint still validates normally.

No workload, threshold, size, round count, representation, byte contract or decision law changes. Any earlier fixed-order run that completes is method-development evidence only and is superseded for promotion authority by the alternating-order exact-head run.