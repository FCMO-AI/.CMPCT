# ONE-G0.2 observer-run -> Fill Law result — 2026-09-08

## Authority

- Source SHA: `bf676f0615de0e38ffe60911bf97d667029da8c2`
- Workflow run: `34269270943`
- Job: `102206437439` (`small-vector-observer`)
- Artifact: `one-g02-observer-evidence-bf676f0615de0e38ffe60911bf97d667029da8c2`
- Artifact ID: `10073217177`
- Artifact ZIP SHA-256: `94b1b4ad5d336ec15a029f56c41c337f47a57882cf4906acf980e94a64d34264`
- Experimental version: ONE-G0.2

The exact-source lane checked out and bound the source SHA, passed all 16 semantic/adjudication tests, completed the frozen small-vector observer falsifier, completed the frozen run-Fill benchmark, and preserved both JSON outputs. The workflow conclusion is `failure` only because the run-Fill executable deliberately exits non-zero for a non-ADVANCE decision.

## Result A — small-vector observer

Decision: **`ADVANCE_SMALL_VECTOR_OBSERVER`**.

This is writer-internal handoff evidence only. It does not change stored ONE bytes, reader semantics, durability, recovery, portability, or comparator authority.

At 1 MiB the structured row reduced median wall time from 23.635377 ms to 7.860800 ms (`0.332586x`) and median CPU to `0.332747x`. The same row contained 12,288 native opportunities and retained 294,912 useful observer bytes from 3,539,040 bytes of reserved capacity.

The 1 MiB controls stayed close to neutral: compressed-like `0.996822x` wall, random `0.994906x`, near-repeats `0.997499x`; long-runs was `1.011115x`, inside the frozen `1.05x` no-regression bound.

Interpretation: compact/small-vector observer handoff is now supported as the preferred writer-internal shape. This does not rehabilitate the older positional observation cache.

## Result B — observer-run -> generic Fill/Concat compiler

Decision: **`HOLD_OBSERVER_RUN_FILL_LAW`** (not INVALIDATE).

The compiler is semantically exact and uses only the existing `surprise`, `fill`, and `concat` grammar. Its predictive principle is promising, but this direct graph shape violates the frozen access/work and timing contract.

### 1 MiB decisive rows

| family | wire ratio | wall ratio | CPU ratio | reader-work ratio | notes |
| --- | ---: | ---: | ---: | ---: | --- |
| structured | 0.875018 | 0.979613 | 0.979630 | **1.333333** | one 262,144-byte Fill |
| compressed-like | 1.000000 | 0.967354 | 0.966854 | 1.000000 | no qualifying runs |
| long-runs | **0.501019** | **1.110941** | **1.111013** | **1.333333** | 220 Fill spans |
| random | 1.000000 | 1.019822 | 1.019831 | 1.000000 | no qualifying runs |
| near-repeats | 1.000000 | 1.039541 | 1.038743 | 1.000000 | one observed run, none qualifying |

The 1 MiB long-runs row eliminates 1,046,499 wire bytes while adding about 0.935 ms wall / 0.936 ms CPU, or roughly 1.119 MB of wire eliminated per added wall millisecond. Density therefore passes the intended `<=0.55x` gate, but creation narrowly misses the `<=1.10x` run-rich gate and reader work misses decisively.

The same locality/work failure appears on every row that actually uses Fill: candidate/control reader work is exactly `4/3`. The 64 KiB long-runs row also exposes the fixed/per-run creation cost more strongly (`1.194714x` wall, `1.195194x` CPU).

## Causal diagnosis

The reference evaluator charges each terminal Fill/Surprise node for materialization, then `concat` charges another read of every child plus a full output write, then the root range and root SHA are charged. A literal current root does not pay that intermediate child->concat pass. Consequently the present Fill+Concat graph shape makes useful Law structure pay an avoidable extra full-current-root pass.

This is not evidence that constant-run Law is intrinsically bad. It is evidence that compiling a useful Law into separately materialized terminal nodes and then reconstructing them through a generic materializing `concat` is the wrong execution shape for ONE's access/work contract.

## Referee / next hypothesis

**Hypothesis:** terminal `surprise`/`fill` pieces under a current-root `concat` can be reconstructed through a bounded root sink in one output pass, preserving exactly the same Program/wire semantics while eliminating the extra child-materialization/concat-copy work that caused the `4/3` reader-work ratio.

**Disproof:** on the frozen filled rows, an independent fused evaluator must reproduce the reference evaluator's exact current/previous bytes and root SHA-256 values, stay within unchanged depth/node/output/work bounds, and reduce measured reconstruction traffic without increasing selective-read amplification or hiding work in uncharged preprocessing. If it cannot bring filled-row reader work to `<=1.05x` of the literal control, the direct run-Fill compiler remains HOLD regardless of its density win.

The first experiment should be an execution-level rehabilitation of the *same* stored graph, not a new opcode and not a reader-visible run codec. Only after semantic vectors prove equivalence should a native bulk sink be considered.

## Claim boundary

No Genesis supersession point is claimed. v0.29 and deferred v0.30 remain frozen comparators. This result neither weakens locality/integrity/resource requirements nor authorizes a format change.