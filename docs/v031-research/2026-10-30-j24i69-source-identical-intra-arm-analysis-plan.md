# J24I69 — Source-identical within-arm temporal placebo (analysis plan)

**Status: bounded, explicitly POST-HOC scientific follow-up; NOT a prospective blind preregistration.** This plan was written after an exploratory inspection of the original J24I65 artifacts had already revealed some within-arm variability. No claim of unobserved outcome or statistical significance is authorized. The plan precedes the new reusable instrument, full admissibility checks and detailed summary.

## Authority and baseline

- Released `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0, revision 24.
- Research source #865 demonstrates that ZIP co-drift is not a reliable per-cell CMPCT timing correction. #835/#837 provide **three original** GitHub Actions A/B/B/A attempts whose **product engine and benchmark source are identical** between labels. Original benchmark results and all historical failures remain binding.
- #819/#821/#825 already own separate same-source process/Builder attribution. #238 and #715 own new A/A experiment construction. This lane **only reinterprets already-recorded historical four-sweep medians**, creates no new engine/workload and touches none of their mutation surfaces.
- The shared Discovery Engine cache and current release/benchmark policy are untouched.

## Primary question and bounded decision

Can the *same arm* (base A vs base B; candidate A vs candidate B) move across the existing **>5% AND >3ms magnitude** envelope, on exactly unchanged source and identical measured archived bytes, inside one original hosted ABBA execution? This is a same-variant temporal-placebo diagnostic; it **does not** use the release gate for approval, replace the official base-vs-candidate comparison, or prove any mechanism of noise.

Fixed primary evidence set, no selective exclusion:
1. #835 first original ZIP `cmpct_p835_firstfailure_12981944713.zip`; SHA-256 `cf20ded12b7e5b6348a9fc272cadc7565dc4e76982e1760fce674b1b2e7e1598`.
2. #835 second original ZIP `cmpct_source_identical_835_12986955317.zip`; SHA-256 `aedd2d6150746f5c6bcef4b0e8a41af5ed5f5c9f9fbb0c3ba78b54da59bbd1ee`.
3. #837 original ZIP `cmpct_source_identical_837_12988780098.zip`; SHA-256 `1d43e55fb359db5ec779607d9da25508efe61bbaa6d5ba5c5665d8819999490b`.

These originals are available in public provider Actions artifacts and a separately retained J24I65 bundle. The instrument must admit **original provider ZIP bytes only** by exact SHA. No provider hashes may be edited after observing a disappointing result. Whole-archive byte identity *within a trial* refers to the reported frozen archive sizes, not a full per-invocation physical archive SHA: the r24/ZIP summaries do not record those complete hashes.

## Analysis / honest comparison boundary

- Read exactly four `base-a.json`, `base-b.json`, `candidate-a.json`, `candidate-b.json` medians from each original ZIP; validate all eight canonical corpus labels, both modes, two engines and both operations.
- Confirm corpus source and logical sizes, reported archive byte sizes, schema, repetition count 7, finite positive timing values and no duplicate ZIP entry names before scientific computation. Inspect source receipts and environment information when available. A provenance mismatch invalidates the trial.
- For each engine and each source arm, compute signed late-minus-early milliseconds, signed percent of the earlier median, and magnitude predicate `abs(delta_ms) > 3 AND abs(delta_pct) > 5`.
- Retain **all 3 × 2 arms × 2 engines × 8 corpora × 2 modes × 2 operations = 384 within-arm effects** and separate CMPCT (192) from ZIP (192); do not treat 384 correlated cells as independent trials.
- Recompute the 32 official CMPCT base/candidate median effects per original trial using the two A/B arm medians. Preserve every official negative.
- Report how many material placebo shifts occurred in each of the three trials, the location and sign, whether they coincide with an official red, and the subset of 32 candidate/base cells where both arms are temporal-placebo neutral.
- No pooling across CPU models for a causal parameter, no posthoc statistical significance, no subtraction-based correction, no adjusted comparator or release threshold.
- Adversarial refusal: changed provider ZIP digest, malformed/missing/duplicated JSON, nonpositive or non-finite timing, mismatched corpus/archived bytes; strengthen the instrument rather than excluding hostile cases.

## Scientific criterion and disposition

A valid magnitude crossing in **either** arm establishes that a source-identical within-run stage can move at least as much as the official numerical threshold. It does **not** establish that any official red is "noise"; it cannot bound unknown effects between sweeps. Zero crossings would narrow the temporal-placebo explanation for these three specific runs but not exonerate other runs. This result should retire yet another attempt at post-hoc gate correction rather than motivate repetitive CI.

## Cost, limitations and counterfactual

Only archived JSON/ZIP arithmetic: zero new product archive bytes, 0 new host benchmarks, no CPU/wall/RSS measurement of CMPCT, and no Reader/Writer/native/format/ABI modifications. The original seven per-operation samples are not present in the four sweep summaries; **a median of seven is not a raw repeated-sample distribution**. CPU frequency, process state, temporal timestamps and contention are not established by this data. The cheapest prospective lesson, if the bounded test is decisive, is to capture the raw ordered per-operation samples and native/runtime identity in a future *separately-owned* instrument, never change official gates from these diagnostics.

**Stop this lane after a complete, auditable verdict; return to the representation / product frontier.**
