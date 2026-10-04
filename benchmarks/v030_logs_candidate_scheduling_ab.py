from __future__ import annotations

"""Research-only Logs candidate-scheduling A/B/C for PR #175.

Arms freeze the pre-productization threaded control, the sequential overlap falsifier, and an r24-child ownership
control. Admission, candidate implementations, archive publication, and verification remain shipping code. No arm
earns product credit by itself.
"""

import argparse
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import threading
import time


def _rss_kib(pid: int) -> int:
    try:
        pages = int(Path(f"/proc/{pid}/statm").read_text().split()[1])
        return pages * os.sysconf("SC_PAGE_SIZE") // 1024
    except Exception:
        return 0


def _children(pid: int) -> list[int]:
    try:
        text = Path(f"/proc/{pid}/task/{pid}/children").read_text().strip()
        return [int(x) for x in text.split()] if text else []
    except Exception:
        return []


def _tree_rss_kib(pid: int) -> int:
    seen: set[int] = set(); stack = [pid]; total = 0
    while stack:
        cur = stack.pop()
        if cur in seen: continue
        seen.add(cur); total += _rss_kib(cur); stack.extend(_children(cur))
    return total


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""): h.update(chunk)
    return h.hexdigest()


def _child_r24(root: str, archive: str) -> dict:
    from experiments import entropygraph_v030_release_product_logs_candidate as L
    return L._build_r24(Path(root), Path(archive))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=("threaded", "sequential", "r24-child"), required=True)
    ap.add_argument("--source-root", type=Path, required=True)
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    from experiments import entropygraph_v030_release_product as RP
    from experiments import entropygraph_v030_release_product_logs_candidate as L

    shutil.rmtree(args.work_root, ignore_errors=True); args.work_root.mkdir(parents=True)
    out = args.work_root / "logs.cmpct"; original = L._parallel_candidates

    def threaded(root: Path, temp: Path):
        r24_path = temp / "candidate-r24.cmpct"; logs_path = temp / "candidate-logs.cmpct"; started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix="cmpct-v030-logs-selector") as pool:
            r24_future = pool.submit(L._build_r24, root, r24_path)
            logs_future = pool.submit(L._build_logs, root, logs_path)
            r24 = r24_future.result(); logs = logs_future.result()
        return r24, logs, r24_path, logs_path, time.perf_counter() - started

    def sequential(root: Path, temp: Path):
        r24_path = temp / "candidate-r24.cmpct"; logs_path = temp / "candidate-logs.cmpct"; started = time.perf_counter()
        r24 = L._build_r24(root, r24_path); logs = L._build_logs(root, logs_path)
        return r24, logs, r24_path, logs_path, time.perf_counter() - started

    def r24_child(root: Path, temp: Path):
        r24_path = temp / "candidate-r24.cmpct"; logs_path = temp / "candidate-logs.cmpct"; started = time.perf_counter()
        with ProcessPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_child_r24, os.fspath(root), os.fspath(r24_path))
            logs = L._build_logs(root, logs_path); r24 = future.result()
        return r24, logs, r24_path, logs_path, time.perf_counter() - started

    L._parallel_candidates = {"threaded": threaded, "sequential": sequential, "r24-child": r24_child}[args.arm]
    stop = threading.Event(); peak_parent = 0; peak_tree = 0; samples: list[dict] = []; pid = os.getpid(); t0 = time.perf_counter()

    def sample() -> None:
        nonlocal peak_parent, peak_tree
        while not stop.is_set():
            parent = _rss_kib(pid); tree = _tree_rss_kib(pid)
            peak_parent = max(peak_parent, parent); peak_tree = max(peak_tree, tree)
            samples.append({"t": time.perf_counter() - t0, "parent_rss_kib": parent, "tree_rss_kib": tree})
            time.sleep(0.005)

    before_self = resource.getrusage(resource.RUSAGE_SELF); before_child = resource.getrusage(resource.RUSAGE_CHILDREN)
    sampler = threading.Thread(target=sample, daemon=True); sampler.start()
    try: stats = RP.build(args.source_root, out)
    finally:
        stop.set(); sampler.join(); L._parallel_candidates = original
    wall = time.perf_counter() - t0
    after_self = resource.getrusage(resource.RUSAGE_SELF); after_child = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu_s = ((after_self.ru_utime + after_self.ru_stime) - (before_self.ru_utime + before_self.ru_stime) +
             (after_child.ru_utime + after_child.ru_stime) - (before_child.ru_utime + before_child.ru_stime))
    verified = RP.strong_verify(out)
    if not verified.get("ok"): raise RuntimeError(f"arm failed strong verification: {verified!r}")
    result = {
        "schema": "cmpct-v030-logs-candidate-scheduling-ab-v1", "product_credit": False, "arm": args.arm,
        "question": "does concurrent r24/logs candidate materialization own the residual Logs parent RSS?",
        "selected": stats.get("selected"), "format_revision": stats.get("format_revision"), "archive_bytes": out.stat().st_size,
        "archive_sha256": _sha256(out), "parent_peak_rss_kib": peak_parent, "tree_peak_rss_kib": peak_tree,
        "wall_s": wall, "cpu_s": cpu_s, "logs_candidate_pair_create_s": stats.get("logs_candidate_pair_create_s"),
        "admission": stats.get("logs_terminal_admission"), "samples": samples,
        "claim_boundary": "Frozen Logs source; only exact candidate scheduling/ownership changes. Admission, bytes, verification, thresholds and format are unchanged.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("arm", "selected", "archive_bytes", "archive_sha256", "parent_peak_rss_kib", "tree_peak_rss_kib", "wall_s", "cpu_s")}, indent=2))


if __name__ == "__main__": main()
