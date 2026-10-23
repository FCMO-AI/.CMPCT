# v0.31 direct-Deflate ZIP-export integrity falsifier — preregistered 2026-10-23

**Status:** pre-result scientific/control court; no product-code ownership, release promotion, or revision-24 mutation.

## Authority and scope
- Canonical candidate source: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`.
- Reader blob: `e716233403dabd0966863c45635e18fa5ac6afb8`; codec blob `29526db4203723d83523fc95d074c346b63d7587`; independent fixed fixture `tests/conformance/v24-direct-codecs.json` blob `d10b7dab9126d39e819a74279c186363a163f2ef`.
- ZIP64 count/product ownership remains with PR #260; this is a **different narrow question** about direct-Deflate stream integrity, with no edits to its Reader, workflows or evaluations.

## Primary question / baseline
The official `CMPCT.export_zip()` fast path calls `_direct_deflate_stream()`, which returns encoded RFC-1951 bytes and the CRC declaration from the physical header without invoking the normal file-read CRC check. **Prediction:** a single in-place corruption of the physical blob's CRC32 declaration causes ordinary `CMPCT.read()` to reject the file, but `export_zip()` still returns success and writes a ZIP whose independently decoded member is rejected by Python's `zipfile`. A second one-byte corruption of the retained Deflate payload should reproduce the same discrepancy. A pristine builder-independent v24 Deflate vector must pass both operations.

## Controls, alternatives, kill/narrow
- Independent oracle: CPython `zipfile`, which reads/checks the exported archive rather than trusting CMPCT's return value. Also use `CMPCT.read()` on the exact same tampered source. Compare the original fixture SHA and exact logical payload.
- Stronger simpler control: keeping this as a research-only read/export contradiction while PR #260 owns export optimizations. Do not immediately add a second exporter or change its CRC semantics.
- Alternative explanations: not a malformed index or missing codec; only one byte inside a known valid physical record changes, and `CMPCT(...)` must open the same index. A ZIP reader rejecting only an invalid archive *after* export does not prove export itself rejected it.
- Disproof: if `export_zip()` itself rejects both corruptions before reporting success, the predicted bypass does not occur. If only one corruption reproduces, narrow accordingly. A missing native package/dependency is an infrastructure error, not a clean negative.
- Economical rung: three tiny 425-byte input archives and a standalone installed-package oracle; no expensive release parity/size/throughput run.

## Cost and safety boundary
No decompression algorithm or source format is modified. This court cannot prove an eventual fix's runtime cost. Any future product fix must verify retained Deflate bytes without sacrificing the exact stream identity, should price CPU/RSS/streaming versus the current zero-recompression exporter, and must preserve ZIP64 owner #260's independent counts and fallback behavior. CRC and SHA consistency do not amount to authenticated provenance.

## Handoff
Record all outcomes, exact source SHA and independent ZIP reader results. If the bypass is confirmed, notify PR #260 and open a narrow remedy issue/PR without changing another agent's active implementation. Do not weaken strict archive conformance or treat a scientific negative as release credit.
