# ONE-G0.2 local Gear certificate native carrying-cost preregistration

## Mission Lock / Referee

The frozen structural result for the content-local Gear certificate repaired the 4/8 KiB fragmented relation-nomination debt with a bounded bottom-8 rolling certificate and no false nominations on its frozen negatives. Its explicit remaining debt is native carrying cost: the writer must pay a 32-byte rolling window, eight `(u64 hash,u32 position)` witnesses, and one rolling u64 state (136 B modeled state), plus source bottom-8 maintenance and target witness checks.

This experiment asks a narrower question before touching the product writer: **is the certificate's incremental per-byte work cheap enough in a native Gear observation hot loop to justify a full promoted-observer integration A/B?**

It does not re-prove the certificate's structural value and does not claim end-to-end writer speed.

## Frozen arms

Baseline: one native forward Gear observation over source then target, charging run tracking, the canonical historical Gear recurrence `h = (h << 1) + gear[byte]`, 64-byte observation eligibility and the existing sparse 1/1024 anchor predicate.

Candidate: byte-identical baseline observation plus the exact certificate work from the structural Builder:

- 32-byte rolling Gear/buzhash window;
- source bottom-8 `(hash,position)` maintenance;
- target comparison against the eight retained hashes;
- exact 32-byte equality before a nomination;
- fixed 136 B logical certificate state.

The canonical 256-entry `_GEAR` table is supplied by the existing Python authority to the native kernel; no substitute table is allowed.

## Frozen matrix

Generator-distinct deterministic rows, all timed as source+target pairs:

- tiny 4 KiB shifted +1;
- tiny 8 KiB fragmented every 96 bytes;
- 64 KiB shifted +1;
- 256 KiB fragmented every 96 bytes;
- 256 KiB independent random;
- 1 MiB independent random/incompressible;
- 1 MiB already-compressed-like payload (zlib of deterministic random bytes);
- 1 MiB repeated/versioned basis.

Warm-up is mandatory. Timed repetitions: 101. A/B and B/A order alternates. The compiler is `-O3 -std=c11 -Wall -Wextra -Werror`.

## Required parity / anti-cheating

The candidate must preserve every baseline observation counter exactly. The certificate state must be bounded to eight witnesses and must report no more than 136 B modeled retained state. For rows where the structural certificate should nominate, native nomination must be nonzero; independent-random controls must not create an exact 32-byte false nomination.

The candidate's certificate work must remain inside the timed region. No precomputed source certificate may be passed into the timed candidate.

## Falsifier

This is a **triage gate**, not promotion.

Advance to a full promoted-observer carrying-cost A/B only if all are true:

- mature (>=64 KiB) median candidate/baseline elapsed <= **1.08x**;
- fragmented mature median <= **1.10x**;
- no mature row > **1.15x**;
- tiny median <= **1.15x**;
- semantic/counter parity and bounded-state checks pass.

Otherwise retire the present per-byte bottom-8 certificate carrying shape. Do not rescue it with file-size thresholds, certificate K tuning, window tuning, corpus dispatch or a weaker negative matrix.

A legitimate redesign after rejection must reduce work structurally (for example derive witnesses from observation events already emitted by the promoted observer) rather than merely retune this rolling certificate.

## Claim boundary

A PASS only licenses a full promoted-observer/native writer A/B. A FAIL is sufficient to reject this carrying shape because the product path can only add more surrounding work. No stored-byte, reader, density, RSS, release, v0.29/v0.30 or full-ingest claim follows from this microbenchmark.
