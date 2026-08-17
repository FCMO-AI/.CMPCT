"""Hardened entrypoint for the v0.30 complete Synthetic Phrase Substrate benchmark.

Importing the safety facade first patches the shared CMPNX15 module object so both the benchmark's strong
verification and any extraction path preflight logical materialization bounds before joining phrase bytes.
The benchmark implementation itself remains one source of truth for frozen corpus identity and size gates.
"""
from experiments import entropygraph_v030_attractor_substrate_safe as _SAFE  # noqa: F401
from benchmarks import attractor_substrate_v030_probe as IMPL


if __name__ == "__main__":
    IMPL.main()
