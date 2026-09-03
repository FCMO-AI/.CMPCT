from __future__ import annotations

"""Whole-process-tree RSS companion for the frozen v0.30 paired runtime authority.

The canonical runtime worker remains unchanged and still owns the frozen operation timer.  This harness only
strengthens RSS accounting now that the promoted product may spawn a bounded PrefixGraph helper: every live
worker descendant is charged through a 10 ms /proc sampler, with the worker's inherited RUSAGE_SELF high-water
retained as a floor so sampling can never make the old measurement smaller.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from benchmarks import v030_release_performance as B
from experiments import entropygraph_v030_release_product as PRODUCT
from tools import check_v030_release_lock as RELEASE_LOCK

SCHEMA = "cmpct-v030-release-performance-tree-rss-v1"
RSS_ACCOUNTING = "whole-process-tree-vmrss-10ms-with-parent-rumaxrss-floor"
SAMPLE_INTERVAL_S = 0.01
B.WORKER = B.ROOT / "benchmarks" / "v030_perf_worker_v2.py"


def _candidate_fingerprint() -> str:
    fingerprint, _ = RELEASE_LOCK.fingerprint(RELEASE_LOCK.load_manifest())
    return fingerprint


def _expected_tree(engine: str, source: Path, historical_expected: str) -> str:
    return PRODUCT.treehash(source) if engine == "v030" else historical_expected


B._expected_tree_for_engine = _expected_tree


def _pid_vmrss_kib(pid: int) -> int:
    try:
        text = Path(f"/proc/{pid}/status").read_text()
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return 0
    for line in text.splitlines():
        if line.startswith("VmRSS:"):
            try:
                return int(line.split()[1])
            except (IndexError, ValueError):
                return 0
    return 0


def _children(pid: int) -> list[int]:
    try:
        raw = Path(f"/proc/{pid}/task/{pid}/children").read_text().strip()
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return []
    out: list[int] = []
    for token in raw.split():
        try:
            out.append(int(token))
        except ValueError:
            pass
    return out


def _tree_rss_kib(root_pid: int) -> tuple[int, int]:
    total = 0
    count = 0
    queue = [root_pid]
    seen: set[int] = set()
    while queue:
        pid = queue.pop()
        if pid in seen:
            continue
        seen.add(pid)
        rss = _pid_vmrss_kib(pid)
        if rss:
            total += rss
            count += 1
        queue.extend(_children(pid))
    return total, count


_RECEIPTS: list[dict] = []


def _run_worker_tree(*args: str) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(B.ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.Popen(
        [sys.executable, str(B.WORKER), *args],
        cwd=B.ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    samples = 0
    sampled_peak = 0
    peak_processes = 0
    while proc.poll() is None:
        rss, processes = _tree_rss_kib(proc.pid)
        samples += 1
        if rss > sampled_peak:
            sampled_peak = rss
            peak_processes = processes
        time.sleep(SAMPLE_INTERVAL_S)
    # Capture one final sample before /proc necessarily disappears.
    rss, processes = _tree_rss_kib(proc.pid)
    samples += 1
    if rss > sampled_peak:
        sampled_peak = rss
        peak_processes = processes
    stdout, stderr = proc.communicate()
    if proc.returncode:
        raise RuntimeError(
            "tree-RSS performance worker failed: "
            f"args={args!r} returncode={proc.returncode} stdout={stdout!r} stderr={stderr!r}"
        )
    lines = [line for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"tree-RSS performance worker produced no JSON: stderr={stderr!r}")
    result = json.loads(lines[-1])
    parent_peak = int(result["peak_rss_kib"])
    decisive_peak = max(parent_peak, int(sampled_peak))
    receipt = {
        "engine": result.get("engine"),
        "op": result.get("op"),
        "parent_peak_rss_kib": parent_peak,
        "sampled_tree_peak_rss_kib": int(sampled_peak),
        "decisive_peak_rss_kib": decisive_peak,
        "tree_rss_samples": samples,
        "tree_peak_processes": peak_processes,
        "sample_interval_s": SAMPLE_INTERVAL_S,
    }
    _RECEIPTS.append(receipt)
    result["parent_peak_rss_kib"] = parent_peak
    result["sampled_tree_peak_rss_kib"] = int(sampled_peak)
    result["peak_rss_kib"] = decisive_peak
    result["tree_rss_samples"] = samples
    result["tree_peak_processes"] = peak_processes
    result["rss_accounting"] = RSS_ACCOUNTING
    return result


B._run_worker = _run_worker_tree


def run(work_root: Path) -> dict:
    fingerprint = _candidate_fingerprint()
    _RECEIPTS.clear()
    result = dict(B.run(work_root))
    result["schema"] = SCHEMA
    result["engine"] = "experiments/entropygraph_v030_release_product.py"
    result["release_facade"] = "cmpct-v030-release-product-v1"
    result["worker"] = "benchmarks/v030_perf_worker_v2.py"
    result["identity_binding"] = "v029-historical-content-tree + v030-canonical-user-tree"
    result["candidate_fingerprint"] = fingerprint
    result["rss_accounting"] = RSS_ACCOUNTING
    result["tree_rss_contract"] = {
        "sample_interval_s": SAMPLE_INTERVAL_S,
        "decisive_peak": "max(worker parent RUSAGE_SELF ru_maxrss, sampled live worker process-tree VmRSS)",
        "child_memory_gifted": False,
        "timing_boundary_changed": False,
        "peak_rss_threshold_changed": False,
        "release_credit": False,
    }
    result["tree_rss_receipts"] = list(_RECEIPTS)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-release-performance-tree-rss-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-release-performance-tree-rss.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_fingerprint": result["candidate_fingerprint"], "totals": result["totals"], "gate": result["gate"], "rss_accounting": result["rss_accounting"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("v0.30 whole-process-tree RSS runtime promotion gate failed")


if __name__ == "__main__":
    main()
