# O33 — Canonical hardlink Reader cold-open CPU/RSS: decisive research result

**Date:** 2026-10-24 UTC. **Status:** RESULT-BEARING RESEARCH; product owner PR #385 remains independent draft. No product files changed by O33.

## Exact evidence and source custody

- **Source control:** PR #381 / O28 `9c9cecc6c21dc741e57188076ea43dc0ede6425b`, Reader Git blob `c7850c08c7bb27563955c6e2294b8c17c140d0a2`.
- **Source candidate:** PR #385 / O31 `0edb7bc6e832deb1b403fea50c36e655da9844fd`, Reader Git blob `de9accf6607aca7cf70dfe71d7b299a02e298a2d`.
- **O33 experiment implementation:** `be188e94e9b2f85c4559ba1b789c5e85a9c69f3a`. Scientific predictions frozen first at `ce842827e11df9454c412c3982179ef0c4e0714a`. O33 modifies no product code. Each interpreter asserts historical/candidate Python module **and native codec** physically originate in the pinned selected source.
- **Hosted run:** [GitHub Actions #40137532970](https://github.com/FCMO-AI/.CMPCT/actions/runs/40137532970), **SUCCESS** with actual measurements.
- **Raw artifact:** [#12577906960](https://github.com/FCMO-AI/.CMPCT/actions/runs/40137532970/artifacts/12577906960); complete `o33-raw.json` SHA-256 **`b02bff9a5dc941da4ed544ce9b5f632fc77329204d5ebb5b1b4af424b63a9ac3`**. The artifact includes the SHA-256 of all six physical archives, raw observations, and native materialization/source receipts.
- **Semantic controls:** 15 source-bound inherited O25 and O31 pytest checks passed before timing.
- **Platform:** one Ubuntu 24.04 hosted runner, Python 3.11. Fresh independent subprocesses, eight observations per exact source and each of six shapes, alternating ABBA/BAAB; median observations below. The same physically signed archive file was passed to both engines for each row.

## O33 scientific decision — material owner-map CPU debt observed

| Authenticated r24 checkpoint | Historical constructor median (ms) | O31 constructor median (ms) | O31 / O28 | Candidate post-constructor RSS (KiB) | Decision |
|---|---:|---:|---:|---:|---|
| plain, 512 regular rows | 2.213 | 2.184 | 0.987x | 24,542 | near neutral |
| fanout, 512 rows | 2.510 | 2.867 | 1.142x | 24,586 | +0.357 ms, below absolute triage floor |
| chain, 512 rows | 2.469 | 2.793 | 1.131x | 24,572 | +0.324 ms, below absolute triage floor |
| plain, 4,096 regular rows | 6.797 | 6.937 | 1.021x | 26,196 | near neutral |
| **fanout, 4,096 rows** | **9.083** | **12.091** | **1.331x** | **26,550** | **MATERIAL TRIAGE REGRESSION: +3.008 ms (33.1%)** |
| chain, 4,096 rows | 8.847 | 11.618 | 1.313x | 26,750 | +2.771 ms (31.3%); relative red, just below prereg absolute 3ms boundary |

**Do not round the chain to a passing result:** it is an economically significant directional warning even though it did **not** cross the combined preregistered threshold. O33's original hypothesis that canonical owner mapping would be below 10% or 3 ms at 4,096 entries is **falsified on fanout**. This research win is an accurately attributed **negative product-performance observation**, not release authorization.

The complete fresh process medi​​an on fanout 4,096 went from **76.830 ms to 79.922 ms** (about +4.0%). The constructor CPU from **9.180 ms to 12.204 ms** tracks the constructor wall difference and disfavors external I/O/cache as the sole explanation. The 4,096 plain control stayed nearly neutral (+0.140 ms), strongly suggesting that the exported cost is in **per-hardlink target canonicalization/lookup**, not a fundamental all-file dictionary allocation. That is a causal hypothesis requiring targeted profiling, not yet an exact measured function-level attribution.

The candidate showed **no material RSS delta** under the prospectively defined +10% AND +4 MiB triage threshold. Median fanout post-constructor VmRSS actually measured 26,550 KiB vs 26,580 KiB historical (−30 KiB, noise-scale), and HWM incremental readings 2,950 KiB vs 2,970 KiB historical. Such readings do not demonstrate zero memory overhead inside construction or universal memory safety.

The source-specific code basis: O28 reuses the validated raw path in `node=link[0]`; O31 for every hardlink executes `canonical_logical_path(link[0])` and resolves via `canonical_names.get(target_key,link[0])`, even when the target already matches a canonical validated exact-name row. Testing a **safe fast-path conditional** (only for source-owner exact-string hits after validating all logical paths and preserving unsafe-target rejection) is a plausible bounded engineering next step for owner PR #385. Do **not** bypass canonicalization for targets whose lexical spelling is not an exact admitted row, or drop eager graph and post-open mutation checks. An owner implementation must still prove the O29 backslash target, canonical collision, implicit-parent, cycle, namespace and O25/O27 adversaries remain green.

## Counterfactual / BONK result

One cheap A/B on 4,096 *plain* and 4,096 *fanout* (with exact historical source and authentic archive semantics) would have been sufficient to expose the exported CPU cost; the chain and 512 cases provide transfer/noise structure. This was prospectively recognizable from the new per-edge canonical normalization in the source diff. It does not justify changing global discovery policy from a single episode.

**Do not relabel the hosted workflow's SUCCESS as a product-performance PASS.** SUCCESS means the scientific comparator ran and honestly preserved a negative. The official r24 parity on *O31 owner HEAD* [#40135788585](https://github.com/FCMO-AI/.CMPCT/actions/runs/40135788585) actually executed ABBA and concluded PASS/0 confirmed regressions, but its monitored create/extract size/time matrix is not an ordinary large-hardlink cold-open measurement. These results therefore are not contradictory. They probe different user costs. O31 installed package [#40135788544](https://github.com/FCMO-AI/.CMPCT/actions/runs/40135788544) remained administratively SUCCESS with build/install/compatibility jobs SKIPPED and is not shipping-wheel evidence.

## External cost/limits and handoff

This court covers one Linux host; fresh process includes import/startup but not guaranteed cold Linux filesystem page-cache. One physical RAW record per archive isolates index graph semantics and has no claim about compression/create throughput or diverse codecs. Neither direct target-canonical fast-path nor whole product memory/throughput was changed or retested in O33; source owner PR #385 must own engineering repairs. Preserve exact O33 negative when evaluating the stronger canonical/implicit-parent product capabilities; do not remove those fixes merely to make the intermediate old-code ratio green.

**Next strongest executable action:** product owner may preregister a small alternative that reuses already-validated exact-name rows on common hardlink edges, preserves general canonical mapping for noncanonical signed targets, retains extraction-time mutation checks, and measures it against BOTH exact O28 and O31 on these same six corpus hashes and new hostile mixed-separator held-out cases. Accept only if hardlink canonical compatibility and all inherited security gates remain, and CPU/RSS + official release comparators independently meet release law. If a safe fast path cannot pass, retain O31 with explicit cold-open debt and investigate representation ownership more deeply.

**Disposition:** O31 capability improvement remains scientifically valid from owner product courts. O33 causal cost hypothesis advanced; sub-10% fanout prediction falsified; memory-regression hypothesis not supported at observed scale; code integration/release **blocked pending independent product-owner resolution**. Discovery STATE cache and policy untouched, because neither is a lock or authority for this narrow episode.
