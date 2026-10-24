# O33 — O31 canonical hardlink Reader economics (prospective preregistration)

Date: 2026-10-24 (UTC). Status: **PREDICTION ONLY — NO RESULT YET**.

## Authority, ownership, and source boundary

Released CMPCT v0.30.0 remains format revision 24. This is a research-only independent economics follow-up stacked on draft product owner PR #385, exact starting HEAD `0edb7bc6e832deb1b403fea50c36e655da9844fd`, Reader Git blob `de9accf6607aca7cf70dfe71d7b299a02e298a2d`. Historical control is exact parent PR #381 HEAD `9c9cecc6c21dc741e57188076ea43dc0ede6425b`. No product code, inherited test, benchmark threshold, frozen workload, format, or release gate may be modified by O33. Preserve source-specific known inherited reds in O28 as separate from this economic court.

PR #385 owns canonical hardlink resolution and implicit hardlink parent reconstruction. This court owns only an independently reproducible **same-input** cold Reader open/CPU/RSS evaluation. Check for a concurrent narrow economics owner before further writes; do not duplicate if another operator claims it.

## Primary falsifiable question

Does the O31 canonical-path map plus eager authenticated hardlink-owner resolution impose material cold-open latency or resident-memory cost relative to exact O28, particularly on ordinary no-hardlink checkpoints, while retaining its O29/O31 new semantic fixes?

Baseline: O28 performs Reader path/graph admission and static pre-existing destination containment, but lacks O31 canonical owner target resolution. O31 builds a canonical-to-raw map for all logical entries, memoizes every hardlink terminal owner, and preserves a separate extraction-time graph check. A `read()/verify()` speed win is not assumed. Its new positive capability on backslash owner targets is orthogonal and must not be counted as a performance regression of O28.

Predictions: O31 produces some O(N) constructor/RSS overhead, likely smaller than 10% median or 3.0 ms at 4,096 entries on comparable checkpoints. Direct hardlink fanout may benefit from O31's resolution reuse, while deep chains remain linear through path compression. A reverse trend is an honest negative.

## Cheapest same-semantics control

Construct authentic SHA-committed revision-24 *checkpoint* archives using the actual CMPCT codec framing and raw physical record, not mocked Reader objects, at sizes 512 and 4,096 logical entries. Compare three structural classes with the **same bytes** passed to both exact implementations:

1. **Plain:** N independent regular rows referring to the same authenticated raw physical blob (no hardlink aliases).
2. **Fanout:** one regular owner, N-1 hardlink aliases directly targeting that owner.
3. **Chain:** one regular owner and N-1 aliases where each points at the next alias, terminating at the owner.

Verify signed index/authenticated payload and strict preflight once before timing; both Readers must read/sha/range the same sample and expose identical logical content. Generate all six inputs once per runner; hash and record complete archives. Avoid a benchmark corpus whose spelling is deliberately *not* supported by the historical O28 control. No case-specific threshold selection based on results.

Run at least 8 **fresh independent Python processes per variant per scenario**, alternating O28/O31 in paired ABBA/BAAB order on one Ubuntu runner. Each child imports the selected exact source tree (with provenance asserted by file path and Git blobs), times import, `CMPCT(path)`, and a minimal content/range check separately, and records user+system CPU, `/proc/self/status` VmRSS and VmHWM before/after construction, and `resource.ru_maxrss`. Parent separately times complete subprocess wall. Do not combine in-process warm timing and full-process cold timing. Preserve raw pairs rather than only ratios.

## Material-debt / disproof criteria

Treat as a prospective concerning regression if, at N=4,096, the candidate's paired constructor median is slower by **both** >=10% and >=3.0 ms in any scenario, or its after-constructor VmRSS exceeds O28 by **both** >=10% and >=4 MiB under comparable fresh processes. The criteria are for *research triage*, not a replacement for official frozen r24 release gates. Smaller differences remain measured debt, not proof of zero cost; noise in the same-runner repeats must be disclosed. If historical source unexpectedly fails a common-case fixture, remove that fixture from the shared economic claim and preserve the failure as a separate semantic discrepancy rather than weakening the semantic contract.

Positive findings need at least two structurally different controls, complete physical archive SHA identities, source-bound repeated measurements, and a reasoned comparison against import/startup fixed costs. A source-level claim of O(N+E) graph complexity alone has no product-performance credit. No merge/release/version bump is authorized from this court.

## Alternatives and PARETOBONK

Rather than another O31 implementation or speculative index refactor, first measure the direct economic liability of existing owner change. Stronger control is O28 exact source; alternative explanation is unrelated hosted-runner, import, cold filesystem-cache, and process-memory noise. A full benchmark matrix is premature for a constructor-only fork; the official parity comparator and complete safety suite remain independent obligations. O31's capability improvement is not traded against microseconds by changing file-system semantics.

## Next decision

If material: owner should investigate allocation placement or shared map representation without sacrificing canonical identity or eager graph validation. If nonmaterial: stop local map tuning and prioritize O31 full-source convergence, independent installed-wheel security, official performance and recovery gates. Retain raw negative/ambiguous data. This record is append-only; results belong in a separate report tied to the exact run/HEAD and should not edit this prediction.
