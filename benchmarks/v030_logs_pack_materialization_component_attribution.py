from __future__ import annotations

"""Frozen D2 attribution inside the promoted Logs authenticated pack-materialization boundary."""

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
PREREG = "docs/v030-rnd/R25_LOGS_PACK_MATERIALIZATION_COMPONENT_ATTRIBUTION_PREREG.md"


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
        raise RuntimeError("Logs pack-component control tree drift")
    return elapsed


def _instrumented(archive: Path, dst: Path, tree: str) -> dict:
    _clean(dst)
    gc.collect()

    totals = {
        "pack_total_s": 0.0,
        "io_seek_read_s": 0.0,
        "zstd_materialization_s": 0.0,
        "crc32_s": 0.0,
        "sha256_s": 0.0,
    }
    pack_calls = 0
    raw_pack_calls = 0
    zstd_pack_calls = 0

    archive_cls = FUSED.LOGS.Archive
    inherited = archive_cls._read_pack
    pack_module = FUSED.LOGS.V2.P

    def timed_pack(self, index: int) -> bytes:
        nonlocal pack_calls, raw_pack_calls, zstd_pack_calls
        pack_started = time.perf_counter()
        if index < 0 or index >= len(self.pack_offsets):
            raise RuntimeError("logs profile pack index")
        offset, codec, usize, csize, crc, sha = self.pack_offsets[index]

        started = time.perf_counter()
        self.handle.seek(offset)
        payload = self.handle.read(csize)
        totals["io_seek_read_s"] += time.perf_counter() - started
        if len(payload) != csize:
            raise RuntimeError("short logs profile pack")

        if codec == pack_module.CODEC_RAW:
            raw = payload
            raw_pack_calls += 1
        else:
            started = time.perf_counter()
            raw = pack_module.zstd.ZstdDecompressor().decompress(payload, max_output_size=usize)
            totals["zstd_materialization_s"] += time.perf_counter() - started
            zstd_pack_calls += 1

        started = time.perf_counter()
        actual_crc = pack_module.binascii.crc32(raw) & 0xFFFFFFFF
        totals["crc32_s"] += time.perf_counter() - started

        started = time.perf_counter()
        actual_sha = pack_module.hashlib.sha256(raw).digest()
        totals["sha256_s"] += time.perf_counter() - started

        if len(raw) != usize or actual_crc != crc or actual_sha != sha:
            raise RuntimeError("logs profile pack identity")
        pack_calls += 1
        totals["pack_total_s"] += time.perf_counter() - pack_started
        return raw

    archive_cls._read_pack = timed_pack
    try:
        started = time.perf_counter()
        RUNTIME.extract(archive, dst)
        total_s = time.perf_counter() - started
    finally:
        archive_cls._read_pack = inherited

    if PRODUCT.treehash(dst) != tree:
        raise RuntimeError("Logs pack-component instrumented tree drift")

    tracked = sum(totals[key] for key in ("io_seek_read_s", "zstd_materialization_s", "crc32_s", "sha256_s"))
    remainder = max(0.0, totals["pack_total_s"] - tracked)
    return {
        "total_s": total_s,
        **totals,
        "pack_remainder_s": remainder,
        "pack_calls": pack_calls,
        "raw_pack_calls": raw_pack_calls,
        "zstd_pack_calls": zstd_pack_calls,
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
        raise RuntimeError("frozen Logs pack-component archive/selection verification failed")

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
    component_keys = ("io_seek_read_s", "zstd_materialization_s", "crc32_s", "sha256_s")
    medians = {key: _median(rows, key) for key in component_keys}
    shares = {key: value / instrumented_median for key, value in medians.items()}
    material = {
        key: medians[key] >= MATERIAL_ABSOLUTE_S and shares[key] >= MATERIAL_SHARE
        for key in component_keys
    }
    call_vectors = {
        (int(row["pack_calls"]), int(row["raw_pack_calls"]), int(row["zstd_pack_calls"]))
        for row in rows
    }
    stable_calls = len(call_vectors) == 1
    valid = len(controls) == ROUNDS and len(rows) == ROUNDS and overhead_ratio <= MAX_OVERHEAD_RATIO and stable_calls

    labels = {
        "io_seek_read_s": "PACK_IO_HEADROOM",
        "zstd_materialization_s": "PACK_ZSTD_HEADROOM",
        "crc32_s": "PACK_CRC32_HEADROOM",
        "sha256_s": "PACK_SHA256_HEADROOM",
    }
    if not valid:
        decision = "INVALID_PACK_COMPONENT_ATTRIBUTION"
    else:
        winners = [key for key in component_keys if material[key]]
        winners.sort(key=lambda key: (-medians[key], component_keys.index(key)))
        decision = "+".join(labels[key] for key in winners) if winners else "TRACKED_PACK_COMPONENTS_INSUFFICIENT"

    return {
        "schema": "cmpct-v030-logs-pack-materialization-component-attribution-v1",
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
        "pack_total_median_s": _median(rows, "pack_total_s"),
        "pack_component_medians_s": medians,
        "pack_component_shares_of_total": shares,
        "pack_component_material": material,
        "pack_remainder_median_s": _median(rows, "pack_remainder_s"),
        "pack_calls_median": _median(rows, "pack_calls"),
        "raw_pack_calls_median": _median(rows, "raw_pack_calls"),
        "zstd_pack_calls_median": _median(rows, "zstd_pack_calls"),
        "call_counts_stable": stable_calls,
        "material_absolute_floor_s": MATERIAL_ABSOLUTE_S,
        "material_share_floor": MATERIAL_SHARE,
        "maximum_instrumentation_wall_ratio": MAX_OVERHEAD_RATIO,
        "experiment_valid": valid,
        "decision": decision,
        "release_credit": False,
        "production_source_changed": False,
        "authentication_work_disabled": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-logs-pack-components-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-logs-pack-components.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in (
        "control_median_s", "instrumented_median_s", "instrumentation_wall_ratio", "pack_total_median_s",
        "pack_component_medians_s", "pack_component_shares_of_total", "pack_component_material",
        "pack_remainder_median_s", "pack_calls_median", "raw_pack_calls_median", "zstd_pack_calls_median",
        "experiment_valid", "decision",
    )}, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("Logs pack-materialization component attribution invalid")


if __name__ == "__main__":
    main()
