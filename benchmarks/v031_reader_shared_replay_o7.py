#!/usr/bin/env python3
"""O7 source-exact ordinary Reader history-vs-candidate A/B on authenticated r24.

A negative result is still valid evidence. Timings exclude import, archive
construction, process startup and payload read; raw repetitions are retained.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path

from cmpct.builder import Builder
from cmpct.reader import CMPCT as Candidate

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v031_signed_delta_replay_o0 import PAYLOAD, make_case  # noqa: E402

BASE_HEAD = "5f6c1462e30686687ea13cc2507c9702f13df116"
BASE_READER_BLOB = "604f6a81bf03bd97a4defb4ad7a1393d01ed491f"


def baseline_reader(scratch: Path):
    data = subprocess.check_output(
        ["git", "show", f"{BASE_HEAD}:src/cmpct/reader.py"],
    )
    blob = subprocess.check_output(
        ["git", "hash-object", "--stdin"], input=data, text=False,
    ).decode().strip()
    assert blob == BASE_READER_BLOB, (blob, BASE_READER_BLOB)
    path = scratch / "reader_historical_exact.py"
    path.write_bytes(data)
    name = "cmpct._reader_o7_source_exact_historical"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module.CMPCT, blob


def sample(cls, path: Path, n: int, names: tuple[str, ...]) -> dict:
    start = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    reader = cls(path)
    wall_ns = time.perf_counter_ns() - start
    cpu_ns = time.process_time_ns() - cpu_start
    try:
        assert len(reader.files) == n
        for name in names:
            assert reader.read(name) == PAYLOAD
    finally:
        reader.close()
    return {"open_wall_ns": wall_ns, "open_cpu_ns": cpu_ns}


def med(rows: list[dict], key: str) -> float:
    return statistics.median(item[key] for item in rows) / 1e6


def compare(old_cls, paths: dict[str, Path], n: int, repeats: int):
    classes = {"historical": old_cls, "candidate": Candidate}
    names = ("g000000.bin", f"g{n // 2:06d}.bin", f"g{n - 1:06d}.bin")
    raw: dict[str, dict[str, list[dict]]] = {
        version: {"delta": [], "checkpoint": []} for version in classes
    }

    # Same archive for both actual Reader modules; alternate ABBA/BAAB order.
    for i in range(repeats):
        for kind in (("delta", "checkpoint") if i % 2 == 0 else ("checkpoint", "delta")):
            version_order = (
                ("historical", "candidate", "candidate", "historical") if i % 2 == 0
                else ("candidate", "historical", "historical", "candidate")
            )
            for version in version_order:
                raw[version][kind].append(
                    sample(classes[version], paths[kind], n, names),
                )

    summary = {
        version: {
            kind: {
                "open_wall_median_ms": med(raw[version][kind], "open_wall_ns"),
                "open_cpu_median_ms": med(raw[version][kind], "open_cpu_ns"),
                "raw_observations": raw[version][kind],
            }
            for kind in paths
        }
        for version in classes
    }
    hdelta = summary["historical"]["delta"]["open_wall_median_ms"]
    cdelta = summary["candidate"]["delta"]["open_wall_median_ms"]
    hcheckpoint = summary["historical"]["checkpoint"]["open_wall_median_ms"]
    ccheckpoint = summary["candidate"]["checkpoint"]["open_wall_median_ms"]
    return {
        "versions": summary,
        "delta_historical_over_candidate_ratio": hdelta / cdelta,
        "checkpoint_candidate_minus_historical_ms": ccheckpoint - hcheckpoint,
        "checkpoint_candidate_over_historical_ratio": ccheckpoint / hcheckpoint,
        "research_decision": (
            "PROSPECTIVE_WIN"
            if hdelta / cdelta >= 1.5 and not (
                ccheckpoint - hcheckpoint > 3.0 and
                ccheckpoint / hcheckpoint > 1.05
            ) else "NO_PRODUCT_SPEEDUP_CREDIT"
        ),
    }


def allocation_probe(cls, path: Path, n: int) -> dict:
    # Separate from latency to prevent tracemalloc overhead moving A/B timing.
    tracemalloc.start()
    before, _ = tracemalloc.get_traced_memory()
    reader = cls(path)
    during, peak = tracemalloc.get_traced_memory()
    try:
        assert len(reader.files) == n
        assert reader.read("g000000.bin") == PAYLOAD
    finally:
        reader.close()
    tracemalloc.stop()
    return {
        "python_traced_before_bytes": before,
        "python_traced_peak_bytes": peak,
        "python_traced_constructor_increment_peak_bytes": max(0, peak - before),
        "python_traced_after_constructor_bytes": during,
        "rss_limit": "NOT_MEASURED_BY_THIS_PROBE",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--sizes", type=int, nargs="+", default=[512, 2048, 4096])
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    if args.repeats < 3 or any(n < 64 or n > 8192 for n in args.sizes):
        raise SystemExit("invalid preregistered O7 sizes/repetitions")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    expected = os.environ.get("EVIDENCE_HEAD")
    if expected and head != expected:
        raise RuntimeError(f"checkout/source mismatch: {head} vs {expected}")
    args.out.mkdir(parents=True, exist_ok=True)
    report = {
        "experiment": "o7-source-exact-ordinary-reader-shared-delta-replay",
        "head": head,
        "baseline_head": BASE_HEAD,
        "credit": "focussed installed product + direct historical A/B; not release parity",
        "host": platform.platform(),
        "python": sys.version,
        "time_boundary": "Reader constructor only, excludes imports, process startup, build and payload reads",
        "cases": {},
    }
    with tempfile.TemporaryDirectory(prefix="cmpct-reader-o7-") as td:
        root = Path(td)
        old_cls, old_blob = baseline_reader(root)
        report["historical_reader_blob"] = old_blob
        candidate_blob = subprocess.check_output(
            ["git", "hash-object", "src/cmpct/reader.py"], text=True,
        ).strip()
        report["candidate_reader_blob"] = candidate_blob
        source_root = root / "input"
        source_root.mkdir()
        (source_root / "single.bin").write_bytes(PAYLOAD)
        source = root / "source.cmpct"
        Builder(source_root, workers=1, reproducible=True).build(source)
        for n in args.sizes:
            delta, checkpoint, identity = make_case(root, source, n)
            # Independent actual Reader agreement, including blobs, metadata,
            # sorted rows and all payloads sampled in the timed experiment.
            for cls in (old_cls, Candidate):
                with cls(delta) as d, cls(checkpoint) as c:
                    assert d.index == c.index
                    assert d.blobs == c.blobs and d.files == c.files
            with old_cls(delta) as historical, Candidate(delta) as new:
                assert historical.index == new.index
            paths = {"delta": delta, "checkpoint": checkpoint}
            measured = compare(old_cls, paths, n, args.repeats)
            measured["full_archive_bytes"] = {k: p.stat().st_size for k, p in paths.items()}
            measured["full_archive_sha256"] = {
                k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in paths.items()
            }
            measured["exact_final_index_equal"] = True
            measured["identity"] = identity
            if n == max(args.sizes):
                measured["python_allocation_probe"] = {
                    version: allocation_probe(cls, delta, n)
                    for version, cls in (("historical", old_cls), ("candidate", Candidate))
                }
            report["cases"][str(n)] = measured
            print("O7_SOURCE_EXACT " + json.dumps({
                "n": n,
                "historic_delta_ms": measured["versions"]["historical"]["delta"]["open_wall_median_ms"],
                "candidate_delta_ms": measured["versions"]["candidate"]["delta"]["open_wall_median_ms"],
                "speedup": measured["delta_historical_over_candidate_ratio"],
                "historical_checkpoint_ms": measured["versions"]["historical"]["checkpoint"]["open_wall_median_ms"],
                "candidate_checkpoint_ms": measured["versions"]["candidate"]["checkpoint"]["open_wall_median_ms"],
                "decision": measured["research_decision"],
            }), flush=True)
    dest = args.out / "reader-shared-replay-o7-receipt.json"
    dest.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("O7_RECEIPT_SHA256", hashlib.sha256(dest.read_bytes()).hexdigest(), flush=True)


if __name__ == "__main__":
    main()
