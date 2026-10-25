# O49 prospective — transaction update from FIFO source: bounded genuine product falsifier

Date: 2026-10-25 UTC. Research only. No `transactions.py` or product modification.

## Source / mechanism
Canonical v0.31 development `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`, `src/cmpct/transactions.py` blob `964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c`, `append_update()` reads `Path(source).read_bytes()` before `source.stat()`. A path referring to an existing FIFO with no writer can block during the source read, instead of rejecting an unsupported source type. `Path.read_bytes()` on a real FIFO without a writer was separately bounded by a killable child and failed to finish in 0.4s (primitive evidence, not full product). [Issue #403](https://github.com/FCMO-AI/.CMPCT/issues/403) is the prior independent prospective statement of this concern.

## Hypothesis
An actual `python -m cmpct update valid-r24.cmpct member real-no-writer-fifo` process remains blocked at least 2s with no writer, on POSIX, while ordinary regular-file updates succeed and are exactly reconstructible. If an actual installed Writer fails closed in a bounded time rather than blocking, this hypothesis is false; record the result and retire the concern.

## Strongest simpler control
Run the unchanged complete product update entrypoint; no mocking `read_bytes`, stat, writer, or FIFO. Test both an ordinary valid source file with authentic archive creation and update, and a real POSIX FIFO with no writer in a separate killable subprocess. Preservation of the original archive's complete SHA-256 during the bounded blocked attempt distinguishes a stalled input read from a partially written journal.

## Alternative explanations / falsifiers
CLI may have independent source type admission not apparent from the `append_update` function; test the real installed CLI as well as the exact `append_update` source when needed. Very slow startup may produce a misleading 2s timeout; prewarm and measure the ordinary successful update in fresh process first, and record whether the Python import or FIFO source open consumed the time. A blocked terminal invocation is an availability defect but not a destructive archive failure.

## Evidence and safety boundaries
On Linux/macOS use `os.mkfifo` inside a temporary directory. Launch a child with `subprocess.run(..., timeout=3.0, capture_output=True)`, which kills the child when timed out; neither runner nor parent reads FIFO directly. Keep archive SHA identical and verify with the genuine Reader. Windows fixture must skip (not be called pass). Retain exact head, installed module provenance, JUnit/logs and actual result. No product/release credit or mutation; product remediation belongs to current Writer owners (#247, #295, #304, #311 etc.) and requires source lifetime/TOCTOU hardening beyond an unconditional path stat.
