# J24G87 — post-result decision: immutable-plane member snapshots still above 5% on both authentic histories

**2026-10-30 UTC.** Hypothesis frozen in separate preregistration commit `28293d1583b15cca9220ec8b81771445fcb8767a` before running the factorized oracle. Parent #838 and J24G86 complete-index negative remain unchanged.

## New representation and exact semantic scope
Hypothetical checkpoint stores only complete surviving file/member rows, a separately authenticated SHA256 binding to the original immutable index, an explicit 8-byte base-index offset, and a 16-byte grammar/version/flag marker. Reference, keys and complete MessagePack record are fully charged; Zstandard levels 1,3,19 are measured independently. The original physical r24 header/index remains stored and paid in the authentic archive. A verifier refuses a deliberately tampered root SHA. Both original 65-footer histories contain 63 DELETE-only deltas with no new blobs; the *entire non-file index plane* (blobs/recipes/dict_blob/fsmeta/features) is demonstrably identical between authenticated initial index and generation64 final full checkpoint. The member rows are reconstructed byte-for-byte from source rows.

**Do not describe this as an existing legal revision-24 checkpoint. It requires a new bounded reference grammar and Reader contract if ever productized.**

## Signed physical source and charged result
Same two original verified physical archives as J24G86. No production code imported, no original source altered. Compared with current authentic physical stored bytes and exact delta bodies/footers, replacing the deltas at K steps with the new *factorized* signed snapshot yields:

| Source | K | Extra bytes | Complete archive overhead | Worst remaining signed deltas | Preregistered K32 gate |
|---|---:|---:|---:|---:|---|
| 8,192 members, original 1,017,260 B | 8 | 427,923 | 42.066% | 7 | Not tested |
| 8,192 members | 16 | 183,396 | 18.028% | 15 | Not tested |
| 8,192 members | 32 | 61,130 | **6.009%** | 31 | FAIL |
| 32,768 members, original 4,084,062 B | 8 | 1,714,850 | 41.989% | 7 | Not tested |
| 32,768 members | 16 | 734,934 | 17.995% | 15 | Not tested |
| 32,768 members | 32 | 244,980 | **5.998%** | 31 | FAIL |

K32 still provides 2.032x reduction in **maximum delta step count**, but exceeds the prospective <=5% complete stored byte research gate in both cases. Result: `FACTOR_MEMBER_K32_FAILS_O0`. The reduced size relative to J24G86 is genuine, not enough for this criterion. No measured Reader wall/CPU/RSS gain or product credit.

## Stronger alternative and anti-local-optimum decision
The unchanged blob/recipe/fsmeta planes are not the only repeated information. The **file rows themselves** are largely unchanged under DELETE-only histories. A still more different information model could use an authenticated base-row ordinal/bitset survivor map and avoid serializing complete file rows; it must charge the bitmap, index root, extra map decoding/work and bounded branch admission, and fall back to full snapshots for nonmonotonic operations, renames, puts, metadata changes or physical-owner replacement. Compare against the existing signed delta chain and indexed replay. Do **not** treat this suggestion as evidence that an ordinal map wins: it is an untested future hypothesis.

## Negative truth, further gates, and release boundary
The result is an O0 oracle on two actual immutable physical archives, with exact signed root identity but hypothetical new format encoding and no real materialized alternative. We have not demonstrated any valid Reader/preflight/extractor, corruption recovery, cross-platform I/O, Windows hardlinks, xattr identity, multiwriter serialization, resource/hostile-input bounds, or release performance. Reference-availability and fallback semantics are future debt. A material compression/reader claim requires full authenticated physical materialization and O2 parity. The original strict published zero-byte and confirmed timing promotion rules remain intact; <=5% here is solely a preregistered research triage criterion.

## Ownership / handoff
This child branch derives from PR #838, does not modify source, tests, comparators, format/release policy, discovery STATE, or existing owner branches. Concurrency search found no identical active narrow factorized member-plane checkpoint owner. Source-continuity from #833 is verified by the prior J24G86 physical referee. No CI conclusion is claimed for this local O0; GitHub checks must be evaluated separately.
