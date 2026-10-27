# O228c — native CDC versus fallback: prospective source-mode discriminator

**Prerecorded before new instrument/hosted results, 2026-10-27 UTC.** Continuation of O228/O228b research PR #600; no released format/Reader/Builder modification. The previous O228b host produced 64 fixed 256-KiB chunks for every 16-MiB source while the codec can silently fall back when the optional `libcmpct_cdc.so` is not packaged. An observed S_CDC storage tag does **not** prove native chunk boundaries. O228b's negative is accurate for its actual environment, but does not answer the native mode.

## Primary question and independent control

Using the **unchanged released Builder** and **identical deterministic bytes** for each of six O228b sources, does a genuinely loaded native CDC helper produce two **nontrivial** adjacent repeated-(length, owner) reference families with >=8 consecutive references, >=2x complete-MessagePack unpack-heap saving and no complete duplicated-compressed-index byte debt, and at least one family with >=1% whole-archive byte saving? Compare against the actual Builder running with `cmpct.codec._cdc = None` in the same process/platform, not a synthetic index and not a separately generated corpus. Retain native and fallback source hash, codec mode, original archive SHA, source SHA, exact roundtrip and every negative.

## Stronger-source control / validity condition

Build the **exact canonical `native/cmpct_cdc.c` source** as a temporary shared helper into the package path on the CI runner; prove `cmpct.codec._cdc is not None` after import, capture helper source Git blob SHA and runtime library SHA. In the same installed Builder version, set `_cdc=None` explicitly for fallback and restore the same loaded helper for native. Never alter CDC constants, native C source, codec semantics, Builder search or dedup policy. Require at least two nonzero source profiles with native reference length sequence differing from fixed fallback; otherwise `INSTRUMENT_INVALID`, not a product conclusion. Record the `_cdc` mode flag and count/nonuniform length signature in every row. Treat a runtime C error as infrastructure/instrument failure, not negative compression evidence.

## Measurements and decision law

Use the existing O228b `profile()` and its **same-input actual Builder + Reader** verification and isolated unpack child measurements to avoid replacing a proven instrument. For each corpus × both modes measure exact logical hash, whole CMPCT bytes, index bytes including doubled primary/tail index, hypothetical run-bearing *complete* index bytes, build wall/CPU, candidate index encode wall/CPU, isolated index unpack peak heap, references, distinct owners, runs, and maximum run. Require all genuine Reader `verify/read/read_range` controls to pass and source hashes/inputs to match mode-to-mode.

- **`NATIVE_TRANSFER_SEED`** only if >=2 different nonzero nonrandom families meet the joint run/heap/no-byte-debt bar AND at least one whole archive shrinks >=1% while native mode differs genuinely from fallback.
- **`NO_NATIVE_BUILDER_TRANSFER_AT_16MIB`** if modes genuinely differ and no joint prospective gate is reached.
- **`INSTRUMENT_INVALID`** if mode identity, exact bytes, source, reading, or segmentation validity cannot be established.
- Preserve the historical O228 synthetic positive and O228b fallback negative irrespective of decision. Do not use future threshold shifts, only a later materially different information/ownership frame if native transfer fails.

## Risks / scope

Because `CDC_MIN=128 KiB`, a 16-MiB file can carry at most 128 positive-length native references. This imposes a strong likely headroom ceiling but is not substituted for measuring the actual Builder. A low candidate index saving can never earn product credit without complete archive, Reader, memory, CPU, update/recovery, adverse input and multiplatform economics. Native CDC C boundary-extreme defect #606 is separate and not exercised via atypical chunk parameters here; coordinate with its owner, no duplicate patch. No `STATE.json` mutation (PR #574 owns reconciliation), no new format tags on disk, no release, no merge.