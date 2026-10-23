# VZIP Mode-2 native backend exact-byte feasibility — preregistration (2026-10-23)

**Episode:** VZIP-M2-BACKEND-001. **Research-only; no product support/promotion.**
**Source boundary:** agent/phased3-v031-independent-vzip-mode2-golden-r259-20261023@bce6aa4b78a0e9c21faf67033a031e8fce4c0551, based on agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b.
**Fixed independently constructed conformance anchor:** tests/conformance/v24-virtual-zip-deflate-mode2.json (86​1-byte archive SHA-256 febef1d1f1157066204c468d74e81e14c6f79d1490ab2e76e024beed3ce3fb81, 75-byte payload, Deflate level 6 bytes 4b4c4a4ec483929350105ec500).
**Current Rust backend:** native/cmpct-core/Cargo.toml: flate2 1.x with default features disabled and rust_backend enabled. **Reference:** installed CPython zlib compressobj(level, DEFLATED, -15); this matches Python CMPCT's VZIP stream-mode-2 reconstruction contract.

## Question and hypothesis

Can the *currently shipped native dependency backend*, without adding a zlib C dependency or retaining a Deflate copy, regenerate exactly the RFC-1951 bytes that the Python r24 mode-2 recipe expects? Distinguish lossless inflate compatibility from exact compressed-byte compatibility.

**Prediction (before measurement):** a byte mismatch on at least one held-out data family/level is plausible even if both deflate streams independently decompress to identical bytes. If all comparisons match, evidence remains bounded to the tested codec versions/inputs, not universal cross-platform proof.

## Independent controls and procedure

Build a small detached Rust binary against the package-owned flate2 dependency, read bytes from stdin and return the native raw-Deflate stream at levels 1,6,9; compare against Python `zlib.compressobj(level, zlib.DEFLATED, -15)` on the same Linux runner, with identical complete input, without process-start performance claims. Include the immutable 75-byte golden, runs of zeros, seeded incompressible bytes, repetitive patterns, log-like lines, shifted shared blocks and held-out mixed JSON/structured bytes. For each compare raw byte equality, compressed sizes, independent zlib inflate correctness, logical SHA-256, native and Python stream SHA-256, and deterministic repeated native emission. Preserve native/CPython/zlib versions, full per-case JSON, exact source/head SHA and job identity.

**Strong simpler control:** mode 1 already retains exact Deflate physical bytes, so it never depends on compressor determinism; current native mode-2 typed Unsupported remains correct regardless of the result.

**Alternative explanation:** mismatches can arise from compressor implementation or flush strategy, even when both streams are standards-compliant. Use single full-stream finish, raw mode and identical level to isolate; avoid claiming a particular root cause without controlled backend A/B.

**Kill/narrow condition:** ANY difference between valid native and Python streams falsifies drop-in use of the current rust_backend as a universal exact mode-2 generator; no threshold changes or approximations. Any independent decompression failure indicates probe instrumentation invalidity rather than a CMPCT product regression. All matches only justify expanding toward full native product/portability courts, not enabling dispatch.

## Scope and cost

O0/O1 backend-scoped research, not a CMPCT archive-size/create/extract benchmark. Native binary is an experiment, not linked into published Reader; no format, version, release gates, comparators, existing golden bytes, or support statuses may change. Probe materializes at most 1 MiB/sample; source bytes are synthetic/public. Do not claim peak product RSS, streaming extraction, selective locality or all-version cross-zlib exactness.

**Decision unlocked:** choose between native exact zlib-version reproduction, pre-storing RFC-1951 mode-1 bytes, or leaving native mode-2 explicitly unsupported. Preserve nonmatches.
