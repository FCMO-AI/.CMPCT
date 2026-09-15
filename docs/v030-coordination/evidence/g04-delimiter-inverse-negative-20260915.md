# v0.30 G04 delimiter-inverse negative — 2026-09-15

Authority base: `agent/v030-authoritative-integration` @ `f264926994c4b473ac28bbfda48cffa5f7b24421`.
Research exact head: `bf1cba9106568e3dfa22db62a6072aa670cf980f`.
Workflow run: `35034826327`; artifact: `v030-g04-delimiter-inverse-ab-bf1cba9106568e3dfa22db62a6072aa670cf980f`.

The pre-existing exact-archive A/B in `experiments/v030_g04_delimiter_inverse_ab.py` was deliberately executed against canonical `neutral_hostile_v1/09_ml_artifacts`. It required nested G04 selection, strong archive verification, nine alternating control/candidate extractions, exact source-tree identity after every extraction, and six property cases.

Direct result:
- control median: `0.16170011799999884 s`
- candidate median: `0.2428096749999895 s`
- candidate/control: `1.5016048102079385x`
- speedup fraction: `-0.5016048102079385`
- promotion signal: `false`
- release credit: `false`

Decision: **retire the banded Python delimiter-inverse candidate for the current ML runtime debt.** It misses the inherited `minimum_speedup_fraction = 0.15` floor in the wrong direction by a large margin (~50.2% slower). Do not lower the floor, productize this implementation, or treat the green research workflow as product evidence.

Scope: this falsifies this implementation strategy, not the broader claim that G04/Geometry decode owns material ML extraction time. The next action should use the existing shipping extraction ownership profile to select a differently rooted optimization or measure a narrower phase boundary. No release threshold, archive byte, format, workload, or public claim changed.
