"""v0.30-only worker seam for transfer-proven shared-portfolio optimizations.

Historical v0.29 modules remain untouched. The canonical v0.30 private shared-portfolio clone binds this module as
its spawned-worker provider. Two independently proven execution-only changes therefore stay scoped to the v0.30
candidate children: the byte-dead position-independent attempt-5 discovery source is neutralized, and repeated
pack-plan pricing reuses only exact compressed lengths for structurally identical groups inside one six-limit
selector tournament. Raw/compressed payloads are never retained across trials.

Inherited LSH discovery, candidate scoring, compression level, pack-plan tie/admission law, archive grammar,
residual packing and accepted-v0.29 floor selection remain unchanged. Every temporary override is restored before
the child exits so historical/research imports remain independent byte/evidence oracles.
"""
from __future__ import annotations
from pathlib import Path
import time
from experiments import entropygraph_v029_parallel_portfolio as _HISTORICAL_SCHED
from experiments import entropygraph_v029_residual_fast as accepted
from experiments import entropygraph_v030_pack_plan_cache as _PACK_CACHE
CHILD_RESULT_TIMEOUT_S = _HISTORICAL_SCHED.CHILD_RESULT_TIMEOUT_S
ACCEPTED_ENGINE = _HISTORICAL_SCHED.ACCEPTED_ENGINE

def _no_position_independent_candidates(_sketches, _nodes): return []

def _install_pack_cache(owner):
    original = owner._choose_pack_plan
    def cached_choose(nodes, sketches, root_ids):
        chosen, trials, _stats = _PACK_CACHE.choose_pack_plan_cached(
            nodes, sketches, root_ids, owner=owner, compress_record=owner._compress_record)
        return chosen, trials
    owner._choose_pack_plan = cached_choose
    return original

def _worker(kind: str, root_s: str, out_s: str, queue) -> None:
    root=Path(root_s); out=Path(out_s); started=time.perf_counter()
    pack_owner=original_choose=position_owner=original_position=None
    try:
        if kind == "v028":
            pack_owner=accepted.V028; original_choose=_install_pack_cache(pack_owner); stats=accepted.V028.build(root,out)
        elif kind == "attempt5":
            pack_owner=accepted.BASE.P.PARENT.V028; original_choose=_install_pack_cache(pack_owner)
            position_owner=accepted.BASE.P; original_position=position_owner._position_independent_candidates
            position_owner._position_independent_candidates=_no_position_independent_candidates
            stats=accepted.build_graph(root,out)
        else: raise ValueError(kind)
        queue.put({"kind":kind,"ok":True,"elapsed_s":time.perf_counter()-started,"stats":stats})
    except BaseException as exc:
        queue.put({"kind":kind,"ok":False,"elapsed_s":time.perf_counter()-started,"error":repr(exc)})
    finally:
        if position_owner is not None and original_position is not None: position_owner._position_independent_candidates=original_position
        if pack_owner is not None and original_choose is not None: pack_owner._choose_pack_plan=original_choose

__all__=["CHILD_RESULT_TIMEOUT_S","ACCEPTED_ENGINE","_worker"]
