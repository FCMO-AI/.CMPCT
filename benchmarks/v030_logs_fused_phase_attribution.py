from __future__ import annotations

"""Frozen D2 attribution of required phases inside the promoted one-session Logs extractor."""

import argparse
import gc
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import threading
import time

from benchmarks import neutral_hostile_corpus_v1 as CORPUS
from experiments import entropygraph_v030_release_product_logs_candidate as PRODUCT
from experiments import entropygraph_v030_release_product_logs_runtime as RUNTIME
from experiments import entropygraph_v030_logs_fused_extract as FUSED

ROUNDS = 11
MAX_INSTRUMENTATION_RATIO = 1.10
MATERIAL_ABSOLUTE_S = 0.0020
MATERIAL_SHARE = 0.05
PREREG = "docs/v030-rnd/R25_LOGS_FUSED_PHASE_ATTRIBUTION_PREREG.md"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _clean(path: Path) -> None:
    if path.exists() or path.is_symlink():
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()


def _exact_extract(fn, archive: Path, dst: Path, expected_tree: str) -> float:
    _clean(dst)
    gc.collect()
    started = time.perf_counter()
    fn(archive, dst)
    elapsed = time.perf_counter() - started
    got = PRODUCT.treehash(dst)
    if got != expected_tree:
        raise RuntimeError(f"Logs phase-attribution tree mismatch: {got} != {expected_tree}")
    return elapsed


def _instrumented_extract(archive: Path, dst: Path, expected_tree: str) -> dict:
    _clean(dst)
    gc.collect()

    phase = {
        "archive_restore_session_s": 0.0,
        "manifest_decode_s": 0.0,
        "filesystem_metadata_s": 0.0,
    }
    counts = {
        "outer_restore_session_calls": 0,
        "manifest_decode_calls": 0,
        "filesystem_metadata_calls": 0,
    }
    tls = threading.local()

    original_restore = FUSED.LOGS.Archive._restore_session
    original_decode = FUSED.FS.decode_manifest
    original_metadata = FUSED._restore_filesystem_metadata

    def timed_restore(self, *args, **kwargs):
        depth = int(getattr(tls, "restore_depth", 0))
        outer = depth == 0
        if outer:
            started = time.perf_counter()
        tls.restore_depth = depth + 1
        try:
            return original_restore(self, *args, **kwargs)
        finally:
            tls.restore_depth = depth
            if outer:
                phase["archive_restore_session_s"] += time.perf_counter() - started
                counts["outer_restore_session_calls"] += 1

    def timed_decode(*args, **kwargs):
        started = time.perf_counter()
        try:
            return original_decode(*args, **kwargs)
        finally:
            phase["manifest_decode_s"] += time.perf_counter() - started
            counts["manifest_decode_calls"] += 1

    def timed_metadata(*args, **kwargs):
        started = time.perf_counter()
        try:
            return original_metadata(*args, **kwargs)
        finally:
            phase["filesystem_metadata_s"] += time.perf_counter() - started
            counts["filesystem_metadata_calls"] += 1

    FUSED.LOGS.Archive._restore_session = timed_restore
    FUSED.FS.decode_manifest = timed_decode
    FUSED._restore_filesystem_metadata = timed_metadata
    try:
        started = time.perf_counter()
        RUNTIME.extract(archive, dst)
        total = time.perf_counter() - started
    finally:
        FUSED.LOGS.Archive._restore_session = original_restore
        FUSED.FS.decode_manifest = original_decode
        FUSED._restore_filesystem_metadata = original_metadata

    got = PRODUCT.treehash(dst)
    if got != expected_tree:
        raise RuntimeError(f"instrumented Logs extraction tree mismatch: {got} != {expected_tree}")

    tracked = sum(float(x) for x in phase.values())
    remainder = max(0.0, total - tracked)
    return {
        "total_s": total,
        **phase,
        "unattributed_remainder_s": remainder,
        **counts,
    }


def _median(rows: list[dict], key: str) -> float:
    return float(statistics.median(float(row[key]) for row in rows))


def run(work_root: Path) -> dict:
    work_root = Path(work_root)
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    corpus_root = work_root / "corpus"
    CORPUS.corpus_logs(corpus_root)
    source = corpus_root / "05_logs_and_telemetry"
    if not source.is_dir():
        raise RuntimeError("frozen Logs workload was not generated")
    expected_tree = PRODUCT.treehash(source)

    archive = work_root / "logs.cmpct"
    stats = dict(PRODUCT.build(source, archive))
    verified = dict(PRODUCT.strong_verify(archive))
    if not verified.get("ok") or verified.get("tree_sha256") != expected_tree:
        raise RuntimeError(f"Logs archive failed frozen strong verification: {verified!r}")
    if stats.get("selected") != "logs-inverse" or not PRODUCT._is_logs_archive(archive):
        raise RuntimeError("frozen Logs target did not select logs-inverse")

    # Warm both exact paths before the paired measurement.
    _exact_extract(RUNTIME.extract, archive, work_root / "warm-control", expected_tree)
    _instrumented_extract(archive, work_root / "warm-instrumented", expected_tree)

    controls: list[float] = []
    instrumented: list[dict] = []
    order: list[str] = []
    all_exact = True
    for round_index in range(ROUNDS):
        pair = ("control", "instrumented") if round_index % 2 == 0 else ("instrumented", "control")
        for label in pair:
            order.append(label)
            dst = work_root / f"round-{round_index:02d}-{label}"
            if label == "control":
                controls.append(_exact_extract(RUNTIME.extract, archive, dst, expected_tree))
            else:
                instrumented.append(_instrumented_extract(archive, dst, expected_tree))
            all_exact = all_exact and PRODUCT.treehash(dst) == expected_tree

    control_median = float(statistics.median(controls))
    instrumented_median = _median(instrumented, "total_s")
    overhead_ratio = instrumented_median / control_median
    phase_keys = (
        "archive_restore_session_s",
        "manifest_decode_s",
        "filesystem_metadata_s",
    )
    medians = {key: _median(instrumented, key) for key in phase_keys}
    medians["unattributed_remainder_s"] = _median(instrumented, "unattributed_remainder_s")
    shares = {key: medians[key] / instrumented_median for key in phase_keys}
    material = {
        key: medians[key] >= MATERIAL_ABSOLUTE_S and shares[key] >= MATERIAL_SHARE
        for key in phase_keys
    }
    largest = max(phase_keys, key=lambda key: medians[key])

    count_stable = all(
        int(row["manifest_decode_calls"]) == 1
        and int(row["filesystem_metadata_calls"]) == 1
        and int(row["outer_restore_session_calls"]) >= 1
        for row in instrumented
    )
    valid = (
        all_exact
        and len(controls) == ROUNDS
        and len(instrumented) == ROUNDS
        and overhead_ratio <= MAX_INSTRUMENTATION_RATIO
        and count_stable
        and all(value >= 0.0 for value in medians.values())
    )
    if not valid:
        decision = "INVALID_CORRECTNESS_OR_INSTRUMENTATION"
    elif any(material.values()):
        decision = "TRACKED_PHASE_MATERIAL_HEADROOM"
    else:
        decision = "TRACKED_PHASES_INSUFFICIENT_FOR_LOGS_GAP"

    return {
        "schema": "cmpct-v030-logs-fused-phase-attribution-v1",
        "preregistration": PREREG,
        "target": "neutral_hostile_v1/05_logs_and_telemetry",
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha256(archive),
        "selected": stats.get("selected"),
        "source_tree_sha256": expected_tree,
        "strong_verify": verified,
        "rounds": ROUNDS,
        "order": order,
        "control_s": controls,
        "instrumented_rows": instrumented,
        "control_median_s": control_median,
        "instrumented_median_s": instrumented_median,
        "instrumentation_wall_ratio": overhead_ratio,
        "phase_medians_s": medians,
        "tracked_phase_shares": shares,
        "tracked_phase_material": material,
        "largest_tracked_phase": largest,
        "material_absolute_floor_s": MATERIAL_ABSOLUTE_S,
        "material_share_floor": MATERIAL_SHARE,
        "maximum_instrumentation_wall_ratio": MAX_INSTRUMENTATION_RATIO,
        "all_exact": all_exact,
        "call_counts_stable": count_stable,
        "experiment_valid": valid,
        "decision": decision,
        "release_credit": False,
        "production_source_changed": False,
        "release_thresholds_changed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-logs-fused-phase-attribution-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-logs-fused-phase-attribution.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: result[key] for key in (
        "control_median_s", "instrumented_median_s", "instrumentation_wall_ratio",
        "phase_medians_s", "tracked_phase_shares", "tracked_phase_material",
        "largest_tracked_phase", "experiment_valid", "decision",
    )}, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("Logs fused phase attribution invalid")


if __name__ == "__main__":
    main()
