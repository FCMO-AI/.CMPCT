# r25 outer product-scheduling RSS result

Status: **ACCEPTED SCOPED FORGE NEGATIVE / NO RELEASE CREDIT**

This record preserves the result-bearing execution of the frozen A/B in
`docs/v030-rnd/R25_OUTER_PRODUCT_SCHEDULING_RSS_PREREG.md`. The preregistration and result-bearing
instrument are immutable after this execution. This document records the measured result and its
predeclared interpretation only; it does not alter the tested question, thresholds, product bytes,
selector, archive grammar, integrity, recovery, locality/decode-unit limits, or release state.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`
- exact experiment source head: `a9606df421f41dd00d9a71869ada9ad943276fda`
- workflow: `CMPCT v0.30 outer product scheduling RSS A/B`
- workflow run: `33602618399`
- substantive job: `100160154416` (`outer-product-scheduling-rss`)
- evidence artifact id: `9836032220`
- evidence artifact: `v030-r25-outer-product-scheduling-rss-a9606df421f41dd00d9a71869ada9ad943276fda`
- artifact ZIP sha256: `7b119d703d631fb731f458d326ce37bf32191f1b60a50698d393c2e9e089fd7f`
- schema: `cmpct-v030-r25-outer-product-scheduling-rss-v1`
- `experiment_valid`: **true**
- `release_credit`: **false**

The substantive fresh-process job completed successfully and its fail-closed ratchet proved the
serialized arm intercepted exactly one `cmpct-v030-product` executor construction and exactly two outer
submissions. The earlier release-product r24 prebuild optimization and the entire inner r25 scheduling
graph remained untouched. Paired arms produced identical selected complete product bytes, archive
SHA-256, canonical filesystem tree, selected representation, format revision, and both priced
r24/r25 complete-artifact sizes.

## Exact result

Frozen target: `resemblance_hostile_v1 / 01_shifted_versions`.

| arm | median total fresh-process peak RSS | median wall time |
|---|---:|---:|
| inherited concurrent genuine-r24 vs complete-r25 product race | **398,446 KiB** | **58.6160 s** |
| serialized outer genuine-r24 then complete-r25 product race | **358,656 KiB** | **59.4646 s** |

Derived result:

- peak-RSS reduction from outer serialization: **9.9863%**;
- absolute median peak reduction: **39,790 KiB**;
- serialized wall ratio: **1.01448x** — about **1.45% slower**;
- exact selected complete product identity: unchanged across paired arms;
- exact r24/r25 complete-product pricing: unchanged across paired arms;
- intervention/worker failures: none.

The frozen decision rule was explicit: >=20% peak-RSS reduction supports outer r24-vs-r25 lifetime
overlap as a material owner; <10% retires it as the primary explanation; 10–20% is ambiguous. The
measured **9.9863%** reduction is below the frozen 10% boundary. It is close to that boundary, but the
predeclared rule is authoritative and must not be rounded or reinterpreted after observing the result.

## Scoped negative constraint

**Retire the outer genuine-r24-vs-complete-r25 concurrency as the primary explanation for the current
Shifted r25 product RSS red under this exact tested regime.**

Outer overlap is not free: removing it lowered the measured median peak by about 38.9 MiB. But the full
Shifted product remains far above the release RSS budget, and the preregistered causal hurdle required a
material >=20% collapse before scheduling could be treated as the principal owner. The measured change
is only about half that hurdle and also exports a small wall-time cost.

Do not ship outer serialization merely because it lowers one diagnostic RSS number. It does not satisfy
the frozen causal criterion, does not satisfy the release RSS gate, and does not earn release credit.

## Causal interpretation

The causal chain now excludes two tempting scheduling explanations as primary owners:

1. v3 showed that serializing the inner shipping G0-G4/PrefixGraph overlap **increased** peak RSS and
   wall time; and
2. this experiment shows that serializing the outer genuine-r24/complete-r25 race removes only about
   **9.99%** of peak RSS, below the frozen primary-ownership boundary.

Combined with the earlier product-phase and exact semantic-owner evidence, the dominant unresolved
memory debt therefore lies deeper in **retained common/product state and temporary-output lifetime**
inside complete r25 construction, not in either tested executor overlap alone.

The next Forge question should isolate large retained state that survives across candidate/build phases:
source/profile materialization, complete candidate byte buffers, verification/accounting objects,
canonical wrapping, or other product-owned temporaries. Prefer an ownership/lifetime instrument that
can attribute a concrete >=release-gap-sized allocation class rather than another scheduler permutation.

## Reopening predicate

Reopen outer r24-vs-r25 concurrency as the primary Shifted RSS hypothesis only if new causal evidence
shows one of:

1. outer product scheduling/lifetime topology materially changes;
2. a heap/ownership instrument proves this overlap retains a specific allocation class large enough to
   explain the current product red and eliminating it materially lowers total fresh-process peak RSS; or
3. a newly frozen A/B on a materially changed product crosses the >=20% reduction boundary while
   preserving exact complete-product identity and all release invariants.

Runner noise, baseline-subtracted `ru_maxrss`, rounding 9.9863% to 10%, or changing the threshold after
the fact is not a reopening predicate.

## Forge decision

Advance one causal layer deeper to **retained common/product-state lifetime attribution**. Preserve the
proven r25 byte gains and every release invariant. Do not change production scheduling from this result.
The next instrument should distinguish concrete retained-state classes before a Builder intervention;
if no class is large enough to explain the red, preserve that negative evidence and continue the
ownership decomposition rather than weakening the RSS gate or tuning away the compression gain.
