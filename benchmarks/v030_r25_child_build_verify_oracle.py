from __future__ import annotations
"""Diagnostic A/B for moving canonical r25 build+verification behind a process lifetime.

Research-only: archive grammar, admission, thresholds and shipping code are untouched.  The
candidate arm executes the exact shipping r25 builder and strong verifier in a spawned child,
then returns only stats plus the already-materialized candidate path.  Parent and whole-process-
tree RSS are sampled so process placement cannot hide aggregate memory.
"""
import argparse
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
PAGE_KIB = os.sysconf("SC_PAGE_SIZE") // 1024


def _rss_kib(pid: int) -> int | None:
    try:
        fields = Path(f"/proc/{pid}/statm").read_text().split()
        return int(fields[1]) * PAGE_KIB
    except (FileNotFoundError, ProcessLookupError, PermissionError, ValueError, IndexError):
        return None


def _children(pid: int) -> list[int]:
    try:
        text = Path(f"/proc/{pid}/task/{pid}/children").read_text().strip()
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return []
    return [int(item) for item in text.split() if item]


def _tree_rss_kib(root_pid: int) -> tuple[int, int]:
    seen: set[int] = set()
    stack = [root_pid]
    total = 0
    count = 0
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)
        rss = _rss_kib(pid)
        if rss is None:
            continue
        total += rss
        count += 1
        stack.extend(_children(pid))
    return total, count


def _sample(stop: threading.Event, rows: list[dict], t0: float) -> None:
    pid = os.getpid()
    while not stop.is_set():
        parent = _rss_kib(pid) or 0
        tree, processes = _tree_rss_kib(pid)
        rows.append({"t_s": time.perf_counter() - t0, "parent_rss_kib": parent, "tree_rss_kib": tree, "processes": processes})
        stop.wait(0.005)


def _child_r25(staged: str, out: str, conn) -> None:
    try:
        from experiments import entropygraph_v030_release_product as RP
        started = time.perf_counter()
        stats = dict(RP.C._r25_build(Path(staged), Path(out)))
        verify_started = time.perf_counter()
        verified = dict(RP.C.strong_verify(Path(out)))
        if not verified.get("ok"):
            raise RuntimeError(f"child r25 verification failed: {verified!r}")
        conn.send({"ok": True, "stats": stats, "verified": verified, "build_s": verify_started - started, "verify_s": time.perf_counter() - verify_started})
    except BaseException as exc:
        conn.send({"ok": False, "error": repr(exc)})
    finally:
        conn.close()


def _run_arm(source: Path, out: Path, isolated: bool) -> dict:
    from experiments import entropygraph_v030_release_product as RP
    t0 = time.perf_counter()
    samples: list[dict] = []
    stop = threading.Event()
    sampler = threading.Thread(target=_sample, args=(stop, samples, t0), daemon=True)
    sampler.start()
    temp = out.parent / (out.name + ".profile")
    shutil.rmtree(temp, ignore_errors=True)
    marks = []
    try:
        marks.append({"phase": "prepare-start", "t_s": time.perf_counter() - t0})
        prepared = RP.C._prepare_profile_tree(source, temp)
        marks.append({"phase": "prepare-done", "t_s": time.perf_counter() - t0})
        if isolated:
            parent, child = mp.get_context("spawn").Pipe(duplex=False)
            proc = mp.get_context("spawn").Process(target=_child_r25, args=(str(temp), str(out), child))
            proc.start(); child.close()
            payload = parent.recv(); proc.join()
            if proc.exitcode != 0 or not payload.get("ok"):
                raise RuntimeError(f"r25 child failed exit={proc.exitcode}: {payload}")
            stats = payload["stats"]; verified = payload["verified"]
            build_s = float(payload["build_s"]); verify_s = float(payload["verify_s"])
            marks.append({"phase": "child-exited", "t_s": time.perf_counter() - t0})
        else:
            build_started = time.perf_counter()
            stats = dict(RP.C._r25_build(temp, out))
            build_s = time.perf_counter() - build_started
            marks.append({"phase": "r25-done", "t_s": time.perf_counter() - t0})
            verify_started = time.perf_counter()
            verified = dict(RP.C.strong_verify(out))
            verify_s = time.perf_counter() - verify_started
            if not verified.get("ok"):
                raise RuntimeError(f"parent r25 verification failed: {verified!r}")
            marks.append({"phase": "verify-done", "t_s": time.perf_counter() - t0})
        return {
            "arm": "spawn-child-build-plus-verify" if isolated else "in-parent-build-plus-verify",
            "wall_s": time.perf_counter() - t0,
            "build_s": build_s,
            "verify_s": verify_s,
            "archive_bytes": out.stat().st_size,
            "archive_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
            "selected": stats.get("selected"),
            "tree_sha256": verified.get("tree_sha256"),
            "prepared_entries": prepared.get("entries"),
            "peak_parent_rss_kib": max((r["parent_rss_kib"] for r in samples), default=0),
            "peak_tree_rss_kib": max((r["tree_rss_kib"] for r in samples), default=0),
            "max_processes": max((r["processes"] for r in samples), default=1),
            "marks": marks,
        }
    finally:
        stop.set(); sampler.join(timeout=2)
        shutil.rmtree(temp, ignore_errors=True)


def _child_suite(source: Path, out_root: Path) -> dict:
    out_root.mkdir(parents=True, exist_ok=True)
    control = _run_arm(source, out_root / "control.cmpct", False)
    candidate = _run_arm(source, out_root / "candidate.cmpct", True)
    exact = (
        control["archive_bytes"] == candidate["archive_bytes"]
        and control["archive_sha256"] == candidate["archive_sha256"]
        and control["tree_sha256"] == candidate["tree_sha256"]
    )
    if not exact:
        raise RuntimeError("process-isolation candidate changed exact r25 bytes/tree")
    return {"control": control, "candidate": candidate, "exact_identity": exact}


def _invoke(source: Path, out_root: Path) -> dict:
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    p = subprocess.run([sys.executable, __file__, "--child", "--source", str(source), "--out-root", str(out_root)], cwd=ROOT, env=env, check=True, capture_output=True, text=True)
    return json.loads([line for line in p.stdout.splitlines() if line.strip()][-1])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--child", action="store_true")
    ap.add_argument("--source", type=Path)
    ap.add_argument("--out-root", type=Path)
    ap.add_argument("--work-root", type=Path)
    ap.add_argument("--output", type=Path)
    a = ap.parse_args()
    if a.child:
        print(json.dumps(_child_suite(a.source, a.out_root), separators=(",", ":")))
        return
    from benchmarks import v030_release_performance as PERF
    shutil.rmtree(a.work_root, ignore_errors=True); a.work_root.mkdir(parents=True)
    corpora = PERF._build_corpora(a.work_root / "corpus")
    rows = {}
    for suite, name in (("neutral_hostile_v1", "05_logs_and_telemetry"), ("neutral_hostile_v1", "09_ml_artifacts")):
        rows[name] = _invoke(corpora[(suite, name)], a.work_root / (name + "-arms"))
    result = {
        "schema": "cmpct-v030-r25-child-build-verify-oracle-v1",
        "release_credit": False,
        "rows": rows,
        "claim_boundary": "research-only exact-r25 A/B; unchanged parent and whole-tree RSS are both charged; no release threshold or product dispatch changes",
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
