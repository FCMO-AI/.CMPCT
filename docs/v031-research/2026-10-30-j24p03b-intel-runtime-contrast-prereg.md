# J24P03b — Can Intel actually use the dual wheel while rejecting the mislabeled plain wheel?
Date: 2026-10-30
Status: PROSPECTIVE before new Intel-host workflow instrumentation

## Inherited scientific evidence, separated from new question
J24P03 source-exact macos-15 arm64 CI #41115073535 / commit `0b0ee0e9ad9e482cc99fddff5002532b3ada08d4` already returned H1_SURVIVES_ONE_HOST. An independent, dependency-free physical Mach-O parser against the **actual two original GitHub wheel bytes** reproduced: direct no-ARCHFLAGS `cmpct-0.30.0-cp311-cp311-macosx_11_0_universal2.whl` carried only ARM64; direct `ARCHFLAGS="-arch arm64 -arch x86_64"` `cmpct-0.30.0-cp311-cp311-macosx_10_12_universal2.whl` carried both architectures. This proof is about *packaging bytes* only, not Intel execution.

## New primary H2
On a **real GitHub-hosted macos-15-intel x86_64 process**, installing *the same physical wheel bytes* from the ARM builder:
- H2a positive control: dual wheel should install, load its x86_64 native cdylib, and perform the established `tests/installed_native_package_smoke.py` complete native Zstd / CMPCT representative create-read-extract roundtrip without ambient python-zstandard.
- H2b negative control: the falsely universal2 ARM-only wheel should be accepted by a normal CPython 3.11 Intel pip installation due to its tag but `ctypes.CDLL` on its actual installed ARM-only binary must fail with an architecture-specific loader error, rather than execute silently.
- H2 can fail on the dual wheel not installing/loading, on the plain wheel unexpectedly executing successfully, on any wheel-to-installed SHA mismatch, or on an Intel runner masquerading as x86_64.
- A plain wheel refused at *tag admission* rather than load-time narrows, but does not confirm H2b. Preserve raw results and do not count unrelated import dependency errors as architecture failure.

## Controls, resource, and claim boundaries
Use exact same-source ARM producer artifact generated within the same workflow run, not a newly compiled Intel substitute. SHA pin both files to the producer receipt; install into two disjoint virtual environments. Ensure test process architecture `platform.machine() == 'x86_64'`; confirm each installed native SHA equals original wheel member. Run a full smoke only for the dual arm, while plain arm tests the loader failure carefully. This earns native-runtime interoperability evidence **only** for this pair and x86_64 macos-15, not a shipping official product release, Apple Silicon runtime (already previously tested separately), other Python versions or full package distribution matrix.

Existing authoritative exactness, format, release, benchmark, post-load ownership and semantic gates are unchanged. H1 was prospectively frozen and executed on its earlier exact head, not retroactively reinterpreted. Do not overwrite #843 loader or #850 installed-package workflow and do not modify issue #851's observed negative.
