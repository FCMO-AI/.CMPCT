# J24G17 — native MessagePack predecode token-count oracle (prospective measurement protocol)

Date: 2026-10-28 UTC. Branch parent: J24G16 #681 exact `5563b199bc03ed03c3e78918c51a7cf5396c2ff1`. **Research only.** No Reader, format, validator, packaging, version, benchmark/release, or Discovery STATE edits.

## Scope, ownership and why this is new information

J24G16 showed pure-Python full syntactic prepass has ~6.38x admitted ordinary-case CPU cost, despite rejecting a 200k-object hostile MessagePack tree before ~36.58 MiB of memory allocation. A native structural scanner is the smallest *different execution boundary* capable of falsifying whether the predecode concept is economically viable, rather than another Python threshold variant. #681 owns the original Python mechanism; this child owns only a C/ctypes research microcourt. #682 operates on tuple-first chunk-reference ownership and is not this question.

At preregistration time an initial local C parser source was drafted and compiled, but **no quantitative performance/hostile RSS measurements have been run**. This preregistration freezes the decision criteria *before* result-bearing measurement, not before draft implementation. Do not represent it otherwise.

## Hypotheses and strongest controls

- H1 (structural): C scanner counts exact MessagePack wire nodes on >=2,500 deterministic valid nested values; under-cap candidates still pass through unchanged `msgpack.unpackb(raw=False)`. Include malformed nesting, truncated framing, reserved marker, trailing bytes, invalid nested map key, ext/fixext and exact 65,536-node cap. Scanner is **not** an acceptance oracle; resource-based refusal changes acceptance and is a research-only policy.
- H2 (ordinary economics): compare direct canonical unpack to native-scan-plus-unchanged-unpack on the identical 10,000-object ordinary MessagePack metadata; native+decode **must not exceed 2x direct** in *both* within-process CPU and wall medians (at least five repeats in independent fresh worker processes per arm), or retire as currently viable predecode approach. Report relative/absolute latency, separate process-start, C compilation and allocation costs. The much stronger baseline remains direct decode; add skip+decode as a faster but semantically insufficient control if useful.
- H3 (hostile RSS): compare direct admission against native predecode resource refusal for 200,000 tiny maps (~800 KiB) with **separately generated input and fresh worker process** to eliminate J24G15/16 RSS highwater contamination. Expect >=16 MiB measured process RSS reduction. This proves refusal economics only, not more memory-efficient *acceptance*.
- H4 (portability/integrity): count using pointer-bounded C code; no CPython APIs in scanner; build at most one simple shared-library oracle on Linux. Verify exact file SHA and process/run identity; leave Windows/macOS and a production ABI unresolved.

## Methods, disproof, adversary

Baseline must remain original msgpack decoder version and identical payload bytes; no disabling malformed rejection or changing threshold post hoc. Compare native-vs-direct inside each host/runtime, never across hosts. Precompute payload in standalone short-lived process; inside measured process time only the scan+canonical decode or canonical decode. Collect medians and raw CPU/wall in nanoseconds with worker order alternation; collect RSS highwater separately. Randomized valid roundtrips and malformed controls are scientific guards, not a complete independent parser proof. Strongest alternative explanation: ctypes calls/copying, CPU host variation, scanner permitting malformed inputs delegated to decoder, and memory pressure hidden by process RSS baseline.

A positive local Python 3.13 study is **not** hosted Python 3.11 product evidence. If H2 passes locally, run an exact-head GitHub Actions scientific court with raw receipts and separately implemented referee, then decide whether a direct native interface is worth productization; if H2 fails locally with a wide margin, preserve loss and avoid expensive integration. No production or release promotion from either result.

## Completion and handoff

Retain raw data, contrary cases and hashes; compare release-safe alternatives; identify cheapest remaining product-relevant fork. Do not modify #681 owner branch, shared discovery state, frozen controls, or production code.
