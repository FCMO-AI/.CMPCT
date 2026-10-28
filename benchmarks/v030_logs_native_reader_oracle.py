from __future__ import annotations

"""Measure the production Rust logs reader against the promoted Python logs reader.

The canonical logs-inverse representation already wins the external create/size frontier, while the
release runtime gate still measures extraction around 1.7x v0.29.  Rust production dispatch for this
exact profile already exists.  This oracle therefore keeps archive bytes fixed and measures whether the
existing portable reader can retire the remaining logs read-side regression.

Native process startup, archive open and the caller-output-budget ``info`` preflight are inside timing.
A positive result is integration evidence only: it does not switch the public product and carries zero
release credit until the normal reader/fuzz/native/Android/runtime authorities are re-earned.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_logs_inverse_profile_v3 as LOGS
from experiments import entropygraph_v030_native_logs_reader_bridge as NATIVE
from experiments import entropygraph_v030_release_product as PRODUCT

ROUNDS = 5
MIN_VERIFY_IMPROVEMENT = 0.20
MIN_EXTRACT_IMPROVEMENT = 0.20
MAX_OUTPUT_BYTES = LOGS.MAX_LOGICAL_BYTES
TARGET = ("neutral_hostile_v1", "05_logs_and_telemetry")


def _python_verify_measure(archive: Path) -> tuple[float, dict]:
    started = time.perf_counter()
    receipt = PRODUCT.strong_verify(archive)
    return time.perf_counter() - started, receipt


def _python_extract_measure(archive: Path, destination: Path) -> tuple[float, dict]:
    started = time.perf_counter()
    PRODUCT.extract(archive, destination)
    elapsed = time.perf_counter() - started
    return elapsed, {"ok": True, "tree_sha256": PRODUCT.treehash(destination)}


def _native_verify_measure(cli: Path, archive: Path) -> tuple[float, dict]:
    started = time.perf_counter()
    receipt = NATIVE.verify_logs(cli, archive)
    return time.perf_counter() - started, receipt


def _native_extract_measure(cli: Path, archive: Path, destination: Path) -> tuple[float, dict]:
    started = time.perf_counter()
    receipt = NATIVE.extract_logs(
        cli,
        archive,
        destination,
        max_output_bytes=MAX_OUTPUT_BYTES,
    )
    return time.perf_counter() - started, receipt


def _corrupt_both_metadata(source: Path, target: Path) -> None:
    raw = bytearray(Path(source).read_bytes())
    if len(raw) <= LOGS.V2.P.HEADER.size + LOGS.V2.P.FOOTER.size + 8:
        raise RuntimeError("logs archive too short for hostile corruption probe")
    raw[LOGS.V2.P.HEADER.size + 3] ^= 0x5A
    footer = LOGS.V2.P.FOOTER.unpack(bytes(raw[-LOGS.V2.P.FOOTER.size:]))
    tail_csize = int(footer[1])
    tail_meta_offset = len(raw) - LOGS.V2.P.FOOTER.size - tail_csize
    if tail_meta_offset < LOGS.V2.P.HEADER.size or tail_meta_offset + 3 >= len(raw):
        raise RuntimeError("logs tail metadata offset outside hostile probe bounds")
    raw[tail_meta_offset + 3] ^= 0xA5
    Path(target).write_bytes(raw)


def run(work_root: Path, native_cli: Path) -> dict:
    native_cli = Path(native_cli)
    if not native_cli.is_file():
        raise RuntimeError(f"native CLI not found: {native_cli}")
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

    strong = PRODUCT.strong_verify(archive)
    if not strong.get("ok") or strong.get("tree_sha256") != source_tree:
        raise RuntimeError("shipping logs strong verification failed before native A/B")

    warm_info = NATIVE.info_logs(native_cli, archive)
    warm_verify = NATIVE.verify_logs(native_cli, archive)
    if warm_info.get("profile") != NATIVE.CANONICAL_LOGS_PROFILE or int(warm_info.get("revision", 0)) != 25:
        raise RuntimeError("native logs info warm-up did not bind canonical revision/profile")
    if not warm_info.get("tail_metadata_authenticated"):
        raise RuntimeError("native logs info did not authenticate tail metadata")
    if not warm_verify.get("ok"):
        raise RuntimeError("native logs verify warm-up failed")

    samples = {"python_verify": [], "native_verify": [], "python_extract": [], "native_extract": []}
    native_extract_receipts: list[dict] = []
    for round_index in range(ROUNDS):
        native_first = bool(round_index % 2)
        for native in ((True, False) if native_first else (False, True)):
            if native:
                verify_s, verified = _native_verify_measure(native_cli, archive)
                if not verified.get("ok") or verified.get("profile") != NATIVE.CANONICAL_LOGS_PROFILE:
                    raise RuntimeError("native logs verification receipt drift")
                samples["native_verify"].append(float(verify_s))
                destination = work_root / f"native-extract-{round_index}"
                shutil.rmtree(destination, ignore_errors=True)
                extract_s, extracted = _native_extract_measure(native_cli, archive, destination)
                samples["native_extract"].append(float(extract_s))
                native_extract_receipts.append(dict(extracted))
                if PRODUCT.treehash(destination) != source_tree:
                    raise RuntimeError("native logs extraction tree identity drift")
                shutil.rmtree(destination, ignore_errors=True)
            else:
                verify_s, verified = _python_verify_measure(archive)
                if not verified.get("ok") or verified.get("tree_sha256") != source_tree:
                    raise RuntimeError("Python logs verification identity drift")
                samples["python_verify"].append(float(verify_s))
                destination = work_root / f"python-extract-{round_index}"
                shutil.rmtree(destination, ignore_errors=True)
                extract_s, extracted = _python_extract_measure(archive, destination)
                samples["python_extract"].append(float(extract_s))
                if extracted.get("tree_sha256") != source_tree:
                    raise RuntimeError("Python logs extraction tree identity drift")
                shutil.rmtree(destination, ignore_errors=True)

    corrupt = work_root / "logs-both-metadata-corrupt.cmpct"
    _corrupt_both_metadata(archive, corrupt)
    try:
        NATIVE.verify_logs(native_cli, corrupt)
    except NATIVE.NativeLogsReaderError:
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
        "native_tail_metadata_authenticated": bool(warm_info["tail_metadata_authenticated"]),
        "native_corruption_rejected": native_corruption_rejected,
        "native_caller_budget_preserved": native_budget_preserved,
        "verify_materially_faster": verify_improvement >= MIN_VERIFY_IMPROVEMENT,
        "extract_materially_faster": extract_improvement >= MIN_EXTRACT_IMPROVEMENT,
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-logs-native-reader-v1",
        "target": "/".join(TARGET),
        "shipping_build": built,
        "archive_bytes": archive.stat().st_size,
        "native_cli": str(native_cli),
        "native_bridge": "cmpct-portable-logs-process-v1",
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
            "selector_changed": False,
            "maximum_output_bytes": MAX_OUTPUT_BYTES,
            "locality_limit": 8.0,
            "decode_unit_limit_bytes": 8 * 1024 * 1024,
            "caller_extract_budget_enforced_before_publication": True,
        },
        "gate": gate,
        "promotion_signal": bool(gate["passed"]),
        "release_credit": False,
        "claim_boundary": (
            "Research-only A/B of the already-production-dispatched Rust logs-inverse reader through a fail-closed "
            "process bridge against the promoted Python release reader. Native timing includes process startup, "
            "archive open and output-budget info preflight. A positive result authorizes explicit hot-path integration "
            "only; reader/fuzz/native/Android/runtime authority must be re-earned."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--native-cli", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-logs-native-reader-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-logs-native-reader.json"))
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
