"""Stable v0.29 research entrypoint: accepted attempt #5 with byte-identical portfolio scheduling.

This module is the release-facing research wrapper for Mosaic / Residual Program Packing. Multi-file
inputs build the exact embedded v0.28 fallback and exact accepted attempt-5 graph concurrently, then
apply the unchanged smaller-artifact tournament. Single-file inputs preserve the accepted sequential
fast-reject policy so the scheduler cannot re-introduce the known 22.8x dead-end audition.

The output grammar is still experimental ``CMPNX11`` when the attempt-5 graph wins and inherited
research grammar when it falls back. Canonical CMPCT revision 24 is deliberately untouched.

Footnote: this wrapper exists so a measured scheduler improvement becomes a usable research-engine path
rather than living only inside a benchmark oracle. It delegates all parsing, extraction, verification,
hashes and grammar constants to the already-accepted attempt-5 implementation; only creation scheduling
is new. Any future reader-visible promotion still requires a new canonical format revision and its own
conformance/native/recovery/portability work.
"""
from __future__ import annotations

from pathlib import Path
import statistics
import time

from experiments import entropygraph_v029_parallel_portfolio as scheduler
from experiments import entropygraph_v029_residual_fast as accepted

ACCEPTED_ENGINE = scheduler.ACCEPTED_ENGINE
MAG = accepted.MAG


def __getattr__(name: str):
    """Expose the accepted attempt-5 grammar/runtime surface without forking it.

    Footnote: module-level delegation keeps hostile-test hooks and future parser fixes authoritative in
    one implementation. Functions defined here override only the release scheduling/bench surface.
    """
    return getattr(accepted, name)


def build(root: Path, out: Path) -> dict:
    """Build the accepted attempt-5 portfolio with the release scheduler."""
    result = scheduler.build_parallel(root, out)
    result["release_engine"] = ACCEPTED_ENGINE
    result["canonical_format_revision"] = 24
    result["research_magic"] = "CMPNX11-or-inherited-fallback"
    return result


def extract(archive: Path, dst: Path) -> None:
    accepted.extract(archive, dst)


def strong_verify(archive: Path) -> dict:
    return accepted.strong_verify(archive)


def bench(root: Path, out: Path) -> dict:
    result = build(root, out)
    samples: list[float] = []
    for _ in range(3):
        started = time.perf_counter()
        strong_verify(out)
        samples.append(time.perf_counter() - started)
    result["strong_verify_median_s"] = statistics.median(samples)
    result["tree_sha256"] = accepted.BASE.treehash(root)
    return result
