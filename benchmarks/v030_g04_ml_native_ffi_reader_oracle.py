from __future__ import annotations

"""A/B the canonical ML G0-G4 reader through an in-process Rust FFI boundary.

The older native oracle deliberately charged process startup, CLI info JSON and repeated archive opens.
That is useful for judging a subprocess integration, but not for judging the already-existing Rust reader
itself.  This oracle keeps the exact shipping archive fixed and calls the same cmpct-portable semantic owner
in-process.  Archive open, verify/extract work and caller output-budget preflight remain inside each timed FFI
call; only one-time dynamic-library loading is outside timing.
"""

import argparse
import ctypes
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_reader as RR

ROUNDS = 5
MIN_VERIFY_IMPROVEMENT = 0.20
MIN_EXTRACT_IMPROVEMENT = 0.20
TARGET = ("neutral_hostile_v1", "09_ml_artifacts")
MAX_OUTPUT_BYTES = RR.MAX_DECLARED_LOGICAL_BYTES


def _load_library(path: Path):
    lib = ctypes.CDLL(str(path))
    lib.cmpct_g04_verify.argtypes = [ctypes.c_char_p]
    lib.cmpct_g04_verify.restype = ctypes.c_int
    lib.cmpct_g04_extract.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint64]
    lib.cmpct_g04_extract.restype = ctypes.c_int
    return lib


def _native_verify(lib, archive: Path) -> float:
    started = time.perf_counter()
    rc = int(lib.cmpct_g04_verify(str(archive).encode()))
    elapsed = time.perf_counter() - started
    if rc != 0:
        raise RuntimeError(f"G0-G4 FFI verify failed closed with status {rc}")
    return elapsed


def _native_extract(lib, archive: Path, destination: Path, maximum_output_bytes: int = MAX_OUTPUT_BYTES) -> float:
    started = time.perf_counter()
    rc = int(lib.cmpct_g04_extract(str(archive).encode(), str(destination).encode(), int(maximum_output_bytes)))
    elapsed = time.perf_counter() - started
    if rc != 0:
        raise RuntimeError(f"G0-G4 FFI extract failed closed with status {rc}")
    return elapsed


def _python_measure(archive: Path, destination: Path | None) -> tuple[float, dict]:
    started = time.perf_counter()
    result = RR._stream_g04(archive, destination, RR.MAX_DECLARED_LOGICAL_BYTES)
    return time.perf_counter() - started, result


def _corrupt_first_physical_payload(source: Path, target: Path) -> None:
    shutil.copy2(source, target)
    stream, _meta, record_start, offsets, _merkle, _tail = RR._g04_open(target)
    try:
        first = int(record_start) + int(offsets[0])
    finally:
        stream.close()
    with target.open("r+b") as fh:
        fh.seek(first)
        header = fh.read(RR.A5.PH.size)
        if len(header) != RR.A5.PH.size:
            raise RuntimeError("short G0-G4 physical header")
        _codec, _usize, csize, _crc, _sha = RR.A5.PH.unpack(header)
        if int(csize) <= 0:
            raise RuntimeError("cannot corrupt empty G0-G4 physical payload")
        pos = first + RR.A5.PH.size + min(11, int(csize) - 1)
        fh.seek(pos)
        old = fh.read(1)
        if len(old) != 1:
            raise RuntimeError("short G0-G4 physical payload")
        fh.seek(pos)
        fh.write(bytes((old[0] ^ 0x01,)))


def run(work_root: Path, native_library: Path) -> dict:
    native_library = Path(native_library)
    if not native_library.is_file():
        raise RuntimeError(f"native G0-G4 FFI library missing: {native_library}")
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpus")
    source = roots[TARGET]
    source_tree = PRODUCT.treehash(source)
    archive = work_root / "ml.cmpct"

    with PRODUCT.C._revision25_profile_context():
        built = PRODUCT.build(source, archive)
        if archive.read_bytes()[:8] != RR.G04.MAG:
            raise RuntimeError("ML target did not select canonical G0-G4")
        strong = PRODUCT.strong_verify(archive)
        if not strong.get("ok") or strong.get("tree_sha256") != source_tree:
            raise RuntimeError("shipping strong verification failed before G0-G4 FFI A/B")

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
                    raise RuntimeError("native G0-G4 FFI extraction tree identity drift")
                shutil.rmtree(destination, ignore_errors=True)
            else:
                verify_s, verified = _python_measure(archive, None)
                samples["python_verify"].append(float(verify_s))
                if not verified.get("ok") or verified.get("tree_sha256") != source_tree:
                    raise RuntimeError("Python G0-G4 verification identity drift")
                destination = work_root / f"python-extract-{round_index}"
                shutil.rmtree(destination, ignore_errors=True)
                extract_s, extracted = _python_measure(archive, destination)
                samples["python_extract"].append(float(extract_s))
                if not extracted.get("ok") or extracted.get("tree_sha256") != source_tree:
                    raise RuntimeError("Python G0-G4 extraction identity drift")
                if PRODUCT.treehash(destination) != source_tree:
                    raise RuntimeError("Python G0-G4 extraction tree identity drift")
                shutil.rmtree(destination, ignore_errors=True)

    corrupt = work_root / "ml-corrupt.cmpct"
    _corrupt_first_physical_payload(archive, corrupt)
    corruption_rejected = int(lib.cmpct_g04_verify(str(corrupt).encode())) != 0

    budget_destination = work_root / "budget-must-not-publish"
    shutil.rmtree(budget_destination, ignore_errors=True)
    budget_rc = int(lib.cmpct_g04_extract(str(archive).encode(), str(budget_destination).encode(), 1))
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
        "schema": "cmpct-v030-g04-ml-native-ffi-reader-v1",
        "target": "/".join(TARGET),
        "shipping_build": built,
        "archive_bytes": archive.stat().st_size,
        "native_library": str(native_library),
        "native_bridge": "cmpct-portable-g04-inprocess-ffi-v1",
        "rounds": ROUNDS,
        "samples_s": samples,
        "medians_s": medians,
        "verify_improvement_fraction": float(verify_improvement),
        "extract_improvement_fraction": float(extract_improvement),
        "native_corruption_rejected": corruption_rejected,
        "native_budget_rejected_before_publication": budget_rejected_before_publication,
        "contract": {
            "minimum_verify_improvement_fraction": MIN_VERIFY_IMPROVEMENT,
            "minimum_extract_improvement_fraction": MIN_EXTRACT_IMPROVEMENT,
            "archive_bytes_changed": False,
            "grammar_changed": False,
            "selector_changed": False,
            "memory_budget_changed": False,
            "locality_limit": 8.0,
            "decode_unit_limit_bytes": 8 * 1024 * 1024,
            "maximum_output_bytes": MAX_OUTPUT_BYTES,
            "caller_extract_budget_enforced_before_publication": True,
            "native_library_load_inside_timing": False,
            "native_ffi_call_and_archive_open_inside_timing": True,
        },
        "gate": gate,
        "promotion_signal": bool(gate["passed"]),
        "selector_change": False,
        "release_credit": False,
        "claim_boundary": "Research-only in-process FFI A/B over the existing production-dispatched Rust G0-G4 reader. A positive result authorizes explicit ML reader hot-path integration only; fuzz/native/Android/runtime authority must be re-earned.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--native-library", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-native-ffi-reader-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-native-ffi-reader.json"))
    args = parser.parse_args()
    result = run(args.work_root, args.native_library)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"medians_s": result["medians_s"], "verify_improvement_fraction": result["verify_improvement_fraction"], "extract_improvement_fraction": result["extract_improvement_fraction"], "promotion_signal": result["promotion_signal"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
