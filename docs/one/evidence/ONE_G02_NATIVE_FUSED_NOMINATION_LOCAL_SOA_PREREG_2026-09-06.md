# ONE-G0.2 native fused nomination compact local SoA — preregistration

Date: 2026-09-06
Branch: `research/cmpct1`
Experimental line: `ONE-G0.2`
Parent negative: `ONE_G02_NATIVE_FUSED_NOMINATION_FP8_RESULT_2026-09-06.md`
Baseline fused source blob: `89f25972374c747654ddbf631372929b3f21b970`

## Mission Lock / falsifiable hypothesis

The fp8 result showed that local lookup owns material elapsed on miss-heavy traffic but an always-on sidecar can regress hit-rich reuse. The current authoritative local ring stores 64 instances of `one_g02_index_entry { uint64_t key; size_t start; int used; }`, which is 24 B/entry on the CI ABI: 1,536 B total. Yet the ring invariants already carry liveness in `local_count` + `local_head`; every logical slot traversed by a local lookup is live.

Hypothesis: represent the exact same 64-entry first-witness ring as structure-of-arrays (SoA): `uint64_t keys[64]` + `size_t starts[64]`, with liveness still defined solely by count/head. This removes the redundant `used` word/padding and shrinks local state from 1,536 B to 1,024 B while making the hot key scan contiguous. Because it adds no secondary filter or `memchr` path, it should retain miss-heavy locality gains without the fp8 hit-rich penalty.

Disproof: reject as fused speed work if any semantic/event/prior/nomination result differs; if the candidate does not save exactly 512 B of local state on the pinned ABI; if mature productive whole-consumer median >0.95x; if any productive row >1.03x; or if negative/control median >1.03x.

No threshold or workload classifier is permitted. The candidate is always the same local representation.

## Frozen semantic boundary

Baseline remains the exact pinned fused consumer: same Gear/minimizer observer, 64-entry local first-witness semantics, same insertion-on-miss behavior, same ring head/count order, same demand-grown 64->8192 global index, auditions, exact reuse extension, coverage accounting, emitted trace, and downstream semantics.

Candidate changes only local storage and local lookup:

- `uint64_t local_keys[64]`;
- `size_t local_starts[64]`;
- no local `used` array: `local_count` and `local_head` already define exactly which logical slots are valid;
- lookup scans `(local_head + i) & 63` for `i < local_count`, compares the full 64-bit key, and returns the same stored start at the first match;
- insertion and eviction use exactly the baseline slot/head/count transitions;
- global index remains byte-for-byte the baseline representation;
- candidate `reserved_state_bytes` charges the actual arrays and therefore must be baseline -512 B on the pinned Linux/x86-64 ABI used by the exact-source CI.

No reader, wire, Law grammar, Surprise, locality, integrity, recovery, portability, or resource-cap change is permitted.

## Frozen workload / timing law

Reuse the exact fp8 integrated matrix to make the negative directly comparable: sizes 4/8/16/64/256 KiB, seeds 7/29/53, productive `shift_plus1`, `damage_quarter`, `fragmented_every96`, `fragmented_every32`, `local_hit_rich`; controls `independent_random`, `false_pattern`; existing hostile fixed-band family remains measured diagnostically.

Use one native batch boundary and `CLOCK_MONOTONIC_RAW`, A/B then B/A, with 7 paired ratio samples per row. Python is orchestration only. Check all shared fused-result fields and emitted trace exactly; only `reserved_state_bytes` may differ, by exactly -512 B.

Promotion requires all:

1. zero semantic/trace/resource-counter mismatches other than the frozen -512 B state delta;
2. mature productive median <=0.95x;
3. no productive row >1.03x;
4. negative/control median <=1.03x;
5. ONE semantic/hostile tests green.

## Hostile Reviewer pre-commit critique

The likely failure is that AoS stride/state was not the actual cost; 1.5 KiB is already L1-resident and the compiler may have made the baseline lookup nearly optimal. SoA may therefore produce ~1.00x despite saving 512 B. A second risk is that the dedicated SoA loop changes compiler inlining/vectorization enough to create runner-sensitive apparent gains. That is why the whole-consumer gate, per-row ceiling, exact-source pin, and paired timing remain authoritative.

This is a new causal hypothesis, not a post-hoc rescue threshold for fp8.
