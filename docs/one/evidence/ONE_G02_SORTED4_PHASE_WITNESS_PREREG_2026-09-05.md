# ONE-G0.2 — sorted-4 phase-witness selector rehabilitation preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2
Parent owner evidence: `ONE_G02_FUSED_PHASE_WITNESS_OWNER_DECOMPOSITION_RESULT_2026-09-05.md`.

## Mission Lock / Referee

The unconditional fused phase certificate is still retired under its 2.7600x large-control carrying-cost result. Native decomposition identifies bottom-K maintenance as the stable first cost owner on 4/5 frozen large controls, but raw-window and phase-hash work remain close neighbors.

This Builder asks whether the online witness selection representation can be made materially cheaper without changing certificate coverage or exporting work to another reader-visible mechanism.

## Invariant

Keep all of the following frozen:

- phase set `{0,1,2,30,31}` modulo 32;
- 8-byte little-endian phase word;
- `_mix64(word ^ 0x9E3779B97F4A7C15)`;
- K=4 witnesses per phase;
- witness ordering semantics: bottom four `(hash, position)` pairs, with earlier position winning a hash tie;
- observer Gear/run work;
- no payload rescan;
- 248 B modeled incremental retained state ceiling;
- no reader/wire state.

The control remains the exact heap-style `offer()` implementation from source `df083da415fb8aa426c3f6a1ed84cd6d25f5e32d`.

## Builder

Replace only the per-phase heap representation with four witnesses kept in ascending `(hash, position)` order.

Because source positions are offered monotonically, a new candidate with hash equal to an already-filled worst hash can never beat an earlier held equal-hash witness. The full common path can therefore reject `h >= worst_hash` immediately. On a true admission, bounded insertion shifts at most four scalar slots.

This removes heap parent/child traversal and keeps the common rejection path branch-light. It is an implementation change to the same exact certificate, not a new selection policy.

## Frozen controls

Use the parent carrying-cost controls unchanged:

- random 1 MiB;
- zlib-compressed random ~1 MiB;
- repeated-basis 1 MiB;
- shifted/versioned 1 MiB;
- zero 1 MiB;
- alternating-byte hostile 1 MiB;
- random 4 KiB;
- random 64 B.

Also verify exact candidate witness tuples against the independent Python phase-certificate reference before timing can count.

Compile control and candidate as separate `-O3` shared objects from the same parent native source; the sole candidate change is `offer()`.

## Falsifiable hypothesis

A sorted-4 selector will reduce the full fused loop enough to produce a **<=0.90x median candidate/control elapsed ratio across the five large gate controls**, while preserving every exact witness tuple.

## Frozen gate

Advance selection-local rehabilitation only if all are true:

- control and candidate witnesses both equal the independent Python reference on every control;
- five-large-control median candidate/control <=0.90x;
- no individual ~1 MiB row >1.03x;
- 4 KiB <=1.05x;
- 64 B <=1.10x;
- modeled incremental retained state <=248 B;
- pre-existing ONE semantic/hostile tests pass first.

## Disproof / next move

If witness equality fails, the Builder is invalid regardless of speed.

If exactness holds but the total-loop timing gate fails, retire **selection-local spelling changes** as the immediate rehabilitation route. Do not try another heap variant on the same cohort. The decomposition already shows a co-near-dominant three-stage bill; move to a mechanism-level cross-stage intervention: either derive certificate evidence from existing observer state or activate the richer certificate only after independent cheap evidence establishes that the shared observer is insufficient.

A pass still does not revive the unconditional fused path by itself. It only demonstrates that a material fraction of its compute debt can be removed without weakening coverage. The original <=1.12x carrying-cost gate would still have to be rerun before any broader writer claim.

No density, reader-speed, format, product, v0.29, or deferred-v0.30 claim follows from this experiment.