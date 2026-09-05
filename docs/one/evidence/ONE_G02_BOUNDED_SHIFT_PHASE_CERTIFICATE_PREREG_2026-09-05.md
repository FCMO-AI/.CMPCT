# ONE-G0.2 — sparse bounded-shift phase certificate preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2

## Mission Lock

The unconditional 32-byte rolling/bottom-8 content-local Gear certificate was structurally complementary but failed its native carrying-cost gate at a 2.2941x median large-case ratio. Rolling state alone cost about 1.33x, and asking the bottom-8 admission question at essentially every window owned the larger remaining bill.

The next question is not whether to tune that rolling certificate. It is whether the same missing information can be sampled sparsely because the downstream exact relation family is already bounded to shifts `{-2,-1,+1,+2}`.

## Candidate

Use a sparse **writer-only phase certificate**:

- witness width: 8 bytes;
- stride: 32 bytes;
- target scan phase: 0;
- source phases: `{0, 1, 2, 30, 31}`, which exactly cover the target phase under shifts `0, -1, -2, +2, +1` modulo 32;
- four bottom-hash witnesses retained **per source phase** (20 total witnesses);
- each witness stores one 64-bit mixed word and one 32-bit source position;
- modeled retained payload: 240 bytes;
- the 64-bit witness hash is a fixed bijective SplitMix-style finalizer of the 8-byte little-endian word, so equal hashes imply equal 8-byte words; an explicit 8-byte equality check is still performed before nomination.

There is no rolling state and no per-byte hash. Source witness candidates occur only at five of every 32 positions; target audition positions occur at one of every 32 positions. The exact relation dispatcher remains the only Law authority.

This is a writer-side discovery specialization to a bounded search envelope, not a reader-visible shift opcode. The emitted representation remains the same generic ONE Law.

## Why four witnesses per phase

This is frozen as a robustness allowance, not selected from the result-bearing seeds. A single phase witness is brittle to localized damage; four independent content-ranked witnesses provide multiple spatial opportunities while keeping state below 256 bytes and source candidate count fixed by stride. The validation seeds below are distinct from exploratory development seeds.

## Frozen validation

Sizes: 4, 8, 16, 64 and 256 KiB.

Generator-distinct seeds: 11, 37 and 59.

Cases per size/seed:

- ordinary +1 shift;
- contiguous quarter damage;
- mutation every 96 bytes;
- four fixed-band hostile edits;
- the prior rolling-certificate-targeted hostile construction;
- mutation every 32 bytes (exact-relation negative but expected to be a possible sparse-certificate false nomination);
- independent random negative.

The existing overlap-safe relation dispatcher supplies exact positive/negative truth.

## Frozen structural gate

Advance to native cascade-cost testing only if:

- every exact-relation positive is nominated at every size and seed;
- independent-random negatives produce zero nominations;
- source + target sampled-word count is <= 19% of full byte positions (five source phases plus one target phase over stride 32); equivalently, the candidate never becomes a disguised full scan;
- retained witness payload is exactly 240 bytes;
- all existing ONE semantic/hostile tests remain green.

`fragmented_every32` is deliberately **not** required to remain unnominated. An 8-byte local witness can survive between its edits even when the full relation is uneconomic. Such nomination is safe because it cannot create a Law; however, every such false nomination must be carried into the next native experiment and charged through the already-existing sparse relation falsifier. If that cascade cannot reject it cheaply, the candidate fails at the next gate.

## Disproof

A required-positive miss falsifies the sparse phase shape at this witness budget. An independent-random nomination falsifies the current hash/audition discipline. A structural pass does not establish efficiency; it only licenses native measurement of:

`shared observer -> sparse phase certificate only when needed -> sparse relation falsifier -> exact proof`

No threshold, phase set, stride, witness count or test family may be changed after the result to rescue a miss.

## Claim boundary

No density, reader-speed, canonical-format, v0.29/v0.30, or release claim is authorized. This experiment asks only whether complementary content-local evidence can be represented sparsely enough to deserve a native cost test.