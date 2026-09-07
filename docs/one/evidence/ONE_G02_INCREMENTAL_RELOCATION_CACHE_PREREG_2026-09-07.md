# ONE-G0.2 — bounded relocation-cache preregistration — 2026-09-07

## Mission Lock / Referee

ONE-07 already permits writer-side content-addressed observation caches, but the current
aligned-fingerprint cache is positional: unchanged information that moves to another block
position is conservatively recomputed.  That is correct but potentially wasteful for
versioned inputs containing block-aligned insertions or reorders.

Falsifiable hypothesis: a bounded, writer-only content-identity relocation index can recover
most expensive aligned observation work after genuine movement while remaining nearly free
on exact repeats and ordinary sparse mutations.  It must not alter ONE archive bytes,
reader semantics, authenticated current-byte identity, or fresh-vs-incremental feature
results.

The positional `observe_fingerprints_cached` path is the baseline.  The candidate is
`observe_fingerprints_relocated`.  Current bytes are SHA-256 validated in both paths; no
zero-read or trusted-dirty-range assumption is introduced.

## Frozen disproof gates

Resource experiment: `benchmarks/one/one_incremental_relocation_cache.py`.

- 256 KiB and 1 MiB deterministic inputs with distinct block identities.
- 4 KiB observation blocks, 64-byte aligned FNV64 feature chunks.
- 15 paired alternating baseline/candidate repetitions.
- Cases: exact repeat, one-block sparse mutation, one-block aligned insertion, block
  reorder, and hostile one-byte insertion.
- Candidate and baseline fingerprints must match exactly before timing is considered.

Advance only if all rows satisfy:

1. **Aligned movement (`block_insert`, `block_reorder`)**: candidate feature-recompute
   ratio <= 0.10 of positional baseline, median wall <= 0.90x, median process CPU <= 0.90x.
2. **Exact repeat**: relocation index entries = 0, relocation lookups = 0, wall <= 1.05x,
   CPU <= 1.05x.
3. **Sparse mutation**: relocation index entries/lookups/gate activations = 0, wall <=
   1.08x, CPU <= 1.08x.
4. **One-byte insertion hostile control**: wall <= 1.15x and CPU <= 1.15x.  No claim is
   made that position-relative fingerprints can be reused through byte shifts.
5. Lower-bound relocation-index payload <= 2% of current input bytes on every row.

These are mechanism gates, not release gates.  Passing them permits deeper measurement; it
does not establish native/full-ingest authority or a Genesis scoreboard win.

## Builder

`experiments/one/cache_relocation.py` adds a bounded index from prior `(SHA-256 digest,
length)` identities to sealed cached feature payloads.  Positional reuse remains first and
cheapest.  Relocation candidates remain nominations only: the existing policy/block/chunk
identity and synopsis seal checks still have to pass before reuse.

The candidate exposes validation reads, recompute/reuse bytes, seal-hash bytes, cached
feature payload reads, positional and relocated reuse counts, index entries, a lower-bound
index payload model, lookup count, gate activations, and persistent cache payload.  Python
object/RSS overhead is explicitly outside the lower-bound index model and must be measured
before any production claim.

## Hostile Reviewer finding before first authoritative run

The first Builder draft lazily created the global relocation index after the first
positional miss.  That was too eager: one ordinary sparse mutation would pay O(n) index
construction even though there was no evidence that content moved.  This contradicted
ONE's opportunity-gated-search rule and could export more memory traffic than the saved
feature work.

The candidate was therefore changed *before* evidence collection.  One positional miss is
now treated as a local mutation and recomputed.  Relocation search activates only after two
consecutive positional misses.  A later valid positional reuse resets the miss streak.
This intentionally sacrifices reuse of an isolated moved block in exchange for avoiding a
global search on the common sparse-mutation shape.

The hostile tests now require a one-block sparse mutation to cause exactly local
recomputation with zero relocation-index entries, zero relocation lookups, and zero gate
activations.  They also attack corrupted relocated feature payloads, policy relabeling,
bounded index capacity, block reorder, aligned insertion, and byte-shifted input.

## Representation and trust boundary

This experiment is writer discovery only.  It introduces no reader-visible opcode, codec,
cache dependency, or fallback representation.  Fresh and incremental observation must
produce identical aligned fingerprints.  Current content identity is re-established from
current bytes; cached identity metadata is never sufficient on its own.

The cache seal is integrity evidence inside the existing writer-cache trust model, not a
keyed MAC.  Arbitrarily adversarial rewrite of both payload and seal remains outside this
seed's trust boundary.  Archive decode never depends on this cache.

## Negative boundaries / retirement conditions

- Arbitrary byte-shift resynchronization is not solved by this mechanism.  If that matters,
  content-defined observation semantics must be proposed and falsified separately.
- If aligned movement cannot clear both the 0.90x wall and CPU gates after all index/seal
  costs, retire or reform this global-index shape rather than tuning a threshold until it
  turns green.
- If sparse mutation activates global relocation work or exceeds its frozen overhead gate,
  the opportunity gate is inadequate.
- If real Python/native index RSS materially exceeds the modeled lower bound, that exported
  cost must be charged before promotion.
- Even a passing fingerprint experiment must later survive integration with real ONE
  discovery/admission work and full writer accounting.

## Next evidence step

Run the exact-head GitHub workflow `CMPCT1 ONE-G0.2 incremental relocation cache`.  If the
frozen resource gate passes, measure actual peak RSS/index construction traffic and then
attach the mechanism to the broader fused-observation/full-ingest path.  If it fails, retain
the negative evidence and decide from the causal owner: search traffic, integrity cost,
feature cheapness, or insufficient relocation recovery.
