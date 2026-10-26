# O209 — decoded-physical-unit amplification of bounded logical range reads

Date: 2026-10-26 (UTC). Status: **PREREGISTERED BEFORE INSTRUMENT**. Evidence rung: genuine installed Python Reader local-range experiment, not a ZIP64 full-product benchmark.

## Exact inherited source and coordination

- Owner: `FCMO-AI/.CMPCT` O193 ZIP64 streaming PR #521, exact head `392112ce859db5a7f85be593c82d1cabc1f5131f`; reader input kept unchanged.
- Released floor: v0.30.0 / revision-24. On-disk revision, Builder, Reader, evaluator, release gates and frozen corpus must not be changed.
- Adjacent science: O195–O197 verified real 4 GiB ZIP64 output and bounded **requested** ranges. O193 explicitly leaves physical decode-unit RSS unproven. O194/195 sparse extent indexing is a different cost family and is not reopened. J24F05/J24F06 target RAW extraction ownership, not this compressed Zstd random-range question. No simultaneous implementation of the O193 Reader.
- Research-only mutation: O209 adds its independent court/workflow/results. Coordination is through this PR; no shared discovery-state mutation.

## Primary scientific question

Does a valid r24 file with a single 64-MiB compressed Zstd physical blob cause `read_range(name, start, 1 MiB)` to materialize/decode the complete 64-MiB blob, whereas the same logical bytes represented by independent 1-MiB Zstd chunks cause only the intersecting chunk to be decoded? Does that distinction produce a material increase in actual child-process high-water RSS?

This is **not** a claim of unbounded memory: existing physical resource ceilings and host allocation behavior remain in force. It tests whether a 1-MiB logical read limit is a meaningful independent bound on the actual decoded physical unit.

## Prediction, baseline, alternative, falsifiers

- Baseline A: one authentic r24 `S_BLOB` Zstd blob, 64 MiB uncompressed.
- Stronger architectural control B: same 64-MiB synthetic input represented as `S_CHUNKS` with 64 separate 1-MiB Zstd blobs; same file kind/path/mode/mtime/logical SHA; physical index and stored bytes fully charged.
- Same-source true data, full logical SHA and CRC/physical record fields. Both must pass `CMPCT.verify()` in a **separate producer-only validation process** before memory profiling; profiling must exclude producer setup and full-file `verify()`.
- A valid 1-MiB range reading only one chunk should decode 64 MiB in A but 1 MiB in B, by real Reader source control flow. Prediction: child high-water RSS(A) exceeds B by >=32 MiB under isolated fresh processes. CPU/wall and byte counts reported, not converted into universal performance claims.
- Alternative explanation: native codec allocator and Python byte ownership may dominate both variants; the observed RSS delta may be noisy or lower than the decoded byte count. Stronger control is a same-variant no-read child, with separate init/import cost.
- **Kill/narrow conditions:** any differing returned bytes; any invalid archive; source/Reader identity ambiguity; child RSS delta <32 MiB; material hidden evidence harness overhead; or results that do not replicate. If the memory delta is small, retain only the source-derived decoded-work fact, and retire product-memory credit.
- Adversarial case: late-range request and a second independent request; separate physical-decoded-work counts. Do not weaken `ParserLimits` or permit resource exhaustion to make the result dramatic.

## Decision and accounting

If A exceeds B by >=32 MiB on child VmHWM while logical range/bytes match, O193's request-size claim must explicitly remain **logical-buffer-only**, and product promotion needs a separate physical-decode-unit admission bound/strategy (or fully charged, documented bounded physical allocation model). No speculative Reader fix without stronger product/host evidence. If B is equally expensive, investigate package-native codec allocation or the measurement instrument first.

Report: complete archive bytes, producer create CPU/wall, range read CPU/wall, child VmHWM and baseline, decoded logical/physical byte units, original/read SHA, actual reader Git blob/head, and scientific-vs-product scope. Platform Ubuntu only unless another host is actually run. Capture repeat-level raw data and independent reproducibility artifacts.

## Counterfactual

The source-level `_blob` full-frame decode is a cheaper warning than full ZIP64 runs; only genuine child RSS proves its material actual effect. Future agents should distinguish request-length caps from physical decode-unit bounds before describing bounded memory.

No discovery policy change from a single experiment. No numeric release, format change, merge or product promotion from this court.
