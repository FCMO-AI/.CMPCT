from __future__ import annotations

"""Research-only parent live-RSS phase attribution/A-B for frozen Shifted on the #175 product surface."""

import argparse
import hashlib
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--source-root", type=Path)
    ap.add_argument("--bounded-screen", action="store_true")
    args = ap.parse_args()

    from benchmarks import v030_release_performance as PERF
    from experiments import entropygraph_v030_release_product as RP

    C = RP.C
    shared = C.SHARED
    shutil.rmtree(args.work_root, ignore_errors=True)
    args.work_root.mkdir(parents=True)
    if args.source_root is None:
        source = PERF._build_corpora(args.work_root / "corpus")[("neutral_hostile_v1", "01_shifted_versions")]
    else:
        source = Path(args.source_root)
        if not source.is_dir():
            raise FileNotFoundError(source)
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

    canonical_originals = {name: getattr(C, name) for name in ("_r24_build", "_r25_build", "strong_verify")}
    overlay_original = shared._overlay_retained_graph
    read_records_original = shared.strict._read_source_records
    hg_audition_original = shared.G.HG.audition

    if args.bounded_screen:
        from experiments import v030_hierarchical_bounded_screen_probe as BOUNDED
        shared.G.HG.audition = BOUNDED.audition

    def wrap_canonical(name: str):
        fn = canonical_originals[name]

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

    for name in canonical_originals:
        setattr(C, name, wrap_canonical(name))

    def read_records(*pos, **kw):
        mark("g04_read_records_start")
        out = read_records_original(*pos, **kw)
        graph_records = out[3]
        graph_path = Path(pos[0])
        declared_raw = [int(record[1]) for record in graph_records]
        mark(
            "g04_read_records_end",
            graph_records=len(graph_records),
            graph_archive_bytes=graph_path.stat().st_size,
            declared_raw_record_bytes=sum(declared_raw),
            max_declared_raw_record_bytes=max(declared_raw, default=0),
            process_pool_eligible=bool(RP._g04_process_pool_eligible(graph_path, graph_records)),
            process_min_graph_bytes=int(RP.G04_PROCESS_MIN_GRAPH_BYTES),
            process_min_records=int(RP.G04_PROCESS_MIN_RECORDS),
        )
        return out

    def overlay(*pos, **kw):
        mark("g04_overlay_start")
        out = overlay_original(*pos, **kw)
        mark(
            "g04_overlay_end",
            audition_workers=int(out.get("audition_workers", 0)),
            audition_scheduler=out.get("audition_scheduler"),
            records=len(out.get("records", [])),
        )
        return out

    shared.strict._read_source_records = read_records
    shared._overlay_retained_graph = overlay

    def sample() -> None:
        last_bucket = -1
        while not stop.is_set():
            now = time.perf_counter() - t0
            value = rss_kib()
            if value > peak["rss_kib"]:
                peak.update(rss_kib=value, t=now)
            bucket = int(now * 50)
            if bucket != last_bucket:
                samples.append({"t": now, "rss_kib": value})
                last_bucket = bucket
            time.sleep(0.002)

    thread = threading.Thread(target=sample, daemon=True)
    thread.start()
    mark("build_start", bounded_screen=bool(args.bounded_screen))
    stats = None
    try:
        stats = RP.build(source, archive)
        mark("build_end", selected=stats.get("selected"), revision=stats.get("format_revision"))
    finally:
        stop.set()
        thread.join()
        for name, fn in canonical_originals.items():
            setattr(C, name, fn)
        shared._overlay_retained_graph = overlay_original
        shared.strict._read_source_records = read_records_original
        shared.G.HG.audition = hg_audition_original

    result = {
        "schema": "cmpct-v030-shifted-parent-phase-rss-v5",
        "release_credit": False,
        "arm": "bounded-screen-recompute-finalists" if args.bounded_screen else "incumbent-retain-all-screened-transforms",
        "question": "does retaining every screened Hierarchical Geometry transform own Shifted parent high-water?",
        "selected": stats.get("selected") if stats else None,
        "format_revision": stats.get("format_revision") if stats else None,
        "archive_bytes": archive.stat().st_size if archive.exists() else None,
        "archive_sha256": sha256_file(archive) if archive.exists() else None,
        "peak": peak,
        "events": events,
        "samples": samples,
        "claim_boundary": "Frozen Shifted promoted build; research A/B changes only screening-buffer lifetime; no evaluator, format, nomination or admission change.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"arm": result["arm"], "peak": peak, "events": events, "selected": result["selected"], "archive_bytes": result["archive_bytes"], "archive_sha256": result["archive_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
