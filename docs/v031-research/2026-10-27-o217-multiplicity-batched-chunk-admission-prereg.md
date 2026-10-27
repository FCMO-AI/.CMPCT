# O217 — multiplicity-batched S_CHUNKS reference admission (prospective, science only)

**2026-10-27 UTC. Preregistered before O217 instrument / hosted observations.**
Exact parent: O216 PR #570 `6989b25640be2c82436bb77ec545dd15816f698b`, on J24C02 PR #569 `c5e13bb3fbb4cdade8b64246658ce7c7818de41f`. Historical released `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0/r24 unchanged. The historical `validation.py` owner blob is `51c2849061f99a4afeddb7666956b24566ce7de0`; O216's source-exact negative and 19 hostile controls are the inherited strong control. **Do not mutate any owner code, release law, historical evaluator or receipt.**

## Primary question and causal claim

Does shifting **repeated physical-reference validation** from a per-reference Python loop into a C-backed multiplicity histogram materially reduce the authentic full-Reader cold-open cost while retaining strict rejection of *every* malformed reference and total declared-length mismatch?

The current strict O215 validator checks each chunk ID, constructs diagnostic labels, and totals its referenced blob length. O216's exception-only fast path removes many per-ref diagnostics but still incurs +5.3421 ms / 6.232x at 65,536 references, and +21.3570 ms / 6.663x at 262,144 references versus a deliberately unsafe bypass oracle (PR #570, Actions #40451829700). This is **not** a license to bypass checks: O216's best result remains nonpromotable. Every serialized entry must still be inspected; a multiplicity histogram changes which interpreter owns the work, not the proof obligation.

## Proposed mechanism, stronger control and confounders

For exactly `K_FILE/S_CHUNKS`, require the same descriptor list shape; scan **all** IDs for exact built-in `int` (reject bool aliases), and on any unusual type delegate to the **entire original validator** to retain original first-invalid diagnostic/class. Use `collections.Counter(ids)` to count multiplicities using the C-backed counter engine; check the minimum/maximum of **all unique** IDs. If a boundary is bad, delegate to the entire original validator so the exact indexed diagnostic is preserved. Otherwise compute `sum(blobs[idx][1]*count for idx,count in histogram.items())`; reject on the original exact total-size predicate. Every other storage/kind retains original behavior. No unguarded, sampled, probabilistic or unchecked read admission is eligible for product code.

Strongest simpler controls: (A) the **unchanged strict** J24C02 validator; (B) **O216 exception-only** strict inline path, which is already ~4x faster than (A); (C) explicitly unsafe no-check oracle, lower-bound timing ONLY. The candidate must beat (B), not just (A). Possible alternative explanations include CPython version sensitivity, subprocess/load noise, highly compressible repetitive MessagePack references, OS disk caching, and repeated refs atypical of Builder output.

## Preregistered test / evidence tier

Tier: source-bound scientific A/B experiment on **authentic installed CMPCT Reader** (not release/product acceptance), on one Ubuntu runner with identical authenticated r24 bytes across arms. Reuse frozen O216 independent archive constructor and the full 19 original semantic controls; add held-out boolean/float/string/negative/out-of-range/late-invalid and multi-blob valid/invalid checks. Run at least 3 randomized cycles of paired independent subprocess arms, report raw wall/process CPU timings and median-of-process medians. Shapes: repeated 1/4096/65536/262144 refs, plus at least two high-diversity/unique-ID shapes within bounded archive size. Include observed process max RSS or another correctly attributed peak/unique histogram allocation diagnostic; if not feasible call memory unmeasured. End-to-end times exclude fixture construction and startup; retain it separately when claimed.

**Prediction:** for 65,536 and 262,144 repeated refs, batch count is >=1.25x faster than **O216 exception-only** per-reference fast, and still rejects all checked malformed cases identically. Plausible negative: type scan + Counter overhead consumes the gain, or high-uniqueness memory/CPU regressions erase useful generic product value.

**Kill/narrow:** any strict acceptance, rejection, exception class/message mismatch kills the candidate. If the high-count gain against O216 is <1.25x or if high-distinct input produces large memory/latency debt with no bounded admission that can be prospectively selected, retire or narrow this multiplicity formulation. Even if mechanism wins, no product promotion until same-head 3-host reader composition, real corpus cardinality distribution, peak RSS/temp-allocation, extraction/index/recovery/economics and unchanged full release parity are certified. Do not tune a size/uniqueness threshold to this corpus after seeing results.

## Externalities / honest limitations

`Counter` may allocate O(number of distinct IDs) extra objects and perform two full input passes. All-reference validation is necessarily Omega(N) under r24 arbitrary index entries unless separately authenticated summaries change the proof boundary; this experiment only seeks better execution ownership. More copies of the decompressed index are forbidden as an uncharged win. No change to format, payload, index SHA, filesystem path policy, product versions or public claims. O216 and J24C02 owners retain implementation and integration authority. Frozen negative comparisons must remain visible.

## Decision unlocked and counterfactual

A decisive win with bounded cardinality costs justifies proposing a reversible strictly equivalent batch validator to owners; a negative retires the Python multiplicity strategy and redirects to native/bounded-vector or authenticated representation/proof changes. The cheap prospective discriminator is repeated-vs-distinct cardinality plus exact semantic first-invalid equivalence, not merely a favorable single repeated-ID microbenchmark. No Discovery Engine policy change is presupposed.
