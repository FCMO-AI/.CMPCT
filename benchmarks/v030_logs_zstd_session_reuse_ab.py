from __future__ import annotations

"""Frozen R1 A/B for operation-scoped Logs ZstdDecompressor reuse."""

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

ROUNDS = 21
SUPPORT_REDUCTION = 0.04
RETIRE_REDUCTION = 0.01
PREREG = "docs/v030-rnd/R25_LOGS_ZSTD_SESSION_REUSE_AB_PREREG.md"


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


def _extract_control(archive: Path, dst: Path, tree: str) -> dict:
    _clean(dst)
    gc.collect()
    started = time.perf_counter()
    RUNTIME.extract(archive, dst)
    elapsed = time.perf_counter() - started
    if PRODUCT.treehash(dst) != tree:
        raise RuntimeError("Logs Zstd reuse control tree drift")
    return {"wall_s": elapsed}


def _extract_candidate(archive: Path, dst: Path, tree: str) -> dict:
    _clean(dst)
    gc.collect()

    archive_cls = FUSED.LOGS.Archive
    inherited = archive_cls._read_pack
    pack_module = FUSED.LOGS.V2.P
    constructions = 0
    zstd_calls = 0
    pack_calls = 0

    def reused_pack(self, index: int) -> bytes:
        nonlocal constructions, zstd_calls, pack_calls
        if index < 0 or index >= len(self.pack_offsets):
            raise RuntimeError("logs profile pack index")
        offset, codec, usize, csize, crc, sha = self.pack_offsets[index]
        self.handle.seek(offset)
        payload = self.handle.read(csize)
        if len(payload) != csize:
            raise RuntimeError("short logs profile pack")
        if codec == pack_module.CODEC_RAW:
            raw = payload
        else:
            decompressor = getattr(self, "_v030_zstd_session_decompressor", None)
            if decompressor is None:
                decompressor = pack_module.zstd.ZstdDecompressor()
                setattr(self, "_v030_zstd_session_decompressor", decompressor)
                constructions += 1
            raw = decompressor.decompress(payload, max_output_size=usize)
            zstd_calls += 1
        if (
            len(raw) != usize
            or (pack_module.binascii.crc32(raw) & 0xFFFFFFFF) != crc
            or pack_module.hashlib.sha256(raw).digest() != sha
        ):
            raise RuntimeError("logs profile pack identity")
        pack_calls += 1
        return raw

    archive_cls._read_pack = reused_pack
    try:
        started = time.perf_counter()
        RUNTIME.extract(archive, dst)
        elapsed = time.perf_counter() - started
    finally:
        archive_cls._read_pack = inherited

    if PRODUCT.treehash(dst) != tree:
        raise RuntimeError("Logs Zstd reuse candidate tree drift")
    return {
        "wall_s": elapsed,
        "decompressor_constructions": constructions,
        "zstd_pack_calls": zstd_calls,
        "pack_calls": pack_calls,
        "method_restored": archive_cls._read_pack is inherited,
    }


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
        raise RuntimeError("frozen Logs Zstd reuse archive/selection verification failed")

    _extract_control(archive, work_root / "warm-control", tree)
    warm_candidate = _extract_candidate(archive, work_root / "warm-candidate", tree)
    if warm_candidate["decompressor_constructions"] != 1 or warm_candidate["zstd_pack_calls"] != 2:
        raise RuntimeError("warm candidate did not exercise frozen decompressor lifecycle")

    control_rows: list[dict] = []
    candidate_rows: list[dict] = []
    order: list[str] = []
    for i in range(ROUNDS):
        pair = ("control", "candidate") if i % 2 == 0 else ("candidate", "control")
        for label in pair:
            order.append(label)
            dst = work_root / f"round-{i:02d}-{label}"
            if label == "control":
                control_rows.append(_extract_control(archive, dst, tree))
            else:
                candidate_rows.append(_extract_candidate(archive, dst, tree))

    control_median = float(statistics.median(float(row["wall_s"]) for row in control_rows))
    candidate_median = float(statistics.median(float(row["wall_s"]) for row in candidate_rows))
    wall_ratio = candidate_median / control_median
    reduction = 1.0 - wall_ratio
    lifecycle_ok = all(
        row["decompressor_constructions"] == 1
        and row["zstd_pack_calls"] == 2
        and row["pack_calls"] == 7
        and row["method_restored"] is True
        for row in candidate_rows
    )
    valid = len(control_rows) == ROUNDS and len(candidate_rows) == ROUNDS and lifecycle_ok
    if not valid:
        decision = "INVALID_LOGS_ZSTD_SESSION_REUSE_AB"
    elif reduction >= SUPPORT_REDUCTION and wall_ratio <= 0.96:
        decision = "LOGS_ZSTD_SESSION_REUSE_SUPPORTED"
    elif reduction < RETIRE_REDUCTION:
        decision = "LOGS_ZSTD_SESSION_REUSE_RETIRED"
    else:
        decision = "LOGS_ZSTD_SESSION_REUSE_AMBIGUOUS"

    return {
        "schema": "cmpct-v030-logs-zstd-session-reuse-ab-v1",
        "preregistration": PREREG,
        "target": "neutral_hostile_v1/05_logs_and_telemetry",
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha256(archive),
        "selected": stats.get("selected"),
        "tree_sha256": tree,
        "strong_verify": verified,
        "rounds": ROUNDS,
        "order": order,
        "control_rows": control_rows,
        "candidate_rows": candidate_rows,
        "control_median_s": control_median,
        "candidate_median_s": candidate_median,
        "candidate_wall_ratio": wall_ratio,
        "candidate_total_reduction_fraction": reduction,
        "candidate_lifecycle_ok": lifecycle_ok,
        "support_reduction_floor": SUPPORT_REDUCTION,
        "retire_reduction_ceiling": RETIRE_REDUCTION,
        "experiment_valid": valid,
        "decision": decision,
        "release_credit": False,
        "production_source_changed": False,
        "crc32_preserved": True,
        "sha256_preserved": True,
        "cold_selective_semantics_changed": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-logs-zstd-session-reuse-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-logs-zstd-session-reuse.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: result[key] for key in (
        "control_median_s", "candidate_median_s", "candidate_wall_ratio",
        "candidate_total_reduction_fraction", "candidate_lifecycle_ok", "experiment_valid", "decision",
    )}, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("Logs Zstd session reuse evidence invalid")


if __name__ == "__main__":
    main()
