from __future__ import annotations

"""Measure CPU consumed by frozen-v0.30 descendants that Genesis RUSAGE_SELF/process_time omits.

The source-sealed Genesis worker times creation with ``time.process_time()``, which charges only
the parent process.  Frozen v0.30 can use bounded child processes for expensive r25 auditions.
This companion records self and reaped-child user+system CPU around the same frozen product build,
alongside elapsed wall.  It is attribution only and grants no release or benchmark credit.
"""

import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import time

from benchmarks import v030_genesis_rss_attribution as RSS

FROZEN_SHA = RSS.FROZEN_SHA


def _cpu() -> dict:
    me = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {
        "self_cpu_s": float(me.ru_utime + me.ru_stime),
        "children_cpu_s": float(children.ru_utime + children.ru_stime),
    }


def _delta(after: dict, before: dict) -> dict:
    self_cpu = after["self_cpu_s"] - before["self_cpu_s"]
    child_cpu = after["children_cpu_s"] - before["children_cpu_s"]
    return {
        "self_cpu_s": self_cpu,
        "children_cpu_s": child_cpu,
        "total_process_tree_cpu_s": self_cpu + child_cpu,
    }


def _child(checkout: Path, source: Path, archive: Path, output: Path) -> None:
    product, loaded = RSS._load_frozen_surface(checkout)
    before = _cpu(); wall0 = time.perf_counter()
    stats = product.build(source, archive)
    wall = time.perf_counter() - wall0; after = _cpu()
    if not archive.is_file():
        raise RuntimeError("frozen v0.30 build produced no archive")
    verified = product.strong_verify(archive)
    if isinstance(verified, dict) and verified.get("ok") is False:
        raise RuntimeError("frozen v0.30 strong verify failed")
    output.write_text(json.dumps({
        "source_sha": FROZEN_SHA,
        "stored_bytes": archive.stat().st_size,
        "wall_s": wall,
        "cpu": _delta(after, before),
        "peak_rss_bytes": RSS._max_rss_bytes(),
        "loaded_cmpct_modules": loaded,
        "product_stats": stats,
    }, sort_keys=True, default=str) + "\n")


def run(repo: Path, checkout: Path, work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)
    sources = RSS._generate(repo, work / "corpus")
    rows = []
    script = Path(__file__).resolve()
    for name, source in sources.items():
        rowdir = work / name; rowdir.mkdir()
        result = rowdir / "result.json"; archive = rowdir / "candidate.cmpct"
        subprocess.run([
            sys.executable, str(script), "--child", "--checkout", str(checkout),
            "--source", str(source), "--archive", str(archive), "--output", str(result),
        ], check=True, env=os.environ.copy())
        row = json.loads(result.read_text()); row["workload"] = name; rows.append(row)
    return {
        "schema": "cmpct-v030-genesis-child-cpu-attribution-v1",
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "frozen_v030_sha": FROZEN_SHA,
        "rows": rows,
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "frozen_source_sealed": True,
            "self_and_reaped_child_cpu_charged": True,
            "timing_boundary_changed": False,
            "product_format_selector_unchanged": True,
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", type=Path, default=Path.cwd())
    p.add_argument("--checkout", type=Path, required=True)
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-child-cpu-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-child-cpu.json"))
    p.add_argument("--child", action="store_true")
    p.add_argument("--source", type=Path); p.add_argument("--archive", type=Path)
    a = p.parse_args()
    if a.child:
        _child(a.checkout.resolve(), a.source.resolve(), a.archive.resolve(), a.output.resolve()); return
    d = run(a.repo.resolve(), a.checkout.resolve(), a.work_root.resolve())
    a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(d, indent=2, default=str) + "\n")
    print(json.dumps({r["workload"]: {"stored_bytes": r["stored_bytes"], "wall_s": r["wall_s"], **r["cpu"]} for r in d["rows"]}, indent=2))


if __name__ == "__main__":
    main()
