from __future__ import annotations

"""Frozen complete-extraction A/B for a narrow native CRC32+SHA256 Logs authentication seam."""

import argparse
import binascii
import ctypes
import gc
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import neutral_hostile_corpus_v1 as CORPUS
from experiments import entropygraph_v030_release_product_logs_candidate as PRODUCT
from experiments import entropygraph_v030_release_product_logs_runtime as RUNTIME
from experiments import entropygraph_v030_logs_fused_extract as FUSED

ROUNDS = 11
MIN_RELATIVE_IMPROVEMENT = 0.05
MIN_ABSOLUTE_SAVING_S = 0.001
PREREG = "docs/v030-rnd/R25_LOGS_FUSED_AUTH_NATIVE_SEAM_V1_PREREG.md"


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


def _load_native(path: Path):
    lib = ctypes.CDLL(str(path.resolve()))
    func = lib.cmpct_logs_auth_fused
    func.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint32),
        ctypes.POINTER(ctypes.c_ubyte),
    ]
    func.restype = ctypes.c_int
    return lib, func


def _native_auth(func, raw: bytes) -> tuple[int, bytes]:
    crc = ctypes.c_uint32()
    sha = (ctypes.c_ubyte * 32)()
    if raw:
        holder = ctypes.c_char_p(raw)
        ptr = ctypes.cast(holder, ctypes.c_void_p)
    else:
        holder = None
        ptr = ctypes.c_void_p()
    status = int(func(ptr, len(raw), ctypes.byref(crc), sha))
    if status != 0:
        raise RuntimeError(f"fused auth oracle status {status}")
    _ = holder
    return int(crc.value), bytes(sha)


def _oracle_self_check(func) -> list[dict]:
    buffers = [
        b"",
        b"cmpct",
        bytes((i * 17 + 3) & 0xFF for i in range(65535)),
        bytes((i * 19 + 7) & 0xFF for i in range(65536)),
        bytes((i * 23 + 11) & 0xFF for i in range(65537)),
        bytes((i * 29 + 13) & 0xFF for i in range(3 * 1024 * 1024 + 117)),
    ]
    rows = []
    for raw in buffers:
        got_crc, got_sha = _native_auth(func, raw)
        expected_crc = binascii.crc32(raw) & 0xFFFFFFFF
        expected_sha = hashlib.sha256(raw).digest()
        ok = got_crc == expected_crc and got_sha == expected_sha
        rows.append({"bytes": len(raw), "ok": ok})
        if not ok:
            raise RuntimeError(f"fused auth oracle identity mismatch at {len(raw)} bytes")
    return rows


def _extract(archive: Path, dst: Path, tree: str, *, arm: str, native_func) -> dict:
    _clean(dst)
    gc.collect()
    archive_cls = FUSED.LOGS.Archive
    inherited = archive_cls._read_pack
    pack_module = FUSED.LOGS.V2.P
    calls = 0
    auth_bytes = 0

    if arm == "baseline":
        def measured_pack(self, index: int) -> bytes:
            nonlocal calls, auth_bytes
            raw = inherited(self, index)
            calls += 1
            auth_bytes += len(raw)
            return raw
    elif arm == "candidate":
        def measured_pack(self, index: int) -> bytes:
            nonlocal calls, auth_bytes
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
                raw = pack_module.zstd.ZstdDecompressor().decompress(payload, max_output_size=usize)
            got_crc, got_sha = _native_auth(native_func, raw)
            if len(raw) != usize or got_crc != crc or got_sha != sha:
                raise RuntimeError("logs profile pack identity")
            calls += 1
            auth_bytes += len(raw)
            return raw
    else:
        raise ValueError(arm)

    archive_cls._read_pack = measured_pack
    try:
        started = time.perf_counter()
        RUNTIME.extract(archive, dst)
        elapsed = time.perf_counter() - started
    finally:
        archive_cls._read_pack = inherited
    if PRODUCT.treehash(dst) != tree:
        raise RuntimeError(f"Logs fused-auth {arm} tree drift")
    return {"elapsed_s": elapsed, "pack_calls": calls, "authenticated_raw_bytes": auth_bytes}


def _raw_pack_corruption(archive: Path, destination: Path) -> None:
    raw = bytearray(archive.read_bytes())
    with FUSED.LOGS.Archive(archive) as reader:
        chosen = None
        for offset, codec, _usize, csize, _crc, _sha in reader.pack_offsets:
            if codec == FUSED.LOGS.V2.P.CODEC_RAW and csize > 0:
                chosen = (int(offset), int(csize))
                break
        if chosen is None:
            raise RuntimeError("frozen Logs corpus unexpectedly has no nonempty RAW pack")
    offset, csize = chosen
    raw[offset + csize // 2] ^= 0x5A
    destination.write_bytes(raw)


def _rejects(archive: Path, dst: Path, *, arm: str, native_func) -> bool:
    try:
        _extract(archive, dst, "corruption-must-not-reconstruct", arm=arm, native_func=native_func)
    except Exception:
        return True
    return False


def run(work_root: Path, native_library: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    _lib, native_func = _load_native(native_library)
    self_check = _oracle_self_check(native_func)

    corpus = work_root / "corpus"
    CORPUS.corpus_logs(corpus)
    source = corpus / "05_logs_and_telemetry"
    tree = PRODUCT.treehash(source)
    archive = work_root / "logs.cmpct"
    stats = dict(PRODUCT.build(source, archive))
    verified = dict(PRODUCT.strong_verify(archive))
    if not verified.get("ok") or verified.get("tree_sha256") != tree or stats.get("selected") != "logs-inverse":
        raise RuntimeError("frozen Logs fused-auth archive/selection verification failed")
    archive_bytes = archive.stat().st_size
    archive_sha = _sha256(archive)

    _extract(archive, work_root / "warm-baseline", tree, arm="baseline", native_func=native_func)
    _extract(archive, work_root / "warm-candidate", tree, arm="candidate", native_func=native_func)

    rows = []
    for rep in range(1, ROUNDS + 1):
        order = ("baseline", "candidate") if rep % 2 else ("candidate", "baseline")
        measured = {}
        for arm in order:
            measured[arm] = _extract(
                archive,
                work_root / f"round-{rep:02d}-{arm}",
                tree,
                arm=arm,
                native_func=native_func,
            )
        rows.append({"rep": rep, "order": list(order), **measured})

    baseline = [float(row["baseline"]["elapsed_s"]) for row in rows]
    candidate = [float(row["candidate"]["elapsed_s"]) for row in rows]
    baseline_median = float(statistics.median(baseline))
    candidate_median = float(statistics.median(candidate))
    saving_s = baseline_median - candidate_median
    improvement = saving_s / baseline_median
    baseline_calls = {int(row["baseline"]["pack_calls"]) for row in rows}
    candidate_calls = {int(row["candidate"]["pack_calls"]) for row in rows}
    baseline_auth_bytes = {int(row["baseline"]["authenticated_raw_bytes"]) for row in rows}
    candidate_auth_bytes = {int(row["candidate"]["authenticated_raw_bytes"]) for row in rows}

    corrupted = work_root / "corrupted-raw-pack.cmpct"
    _raw_pack_corruption(archive, corrupted)
    corruption = {
        "baseline_rejected": _rejects(corrupted, work_root / "corrupt-baseline", arm="baseline", native_func=native_func),
        "candidate_rejected": _rejects(corrupted, work_root / "corrupt-candidate", arm="candidate", native_func=native_func),
    }

    valid = (
        all(row["ok"] for row in self_check)
        and len(baseline_calls) == 1
        and len(candidate_calls) == 1
        and baseline_calls == candidate_calls
        and len(baseline_auth_bytes) == 1
        and len(candidate_auth_bytes) == 1
        and baseline_auth_bytes == candidate_auth_bytes
        and corruption["baseline_rejected"]
        and corruption["candidate_rejected"]
        and archive.stat().st_size == archive_bytes
        and _sha256(archive) == archive_sha
    )
    if not valid:
        decision = "INVALID_FUSED_AUTH_NATIVE_SEAM"
    elif improvement >= MIN_RELATIVE_IMPROVEMENT and saving_s >= MIN_ABSOLUTE_SAVING_S:
        decision = "FUSED_AUTH_NATIVE_SEAM_HEADROOM_SUPPORTED"
    else:
        decision = "FUSED_AUTH_NATIVE_SEAM_HEADROOM_NOT_SUPPORTED"

    return {
        "schema": "cmpct-v030-logs-fused-auth-native-seam-v1",
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "preregistration": PREREG,
        "target": "neutral_hostile_v1/05_logs_and_telemetry",
        "selected": stats.get("selected"),
        "tree_sha256": tree,
        "archive_bytes": archive_bytes,
        "archive_sha256": archive_sha,
        "native_library": str(native_library),
        "oracle_self_check": self_check,
        "rounds": ROUNDS,
        "rows": rows,
        "baseline_median_s": baseline_median,
        "candidate_median_s": candidate_median,
        "median_saving_s": saving_s,
        "median_improvement_fraction": improvement,
        "minimum_relative_improvement": MIN_RELATIVE_IMPROVEMENT,
        "minimum_absolute_saving_s": MIN_ABSOLUTE_SAVING_S,
        "baseline_pack_calls": sorted(baseline_calls),
        "candidate_pack_calls": sorted(candidate_calls),
        "baseline_authenticated_raw_bytes": sorted(baseline_auth_bytes),
        "candidate_authenticated_raw_bytes": sorted(candidate_auth_bytes),
        "corruption": corruption,
        "experiment_valid": valid,
        "decision": decision,
        "release_credit": False,
        "production_source_changed": False,
        "crc32_disabled": False,
        "sha256_disabled": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--native-library", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root, args.native_library)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in (
        "baseline_median_s", "candidate_median_s", "median_saving_s", "median_improvement_fraction",
        "baseline_pack_calls", "candidate_pack_calls", "corruption", "experiment_valid", "decision",
    )}, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("Logs fused-auth native seam experiment invalid")


if __name__ == "__main__":
    main()
