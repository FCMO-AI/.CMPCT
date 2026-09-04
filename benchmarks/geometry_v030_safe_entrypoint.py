"""Run the Geometry generalization gate with hostile-input CPU bounds installed first.

Import order is intentional: the safe facade patches the single research module object used by the
benchmark, so the measured archive bytes are produced under the same bounded writer/reader helpers that
would be required for promotion.
"""
from experiments import entropygraph_v030_geometry_safe  # noqa: F401  # installs bounds by import
from benchmarks.geometry_v030_generalization_bench import main

if __name__ == "__main__":
    main()
