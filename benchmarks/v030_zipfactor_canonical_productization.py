from __future__ import annotations

"""Canonical-productization proof for the fused compact revision-25 ZIP-factor profile.

The timed candidate path performs one source pass that simultaneously captures the canonical filesystem manifest,
hashes each graph-owned ZIP and parses its framing, then writes the compact profile and performs mandatory one-pass
strong verification. A second independent manifest capture is deliberately *outside* the creation timer and serves
only as source-truth evidence, analogous to post-create extraction/tree verification for external competitors.
Native/Android parity, two-way recovery and selector promotion remain separate hard prerequisites.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import time

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from benchmarks import v030_external_competitors as EXT
from experiments import entropygraph_v030_canonical_final_impl as CANON
from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_zipfactor_compact as ZFC
from experiments import entropygraph_v030_zipfactor_fused as ZFF


def _verify_product_identity(archive: Path) -> dict:
    scan = ZFC.verify_and_identities(archive)
    manifest_raw = scan["manifest_raw"]
    identities = scan["identities"]
    decoded = scan["manifest"]
    expected_paths = set(decoded["regular"]) | {FS.FILESYSTEM_MANIFEST}
    if set(identities) != expected_paths:
        raise RuntimeError("compact ZIP-factor profile/member manifest path mismatch")
    if identities[FS.FILESYSTEM_MANIFEST] != (len(manifest_raw), hashlib.sha256(manifest_raw).digest()):
        raise RuntimeError("compact ZIP-factor filesystem manifest graph identity mismatch")
    for rel, identity in decoded["regular"].items():
        if identities.get(rel) != identity:
            raise RuntimeError(f"compact ZIP-factor manifest/content identity mismatch: {rel}")
    semantic = CANON._semantic_tree_sha(decoded)
    verified = {key: value for key, value in scan.items() if key not in {"manifest_raw", "manifest", "identities"}}
    return {
        "strong_verify": verified,
        "manifest_entries": len(decoded["manifest"]["entries"]),
        "content_members": len(identities),
        "semantic_tree_sha256": semantic,
        "manifest_content_identity_exact": True,
        "verified_max_member_read_amplification": scan["max_member_read_amplification"],
        "verified_max_decode_unit_bytes": scan["max_decode_unit_bytes"],
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    CORPUS.build(corpus)
    source = corpus / "04_deflate_family"
    historical_tree = CORPUS.tree_hash(source)

    with tempfile.TemporaryDirectory(prefix="cmpct-zf-product-", dir=work_root) as td_raw:
        td = Path(td_raw)
        stage = EXT._normalized_stage(source, td)
        zip_result = EXT._zip(stage, td / "base.zip", td / "zip-out")
        zstd_result = EXT._tar_zstd(stage, td / "base.tar.zst", td / "zstd-out", td)

        candidate = td / "candidate-r25-zf.cmpct"
        started = time.perf_counter()
        build_stats = ZFF.build(stage, candidate, level=6, group_size=7)
        build_s = time.perf_counter() - started

        started = time.perf_counter()
        identity = _verify_product_identity(candidate)
        verify_s = time.perf_counter() - started
        create_s = build_s + verify_s
        archive_bytes = candidate.stat().st_size

        # Independent source truth is a postcondition, not codec creation work. It intentionally uses the generic
        # canonical bridge rather than the fused scanner, so a shared scanner bug cannot manufacture identity.
        started = time.perf_counter()
        truth_tree = td / "source-truth-profile"
        truth = CANON._prepare_profile_tree(stage, truth_tree)
        source_tree = CANON._semantic_tree_sha(CANON._decode_manifest(truth["manifest_raw"]))
        source_truth_s = time.perf_counter() - started
        if identity["semantic_tree_sha256"] != source_tree:
            raise RuntimeError("fused ZIP-factor semantic tree differs from independent source truth")

        result = {
            "schema": "cmpct-v030-zipfactor-canonical-productization-v3",
            "claim_boundary": (
                "fused compact canonical Python product-boundary proof only; native/Android parity, two-way recovery, and selector promotion remain mandatory"
            ),
            "workload": "resemblance_hostile_v1/04_deflate_family",
            "historical_tree_sha256": historical_tree,
            "canonical_semantic_tree_sha256": source_tree,
            "independent_source_truth_s": source_truth_s,
            "zip": zip_result,
            "tar_zstd19": zstd_result,
            "candidate": {
                **build_stats,
                **identity,
                "archive_bytes": archive_bytes,
                "profile_prepare_s": 0.0,
                "profile_build_s": build_s,
                "mandatory_verify_s": verify_s,
                "create_s": create_s,
                "fused_manifest_and_zip_parse": True,
                "beats_zip_size": archive_bytes < int(zip_result["archive_bytes"]),
                "beats_zstd19_size": archive_bytes < int(zstd_result["archive_bytes"]),
                "beats_zip_create": create_s < float(zip_result["create_s"]),
                "beats_zstd19_create": create_s < float(zstd_result["create_s"]),
            },
        }
        c = result["candidate"]
        result["gate"] = {
            "exact_manifest_content_identity": c["manifest_content_identity_exact"] is True,
            "canonical_semantic_tree_exact": c["semantic_tree_sha256"] == source_tree,
            "independent_source_truth": True,
            "strong_verify_green": c["strong_verify"]["ok"] is True,
            "locality_green": (
                float(c["verified_max_member_read_amplification"]) <= 8.0
                and int(c["verified_max_decode_unit_bytes"]) <= 8 * 1024 * 1024
            ),
            "strictly_beats_zip_size": c["beats_zip_size"],
            "strictly_beats_zstd19_size": c["beats_zstd19_size"],
            "strictly_beats_zip_create": c["beats_zip_create"],
            "strictly_beats_zstd19_create": c["beats_zstd19_create"],
        }
        result["gate"]["passed"] = all(result["gate"].values())
        return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-zipfactor-product-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zipfactor-product.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate": result["candidate"], "zip": result["zip"], "zstd": result["tar_zstd19"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("fused compact canonical ZIP-factor productization gate failed")


if __name__ == "__main__":
    main()
