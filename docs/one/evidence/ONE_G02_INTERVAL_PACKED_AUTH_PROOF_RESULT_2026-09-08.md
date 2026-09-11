# ONE-G0.2 interval packed authenticated-range proof — exact-source result

Date: 2026-09-08
Experimental version: `ONE-G0.2`
Source branch: `research/cmpct1`
Exact result-bearing source: `740ba74b331567eee4e547f50201824fb9f532da`
Frozen comparators remain: v0.29 `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`; deferred v0.30 `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

## Mission lock

The prior direct packed proof path was a legitimate HOLD because its generic per-level `selected`/`needed` Python set construction produced small-read regressions. This rehabilitation attempt preserved exactly the same RangeProof/integrity semantics but exploited the fact that a requested byte range selects a contiguous leaf interval. Only interval boundaries can introduce proof siblings, so no per-level selected/needed sets are required.

No size gate, post-hoc fallback, leaf threshold, authentication grammar, proof format or reader-visible semantic changed.

## Pre-result falsifier repairs

Hostile review found and repaired two benchmark defects before this source became admissible:

1. the previous arm's `RangeProof` could be destroyed inside the next arm's timing window; owning references are now cleared before either wall or CPU clock starts;
2. the adjudicator checked matrix cardinality but not exact cell identity; it now requires the exact unique `(size, leaf_bytes, start, length)` set and has an adversarial duplicate-row test.

Any interval timing before those repairs remains inadmissible. Frozen performance thresholds and the candidate algorithm were not changed.

## Exact CI authority

Workflow run: `34246754441`
Workflow: `CMPCT1 ONE-G0.2 interval packed auth proof`
Result: `success`
Exact source: `740ba74b331567eee4e547f50201824fb9f532da`
Artifact: `10064391517`
Artifact name: `one-g02-interval-packed-auth-proof-740ba74b331567eee4e547f50201824fb9f532da`
Artifact ZIP SHA-256: `60bb2f97b4d6afc392b91f28102c86b82fa21f59134535072d5915d13fb5bf08`

The benchmark executable exits zero only for `ADVANCE_INTERVAL_PACKED_AUTH_PROOF`.

## Decision

`ADVANCE_INTERVAL_PACKED_AUTH_PROOF`

Every semantic row was exact, and packed digest traffic remained exactly one 32-byte digest read per emitted sibling.

At the 1 MiB decision scale all **16/16** rows were non-regressing on both median wall and CPU, exceeding the frozen 14/16 requirement. The worst 1 MiB ratios were:

- wall: **0.735931x**;
- CPU: **0.744919x**.

Thus even the worst decisive row was about 26% faster; most rows were materially better.

Representative 1 MiB exact ratios:

- leaf 80, first 4 KiB: **0.735931 wall / 0.744919 CPU**;
- leaf 80, middle 4 KiB: **0.467845 / 0.475118**;
- leaf 80, final 4 KiB: **0.530629 / 0.540272**;
- leaf 80, middle 64 KiB: **0.530640 / 0.531505**;
- leaf 96, first 4 KiB: **0.611629 / 0.621933**;
- leaf 96, middle 64 KiB: **0.538663 / 0.539658**;
- leaf 112, first 4 KiB: **0.615141 / 0.625866**;
- leaf 112, middle 64 KiB: **0.541324 / 0.542488**;
- leaf 192, first 4 KiB: **0.617136 / 0.629442**;
- leaf 192, final 4 KiB: **0.521814 / 0.537318**;
- leaf 192, middle 64 KiB: **0.547383 / 0.549082**.

At 256 KiB the worst ratios were also comfortably green: about **0.624595 wall / 0.635262 CPU**. Exact row medians remain in the retained JSON artifact.

## Causal interpretation

The old packed proof HOLD was not evidence that packed tree state inherently harms small reads. Its dominant problem was Python control structure: recreating selected/needed sets at each tree level to rediscover a property already implied by the contiguous requested interval.

Replacing that traversal with boundary arithmetic removes the prior few-percent small-read tax and turns the same packed sidecar into a broad proof-generation win, without reading any extra digest bytes or weakening authentication.

This is a strong example of ONE's compute-efficiency law: avoid reconstructing information already implied by simpler state.

## Claim boundary / next owner

This promotion covers proof generation from a prebuilt authenticated tree only. It does not prove proof-verification throughput, full selective-open latency, peak RSS, filesystem/archive sidecar placement, remote-I/O economics, portability of the libcrypto research backend, or product-level failure isolation.

The next experiment therefore moves upward in scope: profile `proof extraction -> verification/reconstruction` for both the strong materialized reference path and the packed-interval path. If verification owns the combined authenticated selective-open budget, further proof micro-tuning should stop and the next native work should target verification while preserving exact RangeProof/root semantics.
