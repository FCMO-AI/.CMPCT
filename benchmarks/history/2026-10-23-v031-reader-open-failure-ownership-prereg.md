# v0.31 Reader open-failure ownership — preregistration (2026-10-23)

Status: **preregistered before changing Reader implementation, collecting hosted test outcome, or promoting anything**.

## Observation and exact baseline
Canonical `agent/v031-development`, inspected Reader blob `e716233403dabd0966863c45635e18fa5ac6afb8`. `CMPCT.__init__` opens `self.f` before calling `_load_index()`, allocating the mmap, and validating canonical paths. Exceptions from these steps do not explicitly close the file or mmap. Python's eventual destruction is not a deterministic resource-ownership contract, especially when exceptions/tracebacks are retained, the GC is delayed or the implementation is not CPython.

## Question and falsifiable prediction
Can a failed Reader construction be made to **release all resources allocated by that constructor synchronously**, including the underlying file descriptor and any already-created mmap, without changing successful archive bytes, on-disk revision 24, public read semantics, worker lifecycle or release thresholds?

* Baseline prediction: short/corrupt header raises after open and leaves the observed tracked file object open while the exception traceback is retained. Canonical logical-path collision raises after mmap and similarly leaves file/mmap open.
* Candidate requirement: both paths release file and mmap before the exception escapes; original exception type and message remain intact. A forced `mmap` failure must release `self.f`.
* Independent negative control: failure at `open()` (before ownership) must not trigger invented cleanup, while normal valid Reader construction and closure remain correct.
* No success if cleanup only occurs after GC or after releasing the saved traceback.

## Minimum decision court
Instrument the actual module's `open` and `mmap.mmap` entrypoints to retain references to the exact objects acquired. Keep the thrown exception alive, then observe `closed` directly. Exercise a malformed revision-24 header, forced mapper failure with stub index, and a canonical alias collision with two distinct paths. Reuse an independently frozen valid r24 archive for success parity if available; do not substitute a fake valid content interpretation.

## Implementation boundary
Only restructure Reader constructor's exception ownership. Do not change parsing, preflight policy, archive verification, close() ordering for successfully constructed instances, filesystem extraction, compression, or benchmarks. The broader Reader/worker/sparse/hardlink owners remain independent.

## Decision law
If source baseline already closes synchronously under this court, abandon patch and retain the counterexample; if any candidate path leaks or masks a caller-relevant exception, reject. Focused tests are only a correctness gate, not performance or release credit. Attribute any CI red to exact source and inherited evidence rather than weaken tests.

## Expected product cost
One constructor-scoped cleanup path with O(1) metadata and no extra work on successful reads except exception-frame machinery; actual runtime and portability still require separate evidence. No benchmark-sized objects, new dependencies or on-disk bytes. No discovery policy changes from a single event.
