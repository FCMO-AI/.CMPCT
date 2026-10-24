# O4 — source-bound fresh-process RSS for combined authenticated preflight

Date: 2026-10-24 UTC. **Prospective preregistration before measuring or changing any product source.** This is an independent evidence lane on the exact integration owner [PR #348](https://github.com/FCMO-AI/.CMPCT/pull/348) `0062961be78cd4d28231a9acaf37a4d9cf43920c`. The two product owners remain [#342](https://github.com/FCMO-AI/.CMPCT/pull/342) and [#346](https://github.com/FCMO-AI/.CMPCT/pull/346); this branch must not edit their files or make another implementation.

## Problem, alternative explanations, and decision question

Original O2 [#347](https://github.com/FCMO-AI/.CMPCT/pull/347) preserved **+42.77% traced allocation** for 4,096 authenticated journal operations despite a **25.18x same-runner preflight CPU win**. Python allocation peaks do not establish maximum resident set size (RSS), and the hardlink owner independently records ~6–7% ordinary star overhead. Before optimizing the representation of the positional index, answer: **does the combined exact product demonstrably increase process peak RSS or memory growth enough to change admission, relative to the historical linear delta replay, after keeping the same authenticated r24 input, package and process context?**

Controls:
- frozen historical validator Git blob `51c2849061f99a4afeddb7666956b24566ce7de0`, replay function lifted **byte-for-byte only** into the combined validator for the comparator process; all other code stays exactly PR #348;
- combined candidate untouched, with the original integrated hardlink graph resolver;
- fully authenticated Builder-derived r24 journal archives at N=512/2048/4096, corresponding structurally equivalent signed checkpoint controls and exact archive SHA-256 identities;
- fresh Python **child process per timing/memory observation**; report Linux `ru_maxrss` KiB, preflight-internal wall/process CPU (startup excluded from timings), and before/after live `/proc/self/status` VmRSS; do not equate traced allocation and RSS;
- randomized/rotated A/B/B/A execution order with at least 5 independent samples per arm/size; if runner cost warrants, 5 is the smallest charged court;
- verify return semantics and index/bytes identity before timing; retain raw samples, environment, commit and historical blob identities in a durable artifact.

## Falsifiers and alternatives

If historical and candidate fresh-process maximum RSS overlap substantially at N=4096 despite the traced-allocation difference, **do not implement a memory redesign** based on tracemalloc alone: prefer baseline for memory and keep the measured CPU win with a bounded explanation. If process RSS grows materially (prospective discriminator: >=8 MiB absolute or >=10% at N=4096, consistently across repeat medians), the **next** work is a separate bounded algorithmic variant evaluated against equivalent semantics and RSS—not a threshold/fixture-specific admission tweak. The discriminator is a research triage threshold, not a release gate.

Confounds: Linux allocator arena reuse, resident page granularity, process startup, I/O cache, and overcommit; do not infer pure incremental replay RSS solely from process maximum. Same SHA input and fresh-process baseline/candidate pairing narrow—but do not eliminate—these. Evaluate observations against actual peak, sample dispersion, checkpoint baselines, and physical archive bytes. If the 4,096-case peak is indistinguishable, a larger bounded case can be pursued only as a **separate** explicitly labelled extension; avoid dragging one test into unbounded work.

## Non-goals and concurrency

No changes to `src/cmpct/`, Builder, Reader, parser limits, on-disk r24, format/release/version/CI gate thresholds, hardlink owner semantics or the official zip parity evaluator. Do not edit `docs/discovery/STATE.json`: its product head is stale. Preserve negative/no-gain outcomes. A new workflow is acceptable only if it actually executes an exact-head result-bearing court; otherwise retire redundant CI after preserving receipts. No merge/release authority is implied. Main remaining debt: integrated multi-platform reliability and official release parity.

## Counterfactual

A fresh-process memory court run alongside the original source-exact O2 ABBA would have distinguished traced Python object peaks from resident product cost prospectively. This finding may inform later evidence design only if it changes a decision; one run does not authorize Discovery Engine policy changes.
