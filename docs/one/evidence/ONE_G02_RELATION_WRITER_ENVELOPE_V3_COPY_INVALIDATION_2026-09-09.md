# ONE-G0.2 Relation Writer Envelope V3 copy-boundary invalidation — 2026-09-09

Exact source `29974adb303f0dee193f0b0b0ae8f4da2b224261` and its workflow run `34345202132` are **scientifically inadmissible for promotion**, regardless of eventual CI output.

Hostile review found a second traffic-accounting defect before hosted evidence was accepted. Although the corrected C gate reads exactly three source/target pairs per 64-byte version block, the Python `_gate(...)` wrapper constructed ctypes arrays with `from_buffer_copy(source)` and `from_buffer_copy(target)` on every call. Those full-version copies are real memory traffic and CPU work but were not represented in the frozen sparse-probe accounting.

The correction must preserve the exact C kernel, matrix, thresholds and incumbent, but pass pointers to the existing immutable Python byte buffers without copying them. The admissible implementation uses `PyBytes_AsString` only to obtain stable read-only addresses during the synchronous native call. The C kernel remains the only additional source/target reader in the pre-gate.

This is an evidence-lane/accounting invalidation, not a scientific HOLD. Any result from run `34345202132` is debugging evidence only.
