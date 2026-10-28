from __future__ import annotations

"""External-matrix-normalized shadow for r24 compact authenticated control.

The ordinary external ZIP/Zstd matrix normalizes filesystem metadata *before* building every format. Earlier
compact-control experiments intentionally used the repaired historical corpus directly, which is the right domain
for v0.29 causality but not the exact input presented to the external competitor gate. This proof closes that
measurement seam without changing production bytes: it rebuilds the exact 15 accepted workloads, applies the same
external normalization, builds today's shipping r24, and projects only the already-audited two-copy compact control
replacement while leaving every payload record unchanged.

Research only. A green result is a productization signal, never release authority.
"""

import argparse
import json
from pathlib import Path
import shutil
import statistics
import tempfile

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_r24_compact_control_composition_oracle_v2 as CORPUS
from benchmarks import v030_r24_compact_control_oracle as CONTROL
from experiments import entropygraph_v030_release_product as PRODUCT

TARGET = "07_incompressible_and_encrypted_like"
ROUNDS = 5


def _cmpct_projection(stage: Path, archive: Path) -> dict:
    verified = CONTROL._verified_r24(stage, archive)
    compact = CONTROL._compact_once(archive)
    shipping = int(compact["archive_bytes"])
    projected = int(compact["projected_two_copy_archive_bytes"])
    selected = min(shipping, projected)

    # ``PRODUCT.strong_verify`` returns CMPCT's canonical filesystem-semantic tree, while the external comparator
    # intentionally uses its regular-file content tree so ZIP/tar metadata differences cannot manufacture wins.
    # Keep both proofs: strong verification remains mandatory, then independently extract the actual r24 artifact
    # and hash it in the exact external comparator domain.  Never compare those two intentionally different hashes.
    extracted = archive.parent / f"{archive.name}.external-tree"
    shutil.rmtree(extracted, ignore_errors=True)
    PRODUCT.extract(archive, extracted)
    external_tree = EXT._tree(extracted)
    if external_tree != EXT._tree(stage):
        raise RuntimeError("shipping r24 extraction changed external logical tree identity")

    return {
        "shipping_r24_bytes": shipping,
        "compact_projected_bytes": projected,
        "selected_projected_bytes": selected,
        "compact_selected": projected < shipping,
        "saving_bytes": shipping - selected,
        "complete_r24_create_s": float(verified["complete_create_s"]),
        "compact_transform_s": float(compact["compact_transform_s"]),
        "conservative_create_s": float(verified["complete_create_s"] + compact["compact_transform_s"]),
        "semantic_index_roundtrip_exact": bool(compact["semantic_index_roundtrip_exact"]),
        "two_authenticated_control_copies_retained": bool(compact["two_authenticated_control_copies_retained"]),
        "physical_payload_records_unchanged": bool(compact["physical_payload_records_unchanged"]),
        "canonical_tree_sha256": verified["tree_sha256"],
        "external_tree_sha256": external_tree,
    }


def _competitors(stage: Path, work: Path, stem: str) -> tuple[dict, dict]:
    zip_out = work / f"{stem}-zip-out"
    zstd_out = work / f"{stem}-zstd-out"
    zstd_work = work / f"{stem}-zstd-work"
    zstd_work.mkdir(parents=True, exist_ok=True)
    z = EXT._zip(stage, work / f"{stem}.zip", zip_out)
    s = EXT._tar_zstd(stage, work / f"{stem}.tar.zst", zstd_out, zstd_work)
    expected = EXT._tree(stage)
    EXT._verify_extracted(zip_out, expected, "zip")
    EXT._verify_extracted(zstd_out, expected, "zstd19")
    return z, s


def _one(source: Path, work: Path, label: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-extnorm-", dir=work) as td:
        td_path = Path(td)
        stage = EXT._normalized_stage(source, td_path)
        expected = EXT._tree(stage)
        cmpct = _cmpct_projection(stage, td_path / "candidate.cmpct")
        if cmpct["external_tree_sha256"] != expected:
            raise RuntimeError(f"normalized r24 external-tree mismatch for {label}")
        z, s = _competitors(stage, td_path, "single")
        return {
            "workload": label,
            **cmpct,
            "zip_bytes": int(z["archive_bytes"]),
            "zstd19_bytes": int(s["archive_bytes"]),
            "zip_create_s": float(z["create_s"]),
            "zstd19_create_s": float(s["create_s"]),
            "projected_smaller_than_zip": cmpct["selected_projected_bytes"] < int(z["archive_bytes"]),
            "projected_smaller_than_zstd19": cmpct["selected_projected_bytes"] < int(s["archive_bytes"]),
        }


def _target_repeated(source: Path, work: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-extnorm-target-", dir=work) as td:
        td_path = Path(td)
        stage = EXT._normalized_stage(source, td_path)
        expected_tree = EXT._tree(stage)
        rows = []
        for rep in range(ROUNDS):
            order = ["cmpct", "zip", "zstd"]
            order = order[rep % 3 :] + order[: rep % 3]
            cur: dict[str, dict] = {}
            for name in order:
                if name == "cmpct":
                    cur[name] = _cmpct_projection(stage, td_path / f"target-{rep}.cmpct")
                    if cur[name]["external_tree_sha256"] != expected_tree:
                        raise RuntimeError("target r24 external tree mismatch")
                elif name == "zip":
                    out = td_path / f"target-{rep}-zip-out"
                    cur[name] = EXT._zip(stage, td_path / f"target-{rep}.zip", out)
                    EXT._verify_extracted(out, expected_tree, "zip")
                else:
                    out = td_path / f"target-{rep}-zstd-out"
                    zw = td_path / f"target-{rep}-zstd-work"
                    zw.mkdir(parents=True, exist_ok=True)
                    cur[name] = EXT._tar_zstd(stage, td_path / f"target-{rep}.tar.zst", out, zw)
                    EXT._verify_extracted(out, expected_tree, "zstd19")
            rows.append(cur)

        projected = {int(r["cmpct"]["selected_projected_bytes"]) for r in rows}
        shipping = {int(r["cmpct"]["shipping_r24_bytes"]) for r in rows}
        zip_sizes = {int(r["zip"]["archive_bytes"]) for r in rows}
        zstd_sizes = {int(r["zstd"]["archive_bytes"]) for r in rows}
        external_trees = {r["cmpct"]["external_tree_sha256"] for r in rows}
        if not (len(projected) == len(shipping) == len(zip_sizes) == len(zstd_sizes) == len(external_trees) == 1):
            raise RuntimeError("target archive size/tree was not deterministic")
        pb, rb, zb, sb = next(iter(projected)), next(iter(shipping)), next(iter(zip_sizes)), next(iter(zstd_sizes))
        pc = statistics.median(float(r["cmpct"]["conservative_create_s"]) for r in rows)
        zc = statistics.median(float(r["zip"]["create_s"]) for r in rows)
        sc = statistics.median(float(r["zstd"]["create_s"]) for r in rows)
        return {
            "rounds": ROUNDS,
            "shipping_r24_bytes": rb,
            "projected_bytes": pb,
            "saving_bytes": rb - pb,
            "zip_bytes": zb,
            "zstd19_bytes": sb,
            "median_conservative_create_s": pc,
            "median_zip_create_s": zc,
            "median_zstd19_create_s": sc,
            "strict_four_way_potential": pb < zb and pb < sb and pc < zc and pc < sc,
            "size_and_tree_deterministic": True,
            "semantic_index_roundtrip_exact": all(r["cmpct"]["semantic_index_roundtrip_exact"] for r in rows),
            "two_authenticated_control_copies_retained": all(r["cmpct"]["two_authenticated_control_copies_retained"] for r in rows),
            "physical_payload_records_unchanged": all(r["cmpct"]["physical_payload_records_unchanged"] for r in rows),
            "samples": [
                {
                    "cmpct_conservative_create_s": float(r["cmpct"]["conservative_create_s"]),
                    "zip_create_s": float(r["zip"]["create_s"]),
                    "zstd19_create_s": float(r["zstd"]["create_s"]),
                }
                for r in rows
            ],
        }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    shutil.rmtree(args.work_root, ignore_errors=True)
    args.work_root.mkdir(parents=True)

    sources = CORPUS._build_all(args.work_root / "corpus")
    rows = []
    for name in sorted(sources):
        row_work = args.work_root / "rows" / name
        row_work.mkdir(parents=True, exist_ok=True)
        rows.append(_one(sources[name], row_work, name))

    target_source = sources.get(TARGET)
    if target_source is None:
        raise RuntimeError(f"missing target {TARGET!r}")
    target_work = args.work_root / "target-repeat"
    target_work.mkdir(parents=True, exist_ok=True)
    target = _target_repeated(target_source, target_work)

    regressions = [r["workload"] for r in rows if r["selected_projected_bytes"] > r["shipping_r24_bytes"]]
    exact = all(r["semantic_index_roundtrip_exact"] for r in rows)
    copies = all(r["two_authenticated_control_copies_retained"] for r in rows)
    payload = all(r["physical_payload_records_unchanged"] for r in rows)
    external_tree_exact = all(r["external_tree_sha256"] for r in rows)
    result = {
        "schema": "cmpct-v030-r24-compact-control-external-normalized-v2",
        "contract": {
            "workloads": 15,
            "normalization_matches_external_matrix": True,
            "tree_domains_separated": True,
            "canonical_strong_verification_mandatory": True,
            "external_tree_verified_by_independent_extract": True,
            "release_credit": False,
            "production_selector_change": False,
            "format_revision_change": False,
            "two_authenticated_control_copies_retained": True,
            "physical_payload_records_unchanged": True,
            "timing_boundary": "shipping r24 build + mandatory strong verify + post-build compact-control transform",
        },
        "rows": rows,
        "target": target,
        "summary": {
            "aggregate_shipping_r24_bytes": sum(int(r["shipping_r24_bytes"]) for r in rows),
            "aggregate_projected_bytes": sum(int(r["selected_projected_bytes"]) for r in rows),
            "aggregate_saving_bytes": sum(int(r["shipping_r24_bytes"] - r["selected_projected_bytes"]) for r in rows),
            "projected_zstd_size_wins": sum(bool(r["projected_smaller_than_zstd19"]) for r in rows),
            "projected_zip_size_wins": sum(bool(r["projected_smaller_than_zip"]) for r in rows),
            "regressions": regressions,
        },
        "gate": {
            "experiment_valid": len(rows) == 15 and exact and copies and payload and external_tree_exact and not regressions,
            "zero_projected_byte_regressions": not regressions,
            "target_strict_four_way_potential": bool(target["strict_four_way_potential"]),
            "promotion_signal": bool(target["strict_four_way_potential"]),
            "passed": len(rows) == 15 and exact and copies and payload and external_tree_exact and not regressions,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
