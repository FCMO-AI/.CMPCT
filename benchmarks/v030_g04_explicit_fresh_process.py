from __future__ import annotations

"""Fresh-process A/B for explicit G04 attempt-5 custody.

Research evidence only. Each measured arm runs in a new Python process so allocator/import state does not
accumulate across an in-process A/B. ``ru_maxrss`` is retained only as a per-arm high-water observation; it is
not a simultaneous process-tree RSS meter. The parent owns balanced ordering and exact identity checks. This
does not replace the full v0.30 release-performance gate.
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

ROOT = Path(__file__).resolve().parents[1]
ORDER = (("control", "explicit"), ("explicit", "control"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _usage() -> dict:
    self_usage = resource.getrusage(resource.RUSAGE_SELF)
    child_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {
        "cpu_s": self_usage.ru_utime + self_usage.ru_stime + child_usage.ru_utime + child_usage.ru_stime,
        "rss_highwater_kib_observed": max(int(self_usage.ru_maxrss), int(child_usage.ru_maxrss)),
    }


def _worker(arm: str, source: Path, out: Path) -> dict:
    from experiments import entropygraph_v030_geometry_overlay_g04 as verifier

    if arm == "control":
        build = verifier.build
    elif arm == "explicit":
        from experiments import entropygraph_v030_geometry_overlay_g04_explicit_handoff as explicit
        build = explicit.build
    else:
        raise ValueError(arm)

    before = _usage()
    started = time.perf_counter()
    stats = dict(build(source, out))
    wall = time.perf_counter() - started
    after = _usage()
    verified = dict(verifier.strong_verify(out))
    if not verified.get("ok"):
        raise RuntimeError(f"{arm} strong verification failed: {verified!r}")
    return {
        "arm": arm,
        "wall_s": wall,
        "cpu_s": after["cpu_s"] - before["cpu_s"],
        "rss_highwater_kib_observed": after["rss_highwater_kib_observed"],
        "archive_bytes": out.stat().st_size,
        "archive_sha256": _sha256(out),
        "tree_sha256": verified.get("tree_sha256"),
        "selected": stats.get("selected"),
        "stats": stats,
    }


def _run_child(arm: str, source: Path, out: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--worker-arm", arm, "--source", str(source), "--archive", str(out)],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"fresh-process worker produced no JSON: {completed.stderr!r}")
    return json.loads(lines[-1])


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    source = PERF._build_corpora(work / "corpus")[("neutral_hostile_v1", "09_ml_artifacts")]
    pairs = []
    for pair, order in enumerate(ORDER):
        arms = {}
        for slot, arm in enumerate(order):
            root = work / "runs" / f"pair-{pair}-{slot}-{arm}"
            root.mkdir(parents=True, exist_ok=True)
            arms[arm] = _run_child(arm, source, root / "out.cmpct")
        control, explicit = arms["control"], arms["explicit"]
        if control["archive_sha256"] != explicit["archive_sha256"]:
            raise RuntimeError("fresh-process final archive identity mismatch")
        if control["tree_sha256"] != explicit["tree_sha256"]:
            raise RuntimeError("fresh-process tree identity mismatch")
        retention = explicit["stats"].get("attempt5_retention", {})
        if explicit["stats"].get("global_monkeypatches") != 0:
            raise RuntimeError("fresh-process explicit arm used global monkeypatching")
        if retention.get("payload_write_bytes") != 0 or retention.get("mode") != "same-filesystem-hardlink":
            raise RuntimeError("fresh-process retention exported payload-copy cost")
        pairs.append({
            "pair": pair,
            "order": list(order),
            "control": control,
            "explicit": explicit,
            "wall_saving_fraction": 1.0 - explicit["wall_s"] / control["wall_s"],
            "cpu_saving_fraction": 1.0 - explicit["cpu_s"] / control["cpu_s"],
            "rss_highwater_ratio_observed": explicit["rss_highwater_kib_observed"] / max(1, control["rss_highwater_kib_observed"]),
        })
    return {
        "schema": "cmpct-v030-g04-explicit-fresh-process-v1",
        "release_credit": False,
        "pairs": pairs,
        "median_wall_saving_fraction": statistics.median(p["wall_saving_fraction"] for p in pairs),
        "median_cpu_saving_fraction": statistics.median(p["cpu_saving_fraction"] for p in pairs),
        "max_rss_highwater_ratio_observed": max(p["rss_highwater_ratio_observed"] for p in pairs),
        "claim_boundary": "Fresh-process ML mechanism evidence only. ru_maxrss is a per-arm high-water observation, not simultaneous process-tree RSS; full promoted-product three-target and 15-workload authorities remain required.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker-arm", choices=("control", "explicit"))
    parser.add_argument("--source", type=Path)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    if args.worker_arm:
        if args.source is None or args.archive is None:
            raise SystemExit("worker mode requires --source and --archive")
        print(json.dumps(_worker(args.worker_arm, args.source, args.archive), separators=(",", ":"), default=str))
        return
    if args.work_root is None or args.output is None:
        raise SystemExit("parent mode requires --work-root and --output")
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
