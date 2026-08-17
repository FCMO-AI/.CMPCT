# CMPCT v0.30 PrefixGraph evidence

Status: **green mechanism oracle; research-only; canonical r24 unchanged**.

This document records the first independent CI result that satisfied the preregistered PrefixGraph causal
contract.  It is evidence to preserve the mechanism and proceed to composition work; it is **not** a v0.30
release claim.

## Authoritative run

- workflow: `CMPCT v0.30 PrefixGraph oracle`
- workflow run: `32068291053`
- source commit: `ec6a3b90c43320eea41cfcd0af18bc968b7908cf`
- result: `success`
- uploaded artifact id: `9301626133`
- artifact digest: `sha256:caca578f85e49e4d9300c104e1fed1a1ecc073420b3751843265f386a6ac2bb2`
- preserved exact JSON: `benchmarks/history/2026-08-17-v030-prefixgraph-oracle-v1.json`

The CI job independently completed focused PrefixGraph tests, exact historical control regeneration, the frozen
contract enforcement, the public-surface guard and evidence upload.

## Exact result

| workload | accepted v0.29 | PrefixGraph | saving | prefix records | depth |
|---|---:|---:|---:|---:|---:|
| `01_shifted_versions` | 1,723,056 B | 1,700,242 B | **22,814 B** | 17 | 1 |
| `03_boundary_churn` | 79,876 B | 75,480 B | **4,396 B** | 11 | 1 |
| **total** | **1,802,932 B** | **1,775,722 B** | **27,210 B** | — | **1** |

Frozen gate:

- aggregate minimum: 24,576 B → **passed by 2,634 B**;
- per-workload minimum: 2,048 B → minimum observed **4,396 B**;
- workloads improved: **2/2**;
- workloads regressed: **0**;
- maximum dependency depth: **1**;
- mechanism gate: **true**.

Both regenerated source trees matched their accepted v0.29 SHA-256 identities exactly, and the rebuilt v0.29
archive byte counts matched accepted history before any candidate saving was credited.

## Timing observation, not release performance claim

The focused standalone PrefixGraph writer measured 9.241 s on shifted versions and 3.191 s on boundary churn,
while rebuilding the accepted v0.29 portfolio controls took 84.875 s and 60.816 s respectively in the same
workflow.  These numbers are useful evidence that the mechanism itself is not inherently expensive, but they
are **not** a release-level creation-speed comparison: v0.30 composition, full 15-workload timing, memory,
extraction and selection costs remain unmeasured.

## What this proves

It proves a real orthogonal source of savings exists: a directly stored sibling can serve as raw Zstandard
history for another version-family member, with complete serialized artifact accounting and bounded depth 1.
The gain survived immutable historical controls rather than only a favorable local fixture.

It does **not** prove that 27,210 B can simply be added to Geometry savings.  Geometry and PrefixGraph must be
composed and ablated in one artifact because transform selection, graph structure, metadata and fallback can
interact.

## Promotion debt

1. Integrate PrefixGraph as an authenticated edge inside the accepted graph/compiler rather than promote the
   standalone `CMPNXP1` oracle grammar.
2. Compose it with CMPNX14 Geometry IR and measure `Geometry only`, `PrefixGraph only`, `combined`, and exact
   v0.29 fallback on the same source identities.
3. Enforce per-member locality <=8x; weighted-average locality is insufficient.
4. Harden malformed anchor/base ids, physical spans, prefix-reference integrity and recovery paths.
5. Prove native/shared-reader parity and deterministic golden vectors.
6. Run the complete repaired 15-workload generalization matrix, creation/extraction/selective-read/memory
   measurements and external format frontier before any v0.30 promotion.

Footnote: the earlier local estimate was roughly 27.7 KiB.  The durable number is the CI artifact above:
**27,210 B**.  Research prose and future composition work must use the durable value rather than the preliminary
estimate.
