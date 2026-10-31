# J24I72 — Fresh-process economic boundary for the genuine 63-DELETE owned Reader

**Date: 2026-10-31 UTC. Status: prospective preregistration; not product, release, or performance-gate authority.**

## Source, claim, and concurrency

- Published base is CMPCT v0.30.0 / r24 at `main@80c358f8824ec1b20d349c92ed94c898090969b0`.
- This isolated research child starts from #871 exact `df2edd9d61a782616d7de1f3c054841e9ebb9eb2`; #871 owns original same-file warm A/B/C and the unchanged Reader source `29a8be64f3acfb027750351c6a567fd82cf7dc97`.
- #853 exact `129edec976efe8bb604584517de39553487fec34` owns original public Writer and DELETE-only control; #823 owns private fresh-decoder Reader; #362 previously tested different O7 4,096-RENAME sources in a fresh process. This question is **not** a replication of O7, nor a rewrite of #871.
- No edits to source Reader/Writer/Builder, format, native codec, test expectations, official benchmark, release thresholds, or shared `docs/discovery/STATE.json`. #574 owns that state.

## The material question

#871 measures genuine full Reader opening in a **long-lived imported process**, under the same physical r24 A (63 DELETE operations) versus B (identical logical state, newly written checkpoint), across released public, private factored, private owned-fresh-decoder, and simpler one-pass DELETE-only readers. It reports a marked warm owned win over public A and a narrow 1.31–1.46x disadvantage to public B. A one-shot Python user pays interpreter startup, package and dependency imports, reader opening and process exit. Can the private owned and DELETE-only optimizations still change *gross fresh-process* economics, or is the apparent speedup fully dominated by startup/import?

## Hypotheses and precommitted fork

- **H1 (cold net benefit):** the owned Reader opening A is at least 5% and 3ms faster than public Reader opening A in parent-measured whole-process wall on each Ubuntu/Windows host at N=8,192. This is a descriptive research materiality test, **not** the official release timing gate and not a claim of future product behavior. Fail H1 if either host does not cross both conditions.
- **H2 (checkpoint crossover):** owned Reader on A is at most 1.20x gross full-process wall of public Reader on B at N=8,192. Fail if >1.20x on either host. Retain the historical warm ratio and every negative split by OS/size; no post-hoc reclassification.
- **H3 (process import cost):** standalone import-only process cost is a material share of the whole-process result. Report separate import, constructor and gross timings; do **not** subtract separately measured process medians and claim causal isolation from the subtraction alone.
- **Strong simpler controls:** released public Reader on A and B; DELETE-only from #853 versus general owned Reader #823; import-only child for each variant; and same physical archive B with identical final logical state.
- **Competing explanations:** OS scheduling and process spawn, import graph asymmetry, filesystem cache, antivirus/indexing, native library loading, CPU thermal variation, source mix-up, or the physical A/B inputs differing from the original #871 court. An imported-class time benefit is not necessarily a CLI or native-handler benefit.

## Cheapest decisive experiment

Run source-locked actual public Builder/63-DELETE Writer `make_court` from #853 without modifying it. For each N=4,096 and 8,192, create A and checkpoint B **once** per OS, preflight both, verify exact index and member SHA identity through all four readers, record original complete archive SHA/size. Then execute **at least six independent interpreter subprocesses for every 4 Reader × A/B cell**, with balanced/reversed rotation, same Python interpreter and environment, no concurrent benchmark children. A child imports only the selected Reader variant, opens one physical archive, confirms member count/index and selected payload SHA, closes and emits timing; parent separately records whole-process wall including startup and exit. Add at least three import-only children per variant. Report every raw observation, median and per-iteration/block dispersion; child process CPU and Linux RSS/HWM where available, separately from Python heap tracemalloc. Never use warm result as a cold one.

The initial rung is a dedicated original CI two-host controlled research court. Third-host macOS is useful but optional; if enabled it cannot retroactively become part of the two-host preregistered H1/H2 decision. Do not run the expensive official r24/ZIP matrix for this distinct non-product mechanism.

## Required validity and disproof

Any source Git blob mismatch, invalid physical A/B, divergent logical index/content, wrong selected Reader route, incorrect reference source, nonzero process exit, JSON provenance discrepancy, failed preflight or inconsistent exact SHA invalidates that case. Import-only and active children must execute the same installed package. Defective/missing metadata is not cured by changing an evaluator or fixture. Strict independent verifier must recompute medians from raw measurements and reject at least one forged source receipt, timing median, artifact SHA and archive-byte claim. CI administrative green without the material jobs is **not** evidence.

## Costs, semantics, and follow-through

Record stored A/B bytes, materialization time outside timing, raw wall+CPU and per-child RSS/HWM, total subprocess wall and provenance; record omitted cold-disk hardware flush, true native C/Rust CLI, publication/zip export, multiwriter concurrency, full filesystem metadata and 128MiB+ sparse cases. The result is **research**, never a product benchmark, source promotion or release. A net benefit changes the next productization question toward source-safe multi-mutation ownership; a disappearing benefit narrows one-shot Python leverage but does not retire warm long-lived or native-handler usefulness. Preserve negative data and communicate to #871/#823/#853 without overwriting their branches.
