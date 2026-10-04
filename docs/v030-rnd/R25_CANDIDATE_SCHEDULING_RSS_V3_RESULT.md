# r25 candidate-scheduling RSS v3 result

Status: **ACCEPTED SCOPED FORGE NEGATIVE / NO RELEASE CREDIT**

This record preserves the result-bearing execution of the frozen v3 scheduling A/B defined by
`docs/v030-rnd/R25_CANDIDATE_SCHEDULING_RSS_V3_PREREG.md`. The preregistration and result-bearing
instrument remain immutable. This document records the result and its allowed interpretation; it does
not modify the frozen question, thresholds, candidate set, selector, archive grammar, integrity,
recovery, locality/decode-unit limits, or release state.

## Authority

- authoritative branch: `agent/v030-authoritative-integration`
- exact source head: `e11529a250fec95908062a239e34563664048c47`
- workflow: `CMPCT v0.30 candidate scheduling RSS A/B v3`
- workflow run: `33599187748`
- substantive job: `100149031315` (`candidate-scheduling-rss-v3`)
- evidence artifact id: `9834873357`
- evidence artifact: `v030-r25-candidate-scheduling-rss-v3-e11529a250fec95908062a239e34563664048c47`
- artifact ZIP sha256: `0f4d4d006e9719d9e5735e8df92005fb70ced24311cd3ae18c0de1dbea8e430b`
- schema: `cmpct-v030-r25-candidate-scheduling-rss-v3`
- `experiment_valid`: **true**
- `release_credit`: **false**

The substantive job executed the frozen fresh-process A/B; this authority is not a classifier-only
success. The v3 intervention ratchet proved that the serialized arm intercepted exactly the intended
`cmpct-v030-prefixgraph` executor construction/submission while leaving unrelated executors delegated.
Both arms retained exact canonical semantic-owner identity and emitted byte-identical selected product
artifacts with the same verified canonical filesystem tree.

## Exact result

Frozen target: `resemblance_hostile_v1 / 01_shifted_versions`.

| arm | median total fresh-process peak RSS | median wall time |
|---|---:|---:|
| inherited concurrent inner G0-G4 / PrefixGraph scheduling | **399,398 KiB** | **57.3492 s** |
| serialized exact inner G0-G4 / PrefixGraph scheduling | **421,254 KiB** | **65.3971 s** |

Derived result:

- serialized peak-RSS reduction: **-5.4722%** — serialization increased peak RSS by **21,856 KiB**;
- serialized wall ratio: **1.1403x** — serialization increased median wall time by about **14.03%**;
- selected representation: PrefixGraph in both arms and repetitions;
- selected complete product bytes/SHA/tree: identical across paired arms;
- worker/intervention failures: none.

The preregistered decision rule was: >=20% RSS reduction supports inner concurrency/lifetime ownership;
<10% retires it as the primary explanation; 10–20% is ambiguous. The measured reduction is negative,
well inside the retirement region.

## Scoped negative constraint

**Retire the shipping G0-G4-vs-PrefixGraph inner candidate concurrency as the primary explanation for
the Shifted r25 product RSS red under this exact tested regime.**

The result does not say concurrency can never consume memory and does not prove serialized scheduling
is universally worse. It says the only shipping inner overlap changed by this A/B fails the frozen
causal hurdle: removing that overlap did not collapse the product high-water mark and instead made both
RSS and wall time worse on the exact frozen target while preserving product bytes.

Do not spend further Forge cycles serializing, retiming, or threshold-tuning this inner overlap merely
because the shipping product selects PrefixGraph. V2 semantic-owner evidence already showed that exact
G0-G4 and exact PrefixGraph in isolation each peak far below the complete product; v3 now shows that
serializing their shipping overlap does not explain the missing high-water memory.

## Causal interpretation

The unresolved ownership boundary moves one level outward. The canonical product builder itself starts
**genuine r24 construction and the complete r25 tournament concurrently** under the
`cmpct-v030-product` executor before comparing their complete physical artifact sizes. That outer
product-floor overlap is materially different from the retired inner G0-G4/PrefixGraph overlap: it can
keep a complete genuine-r24 build and the entire r25 construction graph live in the same process.

The next causal experiment should therefore isolate that exact outer product lifetime boundary before
changing shipping scheduling or representation internals.

## Reopening predicate

Reopen inner G0-G4/PrefixGraph scheduling as the primary Shifted RSS hypothesis only if new causal
evidence shows one of:

1. the exact shipping semantic-owner implementations or their lifetime topology materially change;
2. a heap/lifetime instrument proves the inner overlap retains a specific allocation class large enough
   to explain the product red and removing that ownership lowers total fresh-process peak RSS; or
3. an independently frozen A/B on a materially changed product shows >=20% total peak-RSS reduction
   from changing that same inner overlap while preserving exact product identity.

Runner noise, baseline-subtracted `ru_maxrss`, or a different scheduling threshold is not a reopening
predicate.

## Forge decision

Advance from inner-candidate scheduling to **outer genuine-r24-vs-r25 product lifetime attribution**.
Preserve the byte gain and every frozen release invariant. The next A/B must change only the outer
`cmpct-v030-product` scheduling seam, leave the inherited inner r25 tournament untouched, require exact
selected archive bytes/SHA/tree parity, charge total fresh-process peak RSS and wall time, and grant no
release credit by itself.
