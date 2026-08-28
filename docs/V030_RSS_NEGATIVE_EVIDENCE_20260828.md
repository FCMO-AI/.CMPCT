# v0.30 RSS negative evidence — 2026-08-28

This decision record preserves exact-head experiments that must not be rediscovered as speculative production changes.
It grants no release credit and changes no selector, format, integrity, locality, recovery, or performance threshold.

## r25 candidate-overlap serialization is not the Shifted RSS owner

Exact candidate head: `40896636401a8c139f328b52669755f7773fc7ad`

Workflow run: `33198035046` (`CMPCT v0.30 r25 candidate-overlap RSS oracle`)

The A/B ran shipping candidate construction against an otherwise identical serialization of the r25 candidate boundary in fresh processes. Archive SHA-256, archive bytes, tree SHA-256, candidate admission, candidate-internal parallelism, grammar, integrity, locality, decode-unit and recovery semantics were required to remain identical.

Observed medians:

| target | serial/shipping wall ratio | serial/shipping RSS ratio | RSS reduction |
| --- | ---: | ---: | ---: |
| `resemblance_hostile_v1/01_shifted_versions` | 1.068291 | 1.002280 | -0.2280% |
| `neutral_hostile_v1/09_ml_artifacts` | 0.983313 | 0.994314 | +0.5686% |

`promotion_signal=false`.

Decision: do **not** serialize the r25 candidate boundary as an RSS fix. It slightly worsened Shifted RSS and moved ML RSS by less than 1%. Combined with the separately falsified PrefixGraph worker-count and r24-prebuild-overlap hypotheses, the remaining Shifted excess should be sought inside full-product/per-candidate materialization or source/payload lifetime rather than scheduler overlap.

The CI artifact was exact-head bound and uploaded as `v030-r25-candidate-overlap-rss-40896636401a8c139f328b52669755f7773fc7ad` with artifact ZIP SHA-256 `3b4159b867dca952b25519286c59dd2f5dace2a8e904051ac75a5ed8d55c4539`.
