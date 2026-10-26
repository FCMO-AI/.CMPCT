# O169 — Bounded decoded Reader cache (preregistration, 2026-10-26 UTC)

## Authority and baseline
Canonical `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; public v0.30.0 / r24 unchanged. `src/cmpct/reader.py` currently retains every decoded blob of at most 2 MiB indefinitely in `self.cache` and every reconstructed `S_VZIP` byte string indefinitely in `self.vcache`. Neither map has aggregate admission or eviction. Repeated distinct reads can retain O(total decoded archive bytes) in Python independently of mmap, even after callers release their results. This is a code-level upper-bound observation, not a measured RSS result.

## Question, falsifiable prediction, and simpler controls
Can one fixed 64 MiB **combined** byte budget for decoded `S_BLOB` and reconstructed `S_VZIP` cache residents preserve exact logical bytes while preventing unbounded retained payloads? Predictions: all successful reads still return the same exact bytes; cumulative resident cache payload remains <= 64 MiB for sequential and concurrent calls, even across both storage families; ordinary repeated small-item reads continue receiving cache hits; files larger than budget are returned but not retained. A single-file `read()` may still allocate more than the budget, so this is **not** an overall RSS guarantee.

Control A (existing): unbounded dicts, fastest repeated accesses but O(total seen bytes) retained. Control B (no cache): bounded retained cache but repeated decompression on all workloads. Control C (per-item cap only): already present for blobs and cannot bound aggregate. Control D (independent per-family LRUs): permits double combined retained payload. Selected single shared LRU accounts actual `len(bytes)` and does not modify codecs, format, or output.

## Cheapest decisive test and disproof
Before any benchmark, independently exercise bounded admission/eviction and mixed-family eviction with >100 MiB of deterministic byte values, oversized exact returns, zero-length values, repeated hottest keys, and parallel inserts/reads. Check that cache-resident bytes equal the sum of all actual retained value lengths and never exceed 64 MiB, that evicted keys miss, and that no admitted values change. A disproving byte mismatch, budget overrun, deadlock, or unexpected exception retires the candidate. Then run unchanged general/core/fuzz suites and substantive same-head official parity; any proven create/extract regression beyond the inherited release envelope blocks promotion. A unit model cannot earn product or RSS credit.

## Threat model, exported cost, and stop condition
Protection is against long-lived Reader cache retention under a sequence of legitimate distinct reads, not a hostile memory-safe parser guarantee. A transient caller result, decompressor intermediate, index, mmap, or a concurrent cohort of in-flight `read()` calls may exceed 64 MiB. Eviction can cost repeated decoding, particularly for >64 MiB virtual members; no speed win is claimed. The proposal is product-only cache admission/ownership, not a new format, compression ratio, or release.

## Concurrency and immutable evidence
Before mutation, searched open and historical PRs for decoded Reader cache/LRU/RSS; no owner for this narrow cache surface was found. Search may be incomplete; reconcile again before late writes. No shared Discovery `STATE.json` mutation. Preserve old experiments and frozen v0.30 benchmarks; leave any CI negative intact. Report exact source/CI identity and route any conclusive performance debt to the next operator.

**Decision threshold:** keep as research only unless real compiled/install tests and full official comparator demonstrate required parity. Never change the comparator or claim total process-memory boundedness from cache-resident accounting.
