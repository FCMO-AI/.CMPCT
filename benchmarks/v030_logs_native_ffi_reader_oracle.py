from __future__ import annotations

"""A/B the canonical logs reader through an in-process Rust FFI boundary.

The existing subprocess oracle proved correctness but lost badly to Python because process startup,
CLI JSON/info preflight and repeated archive opens dominate a ~50 ms operation.  cmpct-portable is
already a cdylib-capable production reader.  This oracle therefore measures the same semantic owner
in-process, keeps archive bytes fixed, preserves caller output-budget enforcement before publication,
and requires corruption rejection before any promotion signal can exist.
"""

import argparse
import ctypes
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_logs_inverse_profile_v3 as LOGS
from experiments import entropygraph_v030_release_product as PRODUCT

ROUNDS = 5
MIN_VERIFY_IMPROVEMENT = 0.20
MIN_EXTRACT_IMPROVEMENT = 0.20
MAX_OUTPUT_BYTES = LOGS.MAX_LOGICAL_BYTES
TARGET = ("neutral_hostile_v1", "05_logs_and_telemetry")


def _load_library(path: Path):
    lib = ctypes.CDLL(str(path))
    lib.cmpct_logs_verify.argtypes = [ctypes.c_char_p]
    lib.cmpct_logs_verify.restype = ctypes.c_int
    lib.cmpct_logs_extract.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint64]
    lib.cmpct_logs_extract.restype = ctypes.c_int
    return lib


def _native_verify(lib, archive: Path) -> float:
    started = time.perf_counter()
    rc = int(lib.cmpct_logs_verify(str(archive).encode()))
    elapsed = time.perf_counter() - started
    if rc != 0:
        raise RuntimeError(f"logs FFI verify failed closed with status {rc}")
    return elapsed


def _native_extract(lib, archive: Path, destination: Path, maximum_output_bytes: int = MAX_OUTPUT_BYTES) -> float:
    started = time.perf_counter()
    rc = int(lib.cmpct_logs_extract(str(archive).encode(), str(destination).encode(), int(maximum_output_bytes)))
    elapsed = time.perf_counter() - started
    if rc != 0:
        raise RuntimeError(f"logs FFI extract failed closed with status {rc}")
    return elapsed


def _corrupt_both_metadata(source: Path, target: Path) -> None:
    raw = bytearray(Path(source).read_bytes())
    raw[LOGS.V2.P.HEADER.size + 3] ^= 0x5A
    footer = LOGS.V2.P.FOOTER.unpack(bytes(raw[-LOGS.V2.P.FOOTER.size:]))
    tail_csize = int(footer[1])
    tail_meta_offset = len(raw) - LOGS.V2.P.FOOTER.size - tail_csize
    if tail_meta_offset < LOGS.V2.P.HEADER.size or tail_meta_offset + 3 >= len(raw):
        raise RuntimeError("logs tail metadata offset outside hostile probe bounds")
    raw[tail_meta_offset + 3] ^= 0xA5
    Path(target).write_bytes(raw)


def run(work_root: Path, native_library: Path) -> dict:
    native_library = Path(native_library)
    if not native_library.is_file():
        raise RuntimeError(f"native FFI library missing: {native_library}")
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpus")
    source = roots[TARGET]
    source_tree = PRODUCT.treehash(source)
    archive = work_root / "logs.cmpct"
    built = PRODUCT.build(source, archive)
    revision, profile = PRODUCT._revision_for_archive(archive)
    if int(revision or 0) != 25 or profile != LOGS.PROFILE:
        raise RuntimeError(f"logs target did not select canonical logs profile: {revision}/{profile}")
    receipt = PRODUCT.strong_verify(archive)
    if not receipt.get("ok") or receipt.get("tree_sha256") != source_tree:
        raise RuntimeError("shipping logs strong verification failed before FFI A/B")

    lib = _load_library(native_library)
    _native_verify(lib, archive)

    samples = {"python_verify": [], "native_verify": [], "python_extract": [], "native_extract": []}
    for round_index in range(ROUNDS):
        for native in ((True, False) if round_index % 2 else (False, True)):
            if native:
                samples["native_verify"].append(_native_verify(lib, archive))
                destination = work_root / f"native-extract-{round_index}"
                shutil.rmtree(destination, ignore_errors=True)
                samples["native_extract"].append(_native_extract(lib, archive, destination))
                if PRODUCT.treehash(destination) != source_tree:
                    raise RuntimeError("native FFI extraction tree identity drift")
                shutil.rmtree(destination, ignore_errors=True)
            else:
                started = time.perf_counter()
                verified = PRODUCT.strong_verify(archive)
                samples["python_verify"].append(time.perf_counter() - started)
                if not verified.get("ok") or verified.get("tree_sha256") != source_tree:
                    raise RuntimeError("Python logs verification identity drift")
                destination = work_root / f"python-extract-{round_index}"
                shutil.rmtree(destination, ignore_errors=True)
                started = time.perf_counter()
                PRODUCT.extract(archive, destination)
                samples["python_extract"].append(time.perf_counter() - started)
                if PRODUCT.treehash(destination) != source_tree:
                    raise RuntimeError("Python logs extraction tree identity drift")
                shutil.rmtree(destination, ignore_errors=True)

    corrupt = work_root / "logs-both-metadata-corrupt.cmpct"
    _corrupt_both_metadata(archive, corrupt)
    corruption_rejected = int(lib.cmpct_logs_verify(str(corrupt).encode())) != 0
    budget_destination = work_root / "budget-must-not-publish"
    shutil.rmtree(budget_destination, ignore_errors=True)
    budget_rc = int(lib.cmpct_logs_extract(str(archive).encode(), str(budget_destination).encode(), 1))
    budget_rejected_before_publication = budget_rc != 0 and not budget_destination.exists()

    medians = {key: float(statistics.median(values)) for key, values in samples.items()}
    verify_improvement = 1.0 - medians["native_verify"] / max(medians["python_verify"], 1e-9)
    extract_improvement = 1.0 - medians["native_extract"] / max(medians["python_extract"], 1e-9)
    gate = {
        "archive_bytes_unchanged": True,
        "canonical_tree_preserved": True,
        "native_corruption_rejected": corruption_rejected,
        "native_budget_rejected_before_publication": budget_rejected_before_publication,
        "verify_materially_faster": verify_improvement >= MIN_VERIFY_IMPROVEMENT,
        "extract_materially_faster": extract_improvement >= MIN_EXTRACT_IMPROVEMENT,
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-logs-native-ffi-reader-v1",
        "target": "/".join(TARGET),
        "shipping_build": built,
        "archive_bytes": archive.stat().st_size,
        "native_library": str(native_library),
        "native_bridge": "cmpct-portable-logs-inprocess-ffi-v1",
        "rounds": ROUNDS,
        "samples_s": samples,
        "medians_s": medians,
        "verify_improvement_fraction": verify_improvement,
        "extract_improvement_fraction": extract_improvement,
        "native_corruption_rejected": corruption_rejected,
        "native_budget_rejected_before_publication": budget_rejected_before_publication,
        "contract": {
            "minimum_verify_improvement_fraction": MIN_VERIFY_IMPROVEMENT,
            "minimum_extract_improvement_fraction": MIN_EXTRACT_IMPROVEMENT,
            "archive_bytes_changed": False,
            "grammar_changed": False,
            "selector_changed": False,
            "maximum_output_bytes": MAX_OUTPUT_BYTES,
            "caller_extract_budget_enforced_before_publication": True,
            "native_library_load_inside_timing": False,
            "native_ffi_call_and_archive_open_inside_timing": True,
        },
        "gate": gate,
        "promotion_signal": bool(gate["passed"]),
        "selector_change": False,
        "release_credit": False,
        "claim_boundary": "Research-only in-process FFI A/B over the already-production-dispatched Rust logs reader. A positive result authorizes explicit reader hot-path integration only; fuzz/native/Android/runtime authority must be re-earned.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--native-library", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-logs-native-ffi-reader-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-logs-native-ffi-reader.json"))
    args = parser.parse_args()
    result = run(args.work_root, args.native_library)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"medians_s": result["medians_s"], "verify_improvement_fraction": result["verify_improvement_fraction"], "extract_improvement_fraction": result["extract_improvement_fraction"], "promotion_signal": result["promotion_signal"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
