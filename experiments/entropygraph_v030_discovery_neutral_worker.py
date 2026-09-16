"""v0.30-only worker seam for the transfer-proven byte-dead attempt-5 discovery source.

Historical v0.29 modules remain untouched.  The canonical v0.30 private shared-portfolio clone binds this module
as its worker provider, so the position-independent candidate source is neutralized only inside the spawned
attempt-5 child and restored before that child exits.  Inherited LSH discovery, candidate scoring, archive grammar,
residual packing and v0.29 floor selection are unchanged.
"""
from __future__ import annotations

from pathlib import Path
import time

from experiments import entropygraph_v029_parallel_portfolio as _HISTORICAL_SCHED
from experiments import entropygraph_v029_residual_fast as accepted

CHILD_RESULT_TIMEOUT_S = _HISTORICAL_SCHED.CHILD_RESULT_TIMEOUT_S
ACCEPTED_ENGINE = _HISTORICAL_SCHED.ACCEPTED_ENGINE


def _no_position_independent_candidates(_sketches, _nodes):
    return []


def _worker(kind: str, root_s: str, out_s: str, queue) -> None:
    """Build one shared candidate with the v0.30 R3 neutralization scoped to the attempt-5 child."""
    root = Path(root_s)
    out = Path(out_s)
    started = time.perf_counter()
    try:
        if kind == "v028":
            stats = accepted.V028.build(root, out)
        elif kind == "attempt5":
            owner = accepted.BASE.P
            original = owner._position_independent_candidates
            owner._position_independent_candidates = _no_position_independent_candidates
            try:
                stats = accepted.build_graph(root, out)
            finally:
                owner._position_independent_candidates = original
        else:
            raise ValueError(kind)
        queue.put({"kind": kind, "ok": True, "elapsed_s": time.perf_counter() - started, "stats": stats})
    except BaseException as exc:
        queue.put({"kind": kind, "ok": False, "elapsed_s": time.perf_counter() - started, "error": repr(exc)})


__all__ = ["CHILD_RESULT_TIMEOUT_S", "ACCEPTED_ENGINE", "_worker"]
