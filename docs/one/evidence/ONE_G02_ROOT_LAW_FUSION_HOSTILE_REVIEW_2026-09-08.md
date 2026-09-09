# ONE-G0.2 root Law fusion — hostile review receipt

Date: 2026-09-08

The first Builder draft reconstructed into a Python `bytearray` and then called `bytes(sink)`. That creates a complete extra root-sized copy. The draft traffic model did not charge that copy, so accepting timings from that implementation would understate actual memory work.

All root-Law-fusion evidence at source `47e980ba970c551163b4b0c58636d005bee19fc5` or earlier is therefore **pre-result inadmissible**, regardless of any future CI status. No hosted falsifier had been accepted when this defect was found.

The repaired descendant allocates the final CPython `bytes` object once through the CPython C API and fills that private payload before returning it. Root SHA-256 still runs after reconstruction and inside the timed call. The traffic model now has no hidden bytearray-to-bytes freeze traversal.

This is research machinery only. CPython C-API allocation is not a canonical ONE ABI or portability decision; a production/native reader would own its destination buffer directly. The scientific matrix, wire threshold, generic-improvement threshold, literal-speed boundary, root semantics, and node limits are unchanged.
