# R39 — dynamic worker-pull whole-build result

Decision: **WHOLE_BUILD_DYNAMIC_PULL_TRANSFERS**.
Evidence head: `47c2a29bbe4915ff8a6c9223fefb9b83a1d672a5`.
Workflow run: `35219545619`; result-bearing job: `105196020141`.
Immutable artifact: `10495873612`; artifact digest `sha256:98ab4044ca4aaca2c7da190ce565d132f8fb9d0256bb6a81f73d561be0f8672e`.

The preregistered complete-build gate passed on both frozen targets with 9 alternating repetitions and complete archive-byte identity on every arm/repetition.

| target | baseline median | dynamic-pull median | ratio | median saved | archive bytes |
|---|---:|---:|---:|---:|---:|
| full-backups | 479.667 ms | 471.428 ms | 0.982823x | **8.239 ms** | 8,029,563 |
| nested-only | 404.589 ms | 398.880 ms | 0.985889x | **5.709 ms** | 2,177,164 |

Complete archive SHA-256 identity held:
- full-backups: `a4bb323deb9e15bbdecf61783b66aba37e0420d6e8d87b81fac724436d373d16`
- nested-only: `2b3e5fdd97d137475a259b9ae9347b75b2ffa2c905239df5dd78e3e42ed5dd2d`

## Interpretation

R38's candidate-encoding gain survives the complete `Builder.build()` boundary. The effect is smaller after dilution by scan/dictionary/materialization/write work, but it remains positive on both preregistered targets and clears the frozen >=2 ms threshold.

This is still research evidence, not product/release credit. It authorizes the minimal product implementation of the same execution architecture, followed by differently rooted archive-identity tests and whole-system CPU/RSS/I/O + canonical runtime-matrix validation. The product patch must not alter codecs, admission, candidate ordering, worker count, archive layout, release thresholds, or benchmark semantics.

Strongest caveat: the full-build gain is ~1.7% on full-backups and ~1.4% on nested-only. That is real under this frozen A/B, but small enough that broader workloads/noise may erase it. Productization is justified as a causal work-elimination candidate, not yet as a release-gate victory.
