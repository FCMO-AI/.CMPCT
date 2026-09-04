from __future__ import annotations

"""Frozen Forge D2 attribution inside the promoted Logs inverse-decode owner."""

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

ROUNDS = 15
MAX_OVERHEAD_RATIO = 1.10
MATERIAL_ABSOLUTE_S = 0.0020
MATERIAL_SHARE = 0.05
EXPECTED_CALLS = {"gzip": 2, "zstd": 1, "xz": 0}
PREREG = "docs/v030-rnd/R25_LOGS_INVERSE_CODEC_ATTRIBUTION_PREREG.md"


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
        raise RuntimeError("Logs inverse-codec control tree drift")
    return elapsed


def _instrumented(archive: Path, dst: Path, tree: str) -> dict:
    _clean(dst)
    gc.collect()
    codec_s = {codec: 0.0 for codec in EXPECTED_CALLS}
    codec_calls = {codec: 0 for codec in EXPECTED_CALLS}
    unknown_calls: dict[str, int] = {}

    original_decode = FUSED.LOGS.V2.BASE._decode

    def timed_decode(codec, payload):
        label = str(codec)
        started = time.perf_counter()
        try:
            return original_decode(codec, payload)
        finally:
            elapsed = time.perf_counter() - started
            if label in codec_s:
                codec_s[label] += elapsed
                codec_calls[label] += 1
            else:
                unknown_calls[label] = unknown_calls.get(label, 0) + 1

    FUSED.LOGS.V2.BASE._decode = timed_decode
    try:
        started = time.perf_counter()
        RUNTIME.extract(archive, dst)
        total = time.perf_counter() - started
    finally:
        FUSED.LOGS.V2.BASE._decode = original_decode

    if PRODUCT.treehash(dst) != tree:
        raise RuntimeError("Logs inverse-codec instrumented tree drift")
    return {
        "total_s": total,
        "codec_s": codec_s,
        "codec_calls": codec_calls,
        "unknown_calls": unknown_calls,
    }


def _median(values) -> float:
    return float(statistics.median(float(value) for value in values))


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
    warm = _instrumented(archive, work_root / "warm-instrumented", tree)
    if warm["unknown_calls"]:
        raise RuntimeError(f"unexpected inverse codec during warmup: {warm['unknown_calls']!r}")

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

    control_median = _median(controls)
    instrumented_median = _median(row["total_s"] for row in rows)
    overhead_ratio = instrumented_median / control_median
    codec_medians = {
        codec: _median(row["codec_s"][codec] for row in rows)
        for codec in EXPECTED_CALLS
    }
    codec_shares = {
        codec: codec_medians[codec] / instrumented_median
        for codec in EXPECTED_CALLS
    }
    codec_material = {
        codec: codec_medians[codec] >= MATERIAL_ABSOLUTE_S and codec_shares[codec] >= MATERIAL_SHARE
        for codec in EXPECTED_CALLS
    }
    observed_call_sets = {
        codec: sorted({int(row["codec_calls"][codec]) for row in rows})
        for codec in EXPECTED_CALLS
    }
    no_unknown = all(not row["unknown_calls"] for row in rows)
    geometry_exact = all(observed_call_sets[codec] == [expected] for codec, expected in EXPECTED_CALLS.items())
    valid = (
        len(controls) == ROUNDS
        and len(rows) == ROUNDS
        and overhead_ratio <= MAX_OVERHEAD_RATIO
        and no_unknown
        and geometry_exact
    )

    decision_parts = []
    if valid:
        for codec, label in (
            ("gzip", "GZIP_INVERSE_DECODE_HEADROOM"),
            ("zstd", "ZSTD_INVERSE_DECODE_HEADROOM"),
            ("xz", "XZ_INVERSE_DECODE_HEADROOM"),
        ):
            if codec_material[codec]:
                decision_parts.append(label)
        decision = "+".join(decision_parts) if decision_parts else "TRACKED_INVERSE_CODECS_INSUFFICIENT"
    else:
        decision = "INVALID_INVERSE_CODEC_ATTRIBUTION"

    return {
        "schema": "cmpct-v030-logs-inverse-codec-attribution-v1",
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
        "codec_medians_s": codec_medians,
        "codec_shares_of_total": codec_shares,
        "codec_material": codec_material,
        "observed_codec_call_sets": observed_call_sets,
        "expected_codec_calls": EXPECTED_CALLS,
        "unknown_codec_calls_absent": no_unknown,
        "call_geometry_exact": geometry_exact,
        "material_absolute_floor_s": MATERIAL_ABSOLUTE_S,
        "material_share_floor": MATERIAL_SHARE,
        "maximum_instrumentation_wall_ratio": MAX_OVERHEAD_RATIO,
        "experiment_valid": valid,
        "decision": decision,
        "release_credit": False,
        "production_source_changed": False,
        "decode_output_substituted_or_cached": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-logs-inverse-codec-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-logs-inverse-codec.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: result[key] for key in (
        "control_median_s", "instrumented_median_s", "instrumentation_wall_ratio",
        "codec_medians_s", "codec_shares_of_total", "codec_material",
        "observed_codec_call_sets", "experiment_valid", "decision",
    )}, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("Logs inverse-codec attribution invalid")


if __name__ == "__main__":
    main()
