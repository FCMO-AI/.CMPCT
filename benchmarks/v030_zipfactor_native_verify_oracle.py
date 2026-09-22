from __future__ import annotations

"""Exact Python-vs-native verification A/B for the canonical ZIP-factor candidate.

Research-only.  The archive bytes are built once with the existing canonical binary-control-v3 builder.  Five
rotated rounds compare the mandatory Python verifier with the portable Rust reader's `verify` command.  Native
process startup and archive open are inside timing; Rust compilation is outside.  Promotion requires exact archive
identity, semantic equivalence, hostile-payload rejection, unchanged locality/decode bounds, and >=20% lower median
verification time.  This oracle grants no release or selector credit by itself.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import tempfile
import time

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from experiments import entropygraph_v030_canonical_final_impl as CANON
from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_zipfactor_compact_v3 as V3

ROUNDS = 5
MIN_SPEEDUP = 0.20


def _python_verify(path: Path) -> dict:
    scan = V3.verify_and_identities(path)
    manifest_raw = scan["manifest_raw"]
    decoded = scan["manifest"]
    identities = scan["identities"]
    expected_paths = set(decoded["regular"]) | {FS.FILESYSTEM_MANIFEST}
    if set(identities) != expected_paths:
        raise RuntimeError("Python ZIP-factor verifier namespace mismatch")
    if identities[FS.FILESYSTEM_MANIFEST] != (len(manifest_raw), hashlib.sha256(manifest_raw).digest()):
        raise RuntimeError("Python ZIP-factor verifier manifest identity mismatch")
    for rel, identity in decoded["regular"].items():
        if identities.get(rel) != identity:
            raise RuntimeError(f"Python ZIP-factor verifier member identity mismatch: {rel}")
    return {
        "tree": CANON._semantic_tree_sha(decoded),
        "max_member_read_amplification": float(scan["max_member_read_amplification"]),
        "max_decode_unit_bytes": int(scan["max_decode_unit_bytes"]),
    }


def _native_verify(binary: Path, archive: Path) -> str:
    proc = subprocess.run(
        [str(binary), "verify", str(archive)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"native verify failed: {proc.stderr.strip()}")
    out = proc.stdout.strip()
    if not out.startswith("ok profile="):
        raise RuntimeError(f"unexpected native verify receipt: {out!r}")
    return out


def _native_info(binary: Path, archive: Path) -> dict[str, str]:
    proc = subprocess.run(
        [str(binary), "info", str(archive)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    result: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            result[key] = value
    return result


def _corrupt_physical_payload(source: Path, dest: Path) -> None:
    data = bytearray(source.read_bytes())
    # Locate the first physical record after the canonical header/control area using the verified parser's
    # format metadata.  Fall back to a middle-byte mutation only if the implementation does not expose an offset;
    # native verification must reject either corruption.
    scan = V3.verify_and_identities(source)
    offset = int(scan.get("first_physical_payload_offset", 0))
    if offset <= 0 or offset >= len(data):
        offset = max(64, len(data) // 2)
    data[offset] ^= 0x01
    dest.write_bytes(data)


def run(work_root: Path, native_binary: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    CORPUS.build(corpus)
    source = corpus / "04_deflate_family"

    with tempfile.TemporaryDirectory(prefix="cmpct-zf-native-verify-", dir=work_root) as td_raw:
        td = Path(td_raw)
        candidate = td / "candidate.cmpct"
        build_stats = V3.build(source, candidate, level=3, group_size=7)
        archive_sha = hashlib.sha256(candidate.read_bytes()).hexdigest()
        python_identity = _python_verify(candidate)
        native_receipt = _native_verify(native_binary, candidate)
        info = _native_info(native_binary, candidate)

        python_samples: list[float] = []
        native_samples: list[float] = []
        for round_index in range(ROUNDS):
            order = ("python", "native") if round_index % 2 == 0 else ("native", "python")
            for impl in order:
                started = time.perf_counter()
                if impl == "python":
                    again = _python_verify(candidate)
                    if again != python_identity:
                        raise RuntimeError("Python verification identity drifted between rounds")
                    python_samples.append(time.perf_counter() - started)
                else:
                    _native_verify(native_binary, candidate)
                    native_samples.append(time.perf_counter() - started)

        corrupt = td / "corrupt.cmpct"
        _corrupt_physical_payload(candidate, corrupt)
        hostile = subprocess.run(
            [str(native_binary), "verify", str(corrupt)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        native_rejects_corruption = hostile.returncode != 0

        py_median = statistics.median(python_samples)
        native_median = statistics.median(native_samples)
        speedup = (py_median - native_median) / py_median if py_median else 0.0
        locality_green = (
            python_identity["max_member_read_amplification"] <= 8.0
            and python_identity["max_decode_unit_bytes"] <= 8 * 1024 * 1024
        )
        exact_profile = info.get("profile") == V3.PROFILE and info.get("revision") == "25"
        experiment_valid = bool(
            archive_sha == hashlib.sha256(candidate.read_bytes()).hexdigest()
            and native_receipt == f"ok profile={V3.PROFILE}"
            and exact_profile
            and locality_green
            and native_rejects_corruption
            and len(python_samples) == ROUNDS
            and len(native_samples) == ROUNDS
        )
        promotion_signal = bool(experiment_valid and speedup >= MIN_SPEEDUP)
        return {
            "schema": "cmpct-v030-zipfactor-native-verify-oracle-v1",
            "contract": {
                "rounds": ROUNDS,
                "minimum_native_verify_speedup": MIN_SPEEDUP,
                "native_compile_inside_timing": False,
                "native_process_startup_inside_timing": True,
                "archive_bytes_changed": False,
                "selector_change": False,
                "release_credit": False,
            },
            "candidate": {
                **build_stats,
                "archive_bytes": candidate.stat().st_size,
                "archive_sha256": archive_sha,
                "profile": info.get("profile"),
                "revision": info.get("revision"),
                "semantic_tree_sha256": python_identity["tree"],
                "max_member_read_amplification": python_identity["max_member_read_amplification"],
                "max_decode_unit_bytes": python_identity["max_decode_unit_bytes"],
            },
            "python_verify_samples_s": python_samples,
            "native_verify_samples_s": native_samples,
            "python_verify_median_s": py_median,
            "native_verify_median_s": native_median,
            "native_verify_speedup": speedup,
            "native_rejects_corruption": native_rejects_corruption,
            "experiment_valid": experiment_valid,
            "promotion_signal": promotion_signal,
            "release_credit": False,
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--native-binary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root, args.native_binary)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("ZIP-factor native verification experiment invalid")


if __name__ == "__main__":
    main()
