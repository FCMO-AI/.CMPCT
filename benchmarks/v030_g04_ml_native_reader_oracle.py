from __future__ import annotations

"""Measure the existing Rust G0-G4 reader against the canonical Python ML reader.

This is a research-only execution-path oracle. It changes no archive bytes, grammar, cache budget,
locality law, recovery rule or SHA-256 requirement. The Rust CLI is built before timing; each timed
sample includes ordinary process startup plus native archive open/verify or transactional extract.
The Python baseline is the current canonical G0-G4 streaming reader used by the release product.

A positive result does not switch shipping by itself. It establishes whether the already-existing
portable Rust reader is fast enough to justify wiring the ML complete verify/extract hot path to
native code and then re-earning reader/fuzz/native/Android/runtime authority.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import time

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_release_reader as RR

ROUNDS = 5
MIN_VERIFY_IMPROVEMENT = 0.20
MIN_EXTRACT_IMPROVEMENT = 0.20


def _python_measure(archive: Path, destination: Path | None) -> tuple[float, dict]:
    started = time.perf_counter()
    result = RR._stream_g04(archive, destination, RR.MAX_DECLARED_LOGICAL_BYTES)
    return time.perf_counter() - started, result


def _native_measure(cli: Path, command: str, archive: Path, destination: Path | None = None) -> float:
    argv = [str(cli), command, str(archive)]
    if destination is not None:
        argv.append(str(destination))
    started = time.perf_counter()
    completed = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    elapsed = time.perf_counter() - started
    if completed.returncode != 0:
        raise RuntimeError(
            f"native {command} failed rc={completed.returncode}: "
            + completed.stderr.decode("utf-8", errors="replace")[-2000:]
        )
    return elapsed


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

    # Untimed warm-up validates that the native binary recognizes the exact canonical archive.
    _native_measure(native_cli, "verify", archive)

    samples = {"python_verify": [], "native_verify": [], "python_extract": [], "native_extract": []}
    for round_index in range(ROUNDS):
        native_first = bool(round_index % 2)
        for native in ((True, False) if native_first else (False, True)):
            if native:
                samples["native_verify"].append(_native_measure(native_cli, "verify", archive))
                destination = work_root / f"native-extract-{round_index}"
                shutil.rmtree(destination, ignore_errors=True)
                samples["native_extract"].append(_native_measure(native_cli, "extract", archive, destination))
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
    native_corruption_rejected = subprocess.run(
        [str(native_cli), "verify", str(corrupt)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    ).returncode != 0

    medians = {key: float(statistics.median(values)) for key, values in samples.items()}
    verify_improvement = 1.0 - medians["native_verify"] / max(medians["python_verify"], 1e-9)
    extract_improvement = 1.0 - medians["native_extract"] / max(medians["python_extract"], 1e-9)
    gate = {
        "archive_bytes_unchanged": True,
        "canonical_tree_preserved": True,
        "native_corruption_rejected": native_corruption_rejected,
        "verify_materially_faster": verify_improvement >= MIN_VERIFY_IMPROVEMENT,
        "extract_materially_faster": extract_improvement >= MIN_EXTRACT_IMPROVEMENT,
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-g04-ml-native-reader-v1",
        "target": "neutral_hostile_v1/09_ml_artifacts",
        "shipping_build": built,
        "native_cli": str(native_cli),
        "rounds": ROUNDS,
        "samples_s": samples,
        "medians_s": medians,
        "verify_improvement_fraction": float(verify_improvement),
        "extract_improvement_fraction": float(extract_improvement),
        "native_corruption_rejected": native_corruption_rejected,
        "contract": {
            "minimum_verify_improvement_fraction": MIN_VERIFY_IMPROVEMENT,
            "minimum_extract_improvement_fraction": MIN_EXTRACT_IMPROVEMENT,
            "archive_bytes_changed": False,
            "grammar_changed": False,
            "memory_budget_changed": False,
            "locality_limit": 8.0,
            "decode_unit_limit_bytes": 8 * 1024 * 1024,
        },
        "gate": gate,
        "promotion_signal": bool(gate["passed"]),
        "release_credit": False,
        "claim_boundary": (
            "Research-only A/B of the already-existing portable Rust G0-G4 reader against the canonical Python "
            "complete-stream reader. A positive result only authorizes explicit native hot-path integration work; "
            "reader/fuzz/native/Android/runtime authority must be re-earned on the integrated candidate."
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
        "promotion_signal": result["promotion_signal"],
    }, indent=2), flush=True)
    # A valid but slower native reader is still useful negative evidence. Integrity/identity failures raise above.


if __name__ == "__main__":
    main()
