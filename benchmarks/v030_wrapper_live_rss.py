from __future__ import annotations
"""Live parent-RSS attribution across the canonical r24/r25 wrapper. Diagnostic only.

Unlike ru_maxrss, /proc/self/statm reports current resident pages. Sampling the real
shipping wrapper therefore distinguishes simultaneous candidate lifetime overlap from
standalone component high-water. No product/release semantics are changed.
"""
import argparse, hashlib, json, os, shutil, subprocess, sys, threading, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE_KIB = os.sysconf("SC_PAGE_SIZE") // 1024


def live_rss_kib() -> int:
    fields = Path("/proc/self/statm").read_text().split()
    return int(fields[1]) * PAGE_KIB


def child(source: Path, out: Path) -> None:
    from experiments import entropygraph_v030_release_product as RP

    marks: list[dict] = []
    samples: list[dict] = []
    lock = threading.Lock()
    stop = threading.Event()
    t0 = time.perf_counter()

    def mark(phase: str, event: str, **extra) -> None:
        row = {"t_s": time.perf_counter() - t0, "phase": phase, "event": event, "rss_kib": live_rss_kib()}
        row.update(extra)
        with lock:
            marks.append(row)

    def sampler() -> None:
        while not stop.is_set():
            with lock:
                samples.append({"t_s": time.perf_counter() - t0, "rss_kib": live_rss_kib()})
            stop.wait(0.01)

    # Instrument the actual globals resolved by canonical build. Wrappers preserve arguments,
    # return values and exceptions; they only record current parent RSS at ownership boundaries.
    original_prepare = RP.C._prepare_profile_tree
    original_r24 = RP.C._r24_build
    original_r25 = RP.C._r25_build

    def prepare(*args, **kwargs):
        mark("profile-tree", "start")
        try:
            result = original_prepare(*args, **kwargs)
        except BaseException as exc:
            mark("profile-tree", "error", error=type(exc).__name__)
            raise
        mark("profile-tree", "done")
        return result

    def r24(*args, **kwargs):
        mark("r24-future", "start")
        try:
            result = original_r24(*args, **kwargs)
        except BaseException as exc:
            mark("r24-future", "error", error=type(exc).__name__)
            raise
        mark("r24-future", "done", selected=result.get("selected"), archive_bytes=result.get("archive_bytes"))
        return result

    def r25(*args, **kwargs):
        mark("r25", "start")
        try:
            result = original_r25(*args, **kwargs)
        except BaseException as exc:
            mark("r25", "error", error=type(exc).__name__)
            raise
        mark("r25", "done", selected=result.get("selected"), archive_bytes=result.get("archive_bytes"))
        return result

    RP.C._prepare_profile_tree = prepare
    RP.C._r24_build = r24
    RP.C._r25_build = r25
    thread = threading.Thread(target=sampler, name="cmpct-live-rss-sampler", daemon=True)
    mark("wrapper", "start")
    thread.start()
    started = time.perf_counter()
    try:
        stats = RP.build(source, out)
    finally:
        stop.set(); thread.join(timeout=2)
    wall_s = time.perf_counter() - started
    mark("wrapper", "done", selected=stats.get("selected"), format_revision=stats.get("format_revision"))
    with lock:
        peak = max((row["rss_kib"] for row in samples), default=live_rss_kib())
        copied_marks = list(marks)
        copied_samples = list(samples)
    verified = RP.strong_verify(out)
    print(json.dumps({
        "schema": "cmpct-v030-wrapper-live-rss-v1",
        "release_credit": False,
        "source": source.name,
        "wall_s": wall_s,
        "peak_live_rss_kib": peak,
        "final_live_rss_kib": live_rss_kib(),
        "archive_bytes": out.stat().st_size,
        "archive_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "selected": stats.get("selected"),
        "format_revision": stats.get("format_revision"),
        "verify_ok": bool(verified.get("ok")),
        "marks": copied_marks,
        "samples": copied_samples,
        "claim_boundary": "10ms /proc/self/statm current-parent RSS sampled across the unchanged shipping wrapper; diagnostic only, no release credit. Child-process RSS remains owned by the existing whole-tree companion."
    }, separators=(",", ":")))


def invoke(source: Path, out: Path) -> dict:
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    p = subprocess.run([sys.executable, __file__, "--child", "--source", str(source), "--archive", str(out)], cwd=ROOT, env=env, check=True, capture_output=True, text=True)
    return json.loads([line for line in p.stdout.splitlines() if line.strip()][-1])


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--child", action="store_true")
    p.add_argument("--source", type=Path)
    p.add_argument("--archive", type=Path)
    p.add_argument("--work-root", type=Path)
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    if a.child:
        child(a.source, a.archive)
        return
    from benchmarks import v030_release_performance as PERF
    shutil.rmtree(a.work_root, ignore_errors=True)
    a.work_root.mkdir(parents=True)
    corpora = PERF._build_corpora(a.work_root / "corpus")
    rows = {}
    for suite, name in (("neutral_hostile_v1", "05_logs_and_telemetry"), ("neutral_hostile_v1", "09_ml_artifacts")):
        rows[name] = invoke(corpora[(suite, name)], a.work_root / f"{name}.cmpct")
    result = {"schema": "cmpct-v030-wrapper-live-rss-suite-v1", "release_credit": False, "rows": rows}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
