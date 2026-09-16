from __future__ import annotations

"""Bind the fast-solid research oracle to the frozen external-comparison tree identity.

The external compression matrix intentionally compares regular-file content because ZIP/tar/Zstd do not preserve
all canonical r25 filesystem metadata symmetrically. Keep this research oracle in exactly that same identity domain
before importing/running the reusable implementation.
"""

from benchmarks import v030_external_competitors as B
from experiments import entropygraph_v030_release as HISTORICAL_TREE

B._tree = lambda root: HISTORICAL_TREE.treehash(root)

from benchmarks.v030_fast_solid_oracle import main  # noqa: E402


if __name__ == "__main__":
    main()
