# J24R03 — prospective locality-transfer falsifier for sparse selective range

**Frozen before experiment implementation/results.** Date 2026-10-27 UTC.
**Question:** Does the measured J24R02 late-position 55–775x gain from a binary-search S_SPARSE Reader transfer to early, middle, balanced and multi-extent range requests, or does early-position overhead overturn the general-product interpretation?

## Current authority, provenance and no-overlap ownership
- Published CMPCT v0.30.0 / on-disk revision 24 `main@80c358f8824ec1b20d349c92ed94c898090969b0` remains unchanged.
- Exact baseline J24C02 #569 `c5e13bb3fbb4cdade8b64246658ce7c7818de41f`, Reader Git blob `dbd4ac576a05a47eae97e1e40de89cf1de440516`.
- Exact candidate J24R01 #584 `70336307312b5b277f0885c0057d2cddab0aefc1`, Reader blob `ca1763b9d69b385eab80d0ed67a914672dbe93fc`.
- J24R02 #586 has already measured real installed late 1-byte requests, finding 55x at 4096 and 775x at 65536, while small-E lost ~26–30%. **Do not re-run the same narrow experiment**. This investigation tests a different independent distribution of positions and lengths; do not change the owner Reader or J24R02 tests, thresholds or interpretation.
- `docs/discovery/STATE.json` is staleable and independently owned by #574, not a lock. No concurrency protocol or claims helper exists on current main as of orientation.

## Prior causal model and structural alternatives
Old S_SPARSE scans from the first extent until intersecting a query: for early ranges, often O(1); for middle/tail O(E/2)–O(E). Candidate uses bisect over authenticated existing extent ends, O(log E) plus intersections. This implies the tail-only workload is an optimistic bound, not a representative general read mix. No extra index allocation. Alternatives: keep simple linear front early; a structural first-hit accelerator; or materialize offset/index arrays at O(E) memory/open cost. Baseline may rationally win in an early-heavy regime and for small E.

## Frozen same-input physical experiment
- Generate one independent, authentically framed SHA+CRC revision-24 archive per E in `[1,4,4096,65536]` by reusing the unchanged O212 `_archive_bytes` fixture generator. One shared four-byte RAW physical owner repeated at ascending 16-byte-stride extents; actual archive and complete logical SHA recorded. Baseline/candidate read exact same files.
- Query regimes per E, 128 requests each: `front`, `middle`, `tail`, `balanced` (equal deterministic interleaving of those three), `span` (ranges touching up to 32 consecutive extents). Include positions within data and holes, 1/4/12-byte and span requests; clamp rigorously to EOF; reject out-of-bounds as before.
- Three ABBA rounds, alternating B-A-A-B order on odd rounds, one **fresh external-cwd child interpreter per arm/round/E/regime**: 4 counts x 5 regimes x 3 rounds x 4 arm executions = **240 full original observations**. Record open wall+CPU and 128-request wall+CPU, raw per-process values, source/module absolute location, archive bytes, logical bytes, correctness count, and host resource high-water marker (attribution caveat). Run native independent exact code through two isolated installed sites: never time a mocked Reader or mutate either control. Warm one untimed query pass before timed pass, without changing the effective task.
- Preflight unmodified existing O212 geometry/sparse acceptance; for every timed query compare bytes to the independently constructed logical oracle. Preserve queries, raw results, order, failed workers/stderr; no selective deletion of slow samples.
- Independent receipt auditor (different code path) recomputes ABBA completeness, install-source hashes versus `git show`, fixture hashes, all medians/speedups, query digest/count and control interpretation. Deliberately corrupt 2 receipt facts as negative evaluator tests. Three-host semantics are inherited from #586; this run's timed ABBA on Ubuntu 24.04 suffices for scoped transfer.

## Prospective predictions, falsifiers and decision
1. At E >= 4096, **middle and tail** should each improve >10x in median batched wall while same logical answers and wire bytes hold. `balanced` should improve >5x. Failure narrows/retire broad transfer, even if tail-alone stays fast.
2. Early-only high-E may be neutral or **slower** under bisect; record all positive/negative outcomes without declaring a universal gain. For E <= 4, candidate probably loses in several regimes, matching the strong J24R02 negative. That remains promotion debt, not a reason to weaken the tests.
3. The span test may be decode-dominated and need not win: its outcome measures how much lookup speed transfers when necessary physical work increases.
4. Any wrong byte, changed malformed admission, unbound source identity, skipped observed requests, missing ABBA arm, worker error, or changed fixture invalidates corresponding scientific credit. An advantageous isolated selected-range result is not product/release credit. Full release gate and complete filesystem/security semantics remain unmeasured.
5. No threshold tuning, new decoder-visible facts, format change, benchmark redefinition or source mutation permitted during this frozen run. If instrument is wrong, preserve failed execution and commit a separately labeled prospective superseding note **before** modifying the experiment.

## Next branch-owner decision
Evidence should distinguish whether a global unconditional bisect is justified, whether a simple cheap direct-first strategy is worth independently testing on J24R01 owner branch, or whether the family should be narrowed to high-E mid/tail. This does not solve #569 S_CHUNKS cold-open ~28.5x, #528/#572/#582 extraction trust, or #589 permissions. Policy/Discovery Engine unchanged absent repeated causal process evidence.
