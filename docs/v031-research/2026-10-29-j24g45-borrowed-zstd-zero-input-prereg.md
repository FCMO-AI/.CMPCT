# J24G45 — borrowed ctypes input for physically verified encoded-empty Zstd (prospective)
Date: 2026-10-29 UTC. Research/product-candidate continuation of #767, **not a release**.

## Exact baseline and primary question
#767 `e88797831e72a23ae0fd1aff6ad7b3c21cfd5ede` passes its installed zero-output physical integrity court in Ubuntu/macOS/Windows; unchanged general tests fail independently. Its new correct zero-output path still calls `_src(data) = ctypes.create_string_buffer(data)`, making a second compressed-input copy despite a one-byte destination. The original J24G44 bounded 16 MiB input micro measured an additional 16 MiB memory allocation. Product memory and performance are unmeasured.

Question: can we remove this newly exported copy *only for nonempty zero-logical-output Zstd frames*, without altering historical nonzero/ordinary codecs, signed r24 identity, native ABI, decodability or error behavior?

## Hypothesis, stronger controls, competing routes
For immutable Python `bytes`, `ctypes.c_char_p(data)` retains the bytes reference in its `_objects` while passing a pointer to its existing payload. The native signatures all receive explicit lengths, so embedded NULs do not truncate. The local observation that `ctypes.c_char_p` is accepted as `c_void_p` and borrows the identical CPython `PyBytes_AsString` pointer is micro-level evidence only. Keep `_src` for all existing nonzero, compressor and dictionary creation flows as the stronger unchanged-product control.

Alternatives: (1) retain copying (simpler, measurable memory debt); (2) `ctypes.from_buffer_copy` (still copies); (3) Python C-API `PyBytes_AsString` (CPython-only and more lifetime burden); (4) alter Rust ABI (unnecessary wider ownership). Prefer the narrow c_char_p lifetime-bearing wrapper if installed experiments pass.

## Disproof / bounds / adversarial controls
- On actual installed Python+native packages in Ubuntu/macOS/Windows, authentic r24 signed valid Zstd-empty must pass and malformed header / nonempty decoded length must reject as before.
- Run unchanged direct-codec and dictionary golden controls.
- Independently verify that bytes containing embedded zeros are passed with the **full explicit length**, and that the borrowed object holds its source reference. On CPython compare native address with `PyBytes_AsString` using a bounded probe; skip implementation-specific address comparison on other runtimes, not the functional decoding checks.
- On a 16 MiB immutable `bytes` specimen, isolate buffer construction and compare allocation/CPU against `create_string_buffer`: expect at least 8 MiB reduction in incremental allocation and the same input bytes at native pointer, not a promise about full Reader RSS. Probe with `tracemalloc` locally and using installed-source tests (OS allocator RSS can differ).
- Do not weaken any existing test, semantics, size/memory limit, parser, native ABI, comparator, or promotion threshold. Treat a failed installed host, unexpected pointer lifetime, frame acceptance difference, or memory non-improvement as falsification and revert/retire.

## Ownership and publication
Continue the existing Python-codec owner PR #767 on its exact source; native Rust #759/#765 and competing Reader owners remain separate. No main, format, release, `STATE.json` or frozen test mutations. An independent external Zstd decoder remains authoritative for physical corruption controls. Only the specialized extra-copy debt can receive research credit from micro probes; integrated measured performance/release credit requires full product evidence.
