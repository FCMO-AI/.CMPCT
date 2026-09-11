# ONE-G0.2 incremental observation cache / changed-cone preregistration

Date: 2026-09-07
Branch: `research/cmpct1`
Experiment: ONE-07 writer-only discovery cache seed

## Mission lock / falsifiable hypothesis

A content-authenticated, policy-versioned block synopsis cache can make repeated and sparsely edited creation work tend toward changed information for expensive discovery features, while preserving exact fresh-observation results and without making cache state part of ONE reader semantics.

This seed deliberately does **not** claim that unchanged source bytes are untouched: current bytes are still SHA-256 identified before a synopsis is reused. The measured resource split is therefore:

- validation read bytes: all bytes read to establish current content identity;
- feature recompute bytes: bytes whose synopsis is actually rebuilt;
- feature reuse bytes: bytes whose previously computed synopsis is safely reused;
- persistent cache payload bytes: lower-bound payload accounting, separate from Python RSS.

## Invariants

1. Cache is writer-only and never required for archive reconstruction.
2. Cache reuse requires exact current SHA-256 block identity, exact block length, same block size and same compiler-policy ID.
3. Any policy or block-size change invalidates cache entries conservatively.
4. Poisoned/stale digest state cannot authorize stale feature state.
5. Incremental results must equal a from-scratch observation of the same current bytes.
6. Shifted insertions are not silently credited as cache hits in this positional seed; relocation needs a separate content-addressed index and must pay its lookup/memory traffic.

## Disproof / retirement tests

Retire or reform this seed if any of the following holds:

- incremental synopsis differs from a fresh synopsis on any adversarial edit;
- corrupt/stale cache content can be reused without current content identity agreement;
- policy changes can inherit old decisions;
- repeated/sparse-edit workloads fail to reduce feature recomputation materially after validation traffic and cache memory are charged;
- the cost of SHA-256 validation plus cache lookups is not competitive with simply recomputing the useful observation features;
- gains disappear once the cache carries real ONE observation/Law-discovery feature families rather than this compact synopsis seed.

## Builder state

Implementation added at `experiments/one/cache.py` with explicit resource accounting. Adversarial tests added at `tests/one/test_cache.py` covering exact repeat, one-byte edit, policy invalidation, block-size invalidation, poisoned digest state, shifted insertion and empty input.

The current seed computes a compact per-block synopsis (byte sum, transition count, zero count, min/max) only to establish the cache/invalidation semantics. These features are not claimed to be the final ONE observation vocabulary and do not alter canonical ONE0 bytes.

## Hostile-review focus

The strongest current criticism is that SHA-256 validation still reads the entire source and may dominate cheap feature computation. Therefore success cannot be declared from `feature_recompute_bytes` alone. The next result-bearing experiment must measure elapsed time, process CPU, validation traffic, feature work, cache payload/RSS and exact fresh-vs-incremental equivalence across:

- exact repeat;
- one-byte edit;
- several separated sparse edits;
- append-only growth;
- shifted insertion;
- random/incompressible bytes;
- already-compressed/media-like bytes;
- tiny roots where cache overhead should lose;
- policy-version invalidation;
- deliberately damaged cache entries.

A useful result would show that more expensive real observation features can be safely skipped on unchanged authenticated blocks and that this saving exceeds digest/cache overhead on the intended repeated/versioned region. If not, the negative must be preserved and ONE should seek a different changed-cone authority (for example filesystem/provenance-backed changed ranges or a cheaper authenticated hierarchy already required by the writer).
