from __future__ import annotations

"""Complete external frontier for the exact ZIP-factor v3 candidate with native strong verification.

This is the next promotion boundary after the native verifier A/B. It times the complete candidate operation as
canonical v3 build + mandatory Rust strong verification, including native process startup/archive open. The same
normalized source tree is compared in rotated same-runner rounds against deterministic ZIP/Deflate-9 and solid
Zstd-19. ZIP/Zstd creation boundaries remain exactly those used by the external competitor harness.

Identity has two deliberately separate domains. External comparator extraction is checked with the historical
external-matrix treehash because that is the frozen ZIP/Zstd contract. The r25 ZIP-factor filesystem manifest is
checked against the canonical product semantic-tree hash because it binds directories/links as well as regular
content. Comparing those two hashes directly is invalid even when both describe the same normalized source tree.

Research-only: a positive result proves that native verification is sufficient to cross the complete size+create
frontier; it does not itself promote CMP25Z3 into canonical dispatch, recovery, Android, or the release selector.
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
from benchmarks import v030_external_competitors as EXT
from experiments import entropygraph_v030_canonical_final_impl as CANON
from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_zipfactor_compact_v3 as V3

ROUNDS = 9
LEVEL = 3
GROUP_SIZE = 7


def _native_verify(binary: Path, archive: Path) -> str:
    proc = subprocess.run(
        [str(binary), "verify", str(archive)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"native ZIP-factor verification failed: {proc.stderr.strip()}")
    receipt = proc.stdout.strip()
    if receipt != f"ok profile={V3.PROFILE}":
        raise RuntimeError(f"unexpected native ZIP-factor receipt: {receipt!r}")
    return receipt


def _python_identity(path: Path) -> dict:
    scan = V3.verify_and_identities(path)
    manifest_raw = scan["manifest_raw"]
    decoded = scan["manifest"]
    identities = scan["identities"]
    expected = set(decoded["regular"]) | {FS.FILESYSTEM_MANIFEST}
    if set(identities) != expected:
        raise RuntimeError("ZIP-factor namespace mismatch")
    if identities[FS.FILESYSTEM_MANIFEST] != (len(manifest_raw), hashlib.sha256(manifest_raw).digest()):
        raise RuntimeError("ZIP-factor manifest identity mismatch")
    return {
        "tree_sha256": CANON._semantic_tree_sha(decoded),
        "max_member_read_amplification": float(scan["max_member_read_amplification"]),
        "max_decode_unit_bytes": int(scan["max_decode_unit_bytes"]),
    }


def _cmpct_once(stage: Path, archive: Path, binary: Path) -> dict:
    complete_started = time.perf_counter()
    build_started = time.perf_counter()
    stats = V3.build(stage, archive, level=LEVEL, group_size=GROUP_SIZE)
    build_s = time.perf_counter() - build_started
    verify_started = time.perf_counter()
    _native_verify(binary, archive)
    verify_s = time.perf_counter() - verify_started
    complete_s = time.perf_counter() - complete_started
    return {
        "archive_bytes": archive.stat().st_size,
        "create_verify_s": complete_s,
        "build_s": build_s,
        "verify_s": verify_s,
        "stats": stats,
    }


def run(work_root: Path, native_binary: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    CORPUS.build(corpus)
    source = corpus / "04_deflate_family"

    with tempfile.TemporaryDirectory(prefix="cmpct-zf-native-frontier-", dir=work_root) as td_raw:
        td = Path(td_raw)
        stage = EXT._normalized_stage(source, td)
        expected_external_tree = EXT._tree(stage)
        expected_canonical_tree = CANON.treehash(stage)

        # Establish exact candidate identity once outside timing; every timed build must reproduce it byte-for-byte.
        reference = td / "reference.cmpct"
        reference_stats = V3.build(stage, reference, level=LEVEL, group_size=GROUP_SIZE)
        reference_sha = hashlib.sha256(reference.read_bytes()).hexdigest()
        identity = _python_identity(reference)
        _native_verify(native_binary, reference)
        if identity["tree_sha256"] != expected_canonical_tree:
            raise RuntimeError("ZIP-factor semantic tree differs from canonical normalized source")
        if identity["max_member_read_amplification"] > 8.0:
            raise RuntimeError("ZIP-factor locality exceeds 8x")
        if identity["max_decode_unit_bytes"] > 8 * 1024 * 1024:
            raise RuntimeError("ZIP-factor decode unit exceeds 8 MiB")

        samples = {"cmpct": [], "zip": [], "zstd19": []}
        cmpct_phases = {"build": [], "verify": []}
        sizes: dict[str, int] = {}
        orders = (
            ("cmpct", "zip", "zstd19"),
            ("zip", "zstd19", "cmpct"),
            ("zstd19", "cmpct", "zip"),
        )
        for round_index in range(ROUNDS):
            round_dir = td / f"round-{round_index}"
            round_dir.mkdir()
            for impl in orders[round_index % len(orders)]:
                if impl == "cmpct":
                    archive = round_dir / "candidate.cmpct"
                    result = _cmpct_once(stage, archive, native_binary)
                    if hashlib.sha256(archive.read_bytes()).hexdigest() != reference_sha:
                        raise RuntimeError("timed ZIP-factor build drifted from exact reference bytes")
                    samples[impl].append(float(result["create_verify_s"]))
                    cmpct_phases["build"].append(float(result["build_s"]))
                    cmpct_phases["verify"].append(float(result["verify_s"]))
                    sizes.setdefault(impl, int(result["archive_bytes"]))
                    if sizes[impl] != int(result["archive_bytes"]):
                        raise RuntimeError("ZIP-factor archive size drifted between rounds")
                elif impl == "zip":
                    archive = round_dir / "archive.zip"
                    extracted = round_dir / "zip-out"
                    result = EXT._zip(stage, archive, extracted)
                    EXT._verify_extracted(extracted, expected_external_tree, "zip-native-frontier")
                    samples[impl].append(float(result["create_s"]))
                    sizes.setdefault(impl, int(result["archive_bytes"]))
                    if sizes[impl] != int(result["archive_bytes"]):
                        raise RuntimeError("ZIP archive size drifted between rounds")
                else:
                    archive = round_dir / "archive.tar.zst"
                    extracted = round_dir / "zstd-out"
                    zwork = round_dir / "zstd-work"
                    zwork.mkdir()
                    result = EXT._tar_zstd(stage, archive, extracted, zwork)
                    if not result.get("available"):
                        raise RuntimeError("solid Zstd-19 unavailable")
                    EXT._verify_extracted(extracted, expected_external_tree, "zstd19-native-frontier")
                    samples[impl].append(float(result["create_s"]))
                    sizes.setdefault(impl, int(result["archive_bytes"]))
                    if sizes[impl] != int(result["archive_bytes"]):
                        raise RuntimeError("Zstd archive size drifted between rounds")

        medians = {name: statistics.median(values) for name, values in samples.items()}
        phase_medians = {name: statistics.median(values) for name, values in cmpct_phases.items()}
        strict_four_way = bool(
            sizes["cmpct"] < sizes["zip"]
            and sizes["cmpct"] < sizes["zstd19"]
            and medians["cmpct"] < medians["zip"]
            and medians["cmpct"] < medians["zstd19"]
        )
        return {
            "schema": "cmpct-v030-zipfactor-native-complete-frontier-v2",
            "contract": {
                "rounds": ROUNDS,
                "cmpct_timing": "exact-v3-build-plus-native-strong-verify",
                "native_process_startup_inside_timing": True,
                "native_compile_inside_timing": False,
                "zip_timing": "external-harness-deflate9-create",
                "zstd19_timing": "external-harness-solid-tar-plus-zstd19-create",
                "external_identity_domain": "frozen-external-treehash",
                "cmpct_identity_domain": "canonical-r25-semantic-tree",
                "ties_fail": True,
                "archive_bytes_changed": False,
                "selector_change": False,
                "release_credit": False,
                "phase_timing_is_diagnostic_only": True,
            },
            "source_identity": {
                "external_tree_sha256": expected_external_tree,
                "canonical_tree_sha256": expected_canonical_tree,
            },
            "candidate": {
                **reference_stats,
                "archive_bytes": reference.stat().st_size,
                "archive_sha256": reference_sha,
                **identity,
            },
            "sizes": sizes,
            "samples_s": samples,
            "cmpct_phase_samples_s": cmpct_phases,
            "medians_s": medians,
            "cmpct_phase_medians_s": phase_medians,
            "strict_four_way_win": strict_four_way,
            "experiment_valid": True,
            "promotion_signal": strict_four_way,
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
        raise SystemExit("ZIP-factor native complete frontier invalid")


if __name__ == "__main__":
    main()
