from __future__ import annotations

"""Research-only cProfile ownership map for shipping ML G0-G4 extraction.

The profile is diagnostic, not a performance benchmark: profiler overhead invalidates wall-time
comparison. The canonical archive is built and strongly verified before profiling; one unprofiled
warm-up extraction is performed; then exactly one shipping PRODUCT.extract() call is profiled into a
fresh destination and checked for strong tree identity. The same authenticated metadata is also used
to count direct/full-record nodes whose node digest duplicates an already-verified physical-record
digest. That census is explanatory headroom only. No product bytes, thresholds, or release law change.

The output path is also used as a durable progress checkpoint. If CI kills the diagnostic before the
final profile is available, the last completed stage remains inspectable instead of turning a timeout
into an information-free failure. Intermediate checkpoints are explicitly non-results and grant no
scientific or release credit.
"""

import argparse
import cProfile
import json
from pathlib import Path
import pstats
import shutil
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_reader as RR

TARGET = ("neutral_hostile_v1", "09_ml_artifacts")
TOP_N = 50


def _checkpoint(path: Path | None, stage: str, *, started: float, **details) -> None:
    payload = {
        "schema": "cmpct-v030-g04-ml-extract-cprofile-progress-v1",
        "status": "IN_PROGRESS",
        "stage": stage,
        "elapsed_s": float(time.perf_counter() - started),
        "target": "/".join(TARGET),
        "release_credit": False,
        "claim_boundary": "Progress checkpoint only. This is evidence-enablement for interrupted diagnostics, not a benchmark result or product claim.",
        **details,
    }
    print(json.dumps(payload, sort_keys=True), flush=True)
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _row(key, value, total_tt: float) -> dict:
    filename, line, name = key
    cc, nc, tt, ct, _callers = value
    return {
        "filename": str(filename),
        "line": int(line),
        "function": str(name),
        "primitive_calls": int(cc),
        "total_calls": int(nc),
        "self_s": float(tt),
        "cumulative_s": float(ct),
        "self_fraction": float(tt / total_tt) if total_tt > 0 else 0.0,
    }


def _redundant_direct_hash_census(archive: Path) -> dict:
    stream, meta, record_start, offsets, _merkle, _tail = RR._g04_open(archive)
    headers = []
    try:
        for rel in offsets:
            stream.seek(int(record_start) + int(rel))
            raw = stream.read(RR.PH.size)
            if len(raw) != RR.PH.size:
                raise RuntimeError("short physical header during hash census")
            _codec, usize, _csize, _crc, original_sha = RR.PH.unpack(raw)
            headers.append((int(usize), original_sha))
    finally:
        stream.close()
    full_record_direct_nodes = 0
    full_record_direct_bytes = 0
    digest_equivalent_nodes = 0
    digest_equivalent_bytes = 0
    direct_nodes = 0
    direct_bytes = 0
    for desc in meta["nodes"]:
        if desc[0] != "direct":
            continue
        direct_nodes += 1
        _, record_id, offset, length, expected = desc
        length = int(length)
        direct_bytes += length
        usize, original_sha = headers[int(record_id)]
        if int(offset) == 0 and length == usize:
            full_record_direct_nodes += 1
            full_record_direct_bytes += length
            if expected == original_sha:
                digest_equivalent_nodes += 1
                digest_equivalent_bytes += length
    return {
        "direct_nodes": direct_nodes,
        "direct_node_bytes": direct_bytes,
        "full_record_direct_nodes": full_record_direct_nodes,
        "full_record_direct_bytes": full_record_direct_bytes,
        "digest_equivalent_full_record_nodes": digest_equivalent_nodes,
        "digest_equivalent_full_record_bytes": digest_equivalent_bytes,
        "digest_equivalent_fraction_of_direct_bytes": digest_equivalent_bytes / max(direct_bytes, 1),
        "claim_boundary": "Static authenticated-metadata census only. Digest equivalence shows where a node hash may be logically redundant after record integrity succeeds; it does not prove measurable runtime savings or authorize removing an integrity check.",
    }


def run(work_root: Path, checkpoint_path: Path | None = None) -> dict:
    started = time.perf_counter()
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    _checkpoint(checkpoint_path, "work_root_ready", started=started)

    roots = PERF._build_corpora(work_root / "corpus")
    source = roots[TARGET]
    source_tree = PRODUCT.treehash(source)
    _checkpoint(checkpoint_path, "corpus_ready", started=started, source_tree_sha256=source_tree)

    archive = work_root / "ml.cmpct"
    with PRODUCT.C._revision25_profile_context():
        _checkpoint(checkpoint_path, "shipping_build_started", started=started)
        build_started = time.perf_counter()
        built = PRODUCT.build(source, archive)
        build_s = time.perf_counter() - build_started
        if archive.read_bytes()[:8] != RR.G04.MAG:
            raise RuntimeError("canonical ML target did not select G0-G4")
        _checkpoint(
            checkpoint_path,
            "shipping_build_complete",
            started=started,
            build_elapsed_s_context_only=float(build_s),
            archive_bytes=archive.stat().st_size,
        )

        verified = PRODUCT.strong_verify(archive)
        if not verified.get("ok") or verified.get("tree_sha256") != source_tree:
            raise RuntimeError("shipping strong verification failed before profile")
        _checkpoint(checkpoint_path, "strong_verify_complete", started=started)

        hash_census = _redundant_direct_hash_census(archive)
        _checkpoint(checkpoint_path, "hash_census_complete", started=started, redundant_direct_hash_census=hash_census)

        warm = work_root / "warm"
        PRODUCT.extract(archive, warm)
        if PRODUCT.treehash(warm) != source_tree:
            raise RuntimeError("warm-up extraction identity failure")
        _checkpoint(checkpoint_path, "warm_extract_complete", started=started)

        profiled = work_root / "profiled"
        profile = cProfile.Profile()
        _checkpoint(checkpoint_path, "profile_extract_started", started=started)
        wall_started = time.perf_counter()
        profile.enable()
        PRODUCT.extract(archive, profiled)
        profile.disable()
        profiled_wall_s = time.perf_counter() - wall_started
        if PRODUCT.treehash(profiled) != source_tree:
            raise RuntimeError("profiled extraction identity failure")
        _checkpoint(
            checkpoint_path,
            "profile_extract_complete",
            started=started,
            profiled_extract_wall_s_context_only=float(profiled_wall_s),
        )

    stats = pstats.Stats(profile)
    total_tt = float(stats.total_tt)
    rows = [_row(key, value, total_tt) for key, value in stats.stats.items()]
    by_self = sorted(rows, key=lambda row: row["self_s"], reverse=True)[:TOP_N]
    by_cumulative = sorted(rows, key=lambda row: row["cumulative_s"], reverse=True)[:TOP_N]
    top3_self_fraction = sum(row["self_fraction"] for row in by_self[:3])
    return {
        "schema": "cmpct-v030-g04-ml-extract-cprofile-v2",
        "target": "/".join(TARGET),
        "shipping_build": built,
        "archive_bytes": archive.stat().st_size,
        "source_tree_sha256": source_tree,
        "build_elapsed_s_context_only": float(build_s),
        "profiled_extract_wall_s_context_only": float(profiled_wall_s),
        "profile_total_self_s": total_tt,
        "top_self_function_fraction": float(by_self[0]["self_fraction"] if by_self else 0.0),
        "top3_self_fraction": float(top3_self_fraction),
        "redundant_direct_hash_census": hash_census,
        "top_by_self": by_self,
        "top_by_cumulative": by_cumulative,
        "release_credit": False,
        "claim_boundary": "cProfile diagnostic ownership only. Profiled wall time includes profiler overhead and is not release-performance evidence. Function attribution and the static hash census may route the next experiment but cannot promote a mechanism.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-extract-cprofile-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-extract-cprofile.json"))
    args = parser.parse_args()
    result = run(args.work_root, args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "schema": result["schema"],
        "archive_bytes": result["archive_bytes"],
        "build_elapsed_s_context_only": result["build_elapsed_s_context_only"],
        "profile_total_self_s": result["profile_total_self_s"],
        "top_self_function_fraction": result["top_self_function_fraction"],
        "top3_self_fraction": result["top3_self_fraction"],
        "redundant_direct_hash_census": result["redundant_direct_hash_census"],
        "top_by_self": result["top_by_self"][:15],
        "release_credit": False,
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
