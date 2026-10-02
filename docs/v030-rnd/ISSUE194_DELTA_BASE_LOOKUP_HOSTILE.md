# Issue #194 reusable delta-base index — lookup hostile correction

Status: **research evidence / decision-changing correction / no product or release credit**

Authority checked: `agent/v030-authoritative-integration@496c96b40e09b6cd9a4eb81af2ec52db1caed354`.

Existing implementation owner: `agent/phased2-issue194-delta-index-reuse@ad74e628c4197bb1274a481d9c08daffc7a0c0fa`.

Earlier validation branch: `agent/phased3-issue194-delta-index-validation@ba7e4c4315bbca9fed0d019d8a19f27900b70d17`.

## Correction

The earlier local oracle correctly identified repeated weak-index construction as duplicated work, but it timed index construction separately. Charging the complete rolling target-scan loop exposes a representation-level regression in the packed sorted-array lookup used by `delta_encode_prepared`.

The scientific win is **base-owned index reuse**, not the packed lookup representation.

## Held-out complete delta-audition courts

All timings below are local lower-rung research evidence. Payload/stat semantics were checked against the historical encoder.

| workload | edges | bases | historical rebuild/edge | packed prepare/reuse | historical dict grouped/reuse |
| --- | ---: | ---: | ---: | ---: | ---: |
| Shifted Versions | 972 | 80 | 28.5108 s | 17.6661 s | **17.1527 s** |
| Boundary Churn | 180 | 25 | 7.6096 s | 4.9197 s | **4.7981 s** |
| False Neighbors | 15 | 5 | **0.5550 s** | 1.2518 s | **0.5235 s** |

The decisive hostile is False Neighbors: packed prepared lookup is about **2.25x** historical wall even though it avoids repeated index construction.

Cause: the historical encoder uses an amortized O(1) `dict.get(weak_key)` at every rolling target position. The packed representation uses `bisect_left/bisect_right`, making every miss O(log n). False-neighbor scans deliberately create many lookup misses, so exported lookup CPU dominates the saved construction work.

Incompressible hostile has zero LSH candidate edges and therefore no delta-index exposure.

## Surviving route

Preserve the historical weak-key -> ordered-offset dictionary and change **ownership only**:

1. group candidate auditions by immutable base;
2. build the historical dictionary once for that base;
3. audit every target for the base with unchanged first-offset/tie semantics;
4. release the dictionary before the next base.

This retains O(1)-amortized target lookup and avoids retaining all base indexes simultaneously. Local Shifted accounting puts the largest one-base historical dictionary around the same bounded ownership class as one current per-edge index, whereas retaining every base dictionary at once would be unjustified.

A randomized permutation control found no `choose_central_bases` assignment change when measured candidate-row order changed, because that function re-groups and deterministically sorts its inputs. Final integrated archive identity is still required before product credit.

## Current v0.30 relevance

The discovery-neutral v0.30 attempt-5 worker disables position-independent candidate discovery while it builds the current attempt-5 substrate. v0.28 and the current attempt-5 Placement path therefore both pay the inherited LSH/delta audition family. Per-base historical-dict ownership is a low-complexity way to reduce duplicated work inside each child without adding cross-process payload ownership or IPC semantics.

Exact neutral ML remains a hard negative for this mechanism: current v0.28 topology has 114 nodes and **0 LSH candidate edges**. Delta-base reuse must not be used to explain ML's multi-second substrate wall.

## Promotion boundary

Before any productization claim, run one hosted integrated A/B that includes at least Shifted, Boundary Churn and False Neighbors and preserves:

- exact candidate/final archive bytes and tree identity;
- inherited candidate discovery and central-base selection;
- child wall and CPU;
- peak RSS / index ownership;
- complete-product create wall;
- all existing resource and locality bounds.

If the grouped historical-dict route loses on a held-out target-scan hostile, or exported memory erases the wall benefit, retire this implementation family.

No release threshold, comparator, format, reader, admission law or benchmark workload changes.
