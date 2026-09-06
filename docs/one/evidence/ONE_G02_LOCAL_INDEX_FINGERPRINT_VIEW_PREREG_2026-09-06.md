# ONE-G0.2 compact fingerprint ring-view A/B — preregistration

Date: 2026-09-06
Experimental line: ONE-G0.2
Authority: `research/cmpct1`

## Mission Lock

The exact local nomination ring is a verified carrying-cost owner: its scalar search performs about one 64-bit key comparison per input byte on mature rows. Tombstone-free open addressing proved that eliminating most comparisons can create a real speedup, but its hash/probe/deletion maintenance decayed to a 0.9323x size median at 256 KiB and failed the frozen <=0.90x gate. Collision-hostile input also retained irregular long clusters.

The next causal question is whether the authoritative ring can remain untouched while a **tiny, maintenance-free rejection view** makes ordinary misses cheap.

## Frozen candidate

Baseline remains the exact current 64-entry circular ring with scalar full-key search.

Candidate retains that same ring as authority and adds only a duplicated 8-bit fingerprint view:

- fingerprint = the high byte of the existing 64-bit Gear-state key; no extra hash/mixer is computed;
- 128 fingerprint bytes mirror the 64 physical ring slots twice (`fp[s] == fp[s+64]`);
- duplication makes the logical `[head, head+count)` ring interval contiguous across wraparound;
- `memchr` searches that one contiguous fingerprint interval for the target byte;
- only matching fingerprint positions receive a full 64-bit key equality check;
- a full-key equality is the **only** hit authority;
- on a miss, ordinary ring insertion/eviction is unchanged and only the two mirrored fingerprint bytes for that slot are updated.

There is no hash table, tombstone, rebuild, probe cluster, size dispatch or reader-visible state.

## Why this class

The candidate attacks both residual costs exposed by prior experiments:

1. ordinary misses inspect a dense byte array that mature libc/compiler paths can process in bulk instead of executing up to 64 scalar full-key branches;
2. eviction has O(1) maintenance: two byte stores, with no deletion search or cluster repair.

The duplicated view deliberately spends 64 extra bytes over a single fingerprint ring to remove wrap-specific lookup control. This is charged in fixed state.

## Frozen matrix

Reuse the same generator-distinct matrix and cadence as the two exact local-index experiments:

- relation sizes: 4, 8, 16, 64 and 256 KiB;
- seeds: 7, 29 and 53;
- `shift_plus1`, `damage_quarter`, `fragmented_every96`, `hostile_fixed_bands`, `fragmented_every32`, `independent_random`, and `cyclic_local_hits`.

Add an independent key-stream hostile case whose live keys deliberately share the same high-byte fingerprint. It must preserve exact decisions and demonstrate that fingerprint collisions degrade only to bounded full-key checking, never to false hits.

## Measurements

Per ordinary row record:

- exact decision checksum, hit count and live-entry parity;
- baseline full-key comparisons;
- candidate full-key comparisons;
- conservative fingerprint bytes scanned;
- lookup events;
- baseline/candidate fixed state;
- alternating A/B-B/A native elapsed, with scanning/Gear work included identically.

The hostile key stream records baseline and candidate full-key checks and exact decision parity. Its purpose is to expose the worst collision shape, not to disappear from the record if inconvenient.

## Frozen promotion / disproof law

Hard semantic gates:

- zero hit/miss/prior mismatch;
- identical hit and live-entry counts;
- fingerprint match never substitutes for full-key equality;
- hostile same-fingerprint stream remains exact.

Advance to fused-consumer integration only if all hold:

- aggregate candidate full-key checks <= **0.10x** baseline full-key comparisons on ordinary rows;
- elapsed candidate/baseline size medians <= **0.90x** for relation sizes >=16 KiB;
- no ordinary measured row > **1.03x**;
- fixed candidate state <= **1.10x** baseline local-ring state;
- on the same-fingerprint hostile stream, candidate full-key checks <= baseline full-key comparisons (no asymptotic amplification beyond the authoritative ring scan).

If semantics pass but elapsed fails, do not add a size dispatch. Retire this fingerprint-view shape and move to an explicitly SIMD/native bulk full-key comparison or a different local-reuse representation.

## Claim boundary

A pass proves only an isolated local lookup accelerator. It must then survive integration into the fused native nomination consumer with all observation, nomination and state traffic charged. No reader/format/density/comparator authority is created here.
