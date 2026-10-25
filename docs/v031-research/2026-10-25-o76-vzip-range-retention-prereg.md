# O76 preregistration — VZIP selective range versus Deflate-stream retention

**Status:** prospective hypothesis frozen before implementation or new measurements. **Authority:** `AGENTS.md`, `docs/discovery/DISCOVERY_ENGINE.md`, v0.31 release/format law. **Parent:** `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; Builder `663ef0922992b1fbb8f19e6eea88d55c10a56044`, Reader `e716233403dabd0966863c45635e18fa5ac6afb8`, Codec `29526db4203723d83523fc95d074c346b63d7587`.

## Distinct question and mechanism

O70/O73 study **S_PACK physical-owner grouping**. O68/O71 study **VZIP creation/admission**. O76 instead asks whether a **single S_VZIP file using stream mode 2 (regenerate Deflate from large raw logical member)** exports an extreme, hidden decode/re-encode cost to a request for only 64 physical ZIP bytes. `range_vzip` calls `get_stream(mode=2)`, which calls `_blob(rawidx)` and zlib recompresses the complete logical raw content. A reader-selective request is not automatically proportional to the requested length. Changing `Builder(deflate_reuse_min)` from 65536 to 0 retains an existing exact Deflate stream as mode 0, without any wire, Reader or decoder change; this is a **generous existing-product policy oracle**, not a proposed new default.

## Prospective trial

Use **same exact physical source** in each arm, with 2 MiB repeated-byte, 8 MiB periodic-byte, and 2 MiB mixed/partially random ZIPs made with stdlib `ZIP_DEFLATED` level 6, each as one `.zip` in an otherwise empty tree; a 2 MiB independently random archive is a negative eligibility control. Each should remain a valid ZIP. Both arms must construct, verify, full-read, and exact-extract authentic CMPCT r24; 64 physical bytes selected from *inside the original ZIP's first Deflate stream* must match the exact source bytes and must be read using `CMPCT.read_range`. Assert both arms use `S_VZIP` and record the actual recipe mode for every case; do not invent mode 2 if selector chooses otherwise. For mode-2 eligible cases, collect 12 alternating A/B fresh-Reader paired samples of `read_range` wall and process CPU, full archive bytes, full create wall/CPU, complete verify wall, materialized logical bytes through `_blob` (instrumentation, not disk I/O), exact SHA identities, and at least one complete extraction per arm. Preserve raw observations.

## Decision rule / falsifiers

The narrow performance hypothesis survives **only** if at least two structurally different eligible inputs truly select baseline mode 2 versus retained mode 0, every semantic comparison passes, and retained-stream median 64-byte read time is **at least 8× faster** with no hidden second decoder and no more than **64 KiB** extra complete stored bytes *per archive*. An input not selecting the presumed modes narrows eligibility; a semantic failure kills the proposed policy route. A >64 KiB debt or <8× improvement kills **this bounded intervention**, even if other observations remain useful. A mode-0 alternative is **not** a Pareto win unless the full size/create/verify/selective-read surface is acceptable; record actual debt even when hypothesis survives. Negative/random control must not be relabeled as positive.

## Stronger controls and alternative explanations

Equal physical ZIP bytes, archive metadata, toolchain and Reader/Codec code; only the encoder's existing stream-retention threshold differs. Separate one-time source/build work from warm library read and process startup. Compare the equal-byte opaque path in future only if it changes a decision; avoid an unnecessary third arm now. The historical VZIP retention design may already justify mode 2 for byte economy: a read win that exports large stored bytes, creator work or RSS is not domination. Structural analysis is a cheaper discovery rung; hosted source-exact installed product is the next rung, not a full official benchmark.

## Scope / coordination / release

This branch owns a **non-product scientific instrument only**. No Builder/Reader/Codec/format changes, no frozen dataset/comparator edits, no v0.31 release or merge. O70 #426, O73 #429, O68 #424 and O71 #427 continue independently. Store exact head and run/artefact identities on results; never reinterpret a skipped CI job as a pass. Any result is Ubuntu CPython 3.11 research scope until stronger independent evidence exists.
