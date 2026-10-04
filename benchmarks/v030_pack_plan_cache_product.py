from __future__ import annotations

"""Fresh-process product A/B for bounded exact pack-plan compressed-length reuse."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import tempfile
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v028 as V028
from experiments import entropygraph_v029_residual_fast as A5
from experiments import entropygraph_v030_pack_plan_cache as CACHE


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _child(kind: str, candidate: bool, source: Path, out: Path) -> dict:
    if kind == "v028":
        owner = V028
        build = V028.build
        restore = None
    elif kind == "attempt5":
        position_owner = A5.BASE.P
        old_position = position_owner._position_independent_candidates
        position_owner._position_independent_candidates = lambda _s, _n: []
        owner = position_owner.PARENT.V028
        build = A5.build_graph
        restore = lambda: setattr(position_owner, "_position_independent_candidates", old_position)
    else:
        raise ValueError(kind)

    old_choose = owner._choose_pack_plan
    if candidate:
        def cached_choose(nodes, sketches, roots):
            chosen, trials, _stats = CACHE.choose_pack_plan_cached(
                nodes, sketches, roots, compress_record=owner._compress_record
            )
            return chosen, trials
        owner._choose_pack_plan = cached_choose
    started_cpu = time.process_time()
    started = time.perf_counter()
    try:
        stats = build(source, out)
    finally:
        owner._choose_pack_plan = old_choose
        if restore is not None:
            restore()
    wall = time.perf_counter() - started
    cpu = time.process_time() - started_cpu
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {"kind": kind, "candidate": candidate, "wall_s": wall, "cpu_s": cpu,
            "maxrss_kib": rss, "archive_bytes": out.stat().st_size, "archive_sha256": _sha(out),
            "selected": stats.get("selected") if isinstance(stats, dict) else None}


def _invoke(kind: str, candidate: bool, source: Path, out: Path) -> dict:
    cmd = [sys.executable, str(Path(__file__).resolve()), "--child", kind,
           "--source", str(source), "--archive", str(out)]
    if candidate:
        cmd.append("--candidate")
    proc = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])})
    return json.loads(proc.stdout.strip().splitlines()[-1])


def run(work: Path, pairs: int = 3) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    source = PERF._build_corpora(work / "corpus")[("neutral_hostile_v1", "09_ml_artifacts")]
    tree = V028.treehash(source)
    result = {"schema": "cmpct-v030-pack-plan-cache-product-v1", "release_credit": False,
              "source_tree_sha256": tree, "pairs": pairs, "children": {}}
    for kind in ("v028", "attempt5"):
        rows = []
        # Alternate arm order to reduce monotonic host drift; every arm is a fresh Python process.
        for pair in range(pairs):
            order = (False, True) if pair % 2 == 0 else (True, False)
            pair_rows = []
            for candidate in order:
                out = work / f"{kind}-{pair}-{'candidate' if candidate else 'control'}.cmpct"
                pair_rows.append(_invoke(kind, candidate, source, out))
            control = next(r for r in pair_rows if not r["candidate"])
            candidate_row = next(r for r in pair_rows if r["candidate"])
            if control["archive_sha256"] != candidate_row["archive_sha256"]:
                raise RuntimeError(f"{kind} candidate changed archive bytes")
            rows.append({"control": control, "candidate": candidate_row,
                         "wall_improvement_pct": (control["wall_s"]-candidate_row["wall_s"])/control["wall_s"]*100.0,
                         "cpu_improvement_pct": (control["cpu_s"]-candidate_row["cpu_s"])/control["cpu_s"]*100.0})
        walls = sorted(r["wall_improvement_pct"] for r in rows)
        cpus = sorted(r["cpu_improvement_pct"] for r in rows)
        result["children"][kind] = {"rows": rows, "median_wall_improvement_pct": walls[len(walls)//2],
                                     "median_cpu_improvement_pct": cpus[len(cpus)//2],
                                     "max_candidate_rss_kib": max(r["candidate"]["maxrss_kib"] for r in rows),
                                     "max_control_rss_kib": max(r["control"]["maxrss_kib"] for r in rows)}
    result["claim_boundary"] = "Fresh-process child A/B only. Exact archive identity is mandatory. Whole-product parallel-tournament transfer and authoritative runtime remain unpaid."
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--pairs", type=int, default=3)
    p.add_argument("--child", choices=("v028", "attempt5"))
    p.add_argument("--candidate", action="store_true")
    p.add_argument("--source", type=Path)
    p.add_argument("--archive", type=Path)
    a = p.parse_args()
    if a.child:
        print(json.dumps(_child(a.child, a.candidate, a.source, a.archive), separators=(",", ":")))
        return
    if a.work_root is None or a.output is None:
        p.error("--work-root and --output are required in driver mode")
    d = run(a.work_root, a.pairs)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(d, indent=2))


if __name__ == "__main__":
    main()
