from __future__ import annotations

"""Superseding whole-process-tree RSS companion for the frozen v0.30 runtime authority.

v1 sampled the measured worker from a thread inside that same process. Its first
result-bearing execution proved whole-tree RSS headroom but also perturbed
CPU-heavy pack timings enough to trip timing gates owned by the independent
promoted-runtime authority. v2 preserves the exact target/corpus/order/product
semantics while moving only the transitive RSS sampler into this harness
process. The canonical worker therefore retains its original operation/timing
boundary and GIL.

This instrument grants no timing or release credit. Its decision surface is
only correctness/identity custody plus the existing <=1.25x whole-tree RSS
ceiling. Timing is still recorded descriptively and remains governed by the
separate promoted-product runtime job.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import threading

from benchmarks import v030_release_performance as B
from benchmarks import v030_release_performance_product as P

SCHEMA = "cmpct-v030-release-performance-tree-rss-v2"
RSS_ACCOUNTING = "external-parent-whole-process-tree-vmrss-10ms-with-worker-rumaxrss-floor"
SAMPLE_INTERVAL_S = 0.01
MAX_PEAK_RSS_RATIO = B.MAX_PEAK_RSS_RATIO


def _pid_vmrss_kib(pid: int) -> int:
    try:
        text = Path(f"/proc/{pid}/status").read_text(encoding="utf-8")
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
        raw = Path(f"/proc/{pid}/task/{pid}/children").read_text(encoding="utf-8").strip()
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


class _ExternalTreeSampler:
    def __init__(self, root_pid: int) -> None:
        self.root_pid = root_pid
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.samples = 0
        self.peak_kib = 0
        self.peak_processes = 0
        self.errors: list[str] = []

    def _sample(self) -> None:
        try:
            rss, processes = _tree_rss_kib(self.root_pid)
            self.samples += 1
            if rss > self.peak_kib:
                self.peak_kib = rss
                self.peak_processes = processes
        except Exception as exc:
            self.errors.append(f"{type(exc).__name__}:{exc}")

    def start(self) -> None:
        def run() -> None:
            while not self.stop_event.is_set():
                self._sample()
                self.stop_event.wait(SAMPLE_INTERVAL_S)
            self._sample()

        self.thread = threading.Thread(
            target=run,
            name="cmpct-release-external-tree-rss-sampler",
            daemon=True,
        )
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=5.0)


_RECEIPTS: list[dict] = []


def _run_worker_external(*args: str) -> dict:
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
    sampler = _ExternalTreeSampler(proc.pid)
    sampler.start()
    try:
        stdout, stderr = proc.communicate()
    finally:
        sampler.stop()

    if proc.returncode != 0:
        raise RuntimeError(
            "performance worker failed: "
            f"args={args!r} returncode={proc.returncode} stdout={stdout!r} stderr={stderr!r}"
        )
    lines = [line for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"performance worker produced no JSON: stderr={stderr!r}")
    try:
        result = json.loads(lines[-1])
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"performance worker final line was not JSON: {lines[-1]!r}; stderr={stderr!r}"
        ) from exc

    worker_peak = int(result["peak_rss_kib"])
    sampled_peak = int(sampler.peak_kib)
    decisive_peak = max(worker_peak, sampled_peak)
    if sampler.samples < 1:
        raise RuntimeError("external whole-tree sampler produced no RSS samples")
    if sampler.errors:
        raise RuntimeError(f"external whole-tree sampler error: {sampler.errors!r}")

    result["worker_peak_rss_kib"] = worker_peak
    result["sampled_tree_peak_rss_kib"] = sampled_peak
    result["peak_rss_kib"] = decisive_peak
    result["tree_rss_samples"] = sampler.samples
    result["tree_peak_processes"] = sampler.peak_processes
    result["tree_sampler_errors"] = list(sampler.errors)
    result["sample_interval_s"] = SAMPLE_INTERVAL_S
    result["rss_accounting"] = RSS_ACCOUNTING
    _RECEIPTS.append(
        {
            "engine": result.get("engine"),
            "op": result.get("op"),
            "worker_peak_rss_kib": worker_peak,
            "sampled_tree_peak_rss_kib": sampled_peak,
            "decisive_peak_rss_kib": decisive_peak,
            "tree_rss_samples": sampler.samples,
            "tree_peak_processes": sampler.peak_processes,
            "tree_sampler_errors": list(sampler.errors),
            "sample_interval_s": SAMPLE_INTERVAL_S,
        }
    )
    return result


B._run_worker = _run_worker_external


def run(work_root: Path) -> dict:
    _RECEIPTS.clear()
    result = dict(P.run(work_root))
    result["schema"] = SCHEMA
    result["worker"] = "benchmarks/v030_perf_worker_canonical.py"
    result["rss_accounting"] = RSS_ACCOUNTING
    result["tree_rss_contract"] = {
        "sample_interval_s": SAMPLE_INTERVAL_S,
        "sampler_process": "harness parent; measured worker retains canonical worker code and GIL",
        "operation_window": "worker lifetime enclosing canonical pack/verify/extract operation",
        "decisive_peak": "max(worker RUSAGE_SELF ru_maxrss, sampled live worker process-tree VmRSS)",
        "child_memory_gifted": False,
        "timing_decision_credit": False,
        "release_credit": False,
        "peak_rss_threshold_changed": False,
        "supersedes": "cmpct-v030-release-performance-tree-rss-v1",
    }
    result["tree_rss_receipts"] = list(_RECEIPTS)

    expected_receipts = len(B.TARGETS) * len(B.REPETITION_ORDER) * 2 * 3
    memory_gate = {
        "exact_target_count": bool(result["gate"]["exact_target_count"]),
        "stable_historical_baseline_identity": bool(result["gate"]["stable_historical_baseline_identity"]),
        "stable_product_identity": bool(result["gate"]["stable_product_identity"]),
        "peak_rss_ratio": float(result["totals"]["max_peak_rss_ratio"]) <= MAX_PEAK_RSS_RATIO,
        "all_tree_receipts_present": len(_RECEIPTS) == expected_receipts,
        "sampler_error_free": all(receipt["tree_sampler_errors"] == [] for receipt in _RECEIPTS),
    }
    memory_gate["passed"] = all(memory_gate.values())
    custody_ok = all(
        memory_gate[key]
        for key in (
            "exact_target_count",
            "stable_historical_baseline_identity",
            "stable_product_identity",
            "all_tree_receipts_present",
            "sampler_error_free",
        )
    )
    if not custody_ok:
        terminal_decision = "INVALID_TREE_RSS_V2_RECEIPT"
    elif memory_gate["peak_rss_ratio"]:
        terminal_decision = "WHOLE_TREE_RSS_PRODUCT_MATRIX_SUPPORTED"
    else:
        terminal_decision = "WHOLE_TREE_RSS_PRODUCT_DEBT_REMAINS"
    result["memory_gate"] = memory_gate
    result["terminal_decision"] = terminal_decision
    result["descriptive_timing"] = {
        "median_create_ratio": float(result["totals"]["median_create_ratio"]),
        "max_workload_create_ratio": float(result["totals"]["max_workload_create_ratio"]),
        "median_extract_ratio": float(result["totals"]["median_extract_ratio"]),
        "max_workload_extract_ratio": float(result["totals"]["max_workload_extract_ratio"]),
        "decision_credit": False,
        "authority": "independent promoted-product runtime job",
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-tree-rss-external-v2-work"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-tree-rss-external-v2.json"),
    )
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "candidate_fingerprint": result["candidate_fingerprint"],
                "totals": result["totals"],
                "memory_gate": result["memory_gate"],
                "terminal_decision": result["terminal_decision"],
                "rss_accounting": result["rss_accounting"],
            },
            indent=2,
        ),
        flush=True,
    )
    if not result["memory_gate"]["passed"]:
        raise SystemExit("v0.30 external whole-process-tree RSS memory gate failed")


if __name__ == "__main__":
    main()
