from __future__ import annotations

"""Exact product-boundary A/B for compact-v2 versus binary-control-v3 ZIP factorization.

Both candidates pay fused source construction plus cold full identity verification. The oracle preserves the frozen
ZIP and solid-Zstd comparators and the <=8x / <=8 MiB locality laws. It cannot authorize selector promotion or
native/Android support; its purpose is to determine whether removing compressed MessagePack control metadata is a
material Pareto improvement worth carrying into the canonical/native profile.

A valid exact experiment is deliberately distinct from a promotion signal. A candidate that is smaller but slower
is durable negative evidence, not an invalid experiment and not release credit.
"""

import argparse
import json
from pathlib import Path
import shutil
import tempfile
import time

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from benchmarks import v030_external_competitors as EXT
from experiments import entropygraph_v030_canonical_final_impl as CANON
from experiments import entropygraph_v030_zipfactor_compact as V2
from experiments import entropygraph_v030_zipfactor_compact_v3 as V3
from experiments import entropygraph_v030_zipfactor_fused as FUSED


def _semantic(scan: dict) -> str:
    return CANON._semantic_tree_sha(scan["manifest"])


def _candidate(stage: Path, archive: Path, *, version: int) -> dict:
    started = time.perf_counter()
    if version == 2:
        build = FUSED.build(stage, archive, level=6, group_size=7)
    else:
        build = V3.build(stage, archive, level=6, group_size=7)
    build_s = time.perf_counter() - started

    started = time.perf_counter()
    scan = V2.verify_and_identities(archive) if version == 2 else V3.verify_and_identities(archive)
    verify_s = time.perf_counter() - started
    return {
        **build,
        "archive_bytes": archive.stat().st_size,
        "build_s": build_s,
        "verify_s": verify_s,
        "create_s": build_s + verify_s,
        "semantic_tree_sha256": _semantic(scan),
        "verified_user_files": scan["verified_user_files"],
        "verified_max_member_read_amplification": scan["max_member_read_amplification"],
        "verified_max_decode_unit_bytes": scan["max_decode_unit_bytes"],
        "strong_verify_green": scan["ok"] is True,
        "identity_count": len(scan["identities"]),
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    CORPUS.build(corpus)
    source = corpus / "04_deflate_family"

    with tempfile.TemporaryDirectory(prefix="cmpct-zf-binary-control-", dir=work_root) as td_raw:
        td = Path(td_raw)
        stage = EXT._normalized_stage(source, td)
        zip_result = EXT._zip(stage, td / "base.zip", td / "zip-out")
        zstd_result = EXT._tar_zstd(stage, td / "base.tar.zst", td / "zstd-out", td)

        v2 = _candidate(stage, td / "candidate-v2.cmpct", version=2)
        v3 = _candidate(stage, td / "candidate-v3.cmpct", version=3)
        truth = CANON._prepare_profile_tree(stage, td / "truth")
        source_semantic = CANON._semantic_tree_sha(CANON._decode_manifest(truth["manifest_raw"]))

        for candidate in (v2, v3):
            candidate["semantic_tree_exact"] = candidate["semantic_tree_sha256"] == source_semantic
            candidate["locality_green"] = (
                float(candidate["verified_max_member_read_amplification"]) <= 8.0
                and int(candidate["verified_max_decode_unit_bytes"]) <= 8 * 1024 * 1024
            )
            candidate["beats_zip_size"] = int(candidate["archive_bytes"]) < int(zip_result["archive_bytes"])
            candidate["beats_zstd19_size"] = int(candidate["archive_bytes"]) < int(zstd_result["archive_bytes"])
            candidate["beats_zip_create"] = float(candidate["create_s"]) < float(zip_result["create_s"])
            candidate["beats_zstd19_create"] = float(candidate["create_s"]) < float(zstd_result["create_s"])

        result = {
            "schema": "cmpct-v030-zipfactor-binary-control-oracle-v2",
            "claim_boundary": "research product-boundary A/B only; selector/native/Android/recovery promotion remains forbidden",
            "workload": "resemblance_hostile_v1/04_deflate_family",
            "source_semantic_tree_sha256": source_semantic,
            "zip": zip_result,
            "tar_zstd19": zstd_result,
            "compact_v2": v2,
            "binary_control_v3": v3,
        }
        result["delta"] = {
            "archive_bytes": int(v3["archive_bytes"]) - int(v2["archive_bytes"]),
            "create_s": float(v3["create_s"]) - float(v2["create_s"]),
            "build_s": float(v3["build_s"]) - float(v2["build_s"]),
            "verify_s": float(v3["verify_s"]) - float(v2["verify_s"]),
        }
        gate = {
            "v2_exact": v2["strong_verify_green"] and v2["semantic_tree_exact"] and v2["locality_green"],
            "v3_exact": v3["strong_verify_green"] and v3["semantic_tree_exact"] and v3["locality_green"],
            "v3_smaller_than_v2": int(v3["archive_bytes"]) < int(v2["archive_bytes"]),
            "v3_faster_than_v2": float(v3["create_s"]) < float(v2["create_s"]),
            "v3_strictly_beats_zip_size": v3["beats_zip_size"],
            "v3_strictly_beats_zstd19_size": v3["beats_zstd19_size"],
            "v3_strictly_beats_zip_create": v3["beats_zip_create"],
            "v3_strictly_beats_zstd19_create": v3["beats_zstd19_create"],
        }
        gate["experiment_valid"] = bool(gate["v2_exact"] and gate["v3_exact"])
        gate["promotion_signal"] = bool(
            gate["experiment_valid"]
            and gate["v3_smaller_than_v2"]
            and gate["v3_faster_than_v2"]
            and gate["v3_strictly_beats_zip_size"]
            and gate["v3_strictly_beats_zstd19_size"]
            and gate["v3_strictly_beats_zip_create"]
            and gate["v3_strictly_beats_zstd19_create"]
        )
        gate["release_credit"] = False
        result["gate"] = gate
        return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-zf-binary-control-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zf-binary-control.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"delta": result["delta"], "v3": result["binary_control_v3"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("binary-control ZIP-factor experiment invalid")


if __name__ == "__main__":
    main()
