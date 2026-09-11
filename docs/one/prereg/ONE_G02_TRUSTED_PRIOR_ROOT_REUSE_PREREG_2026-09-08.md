# ONE-G0.2 trusted prior-root reuse preregistration — 2026-09-08

## Mission lock / Referee

### Observed baseline

The current charged temporal research-writer envelope computes SHA-256 for both the previous and current version inside every writer call. That is conservative and useful for fair local accounting, but a persistent versioned writer can plausibly enter creation with the previous generation's authenticated root identity already known.

The whole-writer owner work therefore risks charging avoidable prior-generation rehash work to `root_hash`. Before designing authentication/observation fusion, isolate that cost.

### Hypothesis

For adjacent-version creation where the previous root digest is already trusted state, supplying that digest rather than rehashing the complete previous root will materially reduce creation wall/CPU cost without changing any ONE Program, canonical wire, reconstruction result, current-root digest, admission result, segmentation result, Surprise bytes, reader work or reader semantics.

### Candidate

`trusted_prior`:

- previous-root digest is prepared outside the timed writer call and supplied as authenticated state;
- current target bytes are SHA-256 hashed inside the timed writer call;
- all remaining writer work is identical to the control;
- lazy Segment allocation is used in both arms, because it is now the preferred research-writer scheduling policy.

### Control

`rehash_both`:

- SHA-256 of previous and current roots occurs inside every timed writer call;
- all remaining writer work is identical to the candidate;
- lazy Segment allocation is used.

### Scope

This is a persistent adjacent-version writer experiment. It does **not** prove that a product archive can safely trust arbitrary caller-supplied digests. The candidate assumes the previous root identity has already been authenticated by the persistent generation/state machinery. Authenticated placement/state transfer itself remains separate product debt.

## Frozen matrix

Sizes:

- 64 KiB transfer guardrail;
- 1 MiB decision scale.

Cases:

- `shift_plus1`;
- `shift_plus1_damage_quarter`;
- `fragmented_every96`;
- `fragmented_every32`;
- `independent_random`.

Repetitions: 15 paired alternating repetitions per row.

## Frozen decision law

Semantic equality is mandatory.

At 1 MiB:

- candidate/control median wall ratio must be <= `0.95` on at least 4 of 5 rows;
- candidate/control median CPU ratio must be <= `0.95` on at least 4 of 5 rows;
- no 1 MiB row may exceed `1.02` on either wall or CPU.

At 64 KiB:

- no row may exceed `1.05` on wall or CPU.

The full matrix must be present. A missing row cannot advance.

Decision values:

- `ADVANCE_TRUSTED_PRIOR_ROOT_REUSE` when every semantic gate passes and all frozen timing conditions pass;
- `HOLD_TRUSTED_PRIOR_ROOT_REUSE` when semantics pass but timing conditions do not;
- `INVALIDATE_TRUSTED_PRIOR_ROOT_REUSE` when semantics differ.

No threshold may move after a result is observed.

## Required semantic equality

For each row, both arms must agree exactly on:

- relation admission and best shift;
- exact proof count and gate accounting;
- native Segment plan;
- Program reconstruction of previous/current roots;
- canonical ONE wire bytes;
- canonical wire byte count;
- Surprise bytes;
- reader work bytes;
- previous-root digest embedded in Program;
- current-root digest embedded in Program;
- Segment capacity and segment count.

The candidate's supplied previous digest must equal an independently computed SHA-256 oracle before timing begins.

## Cost boundary

Both timed arms include:

- source/target bytes-to-ctypes conversion;
- current-root SHA-256;
- relation admission;
- lazy Segment allocation after admission;
- native segmentation when admitted;
- bounded Law + Surprise Program construction;
- validation;
- direct canonical emission.

Only the control additionally computes previous-root SHA-256 inside the timed writer call.

Native compilation, filesystem traversal, authenticated placement/indexing, decode timing and previous-root authentication establishment are outside scope.

## Disproof / retirement result

If trusted prior-root reuse cannot deliver the frozen 1 MiB improvement without a material control regression, then prior-root rehashing is not a large enough writer cost to drive the next architecture decision under this envelope. Preserve the negative and do not build an auth/observation fusion project merely to remove it.

If it advances, the result licenses carrying trusted prior-root identity through the persistent writer boundary as an optimization target; it does not license weakening authentication or accepting unverified caller state.
