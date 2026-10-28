# J24G08 — O10R generation-depth ceilings × J24G06 failed-ancestry cache: recovery compatibility

**2026-10-28 UTC. Preregistered before experiment code, run, and outcome. SCIENCE ONLY / independent cross-owner composition falsifier.** No Reader/Builder/Writer/format/validator change; no merge/release authority.

## Provenance and independent owners
- Product cache owner [#650](https://github.com/FCMO-AI/.CMPCT/pull/650), exact source commit `10a6bc150cfa0ceb8608ee826dc09650ca3f4e3d`, `src/cmpct/reader.py` Git blob `bead2ea6a09a6daaadc3ec2389cfb8853e3dd172`.
- O10R signed-generation ceilings owner [#365](https://github.com/FCMO-AI/.CMPCT/pull/365), exact source commit `54c998200b1908b696ade049fe94df71a736c284`, Reader blob `2402721258531a56cfa2a53dcbd81874fd6c1f76`.
- [#655](https://github.com/FCMO-AI/.CMPCT/pull/655) measured cache cap cliff, N=16,384→16,400, in authentic Reader with unchanged logical recovery. That issue's owner remains separate: this experiment tests a *different* proposed replacement family (resource ceiling) before code-level composition.
- Canonical `main` v0.30.0/r24 unchanged. Current discovery STATE is an outdated index, not authority. No concurrency protocol was present at the two examined source refs.

## Primary question
Can an O10R-style `CMPCT_MAX_DELTA_DEPTH` stop the #650 ancestry work cliff **without violating revision-24 fallback to an older valid committed footer** after an invalid, hash-authentic orphan tail?

## Prediction and mechanism
O10R `_index_from_footer` raises `ResourceLimitError` at `depth > limits.max_delta_depth` while walking the *first* newest orphan candidate. That exception escapes `_latest_generation` before older committed footer candidates can be examined. With max depth 2, an orphan chain of 4 consecutive SHA-valid deltas lacking a checkpoint should therefore prevent recovery of an existing first-party Builder→Writer checkpoint, whereas #650 caches the failed ancestry and recovers it. The same distinction should hold with default limit 128 and a 140-delta orphan tail. O10R's legitimate 3-deep signed generation should still trigger the configured limit (a positive control demonstrating the guard really works).

## Same-input, same-host direct-source court
1. On Ubuntu, build *once* with the unmodified installed #650 Builder and `append_rename` Writer, retain the produced physical .cmpct archives, SHA256 and genuine selected footer.
2. Install exact #650 and #365 sources in **separate venvs** and run the same physical input files in separate processes; assert each installed Reader byte-identical to its Git blob.
3. Five cases: (a) ordinary committed one-delta control, (b) valid two-delta chain with max depth 2, (c) orphan 4 with max depth 2, (d) orphan 140 with default 128, (e) 140 *flat* SHA-valid deltas with max depth 2. Also valid depth-3 under max 2 to verify limit activation. Count real decoder invocations and preserve raw responses.
4. For successful cases assert checkpoint position, generation depth, exact member SHA256, read_range, verify and archive SHA; for failures record exact exception class/text, not only exit status. Retain artifacts, source receipts and raw logs including unexpected results.

## Strong simpler controls / alternatives
- A cheap depth limit is a valid deliberate fail-closed resource policy for *legitimate over-limit* journal chains. The question is **not** whether such refusal should be removed; it is whether a malformed/aborted tail can force the same refusal before an older valid checkpoint can be selected.
- Flat orphan footers isolate footer *count* from linked ancestry *depth*.
- `#650` is the cache-only fallback control; `#365` is the bounded-source control. Neither is a proposed merged product.
- A global bounded decode-work budget that raises explicitly, or compact proof/certificate of invalid chains, are competing mechanisms; this court does not pretend either is implemented.
- An aggressive limit by default may prevent O(N²) work but fail availability. No silent data loss or downgrade of integrity is permissible.

## Disproof / decision
- **Confirmed conflict** only if original #365 raises on orphan-4/orphan-140 while cache-only #650 recovers the same exact committed generation and flat-orphan control remains readable on #365.
- **Falsified** if #365 also preserves fallback under the same constraints, or both fail under a different shared contract.
- **Ambiguous/infrastructure** if source/package identity, shared archive SHA, generation provenance, or exact test execution cannot be proven.
- If conflict confirmed, do *not* mechanically graft O10R's raise into #650. Design a bounded, evidence-backed policy that separates authenticated committed over-depth generation from failed orphan ancestry while preserving valid checkpoint recovery. Prefer simplest no-regression guard; full-product benchmark only after a credible composition.

## Evidence and scope
This is a lower-rung product-source **scientific** experiment. It establishes neither complete resource bounding nor full external-mutation safety, memory economics, porting behavior or release eligibility. No frozen benchmark/evaluator/threshold is weakened. Record negatives exactly. The experiment should terminate its narrow question without opening a third near-duplicate cache implementation.
