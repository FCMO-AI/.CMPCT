# ONE-G0.2 exact local-index hash A/B — preregistration

Date: 2026-09-06
Experimental line: ONE-G0.2
Authority: `research/cmpct1`

## Mission Lock

The exact nomination-index probe attribution lane localized the 64-entry local ring as a plausible carrying-cost owner: on the measured 64/256 KiB relation matrix it performs about 0.984-0.996 key comparisons per input byte while the global index performs far fewer. That evidence is comparison-count attribution only and does not prove elapsed ownership. Nor does the observed zero local cross-object exact share on that matrix authorize deleting local reuse, because the local ring may be valuable for within-object reuse on other workloads.

The next question is therefore narrower and falsifiable: can the **same** 64-entry local lookup semantics be implemented with materially less probe work and elapsed time, without changing which prior position is selected on any lookup?

## Structural observation

The current ring inserts a key only when lookup reports a miss. Therefore the live 64-entry ring contains at most one entry for any 64-bit key. This makes an exact key->ring-slot index possible without changing duplicate-key selection semantics.

## Frozen arms

Both arms scan the exact same input bytes, update the exact same Gear state, issue local lookups at the same 64-byte cadence, suppress run-dominated windows identically, retain at most the same 64 live entries, and return the same prior start on a hit.

**Baseline:** current linear scan over the live circular ring.

**Candidate:** a 128-bucket open-addressed table maps each live 64-bit key to its ring slot. Ring eviction removes the evicted key from the table; insertion adds the new key. Tombstone handling must preserve exact lookup semantics. The ring itself remains authoritative storage and capacity remains 64 entries.

This is creation-time indexing only. It changes no ONE reader operation, wire byte, Law semantics or archive format.

## Frozen matrix

Sizes: 4, 8, 16, 64 and 256 KiB. Seeds: 7, 29 and 53.

Use the existing relation/control family:

- `shift_plus1`
- `damage_quarter`
- `fragmented_every96`
- `hostile_fixed_bands`
- `fragmented_every32`
- `independent_random`

Add two index-specific hostile streams:

1. repeated/cyclic content producing frequent key hits;
2. an adversarial low-bucket-collision key stream for the table implementation, generated independently of the production corpus and checked for exact prior-position parity.

## Measurements

Record per row:

- exact hit/miss and prior-position parity;
- lookup event count;
- baseline key comparisons;
- candidate hash-table probes;
- candidate tombstones and maximum probe length;
- baseline/candidate retained state bytes;
- alternating A/B-B/A native elapsed time.

All input scanning and Gear-state work must be charged equally. No Python loop may sit inside the timed lookup path.

## Disproof / promotion law

Semantic gates are hard:

- zero hit/miss mismatches;
- zero prior-position mismatches;
- identical live-entry count after each insertion/eviction sequence;
- capacity never exceeds 64 live ring entries;
- candidate table must fail closed rather than silently lose a live key if its own 128-bucket bound is exhausted.

Advance to fused-consumer integration only if semantics are exact and:

- aggregate candidate probes <= 0.30x baseline key comparisons;
- productive/control size medians of elapsed candidate/baseline <= 0.90x for sizes >=16 KiB;
- no row exceeds 1.03x;
- candidate total fixed state remains <= 2.5x the current local-ring state.

If exactness fails, reject the structure. If exactness passes but elapsed does not, preserve it as a negative: fewer comparisons alone do not justify more irregular hash-table control.

## Claim boundary

A pass proves only that the local 64-entry lookup can be indexed more cheaply while preserving its exact lookup behavior. It does not prove total fused-observer speed, relation recall, stored-byte gains, product writer speed or comparator superiority. The next gate after a pass must integrate the exact structure into the native nomination consumer/fused observer and charge all carrying cost.
