from __future__ import annotations

"""Decision probe: move only the Logs selector's r24 candidate into the proven one-shot child.

This is deliberately not a product module.  It reuses the exact promoted r24 child owner while leaving Logs
construction, admission, publication, verification and every frozen runtime threshold unchanged.  The experiment
answers one narrow question: is the residual Logs parent-RSS red caused by the selector still building its r24
control in a parent thread after canonical-final r24 ownership moved to a child?
"""

import time
from pathlib import Path

from benchmarks import v030_perf_worker_v2 as W


_BASE_ENGINE = W._engine


def _engine(name: str):
    engine = _BASE_ENGINE(name)
    if name != "v030":
        return engine

    logs = engine._LOGS_PROMOTED
    if getattr(logs, "_cmpct_logs_r24_process_probe", False):
        return engine

    from experiments.entropygraph_v030_r24_process_prebuild import R24PrebuildProcess

    def process_r24_candidates(root: Path, temp: Path):
        r24_path = Path(temp) / "candidate-r24.cmpct"
        logs_path = Path(temp) / "candidate-logs.cmpct"
        started = time.perf_counter()
        proc = R24PrebuildProcess(Path(root), r24_path)
        proc.start()
        try:
            # Preserve useful overlap: Logs remains parent-owned while the exact canonical r24 control is child-owned.
            logs_stats = logs._build_logs(Path(root), logs_path)
            r24_stats = dict(proc.result())
        finally:
            proc.close()
        r24_stats["archive_bytes"] = r24_path.stat().st_size
        return r24_stats, logs_stats, r24_path, logs_path, time.perf_counter() - started

    logs._parallel_candidates = process_r24_candidates
    logs._cmpct_logs_r24_process_probe = True
    return engine


W._engine = _engine

if __name__ == "__main__":
    W.main()
