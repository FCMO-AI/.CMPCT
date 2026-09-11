# ONE-G0.2 incremental relocation unique-identity index — 2026-09-07

## Mission lock / Referee

Hypothesis: the writer-only ONE-07 relocation cache can store at most one prior representative for each `(SHA-256 digest, block length)` identity without changing the current aligned fingerprint stream, while materially reducing relocation-index memory and duplicate-candidate work on repetitive/versioned inputs.

Disproof: any current input for which deduplicating prior candidates changes the fresh fingerprint oracle, makes damaged cache state authoritative, or requires duplicate prior representatives for reader-visible semantics. Any such result retires the dedupe shape.

This remains writer discovery state only. It does not change ONE0 bytes, Law + Surprise grammar, reader discovery obligations, selective-read semantics, or reconstruction semantics.

## Hostile Reviewer finding

The preregistered relocation seed indexed every prior block as a candidate, including blocks with identical content identity and therefore identical content-derived fingerprint payload under the same policy, block size and chunk size. On repetitive data this spent index memory on duplicate candidates that carry no additional observation information.

The fingerprint synopsis used here is a pure function of block bytes under the cache policy/shape, and reuse is still admitted only after current SHA-256 identity plus the existing sealed fingerprint payload validate. Reusing one cached observation representative multiple times is therefore not equivalent to reusing a reader-visible source reference: no ownership, offset, or decode dependency is being shared.

## Builder change

`experiments/one/cache_relocation.py` now builds a bounded map from `(digest, length)` to one representative `FingerprintBlock` rather than a list containing every prior block with that identity. `max_relocation_entries` therefore bounds unique identities. Seal validation remains deferred until current bytes nominate a representative; malformed or damaged representatives fail closed to fresh computation.

This deliberately prefers integrity over reuse availability. If the first representative for a repeated identity has a damaged seal while another duplicate is healthy, the current implementation may recompute matching current blocks instead of searching duplicates. Correctness survives; reuse can decline. Paying to locate a healthy duplicate is regression debt that must justify its extra index/build/hash traffic before admission.

## Adversarial tests

`tests/one/test_cache_relocation.py` now includes two duplicate-identity attacks in addition to the existing exact-repeat, sparse-mutation, aligned-insertion, reorder, arbitrary-byte-shift, bounded-index, corruption and policy-invalidation cases:

1. A 16-block alternating A/B root is reordered to B/A. Exact fresh fingerprints must match; only two unique relocation identities may be indexed; after the one-block movement probe, the remaining fifteen blocks are expected to reuse observation work.
2. The first cached A representative is deliberately corrupted while retaining stale seal metadata. The unique-identity index may lose A reuse, but output must still equal the fresh oracle and the damaged synopsis must never become authority.

## Resource accounting

The existing relocation accounting models a lower-bound 48 bytes per indexed identity: 32-byte digest + length + representative reference. This is not an RSS claim and excludes Python/native container overhead.

For the 16-block A/B hostile fixture:

- old per-block lower bound: `16 * 48 = 768 B`;
- unique-identity lower bound: `2 * 48 = 96 B`;
- modeled index-payload reduction: `8x`.

For a 1 MiB root with 4 KiB blocks and only two unique identities:

- 256 prior blocks;
- old per-block lower bound: `12,288 B` (~1.17% of input);
- unique-identity lower bound: `96 B` (~0.0092% of input);
- modeled index-payload reduction: `128x`.

These are causal lower-bound calculations only. Exact wall time, process CPU, memory traffic and peak RSS for the deduplicated shape have not yet been promoted as evidence.

## Strongest negative / debt

Deduplicating identities reduces stored candidate multiplicity, but initial index construction still scans the prior block sequence and is therefore O(n) in prior blocks. This change attacks index cardinality and duplicate candidate work, not the cost of discovering the unique identities in the first place.

The next stronger shape, if this experiment survives, is an incrementally maintained content-identity directory carried in writer cache state so repeated runs do not rebuild it from scratch. That would itself consume persistent bytes, validation work and memory, so it must be charged rather than assumed beneficial.

Arbitrary byte-shift resynchronization remains unsolved. Aligned FNV observation groups are position-relative, so a one-byte insertion legitimately changes their grouping; content-defined observation anchors require a separate falsifiable experiment.

## Promotion boundary

No CMPCT1 density/speed/access promotion is claimed from this receipt. The frozen relocation resource gate still controls promotion, and the deduplicated shape must obtain exact-head test/benchmark evidence. Frozen v0.29 and deferred v0.30 authorities are unchanged.

## Next decisive action

Run the exact-head hostile tests and frozen relocation resource gate. Add a low-cardinality diagnostic spanning unique-identity counts to measure whether lower index cardinality translates into wall/CPU/RSS benefit rather than merely prettier accounting. If build scanning remains dominant, reform toward a persistent bounded identity directory instead of tuning movement thresholds.
