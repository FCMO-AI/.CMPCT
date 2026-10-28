from __future__ import annotations

"""Measure the existing Rust G0-G4 reader against the canonical Python ML reader.

This is a research-only execution-path oracle. It changes no archive bytes, grammar, cache budget,
locality law, recovery rule or SHA-256 requirement. The Rust CLI is built before timing. Native samples
pass through the fail-closed process bridge intended for any later release integration rather than
calling the executable ad hoc; extraction therefore includes the caller output-budget preflight that
shipping would require. That preflight uses the compact native ``info`` receipt, not full namespace
serialization, so the A/B does not manufacture avoidable process/stdout overhead.

A positive result does not switch shipping by itself. It establishes whether the already-existing
portable Rust reader is fast enough, through a productizable call boundary, to justify wiring the ML
complete verify/extract hot path to native code and then re-earning reader/fuzz/native/Android/runtime authority.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_native_reader_bridge as NATIVE
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_reader as RR

ROUNDS = 5
MIN_VERIFY_IMPROVEMENT = 0.20
MIN_EXTRACT_IMPROVEMENT = 0.20


def _python_measure(archive: Path, destination: Path | None) -> tuple[float, dict]:
    started = time.perf_counter()
    result = RR._stream_g04(archive, destination, RR.MAX_DECLARED_LOGICAL_BYTES)
    return time.perf_counter() - started, result


def _native_verify_measure(cli: Path, archive: Path) -> tuple[float, dict]:
    started = time.perf_counter()
    receipt = NATIVE.verify_g04(cli, archive)
    return time.perf_counter() - started, receipt


def _native_extract_measure(cli: Path, archive: Path, destination: Path) -> tuple[float, dict]:
    started = time.perf_counter()
    receipt = NATIVE.extract_g04(
        cli,
        archive,
        destination,
        max_output_bytes=RR.MAX_DECLARED_LOGICAL_BYTES,
    )
    return time.perf_counter() - started, receipt


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


def run(work_root: Path, native_cli: Path) -> dict:
    if not native_cli.is_file():
        raise RuntimeError(f"native CLI not found: {native_cli}")
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpus")
    source = roots[("neutral_hostile_v1", "09_ml_artifacts")]
    source_tree = PRODUCT.treehash(source)
    archive = work_root / "ml.cmpct"

    with PRODUCT.C._revision25_profile_context():
        built = PRODUCT.build(source, archive)
        if archive.read_bytes()[:8] != RR.G04.MAG:
            raise RuntimeError("ML target did not select canonical G0-G4")
        strong = PRODUCT.strong_verify(archive)
        if not strong.get("ok") or strong.get("tree_sha256") != source_tree:
            raise RuntimeError("shipping strong verification failed before native A/B")

    warm_verify = NATIVE.verify_g04(native_cli, archive)
    warm_info = NATIVE.info_g04(native_cli, archive)
    if not warm_verify.get("ok") or warm_verify.get("profile") != NATIVE.CANONICAL_G04_PROFILE:
        raise RuntimeError("native bridge warm-up did not bind canonical G0-G4")
    if warm_info.get("profile") != NATIVE.CANONICAL_G04_PROFILE or int(warm_info.get("revision", 0)) != 25:
        raise RuntimeError("native info warm-up did not bind canonical G0-G4 revision")

    samples = {"python_verify": [], "native_verify": [], "python_extract": [], "native_extract": []}
    native_extract_receipts: list[dict] = []
    for round_index in range(ROUNDS):
        native_first = bool(round_index % 2)
        for native in ((True, False) if native_first else (False, True)):
            if native:
                verify_s, verify_receipt = _native_verify_measure(native_cli, archive)
                if not verify_receipt.get("ok") or verify_receipt.get("profile") != NATIVE.CANONICAL_G04_PROFILE:
                    raise RuntimeError("native bridge verification receipt drift")
                samples["native_verify"].append(float(verify_s))
                destination = work_root / f"native-extract-{round_index}"
                shutil.rmtree(destination, ignore_errors=True)
                extract_s, extract_receipt = _native_extract_measure(native_cli, archive, destination)
                samples["native_extract"].append(float(extract_s))
                native_extract_receipts.append(dict(extract_receipt))
                if PRODUCT.treehash(destination) != source_tree:
                    raise RuntimeError("native extraction tree identity drift")
                shutil.rmtree(destination, ignore_errors=True)
            else:
                verify_s, verified = _python_measure(archive, None)
                if not verified.get("ok") or verified.get("tree_sha256") != source_tree:
                    raise RuntimeError("Python verification identity drift")
                samples["python_verify"].append(float(verify_s))
                destination = work_root / f"python-extract-{round_index}"
                shutil.rmtree(destination, ignore_errors=True)
                extract_s, extracted = _python_measure(archive, destination)
                if not extracted.get("ok") or extracted.get("tree_sha256") != source_tree:
                    raise RuntimeError("Python extraction identity drift")
                if PRODUCT.treehash(destination) != source_tree:
                    raise RuntimeError("Python extraction tree identity drift")
                samples["python_extract"].append(float(extract_s))
                shutil.rmtree(destination, ignore_errors=True)

    corrupt = work_root / "ml-corrupt.cmpct"
    _corrupt_first_physical_payload(archive, corrupt)
    try:
        NATIVE.verify_g04(native_cli, corrupt)
    except NATIVE.NativeReaderError:
        native_corruption_rejected = True
    else:
        native_corruption_rejected = False

    native_budget_preserved = all(
        int(receipt.get("declared_regular_bytes", -1)) <= int(receipt.get("caller_max_output_bytes", -2))
        and receipt.get("transactional_native_extract") is True
        and receipt.get("budget_preflight") == "native-info-logical-regular-bytes-v1"
        for receipt in native_extract_receipts
    )
    medians = {key: float(statistics.median(values)) for key, values in samples.items()}
    verify_improvement = 1.0 - medians["native_verify"] / max(medians["python_verify"], 1e-9)
    extract_improvement = 1.0 - medians["native_extract"] / max(medians["python_extract"], 1e-9)
    gate = {
        "archive_bytes_unchanged": True,
        "canonical_tree_preserved": True,
        "native_corruption_rejected": native_corruption_rejected,
        "native_caller_budget_preserved": native_budget_preserved,
        "verify_materially_faster": verify_improvement >= MIN_VERIFY_IMPROVEMENT,
        "extract_materially_faster": extract_improvement >= MIN_EXTRACT_IMPROVEMENT,
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-g04-ml-native-reader-v2",
        "target": "neutral_hostile_v1/09_ml_artifacts",
        "shipping_build": built,
        "native_cli": str(native_cli),
        "native_bridge": "cmpct-portable-process-v2",
        "native_extract_budget_preflight": "native-info-logical-regular-bytes-v1",
        "native_extract_budget_preflight_timed": True,
        "rounds": ROUNDS,
        "samples_s": samples,
        "medians_s": medians,
        "verify_improvement_fraction": float(verify_improvement),
        "extract_improvement_fraction": float(extract_improvement),
        "native_corruption_rejected": native_corruption_rejected,
        "native_caller_budget_preserved": native_budget_preserved,
        "contract": {
            "minimum_verify_improvement_fraction": MIN_VERIFY_IMPROVEMENT,
            "minimum_extract_improvement_fraction": MIN_EXTRACT_IMPROVEMENT,
            "archive_bytes_changed": False,
            "grammar_changed": False,
            "memory_budget_changed": False,
            "locality_limit": 8.0,
            "decode_unit_limit_bytes": 8 * 1024 * 1024,
            "caller_extract_budget_enforced_before_publication": True,
        },
        "gate": gate,
        "promotion_signal": bool(gate["passed"]),
        "release_credit": False,
        "claim_boundary": (
            "Research-only A/B of the existing portable Rust G0-G4 reader through the fail-closed process bridge "
            "against the canonical Python complete-stream reader. Native extraction timing includes the compact "
            "native-info budget preflight needed to preserve the caller max-output contract. A positive result only "
            "authorizes explicit native hot-path integration; reader/fuzz/native/Android/runtime authority must be re-earned."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--native-cli", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-native-reader-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-g04-ml-native-reader.json"))
    args = parser.parse_args()
    result = run(args.work_root, args.native_cli)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "medians_s": result["medians_s"],
        "verify_improvement_fraction": result["verify_improvement_fraction"],
        "extract_improvement_fraction": result["extract_improvement_fraction"],
        "native_corruption_rejected": result["native_corruption_rejected"],
        "native_caller_budget_preserved": result["native_caller_budget_preserved"],
        "promotion_signal": result["promotion_signal"],
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
