# ONE-G0.2 segment-observation root-hash fusion — terminal result

**Decision:** REJECT as an ordinary root-hash/segmentation fusion optimization.

## Authority

- Branch: `research/cmpct1`
- Exact result-bearing source: `4fecc047e064d080d570db4ed17c08886d6ee311`
- Workflow: `ONE-G0.2 segment-observation root-hash fusion`
- Run: `34082915052`
- Job: `101621493532`
- Artifact: `10004320354`
- Artifact ZIP SHA-256: `3955cd7c5df1156fcc749e4bc86776c44884b7115661a28a0b83c00f3bcdb80e`
- Experimental version: `ONE-G0.2`
- Frozen hash block: 16,384 B
- Repetitions: 101

## Mission lock

Hypothesis: while the required one-pass native Segment construction scans the current target, advance the current-root SHA-256 in regular contiguous 16 KiB blocks so that hashing work depends on bytes/blocks rather than Law-fragment count. This was intended to eliminate the later whole-target SHA pass without the per-segment `EVP_DigestUpdate` fragmentation cost that killed the preceding plan-carried-root-hash experiment.

Disproof: reject if the preregistered mature gates fail, even if semantic parity is exact. No post-hoc block-size tuning or size/fragment-count dispatcher is allowed to rescue this shape.

## Semantic result

PASS.

- ONE semantic/hostile suite: 93 passed.
- Strict native build: PASS under `-O3 -std=c11 -Wall -Wextra -Werror`.
- Native Segment plan parity: exact on all reported rows.
- Current-root digest parity: exact on all reported rows.

The workflow is red only because the final preregistered decision-enforcement step correctly rejects the measured candidate.

## Performance result

Frozen aggregate candidate/baseline ratios:

- mature all median: **1.132711588492142x**
- mature productive median: **1.1343413173652694x**
- mature fragmented median: **1.1184365311836522x**
- mature worst row: **1.1580104927947947x**

Representative rows:

- 4 KiB shift+1: 1.089243x
- 32 KiB shift+1 damage-quarter: 1.134341x
- 64 KiB fragmented/96: 1.126245x
- 128 KiB independent-random: 1.158010x
- 256 KiB shift+1: 1.151409x
- 256 KiB fragmented/96: 1.137629x

Every mature regime is materially slower than the baseline's `one-pass Segment construction + separate whole-target SHA-256`.

## Causal interpretation

The previous per-segment hash experiment showed that fragment-count-driven digest updates are expensive. This experiment removed that variable by fixing digest updates to contiguous 16 KiB blocks, yet still lost by roughly 9–16% per mature row and ~13% at the medians.

Therefore the dominant problem is broader than Law fragmentation. On this implementation/runtime, interleaving OpenSSL SHA update bookkeeping with the segmentation loop disrupts a cheap, regular scan enough that two simple bulk passes are faster than one fused mixed-purpose pass.

This is a useful falsification of the simplistic doctrine that fewer input passes always means less elapsed time. For ONE, fused observation should combine signals only when their incremental instructions/cache/control cost is lower than the regularity advantage of separate bulk kernels.

## Retirement scope

Close ordinary current-root SHA fusion into the present Segment-construction loop. Do **not** reopen via:

- a different fixed SHA block size;
- segment-count or file-size thresholds;
- corpus/workload dispatch;
- per-segment digest updates;
- another equivalent OpenSSL update-placement variant.

Legitimate reopening requires a causally different primitive, e.g. a genuinely shared vector/native observation kernel where digest work reuses already-loaded vector lanes or hardware acceleration makes the fused instruction stream cheaper than the separate bulk pass.

## Claim boundary

This result says nothing about density, Program/writer bytes, authenticated placement, selective access, v0.29/v0.30 superiority, or full ingest. It only retires this root-hash/segmentation fusion shape under the frozen native matrix.
