from __future__ import annotations

"""Direct productization proof for C25CC01 on the exact external-normalized corpus.

Unlike the earlier projection oracle, this lane writes the real candidate archive, performs mandatory candidate
strong verification, extracts it through the candidate reader, and times the complete candidate build+verify
boundary against ZIP/Deflate-9 and solid Zstd-19.  It remains promotion evidence only: native, Android, shipping
selector and ordinary all-15 release authority are separate gates.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_r24_compact_control_composition_oracle_v2 as CORPUS
from experiments import entropygraph_v030_r24_compact_control_profile as CC
from experiments import entropygraph_v030_release_product as PRODUCT

TARGET = "07_incompressible_and_encrypted_like"
ROUNDS = 5


def _candidate(stage: Path, archive: Path, extract_to: Path) -> dict:
    started = time.perf_counter()
    stats = dict(CC.build(stage, archive))
    verified = dict(CC.strong_verify(archive))
    complete = time.perf_counter() - started
    if not verified.get("ok"):
        raise RuntimeError(f"C25CC01 strong verification failed: {verified!r}")
    if verified.get("format_profile") != CC.PROFILE:
        raise RuntimeError("C25CC01 profile identity drift")
    shutil.rmtree(extract_to, ignore_errors=True)
    CC.extract(archive, extract_to)
    external_tree = EXT._tree(extract_to)
    expected = EXT._tree(stage)
    if external_tree != expected:
        raise RuntimeError("C25CC01 external logical tree mismatch")
    return {
        **stats,
        "complete_create_s": complete,
        "tree_sha256": verified["tree_sha256"],
        "external_tree_sha256": external_tree,
        "candidate_strong_verify_green": True,
    }


def _competitor(stage: Path, work: Path, rep: int, name: str) -> dict:
    if name == "zip":
        out = work / f"zip-out-{rep}"
        row = EXT._zip(stage, work / f"row-{rep}.zip", out)
    else:
        out = work / f"zstd-out-{rep}"
        zw = work / f"zstd-work-{rep}"
        zw.mkdir(parents=True, exist_ok=True)
        row = EXT._tar_zstd(stage, work / f"row-{rep}.tar.zst", out, zw)
    EXT._verify_extracted(out, EXT._tree(stage), name)
    return row


def _target(source: Path, work: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-cc-direct-", dir=work) as td:
        root = Path(td)
        stage = EXT._normalized_stage(source, root / "stage-work")
        rows = []
        for rep in range(ROUNDS):
            order = ["cmpct", "zip", "zstd"]
            order = order[rep % 3 :] + order[: rep % 3]
            cur = {}
            for name in order:
                if name == "cmpct":
                    cur[name] = _candidate(stage, root / f"candidate-{rep}.cmpct", root / f"cmpct-out-{rep}")
                else:
                    cur[name] = _competitor(stage, root, rep, name)
            rows.append(cur)

        candidate_sizes = {int(row["cmpct"]["archive_bytes"]) for row in rows}
        zip_sizes = {int(row["zip"]["archive_bytes"]) for row in rows}
        zstd_sizes = {int(row["zstd"]["archive_bytes"]) for row in rows}
        candidate_sha = {__import__("hashlib").sha256((root / f"candidate-{i}.cmpct").read_bytes()).hexdigest() for i in range(ROUNDS)}
        trees = {row["cmpct"]["external_tree_sha256"] for row in rows}
        if not (len(candidate_sizes) == len(zip_sizes) == len(zstd_sizes) == len(candidate_sha) == len(trees) == 1):
            raise RuntimeError("C25CC01 target bytes/tree were not deterministic")
        cb = next(iter(candidate_sizes))
        zb = next(iter(zip_sizes))
        sb = next(iter(zstd_sizes))
        cc = statistics.median(float(row["cmpct"]["complete_create_s"]) for row in rows)
        zc = statistics.median(float(row["zip"]["create_s"]) for row in rows)
        sc = statistics.median(float(row["zstd"]["create_s"]) for row in rows)
        return {
            "rounds": ROUNDS,
            "candidate_bytes": cb,
            "zip_bytes": zb,
            "zstd19_bytes": sb,
            "median_candidate_complete_create_s": cc,
            "median_zip_create_s": zc,
            "median_zstd19_create_s": sc,
            "strictly_smaller_than_zip": cb < zb,
            "strictly_smaller_than_zstd19": cb < sb,
            "strictly_faster_than_zip": cc < zc,
            "strictly_faster_than_zstd19": cc < sc,
            "strict_four_way_win": cb < zb and cb < sb and cc < zc and cc < sc,
            "archive_sha_deterministic": True,
            "external_tree_deterministic": True,
            "physical_payload_records_unchanged": all(row["cmpct"]["physical_payload_records_unchanged"] for row in rows),
            "two_authenticated_control_copies": all(row["cmpct"]["two_authenticated_control_copies"] for row in rows),
            "semantic_index_roundtrip_exact": all(row["cmpct"]["semantic_index_roundtrip_exact"] for row in rows),
            "samples": [
                {
                    "candidate_create_s": float(row["cmpct"]["complete_create_s"]),
                    "zip_create_s": float(row["zip"]["create_s"]),
                    "zstd19_create_s": float(row["zstd"]["create_s"]),
                }
                for row in rows
            ],
        }


def _all15(sources: dict[str, Path], work: Path) -> dict:
    rows = []
    for name in sorted(sources):
        row_root = work / name
        row_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="cmpct-v030-cc-all15-", dir=row_root) as td:
            root = Path(td)
            stage = EXT._normalized_stage(sources[name], root / "stage-work")
            r24 = root / "shipping-r24.cmpct"
            PRODUCT._locality_bounded_r24_build(stage, r24)
            r24v = PRODUCT.strong_verify(r24)
            if not r24v.get("ok"):
                raise RuntimeError(f"shipping r24 failed on {name}")
            candidate = root / "candidate.cmpct"
            try:
                stats = dict(CC._write_profile(r24, candidate))
                cv = dict(CC.strong_verify(candidate))
                if not cv.get("ok") or cv["tree_sha256"] != r24v["tree_sha256"]:
                    raise RuntimeError(f"C25CC01 semantic mismatch on {name}")
                rows.append({
                    "workload": name,
                    "eligible": True,
                    "r24_bytes": r24.stat().st_size,
                    "candidate_bytes": candidate.stat().st_size,
                    "delta_vs_r24_bytes": candidate.stat().st_size - r24.stat().st_size,
                    "same_tree": True,
                    "physical_payload_records_unchanged": stats["physical_payload_records_unchanged"],
                })
            except CC.ProfileNotEligible:
                rows.append({
                    "workload": name,
                    "eligible": False,
                    "r24_bytes": r24.stat().st_size,
                    "candidate_bytes": None,
                    "delta_vs_r24_bytes": 0,
                    "same_tree": True,
                    "physical_payload_records_unchanged": True,
                })
    regressions = [row["workload"] for row in rows if row["eligible"] and row["delta_vs_r24_bytes"] >= 0]
    return {
        "rows": rows,
        "eligible_count": sum(row["eligible"] for row in rows),
        "strict_improvement_count": sum(row["eligible"] and row["delta_vs_r24_bytes"] < 0 for row in rows),
        "regressions": regressions,
        "all15_complete": len(rows) == 15,
        "zero_candidate_regressions_vs_r24": not regressions,
        "all_trees_equal": all(row["same_tree"] for row in rows),
        "all_payloads_unchanged": all(row["physical_payload_records_unchanged"] for row in rows),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    shutil.rmtree(args.work_root, ignore_errors=True)
    args.work_root.mkdir(parents=True)
    sources = CORPUS._build_all(args.work_root / "corpus")
    if set(sources) != set(CORPUS.ACCEPTED_ROWS):
        raise RuntimeError("C25CC01 productization corpus is not the exact accepted 15-workload set")
    all15 = _all15(sources, args.work_root / "all15")
    target = _target(sources[TARGET], args.work_root / "target")
    result = {
        "schema": "cmpct-v030-r24-compact-control-profile-productization-v1",
        "contract": {
            "profile": CC.PROFILE,
            "format_revision": CC.REVISION,
            "workloads": 15,
            "external_metadata_normalization": True,
            "candidate_strong_verification_inside_creation_timing": True,
            "two_authenticated_control_copies": True,
            "physical_payload_records_unchanged": True,
            "release_credit": False,
            "selector_change": False,
            "native_dispatch_change": False,
            "android_dispatch_change": False,
        },
        "all15": all15,
        "target": target,
        "gate": {
            "experiment_valid": all15["all15_complete"] and all15["zero_candidate_regressions_vs_r24"] and all15["all_trees_equal"] and all15["all_payloads_unchanged"],
            "target_strict_four_way_win": target["strict_four_way_win"],
            "promotion_signal": target["strict_four_way_win"],
            "passed": all15["all15_complete"] and all15["zero_candidate_regressions_vs_r24"] and all15["all_trees_equal"] and all15["all_payloads_unchanged"] and target["strict_four_way_win"],
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
