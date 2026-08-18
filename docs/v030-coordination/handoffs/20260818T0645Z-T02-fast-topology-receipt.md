# T02 fast / topology receipt

- Source SHA: `e3c9533e5911210ed7b4cf823536c5d2ebcdc7db`
- GitHub Actions run: `32108213897` attempt `1`
- Python: `3.11.15`
- Platform: `Linux-6.17.0-1022-azure-x86_64-with-glibc2.39`
- Runner: `Linux/X64`
- Result: **PASS** — this file is committed only after every command below exits zero.

## Fast contract output

```text
$ python -m py_compile benchmarks/v030_release_ablation_canonical.py benchmarks/v030_perf_worker_canonical.py benchmarks/v030_release_selective_read_canonical.py

$ python -m pytest -q tests/test_v030_release_ablation_contract.py tests/test_v030_release_selective_read_contract.py
..........                                                               [100%]
10 passed in 0.24s

$ python tools/check_public_surface.py
CMPCT disclosure guard: clean (445 tracked text files checked)

```

## Exact topology checker output

```text
$ python tools/check_ci_topology.py <17 coordinator-listed v0.30 workflows>
.github/workflows/geometry-v030-breakthrough.yml: topology OK
.github/workflows/v030-authoritative-pr-gates.yml: topology OK
.github/workflows/v030-authoritative-v2-pr.yml: topology OK
.github/workflows/v030-canonical-authority.yml: topology OK
.github/workflows/v030-external-competitors.yml: topology OK
.github/workflows/v030-g04-overlay-oracle.yml: topology OK
.github/workflows/v030-geometry-overlay-oracle.yml: topology OK
.github/workflows/v030-gir-build-rehab.yml: topology OK
.github/workflows/v030-gir-focused-complete.yml: topology OK
.github/workflows/v030-gir-hardening.yml: topology OK
.github/workflows/v030-hierarchical-geometry.yml: topology OK
.github/workflows/v030-prefixgraph-oracle.yml: topology OK
.github/workflows/v030-release-fuzz.yml: topology OK
.github/workflows/v030-release-generalization.yml: topology OK
.github/workflows/v030-release-performance.yml: topology OK
.github/workflows/v030-release-reader.yml: topology OK
.github/workflows/v030-shared-portfolio-rehab.yml: topology OK

$ python tools/check_ci_topology.py .github/workflows/v030-coop-evidence-performance.yml
.github/workflows/v030-coop-evidence-performance.yml: topology OK

```

Footnote: this receipt proves the slot-02 harness contracts and CI topology on the source SHA above. It does not claim final product/compression/runtime/competitor authority; those remain bound to the exact T00 reconciled candidate after corrected T01/T03 import.
