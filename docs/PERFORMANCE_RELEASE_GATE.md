# CMPCT performance release gate

Status: normative project-development policy for pre-1.0 releases.

## Objective

CMPCT is allowed to discover new tradeoffs; it is not allowed to silently move its measured
performance frontier backward. Every material project version therefore benchmarks the candidate
against its direct base before merge and commits a fresh public result record.

This is stricter than a marketing benchmark. The purpose is to make performance a release invariant.

## Comparison topology

A valid release comparison uses:

1. the **candidate benchmark harness** for both engines;
2. one generated public corpus tree;
3. normalized filesystem timestamps/metadata where the harness controls them;
4. a recorded corpus fingerprint;
5. the direct base engine and candidate engine against that exact same tree;
6. the same runner, dependency set, repetition count and operation semantics;
7. separate library and fresh-process CLI layers.

Footnote: using each revision's historical harness independently is invalid for a release gate. A
harness change could otherwise alter corpus bytes, timing boundaries or semantics and make the
candidate appear better or worse even when the archive engine is identical.

## Size rule — zero-byte tolerance

For the same logical/filesystem input and the same encoder semantics, CMPCT archive size is
deterministic. Therefore:

> **candidate archive bytes must be <= direct-base archive bytes on every release-parity workload.**

There is no percentage/noise tolerance for archive size. One extra byte is a regression signal that
must be understood.

If a deliberate format change necessarily buys another product property with bytes, that is not an
excuse to turn the check off. The project must explicitly redesign the benchmark contract, version the
new semantics, and show why the new Pareto position dominates under the broader product objective.
Until that evidence exists, the larger archive does not merge.

## Timing rule — same-runner confirmed regression

Timing is noisy, especially on hosted CI. The gate therefore uses repeated medians and currently
requires a candidate slowdown to clear **both**:

- a relative threshold of 5%; and
- an absolute threshold of 3 ms.

A slowdown inside either side of that envelope is recorded as ambiguous runner noise rather than
called a regression. A slowdown outside both thresholds blocks release.

This envelope is not a performance budget to consume. It is a measurement-confidence rule. Controlled
hardware or more repetitions should tighten it over time.

## What gets benchmarked

The canonical release-parity corpus currently covers:

- many tiny structured files;
- a source/configuration tree;
- mixed media and already-compressed payloads;
- compressible and incompressible large binary files;
- duplicate content plus hardlink/symlink semantics;
- sparse storage;
- nested ZIP containers;
- a combined heterogeneous tree.

The broader neutral/hostile EntropyGraph suite remains a second frontier benchmark and must continue to
show developer, office, media, analytics/database, logs, incremental backups, incompressible data,
tiny files, ML artifacts and mixed binary workloads. It preserves losing cases by policy.

## Public release record

A material version is incomplete until the accepted candidate result is committed under
`benchmarks/history/`. The record should include at least:

- project version;
- format revision;
- source commit;
- direct comparison base commit;
- corpus fingerprint and logical size;
- repetitions/statistic;
- environment and codec versions;
- cache/process semantics;
- integrity/filesystem semantic qualifications;
- every workload result, including losses.

CI artifacts are useful diagnostics but are not durable history.

## Website contract

The website is a consumer of committed evidence, not an independent source of performance truth.
`site/build_site.py` builds headline metrics, competitor comparisons, workload wins/losses and release
state from benchmark history. Large performance percentages must not be typed into static HTML.

The site may present the evidence aggressively. It must distinguish:

- **canonical parity** — the executable reference reader/writer and its current format revision;
- **research frontier** — experimental engines such as EntropyGraph that may lead canonical behavior
  but are not yet interoperability claims.

## Failure behavior

A failed performance gate blocks merge. The correct responses are to:

- find and fix a real engine regression;
- improve an optimization until the candidate dominates the base;
- repair an invalid benchmark substrate while preserving or strengthening the invariant;
- increase measurement quality when timing evidence is ambiguous.

The incorrect responses are to drop the losing corpus, loosen size tolerance, compare against a weaker
operation, change process boundaries, or relabel a regression as acceptable without a new product-level
Pareto argument.
