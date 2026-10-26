# J24F01 — frozen chunk-map extraction publication court (preregistration)

**Status:** PREREGISTERED BEFORE IMPLEMENTATION / RESULT UNKNOWN.
**Repository:** FCMO-AI/.CMPCT, canonical v0.31 base `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`.
**Original Reader Git blob:** `e716233403dabd0966863c45635e18fa5ac6afb8`.
**Frozen independent source:** `tests/conformance/v24-chunk-maps.json`, Git blob `91141405bb10b2e1226b0652e3aa0a13ba41846c`.
**Authority:** AGENTS.md / docs/HARDENING.md / docs/FORMAT.md; on-disk revision 24, published v0.30.0 unchanged.

## Problem and prior evidence

O108 (#463) demonstrated that S_CDC, unlike S_BLOB and S_SPARSE, uses an atomic staged extract path and does not block on an existing FIFO in the tested Linux/macOS Reader; it used genuine Builder-created archives. O121 (#471) demonstrated FIFO blocking for S_PACK and S_VZIP. The remaining S_CHUNKS mode shares the staged implementation with S_CDC but has not received a fixed-archive independent destination-publication court. Existing revision-24 hand-built vectors already encode both S_CHUNKS (1) and S_CDC (5) using mixed RAW/Zstd/Deflate chunks. Before buying a new Builder experiment, use those stronger independent, frozen controls.

## Primary scientific question

Will the original installed Reader, reading **exact frozen Builder-independent archives**, publish S_CHUNKS and S_CDC outputs without FIFO blocking, while preserving exact logical bytes, its original archive and external alias targets? Will a deliberately damaged physical chunk be rejected before any existing regular output is replaced?

**P1 (positive):** each exact frozen archive extracts onto fresh, pre-existing regular, FIFO and symlink-to-FIFO outputs in bounded subprocess time; no FIFO open hangs; full logical SHA matches frozen oracle; original archive SHA remains identical. Same expected for symlink-to-external-regular and hardlinked-existing-leaf variants; the current staged replace semantics should preserve *external* targets by replacing only the destination directory entry.

**P2 (negative/falsifier):** corruption of a physical chunk in an independently fixed archive should raise during extraction and leave the previously existing regular output bytes+inode intact. Any partial temp publication, unexpected clean return, or changed external target falsifies the claimed staged integrity.

**Controls:** one original unchanged reference artifact per physical mode and its authored logical digest, direct `CMPCT.read` + `CMPCT.verify`, unchanged source archive hashes across all destination cases, pre-existing regular-file identity and external alias bytes. A fixed vector is not a Builder/Writer regression test. Distinguish a negative process timeout from a successful fixed-stream extraction.

## BONK / alternatives

A code review predicts both modes share `_extract_chunked_verified`; that is weaker than real hosted installed extraction of independently authored archives. Builder-generated larger data would add generator-selection uncertainty and cost but no stronger format independence. Rewriting the Reader or staging path would overlap #269/#472/#479 and risk altering old semantics: **no product mutation** is authorized by this independent conformance question. A small fixed-byte court with independent SHA and killable subprocesses can decide this fork cheaply.

## Evidence and kill/narrow criterion

Prefer 2-host Ubuntu 24.04/macOS 14 exact-head GitHub Actions with ordinary `pip install . pytest` outside-repo execution, a tamper attempt per storage kind, JUnit plus row-level structured receipts. If any prerequisite fails, preserve it as such; do not fake a product outcome or change the frozen vectors. The run must expose source HEAD, Reader blob, fixed vector blob, installed module path, exact row results, timeout boundary, and artifact/run ID. Abort false-positive conclusions if source identity does not match or no real S_CHUNKS/S_CDC row is present. Source-bound result must not be extrapolated to concurrent directory replacement, Windows named pipes, power-loss persistence, arbitrary hostile archives, or global file durability.

No format/core version change, no frozen benchmark modification, no release credit and no score inference from a CI wrapper. Once decision-changing result is obtained, stop this narrow family and return to the larger CMPCT product frontier. Leave discovery STATE under its independent owner (#440) unless current authority demands a coordinated truth change.
