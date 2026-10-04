# CMPCT v0.30 efficiency recovery directive

Status: **TEMPORARY NORMATIVE PRIORITY — ACTIVE UNTIL EXIT CONDITIONS ARE PROVEN.**

This directive changes **work allocation**, not benchmark semantics, release thresholds, archive semantics, safety law, or scheduled-task configuration. It exists because the current v0.30 candidate has a real compression win while carrying unacceptable end-to-end execution debt. Until the exit conditions below are satisfied, efficiency recovery is the dominant CMPCT engineering mission.

Read together with `AGENTS.md`, `docs/AGI_ENGINEERING_STANDARD.md`, `docs/RND_DOMINATION_RUBRIC.md`, `docs/PERFORMANCE_RELEASE_GATE.md`, `docs/BREAKTHROUGH_REHABILITATION.md`, `docs/V030_RELEASE_LOCK.json`, and the v0.30 coordination ledger. Where those documents define stricter correctness, evidence, safety, locality, recovery, portability, or release rules, the stricter rule wins.

## 1. Why this directive exists

The current candidate has earned material compression gains and must not optimize them away merely to make a timing graph green. At the same time, a compression system that obtains smaller archives by spending excessive CPU, wall time, I/O, memory, repeated scans, redundant transforms, losing auditions, or expensive reconstruction is not the product CMPCT is trying to ship.

Recent exact-candidate evidence has already isolated real execution debt:

- promoted-product create and extract timing remain red under the unchanged v0.30 runtime ceilings;
- whole-process-tree RSS is not the current primary blocker;
- ML/G04 create + extraction and Logs extraction are known material owners in the current evidence;
- the 15-workload compression/generalization matrix is strong, but it is not by itself sufficient evidence that CMPCT has regained broad real-world efficiency;
- locality is green but close enough to its bound that speed work may not simply export cost into selective reads;
- current release authority still requires strict fair external competitor evidence, including ZIP/Deflate and Zstd-19.

The engineering response is therefore not “make one benchmark a little faster.” It is to remove the architectural causes of wasted work until the actual product is again fast, resource-efficient, and broadly competitive.

## 2. Dominant-priority law

While this directive is ACTIVE, **every discretionary material CMPCT activation should primarily do one of the following**:

1. remove, fuse, avoid, parallelize safely, or move to a more appropriate implementation boundary a measured end-to-end cost;
2. causally identify a large unresolved owner strongly enough to choose the next architectural intervention;
3. redesign search/admission so expensive losing candidates are never built when exact or safely bounded futility can reject them earlier;
4. rehabilitate a proven compression mechanism so its byte gain survives without unacceptable create/extract/CPU/I/O/locality cost;
5. build or strengthen honest real-corpus/competitor measurement needed to prove that the product is actually efficient;
6. close a correctness, recovery, portability, custody, or platform prerequisite that is genuinely blocking the above work or the final proof of it.

Work that does not materially advance, measure, unblock, or falsify this efficiency-recovery mission is lower priority until the exit conditions are met.

This is intentionally stronger than “performance matters.” Efficiency recovery is the default allocator for Forge work and, while no primary Foundry thesis is active, it also controls where new research attention goes. A new Foundry thesis during this interval should require a credible path to attack a broad efficiency/representation cost or another release-critical bottleneck; do not create unrelated novelty merely to keep Foundry busy.

Safety, exactness, integrity, recovery, hostile-input handling, evidence truth, and required portability work are never skipped in the name of speed.

## 3. No micro-optimization drift

Local optimization is allowed only when measured evidence shows that the local owner can plausibly change the product decision, cross a gate, or remove a material fraction of a real end-to-end cost.

Do **not** spend the primary budget on endless tiny edits such as isolated branch shaving, cosmetic Python cleanup, one allocation removed from an insignificant phase, or benchmark-specific special casing while a D2/D3/D4 owner dominates the wall clock.

Prefer, in order of causal fit rather than novelty:

- **D2/R2:** eliminate duplicate scans, hashes, materializations, authentication, parsing, reconstruction, process setup, IPC, copies, and repeated semantic ownership;
- **D3/R3:** exact futility, lower bounds, proof-directed admission, candidate reuse, branch-and-bound, and tournament/search redesign that avoids constructing losers;
- **D4/R4:** physical-layout or representation-boundary changes when the current architecture itself exports unavoidable work;
- **R1:** only when the measured local budget is large enough to matter.

Two consecutive low-yield attempts in one local family without a newly measured sufficient owner should trigger escalation or retirement under the existing Forge saturation law. Do not polish a losing floor.

## 4. Product-wide efficiency boundary

Measure the complete system, not a convenient codec kernel. For creation, extraction, verification, selective access, and representative recovery paths, record where available:

- wall-clock latency and throughput;
- process-tree CPU time (user + system);
- peak whole-process-tree RSS;
- bytes read and written;
- temporary-file / scratch I/O;
- process creation / IPC / serialization cost;
- hashes, scans, sorts, candidate builds and compression calls;
- syscalls or equivalent operation counts when they materially explain a gap;
- startup/import cost separately from library-core cost;
- selective-read decoded-context amplification and decode-unit size;
- exact archive bytes and all integrity/recovery metadata;
- exact-tree/member identity after extraction.

Never move mandatory work outside the timed or resource boundary to make a result look fast. Separate library-to-library and fresh-process CLI evidence so startup cost is visible rather than hidden or accidentally double-counted.

## 5. Real-corpus expansion beyond the current 15

The frozen 15-workload matrix remains mandatory and immutable for its existing purpose. It is **not** the only court of efficiency truth during this recovery.

Build and maintain an additional reproducible serious-corpus performance matrix that exercises multiple independent real-world families and scales. Prefer public or deterministically reconstructable data and record exact fingerprints/provenance. The expanded matrix should include, when practical, substantial representatives of:

- source/developer repositories and build trees;
- office/document workspaces;
- media and already-compressed assets;
- databases / analytics / columnar or structured exports;
- logs and telemetry;
- ML/model artifacts;
- backup/versioned data;
- many-tiny-file trees;
- large mixed binaries;
- incompressible/encrypted-like inputs;
- duplicate/hardlink/symlink/sparse filesystem semantics;
- nested archives/containers and heterogeneous mixed trees.

Use multiple scales where cost curves can change materially. Do not let filename, extension, benchmark identity, known corpus hash, or workload name become encoder policy. Hold out some corpora from mechanism development so transfer can be tested rather than narrated.

The purpose is not to manufacture a larger leaderboard. It is to catch architecture that looks acceptable on the frozen 15 but collapses on realistic scale, file-count, entropy, metadata, or process-overhead regimes.

## 6. Competitor and inherited-floor target

The active target is stronger than merely returning to v0.29 timing.

For every required competitor row under equivalent semantics and same-input measurement:

- preserve the existing zero-byte inherited CMPCT regression floor;
- restore the v0.30 runtime gate (`median create/extract <= 1.10x`, `max workload create/extract <= 1.25x`, whole-tree peak RSS `<= 1.25x` versus the required inherited comparison);
- satisfy the current release-lock external-competitor law: strict no-tie wins over ordinary ZIP/Deflate and solid Zstd-19 in **size and creation time** on every required workload, with exact-tree verification before credit;
- on the expanded serious-corpus matrix, treat any confirmed slower-than-ZIP creation row as a real engineering red until it is either fixed or demonstrated to be a genuinely different semantic/product operation. Do not average it away;
- report CPU, RSS and I/O alongside wall time. A wall-clock win obtained by exporting an obviously material resource regression is not “efficiency recovered” until the broader Pareto position is understood and repaired.

Where ZIP is already faster, study *why*: candidate search, repeated traversal, Python orchestration, hashing, process topology, compression effort, metadata work, reconstruction preparation, fsync/durability, or another owner. Attack the owner, not the stopwatch.

## 7. Current known priority owners

The exact current evidence controls ordering, so this list may evolve without changing this directive. At activation start, recover fresh evidence before assuming these remain dominant.

As of the current v0.30 evidence wave, high-value owners include:

1. **ML / G04 creation and extraction:** remove duplicated/redundant work in the canonical shipping path while retaining the earned bytes and exact semantics;
2. **Logs extraction:** isolate and remove the extraction-specific owner rather than touching its already-strong creation path;
3. **global candidate/search overhead:** determine how much total creation time is spent auditioning representations that ultimately lose, then use exact futility/admission redesign where material;
4. **broad external competitor creation gap:** close it on same-input serious corpora, not only synthetic or friendly cases;
5. **locality headroom:** speed work must not consume the remaining <=8x selective-read budget by silently widening decode context.

A newer measurement may replace this ordering immediately if it proves a larger causal owner. Repository truth beats this prose.

## 8. Decisive-engineering standard

A useful activation should aim for at least one of these outcomes:

- delete/fuse an entire material pass or work category;
- avoid constructing a large class of losing candidates;
- move a proven hot path across an implementation boundary with exact semantic parity;
- change ownership so a costly fact is computed once and reused safely;
- materially reduce a release-blocking create/extract gap on more than one independent corpus;
- establish a reusable architectural win that transfers to held-out corpora;
- prove an optimistic floor that kills an insufficient optimization family and forces a better tier;
- cross a strict external competitor or inherited-runtime boundary with margin;
- produce decisive negative evidence that prevents further wasted optimization work.

Commit count, number of experiments, number of green classifiers, or tiny isolated percentages are not progress by themselves.

## 9. Experimental discipline

For each material performance intervention:

1. recover exact current head/fingerprint and current measured gap;
2. name the dominant owner and D0–D5 diagnosis;
3. state the mechanism hypothesis and simplest strong control;
4. state what percentage/absolute budget the owner controls, where measurable;
5. define a result that falsifies the intervention family;
6. preserve identical input trees and equivalent semantics;
7. run repeated paired measurements with enough samples to separate the repository's timing-noise envelope;
8. include at least one held-out or hostile corpus when claiming transfer;
9. measure bytes, create, extract, CPU, RSS, I/O/locality as applicable;
10. rerun the product gate after the local causal test; a microbenchmark win is not product evidence.

Preserve negative evidence and do not move thresholds after seeing the result.

## 10. Exit conditions

This directive remains ACTIVE until repository evidence proves **all** of the following on the authoritative product path:

1. the frozen v0.30 compression/generalization and zero-regression guarantees still pass;
2. the promoted-product runtime/RSS gate is green under its unchanged ceilings;
3. the current strict external competitor matrix is result-bearing and green, including strict ZIP and Zstd-19 size + creation-time wins where required;
4. the serious-corpus matrix contains multiple independent real-world families/scales and shows no unresolved confirmed creation-speed loss to ordinary ZIP under equivalent semantics;
5. creation efficiency has no known material CPU/RSS/I/O regression being hidden by wall-clock aggregation;
6. extraction, verification and selective-read costs have no unresolved release-blocking regression, with locality still within its existing bound;
7. the byte gains that justified v0.30 remain retained rather than being optimized away;
8. evidence is tied to the current authoritative candidate and preserved durably enough for a zero-history agent to reproduce the decision.

Meeting only the frozen 15, only one friendly corpus, only an aggregate average, or only one machine is not sufficient to deactivate this directive.

When all exit conditions are met, record the evidence and explicitly mark this directive **SATISFIED / no longer the dominant temporary allocator**. Until then, CMPCT should keep coming back to the same question:

> **What large, measured piece of unnecessary work can we eliminate next so the real product becomes decisively faster and more efficient without surrendering its compression, exactness, locality, recovery, or portability strengths?**
