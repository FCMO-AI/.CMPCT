#!/usr/bin/env python3
"""J24I55 research-only source-identical Builder phase and fault instrument."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import resource
import statistics
import sys
import time

import cmpct
from cmpct import builder as bm
from cmpct.native_codec import _library_path

STAGE_METHODS = ("scan", "_build_micro_packs", "_prepare_deflate_reuse", "_train_dictionary")
STAGES = (*STAGE_METHODS, "ordered_encode")
ACTIVE = None

def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while block := f.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()

def install_stage_instrument() -> None:
    for name in STAGE_METHODS:
        old = getattr(bm.Builder, name)
        def instrumented(self, *args, _old=old, _stage=name, **kw):
            global ACTIVE
            if ACTIVE is None:
                return _old(self, *args, **kw)
            w0, c0 = time.perf_counter_ns(), time.process_time_ns()
            try:
                return _old(self, *args, **kw)
            finally:
                c1, w1 = time.process_time_ns(), time.perf_counter_ns()
                assert _stage not in ACTIVE["phases"], ("duplicate phase", _stage)
                ACTIVE["phases"][_stage] = {"wall_ms": (w1-w0)/1e6, "cpu_ms": (c1-c0)/1e6}
        setattr(bm.Builder, name, instrumented)
    old_pull = bm.ordered_worker_pull
    def instrumented_pull(*args, **kw):
        global ACTIVE
        if ACTIVE is None:
            return old_pull(*args, **kw)
        w0, c0 = time.perf_counter_ns(), time.process_time_ns()
        try:
            return old_pull(*args, **kw)
        finally:
            c1, w1 = time.process_time_ns(), time.perf_counter_ns()
            assert "ordered_encode" not in ACTIVE["phases"]
            ACTIVE["phases"]["ordered_encode"] = {"wall_ms": (w1-w0)/1e6, "cpu_ms": (c1-c0)/1e6}
    bm.ordered_worker_pull = instrumented_pull

def create(src: Path, dest: Path) -> dict:
    global ACTIVE
    if dest.exists():
        dest.unlink()
    ACTIVE = {"phases": {}}
    before = resource.getrusage(resource.RUSAGE_SELF)
    w0, c0 = time.perf_counter_ns(), time.process_time_ns()
    try:
        bm.Builder(src).build(dest)
    finally:
        c1, w1 = time.process_time_ns(), time.perf_counter_ns()
        after = resource.getrusage(resource.RUSAGE_SELF)
        phases = ACTIVE["phases"]
        ACTIVE = None
    if set(phases) != set(STAGES):
        raise AssertionError(("phase coverage missing", sorted(set(STAGES)-set(phases)), sorted(phases)))
    total = {"wall_ms": (w1-w0)/1e6, "cpu_ms": (c1-c0)/1e6}
    residual = {k: total[k]-sum(phases[p][k] for p in STAGES) for k in total}
    if any(v < -2 for v in residual.values()):
        raise AssertionError(("non-exclusive phase accounting", total, phases, residual))
    return {"total": total, "phases": phases, "residual": residual,
            "minor_faults": after.ru_minflt-before.ru_minflt,
            "major_faults": after.ru_majflt-before.ru_majflt}

def main() -> None:
    if len(sys.argv) != 6:
        raise SystemExit("usage: CHILD ROOT CORPORA OUTPUT FRESH|BUILD REPS")
    root, corp, out = (Path(s).resolve() for s in sys.argv[1:4])
    mode = sys.argv[4]
    reps = int(sys.argv[5])
    assert mode in ("FRESH", "BUILD") and 1 <= reps <= 7
    pkg = Path(cmpct.__file__).resolve()
    assert pkg.is_relative_to(root / "src"), ("package origin", pkg)
    lib = Path(_library_path()).resolve()
    lib_sha = digest_file(lib)
    install_stage_instrument()
    out.parent.mkdir(parents=True, exist_ok=True)
    prefix = []
    if mode == "BUILD":
        for name in ("tiny", "source", "media"):
            target = out.parent / ("prefix-" + name + ".cmpct")
            step = create(corp / name, target)
            prefix.append({"name": name, "total": step["total"],
                           "sha256": digest_file(target), "bytes": target.stat().st_size})
            target.unlink()
    create(corp / "binary", out)  # Equal untimed immediate binary warmup.
    rows = []
    for i in range(reps):
        sample = create(corp / "binary", out)
        # Hash and size are audited AFTER the full timed build.
        sample.update({"rep": i, "archive_sha256": digest_file(out),
                       "archive_bytes": out.stat().st_size})
        rows.append(sample)
    assert len({r["archive_sha256"] for r in rows}) == 1
    assert len({r["archive_bytes"] for r in rows}) == 1
    print(json.dumps({"mode": mode, "package": str(pkg), "native_path": str(lib),
                      "native_sha256": lib_sha, "prefix": prefix, "samples": rows,
                      "rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
                     sort_keys=True))

if __name__ == "__main__":
    main()
