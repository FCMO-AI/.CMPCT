# J24I50e — Python-origin versus pathname-reopened native ABI split

**2026-10-30 UTC; prospectively recorded before extending the fixed physical source-swap court.** Exact parent `ef6c73fce93f75e4b3fcf9ccbd8522a8a44cac51` on [#807](https://github.com/FCMO-AI/.CMPCT/pull/807). No product/format/ABI/release modification.

## Decision question

A future implementation might delegate an **already-open** `CMPCT.verify()` Python object's work to `cmpct_open(str(self.path))` rather than share its established archive inode/generation. The code inspection indicates a source split. Can that split be demonstrated with the real shipped Python Reader and real public compiled C ABI on **one Builder-independent fixed r24 WAV/FLAC archive**, under a controlled pathname rename and replacement? This is a narrow source-custody test, not an exploit demonstration.

## Prospective experiment and controls

Reuse J24I50d's `tests/conformance/v24-wavflac.json` identity, fully checked physical hashes and same rename/replacement mutation. Before rebinding the pathname, **open both** (a) an actual `CMPCT(original)` Python reader and (b) one `cmpct_open(original)` native handle. After renaming the inode aside and writing an equally sized but physical-SHA-corrupt replacement at `original`, demand:

- Held Python `verify()` still returns exactly one (the *original* data).
- Held native C `cmpct_verify_complete` also returns success/one (the original).
- A fresh native C `cmpct_open(original)` succeeds index admission but its strong verify rejects corruption with zero output count; fresh CLI fails with empty stdout.
- Retained physical original remains byte-for-byte SHA-equal to the frozen golden; restore the original pathname after all assertions.
- Report an explicit structured test observation in the existing court's stdout so the run log establishes the new parity/split, not just a silent assertion.

**Kill:** if the two existing readers disagree on an untouched unchanged original inode, the test defeats the proposed origin invariance; investigate instead of weakening the assertion. If a fresh native path-derived handle accepts physical corruption, the native bridge is unsafe. If a Python object unexpectedly switches to replacement, record the Python source-custody defect separately. The test is Ubuntu/POSIX-only because the native-core Actions job owns that environment; no Win32 rename evidence.

## Meaning and boundaries

This does **not** prove that Python `CMPCT.verify()` currently delegates (it does not), nor that native verify has all Python transaction recovery semantics. It specifically **falsifies the source-identity premise** required to connect an already-open Python Reader by late pathname reopen. The bounded safe options remain original-handle transfer or a deliberate separately labeled operation with distinct semantics; both require further work, OS-specific FD ownership and recovery evidence. No speed, release or integrity claim beyond this controlled mismatch.
