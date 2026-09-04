from __future__ import annotations

"""Frozen D2 sub-attribution inside the promoted Logs authenticated restore boundary."""

import argparse
import gc
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import neutral_hostile_corpus_v1 as CORPUS
from experiments import entropygraph_v030_release_product_logs_candidate as PRODUCT
from experiments import entropygraph_v030_release_product_logs_runtime as RUNTIME
from experiments import entropygraph_v030_logs_fused_extract as FUSED

ROUNDS = 11
MAX_OVERHEAD_RATIO = 1.10
MATERIAL_ABSOLUTE_S = 0.0020
MATERIAL_SHARE = 0.05
PREDECESSOR_RESTORE_MEDIAN_S = 0.026265138000027832
PREREG = "docs/v030-rnd/R25_LOGS_RESTORE_INNER_ATTRIBUTION_PREREG.md"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _clean(path: Path) -> None:
    if path.exists() or path.is_symlink():
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()


def _control(archive: Path, dst: Path, tree: str) -> float:
    _clean(dst)
    gc.collect()
    started = time.perf_counter()
    RUNTIME.extract(archive, dst)
    elapsed = time.perf_counter() - started
    if PRODUCT.treehash(dst) != tree:
        raise RuntimeError("Logs inner-attribution control tree drift")
    return elapsed


def _instrumented(archive: Path, dst: Path, tree: str) -> dict:
    _clean(dst)
    gc.collect()
    pack_s = 0.0
    decode_s = 0.0
    pack_calls = 0
    decode_calls = 0

    original_pack = FUSED.LOGS.Archive._read_pack
    original_decode = FUSED.LOGS.V2.BASE._decode

    def timed_pack(self, *args, **kwargs):
        nonlocal pack_s, pack_calls
        started = time.perf_counter()
        try:
            return original_pack(self, *args, **kwargs)
        finally:
            pack_s += time.perf_counter() - started
            pack_calls += 1

    def timed_decode(*args, **kwargs):
        nonlocal decode_s, decode_calls
        started = time.perf_counter()
        try:
            return original_decode(*args, **kwargs)
        finally:
            decode_s += time.perf_counter() - started
            decode_calls += 1

    FUSED.LOGS.Archive._read_pack = timed_pack
    FUSED.LOGS.V2.BASE._decode = timed_decode
    try:
        started = time.perf_counter()
        RUNTIME.extract(archive, dst)
        total = time.perf_counter() - started
    finally:
        FUSED.LOGS.Archive._read_pack = original_pack
        FUSED.LOGS.V2.BASE._decode = original_decode

    if PRODUCT.treehash(dst) != tree:
        raise RuntimeError("Logs inner-attribution instrumented tree drift")
    return {
        "total_s": total,
        "pack_materialization_s": pack_s,
        "inverse_decode_s": decode_s,
        "pack_calls": pack_calls,
        "inverse_decode_calls": decode_calls,
    }


def _median(rows: list[dict], key: str) -> float:
    return float(statistics.median(float(row[key]) for row in rows))


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    CORPUS.corpus_logs(corpus)
    source = corpus / "05_logs_and_telemetry"
    tree = PRODUCT.treehash(source)
    archive = work_root / "logs.cmpct"
    stats = dict(PRODUCT.build(source, archive))
    verified = dict(PRODUCT.strong_verify(archive))
    if not verified.get("ok") or verified.get("tree_sha256") != tree or stats.get("selected") != "logs-inverse":
        raise RuntimeError("frozen Logs archive/selection verification failed")

    _control(archive, work_root / "warm-control", tree)
    _instrumented(archive, work_root / "warm-instrumented", tree)

    controls: list[float] = []
    rows: list[dict] = []
    order: list[str] = []
    for i in range(ROUNDS):
        pair = ("control", "instrumented") if i % 2 == 0 else ("instrumented", "control")
        for label in pair:
            order.append(label)
            dst = work_root / f"round-{i:02d}-{label}"
            if label == "control":
                controls.append(_control(archive, dst, tree))
            else:
                rows.append(_instrumented(archive, dst, tree))

    control_median = float(statistics.median(controls))
    instrumented_median = _median(rows, "total_s")
    overhead_ratio = instrumented_median / control_median
    medians = {
        "pack_materialization_s": _median(rows, "pack_materialization_s"),
        "inverse_decode_s": _median(rows, "inverse_decode_s"),
    }
    shares = {key: value / instrumented_median for key, value in medians.items()}
    material = {
        key: medians[key] >= MATERIAL_ABSOLUTE_S and shares[key] >= MATERIAL_SHARE
        for key in medians
    }
    stable_calls = len({int(row["pack_calls"]) for row in rows}) == 1 and len({int(row["inverse_decode_calls"]) for row in rows}) == 1
    valid = len(controls) == ROUNDS and len(rows) == ROUNDS and overhead_ratio <= MAX_OVERHEAD_RATIO and stable_calls
    decisions: list[str] = []
    if not valid:
        decision = "INVALID_RESTORE_INNER_ATTRIBUTION"
    else:
        if material["pack_materialization_s"]:
            decisions.append("PACK_MATERIALIZATION_HEADROOM")
        if material["inverse_decode_s"]:
            decisions.append("INVERSE_DECODE_HEADROOM")
        decision = "+".join(decisions) if decisions else "TRACKED_RESTORE_SUBBOUNDARIES_INSUFFICIENT"
    tracked = sum(medians.values())
    predecessor_remainder = max(0.0, PREDECESSOR_RESTORE_MEDIAN_S - tracked)
    return {
        "schema": "cmpct-v030-logs-restore-inner-attribution-v1",
        "preregistration": PREREG,
        "target": "neutral_hostile_v1/05_logs_and_telemetry",
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha256(archive),
        "selected": stats.get("selected"),
        "tree_sha256": tree,
        "strong_verify": verified,
        "rounds": ROUNDS,
        "order": order,
        "control_s": controls,
        "instrumented_rows": rows,
        "control_median_s": control_median,
        "instrumented_median_s": instrumented_median,
        "instrumentation_wall_ratio": overhead_ratio,
        "subphase_medians_s": medians,
        "subphase_shares_of_total": shares,
        "subphase_material": material,
        "pack_calls_median": _median(rows, "pack_calls"),
        "inverse_decode_calls_median": _median(rows, "inverse_decode_calls"),
        "call_counts_stable": stable_calls,
        "predecessor_restore_median_s": PREDECESSOR_RESTORE_MEDIAN_S,
        "predecessor_scale_unattributed_restore_remainder_s": predecessor_remainder,
        "material_absolute_floor_s": MATERIAL_ABSOLUTE_S,
        "material_share_floor": MATERIAL_SHARE,
        "maximum_instrumentation_wall_ratio": MAX_OVERHEAD_RATIO,
        "experiment_valid": valid,
        "decision": decision,
        "release_credit": False,
        "production_source_changed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-logs-restore-inner-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-logs-restore-inner.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in (
        "control_median_s", "instrumented_median_s", "instrumentation_wall_ratio",
        "subphase_medians_s", "subphase_shares_of_total", "subphase_material",
        "predecessor_scale_unattributed_restore_remainder_s", "experiment_valid", "decision",
    )}, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("Logs restore inner attribution invalid")


if __name__ == "__main__":
    main()
