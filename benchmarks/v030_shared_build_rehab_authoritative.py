from __future__ import annotations

"""Fresh-process shared-build rehabilitation evidence for the release-facing G04 owner.

This compares the historical duplicated G04 implementation against the already-productized
``entropygraph_v030_shared_portfolio`` on the frozen ML runtime workload. It changes no product behavior,
timing boundary, threshold, corpus semantic, or archive grammar. Exact source SHA and release fingerprint
are emitted so the result cannot be rebound to a later candidate.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import statistics
import subprocess
import sys
import time

from benchmarks import v030_release_performance as PERF
from tools import check_v030_release_lock as RELEASE_LOCK

ROOT = Path(__file__).resolve().parents[1]
ORDER = (("duplicated", "shared"), ("shared", "duplicated"))
MIN_WALL_PCT = 20.0
MIN_WALL_S = 5.0


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _usage() -> tuple[float, int]:
    self_u = resource.getrusage(resource.RUSAGE_SELF)
    child_u = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = self_u.ru_utime + self_u.ru_stime + child_u.ru_utime + child_u.ru_stime
    rss = max(int(self_u.ru_maxrss), int(child_u.ru_maxrss))
    return cpu, rss


def _worker(arm: str, source: Path, out: Path) -> dict:
    if arm == "duplicated":
        from experiments import entropygraph_v030_geometry_overlay_g04 as engine
    elif arm == "shared":
        from experiments import entropygraph_v030_shared_portfolio as engine
    else:
        raise ValueError(arm)
    before_cpu, _ = _usage()
    started = time.perf_counter()
    stats = engine.build(source, out)
    wall_s = time.perf_counter() - started
    after_cpu, rss = _usage()
    verified = engine.strong_verify(out)
    if not verified.get("ok"):
        raise RuntimeError(f"{arm} strong verification failed: {verified!r}")
    return {"arm": arm, "wall_s": wall_s, "cpu_s": after_cpu - before_cpu,
            "rss_highwater_kib_observed": rss, "archive_bytes": out.stat().st_size,
            "archive_sha256": _sha256(out), "tree_sha256": verified["tree_sha256"], "stats": stats}


def _run_fresh(arm: str, source: Path, out: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    completed = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", arm,
                                "--source", str(source), "--archive", str(out)], cwd=ROOT, env=env,
                               check=True, capture_output=True, text=True)
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"fresh worker emitted no JSON: {completed.stderr!r}")
    return json.loads(lines[-1])


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[("neutral_hostile_v1", "09_ml_artifacts")]
    pairs = []
    for rep, order in enumerate(ORDER):
        measured = {}
        for arm in order:
            out = work_root / "archives" / f"r{rep}-{arm}.cmpct"
            out.parent.mkdir(parents=True, exist_ok=True)
            measured[arm] = _run_fresh(arm, source, out)
        old, new = measured["duplicated"], measured["shared"]
        if old["archive_sha256"] != new["archive_sha256"] or old["tree_sha256"] != new["tree_sha256"]:
            raise RuntimeError("shared-build changed archive or logical-tree identity")
        if int(new["stats"].get("attempt5_graph_build_count", -1)) != 1:
            raise RuntimeError("shared-build did not prove exactly one attempt-5 graph build")
        if int(new["stats"].get("selection_extra_payload_write_bytes", -1)) != 0:
            raise RuntimeError("shared-build exported payload-copy cost")
        saving_s = old["wall_s"] - new["wall_s"]
        pairs.append({"rep": rep, "execution_order": list(order), "duplicated": old, "shared": new,
                      "wallclock_improvement_s": saving_s,
                      "wallclock_improvement_pct": saving_s / max(old["wall_s"], 1e-9) * 100.0,
                      "cpu_improvement_pct": (old["cpu_s"] - new["cpu_s"]) / max(old["cpu_s"], 1e-9) * 100.0,
                      "rss_ratio_observed": new["rss_highwater_kib_observed"] / max(old["rss_highwater_kib_observed"], 1)})
    fingerprint, _ = RELEASE_LOCK.fingerprint(RELEASE_LOCK.load_manifest())
    source_sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    wall_s = statistics.median(p["wallclock_improvement_s"] for p in pairs)
    wall_pct = statistics.median(p["wallclock_improvement_pct"] for p in pairs)
    facts = {"byte_identical": True, "wallclock_improvement_pct": wall_pct,
             "wallclock_improvement_s": wall_s, "attempt5_graph_build_count": 1}
    passed = wall_pct >= MIN_WALL_PCT and wall_s >= MIN_WALL_S
    return {"schema": "cmpct-v030-shared-build-rehab-authoritative-v1", "source_sha": source_sha,
            "candidate_fingerprint": fingerprint,
            "source_surface": "experiments/entropygraph_v030_shared_portfolio.py",
            "control_surface": "experiments/entropygraph_v030_geometry_overlay_g04.py",
            "workload": "neutral_hostile_v1/09_ml_artifacts", "release_credit": False,
            "contract": {"minimum_wallclock_improvement_pct": MIN_WALL_PCT,
                         "minimum_wallclock_improvement_s": MIN_WALL_S, "attempt5_graph_build_count": 1},
            "facts": facts, "pairs": pairs, "gate": {"passed": passed},
            "rss_note": "ru_maxrss high-water observation only; runtime-memory-selective owns normative whole-process-tree RSS"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", choices=("duplicated", "shared"))
    parser.add_argument("--source", type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-shared-build-rehab-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-shared-build-rehab.json"))
    args = parser.parse_args()
    if args.worker:
        if args.source is None or args.archive is None:
            raise SystemExit("--source and --archive required with --worker")
        print(json.dumps(_worker(args.worker, args.source, args.archive), separators=(",", ":")), flush=True)
        return
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source_sha": result["source_sha"], "candidate_fingerprint": result["candidate_fingerprint"],
                      "facts": result["facts"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("shared-build rehabilitation gate failed")


if __name__ == "__main__":
    main()
