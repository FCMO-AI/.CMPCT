# Windows Far-Sentinel Lease × O_APPEND Descriptor Ownership — O1 Preregistration

**PRE-RESULT, 2026-10-23 UTC.** Separate stacked research branch, no change to owner #295 Writer code or parent #298 compatibility court. No product credit.

## Prior observation
Independent O0 Windows Server 2022 / Python 3.11.9 [run 40040076203](https://github.com/FCMO-AI/.CMPCT/actions/runs/40040076203), artifact 12539210499: 3/3 local NTFS true-hardlink conflicts using `msvcrt.locking` at offset `1<<60`, 3/3 concurrent Reader header reads accepted, sample unchanged. Byte-0 control made all 3/3 header reads fail with PermissionError. This is a real primitive decision, not a Writer solution.

## Narrow O1 question
After acquiring the Windows sentinel range lock using a Python `os.O_RDWR | os.O_APPEND | os.O_BINARY` descriptor, does `os.dup()` and `os.fdopen(..., 'wb', buffering=0)` append **exactly** to physical EOF (not the sentinel offset) and return an accurate `tell()` offset for the next footer, while maintaining lock ownership and allowing separate Reader header access?

## Frozen controls / predictions
1. Exact same test payload and `os.dup()` append sequence with **no lock** must preserve original bytes, produce `old_size + appended_size` and `tell() == physical EOF`.
2. With `msvcrt.locking` at `1 << 60`, the same two sequential writes under one owning descriptor must produce byte-identical file contents and offsets versus control. If the OS or CRT writes at the sentinel, extends file sparsely, rejects `O_APPEND`, or makes `tell()` unsuitable as the physical footer position, the naive PR #295 fd strategy is **not** portable; do not rescue by changing the test.
3. While sentinel held, a fresh-process original/hardlink lock attempt must fail, while a fresh-process header read succeeds. The original file bytes and candidate trace are preserved.
4. After releasing sentinel, another process can reacquire the same lock, archive original content+appended bytes remains exact.

## Experimental constraints
Actual hosted Windows 2022 / Python 3.11 runtime, independent process for conflict/read control, no mocks; local NTFS only. Two payload sizes/repetitions, exact cryptographic source & output comparison; no full CMPCT product claim. A red result preserves the original failure trace. The oracle is bounded and deletes temp files. Manual byte-range locks and large sentinel offset introduce OS- and filesystem-dependent caveats not addressed here. Follow-up for crash release, share modes, timeouts, path rebinding and Windows real r24 test remains open.

## BONK / decision policy
Choosing the narrow append-offset falsifier is more informative than implementing a whole Windows Writer backend before checking whether its foundational offset invariants hold. A failure narrows strategy to explicit append offsets/LockFileEx alternative; a pass merely permits implementing a portable, fail-closed adapter in the owner's lane subject to all their original negative controls. None of CMPCT's frozen benchmarks, format, Reader, Writer, thresholds or promotion policy may change.
