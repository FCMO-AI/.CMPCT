# O96 — post-admission output ancestor rebind (prospective preregistration)

**Date:** 2026-10-25 UTC. **Status:** PROSPECTIVE — created before experiment or hosted observation.

## Authority, source identity and coordination

CMPCT released v0.30.0/revision 24 and canonical `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b` remain unchanged. This independent science-only hypothesis is stacked on the exact O93 product head `15aac3f81c23e0a54ae66de3f6b2146642afa350`, PR #451, Builder Git blob `7214a46b781bb10051e6782ba7731989ebf05edb`. O93 owns descriptor-bound final-file publication. O91 PR #449 already owns and proves basename symlink-to-source/FIFO races. O75/O78 own staged-output atomicity and pre-existing inode semantics. **O96 does not edit product files or those owners' tests/branches.**

The O93 prereg explicitly excludes global parent/root pathname rebindings, but no exact-installed CMPCT court there yet proves a post-admission **ancestor-component symlink pivot** of a destination that was originally *absent*. This is a different mutation surface from O91's basename pivot (which O93 blocks via `O_EXCL`), and an independent next-level falsifier for any broader destination-lifetime safety claim.

## Single primary question and prediction

Does O93's `O_CREAT|O_EXCL` + descriptor `fstat` + final `stat` protect the **authorized output namespace** (the previously checked resolved directory), or only the output leaf inode?

**Prediction H1:** create a source directory containing one regular file, an independent empty external directory, and an out path `external_alias/archive.cmpct` whose `external_alias` initially symlinks to that external directory. Require original `realpath(out)` outside root and original out nonexistent. After the original installed Builder's genuine `scan()` completes, atomically replace **only the ancestor symlink** `external_alias` with one targeting the source root. The leaf `archive.cmpct` remains initially absent; `O_EXCL` therefore admits it and the descriptor's regular inode passes `fstat`. Expect Builder to return successful archive creation, Reader verify/extract the original source, while a new archive file is silently created **inside the source tree that preflight was designed to exclude**.

This would prove loss of output *namespace* custody despite correct leaf *inode* custody; it would **not** establish arbitrary writer escalation, source-byte overwrite, infinite wait, power-loss durability, or a vulnerability without an independent actor capable of mutating that ancestor symlink.

## Strong simpler controls and alternative explanations

1. Baseline `Builder(root).build(root/archive.cmpct)` must be refused *before* scanning (existing root-containment protection).
2. Same originally absent out path with stable ancestor symlink to external directory must successfully create a verifiable archive there; source directory must remain unchanged.
3. Hostile parent change uses a genuine atomic `os.replace` of preconstructed symlink-to-directory onto original symlink (no partial directory swap), at a deterministic after-scan barrier wrapping only the original `scan()` invocation. The archive source and encoding remain genuine.
4. A process/worker assertion or archive validation failure disproves the predicted *successful publication*; if the actor fails to swap, the run is invalid, not a PASS.
5. Prove installed `cmpct.builder` originates outside checkout and has exact frozen source Git blob; do not rely on similarly shaped pure `os.open` toy success alone.
6. Attribute on Linux/macOS only where native symlink replacement semantics can be tested; Windows remains unmeasured.

## Decision and safety boundaries

Use isolated temporary roots, tiny non-sensitive payloads, and a bounded executor. Preserve JUnit and raw source identities, including negative or infrastructure results. All experiments are research/falsification, not product improvements. If H1 survives, notify PR #451 owner with exact reproduced result and narrowed claim: O93 fixes final-leaf pivots but does not make destination authorization live across mutable **ancestors**. The economically viable product route must establish an explicit namespace custody contract; no automatic feature/format/release change is authorized.

If H1 is false, preserve that failure; analyze whether path-resolution semantics, an inherited guard, or instrumentation caused it before changing the hypothesis. Do not loosen any existing O93 or official evaluator.
