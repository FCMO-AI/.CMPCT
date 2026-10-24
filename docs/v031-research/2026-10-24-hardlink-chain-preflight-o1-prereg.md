# O1 preregistration — iterative memoized hardlink resolution, preserving strict rejection

Date: 2026-10-24 UTC. Based on exact published O0 research court [run 40084916000](https://github.com/FCMO-AI/.CMPCT/actions/runs/40084916000), at source `c6a5592aa1027b6003278a4e85aa88389fcaa241`. **Unmodified product accepted both signed archive families** N=128/512/2048/4096. Source-exact median preflight latency in milliseconds chain vs star: 1.238/0.580, 12.920/2.231, 185.027/8.369, 730.438/16.489; chain/star ratio 2.136, 5.792, 22.108, 44.298. Raw five-repetition logs and archive/index/physical byte accounting: artifact #12556257687. This is observed O0 product-cost evidence, not a promotion-quality A/B.

## Primary decision
Can the strict validator preserve its current acceptance/rejection of **all** valid/invalid signed hardlink graphs while removing repeated traversals and their superlinear CPU? Strong simpler control is a single bounded nonrecursive graph walk that memoizes each alias's terminal regular-file owner and compresses traversed tails. It must still check every referenced path exists, every chain is acyclic, and every terminal owner is an actual K_FILE, even if an earlier chain was memoized. Do not change the reference Reader/Builder, user-configured ParserLimits, format bytes or parser schema.

## Independent candidate-control plan
Before implementation, add a source-exact hosted negative court that freezes authentic Builder-generated and fully re-signed r24 indexes for long chain, star, reversed row order, valid multiple-owner graph, self/two-node cycle, immediate/indirect missing owner, symlink/directory terminal. Assert structural preflight decisions and classifications; do **not** relax any original #339 signed-tree assertions. An additional malformed indirect chain can expose a pre-existing Python KeyError rather than ValidationError when an intermediate alias targets a missing path: this must be observed on the unchanged source before claiming repair. Keep original hostile input bytes constant.

Then implement iterative memoized traversal within `src/cmpct/validation.py` only, on this separate stacked branch. O1 acceptance requires unchanged positive/negative controls, exact-head hosted focused test and best available same-input repeated chain/star evidence. A linked, source-exact same-runner parent-vs-candidate ABBA is preferred for real product performance; if unavailable, label timing as cross-runner exploratory. Peak RSS and temporary allocations must not silently invalidate the gain.

## Boundaries / alternatives
Complexity-only cap cuts off legitimate deep archives; adding another class of codec heuristics unrelated to CPU owner is noise. Deep recursion is not acceptable. Memoize terminal names, not mutable decoded file data. A pure local randomized differential model (18,000 mixed graph cases) showed no accept/reject divergence, with 4096-chain local algorithm median 771.108ms reference vs 1.357ms memoized. This is **detached oracle only**, not source/product evidence, and it revealed a plausible indirect-missing KeyError failure in the source loop. Preserve separately.

## Falsifiers
A signed long valid chain rejected, a terminal directory/symlink accepted, an indirect missing owner silently allowed, cycle accepted, or any inconsistency in inherited parser limits/ref parsing invalidates the approach. A measured win that exports unacceptable peak RSS or ordinary-index overhead is not a promotion. O1 cannot change tests, comparators or thresholds to pass. No version bump, merge or release without inherited source-exact and parity gates.

## Concurrency
Parent #339 owns new topology and hardlink-owner-type correctness; this O1 is a separate, prospective **algorithmic-cost** intervention stacked on its SHA and coordinated via PR #342. #341 owns CI/provenance reconciliation. No blind overwrite of other agents and no shared Discovery STATE mutation.
