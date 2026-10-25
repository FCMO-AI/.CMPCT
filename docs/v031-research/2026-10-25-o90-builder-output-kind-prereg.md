# O90 (Phased2) — prospective Builder output-kind admission repair

Date: 2026-10-25 UTC. **PREREGISTERED BEFORE PRODUCT CHANGE.** Independent bounded repair of [confirmed O87 defect](https://github.com/FCMO-AI/.CMPCT/issues/446); based on the exact O84 composition head `7efcc51154b64fd6394ddffaab599760659f6c91` (Builder blob `64b0cd21ad54ce7c8e8c6f5847b3c613fff6511c`). Parent O81 #439, O84 #442, and negative O87 #445 are distinct owners and remain unchanged. Shipping v0.30.0/format r24 untouched.

## Primary question / falsifiable prediction

Can a **small pre-scan admission check on the already-fetched output `os.stat`** turn the genuine installed Linux/macOS FIFO and symlink-to-FIFO >8s blocking failure into a prompt, explicit rejection, without modifying regular output bytes, in-tree and source/output-inode protections, or historical symlink-to-regular output semantics?

Prediction: reject any existing output whose *target* is not a regular file (FIFO, socket, directory, char/block device) before scan and encode; reject dangling output symlinks rather than silently writing their absent target; preserve existing regular and symlink-to-regular write semantics and all O80/O81 Builder guards. Existing unsupported special outputs are not a valid generic archive destination.

### Simpler controls, alternatives and kill criteria

- Merely checking `is_symlink` loses historically permitted symlink-to-regular behavior; do not.
- Staging and `os.replace` repairs some failure atomicity but changes output inode, hardlinks, symlink, xattrs, permissions (O78 #435). Do not import that separate mechanism.
- Existing `os.stat(out)` already returns `st_mode`; use `stat.S_ISREG` in the existing branch with near-zero regular-path work. Detect dangling symlinks only in `FileNotFoundError` using `os.path.islink` (or equivalent), preserving normal new-target creation. Any other `OSError` must remain visible.
- Kill or narrow if a genuine static FIFO/symlink-FIFO still blocks, a normal independent existing output differs in archive bytes from O84, valid symlink-to-regular is rejected or changed in semantics, O80/O81 tests regress, or a new output path is rejected unnecessarily.
- This remains a **static preflight**, not descriptor-bound atomic source/destination custody. Explicitly preserve a TOCTOU residual: another actor can swap the output after `stat`.

## Decisive evidence ladder

1. Source-level audit and micro smoke on authentic Builder/O87 cases; stat and errno behavior on real POSIX filesystem.
2. Installed-package subproc court with hard 8s watchdog: existing regular output, FIFO, symlink-to-FIFO; new controls symlink-to-regular, dangling symlink, directory and absent independent output.
3. Original O80/O81 tests (unchanged bytes) and before/after complete revision-24 archive byte parity for stable, same-host regular/tree controls.
4. GitHub Actions ubuntu-24.04, macos-14, windows-2025 (POSIX FIFO cases explicitly unsupported/skipped only on Windows). Record raw JUnit, head, installed module path, byte hashes, skips, and exact-head statuses. General and performance/release gates remain separate and not earned by focused evidence.

No frozen benchmark, release gate, reader/format/codec, policy or discovery state change. This PR is a reviewable candidate for owners of #439/#442; it does not merge or release.