# J24G10 first hosted run — failure preserved before repair
Date: 2026-10-28 UTC
Run: https://github.com/FCMO-AI/.CMPCT/actions/runs/40664533752
HEAD: `9df60a003af2e6314dd22ab84988661f36b2311b` (Reader blob `690ab86564c9f2989ed4af0879167d8394140dd0`).
Status: **FAILURE**, not positive candidate proof. The original 11-section PR evidence gate also FAILED until the full dossier was supplied; inherited J24G09 source-locked court FAILED because it requires exactly the unchanged parent Reader. Neither frozen evaluator was weakened.

## Actual first-run numbers (three alternating repeats)
- Alternating 16,400: #661 original 278,665 decoder calls / median 1941.964 ms; candidate **16,401** / **180.159 ms** (10.78x); unbounded set oracle **16,401** / **134.635 ms**. Genuine signed Builder physical archive was the same.
- Deterministic randomized 16,400: #661 **278,665** / **1975.511 ms**; candidate **16,401** / **177.517 ms** (11.13x); unbounded set **16,401** / **136.903 ms**.
- Uniform AP: 123.905 ms parent, 129.127 ms candidate; flat 1024: 7.602 ms parent, 7.683 ms candidate; valid genuine Writer rename: **0.147274 ms parent vs 0.194012 ms candidate (+31.73%)**, violating the frozen +25% ordinary guard. The court rejected the result appropriately and no success JSON was produced.
- **Critical measurement falsehood identified on review:** the SQLite connection kept an open transaction. Reported physical DB size **8,192 B** was not the persisted proof size; uncommitted B-tree pages could live in SQLite's cache/journal. The 'disk-backed bounded-memory' claim is therefore **NOT ESTABLISHED** by this run.
- The candidate-only close instrumentation was a second timing confound: its `unittest.mock.patch.object` setup was included inside the candidate timed interval but not the historical/oracle intervals; on a 0.15 ms valid baseline that asymmetry can account for a material part of the +31.73% result. This is a measurement explanation, **not** permission to relax the 25% gate.

## Corrective actions required before another positive claim
1. Physically COMMIT spill rows and cross-check from a second SQLite connection before crediting file bytes; retain exact unsigned-key oracle.
2. Move proof.close instrumentation outside the timer for all comparator paths, with the same source and workload; add more paired repetitions to tiny valid-control medians while keeping the **identical +25% gate**.
3. Preserve first original failure and original parent exact source; compare new result at a new SHA with fresh CI rather than relabeling old red as green. Analyze resident/temporary memory and per-chain materialization separately before promotion.

This is a prospective diagnostic correction to the scientific instrument and storage durability, not a new or weakened release policy.