# J24I73 — source-identical algorithm, research import-cone ablation

Date 2026-10-31 UTC. **Preregistered before the instrument and before observing its hosted result.** Research only; product credit 0.

## Authority, ownership and non-duplication
- Canonical CMPCT v0.30.0 main `80c358f8824ec1b20d349c92ed94c898090969b0`, r24. Child of #875 frozen head `f8ef04c149a09f62fc3d5cb9dfdb006b439b5efc`, same original Reader blob `29a8be64f3acfb027750351c6a567fd82cf7dc97`. Historical #875 H1 and H2 outcomes are not reclassified.
- #823 owns experimental OwnedCMPCT semantics, #853 DELETE-only control, #871 physical A/B generation, #875 fresh-process experiment. This is an independently preregistered **out-of-tree, algorithm-identity-ablation** question: no change to any owner-owned Reader/Writer/benchmark/evaluator/source.
- #574 owns shared discovery state; do not edit it. Existing #875 J24I72b descriptive import split is a *control*, not adequate attribution by itself.

## Primary causal question
Can a minimal, dynamically synthesized import cone (copying exactly the inherited `admit`, `reference`, `factored`, `owned_factored_fresh`, and `OwnedCMPCT._index_from_footer` function ASTs unchanged into a throwaway module) remove the ~35ms research-helper import penalty without changing decoded r24 semantics, and thereby narrow the gross full-process cost of owned A against public checkpoint B? Unlike #875's descriptive medians, this modifies the **research import-graph boundary** while holding the selected replay algorithms source identical.

Strong controls: same frozen physical archive A (63 authentic DELETE) and B (same signed index, checkpoint only) produced by #871 source; actual public Reader on A and B; original heavy Owned on A and B; minimal Owned on A and B; Python package/runtime and process interpreter fixed. Independently verify index/member SHA, Reader route, archive bytes, root/ancestry and replayed signed fsmeta. No unexplained errors or omission of workloads.

## Predictions locked before result
- **H1 import-cone effect:** on **both** Ubuntu 24.04 and Windows 2022 at N=8192, minimal-Owner import-only child-class median wall is at least 10ms below original Owned child-class import median, with identical code ASTs for the five transplanted methods and unchanged actual CMPCT core Reader source. Fail if either OS misses the threshold. This is about import cost, not product gain.
- **H2 net-gross crossover (strong):** on **both** hosts at N=8192, independently measured gross **minimal-Owned-A / Public-B** (process start through exit, including SHA proof) must be <= 1.20. Fail if either host exceeds. Record A/B and every raw sample without threshold adjustment. This does NOT undo #875's gross Owned-A/Public-B H2 failure.
- **H3 semantic identity:** every minimal vs original Owned vs public index, count, selected member raw SHA, signed delta_depth and root checkpoint must agree; malformed/adversarial perturbation must fail both original and minimal with identical normalized outcome when feasible. Any mismatch invalidates the performance claim.
- Baseline cold-run original #875: H1 0.4163x/0.4556x for original Owned A/public A, H2 1.3941x/1.3239x for original Owned A/public B (Ubuntu/Windows). Do not use these historical medians as this court's primary controls; execute same-runner contemporaneous controls.

## Cheap decisive rung / scientific hygiene
Generate original #871 fixture at N=8192 only; in one hosted job per OS use same official repository plus exact #853 reference checkout. Before running fresh process trials, synthesize an **ephemeral** minimal module from AST source extracts of the exact inherited helper functions and private Reader method, using checked source files, not translated/reimplemented heuristics. Rewrite only imports and the base-class binding (direct CMPCT instead of FactoredCMPCT, whose only override is the same method now included). Maintain original fallback, validation and exception semantics. Record SHA-256 of the temporary module and AST hashes for each algorithmic function and constructor, compare to donors before measurement. Do not optimize the actual algorithm.
Use 8 balanced/reversed subprocess observations per Reader/physical A/B and 4 import-only observations per Reader, and strict JSON independent referee reconstructing medians. Parent wall includes interpreter launch and exit. Child class import, constructor CPU/wall and RSS separately. Judge H1/H2 only from per-run medians, never subtraction of unrelated medians. Source mismatches invalidate.
No expensive official matrix; product, packaging, cross-platform installed wheels, cold disk, multiwriter and native ABI are not covered. 
## Disproof/kill and escalation
If ASTs change, signed identity differs, or a Reader admits corrupt input differently, stop attribution; fix the test or retire the approach. If H1 fails, imported dependencies are not cheaply isolatable this way. If H1 passes but H2 fails, pure helper imports cannot explain the crossover; investigate actual process/path/constructor cost only if new causal evidence warrants. If H1/H2 both pass, hand a source-ownership-controlled integration option to #823, never merge a research helper as product.
Preserve every negative. No format/version/ABI/release change, no evaluator or workload weakening. This is research evidence, not a release vote.

## Release/quality ratchet
A PR is draft and remains non-promotable unless source attestation, independent corpus integrity, exact-head physical hosted tests, security/semantics, official CI checks and responsible owners agree. Never count successful administrative CI with skipped scientific work as a passing experiment.
