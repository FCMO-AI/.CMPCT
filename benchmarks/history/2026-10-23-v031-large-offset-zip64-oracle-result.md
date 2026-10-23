# v0.31 ZIP64 >4 GiB offset/count — result and product boundary

**Date:** 2026-10-23. **Tier:** O0 ZIP wire-format/reader-interop scientific evidence; **not CMPCT product proof**.

## Pre-result prediction identity

The preregistration was committed at `fb38f9df12af70118bc9f86e10d41d5a3fee6139` **before** the new source or its hosted results: `benchmarks/history/2026-10-23-v031-large-offset-zip64-oracle-prereg.md`. The new script is `benchmarks/v031_zip64_large_offset_oracle.py` at blob SHA obtained from repository source. The actual script SHA-256 reported by the hosted execution is `f3111e1b8a37e4be0ddff93861c4a3d06bf38f25f87018b5f2d0118550608ab2`.

Source head: `8c3cade599ee71d4632fd4f82e9895c1c8930680`. Exact-head [GitHub Actions 39998087137](https://github.com/FCMO-AI/.CMPCT/actions/runs/39998087137) **SUCCESS**, sole experiment job `120566751260` completed SUCCESS. Permanent artifact ID `12520497172`; artifact ZIP digest `sha256:1eeead5b286d7edf098b7b2ec5219ebce824fd382a503f24d3f62d33b80aab8a`. The contained `result.json` digest is `sha256:30de2652be2ee286c05d40112ff716896260b4072cdc0f8d1f424f2ce183ceb1`. Retain raw JSON rather than reconstructing it from this note.

## Real hosted observations

Host: Linux 6.17.0-1022-azure x86_64, CPython 3.11.17. Both valid cases use a synthetic **4,294,971,392-byte** STORED member whose hole bytes are logically all zeros and whose CRC32 is `b875d37f`. No 4 GiB Python buffer or 4 GiB physical write is performed. ZIP is real; CMPCT is **not** used to produce the fixture.

| Case | Members | ZIP logical bytes | Physically allocated bytes | Late local offset | Central offset | CPython | Info-ZIP |
|---|---:|---:|---:|---:|---:|---|---|
| offset-only | 2 | 4,294,971,788 | 8,192 | 4,294,971,452 | 4,294,971,545 | PASS | PASS |
| count+offset | 65,536 | 4,301,918,392 | 6,955,008 | 4,297,527,278 | 4,297,527,371 | PASS | PASS |

Late member exact recovered SHA-256: `e285901f9493a5bc97d9c85028ccb6ebe6e53ac7a99978359edfbf3fcfb7e974` (both). The deliberately wrong ZIP64 central offset is **REJECTED** by CPython `zipfile` (`BadZipFile`).

Full script wall 0.902693 s, peak process RSS 61,932 KiB. Fixture write intervals were 0.000115 s (offset-only) and 0.118057 s (count+offset). **Do not compare those as real compression throughput**: they do not include reading/reconstructing the 4 GiB logical source, the source's full digest, or any CMPCT export. The sparse physical test fixture is an evidence-economics technique, **not** a claimed storage win.

## Decision change / what this falsifies

**Result: ZIP64_OFFSET_WIRE_ORACLE_PASS (O0).** Large offsets and >65,535 entries are structurally composable in ZIP64 with correct selective central extra fields (ZIP64 sizes only when the 32-bit sizes are saturated; relative local-header offset-only when the 32-bit offset is saturated), ZIP64 EOCD, locator and conventional EOCD sentinels. Two independent readers find and reconstruct the trailing Deflate member. Incorrect replacement of the 64-bit offset with a zero offset does not pass.

This rules out **ZIP64 metadata grammar incapability** as a reason to retain an unbounded full-member `self.read` fallback. It does **not** establish a memory-bounded real CMPCT exporter. Owner [PR #260](https://github.com/FCMO-AI/.CMPCT/pull/260) correctly keeps a conservative stdlib fallback while it lacks a native general ZIP64 path.

## Stronger controls, limits and self-critique

- The O0 instrument does *not* test ZIP64 support in CMPCT's Python Reader or native core, produce r24 archive input or validate 4 GiB logical extraction. The giant member's CRC is constructed by streaming zero slabs, but neither reader traverses all those giant bytes in this court.
- The test's 65,536-member case allocates 61 MiB process RSS and ~6.9 MiB disk blocks; that is **not O(1) index memory** in member count. No native ZIP export CPU/RSS/I/O or Windows/macOS interoperability is measured.
- CPython and Info-ZIP are related ZIP-format implementations, not independent proofs of arbitrary readers or hostile parser handling.
- A simpler product solution using incremental `ZipFile.open(..., 'w')` might bound memory without implementing native ZIP64 footer logic, but would ordinarily recompress existing Deflate streams. It deserves a same-input/equal-semantics CPU and physical stream-reuse A/B against a genuine native ZIP64 writer before implementation is promoted.
- For true >4 GiB data, the exact physical/logical format, source identity, streaming CRC, integrity, ZIP64 descriptors/offsets, file metadata, recovery and packaging costs must all be proven.

## Counterfactual and next executable action

A single sparse early member followed by one 20-byte Deflate payload beyond the 32-bit offset limit would have established ZIP64 offset grammar feasibility before any product rewrite; adding 65,534 directory entries showed count coexistence at low incremental resource cost.

**Next owner-safe action:** hand this O0 result to PR #260's owner. Then evaluate a bounded streaming *implementation* with direct raw Deflate stream reuse, 64-bit central offsets and member sizes, no `self.read` of whole 4 GiB members, and controlled same-input CPU/wall/RSS; distinguish fallback necessity from chosen product contract. This court alone does not justify a merge or release.

No Discovery Engine policy mutation or `STATE.json` update: exact case is research-level positive but does not change the current primary CMPCT product bottleneck.
