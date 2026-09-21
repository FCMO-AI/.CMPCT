from __future__ import annotations

"""Research-only parent live-RSS phase attribution for frozen Shifted on the #175 product surface.

This is observational and carries no release credit.  It intentionally reuses the frozen corpus generator and
promoted release front door, then brackets the canonical r24/r25/verification boundaries while sampling the parent
process at 2 ms.  The question is narrower than the release gate: after r24 allocation moved to a child, which
remaining parent phase owns Shifted's high-water?
"""

import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import threading
import time


def rss_kib() -> int:
    try:
        pages = int(Path("/proc/self/statm").read_text().split()[1])
        return pages * os.sysconf("SC_PAGE_SIZE") // 1024
    except Exception:
        return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    from benchmarks import v030_release_performance as PERF
    from experiments import entropygraph_v030_release_product as RP

    C = RP.C
    shutil.rmtree(args.work_root, ignore_errors=True)
    args.work_root.mkdir(parents=True)
    source = PERF._build_corpora(args.work_root / "corpus")[("neutral_hostile_v1", "01_shifted_versions")]
    archive = args.work_root / "shifted.cmpct"

    t0 = time.perf_counter()
    events: list[dict] = []
    samples: list[dict] = []
    stop = threading.Event()
    peak = {"rss_kib": 0, "t": 0.0}

    def mark(kind: str, **extra) -> None:
        events.append({
            "t": time.perf_counter() - t0,
            "rss_kib": rss_kib(),
            "ru_maxrss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
            "kind": kind,
            **extra,
        })

    originals = {name: getattr(C, name) for name in ("_r24_build", "_r25_build", "strong_verify")}

    def wrap(name: str):
        fn = originals[name]

        def inner(*pos, **kw):
            mark(name + "_start")
            out = fn(*pos, **kw)
            archive_bytes = None
            if len(pos) > 1:
                candidate = Path(pos[1])
                if candidate.exists():
                    archive_bytes = candidate.stat().st_size
            mark(name + "_end", archive_bytes=archive_bytes)
            return out

        return inner

    for name in originals:
        setattr(C, name, wrap(name))

    def sample() -> None:
        last_bucket = -1
        while not stop.is_set():
            now = time.perf_counter() - t0
            value = rss_kib()
            if value > peak["rss_kib"]:
                peak.update(rss_kib=value, t=now)
            # Persist a compact ~50 Hz trace while sampling the peak at 500 Hz.
            bucket = int(now * 50)
            if bucket != last_bucket:
                samples.append({"t": now, "rss_kib": value})
                last_bucket = bucket
            time.sleep(0.002)

    thread = threading.Thread(target=sample, daemon=True)
    thread.start()
    mark("build_start")
    stats = None
    try:
        stats = RP.build(source, archive)
        mark("build_end", selected=stats.get("selected"), revision=stats.get("format_revision"))
    finally:
        stop.set()
        thread.join()
        for name, fn in originals.items():
            setattr(C, name, fn)

    result = {
        "schema": "cmpct-v030-shifted-parent-phase-rss-v1",
        "release_credit": False,
        "question": "which parent phase owns Shifted high-water after canonical r24 child isolation?",
        "selected": stats.get("selected") if stats else None,
        "format_revision": stats.get("format_revision") if stats else None,
        "archive_bytes": archive.stat().st_size if archive.exists() else None,
        "peak": peak,
        "events": events,
        "samples": samples,
        "claim_boundary": "Frozen Shifted promoted build; observational parent-only phase attribution; no evaluator or threshold change.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"peak": peak, "events": events, "selected": result["selected"], "archive_bytes": result["archive_bytes"]}, indent=2))


if __name__ == "__main__":
    main()
