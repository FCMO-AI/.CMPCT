from __future__ import annotations
"""Research import surface for the shipping-shaped v0.30 materialization candidate.

Keeping the experiment as a thin alias prevents benchmark/product drift: component A/B
now executes the exact implementation that the release-owned guard would invoke.
"""
from cmpct.v030_release_materialization import SPOOL_MEMORY_LIMIT, StreamedBuilder

__all__=['SPOOL_MEMORY_LIMIT','StreamedBuilder']
