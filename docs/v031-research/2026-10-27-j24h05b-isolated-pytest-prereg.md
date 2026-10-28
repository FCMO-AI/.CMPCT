# J24H05b — Prospectively isolate the narrow hosted product court from unrelated repository-wide conftest

**Date:** 2026-10-27 UTC. **New fork declared after observing first J24H05 hosted attempt #40608360843, before modifying the workflow.** The original three-host results remain FAIL/INCONCLUSIVE for product, not waived.

## Direct observed failure
On exact source HEAD `606b42b5ff91a50d63ade71ad2bc9ae860684b2a`, Ubuntu J24H05 setup, Git-object checks, installed package source identity all passed, then pytest failed **before collecting any tests** at repo `tests/conftest.py` because unrelated experiment imports need `zstandard`. macOS likewise failed before test collection because importing the unrelated historical `experiments/entropygraph_v025.py` attempts `ctypes.CDLL(libzstd.so)` with no shared library. These are test-runner environment/dependency failures, NOT observed Reader extraction failures or negative evidence of the J24H05 mechanism.

## New hypothesis / control / kill
Copy the two **unchanged Git-identity-verified** J24H05/O167 test scripts to a sibling `j24h05-isolated/` directory under repo root, then invoke pytest on those paths. This preserves exactly the same test bodies and acceptance assertions, but avoids discovery of `tests/conftest.py` and its external experiment imports. This matches the isolated genuine O167 testing architecture in O167's original hosted workflow. Install the exact package as before, keep unchanged all 3 platforms, test counts (5; 0 Win32 skips, 1 POSIX skip), source fingerprints, original reparse-target refusal, timestamp and inode conditions, and failure artifacts.

**Disproof:** the isolated test still fails at import/collection or a product assertion fails. A production assertion failure is product evidence to be diagnosed and not reclassified as infrastructure. Do NOT disable tests, skip hosts, install a fake zstd, relax expected outcomes or claim that original red was green. This is a minimal evidence-routing repair, not new product implementation.
