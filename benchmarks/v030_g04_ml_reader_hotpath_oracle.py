from __future__ import annotations

"""Research-only function-level profiler for canonical ML G0-G4 verify/extract.

Exact final authority still shows the ML target at ~1.87x verify and ~2.29x extract versus
accepted v0.29. This diagnostic builds the ordinary canonical product once, verifies exact
tree identity, then profiles one Python semantic-owner verification and one extraction.
Profiler timing receives zero performance or release credit; the purpose is to identify the
next byte-neutral hot path with concrete cumulative CPU evidence rather than guessing.
"""

import argparse
import cProfile
import io
import json
from pathlib import Path
import pstats
import shutil
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_reader as RR

TARGET = ("neutral_hostile_v1", "09_ml_artifacts")
TOP = 30


def _profile(callable_):
    profiler = cProfile.Profile()
    started = time.perf_counter()
    profiler.enable()
    result = callable_()
    profiler.disable()
    elapsed = time.perf_counter() - started
    stats = pstats.Stats(profiler)
    rows = []
    for key, value in sorted(stats.stats.items(), key=lambda kv: kv[1][3], reverse=True)[:TOP]:
        cc, nc, tt, ct, callers = value
        filename, line, name = key
        rows.append({
            "function": name,
            "file": Path(filename).name,
            "line": int(line),
            "primitive_calls": int(cc),
            "total_calls": int(nc),
            "self_s": float(tt),
            "cumulative_s": float(ct),
        })
    return result, elapsed, rows


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpus")
    source = roots[TARGET]
    source_tree = PRODUCT.treehash(source)
    archive = work_root / "ml.cmpct"

    with PRODUCT.C._revision25_profile_context():
        built = PRODUCT.build(source, archive)
    if archive.read_bytes()[:8] != RR.G04.MAG:
        raise RuntimeError("ML hotpath target did not select canonical G0-G4")
    strong = PRODUCT.strong_verify(archive)
    if not strong.get("ok") or strong.get("tree_sha256") != source_tree:
        raise RuntimeError("canonical ML archive failed pre-profile verification")
    expected_sha = __import__("hashlib").sha256(archive.read_bytes()).hexdigest()
    expected_bytes = archive.stat().st_size

    verify, verify_elapsed, verify_top = _profile(
        lambda: RR._stream_g04(archive, None, RR.MAX_DECLARED_LOGICAL_BYTES)
    )
    if not verify.get("ok") or verify.get("tree_sha256") != source_tree:
        raise RuntimeError("profiled ML verification changed identity")

    destination = work_root / "extract"
    shutil.rmtree(destination, ignore_errors=True)
    extracted, extract_elapsed, extract_top = _profile(
        lambda: RR._stream_g04(archive, destination, RR.MAX_DECLARED_LOGICAL_BYTES)
    )
    if not extracted.get("ok") or extracted.get("tree_sha256") != source_tree:
        raise RuntimeError("profiled ML extraction changed reader identity")
    if PRODUCT.treehash(destination) != source_tree:
        raise RuntimeError("profiled ML extraction changed user tree")
    if archive.stat().st_size != expected_bytes or __import__("hashlib").sha256(archive.read_bytes()).hexdigest() != expected_sha:
        raise RuntimeError("profiling changed canonical archive bytes")

    return {
        "schema": "cmpct-v030-g04-ml-reader-hotpath-oracle-v1",
        "target": "/".join(TARGET),
        "contract": {
            "release_credit": False,
            "production_change": False,
            "archive_byte_change": False,
            "profiled_timing_receives_performance_credit": False,
            "semantic_owner": "entropygraph_v030_release_reader._stream_g04",
        },
        "archive": {
            "bytes": expected_bytes,
            "sha256": expected_sha,
            "tree_sha256": source_tree,
            "selected": built.get("selected"),
        },
        "verify": {
            "profiled_wall_s": float(verify_elapsed),
            "physical_record_reads": int(verify.get("physical_record_reads", 0)),
            "top_by_cumulative_cpu": verify_top,
        },
        "extract": {
            "profiled_wall_s": float(extract_elapsed),
            "physical_record_reads": int(extracted.get("physical_record_reads", 0)),
            "top_by_cumulative_cpu": extract_top,
        },
        "gate": {
            "experiment_valid": True,
            "archive_identity_preserved": True,
            "logical_identity_preserved": True,
            "passed": True,
        },
        "claim_boundary": "Diagnostic CPU attribution only. Profiled wall time has zero benchmark credit; any optimization requires a separate exact-byte paired A/B and full runtime authority.",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-reader-hotpath-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-reader-hotpath.json"))
    a = p.parse_args()
    result = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"archive": result["archive"], "verify": result["verify"], "extract": result["extract"], "gate": result["gate"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
