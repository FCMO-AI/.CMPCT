# ONE-G0.2 — fused phase-witness carrying-cost preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2

## Mission Lock

The bounded shift-phase certificate is structurally useful, but the standalone cold-cascade implementation rereads about 1.50 relation bytes of payload per relation byte before its sparse/exact stages. The deterministic 16-probe shortcut was faster on the original cohort but failed a targeted hostile transfer and is retired as a general cold fallback.

This experiment asks whether the **same frozen phase-certificate witness semantics** can be extracted during the already-required byte observation pass without a second payload scan.

No source phases, stride, word size, witness count, hash, relation shift set, exact proof rule, reader operation, or ONE representation changes.

## Candidate

The promoted-observer control performs its ordinary per-byte Gear update and run observation.

The fused candidate performs the same work and additionally:

1. maintains the most recent eight input bytes in one 64-bit little-endian shift register;
2. when the eight-byte window start is in source phase `{0,1,2,30,31}` modulo 32, applies the existing frozen phase `_mix64(word ^ 0x9E3779B97F4A7C15)`;
3. maintains the bottom four `(hash, position)` witnesses for each of the five phases.

The input byte already loaded by the observer is reused. There is **no outgoing-byte read**, no second source scan, and no additional payload load for witness extraction. Exact native witness tuples must equal the Python phase-certificate reference before timing can count.

Modeled incremental retained discovery state is 248 bytes: 240 bytes for twenty `(u64 hash, u32 position)` witness slots plus one 64-bit rolling raw-word register. Heap bookkeeping is scalar/transient and is separately visible in code; no reader/wire state is added.

## Frozen controls

Use fresh deterministic controls:

- random 1 MiB;
- zlib-compressed random ~1 MiB;
- repeated-basis 1 MiB;
- shifted/versioned 1 MiB;
- zero 1 MiB;
- alternating-byte hostile 1 MiB;
- random 4 KiB;
- random 64 B.

Run separately compiled baseline and fused hot loops, seven outer repetitions, with internal repetitions scaled to keep timer noise bounded. Report median elapsed, fused/baseline ratio, sampled phase windows, witness admissions/replacements, anchors, and exact witness equality.

## Falsifiable hypothesis

Removing the standalone payload rescan will make the structurally successful phase evidence cheap enough to carry inside ONE observation: median fused/baseline elapsed ratio across `{random, compressed-like, repeated, shifted/versioned, zeros}` will be <= **1.12x**.

## Frozen promotion gate

Advance the fused phase witness toward combined shared-observer + hostile-relation coverage only if all are true:

- native witnesses equal the frozen Python reference on every control;
- median fused/baseline ratio across the five large gate controls <=1.12x;
- random and compressed-like each <=1.15x;
- every ~1 MiB control, including alternating hostile, <=1.18x;
- 4 KiB <=1.30x;
- 64 B <=1.50x;
- modeled retained discovery state <=248 B;
- pre-existing ONE semantic/hostile tests pass first.

## Disproof / next move

If witness equality fails, fix semantics before measuring; no threshold change is allowed.

If equality holds but carrying cost fails, do not change the five phases, bottom-4 count, or timing gate on these controls. The negative result means unconditional fused phase witness maintenance is still too expensive. Profile whether the owner is per-byte raw-window maintenance, phase hashing, or bottom-K admission, then test a mechanism-level repair that reuses more existing observer state or activates only on independently justified opportunity evidence.

If this passes, the next required test is not promotion to product format. It is a combined coverage test against both the original 34 shared-silent cohort and the targeted hostile rows that retired deterministic sparse suppression, followed by an end-to-end writer-cost A/B charging pair nomination and proof work.

No density, reader-speed, format, v0.29, or deferred-v0.30 claim follows from a pass.